#!/usr/bin/env python3
"""
Sjekk hva som finnes i databasen for CSV-import «Oversikt bygg og eiendom».

Oversikt bygg CSV matcher på properties.lokalisering_id = kode fra "XXXX - Navn".
E-don2 bruker Lokasjonskode (koststed, f.eks. 331810) – ikke samme som 4711.

Kjør: cd backend && railway run python3 scripts/sjekk_lokalisering_for_import.py
eller: DATABASE_URL=... python3 scripts/sjekk_lokalisering_for_import.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.core.models.property import Property

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("Mangler DATABASE_URL.")
    sys.exit(1)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def main():
    async with Session() as s:
        total = (await s.execute(select(func.count()).select_from(Property))).scalar()
        with_lok = (
            await s.execute(
                select(func.count()).select_from(Property).where(Property.lokalisering_id.isnot(None))
            )
        ).scalar()
        print(f"Eiendommer totalt: {total}")
        print(f"Med lokalisering_id satt: {with_lok}")
        print()

        # Furuly / NyeFuruly
        for name_part in ("Furuly", "NyeFuruly"):
            r = await s.execute(
                select(Property)
                .where(Property.name.ilike(f"%{name_part}%"))
                .limit(5)
            )
            props = r.scalars().all()
            for p in props:
                print(f"  {p.name}: lokalisering_id={p.lokalisering_id!r} unit_id_erp={p.unit_id_erp!r} adresse={p.address}")
        print()

        # CSV bruker 4711 for Furuly – finnes det noen med 4711?
        r = await s.execute(select(Property).where(Property.lokalisering_id == "4711"))
        match = r.scalar_one_or_none()
        if match:
            print(f"Treff for lokalisering_id=4711: {match.name} ({match.address})")
        else:
            print("Ingen eiendom med lokalisering_id=4711 (Furuly i Oversikt bygg CSV)")
        print()

        # Eksempler på lokalisering_id-verdier
        r = await s.execute(
            select(Property.lokalisering_id, func.count())
            .where(Property.lokalisering_id.isnot(None))
            .group_by(Property.lokalisering_id)
            .order_by(func.count().desc())
            .limit(15)
        )
        print("Vanligste lokalisering_id (antall eiendommer):")
        for lid, cnt in r.all():
            print(f"  {lid}: {cnt}")


if __name__ == "__main__":
    asyncio.run(main())
