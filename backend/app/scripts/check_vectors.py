import asyncio
import sys
import os
from sqlalchemy import select, func, text

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.models.text_content import TextContent

async def check_vectors():
    async with SessionLocal() as db:
        # Count total
        total = await db.scalar(select(func.count(TextContent.text_id)))
        
        # Count populated vectors
        from sqlalchemy import literal_column
        # We assume search_vector exists. SQLAlchemy model definition might not map it explicitly if it's computed?
        # Let's check the TextContent model def first or use raw SQL to be safe.
        
        query = text("SELECT count(*) FROM text_content WHERE search_vector IS NOT NULL")
        populated = await db.scalar(query)
        
        print(f"Total Rows: {total}")
        print(f"Rows with Vector: {populated}")
        
        if total > 0:
            print(f"Coverage: {populated/total*100:.1f}%")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_vectors())
