
import asyncio
import sys
import logging
from app.db.session import SessionLocal
from app.domains.innsikt.services.rag_service import rag_service

# Configure Logger to see internal RAG logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_retrieval():
    """
    Test the RAG v3 pipeline with a difficult OCR term.
    """
    query = "parkering"  # Known problem term
    
    print(f"\n--- Testing RAG v3: '{query}' ---\n")
    
    async with SessionLocal() as db:
        # Mock history
        history = []
        
        # 1. Run Answer
        # We expect logs to show Postgres search running.
        response = await rag_service.answer(query, history, db=db)
        
        print("\n--- RESPONSE FROM AI ---\n")
        print(response)
        
        print("\n--- META VERIFICATION ---\n")
        if "PostgreSQL" in response:
             print("SUCCESS: Source attribution found in response content (if verbosity allows) or logs confirmed fusion.")
        else:
             print("Check logs above to confirm fusion.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_rag_retrieval())
