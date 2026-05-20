"""Barnevern router – /api/v1/barnevern/places og /simulate"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.deps import get_db
from app.domains.core.models.property import Property

router = APIRouter()

# Egenandel per plass per måned (institusjon ordinær), NOK
EGENANDEL: dict[int, float] = {
    2024: 182_700,
    2025: 190_190,
    2026: 197_225,
    2027: 204_650,
    2028: 212_100,
    2029: 220_000,
    2030: 228_000,
}
DEFAULT_EGENANDEL = 190_190  # brukes for år utenfor tabellen


def _egenandel(year: int) -> float:
    return EGENANDEL.get(year, DEFAULT_EGENANDEL)


def _is_barnevern(p: Property) -> bool:
    """Filtrerer på barnevernsinstitusjoner og institusjonsavdelinger."""
    types = (p.unit_type_derived or "").lower()
    return "barnevern" in types or "institusjonsavdeling" in types


@router.get("/places")
async def get_barnevern_places(db: AsyncSession = Depends(get_db)):
    """Returnerer alle barnevernsinstitusjoner med godkjente plasser, gruppert per region."""
    result = await db.execute(
        select(Property).where(
            and_(
                Property.closed_at.is_(None),
                Property.approved_places.isnot(None),
                Property.approved_places > 0,
            )
        )
    )
    properties = result.scalars().all()

    # Filtrer til barnevernsrelaterte enheter
    bv_props = [p for p in properties if _is_barnevern(p)]

    # Bygg institusjonsliste
    institutions = []
    by_region: dict = {}
    egenandel_2025 = _egenandel(2025)

    for p in bv_props:
        places = p.approved_places or 0
        budgeted = p.budgeted_places or 0
        annual_cost = places * egenandel_2025 * 12
        region = p.region or "Ukjent"

        institutions.append({
            "property_id": str(p.property_id),
            "name": p.name or p.address or str(p.property_id),
            "region": region,
            "approved_places": places,
            "budgeted_places": budgeted,
            "annual_cost_2025": annual_cost,
        })

        if region not in by_region:
            by_region[region] = {"approved_places": 0, "budgeted_places": 0, "annual_cost": 0.0, "count": 0}
        by_region[region]["approved_places"] += places
        by_region[region]["budgeted_places"] += budgeted
        by_region[region]["annual_cost"] += annual_cost
        by_region[region]["count"] += 1

    total_approved = sum(i["approved_places"] for i in institutions)

    return {
        "institutions": institutions,
        "by_region": by_region,
        "total_approved_places": total_approved,
        "total_count": len(institutions),
    }


@router.get("/simulate")
async def simulate_barnevern_cost(
    year: int = Query(default=2025, ge=2024, le=2030),
    usage_pct: float = Query(default=0.85, ge=0.0, le=1.0),
    include_ssb: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Simulerer kostnad for brukte og ubrukte plasser per region."""
    result = await db.execute(
        select(Property).where(
            and_(
                Property.closed_at.is_(None),
                Property.approved_places.isnot(None),
                Property.approved_places > 0,
            )
        )
    )
    properties = result.scalars().all()
    bv_props = [p for p in properties if _is_barnevern(p)]

    egenandel_maaned = _egenandel(year)
    egenandel_aar = egenandel_maaned * 12

    region_map: dict = {}
    for p in bv_props:
        region = p.region or "Ukjent"
        places = p.approved_places or 0
        if region not in region_map:
            region_map[region] = 0
        region_map[region] += places

    by_region = []
    totals = {
        "brukte": 0,
        "ubrukte": 0,
        "kost_brukte": 0.0,
        "kost_ubrukte": 0.0,
        "total_kostnad": 0.0,
        "approved": 0,
    }

    for region, approved in region_map.items():
        brukte = round(approved * usage_pct)
        ubrukte = approved - brukte
        kost_brukte = brukte * egenandel_aar
        # Kostnad ubrukte: bruker samme egenandel som proxy for driftskostnad per plass
        kost_ubrukte = ubrukte * egenandel_aar
        total = kost_brukte + kost_ubrukte

        by_region.append({
            "region": region,
            "approved_places": approved,
            "brukte_plasser": brukte,
            "ubrukte_plasser": ubrukte,
            "kost_brukte": kost_brukte,
            "kost_ubrukte": kost_ubrukte,
            "total_kostnad": total,
            "annual_cost_region": approved * egenandel_aar,
        })

        totals["approved"] += approved
        totals["brukte"] += brukte
        totals["ubrukte"] += ubrukte
        totals["kost_brukte"] += kost_brukte
        totals["kost_ubrukte"] += kost_ubrukte
        totals["total_kostnad"] += total

    return {
        "year": year,
        "usage_pct": usage_pct,
        "egenandel_maaned": egenandel_maaned,
        "egenandel_aar": egenandel_aar,
        "by_region": by_region,
        "total_approved_places": totals["approved"],
        "total_brukte": totals["brukte"],
        "total_ubrukte": totals["ubrukte"],
        "total_kost_brukte": totals["kost_brukte"],
        "total_kost_ubrukte": totals["kost_ubrukte"],
        "total_kostnad": totals["total_kostnad"],
        "ssb_data": None,
    }
