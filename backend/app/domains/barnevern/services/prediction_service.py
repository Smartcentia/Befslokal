"""
Barnevern kostnadssimulering – brukte og ubrukte plasser.

Kombinerer BEFS institusjonsdata (approved_places, annual_cost) med egenandelstabell
og valgfri bruksgrad for å simulere total kostnad.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.domains.barnevern.schemas import RegionSimulation, SimulationResult

logger = logging.getLogger(__name__)

# Egenandelstabell (fallback hvis JSON ikke finnes)
DEFAULT_EGENANDEL: Dict[str, int] = {
    "2024": 182700,
    "2025": 190190,
    "2026": 197225,
    "2027": 204650,
    "2028": 212100,
    "2029": 220000,
    "2030": 228000,
}


def _load_egenandel() -> Dict[str, int]:
    """Hent egenandel månedsats per år fra JSON."""
    data_dir = Path(__file__).resolve().parents[5] / "data"
    json_path = data_dir / "barnevern_egenandel.json"
    if not json_path.exists():
        return DEFAULT_EGENANDEL
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        rates = data.get("institusjon_ordinær", {})
        return {str(k): int(v) for k, v in rates.items()} if rates else DEFAULT_EGENANDEL
    except Exception as e:
        logger.warning("Barnevern egenandel load failed: %s", e)
        return DEFAULT_EGENANDEL


async def get_institutions_data(db: AsyncSession) -> Dict[str, Any]:
    """
    Hent barnevernsinstitusjoner med kapasitet og kostnader.
    Samme logikk som GET /properties/institutions.
    """
    try:
        rows = (await db.execute(text("""
            SELECT
                p.property_id,
                p.name,
                p.region,
                p.approved_places,
                p.budgeted_places
            FROM properties p
            WHERE
                (p.unit_type_derived = 'Barnevernsinstitusjon'
                 OR p.unit_type_derived = 'Institusjonsavdeling'
                 OR (p.approved_places IS NOT NULL AND p.approved_places > 0))
            ORDER BY p.region, p.name
        """))).fetchall()

        cost_rows = (await db.execute(text("""
            SELECT property_id, SUM(amount) AS total
            FROM gl_transactions
            WHERE year = 2025 AND property_id IS NOT NULL
            GROUP BY property_id
        """))).fetchall()
        costs_by_pid = {str(r.property_id): float(r.total or 0) for r in cost_rows}

        institutions = []
        for r in rows:
            pid = str(r.property_id)
            ap = r.approved_places or 0
            annual_cost = costs_by_pid.get(pid, 0)
            institutions.append({
                "property_id": pid,
                "name": r.name,
                "region": r.region or "Ukjent",
                "approved_places": ap,
                "budgeted_places": r.budgeted_places or 0,
                "annual_cost_2025": annual_cost,
            })

        by_region: Dict[str, Dict[str, Any]] = {}
        for inst in institutions:
            reg = inst["region"]
            if reg not in by_region:
                by_region[reg] = {
                    "approved_places": 0,
                    "budgeted_places": 0,
                    "annual_cost": 0.0,
                    "count": 0,
                }
            by_region[reg]["approved_places"] += inst["approved_places"]
            by_region[reg]["budgeted_places"] += inst["budgeted_places"]
            by_region[reg]["annual_cost"] += inst["annual_cost_2025"]
            by_region[reg]["count"] += 1

        return {
            "institutions": institutions,
            "by_region": by_region,
            "total_approved_places": sum(i["approved_places"] for i in institutions),
            "total_count": len(institutions),
        }
    except Exception as e:
        logger.debug("get_institutions_data error: %s", e)
        return {
            "institutions": [],
            "by_region": {},
            "total_approved_places": 0,
            "total_count": 0,
        }


async def fetch_ssb_barnevern_data(
    table_id: str = "12279",
    year: int = 2025,
) -> Optional[Dict[str, Any]]:
    """
    Hent SSB KOSTRA barnevern-data (tabell 12279 eller 12280).
    Landet (EAK) for nasjonal referanse.
    """
    try:
        from app.services.external.api_clients.ssb_pxweb_client import SSBPxWebClient
        client = SSBPxWebClient()
        selection = [
            {"variableCode": "KOKkommuneregion0000", "valueCodes": ["EAK"]},
            {"variableCode": "Tid", "valueCodes": [str(year)]},
        ]
        data = await client.get_data(
            table_id=table_id,
            selection=selection,
            output_format="json-stat2",
        )
        return data
    except Exception as e:
        logger.debug("SSB barnevern fetch failed: %s", e)
        return None


async def run_simulation(
    db: AsyncSession,
    year: int = 2026,
    usage_pct: float = 0.85,
    include_ssb: bool = True,
) -> SimulationResult:
    """
    Kjør kostnadssimulering for brukte og ubrukte barnevernsplasser.

    usage_pct: Andel plasser som er brukte (0–1). Brukes til å estimere
               brukte_plasser = approved_places × usage_pct.
    """
    egenandel = _load_egenandel()
    monthly = egenandel.get(str(year), egenandel.get("2026", 197225))
    annual = monthly * 12

    data = await get_institutions_data(db)
    by_region = data["by_region"]

    ssb_data = None
    if include_ssb:
        ssb_data = await fetch_ssb_barnevern_data(table_id="12279", year=min(year, 2025))

    regions: List[RegionSimulation] = []
    total_brukte = 0
    total_ubrukte = 0
    total_kost_brukte = 0.0
    total_kost_ubrukte = 0.0

    for region, agg in by_region.items():
        approved = agg["approved_places"]
        annual_cost = agg["annual_cost"]

        brukte = int(round(approved * usage_pct))
        ubrukte = approved - brukte

        kost_brukte = brukte * annual
        if approved > 0:
            kost_ubrukte = annual_cost * (ubrukte / approved)
        else:
            kost_ubrukte = 0.0

        total_kostnad = kost_brukte + kost_ubrukte

        regions.append(RegionSimulation(
            region=region,
            approved_places=approved,
            brukte_plasser=brukte,
            ubrukte_plasser=ubrukte,
            kost_brukte=kost_brukte,
            kost_ubrukte=kost_ubrukte,
            total_kostnad=total_kostnad,
            annual_cost_region=annual_cost,
        ))

        total_brukte += brukte
        total_ubrukte += ubrukte
        total_kost_brukte += kost_brukte
        total_kost_ubrukte += kost_ubrukte

    return SimulationResult(
        year=year,
        usage_pct=usage_pct,
        egenandel_maaned=float(monthly),
        egenandel_aar=float(annual),
        by_region=regions,
        total_approved_places=data["total_approved_places"],
        total_brukte=total_brukte,
        total_ubrukte=total_ubrukte,
        total_kost_brukte=total_kost_brukte,
        total_kost_ubrukte=total_kost_ubrukte,
        total_kostnad=total_kost_brukte + total_kost_ubrukte,
        ssb_data=ssb_data,
    )
