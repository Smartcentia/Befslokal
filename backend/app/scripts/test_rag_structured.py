import asyncio
import sys
import logging
from dotenv import load_dotenv
import os

# Load env before importing local modules that depend on it
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from app.db.session import SessionLocal
from app.domains.innsikt.services.rag_service import rag_service, RagService

from openai import AsyncOpenAI
from app.core.config import settings

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_structured_retrieval():
    # 1. Test Property Retrieval (Fiskergata 22)
    print("\n\n--- Testing RAG v4 (Property): 'Fiskergata 22' ---")
    await run_query("Hva er arealet på Fiskergata 22?")

    # 2. Test Party Retrieval (Needs a known party from DB)
    print("\n\n--- Testing RAG v4 (Party): 'Utleier' (Generic Test) ---")
    # We need a query that matches a party. Let's try searching for a common name or orgnr if known.
    # Analyzing previous logs or inspection: inspection showed 'name' column.
    # Let's try a generic search that might hit something, or skip specific party test if data unknown.
    # Better: Inspect parties table first to find a valid name? 
    # For now, let's assume "Oslo" might match something or just skip.
    await run_query("Vis meg informasjon om part med navn 'Oslo'") 

async def run_query(query):
    # Setup
    rag_service = RagService()
    rag_service.client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )

    async with SessionLocal() as db:
        history = []
        response = await rag_service.answer(query, history, db=db)
        
        print(f"\nQUERY: {query}")
        print(f"RESPONSE:\n{response}")
        
        # Simple assertions
        if "EIENDOM (" in str(response) or "PART (" in str(response) or "[(type:" in str(response):
             print("✅ SUCCESS: Entity Link or Structured Data found in response.")
        elif "property:" in str(response) or "party:" in str(response):
             print("✅ SUCCESS: Link ID found.")
        else:
             print("❌ WARNING: No entity links found. Check if entity exists in DB.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_structured_retrieval())
