from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.core.property_access import check_property_access, filter_properties_by_access, get_user_accessible_property_ids
from app.domains.hms.models.risk import RiskAssessment, RiskFactor
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.property import Property
from pydantic import BaseModel, ConfigDict
from datetime import datetime

router = APIRouter()

# Default criticality factor (can be extended per property type later)
DEFAULT_CRITICALITY_FACTOR = 1.0
BUDGET_YEAR = 2026

# --- Schemas ---

class RiskAssessmentCreate(BaseModel):
    property_id: UUID
    risk_category: str
    risk_type: str # Mapped to notes/title
    severity: str # Mapped to category
    description: Optional[str] = None

class RiskAssessmentResponse(BaseModel):
    id: UUID
    property_id: UUID
    score: float
    category: str
    date: datetime
    title: str

    model_config = ConfigDict(from_attributes=True)

class PortfolioRiskStats(BaseModel):
    avg_score: float
    count_high: int
    count_medium: int
    count_low: int
    count_critical: int
    total_assessments: int
    top10: List[dict]
    # Internal Control Case statistics
    count_critical_deviations: int = 0
    total_deviations: int = 0


class PrioritizedPropertyItem(BaseModel):
    property_id: str
    address: str
    name: Optional[str] = None
    risk_score: float
    external_risk_score: float = 0.0
    economic_risk_score: float = 0.0
    risk_category: str
    annual_rent: float
    total_costs: float
    annual_cost: float
    priority_index: float
    reserve_factor: float
    budget_by_category: Dict[str, float]
    open_deviations: int = 0
    data_confidence: Optional[float] = None
    assessment_status: Optional[str] = None


class PrioritizedResponse(BaseModel):
    properties: List[PrioritizedPropertyItem]


# --- Endpoints ---

