"""
API for institusjonsplasser — budsjetterte og kvalitetssikrede plasser per avdeling.
Kobles til properties via koststed_mapping.

Endepunkter:
  GET /api/v1/plasser/summary?dato=2026-01-01
  GET /api/v1/plasser/by-property/{property_id}?dato=2026-01-01
  GET /api/v1/plasser/total?dato=2026-01-01
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User

router = APIRouter(prefix="/plasser", tags=["plasser"])


@router.get("/total")
async def get_plasser_total(
    dato: Optional[date] = Query(default=None, description="Rapport-dato (ÅÅÅÅ-MM-DD), default: siste tilgjengelige"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Totalt antall budsjetterte og kvalitetssikrede plasser på tvers av alle regioner."""
    if dato is None:
        res = await db.execute(text("SELECT MAX(rapport_dato) FROM institution_plasser"))
        dato = res.scalar()
        if dato is None:
            return {"dato": None, "antall_budsjetterte": 0, "antall_kvalitetssikrede": 0, "antall_avdelinger": 0}

    res = await db.execute(text("""
        SELECT
            SUM(antall_budsjetterte) AS bud,
            SUM(antall_kvalitetssikrede) AS kval,
            COUNT(*) AS avdelinger
        FROM institution_plasser
        WHERE rapport_dato = :dato
    """), {"dato": dato})
    r = res.fetchone()
    return {
        "dato": str(dato),
        "antall_budsjetterte": int(r.bud or 0),
        "antall_kvalitetssikrede": int(r.kval or 0),
        "antall_avdelinger": int(r.avdelinger or 0),
    }


@router.get("/summary")
async def get_plasser_summary(
    dato: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Plasser summert per region og målgruppe."""
    if dato is None:
        res = await db.execute(text("SELECT MAX(rapport_dato) FROM institution_plasser"))
        dato = res.scalar()
        if dato is None:
            return {"dato": None, "regioner": []}

    res = await db.execute(text("""
        SELECT
            region,
            malgruppe,
            SUM(antall_budsjetterte) AS bud,
            SUM(antall_kvalitetssikrede) AS kval,
            COUNT(*) AS avdelinger
        FROM institution_plasser
        WHERE rapport_dato = :dato
        GROUP BY region, malgruppe
        ORDER BY region, SUM(antall_budsjetterte) DESC
    """), {"dato": dato})
    rows = res.fetchall()

    # Bygg region-struktur
    regioner: dict = {}
    for r in rows:
        reg = r.region or "Ukjent"
        if reg not in regioner:
            regioner[reg] = {"region": reg, "antall_budsjetterte": 0, "antall_kvalitetssikrede": 0, "malgrupper": []}
        regioner[reg]["antall_budsjetterte"] += int(r.bud or 0)
        regioner[reg]["antall_kvalitetssikrede"] += int(r.kval or 0)
        regioner[reg]["malgrupper"].append({
            "malgruppe": r.malgruppe,
            "antall_budsjetterte": int(r.bud or 0),
            "antall_kvalitetssikrede": int(r.kval or 0),
            "antall_avdelinger": int(r.avdelinger or 0),
        })

    return {
        "dato": str(dato),
        "regioner": sorted(regioner.values(), key=lambda x: x["antall_budsjetterte"], reverse=True),
    }


@router.get("/by-property/{property_id}")
async def get_plasser_by_property(
    property_id: str,
    dato: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Plasser per avdeling for én eiendom."""
    if dato is None:
        res = await db.execute(text("SELECT MAX(rapport_dato) FROM institution_plasser"))
        dato = res.scalar()
        if dato is None:
            return {"property_id": property_id, "dato": None, "avdelinger": []}

    res = await db.execute(text("""
        SELECT
            koststed_kode,
            malgruppe,
            avdelings_navn,
            antall_budsjetterte,
            antall_kvalitetssikrede
        FROM institution_plasser
        WHERE property_id = :pid AND rapport_dato = :dato
        ORDER BY malgruppe, avdelings_navn
    """), {"pid": property_id, "dato": dato})
    rows = res.fetchall()

    return {
        "property_id": property_id,
        "dato": str(dato),
        "antall_budsjetterte_total": sum(int(r.antall_budsjetterte or 0) for r in rows),
        "antall_kvalitetssikrede_total": sum(int(r.antall_kvalitetssikrede or 0) for r in rows),
        "avdelinger": [
            {
                "koststed_kode": r.koststed_kode,
                "malgruppe": r.malgruppe,
                "avdelings_navn": r.avdelings_navn,
                "antall_budsjetterte": int(r.antall_budsjetterte or 0),
                "antall_kvalitetssikrede": int(r.antall_kvalitetssikrede or 0),
            }
            for r in rows
        ],
    }
