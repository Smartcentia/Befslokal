import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

import app.db.base  # noqa – ensure all models are registered
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.organisation import Organisation
from app.domains.core.models.property import Property as PropertyModel
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.unit import Unit as UnitModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class OrganisationCreate(BaseModel):
    name: str
    region_code: Optional[str] = None
    org_nr: Optional[str] = None
    contact_email: Optional[str] = None
    budget_target_nok: Optional[Decimal] = None
    is_active: bool = True


class OrganisationUpdate(BaseModel):
    name: Optional[str] = None
    region_code: Optional[str] = None
    org_nr: Optional[str] = None
    contact_email: Optional[str] = None
    budget_target_nok: Optional[Decimal] = None
    is_active: Optional[bool] = None


class OrganisationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: UUID
    name: str
    region_code: Optional[str] = None
    org_nr: Optional[str] = None
    contact_email: Optional[str] = None
    budget_target_nok: Optional[Decimal] = None
    is_active: bool


class OrganisationKPI(BaseModel):
    property_count: int
    user_count: int
    active_contracts: int
    total_monthly_rent_nok: float
    budget_target_nok: Optional[float]
    compliance_rate: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_admin(current_user: User):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=List[OrganisationOut])
async def list_organisations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List organisations. ADMIN sees all, others see only their own."""
    stmt = select(Organisation)
    if current_user.role != UserRole.ADMIN:
        if current_user.org_id is None:
            return []
        stmt = stmt.where(Organisation.org_id == current_user.org_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{org_id}", response_model=OrganisationOut)
async def get_organisation(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single organisation."""
    result = await db.execute(select(Organisation).where(Organisation.org_id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Non-admins can only see their own
    if current_user.role != UserRole.ADMIN and current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return org


@router.post("", response_model=OrganisationOut, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    payload: OrganisationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organisation. ADMIN only."""
    _require_admin(current_user)

    org = Organisation(**payload.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@router.patch("/{org_id}", response_model=OrganisationOut)
async def update_organisation(
    org_id: UUID,
    payload: OrganisationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an organisation. ADMIN only."""
    _require_admin(current_user)

    result = await db.execute(select(Organisation).where(Organisation.org_id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return org


@router.get("/{org_id}/properties")
async def get_organisation_properties(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List properties belonging to the organisation."""
    # Check access
    if current_user.role != UserRole.ADMIN and current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(PropertyModel).where(PropertyModel.org_id == org_id)
    )
    props = result.scalars().all()

    return [
        {
            "property_id": str(p.property_id),
            "name": p.name,
            "address": p.address,
            "city": p.city,
            "region": p.region,
        }
        for p in props
    ]


@router.get("/{org_id}/users")
async def get_organisation_users(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List users belonging to the organisation."""
    if current_user.role != UserRole.ADMIN and current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.domains.core.models.user import User as UserModel
    result = await db.execute(
        select(UserModel).where(UserModel.org_id == org_id)
    )
    users = result.scalars().all()

    return [
        {
            "user_id": str(u.user_id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "region": u.region,
        }
        for u in users
    ]


@router.get("/{org_id}/kpi", response_model=OrganisationKPI)
async def get_organisation_kpi(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """KPI summary for an organisation."""
    if current_user.role != UserRole.ADMIN and current_user.org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch org to get budget_target
    org_result = await db.execute(select(Organisation).where(Organisation.org_id == org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Property count
    try:
        prop_result = await db.execute(
            select(func.count()).select_from(PropertyModel).where(PropertyModel.org_id == org_id)
        )
        property_count = prop_result.scalar_one() or 0
    except Exception:
        property_count = 0

    # User count
    try:
        from app.domains.core.models.user import User as UserModel
        user_result = await db.execute(
            select(func.count()).select_from(UserModel).where(UserModel.org_id == org_id)
        )
        user_count = user_result.scalar_one() or 0
    except Exception:
        user_count = 0

    # Active contracts via units → properties in this org
    active_contracts = 0
    total_monthly_rent_nok = 0.0
    try:
        # Get property_ids for this org
        prop_ids_result = await db.execute(
            select(PropertyModel.property_id).where(PropertyModel.org_id == org_id)
        )
        property_ids = [row[0] for row in prop_ids_result.all()]

        if property_ids:
            # Get unit_ids for these properties
            unit_ids_result = await db.execute(
                select(UnitModel.unit_id).where(UnitModel.property_id.in_(property_ids))
            )
            unit_ids = [row[0] for row in unit_ids_result.all()]

            if unit_ids:
                # Count active contracts
                active_contracts_result = await db.execute(
                    select(func.count())
                    .select_from(ContractModel)
                    .where(
                        ContractModel.unit_id.in_(unit_ids),
                        ContractModel.status == "active",
                    )
                )
                active_contracts = active_contracts_result.scalar_one() or 0

                # Estimate monthly rent from caretaker_cost + cleaning_cost as proxy
                # (no dedicated monthly_rent column exists; use caretaker_cost sum as indicator)
                rent_result = await db.execute(
                    select(
                        func.coalesce(func.sum(ContractModel.caretaker_cost), 0.0)
                    )
                    .where(
                        ContractModel.unit_id.in_(unit_ids),
                        ContractModel.status == "active",
                    )
                )
                yearly_proxy = float(rent_result.scalar_one() or 0.0)
                total_monthly_rent_nok = round(yearly_proxy / 12, 2)
    except Exception:
        pass

    # Compliance rate: active_contracts / max(property_count, 1) as simple proxy
    compliance_rate = 0.0
    if property_count > 0:
        compliance_rate = round(min(active_contracts / property_count, 1.0), 2)

    budget_target = float(org.budget_target_nok) if org.budget_target_nok else None

    return OrganisationKPI(
        property_count=property_count,
        user_count=user_count,
        active_contracts=active_contracts,
        total_monthly_rent_nok=total_monthly_rent_nok,
        budget_target_nok=budget_target,
        compliance_rate=compliance_rate,
    )
