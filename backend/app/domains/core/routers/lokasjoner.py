from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.api.deps import get_db
from app.domains.core.models.lokasjon import Lokasjon
from app.domains.core.models.property import Property

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class LokasjonCreate(BaseModel):
    navn: str
    adresse: Optional[str] = None
    lokalisering_id: Optional[str] = None
    region: Optional[str] = None
    merknad: Optional[str] = None


class LokasjonUpdate(BaseModel):
    navn: Optional[str] = None
    adresse: Optional[str] = None
    lokalisering_id: Optional[str] = None
    region: Optional[str] = None
    merknad: Optional[str] = None


class EiendomSummary(BaseModel):
    property_id: str
    name: Optional[str]
    address: Optional[str]
    region: Optional[str]


class LokasjonOut(BaseModel):
    lokasjon_id: str
    navn: str
    adresse: Optional[str]
    lokalisering_id: Optional[str]
    region: Optional[str]
    merknad: Optional[str]
    antall_eiendommer: int
    eiendommer: List[EiendomSummary]

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[LokasjonOut])
async def list_lokasjoner(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Lokasjon)
        .options(selectinload(Lokasjon.eiendommer))
        .order_by(Lokasjon.navn)
    )
    rows = (await db.execute(stmt)).scalars().all()
    result = []
    for lok in rows:
        result.append(LokasjonOut(
            lokasjon_id=str(lok.lokasjon_id),
            navn=lok.navn,
            adresse=lok.adresse,
            lokalisering_id=lok.lokalisering_id,
            region=lok.region,
            merknad=lok.merknad,
            antall_eiendommer=len(lok.eiendommer),
            eiendommer=[
                EiendomSummary(
                    property_id=str(e.property_id),
                    name=e.name,
                    address=e.address,
                    region=e.region,
                )
                for e in sorted(lok.eiendommer, key=lambda x: x.name or "")
            ],
        ))
    return result


@router.post("", response_model=LokasjonOut, status_code=201)
async def create_lokasjon(body: LokasjonCreate, db: AsyncSession = Depends(get_db)):
    lok = Lokasjon(**body.model_dump())
    db.add(lok)
    await db.commit()
    await db.refresh(lok)
    return LokasjonOut(
        lokasjon_id=str(lok.lokasjon_id),
        navn=lok.navn,
        adresse=lok.adresse,
        lokalisering_id=lok.lokalisering_id,
        region=lok.region,
        merknad=lok.merknad,
        antall_eiendommer=0,
        eiendommer=[],
    )


@router.patch("/{lokasjon_id}", response_model=LokasjonOut)
async def update_lokasjon(
    lokasjon_id: str,
    body: LokasjonUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Lokasjon)
        .options(selectinload(Lokasjon.eiendommer))
        .where(Lokasjon.lokasjon_id == uuid.UUID(lokasjon_id))
    )
    lok = (await db.execute(stmt)).scalar_one_or_none()
    if not lok:
        raise HTTPException(404, "Lokasjon ikke funnet")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lok, field, value)
    await db.commit()
    await db.refresh(lok)
    return LokasjonOut(
        lokasjon_id=str(lok.lokasjon_id),
        navn=lok.navn,
        adresse=lok.adresse,
        lokalisering_id=lok.lokalisering_id,
        region=lok.region,
        merknad=lok.merknad,
        antall_eiendommer=len(lok.eiendommer),
        eiendommer=[
            EiendomSummary(
                property_id=str(e.property_id),
                name=e.name,
                address=e.address,
                region=e.region,
            )
            for e in sorted(lok.eiendommer, key=lambda x: x.name or "")
        ],
    )


@router.delete("/{lokasjon_id}", status_code=204)
async def delete_lokasjon(lokasjon_id: str, db: AsyncSession = Depends(get_db)):
    lok = await db.get(Lokasjon, uuid.UUID(lokasjon_id))
    if not lok:
        raise HTTPException(404, "Lokasjon ikke funnet")
    await db.delete(lok)
    await db.commit()


@router.post("/{lokasjon_id}/eiendommer", response_model=LokasjonOut)
async def assign_eiendommer(
    lokasjon_id: str,
    property_ids: List[str],
    db: AsyncSession = Depends(get_db),
):
    """Replace the full set of properties assigned to this lokasjon."""
    lok_uuid = uuid.UUID(lokasjon_id)
    lok = (await db.execute(
        select(Lokasjon).options(selectinload(Lokasjon.eiendommer)).where(Lokasjon.lokasjon_id == lok_uuid)
    )).scalar_one_or_none()
    if not lok:
        raise HTTPException(404, "Lokasjon ikke funnet")

    # Unlink all current eiendommer from this lokasjon
    for p in lok.eiendommer:
        p.lokasjon_id = None

    # Link new set
    if property_ids:
        props = (await db.execute(
            select(Property).where(Property.property_id.in_([uuid.UUID(pid) for pid in property_ids]))
        )).scalars().all()
        for p in props:
            p.lokasjon_id = lok_uuid

    await db.commit()
    await db.refresh(lok)
    return LokasjonOut(
        lokasjon_id=str(lok.lokasjon_id),
        navn=lok.navn,
        adresse=lok.adresse,
        lokalisering_id=lok.lokalisering_id,
        region=lok.region,
        merknad=lok.merknad,
        antall_eiendommer=len(lok.eiendommer),
        eiendommer=[
            EiendomSummary(
                property_id=str(e.property_id),
                name=e.name,
                address=e.address,
                region=e.region,
            )
            for e in sorted(lok.eiendommer, key=lambda x: x.name or "")
        ],
    )


@router.get("/unassigned", response_model=List[EiendomSummary])
async def unassigned_eiendommer(db: AsyncSession = Depends(get_db)):
    """Properties not yet linked to any lokasjon."""
    stmt = select(Property).where(Property.lokasjon_id.is_(None)).order_by(Property.name)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        EiendomSummary(
            property_id=str(r.property_id),
            name=r.name,
            address=r.address,
            region=r.region,
        )
        for r in rows
    ]
