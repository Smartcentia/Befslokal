#!/usr/bin/env python3
"""
Viser antall eiendommer, enheter, kontrakter og partier (leietakere/utleiere) i databasen.

Kjør fra backend: python3 scripts/count_core_data.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.unit import Unit

# Registrer relasjoner (Property -> Center, RiskAssessment, InternalControlCase)
import app.domains.core.models.center  # noqa: F401
import app.domains.hms.models.risk  # noqa: F401
import app.domains.hms.models.internal_control  # noqa: F401


async def main():
    async with SessionLocal() as db:
        props = await db.scalar(select(func.count(Property.property_id)))
        units = await db.scalar(select(func.count(Unit.unit_id)))
        contracts = await db.scalar(select(func.count(Contract.contract_id)))
        parties = await db.scalar(select(func.count(Party.party_id)))

        # Kontrakter med party (leietaker/utleier koblet)
        with_party = await db.scalar(
            select(func.count(Contract.contract_id)).where(Contract.party_id.isnot(None))
        )

        print("=" * 50)
        print("📊 Eiendom, kontrakt og leietaker/utleier")
        print("=" * 50)
        print(f"  Eiendommer (properties):  {props}")
        print(f"  Enheter (units):         {units}")
        print(f"  Kontrakter:              {contracts}")
        print(f"  Partier (leietakere/utl.): {parties}")
        print(f"  Kontrakter med part kobl: {with_party}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
