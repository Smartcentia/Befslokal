import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from sqlalchemy import text
from app.db.session import SessionLocal

async def global_search():
    db = SessionLocal()
    try:
        tables = ['properties', 'contracts', 'units', 'parties']
        keyword = '%arkiv%'
        
        print(f"--- Global Search for '{keyword}' ---")
        
        for table in tables:
            stmt = text(f"SELECT * FROM {table} WHERE row_to_json({table})::text ILIKE :kw LIMIT 5")
            result = await db.execute(stmt, {"kw": keyword})
            rows = result.fetchall()
            
            if rows:
                print(f"Match in table '{table}': {len(rows)} rows found.")
                for row in rows:
                    # distinct fields depending on table
                    print(f"  Row: {row}")
            else:
                print(f"No match in table '{table}'.")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(global_search())
