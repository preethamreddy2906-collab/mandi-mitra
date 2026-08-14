import json
from pathlib import Path

import pandas as pd

from .agmarknet_api import fetch_historical_prices
from .weather_api import fetch_weather_data

BASE_DIR = Path(__file__).resolve().parent
CROP_KB_PATH = BASE_DIR.parent.parent / "crop_database" / "crop_knowledge_base.json"


COMMODITY = 'Potato'
STATE = 'Andhra Pradesh'
MARKET = 'Palamaner APMC'
LANGUAGE = 'Telugu'

# Madanapalle Area
LATITUDE = 13.552040
LONGITUDE = 78.505798

def get_crop_knowledge(commodity):
    with open(CROP_KB_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    crop_knowledge = data[f'{commodity.lower()}']

    return crop_knowledge


def safe_float(value, default=None):
    """Convert values including NaN into JSON-safe floats."""
    if value is None or pd.isna(value):
        return default
    return float(value)

def summarize_market(history: pd.DataFrame) -> dict:
    """
    history must contain:
    arrival_date, state, district, market, commodity,
    min_price, max_price, modal_price, price_unit
    """
    if history is None or history.empty:
        return {
            "available": False,
            "message": "No market-price records found."
        }

    df = history.copy()

    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    df["min_price"] = pd.to_numeric(df["min_price"], errors="coerce")
    df["max_price"] = pd.to_numeric(df["max_price"], errors="coerce")

    df = (
        df.dropna(subset=["arrival_date", "modal_price"])
          .sort_values("arrival_date")
          .drop_duplicates(subset=["arrival_date"], keep="last")
          .tail(7)
          .reset_index(drop=True)
    )

    if df.empty:
        return {
            "available": False,
            "message": "No valid market-price records found."
        }

    first = df.iloc[0]
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) >= 2 else None

    avg_price = float(df["modal_price"].mean())
    first_price = float(first["modal_price"])
    latest_price = float(latest["modal_price"])

    seven_day_change = (
        ((latest_price - first_price) / first_price) * 100
        if first_price != 0 else None
    )

    previous_price = float(previous["modal_price"]) if previous is not None else None
    day_change = (
        ((latest_price - previous_price) / previous_price) * 100
        if previous_price not in (None, 0) else None
    )

    # Small fluctuations should not be labeled rising/falling.
    if seven_day_change is None or abs(seven_day_change) < 5:
        trend = "stable"
    elif seven_day_change > 0:
        trend = "rising"
    else:
        trend = "falling"

    recent_prices = [
        {
            "date": row["arrival_date"].strftime("%Y-%m-%d"),
            "modal_price": safe_float(row["modal_price"]),
            "modalPrice": safe_float(row["modal_price"]),
            "max_price": safe_float(row["max_price"]),
            "maxPrice": safe_float(row["max_price"]),
            "min_price": safe_float(row["min_price"]),
            "minPrice": safe_float(row["min_price"]),
        }
        for _, row in df.iterrows()
    ]

    return {
        "available": True,
        "source": "AGMARKNET / OGD India",
        "state": str(latest.get("state", "")),
        "district": str(latest.get("district", "")),
        "market": str(latest.get("market", "")),
        "crop": str(latest.get("commodity", "")),
        "price_unit": str(latest.get("price_unit", "Rs./Quintal")),
        "period": {
            "from": first["arrival_date"].strftime("%Y-%m-%d"),
            "to": latest["arrival_date"].strftime("%Y-%m-%d")
        },
        "latest": {
            "date": latest["arrival_date"].strftime("%Y-%m-%d"),
            "min_price": safe_float(latest["min_price"]),
            "max_price": safe_float(latest["max_price"]),
            "modal_price": latest_price
        },
        "seven_day_average_modal_price": round(avg_price, 2),
        "previous_day_modal_price": previous_price,
        "day_over_day_change_percent": (
            round(day_change, 2) if day_change is not None else None
        ),
        "seven_day_change_percent": (
            round(seven_day_change, 2) if seven_day_change is not None else None
        ),
        "trend": trend,
        "recent_modal_prices": recent_prices,
        "recent_prices": recent_prices,
    }

