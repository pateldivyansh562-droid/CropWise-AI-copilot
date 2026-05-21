"""
crop_doctor/utils.py
"""

import base64
import requests

PLANT_ID_KEY = "MulWGVXHjpx8t6h0dLb4iWDDpf8E938goZVEPCVESWYboPxkm6"
PLANT_ID_URL = "https://api.plant.id/v3/health_assessment"

OLLAMA_URL = "https://ollama.com/v1/chat/completions"
MODEL      = "gemma3:12b"


def detect_disease(image_bytes: bytes) -> dict:
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "images": [b64],
            "health": "only",
        }
        headers = {
            "Api-Key":      PLANT_ID_KEY,
            "Content-Type": "application/json",
        }

        resp = requests.post(PLANT_ID_URL, json=payload, headers=headers, timeout=30)
        data = resp.json()

        # ✅ Plant.id returns 201 Created on success — accept both 200 and 201
        if resp.status_code not in (200, 201):
            return {
                "healthy": False, "disease_name": None, "probability": None,
                "description": None, "suggestions": [], "raw": data,
                "error": data.get("message", f"API error {resp.status_code}"),
            }

        suggestions_raw = (
            data.get("result", {})
                .get("disease", {})
                .get("suggestions", [])
        )

        suggestions = []
        for s in suggestions_raw[:5]:
            suggestions.append({
                "name":        s.get("name", "Unknown"),
                "probability": round(s.get("probability", 0) * 100, 1),
                "description": (s.get("details", {}) or {}).get("description", ""),
            })

        is_healthy = not suggestions or (suggestions[0]["probability"] < 15)

        if is_healthy:
            return {
                "healthy": True, "disease_name": None, "probability": None,
                "description": None, "suggestions": suggestions, "raw": data, "error": None,
            }

        top = suggestions[0]
        return {
            "healthy":      False,
            "disease_name": top["name"],
            "probability":  top["probability"],
            "description":  top["description"],
            "suggestions":  suggestions,
            "raw":          data,
            "error":        None,
        }

    except requests.exceptions.ConnectionError:
        return {
            "healthy": False, "disease_name": None, "probability": None,
            "description": None, "suggestions": [], "raw": {},
            "error": "Cannot reach Plant.id API. Check your internet connection.",
        }
    except Exception as e:
        return {
            "healthy": False, "disease_name": None, "probability": None,
            "description": None, "suggestions": [], "raw": {},
            "error": str(e),
        }


