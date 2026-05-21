
"""
main.py — FastAPI application
──────────────────────────────────────────────────────────────
Run:
    uvicorn main:app --reload --port 8000

The Kisan AI assistant is mounted at /assistant
The beautiful farmer dashboard is served at /
"""

import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import AsyncGenerator
import httpx
import uvicorn

# ── Import routers ─────────────────────────────────────────────────────────────
from assistant.app.router  import router as assistant_router
from manage_lands.router   import router as lands_router
from schemes.router        import router as schemes_router
from crop_doctor.router    import router as doctor_router
from mandi_prices.router   import router as mandi_router
from kisan_videos.router   import router as videos_router

app = FastAPI(title="Kisan AI")

# ── CORS (needed for Render deployment) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).parent

# ── Static files (mount BEFORE routers) ───────────────────────────────────────
app.mount("/assistant/static",    StaticFiles(directory=str(ROOT / "assistant"    / "static")), name="assistant-static")
app.mount("/manage-lands/static", StaticFiles(directory=str(ROOT / "manage_lands" / "static")), name="lands-static")

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(assistant_router, prefix="/assistant",    tags=["Assistant"])
app.include_router(lands_router,     prefix="/manage-lands", tags=["Manage Lands"])
app.include_router(schemes_router,   prefix="/schemes",      tags=["Schemes"])
app.include_router(doctor_router,    prefix="/crop-doctor",  tags=["Crop Doctor"])
app.include_router(mandi_router,     prefix="/mandi",        tags=["Mandi"])
app.include_router(videos_router,    prefix="/videos",       tags=["Videos"])

# ── Dashboard chat proxy (avoids CORS issues on Render) ────────────────────────
CLOUD_URL   = "https://ollama.com/v1/chat/completions"
CLOUD_KEY   = "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d"
CLOUD_MODEL = "gemma3:12b"

@app.post("/api/dashboard-chat")
async def dashboard_chat(request: Request):
    body = await request.json()
    messages = body.get("messages", [])

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                CLOUD_URL,
                headers={
                    "Authorization": f"Bearer {CLOUD_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CLOUD_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )
            data = resp.json()
            return data
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/api/geocode")
async def geocode(lat: float, lng: float):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"

        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers={"User-Agent": "kisan-ai-app"})

        data = res.json()

        # Extract readable location
        address = data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or ""
        state = address.get("state", "")

        return {
            "location": f"{city}, {state}".strip(", ")
        }

    except Exception as e:
        return {"error": str(e)}

# ── Dashboard HTML (loaded from file) ─────────────────────────────────────────
DASHBOARD_HTML = (ROOT / "dashboard.html").read_text(encoding="utf-8")

# ── Home — serves the beautiful Kisan AI Dashboard ────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=DASHBOARD_HTML)

# ── Run directly: python main.py ───────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)