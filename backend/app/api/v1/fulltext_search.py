"""
Full-text search API endpoints using PostgreSQL.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import SessionLocal
from app.services.search.search_service import search_fulltext, get_search_stats


router = APIRouter(prefix="/search", tags=["search"])


# Dependency
async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class SearchRequest(BaseModel):
    """Full-text search request."""
    query: str = Field(..., description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    language: str = Field('norwegian', description="Search language (norwegian, english)")


class SearchResult(BaseModel):
    """Individual search result."""
    text_id: str
    source_index_id: Optional[str]
    content: str
    source_file: Optional[str]
    source_type: Optional[str]
    category: Optional[str]
    chunk_index: int
    metadata: Optional[dict]
    contract_id: Optional[str]
    property_id: Optional[str]
    unit_id: Optional[str]
    created_at: Optional[str]
    rank: float
    headline: str


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    query: str
    total_results: int
    results: List[SearchResult]
    offset: int
    limit: int


class SearchStatsResponse(BaseModel):
    """Search statistics response."""
    total_documents: int
    indexed_documents: int
    categories: dict


@router.post("/fulltext", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Perform full-text search on document content using PostgreSQL.
    
    Supports Norwegian language stemming and ranking.
    Returns highlighted snippets and relevance scores.
    """
    
    results = await search_fulltext(
        session=session,
        query=request.query,
        limit=request.limit,
        offset=request.offset,
        language=request.language
    )
    
    return SearchResponse(
        query=request.query,
        total_results=len(results),
        results=[SearchResult(**r) for r in results],
        offset=request.offset,
        limit=request.limit
    )


@router.get("/stats", response_model=SearchStatsResponse)
async def search_statistics(
    session: AsyncSession = Depends(get_session)
):
    """
    Get statistics about searchable content.
    
    Returns counts of total documents, indexed documents, and breakdown by category.
    """
    
    stats = await get_search_stats(session)
    
    return SearchStatsResponse(**stats)
