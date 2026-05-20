
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Any
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

router = APIRouter()

class SearchResultItem(BaseModel):
    id: str
    type: str  # "property", "contract", "deviation"
    title: str
    subtitle: Optional[str] = None
    url: str
    status: Optional[str] = None

class GlobalSearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]

@router.get("/global", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search terms"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Søk globalt på tvers av Eiendommer, Kontrakter og Avvik.
    """
    search_term = f"%{q}%"
    results = []

    # 1. Properties
    stmt_prop = select(Property).where(
        or_(
            Property.name.ilike(search_term),
            Property.address.ilike(search_term)
        )
    ).limit(limit)
    
    props = await db.execute(stmt_prop)
    for p in props.scalars().all():
        results.append(SearchResultItem(
            id=str(p.property_id),
            type="property",
            title=p.name or p.address,
            subtitle=p.address if p.name else None,
            url=f"/properties/{p.property_id}",
            status="Active" # Placeholder
        ))
        
    # 2. Contracts – søk på kategori, partnavn og kontraktnavn (external_data.contract_name, PostgreSQL)
    try:
        # .astext finnes på PostgreSQL JSONB; SQLite (test) bruker JSON uten astext
        contract_name_expr = Contract.external_data["contract_name"].astext.ilike(search_term)
        contract_conditions = or_(
            Contract.category.ilike(search_term),
            Party.name.ilike(search_term),
            contract_name_expr
        )
    except (AttributeError, TypeError):
        contract_conditions = or_(
            Contract.category.ilike(search_term),
            Party.name.ilike(search_term)
        )
    stmt_contract = select(Contract).join(Contract.party, isouter=True).where(
        contract_conditions
    ).options(selectinload(Contract.party)).limit(limit)
    
    contracts = await db.execute(stmt_contract)
    for c in contracts.scalars().all():
        party_name = c.party.name if c.party else "Ukjent part"
        results.append(SearchResultItem(
            id=str(c.contract_id),
            type="contract",
            title=f"{c.category} - {party_name}",
            subtitle=f"Utløper: {c.end_date}" if c.end_date else "Løpende",
            url=f"/contracts/{c.contract_id}",
            status=str(c.status) if c.status else None
        ))

    # 3. Deviations (RiskAssessment based on deviations.py)
    # Search in notes or risk_category
    stmt_risk = select(RiskAssessment).join(RiskAssessment.property, isouter=True).where(
        or_(
            RiskAssessment.notes.ilike(search_term),
            RiskAssessment.risk_category.ilike(search_term)
        )
    ).options(selectinload(RiskAssessment.property)).limit(limit)
    
    risks = await db.execute(stmt_risk)
    for r in risks.scalars().all():
        prop_name = r.property.name if r.property else "Ukjent eiendom"
        results.append(SearchResultItem(
            id=str(r.assessment_id),
            type="deviation",
            title=r.notes[:50] + "..." if r.notes and len(r.notes)>50 else (r.notes or "Uten beskrivelse"),
            subtitle=f"{prop_name} - {r.risk_category}",
            url=f"/deviations?id={r.assessment_id}",
            status="OPEN" # Based on deviations listing assumption
        ))
        
    # Sort results? For now just mix them or we could prioritize properties
    # Simple sort by type for grouping could work
    
    return GlobalSearchResponse(
        query=q,
        results=results[:10] # Hard limit total to 10 for dropdown
    )
