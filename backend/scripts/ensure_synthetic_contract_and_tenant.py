#!/usr/bin/env python3
"""
Sikrer at alle syntetiske eiendommer har minst én syntetisk kontrakt og tilknyttet leietaker.
- Finner eiendommer der external_data.synthetic er True (eller data_source er 'synthetic').
- For hver slik eiendom uten aktiv kontrakt: oppretter én Unit, én Party (syntetisk leietaker)
  og én Contract (Leiekontrakt, aktiv) med external_data.synthetic = True.

Krever DATABASE_URL. For å merke alle eiendommer som syntetiske, kjør først
scripts/mark_all_properties_synthetic.py. Kan kjøres etter establish_bufdir_unmatched.py
eller uavhengig for å fylle inn manglende syntetisk kontrakt/leietaker.
"""
import uuid as uuid_mod
from datetime import date, datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import sys as _sys
if str(BACKEND_DIR) not in _sys.path:
    _sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from app.db.session import SessionLocal
# Last relaterte modeller før Property/InternalControlCase slik at relationship("Center"), "User" etc. kan løses
from app.domains.core.models.user import User  # noqa: F401
from app.domains.core.models.center import Center  # noqa: F401
from app.domains.hms.models.risk import RiskAssessment  # noqa: F401
from app.domains.hms.models.internal_control import InternalControlCase  # noqa: F401
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.contract import Contract


SYNTHETIC_TENANT_NAME = "Bufetat (syntetisk)"


def _is_synthetic(prop: Property) -> bool:
    """Sjekk om eiendom regnes som syntetisk."""
    ext = prop.external_data or {}
    if ext.get("synthetic") is True:
        return True
    if ext.get("data_source") == "synthetic":
        return True
    return False


async def _get_or_create_synthetic_tenant(db) -> Party:
    """Finn eller opprett én felles syntetisk leietaker (Bufetat syntetisk)."""
    stmt = select(Party).where(
        Party.name == SYNTHETIC_TENANT_NAME,
        Party.orgnr.is_(None),
    )
    result = await db.execute(stmt)
    party = result.scalar_one_or_none()
    if party:
        return party
    party = Party(
        party_id=uuid_mod.uuid4(),
        name=SYNTHETIC_TENANT_NAME,
        orgnr=None,
        external_data={"synthetic": True, "synthetic_note": "Leietaker for syntetiske eiendommer"},
    )
    db.add(party)
    await db.flush()
    return party


async def _property_has_active_contract(db, property_id) -> bool:
    """Sjekk om eiendom har minst én enhet med aktiv kontrakt."""
    stmt_units = select(Unit).where(Unit.property_id == property_id)
    res_units = await db.execute(stmt_units)
    units = list(res_units.scalars().all())
    if not units:
        return False
    from sqlalchemy import or_
    unit_ids = [u.unit_id for u in units]
    stmt_contract = select(Contract).where(
        Contract.unit_id.in_(unit_ids),
        Contract.status == "active",
    )
    res = await db.execute(stmt_contract)
    return res.first() is not None


async def ensure_synthetic_contract_and_tenant(dry_run: bool = False):
    print("Sikrer syntetisk kontrakt og leietaker for syntetiske eiendommer")
    print("=" * 60)

    async with SessionLocal() as db:
        # Hent alle eiendommer
        stmt = select(Property)
        result = await db.execute(stmt)
        all_props = list(result.scalars().all())

        synthetic_props = [p for p in all_props if _is_synthetic(p)]
        print(f"Fant {len(synthetic_props)} syntetiske eiendommer (av {len(all_props)} totalt)")

        if not synthetic_props:
            print("Ingen syntetiske eiendommer å oppdatere.")
            return

        synthetic_tenant = await _get_or_create_synthetic_tenant(db)
        if not dry_run:
            await db.flush()

        created_units = 0
        created_contracts = 0
        skipped = 0

        for prop in synthetic_props:
            has_contract = await _property_has_active_contract(db, prop.property_id)
            if has_contract:
                skipped += 1
                continue

            # Finn eller opprett Unit for eiendommen (eiendom kan ha flere enheter – bruk første)
            stmt_u = select(Unit).where(Unit.property_id == prop.property_id)
            res_u = await db.execute(stmt_u)
            unit = res_u.scalars().first()
            if not unit:
                unit = Unit(
                    unit_id=uuid_mod.uuid4(),
                    property_id=prop.property_id,
                    purpose="Hovedenhet",
                    area_sqm=prop.total_area,
                    external_data={"synthetic": True},
                )
                db.add(unit)
                await db.flush()
                created_units += 1
                if dry_run:
                    print(f"  [dry-run] Ville opprettet enhet for: {prop.name or prop.address}")

            if dry_run:
                created_contracts += 1
                continue

            # Syntetisk leie: bruk rent_summary fra external_data hvis tilgjengelig
            amount_per_year = None
            ext = prop.external_data or {}
            fin = ext.get("financials") or {}
            if isinstance(fin.get("rent_summary"), (int, float)):
                amount_per_year = float(fin["rent_summary"])

            contract = Contract(
                contract_id=uuid_mod.uuid4(),
                unit_id=unit.unit_id,
                party_id=synthetic_tenant.party_id,
                status="active",
                category="Leiekontrakt",
                start_date=date.today(),
                end_date=None,
                amount={"currency": "NOK", "amount_per_year": amount_per_year},
                periods=[{"start_date": date.today().isoformat(), "end_date": None, "index_name": "KPI"}],
                external_data={
                    "synthetic": True,
                    "synthetic_note": "Syntetisk kontrakt for syntetisk eiendom (ingen registertreff)",
                },
            )
            db.add(contract)
            created_contracts += 1
            print(f"  + Kontrakt + leietaker: {prop.name or prop.address or str(prop.property_id)}")

        if not dry_run:
            await db.commit()

    print()
    print(f"Oppsummering: {created_units} enheter opprettet, {created_contracts} kontrakter opprettet, {skipped} hoppet over (hadde allerede aktiv kontrakt).")
    if dry_run:
        print("(Kjør uten --dry-run for å persistere.)")


if __name__ == "__main__":
    import asyncio
    import argparse
    parser = argparse.ArgumentParser(description="Sikre syntetisk kontrakt og leietaker for syntetiske eiendommer")
    parser.add_argument("--dry-run", action="store_true", help="Vis bare hva som ville blitt gjort")
    args = parser.parse_args()
    asyncio.run(ensure_synthetic_contract_and_tenant(dry_run=args.dry_run))
