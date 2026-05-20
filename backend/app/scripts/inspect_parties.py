
import asyncio
import sys
from app.db.session import SessionLocal
from sqlalchemy import text

async def inspect_parties():
    async with SessionLocal() as db:
        print("Checking 'parties' columns:")
        res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'parties';"))
        cols = [r[0] for r in res.fetchall()]
        print(cols)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect_parties())
