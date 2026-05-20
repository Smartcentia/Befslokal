"""
Media Monitor router – API endpoints for nightly sentiment analysis dashboard.

Endpoints:
  GET  /api/v1/media-monitor/ranking   → sorted list (most negative first)
  POST /api/v1/media-monitor/run-all   → trigger full nightly run (admin only)
  POST /api/v1/media-monitor/run/{party_id} → single-party refresh
  GET  /api/v1/media-monitor/status    → last run status
"""
import logging
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple in-memory last-run status
_last_run_result: dict = {}


@router.get("/ranking")
async def get_sentiment_ranking(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return all tenants with media monitoring data, sorted by sentiment score ascending
    (most negative first). Requires authentication.
    """
    from app.services.media_monitor_service import get_tenant_sentiment_ranking
    try:
        results = await get_tenant_sentiment_ranking(db)
        return results
    except Exception as e:
        logger.exception("media_monitor ranking error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-all")
async def trigger_full_run(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Trigger a full media monitoring run for all active tenants.
    Runs in background.
    """
    global _last_run_result

    from app.services.media_monitor_service import run_all_active_tenants

    async def _bg(db_: AsyncSession):
        global _last_run_result
        _last_run_result = {"status": "running", "started_at": datetime.datetime.utcnow().isoformat()}
        result = await run_all_active_tenants(db_)
        _last_run_result = {**result, "finished_at": datetime.datetime.utcnow().isoformat()}

    background_tasks.add_task(_bg, db)
    return {"status": "started", "message": "Media monitoring kjores i bakgrunnen."}


@router.post("/run/{party_id}")
async def trigger_single_party(
    party_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run media monitoring for a single party and return result immediately.
    """
    from app.services.media_monitor_service import monitor_single_party
    result = await monitor_single_party(db, party_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Party ikke funnet eller mangler org.nr.")
    return result


@router.get("/status")
async def get_status(current_user=Depends(get_current_user)):
    """Return status of last media monitoring run."""
    return _last_run_result or {"status": "not_run_yet", "job_running": False}