@router.get("/portfolio", response_model=PortfolioRiskStats)
async def get_portfolio_risk_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hent porteføljeoversikt for risiko (filtrert basert på property access).
    Aggregerer data fra SISTE RiskAssessment per property.
    """
    
    # 1. Subquery to find latest assessment date per property
    subquery = (
        select(
            RiskAssessment.property_id,
            func.max(RiskAssessment.assessment_date).label("latest_date")
        )
        .group_by(RiskAssessment.property_id)
        .subquery()
    )
    
    # 2. Join to get full assessment objects
    stmt = (
        select(RiskAssessment)
        .options(selectinload(RiskAssessment.property))
        .join(
            subquery,
            (RiskAssessment.property_id == subquery.c.property_id) &
            (RiskAssessment.assessment_date == subquery.c.latest_date)
        )
    )
    
    result = await db.execute(stmt)
    all_assessments = result.scalars().all()
    
    # 3. Filter assessments based on property access
    # Get unique properties from assessments
    properties = [a.property for a in all_assessments if a.property]
    accessible_properties = await filter_properties_by_access(
        db=db,
        user=current_user,
        properties=properties
    )
    accessible_property_ids = {p.property_id for p in accessible_properties}
    
    # Filter assessments to only those for accessible properties
    latest_assessments = [a for a in all_assessments if a.property_id in accessible_property_ids]
    
    if not latest_assessments:
        # Still need to check internal control cases even if no risk assessments
        # Use raw SQL to avoid ORM relationship loading
        from sqlalchemy import text
        ic_total_result = await db.execute(text("SELECT COUNT(*) FROM internal_control_cases"))
        total_deviations = ic_total_result.scalar() or 0
        
        ic_critical_result = await db.execute(text(
            "SELECT COUNT(*) FROM internal_control_cases WHERE priority IN ('high', 'critical')"
        ))
        count_critical_deviations = ic_critical_result.scalar() or 0
        
        return {
            "avg_score": 0.0,
            "count_high": 0,
            "count_medium": 0,
            "count_low": 0,
            "count_critical": 0,
            "total_assessments": 0,
            "top10": [],
            "count_critical_deviations": count_critical_deviations,
            "total_deviations": total_deviations
        }
        
    # Python aggregation (simpler than complex SQL string logic for categories)
    total_score = sum(a.overall_risk_score or 0 for a in latest_assessments)
    avg_score = total_score / len(latest_assessments)
    
    # Normalize categories to lowercase for counting
    categories = [str(a.risk_category).lower() if a.risk_category else "medium" for a in latest_assessments]
    
    count_high = categories.count("high")
    count_medium = categories.count("medium")
    count_low = categories.count("low")
    count_critical = categories.count("critical")
    
    # Top 10
    top_assessments = sorted(
        latest_assessments,
        key=lambda a: a.overall_risk_score or 0,
        reverse=True
    )[:10]
    
    top10 = []
    for a in top_assessments:
        prop_addr = a.property.address if a.property else "Unknown Property"
        top10.append({
            "entity_type": "property",
            "entity_id": str(a.property_id),
            "score": float(a.overall_risk_score or 0),
            "category": a.risk_category,
            "property_address": prop_addr,
            "assessment_date": a.assessment_date.isoformat() if a.assessment_date else None,
            "title": a.notes # Using notes as title based on seed strategy
        })
    
    # Query internal control cases for critical deviations count
    # Use raw SQL to avoid ORM relationship loading
    from sqlalchemy import text
    ic_total_result = await db.execute(text("SELECT COUNT(*) FROM internal_control_cases"))
    total_deviations = ic_total_result.scalar() or 0
    
    ic_critical_result = await db.execute(text(
        "SELECT COUNT(*) FROM internal_control_cases WHERE priority IN ('high', 'critical')"
    ))
    count_critical_deviations = ic_critical_result.scalar() or 0
        
    return {
        "avg_score": round(avg_score, 2),
        "count_high": count_high,
        "count_medium": count_medium,
        "count_low": count_low,
        "count_critical": count_critical,
        "total_assessments": len(latest_assessments),
        "top10": top10,
        "count_critical_deviations": count_critical_deviations,
        "total_deviations": total_deviations
    }

@router.get("/stats/external")
async def get_external_risk_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get aggregated statistics for EXTERNAL risk factors (NVE, Flood, Landslide).
    Filtrert basert på property access.
    """
    # Get user's accessible property IDs
    from app.core.property_access import get_user_accessible_property_ids
    accessible_property_ids = await get_user_accessible_property_ids(db, current_user)
    
    # Build query with property access filter
    if accessible_property_ids is None:
        # ADMIN - no filter needed
        property_filter = None
    elif len(accessible_property_ids) == 0:
        # No access - return empty stats
        return {
            "total_external_issues": 0,
            "by_category": {
                "flood": 0,
                "landslide": 0,
                "nve_proximity": 0,
                "building_age": 0,
                "other": 0
            },
            "details": []
        }
    else:
        # Filter by accessible property IDs via RiskAssessment
        property_filter = RiskAssessment.property_id.in_(accessible_property_ids)
    
    # 1. Count by factor name grouping
    # We want to know how many properties are affected by "Flood Risk", "Landslide", "NVE Proximity" etc.
    
    # Join RiskFactor with RiskAssessment to filter by property
    stmt = (
        select(
            RiskFactor.factor_name,
            func.count(RiskFactor.factor_id).label("count")
        )
        .join(RiskAssessment, RiskFactor.assessment_id == RiskAssessment.assessment_id)
        .where(RiskFactor.category == "external")
    )
    
    if property_filter is not None:
        stmt = stmt.where(property_filter)
    
    stmt = stmt.group_by(RiskFactor.factor_name).order_by(desc("count"))
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Process into clean categories
    stats = {
        "total_external_issues": 0,
        "by_category": {
            "flood": 0,
            "landslide": 0,
            "nve_proximity": 0,
            "building_age": 0,
            "other": 0
        },
        "details": []
    }
    
    for row in rows:
        name = row.factor_name.lower()
        count = row.count
        
        stats["total_external_issues"] += count
        
        # Categorize based on keywords
        if "flom" in name or "flood" in name:
            stats["by_category"]["flood"] += count
        elif "skred" in name or "landslide" in name:
            stats["by_category"]["landslide"] += count
        elif "nve" in name or "vannvei" in name:
            stats["by_category"]["nve_proximity"] += count
        elif "alder" in name or "year" in name:
            stats["by_category"]["building_age"] += count
        else:
            stats["by_category"]["other"] += count
            
        stats["details"].append({"factor": row.factor_name, "count": count})
        
    return stats

