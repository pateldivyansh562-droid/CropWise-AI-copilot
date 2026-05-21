"""
mandi_prices/router.py
──────────────────────────────────────────────────────────────
Mount in main.py:
    from mandi_prices.router import router as mandi_router
    app.include_router(mandi_router, prefix="/mandi", tags=["Mandi"])
"""

from pathlib import Path
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from mandi_prices.utils import (
    normalize_crop, reverse_geocode, get_nearby_mandis_osm,
    fetch_data, get_market_prices, get_trend, tag_nearby_markets,
)
import pandas as pd
import numpy as np

BASE_DIR  = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router    = APIRouter()


# ── Pages ───────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def mandi_page(request: Request):
    return templates.TemplateResponse("mandi.html", {"request": request})


# ── API: reverse geocode ───────────────────────────────────────────────────────
@router.get("/api/geocode")
async def api_geocode(lat: float = Query(...), lng: float = Query(...)):
    return reverse_geocode(lat, lng)


# ── API: full analysis ─────────────────────────────────────────────────────────
@router.get("/api/analyze")
async def api_analyze(
    crop:     str   = Query(...),
    lat:      float = Query(28.6692),
    lng:      float = Query(77.4538),
    state:    str   = Query(""),
    district: str   = Query(""),
):
    from mandi_prices.utils import predict_price

    commodity = normalize_crop(crop)
    df        = fetch_data(commodity, state.strip(), district.strip())

    if df.empty:
        return JSONResponse(status_code=404, content={
            "error_en": f"No data found for '{commodity}'. Please try another crop name.",
            "error_hi": f"'{commodity}' का डेटा नहीं मिला। कृपया दूसरा नाम आज़माएं।",
        })

    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    df = df.dropna(subset=["modal_price"])
    if df.empty:
        return JSONResponse(status_code=404, content={
            "error_en": "Price data is currently unavailable.",
            "error_hi": "मूल्य डेटा अभी उपलब्ध नहीं है।",
        })

    prices            = df["modal_price"].tolist()
    overall_current   = round(float(np.median(prices)), 2)
    overall_predicted = round(predict_price(prices), 2)
    change_pct        = round(((overall_predicted - overall_current) / overall_current) * 100, 1) if overall_current else 0
    decision          = "WAIT" if overall_predicted > overall_current else "SELL"

    markets    = get_market_prices(df)
    nearby_osm = get_nearby_mandis_osm(lat, lng)
    markets    = tag_nearby_markets(markets, nearby_osm, district)
    best       = markets[0] if markets else None

    nearby_markets  = [m for m in markets if m["is_nearby"]]
    other_markets   = [m for m in markets if not m["is_nearby"]]
    ordered_markets = nearby_markets + other_markets

    trend = get_trend(df, best["market"] if best else None)

    return {
        "commodity":              commodity,
        "overall_current":        overall_current,
        "overall_predicted":      overall_predicted,
        "change_pct":             change_pct,
        "decision":               decision,
        "best_market":            best,
        "markets":                ordered_markets[:30],
        "nearby_markets_count":   len(nearby_markets),
        "nearby_osm":             nearby_osm,
        "trend":                  trend,
        "total_records":          len(df),
        "data_scope":             district or state or "National",
    }
