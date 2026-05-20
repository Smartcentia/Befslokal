"""API endpoints for vector search and indexing."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from app.api.deps import get_db
# Import dependencies from OUR migrated services
# Note: vector_search_contracts was in app.services.search in external. 
# We haven't migrated app.services.search yet. We verify its logic or implement it here.
from app.services.search.indexer import index_pdf_file_async, batch_index_all_files, index_contract_files
from app.services.vectordb import search_documents
from app.domains.core.models.property import Property
from app.core.config import settings

# Helper wrapper for vector search
async def vector_search_contracts(
    db: AsyncSession,
    query_text: str,
    n_results: int = 5,
    contract_id_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    from app.services.embeddings import generate_query_embedding
    
    # Generate embedding
    query_embedding = generate_query_embedding(query_text)
    if not query_embedding:
        return []
    
    # Prepare filter
    where = {}
    if contract_id_filter:
        where["contract_id"] = contract_id_filter
        
    # Search Vector DB
    # Note: this is blocking if using sync client.
    # Search Vector DB
    results = await search_documents(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where if where else None,
        db=db
    )
    
    # Process results structure from Vector DB
    # structure: {'ids': [['id1', ...]], 'distances': [[0.1...]], 'documents': [['text...']], 'metadatas': [[{...}]]}
    formatted_results = []
    
    if results and results.get('ids') and results['ids'][0]:
        ids = results['ids'][0]
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0] if results.get('distances') else [0] * len(ids)
        
        for i in range(len(ids)):
            formatted_results.append({
                "id": ids[i],
                "text": documents[i],
                "metadata": metadatas[i],
                "score": 1.0 - distances[i] # Convert distance to similarity score
            })
            
    return formatted_results

router = APIRouter()


class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query: str
    n_results: int = 5
    contract_id: Optional[str] = None


class VectorSearchResponse(BaseModel):
    """Response model for vector search."""
    query: str
    results: List[Dict[str, Any]]
    total_results: int


@router.post("/vector", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Utfør semantisk vektorsøk i kontrakt-dokumenter.
    """
    if not settings.ENABLE_VECTOR_SEARCH:
        raise HTTPException(
            status_code=503,
            detail="Vektorsøk er ikke aktivert"
        )
    
    try:
        results = await vector_search_contracts(
            db,
            query_text=request.query,
            n_results=request.n_results,
            contract_id_filter=request.contract_id
        )
        
        return VectorSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feil ved vektorsøk: {str(e)}"
        )


@router.get("/vector/status")
async def vector_search_status():
    """
    Hent status for vektorsøk-systemet.
    """
    from app.services.vectordb import get_collection_info
    try:
        info = get_collection_info()
        return {
            "enabled": settings.ENABLE_VECTOR_SEARCH,
            "collection": info,
            "embedding_deployment": getattr(settings, "OPENAI_MODEL", "unknown")
        }
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e)
        }


@router.post("/index/{file_id}")
async def index_file(
    file_id: UUID,
    re_index: bool = Query(False, description="Re-indekser hvis allerede indeksert"),
    db: AsyncSession = Depends(get_db),
):
    """
    Indekser en PDF-fil manuelt.
    """
    if not settings.ENABLE_VECTOR_SEARCH:
        raise HTTPException(
            status_code=503,
            detail="Vektorsøk er ikke aktivert"
        )
    
    try:
        result = await index_pdf_file_async(
            file_id=file_id,
            db=db,
            re_index=re_index
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feil ved indeksering: {str(e)}"
        )
