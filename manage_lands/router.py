"""
manage_lands/router.py
Mount in main.py:
    from manage_lands.router import router as lands_router
    app.mount("/manage-lands/static", StaticFiles(...), name="lands-static")
    app.include_router(lands_router, prefix="/manage-lands")
"""

import json
import uuid
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from manage_lands.utils import (
    load_lands, upsert_land, delete_land, get_land,
    get_live_weather_forecast, build_suggestion_prompt,
    MODEL, OLLAMA_URL, CLOUD_KEY,
)

BASE_DIR  = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router    = APIRouter()


# ── Models ─────────────────────────────────────────────────────────────────────
class LandIn(BaseModel):
    name:          str
    crop_name:     str
    sowing_date:   str = ""
    last_watered:  str = ""
    watering_freq: str = ""
    notes:         str = ""
    lang:          str = "en"

class SuggestRequest(BaseModel):
    land_id: str
    lang:    str = "en"


# ── Pages ───────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def list_page(request: Request):
    lands   = load_lands()
    weather = get_live_weather_forecast()
    return templates.TemplateResponse("list.html", {
        "request": request,
        "lands":   list(lands.values()),
        "weather": weather,
        "now":     datetime.now().strftime("%d %b %Y"),
    })

@router.get("/land/{land_id}", response_class=HTMLResponse)
async def detail_page(request: Request, land_id: str):
    land = get_land(land_id)
    if not land:
        raise HTTPException(404, "Land not found")
    weather = get_live_weather_forecast()
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "land":    land,
        "weather": weather,
        "now":     datetime.now().strftime("%d %b %Y"),
    })


# ── CRUD API ────────────────────────────────────────────────────────────────────
@router.get("/api/lands")
async def api_get_lands():
    return {"lands": list(load_lands().values())}

@router.post("/api/lands")
async def add_land(body: LandIn):
    land_id = str(uuid.uuid4())[:8]
    land = {"id": land_id, "created_at": datetime.now().isoformat(), **body.model_dump()}
    upsert_land(land_id, land)
    return {"ok": True, "land_id": land_id, "land": land}

@router.put("/api/lands/{land_id}")
async def update_land(land_id: str, body: LandIn):
    existing = get_land(land_id)
    if not existing:
        raise HTTPException(404, "Land not found")
    land = {**existing, **body.model_dump(), "updated_at": datetime.now().isoformat()}
    upsert_land(land_id, land)
    return {"ok": True, "land": land}

@router.delete("/api/lands/{land_id}")
async def remove_land(land_id: str):
    if not get_land(land_id):
        raise HTTPException(404, "Land not found")
    delete_land(land_id)
    return {"ok": True}

@router.get("/api/weather")
async def api_weather():
    return get_live_weather_forecast()


# ── AI suggestion — streaming SSE ──────────────────────────────────────────────
@router.post("/api/suggest/stream")
async def suggest_stream(body: SuggestRequest):
    land = get_land(body.land_id)
    if not land:
        raise HTTPException(404, "Land not found")

    lang           = body.lang if body.lang in ("en", "hi") else "en"
    weather        = get_live_weather_forecast()
    system, user   = build_suggestion_prompt(land, weather, lang)
    messages       = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    async def token_gen() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                async with client.stream(
                    "POST", OLLAMA_URL,
                    headers={
                        "Authorization": f"Bearer {CLOUD_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"model": MODEL, "messages": messages, "stream": True},
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line or line == "data: [DONE]":
                            continue

                        # Ollama Cloud uses OpenAI-style SSE: strip "data: " prefix
                        if line.startswith("data: "):
                            line = line[6:]

                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # OpenAI-style delta format
                        token = (
                            chunk.get("choices") or [{}]
                        )[0].get("delta", {}).get("content", "")

                        if token:
                            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0)

                        # Stop when finish_reason is set
                        finish = (chunk.get("choices") or [{}])[0].get("finish_reason")
                        if finish == "stop":
                            break
            yield f"data: {json.dumps({'done': True})}\n\n"
        except httpx.ConnectError:
            yield f"data: {json.dumps({'error': 'Cannot connect to Ollama Cloud. Check your API key and network.'})}\n\n"
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'error': 'Request timed out. Try again.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        token_gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
