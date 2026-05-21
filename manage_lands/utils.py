"""
manage_lands/utils.py  — v2 (accurate, deterministic, stage-aware)
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

WEATHER_API_KEY = "21cf7dce8403e3bac30aef6d7bda0a4c"
OLLAMA_URL      = "https://ollama.com/v1/chat/completions"
MODEL           = "gemma3:12b"
CLOUD_KEY       = "4ef5f111adcc4d5da56cdb9847927b33.6Wv_694o5MQGUJnpS0IRUW5d"
LANDS_FILE      = Path(__file__).parent / "data" / "lands.json"
LANDS_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── Lands storage ──────────────────────────────────────────────────────────────
def load_lands() -> dict:
    if LANDS_FILE.exists():
        try:
            return json.loads(LANDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_lands(data: dict):
    LANDS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_land(land_id: str) -> dict | None:
    return load_lands().get(land_id)

def upsert_land(land_id: str, land: dict):
    data = load_lands()
    data[land_id] = land
    save_lands(data)

def delete_land(land_id: str):
    data = load_lands()
    data.pop(land_id, None)
    save_lands(data)


# ── Weather ────────────────────────────────────────────────────────────────────
def get_live_weather_forecast(api_key: str = WEATHER_API_KEY) -> dict:
    try:
        geo      = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = geo["loc"].split(",")
        city     = geo.get("city", "Unknown")
        resp     = requests.get(
            "http://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=8,
        )
        wd = resp.json()
        if resp.status_code != 200:
            return {"error": wd.get("message", "Weather API error"), "city": city, "forecast": []}

        # Group all 3-hour slots by date → pick the best representative slot per day
        from collections import defaultdict
        daily: dict[str, list] = defaultdict(list)
        for entry in wd["list"]:
            date_key = entry["dt_txt"].split(" ")[0]
            daily[date_key].append(entry)

        forecast = []
        for date_key in sorted(daily.keys())[:5]:
            slots = daily[date_key]
            # Use midday slot if available, else first slot
            mid = next((s for s in slots if "12:00" in s["dt_txt"]), slots[0])
            total_rain = sum(s.get("rain", {}).get("3h", 0) for s in slots)
            forecast.append({
                "date":     date_key,
                "temp":     round(mid["main"]["temp"], 1),
                "temp_min": round(min(s["main"]["temp_min"] for s in slots), 1),
                "temp_max": round(max(s["main"]["temp_max"] for s in slots), 1),
                "feels":    round(mid["main"]["feels_like"], 1),
                "humidity": mid["main"]["humidity"],
                "desc":     mid["weather"][0]["description"].capitalize(),
                "icon":     mid["weather"][0]["icon"],
                "wind":     mid["wind"]["speed"],
                "rain":     round(total_rain, 1),          # total for the day
                "clouds":   mid.get("clouds", {}).get("all", 0),
            })
        return {"city": city, "lat": lat, "lon": lon, "forecast": forecast, "error": None}
    except Exception as e:
        return {"error": str(e), "city": "Unknown", "forecast": []}


# ── Time helpers ───────────────────────────────────────────────────────────────
def _days_since(date_str: str) -> int | None:
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return (datetime.now() - d).days
    except ValueError:
        return None

def _watering_freq_days(freq_str: str) -> int | None:
    mapping = {
        "roz": 1, "daily": 1,
        "2 din mein": 2, "every 2 days": 2,
        "3 din mein": 3, "every 3 days": 3,
        "hafte mein": 7, "weekly": 7,
        "bi-weekly": 14,
        "baarish par nirbhar": None, "rain-fed": None, "baarish par": None,
    }
    if not freq_str:
        return None
    return mapping.get(freq_str.strip().lower())


# ── Crop stage ─────────────────────────────────────────────────────────────────
def _crop_stage(days: int | None, crop: str) -> dict:
    """
    Returns a dict with:
      stage      : short stage name
      description: plain-language description
      key_tasks  : list of agronomic tasks that are relevant at this stage
                   (does NOT include watering — handled separately)
    """
    if days is None:
        return {"stage": "unknown", "description": "Unknown stage", "key_tasks": []}

    c = crop.lower()

    # ── WHEAT ─────────────────────────────────────────────────────────────────
    if any(x in c for x in ["wheat", "gehun", "गेहूं", "गेहूँ"]):
        if days < 15:
            return {
                "stage": "germination",
                "description": "Seeds are germinating, seedlings just emerging from soil.",
                "key_tasks": [
                    "Check soil moisture daily — seedlings die if the topsoil dries out.",
                    "Watch for damping-off fungal disease; apply copper-based fungicide if seedlings collapse.",
                    "Keep the field free of weeds at this early stage.",
                ]
            }
        if days < 40:
            return {
                "stage": "tillering",
                "description": "Crop is branching out; tillers forming. This stage determines yield potential.",
                "key_tasks": [
                    "Apply first dose of nitrogen fertilizer (urea ~65 kg/acre) if not done at sowing.",
                    "Scout for aphids and armyworm on the leaves; spray Chlorpyrifos if infestation >5%.",
                    "Remove weeds manually or apply pre-emergence herbicide (Isoproturon 75 WP).",
                ]
            }
        if days < 80:
            return {
                "stage": "jointing",
                "description": "Stem nodes are forming and elongating. Crop needs maximum nutrients now.",
                "key_tasks": [
                    "Apply second nitrogen split dose (urea ~30 kg/acre) at jointing.",
                    "Spray potassium nitrate (0.5%) if leaves show yellowing/tip burn.",
                    "Monitor for yellow rust (Puccinia striiformis) — yellow stripes on leaves. Spray Propiconazole if found.",
                    "Do NOT disturb the soil around roots at this stage.",
                ]
            }
        if days < 110:
            return {
                "stage": "heading",
                "description": "Ears emerging from the boot. Critical stage — stress here directly reduces grain count.",
                "key_tasks": [
                    "Ensure irrigation is available — heading is the most water-sensitive stage.",
                    "Spray micronutrient mix (zinc sulphate 0.5%) if leaves are pale.",
                    "Watch for powdery mildew — white powdery coating on leaves. Spray Hexaconazole.",
                    "Keep birds away from the field at heading.",
                ]
            }
        if days < 130:
            return {
                "stage": "grain_filling",
                "description": "Grains are filling up with starch. Yield is being determined day by day.",
                "key_tasks": [
                    "This is the LAST irrigation — do a light watering only if humidity is very low.",
                    "Avoid any heavy spray or mechanical disturbance — grains can shatter.",
                    "Watch for loose smut (black powdery ears). Remove and destroy affected ears immediately.",
                    "Plan for harvest logistics — arrange thresher/combine in advance.",
                ]
            }
        return {
            "stage": "maturity",
            "description": "Crop is mature or near harvest. Grains have hardened.",
            "key_tasks": [
                "Stop all irrigation immediately.",
                "Check grain moisture — harvest when moisture is 12–14% (leaves rustling, grain hard).",
                "Arrange harvesting equipment and labor well in advance to avoid lodging losses.",
                "Dry harvested grain in sun for 2–3 days before storage.",
            ]
        }

    # ── RICE / PADDY ──────────────────────────────────────────────────────────
    if any(x in c for x in ["rice", "chawal", "paddy", "धान"]):
        if days < 20:
            return {
                "stage": "nursery",
                "description": "Seedlings in nursery bed. Delicate stage requiring careful management.",
                "key_tasks": [
                    "Maintain 2–3 cm water level in the nursery bed.",
                    "Apply basal dose of DAP (20 kg per nursery bed) if not done.",
                    "Spray Carbendazim (0.1%) to prevent seedling blight.",
                    "Thin overcrowded seedlings so each has space to grow.",
                ]
            }
        if days < 50:
            return {
                "stage": "tillering",
                "description": "Transplanted seedlings establishing and producing tillers. Yield formation begins.",
                "key_tasks": [
                    "Maintain 5 cm standing water in the field at all times.",
                    "Apply first nitrogen top-dress (urea 25 kg/acre) 2 weeks after transplanting.",
                    "Weed the field — use Bispyribac-sodium herbicide or manual weeding.",
                    "Watch for stem borer — yellowing/dead heart in tillers. Apply Chlorantraniliprole.",
                ]
            }
        if days < 90:
            return {
                "stage": "panicle_initiation",
                "description": "Panicles (grain heads) beginning to form inside the stem — most critical stage.",
                "key_tasks": [
                    "Keep field flooded — any drought stress at this stage causes heavy yield loss.",
                    "Apply second urea dose (20 kg/acre) at panicle initiation.",
                    "Spray Tricyclazole (0.06%) for blast disease prevention if humid weather persists.",
                    "Scout for leafhoppers and brown plant hoppers — spray Imidacloprid if severe.",
                ]
            }
        if days < 115:
            return {
                "stage": "flowering",
                "description": "Flowers opening and pollination occurring. Temperature and humidity are critical.",
                "key_tasks": [
                    "Maintain 3–5 cm water level — do NOT let the field dry out.",
                    "Avoid spraying any pesticide during peak flowering hours (6–9 am).",
                    "If temperature >35°C during day, irrigate lightly to cool the canopy.",
                    "Watch for neck blast — gray lesion on neck of panicle. Spray Isoprothiolane immediately.",
                ]
            }
        return {
            "stage": "maturity",
            "description": "Grains filling and hardening. Preparing for harvest.",
            "key_tasks": [
                "Drain the field 10–15 days before expected harvest to let soil firm up.",
                "Check grain color — golden yellow = ready to harvest.",
                "Harvest when 80% of grains are straw-colored and hard.",
                "Dry harvested paddy to 14% moisture before milling or storage.",
            ]
        }

    # ── SUGARCANE ─────────────────────────────────────────────────────────────
    if any(x in c for x in ["sugarcane", "ganna", "गन्ना"]):
        if days < 30:
            return {
                "stage": "germination",
                "description": "Setts germinating underground. Soil moisture is critical.",
                "key_tasks": [
                    "Keep soil moist but not waterlogged — irrigate every 7 days.",
                    "Apply Atrazine herbicide (1 kg a.i./acre) for weed control before emergence.",
                    "Gap-fill any empty spots in the row with new setts within 3 weeks.",
                ]
            }
        if days < 120:
            return {
                "stage": "tillering",
                "description": "Shoots emerging and multiplying. Population establishment happening.",
                "key_tasks": [
                    "Apply nitrogen fertilizer (urea 50 kg/acre) split in 2 doses during this stage.",
                    "Earth up the base of the crop to support the growing stalks.",
                    "Watch for early shoot borer — apply Chlorpyrifos granules in the whorls.",
                    "Manual or chemical weeding between rows.",
                ]
            }
        if days < 270:
            return {
                "stage": "grand_growth",
                "description": "Rapid stalk elongation. This is when most of the cane biomass is produced.",
                "key_tasks": [
                    "Irrigate every 10–14 days — cane needs consistent water at this stage.",
                    "Apply potassium sulphate (25 kg/acre) to improve sugar content and stalk strength.",
                    "Trash mulching between rows helps conserve moisture and control weeds.",
                    "Scout for top borer and red rot — spray Indoxacarb if borer damage exceeds 5%.",
                    "Propping/staking may be needed if stalks lean after rains.",
                ]
            }
        return {
            "stage": "ripening",
            "description": "Sugar accumulating in the stalk. Management now determines juice quality.",
            "key_tasks": [
                "Stop nitrogen application completely — it reduces sugar content.",
                "Reduce irrigation frequency to once every 3–4 weeks to stress the crop for ripening.",
                "Apply ethephon (ripener) spray if recommended by the sugar mill.",
                "Arrange harvest booking with the nearest sugar mill early.",
            ]
        }

    # ── TOMATO ────────────────────────────────────────────────────────────────
    if any(x in c for x in ["tomato", "tamatar", "टमाटर"]):
        if days < 20:
            return {
                "stage": "seedling",
                "description": "Young seedlings establishing root system.",
                "key_tasks": [
                    "Water gently twice daily — do not let the seedbed dry out.",
                    "Harden seedlings by reducing shade 5–7 days before transplanting.",
                    "Apply starter fertilizer (DAP, 10 g/litre water) as a soil drench.",
                ]
            }
        if days < 45:
            return {
                "stage": "vegetative",
                "description": "Rapid leaf and stem growth. Foundation for a high-yielding plant.",
                "key_tasks": [
                    "Stake or cage plants before they fall over (>30 cm tall).",
                    "Apply 19:19:19 NPK fertilizer at 5 g/litre as foliar spray every 10 days.",
                    "Remove suckers (side shoots) in the leaf axils weekly.",
                    "Watch for leaf curl virus transmitted by whiteflies — apply yellow sticky traps.",
                ]
            }
        if days < 70:
            return {
                "stage": "flowering",
                "description": "Flowers appearing. Pollination determines fruit set — extremely critical.",
                "key_tasks": [
                    "Do NOT apply nitrogen-heavy fertilizer now — it promotes leaves over flowers.",
                    "Apply 0:52:34 (mono potassium phosphate) at 5 g/litre to boost fruit set.",
                    "Tap the stakes/cages gently in the morning to help pollination.",
                    "Spray Boron (0.1%) to prevent blossom drop.",
                    "Watch for early blight (brown concentric spots) — spray Mancozeb 75 WP.",
                ]
            }
        return {
            "stage": "fruiting",
            "description": "Fruits forming and sizing up. Quality management is key now.",
            "key_tasks": [
                "Apply SOP (sulphate of potash, 5 g/litre) every 10 days for color and firmness.",
                "Maintain consistent irrigation — irregular watering causes blossom-end rot and cracking.",
                "Scout for fruit borer — apply Spinosad at 0.3 ml/litre if eggs/larvae found.",
                "Remove diseased fruits immediately to prevent spread.",
                "Harvest when fruits start turning from green to light yellow/orange.",
            ]
        }

    # ── POTATO ────────────────────────────────────────────────────────────────
    if any(x in c for x in ["potato", "aloo", "आलू"]):
        if days < 20:
            return {
                "stage": "sprouting",
                "description": "Seed tubers sprouting; shoots pushing through soil.",
                "key_tasks": [
                    "Keep soil moist and loose — do not let a hard crust form on the surface.",
                    "Apply Mancozeb 75 WP as a preventive drench for early blight.",
                    "Check for cutworm damage at the base of emerging shoots.",
                ]
            }
        if days < 50:
            return {
                "stage": "vegetative",
                "description": "Leafy growth and canopy development. Plant is building energy reserves.",
                "key_tasks": [
                    "Earth up (hill) the rows — expose potato tubers to light and they turn green and toxic.",
                    "Apply second dose of nitrogen (urea 20 kg/acre).",
                    "Scout for late blight (water-soaked dark spots on leaves) — spray Cymoxanil+Mancozeb.",
                    "Aphid control is critical — they spread virus diseases. Spray Imidacloprid.",
                ]
            }
        if days < 80:
            return {
                "stage": "tuber_initiation",
                "description": "Tubers forming at stolon tips. This stage determines the number of tubers.",
                "key_tasks": [
                    "Reduce nitrogen, increase potassium (MOP 25 kg/acre) now.",
                    "Maintain steady soil moisture — uneven watering causes malformed tubers.",
                    "Continue earthing up if needed.",
                    "Preventive spray for late blight every 7–10 days in humid weather.",
                ]
            }
        return {
            "stage": "tuber_bulking",
            "description": "Tubers rapidly increasing in size and starch content.",
            "key_tasks": [
                "This is the last irrigation window — do a final watering then stop.",
                "Stop all nitrogen fertilizer to improve storage quality.",
                "Watch for late blight — destroy affected haulms (tops) immediately.",
                "When leaves start yellowing and dying back, cut the tops 2 weeks before harvest.",
                "Harvest when skin is set (does not peel easily when rubbed).",
            ]
        }

    # ── Generic fallback ───────────────────────────────────────────────────────
    if days < 20:
        return {
            "stage": "seedling",
            "description": "Early seedling establishment stage.",
            "key_tasks": ["Ensure consistent soil moisture.", "Remove any weeds around seedlings.", "Check for damping-off or seed rot."]
        }
    if days < 60:
        return {
            "stage": "vegetative",
            "description": "Active vegetative growth phase.",
            "key_tasks": ["Apply nitrogen fertilizer as per crop requirement.", "Weed the field.", "Scout for common pests and diseases."]
        }
    if days < 100:
        return {
            "stage": "reproductive",
            "description": "Flowering or reproductive stage.",
            "key_tasks": ["Avoid nitrogen application — shift to phosphorus/potassium.", "Ensure adequate water.", "Monitor for flower/pod borers."]
        }
    return {
        "stage": "maturity",
        "description": "Crop approaching maturity.",
        "key_tasks": ["Reduce irrigation.", "Prepare for harvest.", "Dry and store grain properly."]
    }


# ── Deterministic 5-day watering plan ─────────────────────────────────────────
def _build_watering_plan(
    days_since_watered: int | None,
    watering_freq_days: int | None,
    forecast: list[dict],
) -> list[dict]:
    """
    Returns a list of 5 dicts, one per forecast day:
      {
        "date": "YYYY-MM-DD",
        "should_water": bool,
        "skip_reason": str | None,   # reason to skip (rain / not yet due)
        "water_note": str | None,    # specific watering instruction if should_water
        "rain_mm": float,
      }

    KEY FIX: Each day is evaluated INDEPENDENTLY by projecting forward from the
    last watered date — not with a running counter that carries over.
    """
    plan = []

    for i, day in enumerate(forecast[:5]):
        rain_mm = day.get("rain", 0)
        date    = day["date"]
        result  = {"date": date, "should_water": False, "skip_reason": None,
                   "water_note": None, "rain_mm": rain_mm}

        # Rain-fed crop
        if watering_freq_days is None:
            if rain_mm > 0:
                result["skip_reason"] = f"Rain expected ({rain_mm}mm) — natural irrigation."
            else:
                result["skip_reason"] = "Rain-fed crop — only water if no rain for 4+ days."
            plan.append(result)
            continue

        # Unknown last watered date
        if days_since_watered is None:
            result["skip_reason"] = "Last watered date unknown — cannot schedule precisely."
            plan.append(result)
            continue

        # Project: how many days since last watered ON THIS particular day?
        days_since_on_this_day = days_since_watered + i

        # Is watering due on this day?
        # Due if: days_since_on_this_day is exactly a multiple of the frequency,
        # OR if we are overdue (first day only — i.e. today).
        is_due = (days_since_on_this_day % watering_freq_days == 0) or \
                 (i == 0 and days_since_on_this_day > watering_freq_days)

        if is_due:
            if rain_mm >= 5:
                result["skip_reason"] = (
                    f"Watering DUE today but significant rain forecast ({rain_mm}mm) — "
                    f"skip watering, rain will cover it."
                )
            elif rain_mm > 0:
                result["should_water"] = True
                result["water_note"] = (
                    f"Watering due. Light rain expected ({rain_mm}mm) — water the field "
                    f"but reduce the amount by half."
                )
            else:
                result["should_water"] = True
                result["water_note"] = (
                    f"Water the field today — {days_since_on_this_day} days since last watering, "
                    f"schedule is every {watering_freq_days} days. Water in the early morning (before 7 am)."
                )
        else:
            days_until_next = watering_freq_days - (days_since_on_this_day % watering_freq_days)
            result["skip_reason"] = f"No watering needed — next due in {days_until_next} day(s)."

        plan.append(result)

    return plan


# ── Weather context helpers ────────────────────────────────────────────────────
def _heat_stress_note(temp_max: float, crop: str) -> str | None:
    thresholds = {
        "wheat": 30, "gehun": 30, "गेहूं": 30,
        "rice": 35, "paddy": 35, "धान": 35,
        "tomato": 35, "टमाटर": 35,
        "potato": 28, "aloo": 28, "आलू": 28,
    }
    for key, threshold in thresholds.items():
        if key in crop.lower() and temp_max > threshold:
            return (
                f"⚠️ Heat stress risk: Temperature {temp_max}°C exceeds {threshold}°C threshold for {crop}. "
                f"Irrigate in the evening to cool soil; avoid spraying during midday."
            )
    return None

def _frost_risk_note(temp_min: float) -> str | None:
    if temp_min < 4:
        return (
            f"❄️ Frost risk: Minimum temperature {temp_min}°C — cover sensitive crops at night "
            f"with mulch or polythene sheets."
        )
    return None

def _high_humidity_note(humidity: int, crop: str) -> str | None:
    fungal_crops = ["wheat", "gehun", "rice", "paddy", "tomato", "potato", "aloo"]
    if humidity > 80 and any(x in crop.lower() for x in fungal_crops):
        return (
            f"🍄 High humidity ({humidity}%) — fungal disease risk is elevated. "
            f"Avoid wetting foliage; spray preventive fungicide if humidity stays high for 3+ days."
        )
    return None


# ── Main prompt builder ────────────────────────────────────────────────────────
def build_suggestion_prompt(land: dict, weather: dict, lang: str) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt).

    All deterministic facts (watering schedule, crop stage, weather alerts) are
    fully pre-computed here. The AI's ONLY job is to:
      1. Phrase each pre-computed task clearly in the right language.
      2. Add agronomic reasoning/context for the crop stage tasks.
      3. Write the summary and important_tip.
    The AI must NOT recalculate watering or override the pre-built schedule.
    """
    now   = datetime.now()
    today = now.strftime("%d %b %Y")
    crop  = land.get("crop_name", "Unknown crop")
    notes = land.get("notes", "").strip()
    city  = weather.get("city", "Unknown location")

    # ── Pre-compute all deterministic data ─────────────────────────────────────
    days_since_sowing  = _days_since(land.get("sowing_date", ""))
    days_since_watered = _days_since(land.get("last_watered", ""))
    watering_freq_days = _watering_freq_days(land.get("watering_freq", ""))
    stage_info         = _crop_stage(days_since_sowing, crop)
    forecast           = weather.get("forecast", [])
    watering_plan      = _build_watering_plan(days_since_watered, watering_freq_days, forecast)

    # ── Build per-day task lists ──────────────────────────────────────────────
    # Each day gets:
    #   - watering decision (from _build_watering_plan — deterministic)
    #   - weather-based alerts (heat, frost, humidity)
    #   - stage-appropriate agronomic tasks (only on Day 0 and Day 3 to avoid repetition)
    #   - spray restriction on rainy days

    per_day_data = []
    for i, day in enumerate(forecast[:5]):
        wp   = watering_plan[i]
        date = day["date"]
        temp_max  = day.get("temp_max", day.get("temp", 25))
        temp_min  = day.get("temp_min", day.get("temp", 15))
        humidity  = day.get("humidity", 60)
        rain_mm   = day.get("rain", 0)
        wind      = day.get("wind", 0)
        desc      = day.get("desc", "")

        fixed_tasks = []      # Deterministic tasks (AI must include these exactly)
        context_hints = []    # Hints for AI to elaborate on

        # 1. Watering (deterministic)
        if wp["should_water"]:
            fixed_tasks.append(f"WATER: {wp['water_note']}")
        else:
            context_hints.append(f"NO watering: {wp['skip_reason']}")

        # 2. Spray restriction on rainy/windy days
        if rain_mm >= 2:
            fixed_tasks.append(
                f"NO SPRAYING today — rain ({rain_mm}mm) will wash off any pesticide or fertilizer spray. "
                f"Reschedule to the next dry day."
            )
        elif wind > 5:
            fixed_tasks.append(
                f"CAUTION: High wind speed ({wind} m/s) — avoid spraying as it causes drift and waste. "
                f"Spray only in calm morning hours if absolutely necessary."
            )

        # 3. Weather stress alerts
        heat_note = _heat_stress_note(temp_max, crop)
        if heat_note:
            fixed_tasks.append(heat_note)

        frost_note = _frost_risk_note(temp_min)
        if frost_note:
            fixed_tasks.append(frost_note)

        humidity_note = _high_humidity_note(humidity, crop)
        if humidity_note:
            fixed_tasks.append(humidity_note)

        # 4. Stage-specific agronomic tasks — only inject on Day 0 (today) and Day 3
        #    to avoid the AI copy-pasting the same tasks every single day.
        stage_tasks_for_today = []
        if i == 0:
            stage_tasks_for_today = stage_info["key_tasks"]
            context_hints.append(
                f"CROP STAGE: {stage_info['stage']} — {stage_info['description']} "
                f"Recommend the following agronomic actions where relevant to today's weather: "
                + "; ".join(stage_info["key_tasks"])
            )
        elif i == 3 and stage_info["key_tasks"]:
            # On day 3, remind of any unfinished stage tasks
            context_hints.append(
                f"Follow-up on stage tasks if not completed on Day 0: "
                + "; ".join(stage_info["key_tasks"][:2])
            )

        per_day_data.append({
            "date":          date,
            "index":         i,
            "fixed_tasks":   fixed_tasks,
            "context_hints": context_hints,
            "weather_desc":  f"{desc}, {day['temp']}°C (min {temp_min}°C / max {temp_max}°C), humidity {humidity}%, rain {rain_mm}mm",
        })

    # ── Build the data block sent to the AI ───────────────────────────────────
    sowing_line = (
        f"Sown {days_since_sowing} days ago ({land.get('sowing_date','')}), "
        f"current stage: {stage_info['stage']} — {stage_info['description']}"
        if days_since_sowing is not None
        else "Sowing date not provided."
    )
    last_water_line = (
        f"Last watered: {land.get('last_watered','')} ({days_since_watered} days ago), "
        f"frequency: every {watering_freq_days} days."
        if days_since_watered is not None
        else "Last watered: Unknown."
    )

    days_block = ""
    for d in per_day_data:
        date_obj  = datetime.strptime(d["date"], "%Y-%m-%d")
        label     = (
            "TODAY"    if d["index"] == 0 else
            "TOMORROW" if d["index"] == 1 else
            date_obj.strftime("%A")
        )
        line = f"\n--- {label} ({d['date']}) | {d['weather_desc']} ---\n"
        if d["fixed_tasks"]:
            line += "  MANDATORY TASKS (include these verbatim in your output):\n"
            for t in d["fixed_tasks"]:
                line += f"    • {t}\n"
        if d["context_hints"]:
            line += "  CONTEXT / OPTIONAL ELABORATION:\n"
            for h in d["context_hints"]:
                line += f"    ℹ {h}\n"
        days_block += line

    # ── Day labels for JSON template ──────────────────────────────────────────
    day_labels_en = []
    day_labels_hi = []
    for i in range(5):
        date_obj   = now + timedelta(days=i)
        suffix_en  = f"{date_obj.strftime('%A')} {date_obj.strftime('%d %b')}"
        prefix_en  = "Today" if i == 0 else ("Tomorrow" if i == 1 else "")
        label_en   = (f"{prefix_en} ({suffix_en})" if prefix_en else suffix_en)

        suffix_hi  = date_obj.strftime("%d %b")
        prefix_hi  = "आज" if i == 0 else ("कल" if i == 1 else date_obj.strftime("%A"))
        label_hi   = f"{prefix_hi} ({suffix_hi})"

        day_labels_en.append(label_en)
        day_labels_hi.append(label_hi)

    # ── Prompts ────────────────────────────────────────────────────────────────
    if lang == "hi":
        day_json_template = "\n".join([
            f'    {{"day": "{l}", "tasks": ["<task1>", "<task2>"], "nothing_to_do": false}}'
            for l in day_labels_hi
        ])
        system = (
            "आप एक अनुभवी भारतीय कृषि विज्ञानी हैं जो precise, data-driven सलाह देते हैं।\n\n"
            "आपका काम:\n"
            "1. नीचे दिए गए MANDATORY TASKS को EXACTLY वैसे ही हर दिन की tasks list में शामिल करें — इन्हें बदलें नहीं, छोड़ें नहीं।\n"
            "2. CONTEXT hints के आधार पर उस दिन के मौसम के अनुसार 1-2 अतिरिक्त specific सलाह जोड़ें — लेकिन केवल अगर वो genuinely उस दिन के लिए relevant हो।\n"
            "3. अगर किसी दिन कोई MANDATORY TASK नहीं है और कोई genuine agronomic काम नहीं है, तो tasks खाली रखें और nothing_to_do: true करें।\n"
            "4. हर task SPECIFIC और actionable होना चाहिए — समय, मात्रा, और तरीका बताएं।\n"
            "5. हर दिन अलग-अलग tasks होने चाहिए — एक ही काम हर रोज़ repeat मत करें।\n"
            "6. सरल हिंदी में लिखें।\n\n"
            "ONLY इस exact JSON format में जवाब दें:\n"
            "{\n"
            '  "summary": "फसल की मौजूदा stage और स्थिति का 2-3 वाक्यों में सारांश",\n'
            '  "days": [\n'
            f"{day_json_template}\n"
            "  ],\n"
            '  "important_tip": "अभी की सबसे जरूरी एक actionable सलाह"\n'
            "}\n"
            "केवल valid JSON। कोई markdown, कोई explanation नहीं।"
        )
        user = (
            f"आज की तारीख: {today}\n"
            f"स्थान: {city}\n"
            f"फसल: {crop}\n"
            f"बुवाई की जानकारी: {sowing_line}\n"
            f"सिंचाई की जानकारी: {last_water_line}\n"
            f"किसान के नोट्स: {notes or 'कोई नहीं'}\n\n"
            f"5 दिन का डेटा:\n{days_block}\n\n"
            "ऊपर दिए MANDATORY TASKS को exact include करते हुए 5-दिन की योजना बनाएं।"
        )
    else:
        day_json_template = "\n".join([
            f'    {{"day": "{l}", "tasks": ["<task1>", "<task2>"], "nothing_to_do": false}}'
            for l in day_labels_en
        ])
        system = (
            "You are an experienced Indian agronomist providing precise, data-driven farm advice.\n\n"
            "Your job:\n"
            "1. Include ALL MANDATORY TASKS listed for each day EXACTLY as stated — do not omit or alter them.\n"
            "2. Based on the CONTEXT hints, add 1-2 additional specific agronomic tasks ONLY if they are "
            "genuinely needed that specific day given the crop stage and weather.\n"
            "3. If a day has no MANDATORY TASKS and no genuine agronomic need, leave tasks empty and set nothing_to_do: true.\n"
            "4. Every task must be SPECIFIC and ACTIONABLE — include timing, quantity, and method.\n"
            "5. Each day must have DIFFERENT tasks — do not repeat the same task across multiple days.\n"
            "6. Use simple language a farmer can understand.\n\n"
            "Respond ONLY in this exact JSON format:\n"
            "{\n"
            '  "summary": "2-3 sentence summary of the crop\'s current stage and condition",\n'
            '  "days": [\n'
            f"{day_json_template}\n"
            "  ],\n"
            '  "important_tip": "The single most important actionable advice right now"\n'
            "}\n"
            "Return only valid JSON. No markdown, no explanation, no code blocks."
        )
        user = (
            f"Today's date: {today}\n"
            f"Location: {city}\n"
            f"Crop: {crop}\n"
            f"Sowing info: {sowing_line}\n"
            f"Irrigation info: {last_water_line}\n"
            f"Farmer notes: {notes or 'None'}\n\n"
            f"5-day data:\n{days_block}\n\n"
            "Include ALL MANDATORY TASKS exactly as listed, then provide the 5-day plan."
        )

    return system, user