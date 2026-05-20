"""
Meldinger – bruker-til-bruker meldingssystem.

Endepunkter:
  GET  /api/v1/meldinger/innboks   → innboks (mottatte meldinger)
  GET  /api/v1/meldinger/utboks    → utboks (sendte meldinger)
  GET  /api/v1/meldinger/{id}      → enkelt melding (marker som lest)
  POST /api/v1/meldinger           → send ny melding
  PATCH /api/v1/meldinger/{id}/les → marker som lest
  DELETE /api/v1/meldinger/{id}    → arkiver (soft-delete for aktuell part)
  GET  /api/v1/meldinger/brukere   → liste alle brukere man kan sende til
  GET  /api/v1/meldinger/ulest-antall → antall uleste meldinger
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.models.melding import Melding

router = APIRouter(prefix="/meldinger", tags=["meldinger"])


class MeldingCreate(BaseModel):
    mottaker_email: str
    emne: str
    innhold: str
    svar_til_id: Optional[str] = None


def _serialize(m: Melding) -> dict:
    return {
        "id": str(m.id),
        "avsender_email": m.avsender_email,
        "avsender_navn": m.avsender_navn,
        "mottaker_email": m.mottaker_email,
        "mottaker_navn": m.mottaker_navn,
        "emne": m.emne,
        "innhold": m.innhold,
        "lest": m.lest,
        "svar_til_id": str(m.svar_til_id) if m.svar_til_id else None,
        "sendt_dato": m.sendt_dato.isoformat() if m.sendt_dato else None,
        "lest_dato": m.lest_dato.isoformat() if m.lest_dato else None,
    }


@router.get("/ulest-antall")
async def get_ulest_antall(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Antall uleste meldinger for innlogget bruker."""
    result = await db.execute(
        select(Melding).where(
            and_(
                Melding.mottaker_email == current_user.email,
                Melding.lest == False,
                Melding.arkivert_mottaker == False,
            )
        )
    )
    count = len(result.scalars().all())
    return {"antall": count}


@router.get("/innboks")
async def get_innboks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Innboks – mottatte meldinger for innlogget bruker."""
    result = await db.execute(
        select(Melding)
        .where(
            and_(
                Melding.mottaker_email == current_user.email,
                Melding.arkivert_mottaker == False,
            )
        )
        .order_by(Melding.sendt_dato.desc())
    )
    meldinger = result.scalars().all()
    return [_serialize(m) for m in meldinger]


@router.get("/utboks")
async def get_utboks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Utboks – sendte meldinger fra innlogget bruker."""
    result = await db.execute(
        select(Melding)
        .where(
            and_(
                Melding.avsender_email == current_user.email,
                Melding.arkivert_avsender == False,
            )
        )
        .order_by(Melding.sendt_dato.desc())
    )
    meldinger = result.scalars().all()
    return [_serialize(m) for m in meldinger]


@router.get("/brukere")
async def get_brukere(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent liste over alle aktive brukere man kan sende melding til."""
    result = await db.execute(
        text("SELECT email, full_name FROM users WHERE is_active = true AND email != :email ORDER BY full_name"),
        {"email": current_user.email},
    )
    rows = result.fetchall()
    return [{"email": r[0], "navn": r[1] or r[0]} for r in rows]


@router.get("/{melding_id}")
async def get_melding(
    melding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent enkelt melding og marker som lest."""
    try:
        uid = uuid.UUID(melding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig melding-ID")

    result = await db.execute(select(Melding).where(Melding.id == uid))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Melding ikke funnet")

    # Bare avsender eller mottaker kan se meldingen
    if m.avsender_email != current_user.email and m.mottaker_email != current_user.email:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    # Marker som lest hvis mottaker
    if m.mottaker_email == current_user.email and not m.lest:
        m.lest = True
        m.lest_dato = datetime.now(timezone.utc)
        await db.commit()

    return _serialize(m)


@router.post("")
async def send_melding(
    payload: MeldingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send en ny melding til en annen bruker."""
    # Finn mottaker
    mottaker_result = await db.execute(
        text("SELECT email, full_name FROM users WHERE email = :email AND is_active = true"),
        {"email": payload.mottaker_email},
    )
    mottaker_row = mottaker_result.fetchone()
    if not mottaker_row:
        raise HTTPException(status_code=404, detail=f"Bruker '{payload.mottaker_email}' ikke funnet")

    svar_til_uuid = None
    if payload.svar_til_id:
        try:
            svar_til_uuid = uuid.UUID(payload.svar_til_id)
        except ValueError:
            pass

    melding = Melding(
        id=uuid.uuid4(),
        avsender_email=current_user.email,
        avsender_navn=current_user.full_name or current_user.email,
        mottaker_email=mottaker_row[0],
        mottaker_navn=mottaker_row[1] or mottaker_row[0],
        emne=payload.emne,
        innhold=payload.innhold,
        lest=False,
        svar_til_id=svar_til_uuid,
    )
    db.add(melding)
    await db.commit()
    await db.refresh(melding)
    return _serialize(melding)


@router.patch("/{melding_id}/les")
async def marker_lest(
    melding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marker melding som lest."""
    try:
        uid = uuid.UUID(melding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig melding-ID")

    result = await db.execute(select(Melding).where(Melding.id == uid))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Melding ikke funnet")
    if m.mottaker_email != current_user.email:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    m.lest = True
    m.lest_dato = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.delete("/{melding_id}")
async def arkiver_melding(
    melding_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Arkiver melding (soft-delete for aktuell part)."""
    try:
        uid = uuid.UUID(melding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig melding-ID")

    result = await db.execute(select(Melding).where(Melding.id == uid))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Melding ikke funnet")

    if m.avsender_email == current_user.email:
        m.arkivert_avsender = True
    elif m.mottaker_email == current_user.email:
        m.arkivert_mottaker = True
    else:
        raise HTTPException(status_code=403, detail="Ingen tilgang")

    await db.commit()
    return {"ok": True}
