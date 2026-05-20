
import asyncio
import sys
import logging
from uuid import uuid4
from sqlalchemy import text, select
from app.db.session import SessionLocal
from app.services.vectordb import search_documents
from app.models.text_content import TextContent
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_vector_search():
    logger.info("Starting Vector Search Verification...")
    
    if not settings.ENABLE_VECTOR_SEARCH:
        logger.error("Vector search is disabled in settings. Aborting.")
        return

    async with SessionLocal() as db:
        try:
            # 1. Check pgvector extension
            logger.info("Checking pgvector extension...")
            result = await db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if not result.fetchone():
                logger.error("pgvector extension is NOT installed!")
                return
            logger.info("pgvector is installed.")

            # 2. Create a test user/embedding
            test_id = uuid4()
            test_content = f"This is a test document for vector search verification {test_id}"
            
            # Generate dummy embedding (normalized) or use real one if available?
            # Using random unit vector for 1536 dimensions
            import random
            import math
            
            def random_unit_vector(dim):
                vec = [random.gauss(0, 1) for _ in range(dim)]
                mag = math.sqrt(sum(x*x for x in vec))
                return [x/mag for x in vec]

            # In a real scenario, we'd use OpenAI. For this system check, we just want to verify DB logic.
            # But wait, search compares query embedding. 
            # Let's generate TWO vectors that are close, and one far.
            
            target_vec = random_unit_vector(1536)
            
            # Insert Test Data
            logger.info(f"Inserting test document {test_id}...")
            new_doc = TextContent(
                text_id=test_id,
                content=test_content,
                embedding=target_vec,
                source_type="test_script",
                chunk_index=0
            )
            db.add(new_doc)
            await db.commit()

            # 3. Perform Search
            logger.info("Performing vector search...")
            # We search with the SAME vector, should be distance ~0
            results = await search_documents(
                query_embeddings=[target_vec],
                n_results=1,
                db=db
            )
            
            # 4. Verify Results
            found_ids = results['ids'][0]
            found_distances = results['distances'][0]
            
            if str(test_id) in found_ids:
                idx = found_ids.index(str(test_id))
                dist = found_distances[idx]
                logger.info(f"SUCCESS: Found test document! Distance: {dist}")
                
                if dist < 0.0001:
                    logger.info("Distance logic is correct (near 0 for identical vector).")
                else:
                    logger.warning(f"Distance {dist} seems high for identical vector (precision issue?)")
            else:
                logger.error("FAILED: Test document NOT found in search results.")
                logger.error(f"Found IDs: {found_ids}")

            # Cleanup
            logger.info("Cleaning up test data...")
            # delete using ID
            await db.execute(text("DELETE FROM text_content WHERE text_id = :id"), {"id": test_id})
            await db.commit()
            
        except Exception as e:
            logger.error(f"Verification Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_vector_search())
