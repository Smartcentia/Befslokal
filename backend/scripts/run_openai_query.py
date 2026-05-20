#!/usr/bin/env python3
"""
Kjør én enkel OpenAI-spørring for å verifisere at OPENAI_API_KEY og oppsett fungerer.
Bruker samme config som appen (app.core.config.settings).

Kjør fra prosjektrot:
  cd backend && python scripts/run_openai_query.py
eller fra backend:
  python scripts/run_openai_query.py

Alternativt med egen prompt:
  python scripts/run_openai_query.py "Din spørring her"
"""
import asyncio
import os
import sys

# Sørg for at app er på path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

from app.core.config import settings


async def run_query(user_message: str = "Si bare: OK") -> None:
    if not getattr(settings, "OPENAI_API_KEY", None) or not (settings.OPENAI_API_KEY or "").strip():
        print("FEIL: OPENAI_API_KEY er ikke satt. Sett den i backend/.env eller Railway Dashboard → Environment.")
        return
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, "OPENAI_BASE_URL", None) or "https://api.openai.com/v1",
        )
        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        print(f"Sender spørring til OpenAI (modell: {model})...")
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150,
        )
        text = (resp.choices[0].message.content or "").strip()
        print("Svar:", text)
        print("OpenAI-spørring: OK")
    except Exception as e:
        print(f"OpenAI-spørring: FEIL - {e}")


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Si bare: OK"
    asyncio.run(run_query(msg))
