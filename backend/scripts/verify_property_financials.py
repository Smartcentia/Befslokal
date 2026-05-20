
import asyncio
import sys
import os
# Add backend root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db import base
from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        # Check properties with financials
        res = await db.execute(text("SELECT property_id, address, external_data FROM properties WHERE external_data::text LIKE '%financials%' LIMIT 5"))
        rows = res.fetchall()
        
        print(f"--- Properties with Financial Data (Sample 5) ---")
        for r in rows:
            print(f"Property: {r[1]}")
            print(f"External Data Keys: {r[2].keys() if r[2] else 'None'}")
            if r[2] and 'financials' in r[2]:
                 print(f"Financials Sample: {str(r[2]['financials'])[:100]}...")
            print("-" * 20)
            
        # Count total properties with financials
        count_res = await db.execute(text("SELECT count(*) FROM properties WHERE external_data::text LIKE '%financials%'"))
        print(f"Total Properties with Financials: {count_res.scalar()}")

if __name__ == "__main__":
    asyncio.run(main())
