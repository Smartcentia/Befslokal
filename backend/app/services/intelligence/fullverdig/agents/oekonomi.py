"""
Økonomi-agent – henter finansielle data fra GL og property_annual_costs.

Fase 3: Read-only – kostnad per eiendom, regional oversikt, kategorifordeling, trendanalyse.

KRITISKE REGLER (CLAUDE.md §7-12):
- Bruk GROUP BY ... HAVING SUM(belop) > 0, aldri WHERE belop > 0
- Ekskluder 'Statlig'-eiendommer fra regional analyse (sekkepost)
- Aldri presenter tall uten krysssjekk mot kjent referanse
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

CURRENT_YEAR = 2025
MAX_SQL_ROWS = 25

REGIONS = {"nord", "midt", "vest", "sør", "sor", "øst", "ost", "bufdir"}


def _extract_year(message: str) -> int:
    m = re.search(r"\b(20\d{2})\b", message)
    return int(m.group(1)) if m else CURRENT_YEAR


def _extract_region(message: str) -> Optional[str]:
    mapping = {"sor": "Sør", "ost": "Øst", "midt": "Midt-Norge"}
    for r in REGIONS:
        if r in message.lower():
            return mapping.get(r, r.capitalize())
    return None


def _fmt(amount: Optional[float]) -> str:
    if amount is None:
        return "-"
    return f"{amount:,.0f} kr".replace(",", " ")


async def _resolve_property_id(db: AsyncSession, message: str, context: dict) -> Optional[str]:
    if context.get("entity_type") == "property" and context.get("entity_id"):
        return context["entity_id"]
    m = re.search(r"(?:for|til|på|eiendom)\s+([A-Za-zÆØÅæøå0-9\s\-]+?)(?:\?|\.|$|,)", message, re.IGNORECASE)
    if not m:
        return None
    term = m.group(1).strip()
    if len(term) < 2 or term.lower() in ("for", "til", "på", "alle"):
        return None
    r = await db.execute(
        text("SELECT property_id FROM properties WHERE name ILIKE :q OR address ILIKE :q ORDER BY name LIMIT 1"),
        {"q": f"%{term}%"},
    )
    row = r.fetchone()
    return str(row.property_id) if row else None


async def _cost_for_property(db: AsyncSession, property_id: str, year: int) -> str:
    """Kostnad per kategori for én eiendom, ett år."""
    # Sanity: hent total først
    total_q = await db.execute(
        text("""
            SELECT p.name, COALESCE(SUM(g.belop), 0) AS total
            FROM gl_transactions g
            JOIN properties p ON p.property_id = g.property_id
            WHERE g.property_id = :pid AND g.ar = :yr
            GROUP BY p.name
        """),
        {"pid": property_id, "yr": year},
    )
    total_row = total_q.fetchone()
    if not total_row or total_row.total == 0:
        return f"Ingen GL-data for eiendom i {year}."

    prop_name = total_row.name or "Ukjent"
    total = float(total_row.total)

    # Kategorifordeling (netto per kategori)
    kat_q = await db.execute(
        text("""
            SELECT srs_kategori, SUM(belop) AS netto
            FROM gl_transactions
            WHERE property_id = :pid AND ar = :yr
            GROUP BY srs_kategori
            HAVING SUM(belop) != 0
            ORDER BY netto DESC
        """),
        {"pid": property_id, "yr": year},
    )
    rows = kat_q.fetchall()

    lines = [f"Kostnader for {prop_name} – {year} (GL netto):"]
    lines.append(f"  Total: {_fmt(total)}")
    for r in rows:
        kat = r.srs_kategori or "Ukategorisert"
        pct = (float(r.netto) / total * 100) if total else 0
        lines.append(f"  • {kat}: {_fmt(float(r.netto))} ({pct:.1f}%)")
    return "\n".join(lines)


async def _regional_overview(db: AsyncSession, year: int, region: Optional[str]) -> str:
    """Regional kostnadsoversikt – ekskluderer Statlig."""
    params: dict = {"yr": year}
    region_filter = ""
    if region:
        region_filter = "AND g.region ILIKE :region"
        params["region"] = f"%{region}%"

    q = await db.execute(
        text(f"""
            SELECT g.region, COUNT(DISTINCT g.property_id) AS eiendommer,
                   SUM(g.belop) AS netto
            FROM gl_transactions g
            JOIN properties p ON p.property_id = g.property_id
            WHERE g.ar = :yr AND p.name != 'Statlig' {region_filter}
            GROUP BY g.region
            HAVING SUM(g.belop) != 0
            ORDER BY netto DESC
        """),
        params,
    )
    rows = q.fetchall()
    if not rows:
        return f"Ingen GL-data for {year}{'/ ' + region if region else ''}."

    header = f"Regionvis kostnadsoversikt – {year}" + (f" ({region})" if region else "") + ":"
    lines = [header]
    for r in rows:
        reg = r.region or "Ukjent"
        lines.append(f"  • {reg}: {_fmt(float(r.netto))} ({r.eiendommer} eiendommer)")
    return "\n".join(lines)


async def _trend_analysis(db: AsyncSession, property_id: Optional[str]) -> str:
    """År-for-år kostnadsutvikling, siste 5 år."""
    params: dict = {}
    where = "p.name != 'Statlig'"
    if property_id:
        where += " AND g.property_id = :pid"
        params["pid"] = property_id

    q = await db.execute(
        text(f"""
            SELECT g.ar, SUM(g.belop) AS netto, COUNT(DISTINCT g.property_id) AS eiendommer
            FROM gl_transactions g
            JOIN properties p ON p.property_id = g.property_id
            WHERE {where} AND g.ar IS NOT NULL AND g.ar >= :from_yr
            GROUP BY g.ar
            HAVING SUM(g.belop) != 0
            ORDER BY g.ar
        """),
        {"from_yr": CURRENT_YEAR - 4, **params},
    )
    rows = q.fetchall()
    if not rows:
        return "Ingen trenddata tilgjengelig."

    lines = ["Kostnadsutvikling (siste 5 år):"]
    prev = None
    for r in rows:
        netto = float(r.netto)
        change = ""
        if prev is not None and prev != 0:
            pct = (netto - prev) / abs(prev) * 100
            change = f" ({'+' if pct >= 0 else ''}{pct:.1f}%)"
        lines.append(f"  • {int(r.ar)}: {_fmt(netto)}{change}")
        prev = netto
    return "\n".join(lines)


async def _top_properties_by_cost(db: AsyncSession, year: int) -> str:
    """Topp 15 eiendommer etter kostnad."""
    q = await db.execute(
        text("""
            SELECT p.name, p.region, SUM(g.belop) AS netto
            FROM gl_transactions g
            JOIN properties p ON p.property_id = g.property_id
            WHERE g.ar = :yr AND p.name != 'Statlig'
            GROUP BY p.property_id, p.name, p.region
            HAVING SUM(g.belop) > 0
            ORDER BY netto DESC
            LIMIT 15
        """),
        {"yr": year},
    )
    rows = q.fetchall()
    if not rows:
        return f"Ingen data for {year}."
    lines = [f"Topp 15 eiendommer etter kostnad – {year}:"]
    for i, r in enumerate(rows, 1):
        lines.append(f"  {i}. {r.name or 'Ukjent'} ({r.region or '-'}): {_fmt(float(r.netto))}")
    return "\n".join(lines)


async def _run_oekonomi(db: AsyncSession, message: str, context: dict) -> dict:
    msg_lower = message.lower()
    year = _extract_year(message)
    region = _extract_region(message)
    property_id = await _resolve_property_id(db, message, context)

    # Kostnad for én eiendom
    if property_id:
        result_text = await _cost_for_property(db, property_id, year)

    # Trend / utvikling
    elif any(w in msg_lower for w in ("trend", "utvikling", "vekst", "økning", "historisk")):
        result_text = await _trend_analysis(db, None)

    # Topp eiendommer
    elif any(w in msg_lower for w in ("størst", "topp", "mest", "dyreste", "høyest")):
        result_text = await _top_properties_by_cost(db, year)

    # Regional eller generell oversikt
    else:
        result_text = await _regional_overview(db, year, region)

    return {
        "messages": [SystemMessage(content=f"OEKONOMI_RESULTAT:\n{result_text}")],
        "agent_result": result_text,
        "next_step": "writer",
    }


async def oekonomi_agent_node(
    state: FullverdigState,
    config: Optional[RunnableConfig] = None,
) -> dict:
    logger.info("💰 Økonomi-agent: Henter finansielle data...")
    messages = state.get("messages", [])
    context = state.get("context") or {}
    message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

    db = (config.get("configurable") or {}).get("db") if config else None
    if not db:
        async with SessionLocal() as db:
            return await _run_oekonomi(db, message, context)
    return await _run_oekonomi(db, message, context)
