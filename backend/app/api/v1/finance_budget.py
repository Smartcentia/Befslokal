"""
API for vedtatt økonomi-budsjett (finance_budget-tabellen).

Separate endepunkter fra /cost-management/budgets for å forhindre
sammenblanding med BEFS-prediksjoner.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.services.finance_budget_import_service import import_finance_budget, import_kontant_actuals, import_kontant_2026_from_budget_sheet

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/import", response_model=dict[str, Any])
async def import_finance_budget_endpoint(
    file: UploadFile = File(..., description="Excel-fil fra økonomi-avdelingen"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer vedtatt budsjett for 2025 og 2026 fra økonomi-avdelingens Excel-uttrekk.

    Leser fanen 'Budsjett 2025_2026'. Idempotent: re-import overskriver
    eksisterende finance_dept_2025/2026-rader uten å røre prediksjoner
    eller GL-data.

    Kun ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer kan importere økonomi-budsjett",
        )

    content = await file.read()
    report = await import_finance_budget(
        db=db,
        file_content=content,
        filename=file.filename or "upload.xlsx",
        imported_by=current_user.email,
    )

    if report.errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": report.errors, "report": _report_dict(report)},
        )

    return {
        "status": "ok",
        "report": _report_dict(report),
    }


@router.post("/import-kontant", response_model=dict[str, Any])
async def import_kontant_actuals_endpoint(
    file: UploadFile = File(..., description="Excel-fil med regnskap-data (Kontant-fane)"),
    year: int = Query(2025, ge=2023, le=2030, description="Regnskapsår"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer faktiske kostnader (regnskap) fra økonomi-avdelingens Excel-uttrekk.

    Leser fanen 'Kontant {year}' og lagrer med data_source='kontant_{year}'.
    Idempotent: re-import overskriver eksisterende rader for (year, data_source).

    Kun ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer kan importere regnskap-data",
        )

    content = await file.read()
    report = await import_kontant_actuals(
        db=db,
        file_content=content,
        filename=file.filename or "upload.xlsx",
        imported_by=current_user.email,
        year=year,
    )

    if report.errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": report.errors, "report": _report_dict(report)},
        )

    return {
        "status": "ok",
        "year": year,
        "data_source": f"kontant_{year}",
        "report": _report_dict(report),
    }


@router.post("/import-kontant-2026", response_model=dict[str, Any])
async def import_kontant_2026_endpoint(
    file: UploadFile = File(..., description="Excel-fil med budsjett 2025_2026 (Kontantbeløp-kolonne for 2026)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer faktisk brukt 2026 YTD fra Kontantbeløp-kolonnen i 'Budsjett 2025_2026'-fanen.
    Lagrer som data_source='kontant_2026'. Idempotent. Kun ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kun administratorer")

    content = await file.read()
    report = await import_kontant_2026_from_budget_sheet(
        db=db,
        file_content=content,
        filename=file.filename or "upload.xlsx",
        imported_by=current_user.email,
    )

    if report.errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": report.errors, "report": _report_dict(report)},
        )

    return {"status": "ok", "data_source": "kontant_2026", "report": _report_dict(report)}


@router.get("/summary", response_model=dict[str, Any])
async def get_finance_budget_summary(
    year: int = Query(..., ge=2024, le=2030, description="Budsjett-år"),
    data_source: str | None = Query(None, description="Eksakt data_source (f.eks. 'kontant_2025', 'finance_dept_2026'). Standard: finance_dept_{year}"),
    through_month: int | None = Query(None, ge=1, le=12, description="YTD-filter: inkluder kun måneder t.o.m. denne (f.eks. 4 = jan–apr)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Oppsummering av økonomi-data for et år (budsjett eller regnskap).

    Returnerer:
    - total_nok: nasjonal sum (eiendommer + direktorat)
    - total_eiendommer_nok: kun eiendoms-tilknyttede beløp
    - total_direktorat_nok: koststed uten eiendom-match
    - by_property: liste {property_id, property_name, region, total, by_category}
    - by_category: nasjonal sum per kategori
    - through_month: ekko av YTD-filter (null = fulltår)
    """
    try:
        ds = data_source or f"finance_dept_{year}"
        month_filter = "AND fb.month <= :through_month" if through_month else ""
        dir_month_filter = "AND month <= :through_month" if through_month else ""
        params: dict = {"year": year, "ds": ds}
        if through_month:
            params["through_month"] = through_month

        # Per eiendom + region
        prop_rows = await db.execute(text(f"""
            SELECT
                fb.property_id::text,
                p.name           AS property_name,
                p.region,
                fb.category,
                SUM(fb.amount)   AS total
            FROM finance_budget fb
            JOIN properties p ON p.property_id = fb.property_id
            WHERE fb.year = :year
              AND fb.data_source = :ds
              {month_filter}
            GROUP BY fb.property_id, p.name, p.region, fb.category
            ORDER BY p.region, p.name
        """), params)

        prop_map: dict[str, dict] = {}
        for row in prop_rows.all():
            pid = row.property_id
            if pid not in prop_map:
                prop_map[pid] = {
                    "property_id": pid,
                    "property_name": row.property_name or "—",
                    "region": row.region or "Ukjent",
                    "total": 0.0,
                    "by_category": {},
                }
            prop_map[pid]["by_category"][row.category] = (
                prop_map[pid]["by_category"].get(row.category, 0.0) + float(row.total or 0)
            )
            prop_map[pid]["total"] += float(row.total or 0)

        # Direktorat-rader (property_id IS NULL) — fordelt per region via koststed_mapping
        dir_rows = await db.execute(text(f"""
            SELECT
                COALESCE(km.region, 'Ukjent') AS region,
                fb.category,
                SUM(fb.amount) AS total
            FROM finance_budget fb
            LEFT JOIN koststed_mapping km ON km.koststed_kode = fb.koststed_kode
            WHERE fb.year = :year
              AND fb.data_source = :ds
              AND fb.is_direktorat_level = true
              {dir_month_filter}
            GROUP BY km.region, fb.category
        """), params)

        direktorat_by_region: dict[str, dict[str, float]] = {}
        for row in dir_rows.all():
            reg = row.region or "Ukjent"
            cat = row.category
            if reg not in direktorat_by_region:
                direktorat_by_region[reg] = {}
            direktorat_by_region[reg][cat] = (
                direktorat_by_region[reg].get(cat, 0.0) + float(row.total or 0)
            )
        total_direktorat = sum(sum(cats.values()) for cats in direktorat_by_region.values())
        direktorat_by_cat: dict[str, float] = {}
        for cats in direktorat_by_region.values():
            for cat, amt in cats.items():
                direktorat_by_cat[cat] = direktorat_by_cat.get(cat, 0.0) + amt

        total_eiendommer = sum(p["total"] for p in prop_map.values())
        total_all = total_eiendommer + total_direktorat

        by_category: dict[str, float] = {}
        for prop in prop_map.values():
            for cat, amt in prop["by_category"].items():
                by_category[cat] = by_category.get(cat, 0.0) + amt
        for cat, amt in direktorat_by_cat.items():
            by_category[cat] = by_category.get(cat, 0.0) + amt

        return {
            "year": year,
            "data_source": ds,
            "through_month": through_month,
            "total_nok": round(total_all, 2),
            "total_eiendommer_nok": round(total_eiendommer, 2),
            "total_direktorat_nok": round(total_direktorat, 2),
            "antall_eiendommer": len(prop_map),
            "by_property": list(prop_map.values()),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "direktorat": {
                "total": round(total_direktorat, 2),
                "by_category": {k: round(v, 2) for k, v in direktorat_by_cat.items()},
                "by_region": {
                    reg: {
                        "total": round(sum(cats.values()), 2),
                        "by_category": {k: round(v, 2) for k, v in cats.items()},
                    }
                    for reg, cats in direktorat_by_region.items()
                },
            },
        }

    except Exception as exc:
        logger.debug("finance-budget/summary feilet: %s", exc)
        return {
            "year": year,
            "data_source": f"finance_dept_{year}",
            "through_month": through_month,
            "total_nok": 0.0,
            "total_eiendommer_nok": 0.0,
            "total_direktorat_nok": 0.0,
            "antall_eiendommer": 0,
            "by_property": [],
            "by_category": {},
            "direktorat": {"total": 0.0, "by_category": {}, "by_region": {}},
        }


