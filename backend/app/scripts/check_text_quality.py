import asyncio
import sys
import os
from sqlalchemy import select, func, text

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.models.text_content import TextContent

async def check_text_quality():
    async with SessionLocal() as db:
        # 1. Total Count
        count = await db.scalar(select(func.count()).select_from(TextContent))
        print(f"Total TextContent rows: {count}")
        
        # 2. Empty/Short content (Potential OCR failure)
        short_docs = await db.scalars(
            select(TextContent).where(func.length(TextContent.content) < 100).limit(5)
        )
        short_docs_list = short_docs.all()
        print(f"Found docs with <100 chars (Sample of {len(short_docs_list)}):")
        for d in short_docs_list:
             print(f" - ID: {d.text_id} | Length: {len(d.content or '')} | Source: {d.source_file}")

        # 3. Sample text to check for garbled characters
        sample = await db.scalar(select(TextContent).where(func.length(TextContent.content) > 500).limit(1))
        if sample:
            print("\n--- Sample Text Content (First 500 chars) ---")
            print(f"Source: {sample.source_file}")
            print(sample.content[:500])
            print("---------------------------------------------")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_text_quality())
