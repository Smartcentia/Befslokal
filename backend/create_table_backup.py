import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
sys.path.append(os.path.dirname(__file__))

from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as db:
        print("Creating backup table 'contracts_backup_20260101'...")
        try:
            # Check if exists first to avoid error or decide to drop
            # For safety, let's just create if not exists or error if exists
            await db.execute(text("CREATE TABLE contracts_backup_20260101 AS SELECT * FROM contracts"))
            await db.commit()
            print("✅ Backup table created successfully.")
            
            # Verify count
            result = await db.execute(text("SELECT COUNT(*) FROM contracts_backup_20260101"))
            count = result.scalar()
            print(f"Backup contains {count} rows.")
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")

if __name__ == "__main__":
    asyncio.run(main())
