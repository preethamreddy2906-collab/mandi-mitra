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
