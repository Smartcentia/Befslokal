import asyncio
import sys
import os
from sqlalchemy import text
from app.db.session import SessionLocal

async def check_schema():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'contracts'"))
        rows = res.fetchall()
        for r in rows:
            print(f"Column: {r[0]}, Type: {r[1]}")

if __name__ == "__main__":
    asyncio.run(check_schema())
