"""
Cost Management API - Endpoints for budget generation and cost forecasting.

Provides:
- Budget generation (synthetic budgets based on actual costs)
- Cost forecasting (predictive analysis)
- Budget variance analysis
- Monte Carlo simulations

Author: KI Kollega (AI Assistant)
Date: 2026-01-22
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.services.budget_generation_service import budget_generation_service
from app.services.cost_forecasting_service import cost_forecasting_service, CostForecastParams
from app.services.analytics.cost_analysis_service import aggregate_consumption_by_year

router = APIRouter()


# Request/Response Models
class BudgetGenerateRequest(BaseModel):
    """Request to generate synthetic budgets."""
    year: int = Field(..., description="Budget year", ge=2024, le=2030)
    inflation_rate: Optional[float] = Field(0.035, description="Inflation rate (default 3.5%)", ge=-0.10, le=0.20)
    property_ids: Optional[List[str]] = Field(None, description="Optional list of property UUIDs (default: all)")


def _default_years() -> List[int]:
    return [2024, 2025, 2026]


class BudgetGenerateFromConsumptionRequest(BaseModel):
    """Request to generate budgets from consumption (manual_expenses) with ±variance."""
    years: Optional[List[int]] = Field(
        default_factory=_default_years,
        description="Budget years (default 2024–2026)",
    )
    variance_pct: float = Field(0.2, description="Variance per category (default ±20%)", ge=0.0, le=0.5)
    property_ids: Optional[List[str]] = Field(None, description="Optional list of property UUIDs (default: all)")


class CostForecastRequest(BaseModel):
    """Request for cost forecast simulation."""
    property_id: Optional[str] = Field(None, description="Property UUID (null = portfolio-wide)")
    months_ahead: int = Field(12, description="Months to forecast", ge=1, le=36)
    kpi_adjustment: float = Field(0.0, description="Expected KPI adjustment", ge=-0.10, le=0.20)
    operations_variance: float = Field(0.0, description="Operations cost variance", ge=-0.30, le=0.30)
    include_monte_carlo: bool = Field(False, description="Run Monte Carlo simulation")
    monte_carlo_iterations: int = Field(1000, description="Monte Carlo iterations", ge=100, le=10000)


@router.post("/budgets/generate")
async def generate_budgets(
    request: BudgetGenerateRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate synthetic budgets for all properties based on actual costs.

    Since no budget data exists, this creates realistic budgets by:
    1. Analyzing last 12 months of actual costs
    2. Applying inflation adjustment (KPI)
    3. Adding realistic variance per cost category
    4. Storing in budget table

    Returns summary with total budget and properties processed.
    """
    try:
        result = await budget_generation_service.populate_budget_table(
            db=db,
            year=request.year,
            inflation_rate=request.inflation_rate,
            property_ids=request.property_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget generation failed: {str(e)}")


@router.post("/budgets/generate-from-consumption")
async def generate_budgets_from_consumption(
    request: BudgetGenerateFromConsumptionRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate budgets from actual consumption (manual_expenses) with ±variance per category.

    Default: years 2024, 2025, 2026. Uses cost_analysis_service to categorize expenses,
    then applies random variance (default ±20%) per category and distributes over 12 months.
    Properties with no consumption get fallback budget from contracts.
    """
    years = request.years or [2024, 2025, 2026]
    for y in years:
        if not (2024 <= y <= 2030):
            raise HTTPException(status_code=400, detail=f"År må være 2024–2030: {y}")
    try:
        total_budget_nok = 0.0
        total_entries = 0
        generated_total = 0
        failed_total = 0
        properties_processed = 0
        per_year: List[Dict[str, Any]] = []
        for year in years:
            result = await budget_generation_service.populate_budget_from_consumption(
                db=db,
                year=year,
                variance_pct=request.variance_pct,
                property_ids=request.property_ids
            )
            total_budget_nok += result.get("total_budget_nok", 0)
            total_entries += result.get("entries_created", 0)
            generated_total += result.get("generated", 0)
            failed_total += result.get("failed", 0)
            if result.get("properties_processed"):
                properties_processed = result["properties_processed"]
            per_year.append({"year": year, **result})
        return {
            "years": years,
            "variance_pct": request.variance_pct,
            "properties_processed": properties_processed,
            "generated": generated_total,
            "failed": failed_total,
            "total_budget_nok": round(total_budget_nok, 2),
            "entries_created": total_entries,
            "per_year": per_year,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget generation from consumption failed: {str(e)}")


@router.post("/budgets/generate-from-gl")
async def generate_budgets_from_gl(
    property_id: Optional[str] = Body(None, description="Property UUID (null = alle eiendommer)"),
    year: int = Body(2026, description="Budsjettår", ge=2024, le=2030),
    variance_pct: float = Body(0.1, description="Varians ±% per kategori", ge=0.0, le=0.5),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generer budsjett for 2026 basert på faktiske GL-transaksjoner.

    Henter reelle kostnader fra gl_transactions, proraterer til årsestimater,
    og oppretter budsjettoppføringer per måned og kategori.
    Brukes når man har importert CSV-data men mangler budsjett.
    """
    from sqlalchemy import text
    from app.models.financial_models import Budget
    import uuid as uuid_lib
    import random
    import math

    try:
        # Hent eiendommer som skal prosesseres
        if property_id:
            prop_result = await db.execute(
                text("SELECT property_id FROM properties WHERE property_id = :pid"),
                {"pid": property_id}
            )
            prop_rows = prop_result.fetchall()
        else:
            prop_result = await db.execute(text("SELECT property_id FROM properties"))
            prop_rows = prop_result.fetchall()

        if not prop_rows:
            raise HTTPException(status_code=404, detail="Ingen eiendommer funnet")

        # GL-kategorier → budsjett-kategori
        from app.services.analytics.cost_analysis_service import categorize_expense
        entries_created = 0
        properties_processed = 0
        total_budget = 0.0

        for (prop_id,) in prop_rows:
            gl_result = await db.execute(text("""
                SELECT
                    COALESCE(NULLIF(TRIM(category), ''), 'other') as cat,
                    SUM(amount) as total,
                    COUNT(DISTINCT month) as months_covered
                FROM gl_transactions
                WHERE property_id = :pid
                  AND year = :yr
                  AND amount > 0
                GROUP BY COALESCE(NULLIF(TRIM(category), ''), 'other')
            """), {"pid": str(prop_id), "yr": year})
            gl_rows = gl_result.fetchall()

            if not gl_rows:
                continue

            # Bygg kategori-totaler og proratér til årsbudsjett
            cat_totals: Dict[str, float] = {}
            for (cat_raw, total, months) in gl_rows:
                mapped = categorize_expense(cat_raw.upper() if cat_raw else "other")
                cat_key = mapped.value
                months_covered = max(int(months or 1), 1)
                # Proratér: del på faktiske måneder og gang med 12
                annual_estimate = float(total or 0) / months_covered * 12
                cat_totals[cat_key] = cat_totals.get(cat_key, 0.0) + annual_estimate

            if not cat_totals:
                continue

            # Slett eksisterende budsjett for dette år og eiendom
            await db.execute(text("""
                DELETE FROM budget
                WHERE property_id = :pid AND year = :yr
            """), {"pid": str(prop_id), "yr": year})

            # Opprett månedlige budsjettoppføringer per kategori
            for cat_key, annual_total in cat_totals.items():
                monthly_base = annual_total / 12
                for month in range(1, 13):
                    # Tilsett litt varians per måned
                    variance = 1.0 + (random.uniform(-variance_pct, variance_pct) * 0.5)
                    monthly_amount = monthly_base * variance
                    budget_entry = Budget(
                        budget_id=uuid_lib.uuid4(),
                        property_id=prop_id,
                        year=year,
                        month=month,
                        category=cat_key,
                        amount=round(monthly_amount, 2),
                        created_at=datetime.utcnow()
                    )
                    db.add(budget_entry)
                    entries_created += 1
                    total_budget += monthly_amount

            properties_processed += 1

        await db.commit()
        return {
            "status": "success",
            "year": year,
            "properties_processed": properties_processed,
            "entries_created": entries_created,
            "total_budget_nok": round(total_budget, 2),
            "message": f"Budsjett for {year} generert fra GL-transaksjoner for {properties_processed} eiendom(mer)"
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Budsjetgenerering fra GL feilet: {str(e)}")


@router.get("/costs/consumption-by-year")
async def get_consumption_by_year(
    property_id: str = Query(..., description="Property UUID"),
    years: str = Query("2024,2025,2026", description="Comma-separated years"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Hent forbruk (manual_expenses) per år for en eiendom.

    Aggregerer utgifter etter date-felt (2024-01-01, 2026-Q1 osv.).
    Returnerer total og per kategori (property, operations, investment, other) per år.
    """
    from sqlalchemy import text

    year_list = [int(y.strip()) for y in years.split(",") if y.strip()]
    if not year_list:
        year_list = [2024, 2025, 2026]
    for y in year_list:
        if not (2020 <= y <= 2030):
            raise HTTPException(status_code=400, detail=f"Ugyldig år: {y}")

    result = await db.execute(text("""
        SELECT property_id, name, external_data
        FROM properties
        WHERE property_id = :property_id
    """), {"property_id": property_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    ext = row[2]
    if ext is None:
        ext = {}
    elif isinstance(ext, str):
        try:
            ext = json.loads(ext) if ext else {}
        except Exception:
            ext = {}
    else:
        ext = dict(ext) if ext else {}

    property_data = {"property_id": str(row[0]), "name": row[1], "external_data": ext}
    by_year = aggregate_consumption_by_year(property_data, years=year_list)
    # Serialize int keys to str for JSON
    by_year_serialized = {str(k): v for k, v in by_year.items()}
    return {
        "property_id": property_id,
        "property_name": row[1],
        "years": year_list,
        "consumption_by_year": by_year_serialized,
    }


@router.get("/budgets/missing")
async def get_properties_without_budget(
    year: int = Query(2026, description="Budget year", ge=2024, le=2030),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Eiendommer som mangler budsjett for valgt år.
    Bruk for å sjekke at alle har budsjett; kjør deretter POST /budgets/generate-from-consumption for å fylle.
    """
    from sqlalchemy import text

    result = await db.execute(text("""
        SELECT p.property_id, p.name
        FROM properties p
        LEFT JOIN budget b ON b.property_id = p.property_id AND b.year = :year
        WHERE b.property_id IS NULL
        ORDER BY p.name
    """), {"year": year})
    rows = result.fetchall()
    return {
        "year": year,
        "count": len(rows),
        "property_ids": [str(r[0]) for r in rows],
        "properties": [{"property_id": str(r[0]), "name": r[1]} for r in rows],
    }


@router.get("/budgets/summary")
async def get_budgets_summary(
    year: int = Query(2026, description="Budget year", ge=2024, le=2030),
    data_source: str | None = Query(
        None,
        description="Eksakt match på Budget.data_source (f.eks. 'finance_dept_2026'). Utelat for å hente alle.",
    ),
    exclude_data_source: str | None = Query(
        None,
        description="NOT-match på Budget.data_source (f.eks. 'finance_dept_2026' for å hente alt unntatt økonomi-budsjett).",
    ),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Portfolio budsjett-oppsummering for et gitt år.
    Brukes av økonomioversikt og eiendomsliste.
    Returnerer alltid 200; ved manglende tabell eller feil returneres tom oppsummering.

    Filtrering:
      - Utelatt data_source/exclude_data_source: summér alle rader for året (legacy-oppførsel)
      - data_source satt: kun rader med eksakt match
      - exclude_data_source satt: alle rader unntatt eksakt match (NULL telles som ikke-match og inkluderes)
    """
    from sqlalchemy import text

    try:
        # Bygg WHERE-klausul dynamisk slik at vi unngår å lekke ubrukte parametere.
        clauses = ["year = :year"]
        params: Dict[str, Any] = {"year": year}
        if data_source is not None:
            clauses.append("data_source = :data_source")
            params["data_source"] = data_source
        if exclude_data_source is not None:
            clauses.append("(data_source IS NULL OR data_source <> :exclude_data_source)")
            params["exclude_data_source"] = exclude_data_source

        where_sql = " AND ".join(clauses)
        sql = f"""
            SELECT property_id, SUM(amount) AS total_annual_budget
            FROM budget
            WHERE {where_sql}
            GROUP BY property_id
        """
        result = await db.execute(text(sql), params)
        rows = result.fetchall()
        by_property = [{"property_id": str(r[0]), "total_annual_budget": round(float(r[1]), 2)} for r in rows]
        total_budget_nok = sum(p["total_annual_budget"] for p in by_property)

        # Fallback til external_data kun når INGEN filter er satt (legacy-oppførsel for oversiktssiden)
        if not by_property and data_source is None and exclude_data_source is None:
            ext_res = await db.execute(text("""
                SELECT COALESCE(SUM(
                    (external_data->'financials'->>'cost_summary')::float
                ), 0)
                FROM properties
                WHERE external_data->'financials'->>'cost_summary' IS NOT NULL
            """))
            total_budget_nok = float(ext_res.scalar() or 0)
            return {
                "year": year,
                "total_budget_nok": round(total_budget_nok, 2),
                "by_property": [],
                "data_source": "external_data_fallback",
                "message": "Budsjettdata ikke importert. Viser aggregat fra ekstern kostdata.",
            }

        return {
            "year": year,
            "total_budget_nok": round(total_budget_nok, 2),
            "by_property": by_property,
            "data_source": "budget_table",
            "filter": {
                "data_source": data_source,
                "exclude_data_source": exclude_data_source,
            },
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("budgets/summary failed (returning empty): %s", e)
        return {
            "year": year,
            "total_budget_nok": 0.0,
            "by_property": [],
            "data_source": "error",
        }


@router.get("/budgets/{property_id}")
async def get_property_budget(
    property_id: str,
    year: int = Query(..., description="Budget year", ge=2024, le=2030),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get budget for a specific property and year.

    Returns monthly budget breakdown by category.
    """
    from sqlalchemy import text

    result = await db.execute(text("""
        SELECT year, month, category, SUM(amount) as budgeted_amount
        FROM budget
        WHERE property_id = :property_id AND year = :year
        GROUP BY year, month, category
        ORDER BY month, category
    """), {"property_id": property_id, "year": year})

    rows = result.fetchall()

    if not rows:
        # Returner tom struktur i stedet for 404 – manglende budsjett er gyldig tilstand
        return {
            "property_id": property_id,
            "year": year,
            "total_annual_budget": 0.0,
            "by_category": {
                "property": 0.0,
                "operations": 0.0,
                "investment": 0.0,
                "other": 0.0,
            },
            "monthly_budgets": [],
        }

    budget_data = []
    total = 0.0
    by_category: Dict[str, float] = {}

    for row in rows:
        cat = row[2]
        amt = float(row[3])
        budget_data.append({
            "year": row[0],
            "month": row[1],
            "category": cat,
            "amount": amt
        })
        total += amt
        by_category[cat] = by_category.get(cat, 0.0) + amt

    return {
        "property_id": property_id,
        "year": year,
        "total_annual_budget": round(total, 2),
        "by_category": {
            "property": round(by_category.get("property", 0.0), 2),
            "operations": round(by_category.get("operations", 0.0), 2),
            "investment": round(by_category.get("investment", 0.0), 2),
            "other": round(by_category.get("other", 0.0), 2),
        },
        "monthly_budgets": budget_data
    }


@router.post("/costs/forecast")
async def forecast_costs(
    request: CostForecastRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate cost forecast with optional Monte Carlo simulation.

    Returns:
    - Historical costs (last 12 months)
    - Baseline forecast (next N months)
    - Budget data for comparison
    - Budget variance (actual vs budget)
    - Monte Carlo confidence intervals (P10/P50/P90)

    Example response:
    {
      "property_id": "abc-123",
      "historical": [{month, total_cost}, ...],
      "forecast": [{month, forecasted_cost}, ...],
      "budget": [{month, budgeted_amount}, ...],
      "budget_variance": {variance_nok, variance_pct, status},
      "monte_carlo": {p10, p50, p90},
      "summary": {total_forecasted_cost, best_case_annual, worst_case_annual}
    }
    """
    params = CostForecastParams(
        property_id=request.property_id,
        months_ahead=request.months_ahead,
        kpi_adjustment=request.kpi_adjustment,
        operations_variance=request.operations_variance,
        include_monte_carlo=request.include_monte_carlo,
        monte_carlo_iterations=request.monte_carlo_iterations
    )

    try:
        forecast = await cost_forecasting_service.generate_cost_forecast(db, params)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost forecast failed: {str(e)}")


@router.get("/costs/forecast/{property_id}")
async def get_cached_forecast(
    property_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cached cost forecast for property (24h TTL).

    If no cache exists, generates new forecast with default parameters.
    """
    # Check cache first
    from sqlalchemy import text

    result = await db.execute(text("""
        SELECT result, created_at
        FROM forecast_cache
        WHERE property_id = :property_id
          AND forecast_type = 'cost_forecast'
          AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
    """), {"property_id": property_id})

    row = result.fetchone()

    if row:
        return {
            **row[0],
            "cached": True,
            "cache_age_hours": round((datetime.now() - row[1]).total_seconds() / 3600, 1)
        }

    # No cache, generate new forecast
    params = CostForecastParams(
        property_id=property_id,
        months_ahead=12,
        include_monte_carlo=False
    )

    forecast = await cost_forecasting_service.generate_cost_forecast(db, params)

    # Cache the result
    from sqlalchemy.dialects.postgresql import insert
    import uuid
    import json

    stmt = insert(dict(
        forecast_id=uuid.uuid4(),
        property_id=property_id,
        forecast_type='cost_forecast',
        parameters=json.dumps({"months_ahead": 12}),
        result=json.dumps(forecast),
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24)
    ))

    await db.execute(stmt)
    await db.commit()

    return {**forecast, "cached": False}


@router.get("/costs/analysis/budget-variance")
async def get_budget_variance_analysis(
    region: Optional[str] = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Portfolio-wide budget variance analysis.

    Compares actual costs vs budget across all properties,
    grouped by region and category.

    Returns properties over/under budget with variance percentages.
    """
    from sqlalchemy import text

    current_year = datetime.now().year
    current_month = datetime.now().month

    query_filter = ""
    params = {"year": current_year}

    if region:
        query_filter = "AND p.region = :region"
        params["region"] = region

    try:
        result = await db.execute(text(f"""
            WITH actual_costs AS (
                SELECT
                    p.property_id,
                    p.name,
                    p.region,
                    SUM(g.amount) as total_actual
                FROM properties p
                JOIN gl_transactions g ON g.property_id = p.property_id
                WHERE g.year = :year AND g.month <= {current_month}
                {query_filter}
                GROUP BY p.property_id, p.name, p.region
            ),
            budgets AS (
                SELECT
                    b.property_id,
                    SUM(b.amount) as total_budget
                FROM budget b
                WHERE b.year = :year AND b.month <= {current_month}
                GROUP BY b.property_id
            )
            SELECT
                a.property_id,
                a.name,
                a.region,
                a.total_actual,
                COALESCE(b.total_budget, 0) as total_budget,
                CASE
                    WHEN b.total_budget > 0 THEN
                        ((a.total_actual - b.total_budget) / b.total_budget) * 100
                    ELSE 0
                END as variance_pct
            FROM actual_costs a
            LEFT JOIN budgets b ON a.property_id = b.property_id
            ORDER BY variance_pct DESC
        """), params)
        rows = result.fetchall()
    except Exception as e:
        await db.rollback()
        import logging
        logging.getLogger(__name__).warning("budget-variance query failed: %s", e)
        return {
            "year": current_year,
            "month": current_month,
            "region": region,
            "message": "Ingen GL-data importert ennå. Last opp CSV via Admin → Økonomidata.",
            "data_source": "none",
            "portfolio_summary": {
                "total_actual": 0,
                "total_budget": 0,
                "variance_nok": 0,
                "variance_pct": 0,
                "properties_over_budget": 0,
                "properties_under_budget": 0,
            },
            "properties": [],
        }

    properties = []
    total_actual = 0
    total_budget = 0

    for row in rows:
        prop_data = {
            "property_id": str(row[0]),
            "name": row[1],
            "region": row[2],
            "actual": round(float(row[3]), 2),
            "budget": round(float(row[4]), 2),
            "variance_pct": round(float(row[5]), 1),
            "status": "over_budget" if float(row[5]) > 0 else "under_budget"
        }
        properties.append(prop_data)

        total_actual += float(row[3])
        total_budget += float(row[4])

    portfolio_variance_pct = ((total_actual - total_budget) / total_budget * 100) if total_budget > 0 else 0

    return {
        "year": current_year,
        "month": current_month,
        "region": region,
        "portfolio_summary": {
            "total_actual": round(total_actual, 2),
            "total_budget": round(total_budget, 2),
            "variance_nok": round(total_actual - total_budget, 2),
            "variance_pct": round(portfolio_variance_pct, 1),
            "properties_over_budget": sum(1 for p in properties if p["variance_pct"] > 0),
            "properties_under_budget": sum(1 for p in properties if p["variance_pct"] <= 0)
        },
        "properties": properties
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "cost_management",
        "timestamp": datetime.now().isoformat()
    }