def summarize_weather(weather_data: dict) -> dict:
    """
    weather_data is the full JSON dict returned by OpenWeather /forecast.
    It groups 3-hour entries into daily min/max temperatures and max rain chance.
    """
    if not weather_data or weather_data.get("cod") not in ("200", 200):
        return {
            "available": False,
            "message": "Weather forecast is unavailable."
        }

    forecast_df = pd.DataFrame(weather_data.get("list", []))

    if forecast_df.empty:
        return {
            "available": False,
            "message": "Weather forecast contains no entries."
        }

    forecast_df["datetime"] = pd.to_datetime(forecast_df["dt_txt"], errors="coerce")
    forecast_df = forecast_df.dropna(subset=["datetime"]).copy()

    forecast_df["date"] = forecast_df["datetime"].dt.strftime("%Y-%m-%d")
    forecast_df["temp_c"] = forecast_df["main"].apply(
        lambda x: safe_float(x.get("temp")) if isinstance(x, dict) else None
    )
    forecast_df["rain_probability_percent"] = (
        pd.to_numeric(forecast_df.get("pop", 0), errors="coerce")
        .fillna(0)
        .mul(100)
    )
    forecast_df["condition"] = forecast_df["weather"].apply(
        lambda x: x[0].get("description", "unknown")
        if isinstance(x, list) and len(x) > 0 else "unknown"
    )

    forecast_df = forecast_df.dropna(subset=["temp_c"])

    daily = (
        forecast_df.groupby("date", as_index=False)
        .agg(
            min_temp_c=("temp_c", "min"),
            max_temp_c=("temp_c", "max"),
            rain_probability_max_percent=("rain_probability_percent", "max"),
            conditions=("condition", lambda x: ", ".join(sorted(set(x))))
        )
        .head(5)
    )

    daily_forecast = [
        {
            "date": row["date"],
            "min_temp_c": round(safe_float(row["min_temp_c"]), 2),
            "max_temp_c": round(safe_float(row["max_temp_c"]), 2),
            "rain_probability_max_percent": round(
                safe_float(row["rain_probability_max_percent"], 0), 0
            ),
            "conditions": row["conditions"]
        }
        for _, row in daily.iterrows()
    ]

    city = weather_data.get("city", {})
    return {
        "available": True,
        "source": "OpenWeather forecast",
        "location": city.get("name", "Unknown"),
        "latitude": safe_float(city.get("coord", {}).get("lat")),
        "longitude": safe_float(city.get("coord", {}).get("lon")),
        "daily_forecast": daily_forecast
    }

def calculate_rule_engine(market: dict, weather: dict, crop: dict) -> dict:
    facts = []
    reasons = []

    crop_name = crop.get("crop_name", market.get("crop", "This crop"))
    latest_price = market.get("latest", {}).get("modal_price")
    change = market.get("seven_day_change_percent")
    trend = market.get("trend", "unknown")

    max_forecast_temp = None
    max_rain_probability = 0

    if weather.get("available"):
        temperatures = [
            day["max_temp_c"]
            for day in weather.get("daily_forecast", [])
            if day.get("max_temp_c") is not None
        ]

        rain_probs = [
            day.get("rain_probability_max_percent", 0)
            for day in weather.get("daily_forecast", [])
        ]

        max_forecast_temp = max(temperatures) if temperatures else None
        max_rain_probability = max(rain_probs) if rain_probs else 0

    critical_max = crop.get("critical_temp_max_c")
    critical_min = crop.get("critical_temp_min_c")
    storage_life = crop.get("storage_life_days")
    perishability = crop.get("perishability", "unknown")
    sell_bias = crop.get("sell_or_wait_bias", "")
    heat_sensitive = crop.get("heat_sensitive", False)
    rain_sensitive = crop.get("rain_sensitive", False)
    waterlogging_sensitive = crop.get("waterlogging_sensitive", False)

    heat_risk = (
        heat_sensitive
        and max_forecast_temp is not None
        and critical_max is not None
        and max_forecast_temp > critical_max
    )

    rain_risk = (
        max_rain_probability >= 60
        and (rain_sensitive or waterlogging_sensitive)
    )

    cold_risk = False
    min_forecast_temp = None

    if weather.get("available"):
        min_temperatures = [
            day["min_temp_c"]
            for day in weather.get("daily_forecast", [])
            if day.get("min_temp_c") is not None
        ]
        min_forecast_temp = min(min_temperatures) if min_temperatures else None

        cold_risk = (
            min_forecast_temp is not None
            and critical_min is not None
            and min_forecast_temp < critical_min
        )

    if latest_price is not None:
        facts.append(
            f"Latest modal price is Rs.{latest_price:.0f} per quintal."
        )

    if change is not None:
        facts.append(
            f"Seven-day price change is {change:+.2f}% and the trend is {trend}."
        )

    if heat_risk:
        facts.append(
            f"Maximum forecast temperature is {max_forecast_temp:.1f}°C, "
            f"above {crop_name}'s critical maximum of {critical_max:.1f}°C."
        )
        reasons.append(
            f"High temperature may reduce {crop_name} quality or yield."
        )

    if cold_risk:
        facts.append(
            f"Minimum forecast temperature is {min_forecast_temp:.1f}°C, "
            f"below {crop_name}'s critical minimum of {critical_min:.1f}°C."
        )
        reasons.append(
            f"Low temperature may damage {crop_name}."
        )

    if rain_risk:
        facts.append(
            f"Maximum forecast rain probability is {max_rain_probability:.0f}%."
        )
        reasons.append(
            f"Rain may increase harvest, transport, or storage risk for {crop_name}."
        )

    if perishability == "high":
        reasons.append(f"{crop_name} is highly perishable.")
    elif perishability == "medium":
        reasons.append(f"{crop_name} has moderate storage limitations.")

    # Generic, explainable decision policy
    if heat_risk or cold_risk or rain_risk:
        decision = "sell_within_1_to_3_days"

    elif sell_bias == "sell_fast_if_perishable" and trend == "falling":
        decision = "sell_soon"

    elif (
        trend == "rising"
        and storage_life is not None
        and storage_life >= 7
        and perishability != "high"
    ):
        decision = "monitor_for_1_day_before_selling"

    else:
        decision = "sell_soon"

    return {
        "recommended_decision": decision,
        "market_signal": trend,
        "weather_risk": {
            "heat_risk": heat_risk,
            "cold_risk": cold_risk,
            "rain_risk": rain_risk,
            "max_forecast_temp_c": max_forecast_temp,
            "min_forecast_temp_c": min_forecast_temp,
            "max_rain_probability_percent": max_rain_probability
        },
        "crop_storage_signal": perishability,
        "facts_for_explanation": facts,
        "reasons": reasons
    }

