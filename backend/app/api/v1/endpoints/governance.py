import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_superuser
from app.services.governance.classification_service import data_classification_service
from app.services.governance.schema_graph import build_schema_graph, to_mermaid_er
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

class DescriptionUpdate(BaseModel):
    table: str
    column: str
    description: str

@router.get("/catalog", dependencies=[Depends(get_current_active_superuser)])
async def get_data_catalog(db: AsyncSession = Depends(get_db)):
    """
    Get the full data governance catalog with classification.
    """
    try:
        return await data_classification_service.get_catalog(db)
    except Exception as e:
        logger.exception("governance/catalog failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/schema-graph", dependencies=[Depends(get_current_active_superuser)])
async def get_schema_graph(db: AsyncSession = Depends(get_db)):
    """
    Relasjonskart: alle tabeller og fremmednøkler (fra PostgreSQL), pluss ferdig Mermaid erDiagram.
    """
    try:
        def _run(sync_session):
            inspector = inspect(sync_session.connection())
            data = build_schema_graph(inspector)
            return {**data, "mermaid": to_mermaid_er(data)}

        return await db.run_sync(_run)
    except Exception as e:
        logger.exception("governance/schema-graph failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", dependencies=[Depends(get_current_active_superuser)])
async def get_governance_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overview statistics for the data governance dashboard.
    """
    try:
        return await data_classification_service.get_stats(db)
    except Exception as e:
        logger.exception("governance/stats failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/catalog/description", dependencies=[Depends(get_current_active_superuser)])
async def update_data_description(
    payload: DescriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the description for a specific data field.
    """
    await data_classification_service.update_description(
        db, 
        payload.table, 
        payload.column, 
        payload.description
    )
    return {"status": "success", "message": "Description updated"}
