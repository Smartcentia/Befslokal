import asyncio
import sys
import os
from sqlalchemy import select, func, desc

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.session import SessionLocal
from app.models.text_content import TextContent

async def check_indexer_status():
    print("Checking Database Content Status (PostgreSQL)...\n")
    
    async with SessionLocal() as db:
        # 1. Total Count
        count = (await db.execute(select(func.count(TextContent.text_id)))).scalar()
        
        # 2. Last Updated
        last_stmt = select(TextContent.created_at).order_by(desc(TextContent.created_at)).limit(1)
        last_update = (await db.execute(last_stmt)).scalar()
        
        # 3. Categories breakdown
        cat_stmt = select(TextContent.category, func.count(TextContent.text_id))\
                   .group_by(TextContent.category)
        cat_rows = (await db.execute(cat_stmt)).fetchall()
        
        print(f"=== Content Status ===")
        print(f"Total Documents: {count}")
        print(f"Last Import: {last_update}")
        
        print(f"\n=== Categories ===")
        for cat, c in cat_rows:
            print(f"  {cat or 'Uncategorized'}: {c}")
            
        # 4. Source Types
        src_stmt = select(TextContent.source_type, func.count(TextContent.text_id))\
                   .group_by(TextContent.source_type)
        src_rows = (await db.execute(src_stmt)).fetchall()
        
        print(f"\n=== Source Types ===")
        for src, c in src_rows:
            print(f"  {src or 'Unknown'}: {c}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_indexer_status())