def prepare_gemma_payload(history, weather_data, crop_data, language="Telugu") -> dict:
    market_summary = summarize_market(history)
    weather_summary = summarize_weather(weather_data)
    rule_engine_result = calculate_rule_engine(
        market_summary,
        weather_summary,
        crop_data
    )

    return {
        "farmer_context": {
            "language": language,
            "state": market_summary.get("state"),
            "district": market_summary.get("district"),
            "market": market_summary.get("market"),
            "crop": market_summary.get("crop"),
            "weather_location": weather_summary.get("location")
        },
        "market_summary": market_summary,
        "weather_summary": weather_summary,
        "crop_knowledge": crop_data,
        "rule_engine_result": rule_engine_result
    }

def generate_analysis(commodity, state, district, market, latitude, longitude, language="Telugu"):

    # Last 7 days of market prices for the specified commodity, state, and market
    historic_prices = fetch_historical_prices(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
    )

    # fetches crop knowledge from the local JSON file
    crop_knowledge = get_crop_knowledge(commodity)


    data_weather = fetch_weather_data(latitude=latitude, longitude=longitude)

    gemma_payload = prepare_gemma_payload(
        history=historic_prices,
        weather_data=data_weather,
        crop_data=crop_knowledge,
        language=language
    )

    return gemma_payload



def make_fast_payload(gemma_payload):
    market = gemma_payload["market_summary"]
    weather = gemma_payload["weather_summary"]
    crop = gemma_payload["crop_knowledge"]
    rules = gemma_payload["rule_engine_result"]
    farmer = gemma_payload["farmer_context"]

    def safe_round(value, digits=0):
        if value is None:
            return None
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return None

    return {
        "lang": farmer["language"],
        "crop": farmer["crop"],
        "market": farmer["market"],
        "district": farmer["district"],
        "decision": rules["recommended_decision"],
        "price": safe_round(market.get("latest", {}).get("modal_price")),
        "chg7d_pct": safe_round(market.get("seven_day_change_percent"), 1),
        "trend": market.get("trend"),
        "max_temp_c": safe_round(rules.get("weather_risk", {}).get("max_forecast_temp_c")),
        "heat_risk": rules.get("weather_risk", {}).get("heat_risk"),
        "rain_risk": rules.get("weather_risk", {}).get("rain_risk"),
        "perishable": crop.get("perishability"),
        "storage_days": crop.get("storage_life_days"),
        "crit_temp_c": crop.get("critical_temp_max_c"),
        "reasons": rules.get("reasons"),
    }



def payload_to_prompt(p):
    return (
        f"Crop:{p['crop']} Market:{p['market']},{p['district']} Lang:{p['lang']}\n"
        f"Price:{p['price']}/quintal Chg7d:{p['chg7d_pct']}% Trend:{p['trend']}\n"
        f"MaxTemp:{p['max_temp_c']}C HeatRisk:{p['heat_risk']} RainRisk:{p['rain_risk']}\n"
        f"Perishable:{p['perishable']} StorageDays:{p['storage_days']} CritTemp:{p['crit_temp_c']}\n"
        f"Reasons:{'; '.join(p['reasons'])}\n"
        f"Decision so far:{p['decision']}"
    )

