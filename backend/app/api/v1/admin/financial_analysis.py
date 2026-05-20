"""
Financial Analysis API Router for Admin Panel
"""

from collections import Counter
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin_user
from app.services.analytics.financial_analysis_service import FinancialAnalysisService
from app.services.financials.property_data_completeness import (
    compute_all_property_completeness,
    compute_property_completeness_one,
    row_to_dict,
)
from app.domains.core.models.user import User

router = APIRouter(
    prefix="/financial-analysis",
    tags=["admin", "financial-analysis"],
    dependencies=[Depends(get_current_admin_user)]
)


@router.get("/search")
async def search_properties(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Search for properties by name and return financial summary
    
    Returns list of matching properties with:
    - Basic info (name, region, address)
    - Financial summary (rent, costs, total)
    - Data status (complete, missing_costs, missing_rent, missing_all)
    """
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    
    results = await FinancialAnalysisService.search_properties(db, query)
    
    return {
        "query": query,
        "count": len(results),
        "results": results
    }


@router.get("/property/{property_id}")
async def get_property_analysis(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get detailed financial analysis for a specific property
    
    Returns:
    - Complete financial breakdown
    - Cost by category
    - Top providers
    - Contract details
    """
    analysis = await FinancialAnalysisService.get_property_analysis(db, property_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Property not found")

    comp = await compute_property_completeness_one(db, property_id)
    if comp:
        cdict = row_to_dict(comp)
        analysis["completeness"] = cdict
        analysis["data_sources"] = {
            "kontrakt": {
                "annual_rent_contracted": analysis.get("rent"),
                "num_contracts": analysis.get("num_contracts"),
                "description": "Kontraktsfestet leie (sum amount_per_year på aktive kontrakter)",
            },
            "manuelle_utgifter": {
                "total": analysis.get("costs"),
                "num_lines": analysis.get("num_expenses"),
                "description": "Manuelle utgifter (external_data.financials.manual_expenses)",
            },
            "gl_regnskap": {
                "siste_ar_med_aktivitet": cdict.get("gl_last_year"),
                "faktisk_husleie": cdict.get("gl_faktisk_husleie"),
                "andre_kostnader": cdict.get("gl_andre_kostnader"),
                "description": "Bokført fra GL (siste år med transaksjoner for eiendommen)",
            },
            "score_0_100": cdict.get("score"),
            "issue_codes": cdict.get("issue_codes"),
        }

    return analysis


@router.get("/completeness-summary")
async def get_completeness_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    year_min: int = 2020,
    year_max: int = 2030,
):
    """
    Porteføljeoversikt: datatetthet-score og antall per avvikskode (tung query).
    """
    rows = await compute_all_property_completeness(db, year_min=year_min, year_max=year_max)

    codes: Counter[str] = Counter()
    for r in rows:
        for c in r.issue_codes:
            codes[c] += 1
    scores = [r.score for r in rows]
    mean_score = sum(scores) / len(scores) if scores else 0
    return {
        "year_min": year_min,
        "year_max": year_max,
        "property_count": len(rows),
        "mean_score": round(mean_score, 2),
        "count_score_below_50": sum(1 for s in scores if s < 50),
        "issue_code_counts": dict(sorted(codes.items(), key=lambda x: (-x[1], x[0]))),
    }


@router.get("/completeness/{property_id}")
async def get_completeness_one(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    year_min: int = 2020,
    year_max: int = 2030,
):
    """Én eiendoms kompletthetsrad (samme som i CSV-rapport)."""
    row = await compute_property_completeness_one(db, property_id, year_min=year_min, year_max=year_max)
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")
    return row_to_dict(row)


@router.get("/patterns")
async def get_common_patterns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get common cost patterns across all properties

    Returns:
    - Most common cost categories
    - Most common providers
    - Statistics
    """
    patterns = await FinancialAnalysisService.get_common_patterns(db)

    return patterns


@router.get("/property/{property_id}/cost-analysis")
async def get_property_cost_analysis(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get detailed cost analysis for a property with categorization and anomaly detection.

    Kategoriserer kostnader i:
    - Eiendomskostnader (husleie, fellesutgifter)
    - Driftskostnader (renhold, strøm, vakthold)
    - Investeringer (oppgraderinger, inventar)

    Flaggrer:
    - Uvanlig høye enkeltkostnader
    - Potensielle duplikater
    - Manglende leverandørinfo
    - Kostnader som overstiger forventet forhold til husleie
    """
    from app.services.analytics.cost_analysis_service import get_property_cost_analysis

    analysis = await get_property_cost_analysis(db, property_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Property not found")

    return analysis


@router.get("/property/{property_id}/forecast")
async def get_property_forecast(
    property_id: str,
    years_ahead: int = 3,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get ML-based cost forecast for a property using historical financial data.
    
    Uses Linear Regression to predict future costs based on historical spending patterns.
    
    Returns:
    - Forecast for next N years
    - Trend (Increasing/Decreasing/Stable)
    - Annual change estimate
    """
    from app.services.analytics.financial_analytics import financial_analytics_service
    
    try:
        # financial_analytics_service works with AsyncSession despite type hint
        forecast = await financial_analytics_service.forecast_future_costs(db, property_id, years_ahead)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@router.get("/property/{property_id}/anomalies")
async def get_property_anomalies(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Detect spending anomalies for a property using Isolation Forest ML algorithm.
    
    Identifies unusual spending patterns in historical financial data.
    
    Returns:
    - Anomaly count
    - List of anomalous years with amounts
    - Status (Normal/Anomalies Detected)
    """
    from app.services.analytics.financial_analytics import financial_analytics_service
    
    try:
        # financial_analytics_service works with AsyncSession despite type hint
        anomalies = await financial_analytics_service.detect_spending_anomalies(db, property_id)
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")
