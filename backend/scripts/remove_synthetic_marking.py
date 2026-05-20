"""
Fjern all syntetisk merking fra eiendommer, kontrakter og parter.
Etter kjøring vil ingen rader lenger ha external_data.synthetic / data_source='synthetic' / synthetic_note,
så dashboard og andre tjenester behandler alt som «ekte» data.

Kjør fra backend: cd backend && python scripts/remove_synthetic_marking.py
Kan kjøres med --dry-run for å bare vise hva som ville blitt endret.
"""
from __future__ import annotations

import asyncio
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party


def _clean_external_data(ext: dict | None, label: str) -> tuple[dict | None, bool]:
    """Fjern kun syntetisk-relaterte nøkler. Returner (ny dict eller None, endret)."""
    if ext is None:
        return None, False
    ext = dict(ext)
    changed = False
    if ext.pop("synthetic", None) is not None:
        changed = True
    if ext.pop("synthetic_note", None) is not None:
        changed = True
    if ext.get("data_source") == "synthetic":
        ext.pop("data_source")
        changed = True
    if ext.get("data_source") == "is_synthetic":  # noen script bruker is_synthetic
        ext.pop("data_source")
        changed = True
    # Behold tom dict som {} i stedet for None for konsistens
    return ext if ext else None, changed


async def run(dry_run: bool):
    async with SessionLocal() as db:
        # 1. Properties
        res = await db.execute(select(Property))
        properties = res.scalars().all()
        prop_updated = 0
        for p in properties:
            new_ext, changed = _clean_external_data(p.external_data, "property")
            if changed:
                prop_updated += 1
                if not dry_run:
                    p.external_data = new_ext
                    db.add(p)
        print(f"Eiendommer: fjernet syntetisk merking fra {prop_updated} av {len(properties)}")

        # 2. Contracts
        res = await db.execute(select(Contract))
        contracts = res.scalars().all()
        contract_updated = 0
        for c in contracts:
            new_ext, changed = _clean_external_data(c.external_data, "contract")
            if changed:
                contract_updated += 1
                if not dry_run:
                    c.external_data = new_ext
                    db.add(c)
        print(f"Kontrakter: fjernet syntetisk merking fra {contract_updated} av {len(contracts)}")

        # 3. Parties
        res = await db.execute(select(Party))
        parties = res.scalars().all()
        party_updated = 0
        for party in parties:
            new_ext, changed = _clean_external_data(party.external_data, "party")
            if changed:
                party_updated += 1
                if not dry_run:
                    party.external_data = new_ext
                    db.add(party)
        print(f"Parter (leietakere): fjernet syntetisk merking fra {party_updated} av {len(parties)}")

        if not dry_run and (prop_updated or contract_updated or party_updated):
            await db.commit()
            print("Endringer er lagret.")
        elif dry_run:
            print("(Dry-run – ingen endringer lagret)")


def main():
    ap = argparse.ArgumentParser(description="Fjern all syntetisk merking fra properties/contracts/parties.")
    ap.add_argument("--dry-run", action="store_true", help="Vis bare antall som ville blitt endret")
    args = ap.parse_args()
    asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
