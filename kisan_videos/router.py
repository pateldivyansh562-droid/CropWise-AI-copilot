"""
kisan_videos/router.py
──────────────────────────────────────────────────────────────
YouTube farming video search router for Kisan AI.

Mount in main.py:
    from kisan_videos.router import router as videos_router
    app.include_router(videos_router, prefix="/videos", tags=["Videos"])
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import requests
import json
import re

router = APIRouter()

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ── Normalise query (Hindi / Hinglish → English keywords) ──────────────────
MAPPING = {
    "गेहूं": "wheat",   "gehu": "wheat",
    "टमाटर": "tomato",  "tamatar": "tomato",
    "आलू": "potato",    "aloo": "potato",
    "खेती": "farming",  "kheti": "farming",
    "बीमारी": "disease","bimari": "disease",
    "धान": "rice",      "dhan": "rice",
    "मक्का": "maize",   "makka": "maize",
    "सरसों": "mustard", "sarson": "mustard",
    "प्याज": "onion",   "pyaaz": "onion",
    "मिट्टी": "soil",   "mitti": "soil",
    "खाद": "fertilizer","khaad": "fertilizer",
    "सिंचाई": "irrigation", "sinchai": "irrigation",
}

SUFFIX = "farming agriculture India Hindi practical tips"

def normalize_query(q: str) -> str:
    q_lower = q.lower()
    extras = []
    for k, v in MAPPING.items():
        if k in q_lower:
            extras.append(v)
    return q + (" " + " ".join(extras) if extras else "") + " " + SUFFIX


# ── Duration helpers ────────────────────────────────────────────────────────
def duration_to_seconds(duration: str) -> int:
    try:
        parts = list(map(int, duration.split(":")))
        if len(parts) == 3:
            h, m, s = parts
        else:
            h, m, s = 0, parts[0], parts[1]
        return h * 3600 + m * 60 + s
    except Exception:
        return 0


def format_duration(duration: str) -> str:
    """Return a readable label like '12 min' or '1 hr 4 min'."""
    secs = duration_to_seconds(duration)
    h, rem = divmod(secs, 3600)
    m, _ = divmod(rem, 60)
    if h:
        return f"{h} hr {m} min"
    return f"{m} min"


# ── Core scraper ─────────────────────────────────────────────────────────────
def get_videos(query: str, limit: int = 6, min_seconds: int = 120) -> list[dict]:
    """
    Scrape YouTube search results and return structured video dicts.
    Returns up to `limit` videos that are at least `min_seconds` long.
    """
    url = "https://www.youtube.com/results"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        res = requests.get(url, params={"search_query": query}, headers=headers, timeout=10)
        html = res.text
    except Exception as e:
        return []

    match = re.search(r"var ytInitialData = (.*?);</script>", html)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
        contents = (
            data["contents"]
            ["twoColumnSearchResultsRenderer"]
            ["primaryContents"]
            ["sectionListRenderer"]
            ["contents"]
        )
    except (KeyError, json.JSONDecodeError):
        return []

    videos = []

    for section in contents:
        if "itemSectionRenderer" not in section:
            continue
        for item in section["itemSectionRenderer"]["contents"]:
            if "videoRenderer" not in item:
                continue
            v = item["videoRenderer"]
            try:
                vid_id   = v["videoId"]
                title    = v["title"]["runs"][0]["text"]
                duration = v.get("lengthText", {}).get("simpleText", "0:00")
                channel  = v.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown")
                views    = v.get("viewCountText", {}).get("simpleText", "")
                thumb    = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                if duration_to_seconds(duration) < min_seconds:
                    continue

                videos.append({
                    "id":       vid_id,
                    "title":    title,
                    "duration": duration,
                    "duration_label": format_duration(duration),
                    "channel":  channel,
                    "views":    views,
                    "thumb":    thumb,
                    "url":      f"https://www.youtube.com/watch?v={vid_id}",
                    "embed":    f"https://www.youtube.com/embed/{vid_id}",
                })
            except Exception:
                continue

            if len(videos) >= limit:
                return videos

    return videos


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def videos_home(request: Request):
    """Landing page with search form."""
    return templates.TemplateResponse("index.html", {"request": request, "results": [], "query": ""})


@router.get("/search", response_class=HTMLResponse)
async def videos_search(
    request: Request,
    q: str = Query(default="", description="Farming query in Hindi or English"),
):
    """Search and return video results page."""
    results = []
    error   = None
    smart_q = ""

    if q.strip():
        smart_q = normalize_query(q.strip())
        results = get_videos(smart_q)
        if not results:
            error = "No videos found. Try a different query."

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "results": results, "query": q, "smart_query": smart_q, "error": error},
    )


@router.get("/api/search")
async def api_search(
    q: str = Query(..., description="Farming query"),
    limit: int = Query(default=6, ge=1, le=20),
    min_sec: int = Query(default=120, ge=0),
):
    """JSON API endpoint for programmatic access."""
    if not q.strip():
        return {"videos": [], "query": q, "smart_query": ""}
    smart_q = normalize_query(q.strip())
    videos  = get_videos(smart_q, limit=limit, min_seconds=min_sec)
    return {"videos": videos, "query": q, "smart_query": smart_q, "count": len(videos)}