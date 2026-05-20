
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@localhost/knowme")

async def check_file_paths():
    print(f"\n--- 📂 Checking File Paths in DB ---")
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT file_id, path, content_type FROM file_meta LIMIT 5"))
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"   - ID: {row[0]}, Path: {row[1]}, Type: {row[2]}")
            else:
                print("   (No files found in file_meta)")
                
    except Exception as e:
        print(f"⚠️  Database query failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_file_paths())
