"""
assistant/app/router.py
────────────────────────────────────────────────────────────────
Drop this router into your main FastAPI app like:

    from assistant.app.router import router as assistant_router
    app.include_router(assistant_router, prefix="/assistant")

All routes live under /assistant/...
Static files are mounted at /assistant/static
History is stored in  assistant/data/history.json
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

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent.parent          # .../assistant/
HISTORY_FILE = BASE_DIR / "data" / "history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Jinja2 ─────────────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ── Router ─────────────────────────────────────────────────────────────────────
router = APIRouter()

# ── Ollama Config ──────────────────────────────────────────────────────────────
CLOUD_KEY   = os.getenv("OLLAMA_CLOUD_KEY", "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d")
CLOUD_URL   = "https://ollama.com/v1/chat/completions"
CLOUD_MODEL = "gemma3:12b"
OLLAMA_CHAT = CLOUD_URL  # for backward compatibility, but using cloud
MODEL       = CLOUD_MODEL
MAX_PAIRS   = 10   # history pairs kept per mode+lang

# ── System Prompts (per language) ──────────────────────────────────────────────
CHAT_SYSTEM = {
    "hi": (
        "आप Kisan AI हैं, एक विशेषज्ञ भारतीय कृषि विज्ञानी और खेती सलाहकार।\n"
        "नियम:\n"
        "1. हमेशा हिंदी में जवाब दें।\n"
        "2. विस्तृत और सहायक उत्तर दें — कारण, समाधान और बचाव स्पष्ट करें।\n"
        "3. जहाँ उचित हो वहाँ बुलेट पॉइंट या क्रमांकित चरणों का उपयोग करें।\n"
        "4. विशिष्ट उत्पाद नाम, मात्रा या तकनीक बताएं।\n"
        "5. केवल वैज्ञानिक रूप से सटीक कृषि सलाह दें।\n"
        "6. पिछली बातचीत याद रखें।"
    ),
    "en": (
        "You are Kisan AI, an expert Indian Agronomist and farming advisor.\n"
        "Rules:\n"
        "1. Always respond in English.\n"
        "2. Give thorough, detailed responses — explain cause, solution, and prevention clearly.\n"
        "3. Use bullet points or numbered steps when listing advice.\n"
        "4. Include specific product names, dosages, or techniques where relevant.\n"
        "5. Only provide scientifically accurate farming advice. No filler phrases.\n"
        "6. Remember previous messages in the conversation for context."
    ),
}

VOICE_SYSTEM = {
    "hi": (
        "आप Kisan AI हैं, एक विशेषज्ञ भारतीय कृषि विज्ञानी।\n"
        "नियम:\n"
        "1. हमेशा हिंदी में जवाब दें।\n"
        "2. बहुत संक्षिप्त रहें — केवल 1-2 वाक्य। आपका जवाब बोला जाएगा।\n"
        "3. कोई बुलेट पॉइंट नहीं, कोई सूची नहीं, कोई मार्कडाउन नहीं। केवल सरल भाषा।\n"
        "4. सबसे जरूरी सलाह ही दें।\n"
        "5. पिछली बातचीत याद रखें।"
    ),
    "en": (
        "You are Kisan AI, an expert Indian Agronomist.\n"
        "Rules:\n"
        "1. Always respond in English.\n"
        "2. Be VERY brief — 1 to 2 sentences only. Your response will be spoken aloud.\n"
        "3. No bullet points, no lists, no markdown. Plain spoken language only.\n"
        "4. Give only the most essential piece of advice.\n"
        "5. Remember previous messages in the conversation for context."
    ),
}

# ── History Helpers ────────────────────────────────────────────────────────────
def _load_store() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Keys: "chat_hi", "chat_en", "voice_hi", "voice_en"
    return {}

def _save_store(store: dict):
    # Always write as UTF-8 — fixes charmap/codec errors with Hindi text
    HISTORY_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def _key(mode: str, lang: str) -> str:
    return f"{mode}_{lang}"

def get_history(mode: str, lang: str) -> list[dict]:
    return _load_store().get(_key(mode, lang), [])

def append_history(mode: str, lang: str, user_msg: str, ai_msg: str):
    store = _load_store()
    k = _key(mode, lang)
    history = store.get(k, [])
    history.append({"role": "user",      "content": user_msg, "ts": datetime.now().isoformat()})
    history.append({"role": "assistant", "content": ai_msg,   "ts": datetime.now().isoformat()})
    store[k] = history[-(MAX_PAIRS * 2):]
    _save_store(store)

def clear_history(mode: str, lang: str):
    store = _load_store()
    store[_key(mode, lang)] = []
    _save_store(store)

def history_count(mode: str, lang: str) -> int:
    return len(get_history(mode, lang)) // 2


# ── Pydantic Models ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    lang: str = "en"   # "hi" | "en"

class VoiceRequest(BaseModel):
    message: str
    lang: str = "hi"

class ClearRequest(BaseModel):
    mode: str   # "chat" | "voice"
    lang: str   # "hi"  | "en"


# ── Page ───────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def assistant_page(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request})


# ── History API ────────────────────────────────────────────────────────────────
@router.get("/api/history/{mode}/{lang}")
async def api_get_history(mode: str, lang: str):
    if mode not in ("chat", "voice") or lang not in ("hi", "en"):
        raise HTTPException(400, "Invalid mode or lang")
    h = get_history(mode, lang)
    return {"mode": mode, "lang": lang, "history": h, "count": len(h) // 2}

@router.post("/api/history/clear")
async def api_clear_history(body: ClearRequest):
    if body.mode not in ("chat", "voice") or body.lang not in ("hi", "en"):
        raise HTTPException(400, "Invalid mode or lang")
    clear_history(body.mode, body.lang)
    return {"ok": True}


# ── STREAMING CHAT ─────────────────────────────────────────────────────────────
@router.post("/api/chat/stream")
async def chat_stream(body: ChatRequest):
    lang = body.lang if body.lang in ("hi", "en") else "en"
    user_msg = body.message.strip()
    if not user_msg:
        raise HTTPException(400, "Empty message")

    history  = get_history("chat", lang)
    system   = CHAT_SYSTEM[lang]
    messages = [{"role": "system", "content": system}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    async def token_generator() -> AsyncGenerator[str, None]:
        full_reply = ""
        try:
            async with httpx.AsyncClient(timeout=90) as client:
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
                            # ensure_ascii=False so Hindi tokens pass through correctly
                            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0)

                        # Stop when finish_reason is set
                        finish = (chunk.get("choices") or [{}])[0].get("finish_reason")
                        if finish == "stop":
                            break

            append_history("chat", lang, user_msg, full_reply)
            count = history_count("chat", lang)
            yield f"data: {json.dumps({'done': True, 'history_count': count}, ensure_ascii=False)}\n\n"

        except httpx.ConnectError:
            yield f"data: {json.dumps({'error': 'Cannot connect to Ollama Cloud. Check your API key and network.'})}\n\n"
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'error': 'Request timed out. Try again.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── VOICE ──────────────────────────────────────────────────────────────────────
@router.post("/api/voice")
async def voice_query(body: VoiceRequest):
    lang = body.lang if body.lang in ("hi", "en") else "hi"
    user_msg = body.message.strip()
    if not user_msg:
        raise HTTPException(400, "Empty message")

    history  = get_history("voice", lang)
    system   = VOICE_SYSTEM[lang]
    messages = [{"role": "system", "content": system}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        async with httpx.AsyncClient(timeout=30) as client:
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
            data  = resp.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not reply:
                reply = "Sorry, unable to process right now." if lang == "en" else "अभी जवाब नहीं मिल सका।"

        append_history("voice", lang, user_msg, reply)
        return {"reply": reply, "history_count": history_count("voice", lang)}

    except httpx.ConnectError:
        raise HTTPException(503, "Cannot connect to Ollama Cloud. Check your API key and network.")
    except Exception as e:
        raise HTTPException(500, str(e))
