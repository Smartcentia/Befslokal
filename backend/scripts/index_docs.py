import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.indexer import index_api_data
from app.services.embeddings import generate_embeddings
from app.services.vectordb import add_documents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCS_TO_INDEX = [
    "/Users/frank/BEFS3/KNOWME/docs/Krav til barnevernsinstitusjoner.txt",
    "/Users/frank/BEFS3/KNOWME/docs/Leietakers internkontroll_ En veileder (1).txt"
]

async def index_documentation():
    logger.info("--- Starting Documentation Indexing ---")
    
    for doc_path in DOCS_TO_INDEX:
        if not os.path.exists(doc_path):
            logger.warning(f"Document not found: {doc_path}")
            continue
            
        logger.info(f"Processing: {doc_path}")
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Create a document for vector DB
        # We manually use add_documents or a similar helper
        from uuid import uuid4
        doc_id = f"doc_{uuid4()}"
        
        # Metadata
        filename = os.path.basename(doc_path)
        meta = {
            "source": "documentation",
            "filename": filename,
            "type": "legal_requirement"
        }
        
        logger.info(f"Generating embedding for {filename} ({len(content)} chars)...")
        
        # Simple chunking (naive split by paragraphs or max chars)
        # For better results, we should use a proper text splitter, but splitting by double newline is a good start for .txt
        chunks = content.split("\n\n")
        chunks = [c.strip() for c in chunks if len(c.strip()) > 50] # Filter small chunks
        
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [meta.copy() for _ in range(len(chunks))]
        
        try:
            logger.info(f"Indexing {len(chunks)} chunks in batches...")
            
            BATCH_SIZE = 5
            for i in range(0, len(chunks), BATCH_SIZE):
                batch_chunks = chunks[i:i + BATCH_SIZE]
                batch_ids = chunk_ids[i:i + BATCH_SIZE]
                batch_metas = metadatas[i:i + BATCH_SIZE]
                
                try:
                    embeddings = generate_embeddings(batch_chunks)
                    add_documents(
                        texts=batch_chunks,
                        embeddings=embeddings,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    logger.info(f"Indexed batch {i//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1} ({len(batch_chunks)} items)")
                    await asyncio.sleep(1) # Rate limit politeness
                except Exception as batch_err:
                    logger.error(f"Error in batch {i}: {batch_err}")
                    # Continue to next batch instead of crashing
                    continue

        except Exception as e:
            logger.error(f"Failed to index {filename}: {e}")

    logger.info("--- Indexing Finished ---")

if __name__ == "__main__":
    asyncio.run(index_documentation())
