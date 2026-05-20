from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.search.search_service import search_fulltext

router = APIRouter()

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class DocumentIngest(BaseModel):
    title: str
    content: str
    source: str

@router.get("/")
async def root():
    return {"status": "Document/RAG MCP Server Active (Postgres)"}

@router.post("/search")
async def search_documents(query: SearchQuery, db: AsyncSession = Depends(get_db)):
    """
    Search for documents using Postgres Full-Text Search.
    """
    try:
        results = await search_fulltext(session=db, query=query.query, limit=query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_document(doc: DocumentIngest):
    """
    Ingest a new document. (Placeholder for Postgres Ingestion)
    """
    return {"status": "success", "message": f"Document '{doc.title}' received. Ingestion logic pending."}