@router.post("/", response_model=RiskAssessmentResponse)
async def create_risk_assessment(
    risk: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Opprett et nytt avvik / risikovurdering (med property access check).
    """
    # Check property access (write access required to create risk assessment)
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(risk.property_id),
        require_write=True
    )
    
    # Map severity to score
    score_map = {
        "critical": 5.0,
        "high": 4.0,
        "medium": 3.0,
        "low": 1.0
    }
    
    new_risk = RiskAssessment(
        assessment_id=str(uuid4()),
        property_id=str(risk.property_id),
        assessment_date=datetime.now(),
        risk_category=risk.severity, # Using severity as category
        overall_risk_score=score_map.get(risk.severity.lower(), 2.0),
        notes=risk.risk_type + (f": {risk.description}" if risk.description else ""),
        assessed_by="User"
    )
    
    db.add(new_risk)
    await db.commit()
    await db.refresh(new_risk)

    # Create InternalControlCase for deviation tracking
    from app.domains.hms.models.internal_control import InternalControlCase
    desc = risk.description or ""
    case_title = (risk.risk_type or "Avvik") + (f": {desc[:60]}..." if len(desc) > 60 else (f": {desc}" if desc else ""))
    deviation_case = InternalControlCase(
        property_id=new_risk.property_id,
        risk_assessment_id=new_risk.assessment_id,
        title=case_title[:200],
        description=risk.description or f"Avvik registrert: {risk.risk_type}. Alvorlighetsgrad: {risk.severity}.",
        case_type="deviation",
        status="open",
        priority=risk.severity.lower() if risk.severity else "medium",
    )
    db.add(deviation_case)
    await db.commit()

    return {
        "id": new_risk.assessment_id,
        "property_id": new_risk.property_id,
        "score": new_risk.overall_risk_score,
        "category": new_risk.risk_category,
        "date": new_risk.assessment_date,
        "title": new_risk.notes
    }


@router.get("/prioritized", response_model=PrioritizedResponse)
async def get_prioritized_properties(
    year: int = Query(BUDGET_YEAR, description="Budsjettår", ge=2024, le=2030),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eiendommer sortert etter prioriteringsindeks for beslutningsstøtte.

    Prioritet = risikoscore × årskostnad × kritikalitetsfaktor.
    Reservefaktor: topp 10 % risiko = 1,5, lav 50 % = 0,5, resten = 1,0.
    Brukes til å styre hvor midler bør prioriteres.
    
    Nyhet: Returnerer også separate 'external_risk_score' (flom/skred) og 'economic_risk_score'.
    """
    from app.services.analytics.cost_analysis_service import get_property_cost_analysis

    # 1. Subquery: siste RiskAssessment per property
    subquery = (
        select(
            RiskAssessment.property_id,
            func.max(RiskAssessment.assessment_date).label("latest_date")
        )
        .group_by(RiskAssessment.property_id)
        .subquery()
    )

    # Eager load factors to calculate external risk score
    stmt = (
        select(RiskAssessment)
        .options(
            selectinload(RiskAssessment.property),
            selectinload(RiskAssessment.factors)
        )
        .join(
            subquery,
            (RiskAssessment.property_id == subquery.c.property_id) &
            (RiskAssessment.assessment_date == subquery.c.latest_date)
        )
    )
    result = await db.execute(stmt)
    all_assessments = result.scalars().all()

    # 2. Filter by property access
    properties = [a.property for a in all_assessments if a.property]
    accessible_properties = await filter_properties_by_access(
        db=db,
        user=current_user,
        properties=properties
    )
    accessible_property_ids = {p.property_id for p in accessible_properties}
    latest_assessments = [a for a in all_assessments if a.property_id in accessible_property_ids]

    if not latest_assessments:
        return PrioritizedResponse(properties=[])

    # 3. Batch: open deviations per property
    prop_ids_list = [str(a.property_id) for a in latest_assessments]
    prop_ids_uuid = [a.property_id for a in latest_assessments]
    dev_result = await db.execute(text("""
        SELECT property_id::text, COUNT(*) as cnt
        FROM internal_control_cases
        WHERE property_id = ANY(:pids)
          AND status NOT IN ('closed', 'lukket')
        GROUP BY property_id
    """), {"pids": prop_ids_uuid})
    dev_counts = {str(r[0]): r[1] for r in dev_result.fetchall()}

    # 4. Batch: budget by category per property
    budget_by_prop: Dict[str, Dict[str, float]] = {}
    for pid in prop_ids_list:
        budget_by_prop[pid] = {"property": 0.0, "operations": 0.0, "investment": 0.0, "other": 0.0}
    # SAVEPOINT: hvis budget-spørringen feiler (manglende tabell/skjema), må vi ikke
    # la transaksjonen stå i "aborted" — ellers feiler alle senere execute() med
    # InFailedSQLTransactionError (asyncpg).
    try:
        async with db.begin_nested():
            budget_result = await db.execute(text("""
                SELECT property_id::text, category, SUM(amount) as total
                FROM budget
                WHERE property_id = ANY(:pids) AND year = :year
                GROUP BY property_id, category
            """), {"pids": prop_ids_uuid, "year": year})
            budget_rows = budget_result.fetchall()
            for row in budget_rows:
                pid = str(row[0])
                cat = row[1] or "other"
                amt = float(row[2] or 0)
                if pid in budget_by_prop and cat in budget_by_prop[pid]:
                    budget_by_prop[pid][cat] = amt
    except Exception:
        pass  # Budget table may not exist

    # 5. Build items with cost data per property
    items: List[PrioritizedPropertyItem] = []
    for a in latest_assessments:
        pid = str(a.property_id)
        cost_analysis = await get_property_cost_analysis(db, pid)
        annual_rent = 0.0
        total_costs = 0.0
        
        # Financial metrics for Economic Risk
        cost_to_rent_ratio = 0.0
        
        if cost_analysis:
            annual_rent = cost_analysis.get("annual_rent") or 0.0
            summary = cost_analysis.get("summary") or {}
            total_costs = (
                (summary.get("property_costs") or 0) +
                (summary.get("operations_costs") or 0) +
                (summary.get("investment_costs") or 0) +
                (summary.get("other_costs") or 0)
            )
            if annual_rent > 0:
                cost_to_rent_ratio = total_costs / annual_rent

        annual_cost = annual_rent + total_costs
        risk_score = float(a.overall_risk_score or 0)
        
        # --- Economic Risk Calculation ---
        economic_risk_score = 0.0
        
        # Factor 1: Cost/Rent Ratio
        if cost_to_rent_ratio > 1.5:
            economic_risk_score += 40
        elif cost_to_rent_ratio > 1.0:
            economic_risk_score += 20
        
        # Factor 2: Budget Variance (Estimated from total vs budget)
        budget_cats = budget_by_prop.get(pid) or {}
        total_budget = sum(budget_cats.values())
        if total_budget > 0:
            variance_pct = (total_budget - total_costs) / total_budget
            if variance_pct < -0.10: # >10% over budget
                economic_risk_score += 30
            elif variance_pct < 0: # Over budget
                economic_risk_score += 10
        
        # Factor 3: Deviations cost (proxy: open deviations usually mean money)
        open_deviations = dev_counts.get(pid, 0)
        if open_deviations > 5:
            economic_risk_score += 30
        elif open_deviations > 0:
            economic_risk_score += 10
            
        economic_risk_score = min(100.0, economic_risk_score)

        # --- External Risk Calculation ---
        external_risk_score = 0.0
        if a.factors:
            for f in a.factors:
                if f.category == 'external':
                    external_risk_score += (f.calculated_score or 0)
        external_risk_score = min(100.0, external_risk_score)
        
        # Update priority index to use overall score as base, but could be adjusted
        criticality_factor = DEFAULT_CRITICALITY_FACTOR
        priority_index = risk_score * annual_cost * criticality_factor

        items.append(PrioritizedPropertyItem(
            property_id=pid,
            address=a.property.address if a.property else "",
            name=a.property.name if a.property else None,
            risk_score=risk_score,
            external_risk_score=round(external_risk_score, 1),
            economic_risk_score=round(economic_risk_score, 1),
            risk_category=(a.risk_category or "moderate").lower(),
            annual_rent=round(annual_rent, 2),
            total_costs=round(total_costs, 2),
            annual_cost=round(annual_cost, 2),
            priority_index=round(priority_index, 2),
            reserve_factor=1.0,  # Set below after sort
            budget_by_category={k: round(v, 2) for k, v in budget_cats.items()},
            open_deviations=open_deviations,
            data_confidence=a.data_confidence,
            assessment_status=a.assessment_status,
        ))

    # 6. Sort by risk_score descending, compute percentiles for reserve_factor
    items_sorted = sorted(items, key=lambda x: x.risk_score, reverse=True)
    n = len(items_sorted)
    for i, it in enumerate(items_sorted):
        if n == 0:
            it.reserve_factor = 1.0
        elif (i + 1) / n <= 0.10:
            it.reserve_factor = 1.5
        elif (i + 1) / n > 0.50:
            it.reserve_factor = 0.5
        else:
            it.reserve_factor = 1.0

    # 7. Final sort by priority_index descending
    items_final = sorted(items, key=lambda x: x.priority_index, reverse=True)
    # Re-apply reserve_factor from risk-based percentiles
    risk_order = {it.property_id: i for i, it in enumerate(items_sorted)}
    for it in items_final:
        idx = risk_order.get(it.property_id, 0)
        if n > 0 and (idx + 1) / n <= 0.10:
            it.reserve_factor = 1.5
        elif n > 0 and (idx + 1) / n > 0.50:
            it.reserve_factor = 0.5
        else:
            it.reserve_factor = 1.0

    return PrioritizedResponse(properties=items_final)


@router.get("/analyze/{property_id}")
async def analyze_property_risk(
    property_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger external risk analysis (NVE/Kartverket) (med property access check).
    """
    # Check property access
    prop = await check_property_access(
        db=db,
        user=current_user,
        property_id=property_id,
        require_write=False
    )
        
    if not prop.latitude or not prop.longitude:
        raise HTTPException(status_code=400, detail="Eiendom mangler koordinater")
        
    from app.services.external_data_orchestrator import ExternalDataOrchestrator
    orchestrator = ExternalDataOrchestrator(db)
    
    try:
        data = await orchestrator.fetch_risk_data(
            prop.latitude, 
            prop.longitude, 
            property_id=str(prop.property_id)
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

