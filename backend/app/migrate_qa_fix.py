
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Fixing QA Enum Types to Uppercase...")
        try:
            await conn.execute(text("ALTER TYPE qastatus RENAME VALUE 'pending' TO 'PENDING';"))
            await conn.execute(text("ALTER TYPE qastatus RENAME VALUE 'pass' TO 'PASS';"))
            await conn.execute(text("ALTER TYPE qastatus RENAME VALUE 'fail' TO 'FAIL';"))
            print("Enum values updated to UPPERCASE.")
        except Exception as e:
            print(f"Update failed (maybe already done?): {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
