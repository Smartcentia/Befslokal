from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Any
from app.api.deps import get_db
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.hms.models.risk import RiskAssessment

router = APIRouter()

@router.get("/recent-activity")
async def get_recent_activity(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated recent activity (new properties, risk assessments, contracts).
    """
    activities = []
    
    # 1. Recent Properties
    props_query = select(Property).order_by(Property.created_at.desc()).limit(3)
    props_result = await db.execute(props_query)
    props = props_result.scalars().all()
    
    for p in props:
        activities.append({
            "type": "property_created",
            "text": f"Ny eiendom registrert: {p.address}",
            "time": p.created_at, # Frontend will format
            "icon": "Building2",
            "color": "text-blue-500"
        })

    # 2. Recent Risks
    # Optimized: Fetch RiskAssessment AND Property.address in one query (JOIN)
    risks_query = (
        select(RiskAssessment, Property.address)
        .join(Property, RiskAssessment.property_id == Property.property_id)
        .order_by(RiskAssessment.assessment_date.desc())
        .limit(3)
    )
    risks_result = await db.execute(risks_query)
    # result rows are (RiskAssessment, address_string)
    risks_data = risks_result.all()
    
    for r, p_addr in risks_data:
        activities.append({
            "type": "risk_assessment",
            "text": f"Risikovurdering ({r.risk_category}): {p_addr or 'Ukjent eiendom'}",
            "time": r.assessment_date,
            "icon": "AlertOctagon",
            "color": "text-green-500" if r.risk_category == "Low" else "text-amber-500"
        })

    # Sort by time
    activities.sort(key=lambda x: x["time"] or "", reverse=True)
    
    return activities[:5] # Return top 5

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get high-level stats for the dashboard, including financial totals.
    """
    from app.domains.core.models.contract import Contract
    from sqlalchemy import func
    
    # 1. Fetch Key Counts (Fast)
    p_count_res = await db.execute(select(func.count()).select_from(Property))
    properties_count = p_count_res.scalar() or 0
    
    c_count_res = await db.execute(select(func.count()).select_from(Contract))
    contracts_count = c_count_res.scalar() or 0
    
    r_count_res = await db.execute(select(func.count()).select_from(RiskAssessment))
    risks_count = r_count_res.scalar() or 0
    
    # 2. Calculate Financials (Requires iteration)
    # Fetch all properties (needed for calculating maintenance cost from JSONB)
    all_props_res = await db.execute(select(Property))
    all_props = all_props_res.scalars().all()
    
    total_maintenance = 0.0
    for p in all_props:
        if p.external_data and isinstance(p.external_data, dict):
            financials = p.external_data.get('financials', {})
            # Sum up various cost components
            total_maintenance += float(financials.get('total_spend_csv', 0) or 0)
            total_maintenance += float(financials.get('total_manual_expenses', 0) or 0)
            
    print(f"DEBUG: Calculated Total Maintenance: {total_maintenance}")

    # Fetch active contracts (needed for rent income)
    active_contracts_res = await db.execute(select(Contract).where(Contract.status == 'active'))
    active_contracts = active_contracts_res.scalars().all()
    
    total_rent = 0.0
    for c in active_contracts:
        if c.amount:
            # replicate frontend logic: check if object has amount_per_year, else use direct value
            if isinstance(c.amount, dict):
                total_rent += float(c.amount.get('amount_per_year', 0) or 0)
            elif isinstance(c.amount, (int, float)):
                total_rent += float(c.amount)
            # ignore string or null
            
    return {
        "properties": properties_count,
        "contracts": contracts_count,
        "risks": risks_count,
        "total_annual_rent": round(total_rent, 2),
        "total_maintenance_cost": round(total_maintenance, 2)
    }
