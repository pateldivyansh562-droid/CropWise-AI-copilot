"""
mandi_prices/utils.py
All business logic extracted from the standalone mandi.py script.
"""

import re
import requests
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from geopy.distance import geodesic

API_KEY     = "579b464db66ec23bdd000001bdccc21bf0eb426f7bcfb88428e0475f"
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

HINDI_MAP = {
    "gehun":"Wheat","gehu":"Wheat","wheat":"Wheat",
    "chawal":"Rice","rice":"Rice","dhan":"Paddy","paddy":"Paddy",
    "tamatar":"Tomato","tomato":"Tomato",
    "aloo":"Potato","potato":"Potato",
    "pyaz":"Onion","onion":"Onion","piyaz":"Onion",
    "sarso":"Mustard","mustard":"Mustard","sarson":"Mustard",
    "makka":"Maize","maize":"Maize","corn":"Maize",
    "moong":"Moong","urad":"Black Gram","arhar":"Arhar (Tur)",
    "chana":"Gram","gram":"Gram",
    "gajar":"Carrot","carrot":"Carrot",
    "gobhi":"Cauliflower","cauliflower":"Cauliflower",
    "matar":"Peas","peas":"Peas",
    "palak":"Spinach","spinach":"Spinach",
    "bhindi":"Ladies Finger","ladyfinger":"Ladies Finger","okra":"Ladies Finger",
    "baingan":"Brinjal","brinjal":"Brinjal","eggplant":"Brinjal",
    "lauki":"Bottle Gourd","bottle gourd":"Bottle Gourd",
    "kaddu":"Pumpkin","pumpkin":"Pumpkin",
    "adrak":"Ginger","ginger":"Ginger",
    "lahsun":"Garlic","garlic":"Garlic",
    "mirch":"Chilli","chilli":"Chilli","chili":"Chilli",
    "soyabean":"Soyabean","soybean":"Soyabean",
    "ganna":"Sugarcane","sugarcane":"Sugarcane",
    "kela":"Banana","banana":"Banana",
    "aam":"Mango","mango":"Mango",
    "seb":"Apple","apple":"Apple",
    "karela":"Bitter Gourd","bitter gourd":"Bitter Gourd",
    "sem":"Beans","beans":"Beans",
    "methi":"Fenugreek","fenugreek":"Fenugreek",
    "dhania":"Coriander","coriander":"Coriander",
    "haldi":"Turmeric","turmeric":"Turmeric",
    "torai":"Ridgeguard","turai":"Ridgeguard",
}


def normalize_crop(name: str) -> str:
    return HINDI_MAP.get(name.strip().lower(), name.strip().title())


def reverse_geocode(lat: float, lng: float) -> dict:
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lng, "format": "json", "zoom": 14, "addressdetails": 1},
            headers={"User-Agent": "KisanMandiAI/3.0"},
            timeout=10,
        ).json()
        addr     = r.get("address", {})
        locality = (addr.get("village") or addr.get("suburb") or addr.get("neighbourhood")
                    or addr.get("hamlet") or addr.get("town") or addr.get("city_district")
                    or addr.get("city") or "")
        district = addr.get("state_district") or addr.get("county") or addr.get("city") or ""
        state    = addr.get("state", "")
        tehsil   = addr.get("county") or addr.get("town") or ""
        return {"locality": locality, "tehsil": tehsil, "district": district, "state": state}
    except Exception:
        return {"locality": "", "tehsil": "", "district": "", "state": "Uttar Pradesh"}


def get_nearby_mandis_osm(lat: float, lng: float, radius_km: int = 50) -> list[dict]:
    r_m = int(radius_km * 1000)
    q = f"""
[out:json][timeout:40];
(
  node["amenity"="marketplace"](around:{r_m},{lat},{lng});
  way["amenity"="marketplace"](around:{r_m},{lat},{lng});
  relation["amenity"="marketplace"](around:{r_m},{lat},{lng});
  node["shop"="market"](around:{r_m},{lat},{lng});
  way["shop"="market"](around:{r_m},{lat},{lng});
  node["marketplace"="yes"](around:{r_m},{lat},{lng});
  node["landuse"="commercial"]["name"~"[Mm]andi|मंडी|बाज़ार|बाजार"](around:{r_m},{lat},{lng});
  node["name"~"[Mm]andi|मंडी|[Ss]abzi|सब्जी|[Kk]rishi|कृषि|[Aa]naaj|अनाज|[Kk]isaan|किसान|[Aa]pmc|[Aa][Pp][Mm][Cc]|[Ff]arm|[Mm]arket|बाज़ार|बाजार"](around:{r_m},{lat},{lng});
  way["name"~"[Mm]andi|मंडी|[Ss]abzi|सब्जी|[Kk]rishi|कृषि|[Aa]naaj|अनाज|[Aa]pmc|[Ff]arm|बाज़ार"](around:{r_m},{lat},{lng});
);
out center body;
"""
    results = []
    try:
        resp = requests.get(
            "https://overpass-api.de/api/interpreter",
            params={"data": q}, timeout=35,
        )
        if resp.status_code != 200:
            raise Exception("OSM fail")
        for el in resp.json().get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name", "").strip()
            if not name or len(name) < 3:
                continue
            if name.lower() in {"yes", "no", "unknown", "market", "mandi", "shop"}:
                continue
            elat = el.get("lat") or el.get("center", {}).get("lat")
            elon = el.get("lon") or el.get("center", {}).get("lon")
            if not elat or not elon:
                continue
            dist = geodesic((lat, lng), (elat, elon)).km
            kind = (tags.get("amenity") or tags.get("shop") or
                    tags.get("marketplace") or tags.get("landuse") or "Mandi")
            results.append({
                "name":        name,
                "lat":         elat,
                "lng":         elon,
                "distance_km": round(dist, 1),
                "type":        kind,
                "address":     tags.get("addr:city", "") or tags.get("addr:district", ""),
            })
    except Exception:
        pass

    seen, unique = {}, []
    for m in sorted(results, key=lambda x: x["distance_km"]):
        k = re.sub(r'\s+', ' ', m["name"].lower().strip())
        if k not in seen:
            seen[k] = True
            unique.append(m)

    if len(unique) < 3 and radius_km < 100:
        return get_nearby_mandis_osm(lat, lng, radius_km + 50)

    return unique[:15]


