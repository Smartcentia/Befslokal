"""
FDVU Fase 5 – Dokumentintelligens API
Endepunkter for tekstuttrekk, embedding og semantisk søk i FDV-dokumenter.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.fdv.models.compliance import FdvDocument

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────
# POST /documents/{document_id}/process
# ─────────────────────────────────────────────

@router.post(
    "/documents/{document_id}/process",
    tags=["FDV Dokumentsøk"],
)
async def process_document_endpoint(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kjør tekstuttrekk og embedding-generering for et FDV-dokument.
    Prosessering skjer asynkront i bakgrunnen.
    """
    doc = await db.get(FdvDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")

    from app.services.doc_intelligence import process_document

    background_tasks.add_task(process_document, db, str(document_id))
    return {"status": "queued", "document_id": str(document_id)}


# ─────────────────────────────────────────────
# GET /documents/search
# ─────────────────────────────────────────────

@router.get(
    "/documents/search",
    tags=["FDV Dokumentsøk"],
)
async def search_documents(
    q: str = Query(..., min_length=1, description="Søketekst for semantisk søk"),
    property_id: Optional[uuid.UUID] = Query(None, description="Filtrer på eiendom"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantisk søk i FDV-dokumenter ved hjelp av pgvector cosine similarity.
    Returnerer dokumenter sortert etter relevans.
    """
    from app.services.doc_intelligence import semantic_search

    try:
        results = await semantic_search(
            db=db,
            query=q,
            property_id=str(property_id) if property_id else None,
            limit=limit,
        )
    except Exception as e:
        logger.error("semantic_search endpoint error: %s", e)
        raise HTTPException(status_code=500, detail=f"Søk feilet: {e}")

    return results


# ─────────────────────────────────────────────
# GET /documents/{document_id}/text
# ─────────────────────────────────────────────

@router.get(
    "/documents/{document_id}/text",
    tags=["FDV Dokumentsøk"],
)
async def get_document_text(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent ekstrahert tekst for et FDV-dokument."""
    doc = await db.get(FdvDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")

    return {
        "document_id": str(document_id),
        "title": doc.title,
        "extraction_status": doc.extraction_status,
        "page_count": doc.page_count,
        "text": doc.extracted_text or "",
    }


# ─────────────────────────────────────────────
# POST /documents/process-all
# ─────────────────────────────────────────────

@router.post(
    "/documents/process-all",
    tags=["FDV Dokumentsøk"],
)
async def process_all_documents(
    property_id: uuid.UUID = Query(..., description="Eiendom å prosessere dokumenter for"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Prosesser alle ubehandlede (pending/failed) FDV-dokumenter for en eiendom.
    Hvert dokument prosesseres asynkront i bakgrunnen.
    """
    result = await db.execute(
        select(FdvDocument).where(
            FdvDocument.property_id == property_id,
            FdvDocument.extraction_status.in_(["pending", "failed"]),
        )
    )
    docs = result.scalars().all()

    if not docs:
        return {"queued": 0, "message": "Ingen ubehandlede dokumenter funnet"}

    from app.services.doc_intelligence import process_document

    for doc in docs:
        background_tasks.add_task(process_document, db, str(doc.document_id))

    logger.debug("process-all: queued %d documents for property %s", len(docs), property_id)
    return {"queued": len(docs), "property_id": str(property_id)}
