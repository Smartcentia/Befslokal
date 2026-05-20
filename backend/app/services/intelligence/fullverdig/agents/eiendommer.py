"""
Eiendommer-agent – henter eiendomsinformasjon fra DB.

Fase 2: Read-only – liste, regional oversikt, detaljer, kostnad per kvm.
"""

import logging
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.services.intelligence.fullverdig.state import FullverdigState

logger = logging.getLogger(__name__)

REGIONS = {"nord", "midt", "vest", "sør", "sor", "øst", "ost", "bufdir"}


def _extract_region(message: str) -> Optional[str]:
    for r in REGIONS:
        if r in message.lower():
            region_map = {"sor": "Sør", "ost": "Øst", "midt": "Midt-Norge"}
            return region_map.get(r, r.capitalize())
    return None


def _format_properties(rows: list, header: str) -> str:
    if not rows:
        return f"{header}\nIngen eiendommer funnet."
    lines = [header]
    for r in rows:
        name = getattr(r, "name", None) or "Ukjent"
        address = getattr(r, "address", None) or "-"
        region = getattr(r, "region", None) or "-"
        area = getattr(r, "total_area", None)
        usage = getattr(r, "usage", None) or "-"
        area_str = f"{area:.0f} m²" if area else "-"
        lines.append(f"- {name} | {address} | Region: {region} | Areal: {area_str} | Bruk: {usage}")
    return "\n".join(lines)


async def _run_eiendommer(db: AsyncSession, message: str, context: dict) -> dict:
    msg_lower = message.lower()

    # Kontekst: brukeren ser på en eiendom
    if context.get("entity_type") == "property" and context.get("entity_id"):
        pid = context["entity_id"]
        r = await db.execute(
            text("""
                SELECT name, address, region, total_area, land_area, usage,
                       construction_year, energy_label, municipality, approved_places,
                       ownership_type, owner_name, unit_type_derived
                FROM properties WHERE property_id = :pid
            """),
            {"pid": pid},
        )
        row = r.fetchone()
        if row:
            parts = [
                f"Eiendom: {row.name or 'Ukjent'}",
                f"Adresse: {row.address or '-'}",
                f"Region: {row.region or '-'}",
                f"Areal: {f'{row.total_area:.0f} m²' if row.total_area else '-'}",
                f"Tomteareal: {f'{row.land_area:.0f} m²' if row.land_area else '-'}",
                f"Bruk: {row.usage or '-'}",
                f"Byggeår: {row.construction_year or '-'}",
                f"Energimerke: {row.energy_label or '-'}",
                f"Kommune: {row.municipality or '-'}",
                f"Godkjente plasser: {row.approved_places or '-'}",
                f"Eierskap: {row.ownership_type or '-'}",
                f"Hjemmelshaver: {row.owner_name or '-'}",
                f"Enhetstype: {row.unit_type_derived or '-'}",
            ]
            result_text = "Eiendomsdetaljer:\n" + "\n".join(parts)
        else:
            result_text = "Fant ikke eiendommen."

    # Regional oversikt
    elif (region := _extract_region(message)):
        q = text("""
            SELECT name, address, region, total_area, usage
            FROM properties
            WHERE region ILIKE :region AND name != 'Statlig'
            ORDER BY name
            LIMIT 30
        """)
        res = await db.execute(q, {"region": f"%{region}%"})
        rows = res.fetchall()
        result_text = _format_properties(rows, f"Eiendommer i region {region}:")

    # Kostnad per kvm
    elif any(w in msg_lower for w in ("kvm", "kostnad per", "kostnad pr", "kr/m")):
        q = text("""
            SELECT p.name, p.address, p.region, p.total_area,
                   SUM(pac.total_cost) AS total_cost,
                   CASE WHEN p.total_area > 0 THEN SUM(pac.total_cost) / p.total_area ELSE NULL END AS cost_per_m2
            FROM properties p
            JOIN property_annual_costs pac ON pac.property_id = p.property_id
            WHERE p.total_area IS NOT NULL AND p.total_area > 0 AND p.name != 'Statlig'
            GROUP BY p.property_id, p.name, p.address, p.region, p.total_area
            ORDER BY cost_per_m2 DESC NULLS LAST
            LIMIT 20
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        if not rows:
            result_text = "Ingen kostnadsdata tilgjengelig."
        else:
            lines = ["Kostnad per kvm (topp 20):"]
            for r in rows:
                cost_m2 = f"{r.cost_per_m2:,.0f} kr/m²" if r.cost_per_m2 else "-"
                total = f"{r.total_cost:,.0f} kr" if r.total_cost else "-"
                lines.append(f"- {r.name or 'Ukjent'} | {r.region or '-'} | {r.total_area:.0f} m² | {total} | {cost_m2}")
            result_text = "\n".join(lines)

    # Søk på navn/adresse
    elif any(w in msg_lower for w in ("søk", "finn", "finnes")) or re.search(r"(heter|kalles|adresse)\s+\S", msg_lower):
        m = re.search(r"(?:heter|kalles|adresse|finn|søk etter)\s+([A-Za-zÆØÅæøå0-9\s\-]+?)(?:\?|\.|$)", message, re.IGNORECASE)
        term = m.group(1).strip() if m else message[:50]
        q = text("""
            SELECT name, address, region, total_area, usage
            FROM properties
            WHERE name ILIKE :q OR address ILIKE :q
            ORDER BY name LIMIT 10
        """)
        res = await db.execute(q, {"q": f"%{term}%"})
        rows = res.fetchall()
        result_text = _format_properties(rows, f"Søkeresultat for «{term}»:")

    # Generell porteføljeoversikt
    else:
        q = text("""
            SELECT region, COUNT(*) AS antall,
                   SUM(total_area) AS total_areal,
                   SUM(approved_places) AS plasser
            FROM properties
            WHERE name != 'Statlig'
            GROUP BY region
            ORDER BY region
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        if not rows:
            result_text = "Ingen eiendomsdata tilgjengelig."
        else:
            lines = ["Eiendomsportefølje per region:"]
            for r in rows:
                areal = f"{r.total_areal:,.0f} m²" if r.total_areal else "-"
                plasser = str(r.plasser) if r.plasser else "-"
                lines.append(f"- {r.region or 'Ukjent'}: {r.antall} eiendommer | {areal} | {plasser} plasser")
            result_text = "\n".join(lines)

    return {
        "messages": [SystemMessage(content=f"EIENDOMMER_RESULTAT:\n{result_text}")],
        "agent_result": result_text,
        "next_step": "writer",
    }


async def eiendommer_agent_node(
    state: FullverdigState,
    config: Optional[RunnableConfig] = None,
) -> dict:
    logger.info("🏠 Eiendommer-agent: Henter eiendomsinformasjon...")
    messages = state.get("messages", [])
    context = state.get("context") or {}
    message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

    db = (config.get("configurable") or {}).get("db") if config else None
    if not db:
        async with SessionLocal() as db:
            return await _run_eiendommer(db, message, context)
    return await _run_eiendommer(db, message, context)
