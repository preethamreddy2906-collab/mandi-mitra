import os
import time

from openai import OpenAI

from .finalize import generate_analysis, make_fast_payload

invoke_url = "http://localhost:11434/v1"
stream = False
OLLAMA_API_KEY = "ollama"

COMMODITY = "Tomato"
STATE = "Andhra Pradesh"
MARKET = "Palamaner APMC"
LANGUAGE = "Malayalam"

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Madanapalle Area
LATITUDE = 13.552040
LONGITUDE = 78.505798


def call_gemma(
    commodity,
    state,
    district,
    market,
    latitude,
    longitude,
    language="Telugu",
):
    gemma_payload = generate_analysis(
        commodity,
        state,
        district,
        market,
        latitude,
        longitude,
        language,
    )
    payload_text = make_fast_payload(gemma_payload)

    system_prompt = f"""
    You are Mandi Mitra, an agricultural advisory assistant.

    Always respond only in {language}.
    Always format your response using Markdown.
    Use only the verified context provided.
    Do not invent facts.
    Do not predict future prices.
    The recommended_decision is authoritative and must not be changed.
    """

    user_prompt = f"""
    Write the farmer advisory in **{language}** language using **Markdown**.

    Use this exact format:

    ## Recommendation

    (One short paragraph)

    ## Why
    - Reason 1
    - Reason 2
    - Reason 3

    ## Actions
    1. Action 1
    2. Action 2
    3. Action 3

    ## Caution

    One short caution.

    Rules:
    - Use Markdown only.
    - Do not return HTML.
    - Do not return JSON.
    - Keep the response under 150 words.
    - Use only the verified context below.

    VERIFIED CONTEXT:
    {payload_text}
    
    """

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    response = client.chat.completions.create(
        model="gemma4:e2b-it-q4_K_M",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=1024,
    )
    return response.choices[0].message.content
    


if __name__ == "__main__":
    start = time.time()
    print(
        call_gemma(
            commodity=COMMODITY,
            state=STATE,
            district="Palamaner",
            market=MARKET,
            latitude=LATITUDE,
            longitude=LONGITUDE,
            language=LANGUAGE,
        )
    )
    end = time.time()
    print("Total Time:", end - start)
# import os
# import time

# from langchain_nvidia_ai_endpoints import ChatNVIDIA
# from langchain_core.messages import SystemMessage, HumanMessage
# from dotenv import load_dotenv
# load_dotenv()

# import os
# from .finalize import generate_analysis, make_fast_payload

# COMMODITY = "Tomato"
# STATE = "Andhra Pradesh"
# MARKET = "Palamaner APMC"
# LANGUAGE = "Malayalam"

# NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# # Madanapalle Area
# LATITUDE = 13.552040
# LONGITUDE = 78.505798

# NVIDIA_MODEL = "meta/llama-3.2-3b-instruct"


def build_local_fallback_advisory(
    commodity,
    state,
    district,
    market,
    latitude,
    longitude,
    language="Telugu",
):
    summary = generate_analysis(
        commodity,
        state,
        district,
        market,
        latitude,
        longitude,
        language,
    )
    latest_price = summary.get("market_summary", {}).get("latest", {}).get("modal_price")
    trend = summary.get("market_summary", {}).get("trend", "stable")
    change = summary.get("market_summary", {}).get("seven_day_change_percent")
    change_label = f"{change:+.1f}%" if change is not None else "recently"
    price_label = f"₹{latest_price:.0f}/quintal" if latest_price is not None else "current local mandi price"
    return (
        f"Based on the latest mandi data for {commodity} in {market}, the trend is {trend} "
        f"with a change of {change_label} over the last 7 days. The current modal price is around {price_label}. "
        f"For now, monitor the local market closely and sell when the price is favourable while keeping crop quality and transport timing in mind."
    )


# def call_gemma(
#     commodity,
#     state,
#     district,
#     market,
#     latitude,
#     longitude,
#     language="Telugu",
# ):
#     if not NVIDIA_API_KEY:
#         raise RuntimeError(
#             "NVIDIA_API_KEY is not set. Export it or add it to your .env file."
#         )

#     try:
#         gemma_payload = generate_analysis(
#             commodity,
#             state,
#             district,
#             market,
#             latitude,
#             longitude,
#             language,
#         )
#         payload_text = make_fast_payload(gemma_payload)

#         system_prompt = f"""
#         You are Mandi Mitra, an agricultural advisory assistant.

#         Always respond only in {language}.
#         Always format your response using Markdown.
#         Use only the verified context provided.
#         Do not invent facts.
#         Do not predict future prices.
#         The recommended_decision is authoritative and must not be changed.
#         """

#         user_prompt = f"""
#         Write the farmer advisory in **{language}** language using **Markdown**.

#         Use this exact format:

#         ## Recommendation

#         (One short paragraph)

#         ## Why
#         - Reason 1
#         - Reason 2
#         - Reason 3

#         ## Actions
#         1. Action 1
#         2. Action 2
#         3. Action 3

#         ## Caution

#         One short caution.

#         Rules:
#         - Use Markdown only.
#         - Do not return HTML.
#         - Do not return JSON.
#         - Keep the response under 150 words.
#         - Use only the verified context below.

#         VERIFIED CONTEXT:
#         {payload_text}

#         """

#         client = ChatNVIDIA(
#             model=NVIDIA_MODEL,
#             api_key=NVIDIA_API_KEY,
#             base_url="https://integrate.api.nvidia.com/v1",
#             temperature=0.2,
#             top_p=0.7,
#             max_completion_tokens=1024,
#         )

#         response = client.invoke(
#             [
#                 SystemMessage(content=system_prompt),
#                 HumanMessage(content=user_prompt),
#             ]
#         )
#         return response.content
#     except Exception as exc:
#         message = str(exc).lower()
#         if "timed out" in message or "timeout" in message or "read timed out" in message:
#             return build_local_fallback_advisory(
#                 commodity,
#                 state,
#                 district,
#                 market,
#                 latitude,
#                 longitude,
#                 language,
#             )
#         raise


# if __name__ == "__main__":
#     start = time.time()
#     print(
#         call_gemma(
#             commodity=COMMODITY,
#             state=STATE,
#             district="Palamaner",
#             market=MARKET,
#             latitude=LATITUDE,
#             longitude=LONGITUDE,
#             language=LANGUAGE,
#         )
#     )
#     end = time.time()
#     print("Total Time:", end - start)