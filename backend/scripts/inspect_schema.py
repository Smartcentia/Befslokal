
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load env from backend root
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal

async def inspect():
    async with SessionLocal() as session:
        print("🔍 Inspecting 'contracts'...")
        res = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'contracts'"))
        for row in res.fetchall():
            print(f" - {row.column_name} ({row.data_type})")

        print("\n🔍 Inspecting 'units'...")
        res = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'units'"))
        for row in res.fetchall():
            print(f" - {row.column_name} ({row.data_type})")

        print("\n🔍 Sample Contract Amount:")
        res = await session.execute(text("SELECT amount FROM contracts LIMIT 1"))
        row = res.fetchone()
        if row:
            print(f" - {row.amount}")

if __name__ == "__main__":
    asyncio.run(inspect())
