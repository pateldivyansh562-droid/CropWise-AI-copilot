"""
schemes/router.py
──────────────────────────────────────────────────────────────
Mount in main.py:
    from schemes.router import router as schemes_router
    app.include_router(schemes_router, prefix="/schemes", tags=["Schemes"])
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from schemes.schemes_data import get_all_schemes, get_scheme_by_id

CLOUD_KEY   = os.getenv("OLLAMA_CLOUD_KEY", "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d")
CLOUD_URL   = "https://ollama.com/v1/chat/completions"
CLOUD_MODEL = "gemma3:12b"

BASE_DIR  = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router    = APIRouter()


# ── Models ─────────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    scheme_id: str
    messages:  list[dict]   # [{"role": "user"/"assistant", "content": "..."}]
    lang:      str = "en"


# ── Streaming chat endpoint — BEFORE wildcard route ────────────────────────────
@router.post("/api/chat/stream")
async def chat_stream(body: ChatMessage):
    scheme = get_scheme_by_id(body.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    lang = body.lang if body.lang in ("en", "hi") else "en"

    if lang == "hi":
        system_prompt = f"""Aap ek sarkaari yojana sahayak hain jo sirf **{scheme['name_hi']} ({scheme['name']})** ke baare mein batate hain.

YOJANA KI JAANKARI:
- Naam: {scheme['name']} / {scheme['name_hi']}
- Shreni: {scheme['category_hi']}
- Vivaran: {scheme['description_hi']}
- Labh: {'; '.join(scheme['benefits_hi'])}
- Patrta: {'; '.join(scheme['eligibility_hi'])}
- Aavedan kaise karein: {'; '.join(scheme['how_to_apply_hi'])}
- Zaroori dastavez: {', '.join(scheme['documents'])}
- Adhikarik link: {scheme['official_link']}

VISTRIT JAANKARI:
{scheme['ai_context']}

NIYAM:
1. SIRF is yojana ke baare mein jawab dein. Doosri yojanaon ka zikar tab karen jab seedha sambandh ho.
2. Saral Hindi mein baat karein jo ek aam kisan samajh sake.
3. Jawab chhota aur kaam ka ho — 3-5 sentences ya bullet points.
4. Agar koi document, form ya link pooche to sahi jaankari dein.
5. Agar koi cheez aapko nahi pata, toh seedha kahein 'yeh jaankari mere paas nahi hai, {scheme['official_link']} par dekhein.'
6. Kisi bhi sthiti mein galat ya mann-ghadant jaankari mat dein."""
    else:
        system_prompt = f"""You are a helpful government scheme assistant who only answers questions about the **{scheme['name']}** scheme.

SCHEME INFORMATION:
- Name: {scheme['name']} ({scheme['name_hi']})
- Category: {scheme['category']}
- Description: {scheme['description']}
- Benefits: {'; '.join(scheme['benefits'])}
- Eligibility: {'; '.join(scheme['eligibility'])}
- How to Apply: {'; '.join(scheme['how_to_apply'])}
- Required Documents: {', '.join(scheme['documents'])}
- Official Link: {scheme['official_link']}

DETAILED CONTEXT:
{scheme['ai_context']}

RULES:
1. Answer ONLY questions about this scheme. Mention other schemes only when directly relevant.
2. Use simple language a farmer without much education can understand.
3. Keep answers concise and actionable — 3-5 sentences or bullet points.
4. If asked about documents, forms, or links — give accurate information.
5. If you don't know something specific, say 'I don't have that detail, please check {scheme['official_link']}'
6. Never make up or hallucinate information about eligibility, amounts, or dates."""

    # Build messages for Ollama Cloud
    messages = [{"role": "system", "content": system_prompt}]
    for msg in body.messages:
        if msg.get("role") in ("user", "assistant") and msg.get("content", "").strip():
            messages.append({"role": msg["role"], "content": msg["content"]})

    async def token_gen() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
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


# ── Pages — wildcard AFTER specific routes ─────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def schemes_list(request: Request):
    schemes = get_all_schemes()
    return templates.TemplateResponse("list.html", {
        "request": request,
        "schemes": schemes,
    })

@router.get("/{scheme_id}", response_class=HTMLResponse)
async def scheme_chat(request: Request, scheme_id: str):
    scheme = get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "scheme":  scheme,
    })