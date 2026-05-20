import asyncio
import sys
import os
from sqlalchemy import select, func, text

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.session import SessionLocal
from app.models.text_content import TextContent

async def check_embeddings():
    print("Checking PostgreSQL Embeddings...\n")
    
    async with SessionLocal() as db:
        # 1. Total Count
        total_stmt = select(func.count(TextContent.text_id))
        total = (await db.execute(total_stmt)).scalar() or 0
        
        # 2. Count with vector
        # Note: Depending on column name, might be 'embedding' or 'search_vector' (tsvector)
        # Based on schema check, 'embedding' is the vector column (pgvector)
        vec_stmt = select(func.count(TextContent.text_id)).where(TextContent.embedding.is_not(None))
        with_vec = (await db.execute(vec_stmt)).scalar() or 0
        
        # 3. Check Dimensions (if possible with SQL)
        # vector_dims usually checks typmod, but we can check one sample
        valid_dims = 0
        sample_stmt = select(TextContent.embedding).where(TextContent.embedding.is_not(None)).limit(5)
        samples = (await db.execute(sample_stmt)).scalars().all()
        
        print(f"Total Documents: {total}")
        print(f"With Embeddings: {with_vec}")
        print(f"Missing Embeddings: {total - with_vec}")
        
        if samples:
            print(f"\nChecking sample dimensions (expecting 1536)...")
            for i, vec in enumerate(samples):
                # vec is likely a list or numpy array depending on driver
                try:
                    dims = len(vec)
                    print(f"  Sample {i+1}: {dims} dims")
                    if dims == 1536:
                        valid_dims += 1
                except Exception as e:
                    print(f"  Sample {i+1}: Error checking dims ({e})")
        
        print("\nSummary:")
        if total > 0 and with_vec == total:
            print("✅ All documents have embeddings.")
        elif with_vec > 0:
            print(f"⚠️ Partial coverage ({with_vec}/{total}). Process more data.")
        else:
            print("❌ No embeddings found.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_embeddings())
