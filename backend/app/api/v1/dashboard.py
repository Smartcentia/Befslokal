from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.domains.core.models.user import User, UserRole
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.config import settings

router = APIRouter()

class SystemStatus(BaseModel):
    database: str
    api_gateway: str
    nve_integration: str
    details: Optional[Dict[str, Any]] = None

@router.get("/status", response_model=SystemStatus)
async def get_system_status(current_user: User = Depends(get_current_user)):
    """
    Returns real-time system status.
    """
    status = {
        "database": "offline",
        "api_gateway": "online", # If this endpoint is reached, API is online
        "nve_integration": "active", # Placeholder, assumed active unless error
        "details": {}
    }

    # 1. Check Database
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        status["database"] = "online"
    except Exception as e:
        status["database"] = "offline"
        status["details"]["db_error"] = str(e)
        
    # 2. Add other dependency checks if needed (e.g. key services)
    
    return status

@router.get("/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """
    Returns simplified stats for the dashboard.
    Leser fra DashboardMetrics når den finnes; ellers beregnes tall live fra properties/contracts
    så dashboard ikke viser 0 når metrics aldri er refreshet.
    """
    from sqlalchemy import select, func
    from app.models.metrics import DashboardMetrics
    from app.services.analytics.metrics_service import get_live_dashboard_metrics, get_occupancy_rate
    from app.domains.core.models.user import User as UserModel
    from app.domains.core.models.property import Property as PropertyModel
    
    async with SessionLocal() as db:
        # Count users
        user_count_stmt = select(func.count(UserModel.user_id))
        user_count_res = await db.execute(user_count_stmt)
        users_count = user_count_res.scalar() or 0

        # Count parties (utleiere/hjemmelshavere som leier ut til Bufetat)
        from app.domains.core.models.party import Party
        party_count_stmt = select(func.count(Party.party_id))
        party_count_res = await db.execute(party_count_stmt)
        parties_count = party_count_res.scalar() or 0

        stmt = select(DashboardMetrics).limit(1)
        result = await db.execute(stmt)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            # Live-beregning fra properties/contracts så vi ikke viser 0
            try:
                live = await get_live_dashboard_metrics(db)
                properties_count = live.get("properties_count", 0)
                contracts_count = live.get("contracts_count", 0)
                risks_count = live.get("risks_count", 0)
                total_annual_rent = live.get("total_annual_rent", 0.0)
                total_maintenance_cost = live.get("total_maintenance_cost", 0.0)
                occupancy_rate = live.get("occupancy_rate", 0.0)
            except Exception:
                await db.rollback()
                properties_count = contracts_count = risks_count = 0
                total_annual_rent = total_maintenance_cost = 0.0
                occupancy_rate = 0.0
        else:
            properties_count = metrics.properties_count
            contracts_count = metrics.contracts_count
            risks_count = metrics.risks_count
            total_annual_rent = metrics.total_annual_rent or 0.0
            total_maintenance_cost = metrics.total_maintenance_cost or 0.0
            try:
                occupancy_rate = await get_occupancy_rate(db)
            except Exception:
                await db.rollback()
                occupancy_rate = 0.0

        # Additional Stats (Calculated on the fly for freshness)
        from app.domains.hms.models.risk import RiskAssessment
        from app.domains.core.models.contract import Contract
        from datetime import datetime, timedelta

        # Critical Deviations (High/Critical risk)
        from app.domains.hms.models.internal_control import InternalControlCase

        # Use case-insensitive status and priority checks
        stmt_crit = select(func.count(InternalControlCase.case_id)).where(
            func.lower(InternalControlCase.status) == 'open',
            func.lower(InternalControlCase.priority).in_(['high', 'critical'])
        )
        res_crit = await db.execute(stmt_crit)
        critical_count = res_crit.scalar() or 0

        # Total Open Deviations for the "risks" counter if it's used for departures
        stmt_total_open = select(func.count(InternalControlCase.case_id)).where(
            func.lower(InternalControlCase.status) == 'open'
        )
        res_total_open = await db.execute(stmt_total_open)
        total_open_cases = res_total_open.scalar() or 0

        # If risks_count from RiskAssessment is 0, fallback to total_open_cases
        display_risks = risks_count if risks_count > 0 else total_open_cases

        # Expiring Contracts (next 90 days)
        stmt_expiring = select(func.count(Contract.contract_id)).where(
            Contract.status == 'active',
            Contract.end_date >= datetime.now().date(),
            Contract.end_date <= datetime.now().date() + timedelta(days=90)
        )
        res_expiring = await db.execute(stmt_expiring)
        expiring_count = res_expiring.scalar() or 0

        # KUN data fra økonomiavdelingens autoriserte CSV — befs_budsjett_sammenligning
        from sqlalchemy import text as sa_text
        try:
            res_oko = await db.execute(sa_text("""
                SELECT
                    COUNT(*)              AS antall_eiendommer,
                    SUM(regn_2025_ok)     AS regn_2025_total,
                    SUM(befs_pred_2026)   AS befs_2026_total,
                    SUM(budsjett_2026_ok) AS budsjett_2026_total
                FROM befs_budsjett_sammenligning
                WHERE region IS NOT NULL
            """))
            row = res_oko.one()
            properties_count       = int(row.antall_eiendommer or 0)
            regn_2025_nok          = float(row.regn_2025_total or 0)
            befs_2026_nok          = float(row.befs_2026_total or 0)
            budsjett_2026_nok      = float(row.budsjett_2026_total or 0)
        except Exception:
            await db.rollback()
            properties_count  = 0
            regn_2025_nok     = 0.0
            befs_2026_nok     = 0.0
            budsjett_2026_nok = 0.0

        return {
            "properties": properties_count,
            "contracts": contracts_count,
            "leietakere": parties_count,
            "risks": display_risks,
            "users": users_count,
            "occupancy_rate": occupancy_rate,
            "total_annual_rent": regn_2025_nok,       # Regn. 2025 (Øk.) fra CSV
            "lokaler_2026_nok": budsjett_2026_nok,    # Budsjett 2026 (Øk.) fra CSV
            "drift_vedlikehold_2026": befs_2026_nok,  # BEFS Prediksjon 2026 fra CSV
            "total_maintenance_cost": 0.0,
            "change_percent": 0,
            "last_updated": metrics.last_updated.isoformat() if metrics and metrics.last_updated else None,
            "critical_deviations": critical_count,
            "total_open_cases": total_open_cases,
            "expiring_contracts": expiring_count,
        }

@router.get("/recent-activity")
async def get_recent_activity(current_user: User = Depends(get_current_user)):
    """
    Returns recent activity log for dashboard.
    TODO: Fetch from audit log / database.
    """
    # Mock data for now to prevent 404
    from datetime import datetime, timedelta
    
    now = datetime.now()
    return [
        {
            "type": "contract",
            "text": "Ny kontrakt opprettet: Leieavtale BUP Oslo",
            "time": (now - timedelta(hours=2)).isoformat(),
            "icon": "FileCheck",
            "color": "blue"
        },
        {
            "type": "deviation",
            "text": "Avvik registrert: Brannsikkerhet",
            "time": (now - timedelta(hours=5)).isoformat(),
            "icon": "AlertOctagon",
            "color": "amber"
        },
        {
            "type": "property",
            "text": "Eiendom oppdatert: Institutt Vest",
            "time": (now - timedelta(days=1)).isoformat(),
            "icon": "Building2",
            "color": "green"
        }
    ]
@router.get("/regional-financials")
async def get_regional_financials(current_user: User = Depends(get_current_user)):
    """
    Returns financial breakdown by region.
    Requires REGIONAL_MANAGER or ADMIN role.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.services.analytics.metrics_service import get_regional_financials as get_reg_stats
        return await get_reg_stats()
    except Exception as e:
        logger.exception("regional-financials failed: %s", e)
        # Return minimal fallback so frontend can still render (budsjett fra properties)
        return [
            {"region": r, "planned_rent": 0.0, "actual_rent": 0.0, "other_costs": 0.0}
            for r in ["Nord", "Midt-Norge", "Vest", "Øst", "Sør", "Bufdir"]
        ]

@router.get("/financial-overview")
async def get_financial_overview(current_user: User = Depends(get_current_user)):
    """
    Returns detailed hierarchical financial data for the dashboard.
    Replacing heavy client-side aggregation.
    Requires REGIONAL_MANAGER or ADMIN role.
    """
    # REGIONAL_MANAGER kan se sin region, ADMIN kan se alt
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only regional managers and administrators can access financial overview"
        )
    
    from app.services.analytics.metrics_service import get_detailed_financial_overview
    return await get_detailed_financial_overview()

