import asyncio
import sys
import os
from sqlalchemy import select, or_, func

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.models.text_content import TextContent

async def check_keywords():
    keywords = {
        "Ansvar/Vedlikehold": ["vedlikehold", "snømåking", "vaktmester", "reparasjon", "ansvar"],
        "Kostnader/Felles": ["felleskostnader", "strøm", "varme", "renhold", "avgifter"],
        "Frister/Opsjoner": ["fornyelse", "opsjon", "oppsigelse", "regulering", "indeks"]
    }

    async with SessionLocal() as db:
        print("--- Keyword Frequency Analysis ---")
        for category, kws in keywords.items():
            print(f"\nCategory: {category}")
            for kw in kws:
                stmt = select(func.count()).where(TextContent.content.ilike(f"%{kw}%"))
                count = await db.scalar(stmt)
                print(f"  - '{kw}': {count} matches")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_keywords())
