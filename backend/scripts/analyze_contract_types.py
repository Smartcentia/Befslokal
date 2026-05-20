
import asyncio
import sys
import os

# Add backend root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        # Fetch all contracts external_data
        res = await db.execute(text("SELECT contract_id, external_data FROM contracts"))
        rows = res.fetchall()
        
        total = len(rows)
        financial_contracts = 0
        real_contracts = 0
        unknown = 0
        
        print(f"Total rows in contracts table: {total}")
        
        for r in rows:
            ext = r[1]
            if ext and isinstance(ext, dict):
                if 'financials' in ext or 'transaction_count' in str(ext):
                    financial_contracts += 1
                else:
                    real_contracts += 1
            else:
                real_contracts += 1 # Assume real if no suspicious metadata
                
        print(f"Identified 'Financial' Contracts (Fake): {financial_contracts}")
        print(f"Identified 'Real' Contracts: {real_contracts}")
        print(f"Ratio: {financial_contracts/total:.1%}")

if __name__ == "__main__":
    asyncio.run(main())
