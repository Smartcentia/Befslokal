"""
Oversikt: eiendommer, enheter (avdelinger), kontrakter og leietakere (parties).
Én endepunkt som returnerer alle fire lister med tilgangskontroll.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.core.property_access import get_user_accessible_property_ids
from app.domains.core.models.property import Property as PropertyModel
from app.domains.core.models.unit import Unit as UnitModel
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.party import Party as PartyModel

router = APIRouter()

# --- Response DTOs (minimale for oversikt) ---


class PropertyOverviewItem(BaseModel):
    property_id: UUID
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    usage: Optional[str] = None

    class Config:
        from_attributes = True


class UnitOverviewItem(BaseModel):
    unit_id: UUID
    property_id: UUID
    property_name: Optional[str] = None
    purpose: Optional[str] = None
    area_sqm: Optional[float] = None

    class Config:
        from_attributes = True


class PartyOverviewItem(BaseModel):
    party_id: UUID
    name: str
    orgnr: Optional[str] = None

    class Config:
        from_attributes = True


class ContractOverviewItem(BaseModel):
    contract_id: UUID
    unit_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    status: Optional[str] = None
    party_name: Optional[str] = None
    property_name: Optional[str] = None
    property_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class OverviewResponse(BaseModel):
    properties: List[PropertyOverviewItem]
    units: List[UnitOverviewItem]
    contracts: List[ContractOverviewItem]
    parties: List[PartyOverviewItem]


@router.get("", response_model=OverviewResponse)
async def get_overview(
    limit: int = Query(2000, ge=1, le=5000, description="Maks antall per type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent oversikt over eiendommer, enheter (avdelinger), kontrakter og leietakere.
    Alle lister er filtrert etter brukerens tilgang (ADMIN ser alt).
    """
    allowed_ids = await get_user_accessible_property_ids(db, current_user)

    # 1) Eiendommer
    prop_stmt = select(PropertyModel).limit(limit)
    if allowed_ids is not None:
        prop_stmt = prop_stmt.where(PropertyModel.property_id.in_(allowed_ids))
    prop_result = await db.execute(prop_stmt)
    properties_db = prop_result.scalars().all()
    properties = [
        PropertyOverviewItem(
            property_id=p.property_id,
            name=p.name,
            address=p.address,
            city=p.city,
            region=p.region,
            usage=p.usage,
        )
        for p in properties_db
    ]

    # 2) Enheter (units) – kun for tilgjengelige eiendommer
    if allowed_ids is not None and not allowed_ids:
        units = []
    else:
        unit_stmt = (
            select(UnitModel, PropertyModel.name.label("property_name"))
            .join(PropertyModel, UnitModel.property_id == PropertyModel.property_id)
            .limit(limit)
        )
        if allowed_ids is not None:
            unit_stmt = unit_stmt.where(UnitModel.property_id.in_(allowed_ids))
        unit_result = await db.execute(unit_stmt)
        rows = unit_result.all()
        units = [
            UnitOverviewItem(
                unit_id=u.unit_id,
                property_id=u.property_id,
                property_name=prop_name,
                purpose=u.purpose,
                area_sqm=u.area_sqm,
            )
            for u, prop_name in rows
        ]

    # 3) Kontrakter med unit+property (filtreres via unit.property_id)
    contract_stmt = (
        select(ContractModel)
        .options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property),
            selectinload(ContractModel.party),
        )
        .limit(limit)
    )
    contract_result = await db.execute(contract_stmt)
    contracts_db = contract_result.scalars().all()
    contracts = []
    for c in contracts_db:
        if allowed_ids is not None:
            prop_id = c.unit.property_id if c.unit else None
            if prop_id is None or prop_id not in allowed_ids:
                continue
        prop_name = None
        if c.unit and c.unit.property:
            prop_name = c.unit.property.name or c.unit.property.address
        contracts.append(
            ContractOverviewItem(
                contract_id=c.contract_id,
                unit_id=c.unit_id,
                party_id=c.party_id,
                status=c.status,
                party_name=c.party.name if c.party else None,
                property_name=prop_name,
                property_id=c.unit.property_id if c.unit else None,
            )
        )

    # 4) Parter (leietakere) – alle (ingen property-filter)
    party_stmt = select(PartyModel).limit(limit)
    party_result = await db.execute(party_stmt)
    parties_db = party_result.scalars().all()
    parties = [
        PartyOverviewItem(party_id=p.party_id, name=p.name, orgnr=p.orgnr)
        for p in parties_db
    ]

    return OverviewResponse(
        properties=properties,
        units=units,
        contracts=contracts,
        parties=parties,
    )
