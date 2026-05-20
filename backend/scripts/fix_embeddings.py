
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import select, text

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.models.text_content import TextContent
from app.services.ki_kollega.service import ki_kollega_service

async def fix_data():
    print("🚀 Starting Repair...")
    
    if not ki_kollega_service.client:
        print("❌ Client not ready")
        return

    async with SessionLocal() as session:
        # 1. Update Search Vectors (SQL)
        print("   Updating search_vector (TSVECTOR)...")
        await session.execute(text("""
            UPDATE text_content 
            SET search_vector = to_tsvector('norwegian', COALESCE(content, ''))
            WHERE search_vector IS NULL
        """))
        await session.commit()
        print("   ✅ Search vectors updated.")

        # 2. Update Embeddings (Python + API)
        stmt = select(TextContent).where(TextContent.embedding.is_(None))
        result = await session.execute(stmt)
        rows = result.scalars().all()
        
        print(f"   Found {len(rows)} rows missing embeddings.")
        
        for row in rows:
            if not row.content:
                continue
            
            print(f"   > Embedding {row.text_id}...")
            # Use the service helper
            emb = await ki_kollega_service._generate_embedding(row.content[:8000])
            if emb:
                row.embedding = emb
            else:
                print("     ❌ Failed")
        
        await session.commit()
        print(f"   ✅ Updated {len(rows)} embeddings.")

if __name__ == "__main__":
    asyncio.run(fix_data())
