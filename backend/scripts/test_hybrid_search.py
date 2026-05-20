import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env from root (2 levels up from scripts/)
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.ki_kollega.service import ki_kollega_service
from app.services.search_service import search_hybrid
from app.services.logger import get_logger

logger = get_logger(__name__)

async def test_search():
    print("🚀 Initializing Test...")
    
    # Check client
    if not ki_kollega_service.client:
        print("❌ KIKollegaService client not initialized. Check API Keys.")
        return

    query = "brannsikkerhet og HMS"
    print(f"🔍 Testing Query: '{query}'")

    async with SessionLocal() as session:
        # 1. Generate Embedding
        print("   Generating embedding...")
        embedding = await ki_kollega_service._generate_embedding(query)
        
        if not embedding:
            print("❌ Failed to generate embedding.")
            return
        
        print(f"   ✅ Embedding generated (len={len(embedding)})")

        # DEBUG: Check DB counts
        from sqlalchemy import text
        cnt_all = (await session.execute(text("SELECT count(*) FROM text_content"))).scalar()
        cnt_emb = (await session.execute(text("SELECT count(*) FROM text_content WHERE embedding IS NOT NULL"))).scalar()
        cnt_vec = (await session.execute(text("SELECT count(*) FROM text_content WHERE search_vector IS NOT NULL"))).scalar()
        print(f"   📊 DB Stats: Total={cnt_all}, With Embeddings={cnt_emb}, With SearchVector={cnt_vec}")

        # 2. Run Hybrid Search
        print("   Running Hybrid Search...")
        results = await search_hybrid(session, query, embedding, limit=5)

        print(f"\n✅ Found {len(results)} results:\n")
        for i, res in enumerate(results, 1):
            print(f"{i}. Score: {res.get('score', 0.0):.4f} | RRF Score")
            print(f"   File: {res['source_file']}")
            print(f"   Snippet: {res['content'][:150]}...")
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_search())
