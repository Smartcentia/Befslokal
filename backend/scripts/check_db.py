#!/usr/bin/env python3
"""
Direct SQL check on what was actually saved to database
"""
import asyncio
from app.db.session import SessionLocal

async def check():
    async with SessionLocal() as db:
        from sqlalchemy import text
        result = await db.execute(text("""
            SELECT contract_id, amount->'amount_per_year' as amt 
            FROM contracts 
            WHERE contract_id = '49effc37-d809-430b-81c0-c87072a4501c'
        """))
        row = result.fetchone()
        print(f"Contract ID: {row[0]}")
        print(f"Amount per year: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check())
