#!/usr/bin/env python3
"""
Sjekk om alle eiendommer og enheter/avdelinger har adresser.
- Eiendommer: properties.address (null eller tom = mangler)
- Enheter (units): har eget address-felt; hvis tom brukes eiendommens adresse.
  Rapporterer eiendommer uten adresse og enheter uten egen eller eiendomsadresse.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit

# Optional: load .env for DATABASE_URL
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass


async def main():
    async with SessionLocal() as db:
        # --- Eiendommer ---
        total_p = (await db.execute(select(func.count()).select_from(Property))).scalar() or 0
        with_addr = (
            await db.execute(
                select(func.count()).select_from(Property).where(
                    Property.address.isnot(None),
                    func.trim(Property.address) != "",
                )
            )
        ).scalar() or 0
        without_addr = total_p - with_addr

        print("=" * 60)
        print("ADRESSE-SJEKK: EIENDOMMER OG ENHETER")
        print("=" * 60)
        print("\n📌 Eiendommer (properties)")
        print(f"   Totalt:           {total_p}")
        print(f"   Med adresse:      {with_addr}")
        print(f"   Uten adresse:    {without_addr}")
        if total_p:
            pct = 100 * with_addr / total_p
            print(f"   Dekning:          {pct:.1f}%")

        if without_addr > 0:
            result = await db.execute(
                select(Property.property_id, Property.name, Property.address, Property.city)
                .where(
                    (Property.address.is_(None)) | (func.trim(Property.address) == "")
                )
            )
            rows = result.all()
            print(f"\n   Eiendommer uten adresse ({len(rows)}):")
            for r in rows[:20]:
                name = (r.name or "-")[:40]
                print(f"     - {name}  (id: {r.property_id})")
            if len(rows) > 20:
                print(f"     ... og {len(rows) - 20} til")

        # --- Enheter (avdelinger) ---
        total_u = (await db.execute(select(func.count()).select_from(Unit))).scalar() or 0
        # Enheter med egen adresse (units.address)
        units_with_own_addr = (
            await db.execute(
                select(func.count()).select_from(Unit).where(
                    Unit.address.isnot(None),
                    func.trim(Unit.address) != "",
                )
            )
        ).scalar() or 0
        # Enheter som har adresse: enten egen eller eiendommens
        units_with_prop_addr = (
            await db.execute(
                select(func.count())
                .select_from(Unit)
                .join(Property, Unit.property_id == Property.property_id)
                .where(
                    Property.address.isnot(None),
                    func.trim(Property.address) != "",
                )
            )
        ).scalar() or 0
        # Enheter uten noen adresse (verken unit.address eller property.address)
        result_no_addr = await db.execute(
            select(Unit.unit_id, Unit.address, Property.name, Property.address.label("prop_address"))
            .join(Property, Unit.property_id == Property.property_id)
            .where(
                (Unit.address.is_(None) | (func.trim(Unit.address) == "")),
                (Property.address.is_(None) | (func.trim(Property.address) == "")),
            )
        )
        units_without_any_addr = result_no_addr.all()

        print("\n📌 Enheter / avdelinger (units)")
        print("   (Enheter kan ha egen address; ellers brukes eiendommens adresse.)")
        print(f"   Totalt enheter:      {total_u}")
        print(f"   Med egen adresse:    {units_with_own_addr}")
        print(f"   Eiendom har adresse: {units_with_prop_addr}")
        print(f"   Uten noen adresse:  {len(units_without_any_addr)}")
        if total_u:
            pct_u = 100 * (total_u - len(units_without_any_addr)) / total_u
            print(f"   Dekning (egen/eiendom): {pct_u:.1f}%")

        if units_without_any_addr:
            print(f"\n   Enheter uten egen og uten eiendomsadresse ({len(units_without_any_addr)}):")
            for r in units_without_any_addr[:15]:
                pname = (r.name or "-")[:35]
                print(f"     - unit {r.unit_id} (eiendom: {pname})")
            if len(units_without_any_addr) > 15:
                print(f"     ... og {len(units_without_any_addr) - 15} til")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
