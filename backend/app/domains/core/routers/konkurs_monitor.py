"""
Konkurs Monitor Router – endpoints for checking bankruptcy/risk status of parties.
"""
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from fastapi import HTTPException, status as http_status
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()

_last_run: dict = {}


@router.get("/flagged")
async def get_flagged_parties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent alle parter med aktive risikoflags (CRITICAL / WARNING)."""
    from app.services.konkurs_monitor_service import get_flagged_parties
    return await get_flagged_parties(db)


@router.post("/run-all")
async def run_all_konkurs_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Kjør konkurs-/risikosjekk for alle parter i bakgrunnen. Krever ADMIN eller REGIONAL_MANAGER."""
    if current_user.role not in (UserRole.ADMIN, UserRole.REGIONAL_MANAGER):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Kun ADMIN eller REGIONAL_MANAGER kan kjøre full konkurssjekk",
        )
    from app.db.session import SessionLocal
    from app.services.konkurs_monitor_service import run_all_parties

    async def _run():
        global _last_run
        async with SessionLocal() as db:
            result = await run_all_parties(db)
            _last_run = result

    background_tasks.add_task(_run)
    return {"status": "started", "message": "Konkurssjekk kjøres i bakgrunnen for alle parter."}


@router.post("/run/{party_id}")
async def run_single_konkurs_check(
    party_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kjør konkurs-/risikosjekk for én part."""
    from app.services.konkurs_monitor_service import check_single_party
    result = await check_single_party(db, str(party_id))
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Part ikke funnet eller mangler gyldig orgnr")
    return result


@router.get("/status")
async def get_run_status(
    current_user: User = Depends(get_current_user),
):
    """Hent resultat fra siste konkurssjekk-kjøring."""
    return _last_run or {"status": "not_run_yet"}