def fetch_data(commodity: str, state: str = "", district: str = "") -> pd.DataFrame:
    url  = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
    base = {
        "api-key": API_KEY, "format": "json",
        "limit": 500, "filters[commodity]": commodity,
    }

    def try_fetch(extra: dict) -> pd.DataFrame:
        try:
            r    = requests.get(url, params={**base, **extra}, timeout=15)
            recs = r.json().get("records", [])
            return pd.DataFrame(recs) if recs else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    if district and state:
        df = try_fetch({"filters[state]": state, "filters[district]": district})
        if not df.empty:
            return df
    if state:
        df = try_fetch({"filters[state]": state})
        if not df.empty:
            return df
    return try_fetch({})


def predict_price(prices: list) -> float:
    arr = np.array(prices, dtype=float)
    if len(arr) < 3:
        return float(arr[-1]) if len(arr) else 0.0
    m = RandomForestRegressor(n_estimators=100, random_state=42)
    m.fit(np.arange(len(arr)).reshape(-1, 1), arr)
    return float(m.predict([[len(arr)]])[0])


def get_market_prices(df: pd.DataFrame) -> list[dict]:
    df = df.copy()
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    df = df.dropna(subset=["modal_price", "market"])
    out = []
    for mkt, grp in df.groupby("market"):
        if "arrival_date" in grp.columns:
            grp = grp.sort_values("arrival_date")
        prices  = grp["modal_price"].tolist()
        current = float(prices[-1])
        pred    = predict_price(prices)
        out.append({
            "market":          mkt,
            "district":        str(grp.iloc[-1].get("district", "") or ""),
            "state":           str(grp.iloc[-1].get("state", "") or ""),
            "current_price":   round(current, 2),
            "predicted_price": round(pred, 2),
            "change_pct":      round(((pred - current) / current) * 100, 1) if current else 0,
            "is_nearby":       False,
        })
    return sorted(out, key=lambda x: x["current_price"], reverse=True)


def get_trend(df: pd.DataFrame, market: str = None) -> list[dict]:
    df = df.copy()
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    sub = df[df["market"] == market].dropna(subset=["modal_price"]) if market else pd.DataFrame()
    if sub.empty:
        sub = df.dropna(subset=["modal_price"])
    if "arrival_date" in sub.columns:
        sub = sub.sort_values("arrival_date")
    return [
        {"i": i, "price": float(r["modal_price"])}
        for i, (_, r) in enumerate(sub.tail(14).iterrows())
    ]


def tag_nearby_markets(markets: list[dict], osm_mandis: list[dict], user_district: str) -> list[dict]:
    user_dist_lower = user_district.lower().strip() if user_district else ""
    osm_names = [m["name"].lower() for m in osm_mandis]

    def name_overlap(a: str, b: str) -> bool:
        a_w    = set(re.sub(r'[^a-z0-9 ]', '', a.lower()).split())
        b_w    = set(re.sub(r'[^a-z0-9 ]', '', b.lower()).split())
        common = (a_w & b_w) - {"market", "mandi", "sabzi", "the", "and", "of", "krishi"}
        return len(common) > 0

    for mkt in markets:
        mkt_dist       = (mkt.get("district") or "").lower().strip()
        district_match = bool(
            user_dist_lower and mkt_dist and
            (user_dist_lower in mkt_dist or mkt_dist in user_dist_lower)
        )
        osm_match       = any(name_overlap(mkt["market"], n) for n in osm_names)
        mkt["is_nearby"] = district_match or osm_match
    return markets
