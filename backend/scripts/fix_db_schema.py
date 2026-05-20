
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def fix_schema():
    async with engine.begin() as conn:
        print("Fixing database schema...")
        
        # 1. Check if columns exist (Double check)
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
        columns = [row[0] for row in result.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column...")
            # We add as VARCHAR to be safe, assuming the app deals with the Enum mapping
            await conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'PROPERTY_MANAGER'"))
            
        if 'region' not in columns:
            print("Adding 'region' column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN region VARCHAR"))

        print("Schema fix complete.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
