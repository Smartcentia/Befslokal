import asyncio
import sys
import os
from sqlalchemy import text
from app.db.session import SessionLocal

async def check():
    async with SessionLocal() as db:
        res = await db.execute(text('SELECT periods, amount FROM contracts WHERE periods IS NOT NULL OR amount IS NOT NULL LIMIT 5'))
        rows = res.fetchall()
        for i, r in enumerate(rows):
            print(f"Row {i}:")
            print(f"  Periods: Type={type(r[0])} Value={r[0]}")
            print(f"  Amount: Type={type(r[1])} Value={r[1]}")

if __name__ == "__main__":
    asyncio.run(check())
