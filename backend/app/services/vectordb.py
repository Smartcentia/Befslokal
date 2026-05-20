"""Vector DB Service - PostgreSQL pgvector implementation."""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.text_content import TextContent
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

async def search_documents(
    query_embeddings: List[List[float]],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """
    Search for documents using pgvector cosine similarity.
    Returns format compatible with ChromaDB style: {'ids': [[]], 'distances': [[]], ...}
    """
    if not db:
        logger.error("No database session provided for vector search")
        return {"ids": [], "distances": [], "documents": [], "metadatas": []}

    if not query_embeddings:
        return {"ids": [], "distances": [], "documents": [], "metadatas": []}

    query_embedding = query_embeddings[0] # Handle single query for now

    try:
        # Calculate distance
        distance_col = TextContent.embedding.cosine_distance(query_embedding).label("distance")
        
        # Build query
        stmt = select(TextContent, distance_col).order_by(distance_col).limit(n_results)

        # Apply basic filters
        if where:
            if "contract_id" in where and where["contract_id"]:
                stmt = stmt.where(TextContent.contract_id == where["contract_id"])

        result = await db.execute(stmt)
        rows = result.all()

        ids = []
        documents = []
        metadatas = []
        distances = []

        for row, dist in rows:
            # source_file is the UUID of the file, text_id is the chunk ID
            ids.append(str(row.text_id)) 
            documents.append(row.content)
            metadatas.append(row.additional_metadata or {})
            distances.append(float(dist) if dist is not None else 0.0)

        return {
            "ids": [ids],
            "distances": [distances],
            "documents": [documents],
            "metadatas": [metadatas]
        }

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"ids": [], "distances": [], "documents": [], "metadatas": []}

def add_documents(documents: list):
    """Deprecated: Use indexer.py directly which writes to postgres."""
    pass

def get_collection_info():
    return {
        "name": "text_content",
        "type": "PostgreSQL pgvector",
        "status": "Active"
    }

def delete_documents(ids=None, where=None):
    """Stub: Deletion handled via indexer/DB directly."""
    pass
