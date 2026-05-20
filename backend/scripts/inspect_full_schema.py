import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from sqlalchemy import text
from app.db.session import SessionLocal

async def list_schema():
    db = SessionLocal()
    try:
        print("--- Tables and Columns ---")
        stmt = text("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, column_name;
        """)
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        current_table = ""
        for row in rows:
            table, column, dtype = row
            if table != current_table:
                print(f"\n[{table}]")
                current_table = table
            print(f"  - {column} ({dtype})")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(list_schema())
