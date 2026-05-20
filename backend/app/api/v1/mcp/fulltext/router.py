from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.search.search_service import search_fulltext, get_search_stats

router = APIRouter()

class FullTextSearchRequest(BaseModel):
    query: str
    limit: int = 5
    offset: int = 0

class FullTextSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[dict]
    offset: int
    limit: int

@router.get("/")
async def root():
    return {"status": "Full-Text Search MCP Server Active", "documents": 481}

@router.post("/search", response_model=FullTextSearchResponse)
async def search(request: FullTextSearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Search through migrated documents using PostgreSQL full-text search with Norwegian language support.
    """
    try:
        result = await search_fulltext(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full-text search error: {str(e)}")

@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    """
    Get statistics about searchable documents.
    """
    try:
        return await get_search_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
