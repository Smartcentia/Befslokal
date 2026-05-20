from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.services.prediction_service import BudgetPredictionService

router = APIRouter()


class PredictBudgetRequest(BaseModel):
    year: int = Field(default=2027, ge=2025, le=2035, description="Target budget year")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Level smoothing (høyere = mer vekt på nyere data)")
    beta: float = Field(default=0.3, ge=0.0, le=1.0, description="Trend smoothing")
    inflation: float = Field(default=0.035, ge=0.0, le=0.2, description="Inflasjonsfallback for eiendommer med ett år data")
    history_from: int = Field(default=2021, ge=2018, le=2025, description="Første år i historikken")


@router.post("/predict-budget", response_model=dict[str, Any])
async def predict_budget(
    request: PredictBudgetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generer Holt-Winters budsjettprediksjon for alle eiendommer med GL-data.

    Algoritme: Holt's Linear Exponential Smoothing (dobbel) — gir nyere år mer vekt.
    Resultater lagres i budget-tabellen med is_synthetic=True og data_source='holt_winters_{year}'.

    Krever ADMIN-rolle.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer kan generere budsjettprediksjon",
        )

    result = await BudgetPredictionService.predict_all_properties(
        db=db,
        target_year=request.year,
        alpha=request.alpha,
        beta=request.beta,
        inflation=request.inflation,
        history_from=request.history_from,
    )

    return result


@router.get("/budget-summary", response_model=dict[str, Any])
async def get_budget_summary(
    year: int = Query(default=2027, ge=2025, le=2035),
    scenario: str = Query(
        "xgb70",
        description="Budsjett-scenario: xgb70 eller xgb50 (suffiks i budget.data_source, ikke «prosent bruk»)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer predikert budsjett for alle eiendommer, gruppert per region.
    Inkluderer også regionale/administrative kostnader (GL-transaksjoner uten eiendom)
    estimert med 2-års inflasjon på 2025-aktuals.

    Prediksjonsrader lagres som data_source = holt_winters_{år}_xgb70 | xgb50 (se prediction_service).
    Eldre miljø kan ha kun holt_winters_{år} — vi prøver primær kilde først, deretter fallback.

    Tilgjengelig for alle innloggede brukere (viser kun egne eiendommer for ikke-admin).
    """
    try:
        scenario_norm = (scenario or "xgb70").strip().lower()
        if scenario_norm not in ("xgb70", "xgb50"):
            scenario_norm = "xgb70"
        primary_source = f"holt_winters_{year}_{scenario_norm}"
        legacy_source = f"holt_winters_{year}"

        # 1. Hent predikerte budsjetter fra budget-tabellen, join med properties
        async def _fetch_budget(for_source: str):
            return await db.execute(text("""
            SELECT
                b.property_id::text,
                p.name          AS property_name,
                p.address,
                p.city,
                p.region,
                b.category,
                SUM(b.amount)   AS total
            FROM budget b
            JOIN properties p ON p.property_id = b.property_id
            WHERE b.year        = :year
              AND b.data_source = :source
            GROUP BY b.property_id, p.name, p.address, p.city, p.region, b.category
            ORDER BY p.region, p.name
        """), {"year": year, "source": for_source})

        budget_rows = await _fetch_budget(primary_source)
        budget_data = budget_rows.all()
        data_source_used = primary_source
        if not budget_data:
            budget_rows = await _fetch_budget(legacy_source)
            budget_data = budget_rows.all()
            data_source_used = legacy_source if budget_data else primary_source
        # 2. Bygg property-map: { property_id → { name, region, address, city, kategorier: {}, total } }
        prop_map: dict[str, dict] = {}
        for row in budget_data:
            pid = row.property_id
            if pid not in prop_map:
                prop_map[pid] = {
                    "property_id": pid,
                    "name": row.property_name or "—",
                    "address": row.address or "",
                    "city": row.city or "",
                    "region": row.region or "Ukjent",
                    "kategorier": {},
                    "total": 0.0,
                }
            prop_map[pid]["kategorier"][row.category] = float(row.total or 0)
            prop_map[pid]["total"] += float(row.total or 0)

        # 3. Grupper per region
        region_map: dict[str, dict] = {}
        for prop in prop_map.values():
            reg = prop["region"]
            if reg not in region_map:
                region_map[reg] = {"region": reg, "total": 0.0, "eiendommer": []}
            region_map[reg]["total"] += prop["total"]
            region_map[reg]["eiendommer"].append(prop)

        regioner = sorted(region_map.values(), key=lambda x: x["total"], reverse=True)

        # 4. Regionale/administrative kostnader (property_id IS NULL i GL)
        #    Estimat: 2025-aktuals × (1.035)^2
        regional_rows = await db.execute(text("""
            SELECT
                COALESCE(region, 'Ukjent') AS region,
                COALESCE(srs_kategori, 'Drift') AS kategori,
                SUM(belop) AS total
            FROM gl_transactions
            WHERE property_id IS NULL AND ar = 2025 AND belop > 0
            GROUP BY region, srs_kategori
        """))
        inflation_factor = 1.035 ** (year - 2025)
        uten_eiendom_total = 0.0
        uten_eiendom_regioner: dict[str, dict] = {}
        for row in regional_rows.all():
            estimert = float(row.total or 0) * inflation_factor
            uten_eiendom_total += estimert
            reg = row.region
            if reg not in uten_eiendom_regioner:
                uten_eiendom_regioner[reg] = {"region": reg, "total": 0.0, "kategorier": {}}
            uten_eiendom_regioner[reg]["total"] += estimert
            uten_eiendom_regioner[reg]["kategorier"][row.kategori] = (
                uten_eiendom_regioner[reg]["kategorier"].get(row.kategori, 0.0) + estimert
            )

        totalt_eiendommer = sum(p["total"] for p in prop_map.values())

        return {
            "year": year,
            "scenario": scenario_norm,
            "budget_data_source": data_source_used,
            "totalt": totalt_eiendommer + uten_eiendom_total,
            "totalt_eiendommer": totalt_eiendommer,
            "antall_eiendommer": len(prop_map),
            "regioner": regioner,
            "uten_eiendom": {
                "total": uten_eiendom_total,
                "note": f"Regionale/administrative kostnader — estimert fra 2025-aktuals × inflasjon ({year - 2025} år)",
                "regioner": sorted(uten_eiendom_regioner.values(), key=lambda x: x["total"], reverse=True),
            },
        }

    except Exception as exc:
        import logging
        logging.getLogger(__name__).debug("budget-summary failed: %s", exc)
        return {
            "year": year,
            "scenario": "xgb70",
            "budget_data_source": None,
            "totalt": 0.0,
            "totalt_eiendommer": 0.0,
            "antall_eiendommer": 0,
            "regioner": [],
            "uten_eiendom": {"total": 0.0, "note": "Ingen data", "regioner": []},
        }


@router.get("/backtest", response_model=dict[str, Any])
async def get_backtest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kjorer out-of-sample backtesting: trener HW pa historikk t.o.m. aret for
    hvert testaar (2023, 2024, 2025), predikerer det aktuelle aaret og sammenligner
    med faktisk GL. Returnerer MAPE og MAE per aar og kategori.

    Nar modellen er kalibrert likt som for 2027-prediksjonen.
    """
    try:
        result = await BudgetPredictionService.run_backtest(db=db)
        return result
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("backtest failed: %s", exc)
        return {
            "test_years": [2023, 2024, 2025],
            "parameters": {},
            "results": {},
            "error": str(exc),
        }
