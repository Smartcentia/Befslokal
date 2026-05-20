"""Delt logikk for aggregert kontraktskostnadsoversikt (admin + API-alias)."""

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit


async def build_contract_cost_overview(db: AsyncSession) -> Dict[str, Any]:
    query = select(Contract).options(
        selectinload(Contract.unit).selectinload(Unit.property)
    )
    result = await db.execute(query)
    contracts = result.scalars().all()

    rows: List[Dict[str, Any]] = []
    for c in contracts:
        prop_name = "Ukjent Eiendom"
        if c.unit and c.unit.property:
            prop_name = c.unit.property.name

        amount_data = c.amount or {}

        annual_rent = amount_data.get("rent") or amount_data.get("amount_per_year") or 0
        try:
            annual_rent = float(annual_rent)
        except (ValueError, TypeError):
            annual_rent = 0.0

        caretaker = float(c.caretaker_cost or 0)
        cleaning = float(c.cleaning_cost or 0)
        parking = float(c.parking_cost or 0)
        card_reader = float(c.card_reader_cost or 0)

        sum_extra = caretaker + cleaning + parking + card_reader
        sum_total = annual_rent + sum_extra

        rows.append(
            {
                "id": str(c.id),
                "contract_id": str(c.id),
                "prop_name": prop_name,
                "category": c.category or "Ukjent",
                "status": c.status or "Ukjent",
                "rent": round(annual_rent, 2),
                "extra": round(sum_extra, 2),
                "total": round(sum_total, 2),
            }
        )

    rows.sort(key=lambda x: x["prop_name"] or "")

    return {
        "count": len(rows),
        "total_rent": sum(r["rent"] for r in rows),
        "total_extra": sum(r["extra"] for r in rows),
        "total_overall": sum(r["total"] for r in rows),
        "data": rows,
    }
