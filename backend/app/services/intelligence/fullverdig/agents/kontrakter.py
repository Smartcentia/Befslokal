"""
Kontrakter-agent – henter kontraktsinformasjon fra DB.

Fase 2: Read-only – utløpende kontrakter, kontrakter per eiendom, oppsummering.
"""

import logging
import re
from datetime import date, timedelta
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.services.intelligence.fullverdig.state import FullverdigState

logger = logging.getLogger(__name__)


def _months_ahead(message: str) -> int:
    """Trekk ut antall måneder fra melding, default 6."""
    m = re.search(r"(\d+)\s*m[åa]ned", message, re.IGNORECASE)
    if m:
        return min(int(m.group(1)), 24)
    if re.search(r"\b(år|12 mnd)\b", message, re.IGNORECASE):
        return 12
    return 6


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


def _format_contracts(rows: list, header: str) -> str:
    if not rows:
        return f"{header}\nIngen kontrakter funnet."
    lines = [header]
    for r in rows:
        name = getattr(r, "contract_name", None) or getattr(r, "archive_code", None) or "Ukjent"
        party = getattr(r, "party_name", None) or "-"
        prop = getattr(r, "property_name", None) or "-"
        status = getattr(r, "status", "-") or "-"
        start = getattr(r, "start_date", None)
        end = getattr(r, "end_date", None)
        start_str = start.strftime("%d.%m.%Y") if start else "-"
        end_str = end.strftime("%d.%m.%Y") if end else "-"
        lines.append(f"- {name} | Part: {party} | Eiendom: {prop} | Status: {status} | {start_str} → {end_str}")
    return "\n".join(lines)


async def _run_kontrakter(db: AsyncSession, message: str, context: dict) -> dict:
    msg_lower = message.lower()

    property_id = await _resolve_property_id(db, message, context)

    # Utløpende kontrakter
    if any(w in msg_lower for w in ("utløp", "utlop", "utløper", "snart", "forfaller")):
        months = _months_ahead(message)
        cutoff = date.today() + timedelta(days=months * 30)
        params: dict = {"today": date.today(), "cutoff": cutoff}
        where = "c.end_date >= :today AND c.end_date <= :cutoff AND c.status = 'active'"
        if property_id:
            where += " AND p.property_id = :pid"
            params["pid"] = property_id
        q = text(f"""
            SELECT c.contract_name, c.archive_code, c.status, c.start_date, c.end_date,
                   pa.name AS party_name, p.name AS property_name
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE {where}
            ORDER BY c.end_date ASC
            LIMIT 25
        """)
        res = await db.execute(q, params)
        rows = res.fetchall()
        header = f"Kontrakter som utløper innen {months} måneder:"
        result_text = _format_contracts(rows, header)

    # Kontrakter for eiendom
    elif property_id:
        q = text("""
            SELECT c.contract_name, c.archive_code, c.status, c.start_date, c.end_date,
                   pa.name AS party_name, p.name AS property_name
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE p.property_id = :pid
            ORDER BY c.status, c.end_date ASC NULLS LAST
            LIMIT 20
        """)
        res = await db.execute(q, {"pid": property_id})
        rows = res.fetchall()
        header = "Kontrakter for eiendommen:"
        result_text = _format_contracts(rows, header)

    # Alle aktive kontrakter (oversikt)
    else:
        q = text("""
            SELECT c.contract_name, c.archive_code, c.status, c.start_date, c.end_date,
                   pa.name AS party_name, p.name AS property_name
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN properties p ON u.property_id = p.property_id
            LEFT JOIN parties pa ON c.party_id = pa.party_id
            WHERE c.status = 'active'
            ORDER BY c.end_date ASC NULLS LAST
            LIMIT 20
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        header = "Aktive kontrakter (utvalg, sortert på utløp):"
        result_text = _format_contracts(rows, header)

    return {
        "messages": [SystemMessage(content=f"KONTRAKTER_RESULTAT:\n{result_text}")],
        "agent_result": result_text,
        "next_step": "writer",
    }


async def kontrakter_agent_node(
    state: FullverdigState,
    config: Optional[RunnableConfig] = None,
) -> dict:
    logger.info("📄 Kontrakter-agent: Henter kontraktsinformasjon...")
    messages = state.get("messages", [])
    context = state.get("context") or {}
    message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")

    db = (config.get("configurable") or {}).get("db") if config else None
    if not db:
        async with SessionLocal() as db:
            return await _run_kontrakter(db, message, context)
    return await _run_kontrakter(db, message, context)
