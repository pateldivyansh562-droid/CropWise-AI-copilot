"""
crop_doctor/router.py
────────────────────────────────────────────────────────────────────────────
Mount in main.py:
    from crop_doctor.router import router as doctor_router
    app.include_router(doctor_router, prefix="/crop-doctor", tags=["Crop Doctor"])
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from crop_doctor.utils import detect_disease, build_disease_prompt, OLLAMA_URL, MODEL

CLOUD_KEY   = "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d"
CLOUD_URL   = "https://ollama.com/v1/chat/completions"
CLOUD_MODEL = "gemma3:12b"

BASE_DIR  = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router    = APIRouter()


# ── Models ─────────────────────────────────────────────────────────────────────
class ExplainRequest(BaseModel):
    disease_name: str
    probability:  float
    description:  str  = ""
    section:      str  = "overview"   # overview | causes | prevention | treatment | spray
    lang:         str  = "en"
    crop_name:    str  = ""


# ── Pages ───────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def doctor_page(request: Request):
    return templates.TemplateResponse("doctor.html", {"request": request})


# ── Disease detection ──────────────────────────────────────────────────────────
@router.post("/api/detect")
async def api_detect(image: UploadFile = File(...)):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:   # 10 MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")

    result = detect_disease(image_bytes)
    return result


# ── AI explanation — streaming SSE ────────────────────────────────────────────
@router.post("/api/explain/stream")
async def api_explain_stream(body: ExplainRequest):
    lang    = body.lang if body.lang in ("en", "hi") else "en"
    system, user = build_disease_prompt(
        disease_name = body.disease_name,
        probability  = body.probability,
        description  = body.description,
        section      = body.section,
        lang         = lang,
        crop_name    = body.crop_name,
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    async def token_gen() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST", CLOUD_URL,
                    headers={
                        "Authorization": f"Bearer {CLOUD_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": CLOUD_MODEL,
                        "messages": messages,
                        "stream": True,
                    },
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
