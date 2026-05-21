"""
assistant/router.py
-------------------
Mount this into your main FastAPI app:

    from assistant.router import router as assistant_router
    app.include_router(assistant_router, prefix="/assistant")

Then visit: http://localhost:8000/assistant
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ── Paths ───────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
HISTORY_FILE = BASE_DIR / "data" / "history.json"
HISTORY_FILE.parent.mkdir(exist_ok=True)

# ── Router ──────────────────────────────────────────────────────────────────────
router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ── Config ──────────────────────────────────────────────────────────────────────
CLOUD_KEY         = os.getenv("OLLAMA_CLOUD_KEY", "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d")
CLOUD_URL         = "https://ollama.com/v1/chat/completions"
CLOUD_MODEL       = "gemma3:12b"
OLLAMA_CHAT       = CLOUD_URL  # for backward compatibility
MODEL             = CLOUD_MODEL
MAX_HISTORY_PAIRS = 10

CHAT_SYSTEM = {
    "en": (
        "You are Kisan AI, an expert Indian Agronomist and farming advisor. "
        "Rules: "
        "1. Always respond in English. "
        "2. Give thorough, detailed responses — explain the cause, solution, and prevention clearly. "
        "3. Use bullet points or numbered steps when listing advice. "
        "4. Include specific product names, dosages, or techniques where relevant. "
        "5. Only provide scientifically accurate farming advice. No filler phrases. "
        "6. Remember previous messages for context."
        "7. Be VERY brief — 5 to 7 sentences only. Your response will be spoken aloud. "
    ),
    "hi": (
        "आप Kisan AI हैं, एक विशेषज्ञ भारतीय कृषि विशेषज्ञ। "
        "नियम: "
        "1. हमेशा हिंदी में उत्तर दें। "
        "2. विस्तृत उत्तर दें — कारण, समाधान और रोकथाम स्पष्ट रूप से बताएं। "
        "3. सलाह देते समय बुलेट पॉइंट या क्रमांकित चरणों का उपयोग करें। "
        "4. जहाँ उचित हो, उत्पाद के नाम, खुराक या तकनीकें शामिल करें। "
        "5. केवल वैज्ञानिक रूप से सटीक कृषि सलाह दें। "
        "6. संदर्भ के लिए पिछले संदेश याद रखें।"
        "7. बहुत संक्षिप्त रहें — केवल 5 से 7 वाक्य। आपका उत्तर बोला जाएगा। "

    ),
}

VOICE_SYSTEM = {
    "en": (
        "You are Kisan AI, an expert Indian Agronomist. "
        "Rules: "
        "1. Always respond in English. "
        "2. Be VERY brief — 1 to 2 sentences only. Your response will be spoken aloud. "
        "3. No bullet points, no lists, no markdown. Plain spoken language only. "
        "4. Give only the single most essential piece of advice. "
        "5. Remember previous messages for context."
    ),
    "hi": (
        "आप Kisan AI हैं, एक विशेषज्ञ भारतीय कृषि विशेषज्ञ। "
        "नियम: "
        "1. हमेशा हिंदी में उत्तर दें। "
        "2. बहुत संक्षिप्त रहें — केवल 1 से 2 वाक्य। आपका उत्तर बोला जाएगा। "
        "3. कोई बुलेट पॉइंट, सूची या मार्कडाउन नहीं। केवल सरल बोली जाने वाली भाषा। "
        "4. केवल सबसे जरूरी सलाह दें। "
        "5. संदर्भ के लिए पिछले संदेश याद रखें।"
    ),
}


# ── History helpers ──────────────────────────────────────────────────────────────
def _load_store() -> dict:
    if HISTORY_FILE.exists():
        try:
            # Always read as UTF-8 — fixes charmap error on Windows
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"chat_en": [], "chat_hi": [], "voice_en": [], "voice_hi": []}


def _save_store(store: dict):
    # Always write as UTF-8 — fixes charmap error on Windows
    HISTORY_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _key(mode: str, lang: str) -> str:
    return f"{mode}_{lang}"


def get_history(mode: str, lang: str) -> list[dict]:
    return _load_store().get(_key(mode, lang), [])


def append_history(mode: str, lang: str, user_msg: str, ai_msg: str):
    store = _load_store()
    key   = _key(mode, lang)
    hist  = store.get(key, [])
    hist.append({"role": "user",      "content": user_msg, "ts": datetime.now().isoformat()})
    hist.append({"role": "assistant", "content": ai_msg,   "ts": datetime.now().isoformat()})
    store[key] = hist[-(MAX_HISTORY_PAIRS * 2):]
    _save_store(store)


def clear_history(mode: str, lang: str):
    store = _load_store()
    store[_key(mode, lang)] = []
    _save_store(store)


# ── Pydantic models ──────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    lang: str = "en"   # "en" | "hi"

class VoiceRequest(BaseModel):
    message: str
    lang: str = "hi"

class ClearRequest(BaseModel):
    mode: str   # "chat" | "voice"
    lang: str   # "en"  | "hi"


# ── Page route ───────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def assistant_page(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request})


# ── History routes ───────────────────────────────────────────────────────────────
@router.get("/api/history/{mode}/{lang}")
async def api_get_history(mode: str, lang: str):
    if mode not in ("chat", "voice") or lang not in ("en", "hi"):
        raise HTTPException(400, "mode must be chat/voice, lang must be en/hi")
    history = get_history(mode, lang)
    return {"mode": mode, "lang": lang, "history": history, "count": len(history) // 2}


@router.post("/api/history/clear")
async def api_clear_history(body: ClearRequest):
    if body.mode not in ("chat", "voice") or body.lang not in ("en", "hi"):
        raise HTTPException(400, "Invalid mode or lang")
    clear_history(body.mode, body.lang)
    return {"ok": True}


# ── Streaming chat ───────────────────────────────────────────────────────────────
@router.post("/api/chat/stream")
async def chat_stream(body: ChatRequest):
    lang     = body.lang if body.lang in ("en", "hi") else "en"
    user_msg = body.message.strip()
    if not user_msg:
        raise HTTPException(400, "Empty message")

    history  = get_history("chat", lang)
    messages = [{"role": "system", "content": CHAT_SYSTEM[lang]}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    async def generate() -> AsyncGenerator[str, None]:
        full_reply = ""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream(
                    "POST",
                    CLOUD_URL,
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
                            full_reply += token
                            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0)

                        # Stop when finish_reason is set
                        finish = (chunk.get("choices") or [{}])[0].get("finish_reason")
                        if finish == "stop":
                            break

            append_history("chat", lang, user_msg, full_reply)
            new_count = len(get_history("chat", lang)) // 2
            yield f"data: {json.dumps({'done': True, 'count': new_count}, ensure_ascii=False)}\n\n"

        except httpx.ConnectError:
            yield f"data: {json.dumps({'error': 'Cannot connect to Ollama Cloud. Check your API key and network.'})}\n\n"
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'error': 'Request timed out. Try again.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Voice (short, non-streaming) ─────────────────────────────────────────────────
@router.post("/api/voice")
async def voice_query(body: VoiceRequest):
    lang     = body.lang if body.lang in ("en", "hi") else "hi"
    user_msg = body.message.strip()
    if not user_msg:
        raise HTTPException(400, "Empty message")

    history  = get_history("voice", lang)
    messages = [{"role": "system", "content": VOICE_SYSTEM[lang]}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp  = await client.post(
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
            data  = resp.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply:
                reply = "Sorry, I could not process that." if lang == "en" else "क्षमा करें, अभी उत्तर नहीं दे सकता।"

        append_history("voice", lang, user_msg, reply)
        count = len(get_history("voice", lang)) // 2
        return {"reply": reply, "history_count": count}

    except httpx.ConnectError:
        raise HTTPException(503, "Cannot connect to Ollama Cloud. Check your API key and network.")
    except Exception as e:
        raise HTTPException(500, str(e))
