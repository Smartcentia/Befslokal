import asyncio
import sys
import os
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import engine
from app.db.base import Base

async def reset_db():
    print("⚠️  WARNING: This will DROP ALL DATA in the database.")
    print("Connecting to database...")
    
    async with engine.begin() as conn:
        print("💥 NUKE OPTION: Dropping public schema cascade...")
        # This clears EVERYTHING including types, views, tables.
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        # Restore permissions if needed (usually defaults are fine for owner)
        # await conn.execute(text("GRANT ALL ON SCHEMA public TO public;")) 
        
        print("Schema reset. Recreating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables recreated successfully.")

if __name__ == "__main__":
    asyncio.run(reset_db())