def build_disease_prompt(
    disease_name: str,
    probability: float,
    description: str,
    section: str,
    lang: str,
    crop_name: str = "",
) -> tuple[str, str]:

    crop_ctx = f" on {crop_name}" if crop_name else ""
    desc_ctx = f"\nDisease description from detection API: {description}" if description else ""

    base_facts = (
        f"Disease detected: {disease_name}{crop_ctx}\n"
        f"Detection confidence: {probability}%"
        f"{desc_ctx}"
    )

    SECTION_PROMPTS = {
        "overview": {
            "en": {
                "sys": (
                    "You are an expert plant pathologist and agricultural scientist.\n"
                    "Explain this crop disease in simple, clear language that a farmer can understand.\n"
                    "Cover: what this disease is, what the plant looks like when infected, "
                    "how quickly it spreads, and how serious it is.\n"
                    "Format: 3-4 short paragraphs. No jargon. Use bullet points for visual symptoms."
                ),
                "usr": f"{base_facts}\n\nExplain this disease — what it is, visual symptoms, and severity.",
            },
            "hi": {
                "sys": (
                    "Aap ek visheshagya plant pathologist hain.\n"
                    "Is fasal ki bimari ko saral Hindi mein samjhaiye jo ek aam kisan samajh sake.\n"
                    "Cover karein: yeh bimari kya hai, sankramit fasal kaisi dikhti hai, "
                    "kitni tezi se phailti hai, aur kitni gambhir hai.\n"
                    "Format: 3-4 chhote paragraphs. Bullet points mein visual lakshan bataiye."
                ),
                "usr": f"{base_facts}\n\nIs bimari ko samjhaiye — kya hai, lakshan kya hain, kitni khatarnak hai.",
            },
        },
        "causes": {
            "en": {
                "sys": (
                    "You are a plant pathologist.\n"
                    "Explain what CAUSES this disease in a farmer's crop.\n"
                    "Cover: the pathogen (fungus/bacteria/virus/pest), environmental conditions that trigger it "
                    "(temperature, humidity, rain, soil type), and farming practices that make it worse.\n"
                    "Use bullet points. Keep it practical and farmer-friendly."
                ),
                "usr": f"{base_facts}\n\nWhat are all the causes of this disease?",
            },
            "hi": {
                "sys": (
                    "Aap ek plant pathologist hain.\n"
                    "Kisan ko batayein ki yeh bimari KYUN hoti hai.\n"
                    "Cover karein: kaun sa jeevanu (fungus/bacteria/virus/kida), "
                    "kaun si maausami sthitiyaan isko trigger karti hain, "
                    "aur kaunsi kheti ki aadat isse bhadati hai.\n"
                    "Bullet points mein. Saral Hindi mein."
                ),
                "usr": f"{base_facts}\n\nIs bimari ke sare kaaran kya hain?",
            },
        },
        "prevention": {
            "en": {
                "sys": (
                    "You are an agricultural expert.\n"
                    "Give a farmer PRACTICAL PREVENTION steps for this disease.\n"
                    "Cover: seed treatment, crop rotation, resistant varieties, field hygiene, "
                    "irrigation management, and early warning signs to watch for.\n"
                    "Make it a clear, numbered action list. Be specific."
                ),
                "usr": f"{base_facts}\n\nHow can a farmer PREVENT this disease from occurring?",
            },
            "hi": {
                "sys": (
                    "Aap ek krishi visheshagya hain.\n"
                    "Kisan ko is bimari se BACHNE ke VYAVHARIK UPAY batayein.\n"
                    "Cover karein: beej upchar, fasal chakra, pratirodhi kismein, "
                    "khet ki safai, sinchai prabandhan, aur shuruaati sanket.\n"
                    "Numbered action list mein. Specific aur saral Hindi mein."
                ),
                "usr": f"{base_facts}\n\nKisan is bimari ko KAISE ROK sakta hai?",
            },
        },
        "treatment": {
            "en": {
                "sys": (
                    "You are a plant disease treatment specialist.\n"
                    "Give TREATMENT options for a farmer who already has this disease in their crop.\n"
                    "Cover:\n"
                    "1. Organic/biological treatments (first priority)\n"
                    "2. Chemical fungicides/pesticides with exact product names and doses\n"
                    "3. When to apply (crop stage, time of day)\n"
                    "4. How many applications needed\n"
                    "Be specific with product names available in India and dosages."
                ),
                "usr": f"{base_facts}\n\nWhat is the complete treatment for this disease?",
            },
            "hi": {
                "sys": (
                    "Aap ek plant disease treatment specialist hain.\n"
                    "Kisan ko is bimari ka ILAAJ batayein jab yeh unki fasal mein lag jaaye.\n"
                    "Cover karein:\n"
                    "1. Jevik/jaivik upchar (pehli praathmikta)\n"
                    "2. Rasayanik dawaiyan — naam aur matra ke saath\n"
                    "3. Kab lagayen (fasal avastha, din ka samay)\n"
                    "4. Kitni baar lagani hai\n"
                    "India mein milne wale products ke naam batayein."
                ),
                "usr": f"{base_facts}\n\nIs bimari ka poora ilaaj kya hai?",
            },
        },
        "spray": {
            "en": {
                "sys": (
                    "You are a precision agriculture specialist.\n"
                    "Create a DETAILED SPRAY SCHEDULE for treating this disease.\n"
                    "Format as a table or numbered weekly plan covering:\n"
                    "- Day/Week number\n"
                    "- Product name (fungicide/pesticide available in India)\n"
                    "- Dose per litre of water\n"
                    "- Dose per acre\n"
                    "- Best time to spray (morning/evening)\n"
                    "- Special instructions (e.g. don't spray if rain expected)\n"
                    "Include 3-4 week schedule. Be very specific."
                ),
                "usr": f"{base_facts}\n\nGive me a complete week-by-week spray schedule.",
            },
            "hi": {
                "sys": (
                    "Aap ek precision agriculture specialist hain.\n"
                    "Is bimari ke ilaaj ke liye DETAILED SPRAY SCHEDULE banayein.\n"
                    "Table ya numbered weekly plan format mein:\n"
                    "- Din/Saptaah number\n"
                    "- Product ka naam (India mein milne wali dawa)\n"
                    "- Matra per litre paani\n"
                    "- Matra per acre\n"
                    "- Spray ka sabse accha samay (subah/shaam)\n"
                    "- Khaas hidayatein (jaise baarish se pehle mat lagayen)\n"
                    "3-4 saptaah ka schedule. Bilkul specific."
                ),
                "usr": f"{base_facts}\n\nPura hafte-dar-hafte spray schedule batayein.",
            },
        },
    }

    chosen  = SECTION_PROMPTS.get(section, SECTION_PROMPTS["overview"])
    lang_k  = "hi" if lang == "hi" else "en"
    prompts = chosen[lang_k]
    return prompts["sys"], prompts["usr"]
