"""
Internkontroll-agent – utfører internkontroll-oppgaver.

Fase 1: Read-only – sjekk status, liste avvik.
"""

import logging
import re
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.services.intelligence.fullverdig.state import FullverdigState

logger = logging.getLogger(__name__)


async def _resolve_property_id(
    db: AsyncSession,
    message: str,
    context: Optional[dict],
) -> Optional[str]:
    """
    Resolve property_id from message or context.
    - context.entity_type=property + entity_id → use directly
    - message contains "for X" / "for [name]" → search by name/address
    """
    if context and context.get("entity_type") == "property" and context.get("entity_id"):
        return context["entity_id"]

    # Extract search term from patterns like "Sjekk internkontroll for Bufdir Helsfyr"
    patterns = [
        r"(?:for|til)\s+([^.?!]+?)(?:\?|\.|$)",
        r"internkontroll\s+(?:for|på)\s+([^.?!]+?)(?:\?|\.|$)",
        r"([A-Za-z0-9\s\-]+)(?:\s+–|$)",
    ]
    search_term = None
    msg_lower = message.strip()
    for pat in patterns:
        m = re.search(pat, msg_lower, re.IGNORECASE)
        if m:
            search_term = m.group(1).strip()
            if len(search_term) >= 2 and search_term.lower() not in ("for", "til", "på", "alle"):
                break

    if not search_term:
        return None

    # Search properties by name or address
    pattern = f"%{search_term}%"
    result = await db.execute(
        text("""
            SELECT property_id, name, address
            FROM properties
            WHERE name ILIKE :q OR address ILIKE :q
            ORDER BY name
            LIMIT 5
        """),
        {"q": pattern},
    )
    rows = result.fetchall()
    if not rows:
        return None
    # Prefer exact match, else first result
    for r in rows:
        if r.name and search_term.lower() in (r.name or "").lower():
            return str(r.property_id)
        if r.address and search_term.lower() in (r.address or "").lower():
            return str(r.property_id)
    return str(rows[0].property_id)


def _format_cases_from_rows(rows: list, property_name: Optional[str] = None) -> str:
    """Format query rows for Writer."""
    if not rows:
        return "Ingen åpne internkontroll-saker funnet."
    lines = []
    for r in rows:
        title = r.title if hasattr(r, "title") else "Ukjent"
        priority = r.priority if hasattr(r, "priority") else "-"
        due = r.due_date if hasattr(r, "due_date") else None
        state = r.process_state if hasattr(r, "process_state") else "-"
        due_str = due.strftime("%d.%m.%Y") if due else "-"
        lines.append(f"- {title} (prioritet: {priority}, frist: {due_str}, status: {state})")
    header = f"Åpne internkontroll-saker{f' for {property_name}' if property_name else ''}:\n"
    return header + "\n".join(lines)


async def internkontroll_agent_node(
    state: FullverdigState,
    config: Optional[RunnableConfig] = None,
) -> dict:
    """
    Internkontroll-agent: henter åpne saker for eiendom eller alle.
    """
    logger.info("🏢 Internkontroll-agent: Henter saker...")
    messages = state.get("messages", [])
    context = state.get("context") or {}

    # Finn brukerens melding
    last_msg = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break
    message = last_msg or ""

    # Hent db fra config eller opprett egen session
    db = None
    if config:
        db = (config.get("configurable") or {}).get("db")
    if not db:
        # Fallback: egen session
        async with SessionLocal() as db:
            return await _run_internkontroll(db, message, context)

    return await _run_internkontroll(db, message, context)


async def _run_internkontroll(
    db: AsyncSession,
    message: str,
    context: dict,
) -> dict:
    property_id = await _resolve_property_id(db, message, context)
    property_name = None

    # Bruk raw SQL for å unngå ORM-modellavhengigheter (f.eks. Center)
    if property_id:
        r = await db.execute(
            text("SELECT name FROM properties WHERE property_id = :pid"),
            {"pid": property_id},
        )
        row = r.fetchone()
        if row:
            property_name = row.name

        q = text("""
            SELECT title, priority, due_date, process_state
            FROM internal_control_cases
            WHERE property_id = :pid AND status = 'open'
            ORDER BY due_date ASC NULLS LAST
            LIMIT 20
        """)
        res = await db.execute(q, {"pid": property_id})
        rows = res.fetchall()
        result_text = _format_cases_from_rows(rows, property_name)
    else:
        q = text("""
            SELECT title, priority, due_date, process_state
            FROM internal_control_cases
            WHERE status = 'open'
            ORDER BY due_date ASC NULLS LAST
            LIMIT 20
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        result_text = _format_cases_from_rows(rows)
        if rows:
            result_text = "Alle åpne internkontroll-saker (utvalg):\n" + result_text

    return {
        "messages": [
            SystemMessage(content=f"INTERNKONTROLL_RESULTAT:\n{result_text}")
        ],
        "agent_result": result_text,
        "next_step": "writer",
    }