@router.get("/by-property/{property_id}", response_model=dict[str, Any])
async def get_finance_budget_by_property(
    property_id: str,
    year: int = Query(..., ge=2024, le=2030),
    data_source: str | None = Query(None, description="Eksakt data_source (f.eks. 'kontant_2025', 'finance_dept_2026'). Standard: finance_dept_{year}"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalj per eiendom: total, per kategori, per måned."""
    try:
        ds = data_source or f"finance_dept_{year}"
        rows = await db.execute(text("""
            SELECT month, konto, konto_navn, category, SUM(amount) AS total
            FROM finance_budget
            WHERE property_id = :pid
              AND year = :year
              AND data_source = :ds
            GROUP BY month, konto, konto_navn, category
            ORDER BY month, konto
        """), {"pid": property_id, "year": year, "ds": ds})

        by_category: dict[str, float] = {}
        monthly: list[dict] = []
        total = 0.0
        for row in rows.all():
            amt = float(row.total or 0)
            by_category[row.category] = by_category.get(row.category, 0.0) + amt
            monthly.append({
                "month": row.month,
                "konto": row.konto,
                "konto_navn": row.konto_navn,
                "category": row.category,
                "amount": round(amt, 2),
            })
            total += amt

        return {
            "property_id": property_id,
            "year": year,
            "total": round(total, 2),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "monthly": monthly,
        }

    except Exception as exc:
        logger.debug("finance-budget/by-property feilet: %s", exc)
        return {
            "property_id": property_id,
            "year": year,
            "total": 0.0,
            "by_category": {},
            "monthly": [],
        }


def _report_dict(report) -> dict:
    return {
        "total_rows": report.total_rows,
        "inserted": report.inserted,
        "matched_properties": report.matched_properties,
        "direktorat_rows": report.direktorat_rows,
        "total_2025_nok": round(report.total_2025_nok, 2),
        "total_2026_nok": round(report.total_2026_nok, 2),
        "skipped": {
            "no_periode": report.skipped_no_periode,
            "wrong_year": report.skipped_wrong_year,
            "zero_amount": report.skipped_zero_amount,
            "unknown_konto": report.skipped_unknown_konto,
        },
        "unmatched_koststeder_count": len(report.unmatched_koststeder),
        "unmatched_koststeder": report.unmatched_koststeder[:50],
    }
