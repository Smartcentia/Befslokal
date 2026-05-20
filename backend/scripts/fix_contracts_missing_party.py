#!/usr/bin/env python3
"""
Sett party_id på aktive kontrakter som mangler leietaker, når det finnes
søskenkontrakt på samme enhet med party, eller annen aktiv kontrakt på samme eiendom.

  python3 scripts/fix_contracts_missing_party.py --dry-run   # standard
  python3 scripts/fix_contracts_missing_party.py --apply
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections import Counter
from pathlib import Path
from uuid import UUID

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

try:
    from dotenv import load_dotenv

    load_dotenv(_backend / ".env", override=False)
except Exception:
    pass

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit


async def main_async(args: argparse.Namespace) -> int:
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL mangler.", file=sys.stderr)
        return 2

    async with SessionLocal() as db:
        r = await db.execute(
            select(Contract)
            .options(selectinload(Contract.unit))
            .where(Contract.status == "active", Contract.party_id.is_(None), Contract.unit_id.isnot(None))
        )
        need = r.scalars().all()

        updates: list[tuple[UUID, UUID, str]] = []

        for c in need:
            uid = c.unit_id
            pid_prop = c.unit.property_id if c.unit else None
            chosen_party: UUID | None = None
            reason = ""

            r_sib = await db.execute(
                select(Contract.party_id)
                .where(
                    Contract.unit_id == uid,
                    Contract.status == "active",
                    Contract.party_id.isnot(None),
                    Contract.contract_id != c.contract_id,
                )
                .limit(1)
            )
            row = r_sib.first()
            if row and row[0]:
                chosen_party = row[0]
                reason = "same_unit_sibling"

            if chosen_party is None and pid_prop:
                r_prop = await db.execute(
                    select(Contract.party_id)
                    .join(Unit, Contract.unit_id == Unit.unit_id)
                    .where(
                        Unit.property_id == pid_prop,
                        Contract.status == "active",
                        Contract.party_id.isnot(None),
                    )
                )
                parties = [x[0] for x in r_prop.fetchall() if x[0]]
                if parties:
                    chosen_party = Counter(parties).most_common(1)[0][0]
                    reason = "same_property_majority"

            if chosen_party:
                updates.append((c.contract_id, chosen_party, reason))

        print(f"Aktive kontrakter uten party: {len(need)}")
        print(f"Kan fylles automatisk: {len(updates)}")

        for cid, party_id, reason in updates:
            print(f"  {cid}  -> party {party_id}  ({reason})")

        if args.apply and updates:
            for cid, party_id, _ in updates:
                await db.execute(
                    update(Contract).where(Contract.contract_id == cid).values(party_id=party_id)
                )
            await db.commit()
            print(f"Oppdatert {len(updates)} kontrakter.")
        elif args.apply:
            print("Ingen oppdateringer.")
        else:
            print("[--dry-run] Bruk --apply for å skrive.")

    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Kun vis (samme som uten flagg)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