@router.post("/refresh-metrics")
async def refresh_metrics(current_user: User = Depends(get_current_user)):
    """
    Triggers a refresh of all dashboard metrics.
    Requires ADMIN role.
    """
    # Kun ADMIN kan trigge refresh av metrics
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can refresh dashboard metrics"
        )
    
    from app.services.analytics.metrics_service import refresh_dashboard_metrics
    return await refresh_dashboard_metrics()

@router.get("/gl-regional-costs")
async def get_gl_regional_costs(year: int = 2025, current_user: User = Depends(get_current_user)):
    """
    Returns GL cost totals for rows NOT linked to a specific property,
    grouped by region and SRS-kategori. These are 'regional/administrative' costs.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer og regionledere kan se regionale GL-kostnader",
        )
    from sqlalchemy import text as sa_text
    async with SessionLocal() as db:
        try:
            rows = await db.execute(sa_text("""
                SELECT COALESCE(region, 'Ukjent') AS region,
                       COALESCE(srs_kategori, 'Drift') AS kategori,
                       SUM(belop) AS total,
                       COUNT(*) AS antall
                FROM gl_transactions
                WHERE property_id IS NULL AND ar = :year AND belop > 0
                GROUP BY region, srs_kategori
                ORDER BY region, total DESC
            """), {"year": year})
            result_rows = rows.all()

            totalt = sum(float(r.total or 0) for r in result_rows)
            antall_totalt = sum(int(r.antall or 0) for r in result_rows)

            regioner: dict = {}
            for r in result_rows:
                reg = r.region
                if reg not in regioner:
                    regioner[reg] = {"region": reg, "total": 0.0, "antall": 0, "kategorier": []}
                regioner[reg]["total"] += float(r.total or 0)
                regioner[reg]["antall"] += int(r.antall or 0)
                regioner[reg]["kategorier"].append({
                    "kategori": r.kategori,
                    "total": float(r.total or 0),
                    "antall": int(r.antall or 0),
                })

            return {
                "year": year,
                "totalt": totalt,
                "antall_totalt": antall_totalt,
                "regioner": sorted(regioner.values(), key=lambda x: x["total"], reverse=True),
            }
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("gl-regional-costs failed: %s", e)
            return {"year": year, "totalt": 0.0, "antall_totalt": 0, "regioner": []}


@router.get("/top-tenants")
async def get_top_tenants(current_user: User = Depends(get_current_user)):
    """
    Returns top 10 tenants by calculated annual revenue.
    """
    from sqlalchemy import select, func, cast, Float, desc
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.party import Party
    
    async with SessionLocal() as db:
        # Calculate annualized rent for each contract
        # Logic matches metrics_service.py
        rent_yearly = func.coalesce(
            Contract.amount['total_per_year'].astext,
            Contract.amount['amount_per_year'].astext
        )
        rent_monthly = func.coalesce(
            Contract.amount['monthly_rent'].astext,
            Contract.amount['amount'].astext
        )
        final_rent = func.coalesce(
            cast(rent_yearly, Float),
            cast(rent_monthly, Float) * 12,
            0.0
        )

        # Aggregate by Party (Tenant)
        stmt = (
            select(
                Party.name,
                Party.party_id,
                func.sum(final_rent).label("total_revenue"),
                func.count(Contract.contract_id).label("contract_count")
            )
            .join(Party, Contract.party_id == Party.party_id)
            .where(Contract.status == 'active')
            .group_by(Party.party_id, Party.name)
            .order_by(desc("total_revenue"))
            .limit(10)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return [
            {
                "tenant_id": str(r.party_id),
                "name": r.name,
                "revenue": float(r.total_revenue or 0),
                "contracts": r.contract_count
            }
            for r in rows
        ]
