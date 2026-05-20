import asyncio
import sys
import os

# Ensure backend root is in python path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import SessionLocal

async def main():
    try:
        async with SessionLocal() as db:
            res = await db.execute(text("SELECT count(*) FROM contracts"))
            count = res.scalar()
            print(f"Contracts count: {count}")
            
            res = await db.execute(text("SELECT count(*) FROM parties"))
            print(f"Parties count: {res.scalar()}")
            
            res = await db.execute(text("SELECT count(*) FROM units"))
            print(f"Units count: {res.scalar()}")

            # Dump first 5 contracts if any
            if count > 0:
                res = await db.execute(text("SELECT contract_id, status FROM contracts LIMIT 5"))
                rows = res.fetchall()
                print("First 5 contracts:")
                for r in rows:
                    print(r)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
