"""
Behovsmeldinger – innmeldte behov og ønsker fra brukere.

Endepunkter:
  GET  /api/v1/behov         → liste alle (admin ser alle, bruker ser sine egne)
  POST /api/v1/behov         → opprett ny behovsmelding
  PATCH /api/v1/behov/{id}   → oppdater status/kommentar (admin)
  DELETE /api/v1/behov/{id}  → arkiver (soft-delete)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.models.behov import Behovsmelding

router = APIRouter(prefix="/behov", tags=["behovsmeldinger"])


class BehovCreate(BaseModel):
    tittel: str
    beskrivelse: Optional[str] = None
    kategori: Optional[str] = None
    prioritet: Optional[str] = None
    eiendom_navn: Optional[str] = None


class BehovUpdate(BaseModel):
    status: Optional[str] = None
    admin_kommentar: Optional[str] = None
    prioritet: Optional[str] = None


def _serialize(b: Behovsmelding) -> dict:
    return {
        "id": str(b.id),
        "tittel": b.tittel,
        "beskrivelse": b.beskrivelse,
        "kategori": b.kategori,
        "prioritet": b.prioritet,
        "status": b.status,
        "opprettet_av": b.opprettet_av,
        "eiendom_navn": b.eiendom_navn,
        "admin_kommentar": b.admin_kommentar,
        "opprettet_dato": b.opprettet_dato.isoformat() if b.opprettet_dato else None,
        "oppdatert_dato": b.oppdatert_dato.isoformat() if b.oppdatert_dato else None,
    }


@router.get("")
async def list_behov(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin ser alle, vanlige brukere ser kun sine egne."""
    is_admin = current_user.role == UserRole.ADMIN
    if is_admin:
        result = await db.execute(
            select(Behovsmelding)
            .where(Behovsmelding.er_arkivert == False)
            .order_by(Behovsmelding.opprettet_dato.desc())
        )
    else:
        result = await db.execute(
            select(Behovsmelding)
            .where(
                Behovsmelding.opprettet_av == current_user.email,
                Behovsmelding.er_arkivert == False,
            )
            .order_by(Behovsmelding.opprettet_dato.desc())
        )
    rows = result.scalars().all()
    return [_serialize(r) for r in rows]


@router.post("")
async def create_behov(
    data: BehovCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett ny behovsmelding."""
    b = Behovsmelding(
        tittel=data.tittel,
        beskrivelse=data.beskrivelse,
        kategori=data.kategori,
        prioritet=data.prioritet,
        eiendom_navn=data.eiendom_navn,
        opprettet_av=current_user.email,
        status="Ny",
    )
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return _serialize(b)


@router.patch("/{behov_id}")
async def update_behov(
    behov_id: str,
    data: BehovUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater status/kommentar. Admin kan oppdatere alle, bruker kan ikke."""
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin:
        raise HTTPException(status_code=403, detail="Kun admin kan oppdatere behovsmeldinger")

    result = await db.execute(
        select(Behovsmelding).where(Behovsmelding.id == uuid.UUID(behov_id))
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Ikke funnet")

    if data.status is not None:
        b.status = data.status
    if data.admin_kommentar is not None:
        b.admin_kommentar = data.admin_kommentar
    if data.prioritet is not None:
        b.prioritet = data.prioritet
    b.oppdatert_dato = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(b)
    return _serialize(b)


@router.delete("/{behov_id}")
async def archive_behov(
    behov_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Arkiver (soft-delete). Admin eller eier."""
    result = await db.execute(
        select(Behovsmelding).where(Behovsmelding.id == uuid.UUID(behov_id))
    )
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Ikke funnet")

    is_admin = current_user.role == UserRole.ADMIN
    is_owner = b.opprettet_av == current_user.email
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Ikke tilgang")

    b.er_arkivert = True
    await db.commit()
    return {"ok": True}
