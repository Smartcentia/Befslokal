import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.vectordb import search_documents
from app.services.embeddings import generate_query_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search():
    query = "hvilke krav gjelder for rømning i barnevernsinstitusjoner?"
    logger.info(f"Testing search with query: '{query}'")
    
    try:
        # 1. Generate embedding for query
        embedding = generate_query_embedding(query)
        
        # 2. Search Vector DB
        # search_documents expects List[List[float]]
        results = search_documents([embedding], n_results=3)
        
        ids = results.get("ids", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        
        logger.info(f"Found {len(ids)} results:")
        for i in range(len(ids)):
            meta = metas[i]
            logger.info(f"[{i+1}] ID: {ids[i]} | Meta: {meta}")
            
    except Exception as e:
        logger.error(f"Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
