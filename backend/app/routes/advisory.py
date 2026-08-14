import sys
import io
import re
import base64
from pathlib import Path

from fastapi import APIRouter
from gtts import gTTS

# EVALUATIONS_DIR = Path(__file__).resolve().parents[3] / "evaluations"
# if str(EVALUATIONS_DIR) not in sys.path:
#     sys.path.append(str(EVALUATIONS_DIR))


from evaluations.model import call_gemma, build_local_fallback_advisory
from evaluations.agmarknet_api import fetch_historical_prices

def clean_text_for_tts(text: str, language_code: str = "") -> str:
    if not text:
        return ""
    
    # 1. Remove markdown code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # 2. Remove inline code blocks
    text = re.sub(r"`.*?`", "", text)
    # 3. Remove markdown links: [text](link) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # 4. Remove headers: #, ##, ### at start of line
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)
    # 5. Remove bold / italic symbols: **, *, __, _
    text = re.sub(r"\*\*|__|\*|_", "", text)
    # 6. Remove list markers at start of lines: * , - , + , or numbers like 1. , 2.
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # 7. Replace newline sequences and carriage returns with spaces
    text = text.replace("\r", " ").replace("\n", " ")
    
    # 7.5 If the language is Telugu ('te'), remove stray English/Latin letters (A-Za-z)
    if language_code == "te":
        text = re.sub(r"[A-Za-z]+", "", text)

    # 8. Collapse multiple spaces into a single space
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()

def map_language_to_gtts(lang_str: str) -> str:
    # Handle BCP-47 codes
    if "te-" in lang_str.lower() or lang_str.lower() == "te":
        return "te"
    if "hi-" in lang_str.lower() or lang_str.lower() == "hi":
        return "hi"
    if "ta-" in lang_str.lower() or lang_str.lower() == "ta":
        return "ta"
    if "en-" in lang_str.lower() or lang_str.lower() == "en":
        return "en"
    
    # Handle plain text language names
    lang_lower = lang_str.lower()
    if "telugu" in lang_lower:
        return "te"
    if "hindi" in lang_lower:
        return "hi"
    if "tamil" in lang_lower:
        return "ta"
    if "english" in lang_lower:
        return "en"
    
    return "en" # Fallback

def generate_audio(text: str, language_code: str) -> str:
    try:
        lang = map_language_to_gtts(language_code)
        cleaned_text = clean_text_for_tts(text, lang)
        print("Cleaned text for TTS:", cleaned_text)
        tts = gTTS(text=cleaned_text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode("utf-8")
        return audio_base64
    except Exception as e:
        print("TTS Generation Error:", e)
        return ""

router = APIRouter(prefix="/advisory", tags=["Advisory"])


@router.post("/")
def get_advisory(data: dict):
    print("Inside API")
    commodity = data.get("crop") or "Tomato"
    state = data.get("state") or "Andhra Pradesh"
    district = data.get("district") or "Palamaner"
    market = data.get("market") or "Palamaner APMC"
    latitude = float(data.get("latitude", 13.552040))
    longitude = float(data.get("longitude", 78.505798))
    language = data.get("language") or "Telugu"

    try:
        recommendation = call_gemma(
            commodity=commodity,
            state=state,
            district=district,
            market=market,
            latitude=latitude,
            longitude=longitude,
            language=language,
        )
        print("Printing Recomendation")
        print(recommendation)
    except Exception as exc:
        recommendation = build_local_fallback_advisory(
            commodity=commodity,
            state=state,
            district=district,
            market=market,
            latitude=latitude,
            longitude=longitude,
            language=language,
        )
        print(f"Falling back to local advisory because NVIDIA call failed: {exc}")

    historic_prices = fetch_historical_prices(
        commodity=commodity,
        state=state,
        market=market,
        district=district,
    )

    if historic_prices.empty:
        market_payload = {
            "market_name": market,
            "current_price": "₹2200 / Quintal",
            "modal_price": 2200,
            "max_price": 2350,
            "min_price": 2050,
        }
    else:
        latest_row = historic_prices.iloc[-1]
        market_payload = {
            "market_name": market,
            "current_price": f"₹{latest_row['modal_price']} / Quintal",
            "modal_price": latest_row["modal_price"],
            "max_price": latest_row["max_price"],
            "min_price": latest_row["min_price"],
        }
    
    audio_base64 = generate_audio(recommendation, language)
    
    return {
        "weather": {
            "temperature": "32°C",
            "humidity": "72%",
            "rainfall": "10%",
        },
        "market": {
            **market_payload,
            "trend": "Increasing",
        },
        "crop": {
            "harvest_tip": "Harvest within 2 days",
            "storage_tip": "Can be stored for 5 days",
            "best_selling_period": "This Week",
        },
        "recommendation": recommendation,
        "audio_base64": audio_base64,
        "confidence": 88,
        "risk_level": "Low",
    }