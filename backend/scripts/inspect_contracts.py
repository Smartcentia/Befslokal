
import asyncio
import sys
import os

# Add backend root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT contract_id, status, amount, periods, external_data FROM contracts LIMIT 5"))
        rows = res.fetchall()
        print("--- Contract Inspection ---")
        for r in rows:
            print(f"ID: {str(r[0])}")
            print(f"Status: {r[1]}")
            print(f"Amount: {r[2]}")
            print(f"Periods: {r[3]}")
            print(f"External Data: {r[4]}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
