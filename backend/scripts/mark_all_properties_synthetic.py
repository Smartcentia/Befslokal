#!/usr/bin/env python3
"""
Merker alle eiendommer som syntetiske ved å sette external_data.synthetic = True
(og synthetic_note) på hver eiendom. Eksisterende external_data beholdes og slås sammen.

Krever DATABASE_URL. Kjør før ensure_synthetic_contract_and_tenant.py hvis du vil
at alle eiendommer skal få syntetisk kontrakt og leietaker.
"""
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
from app.domains.core.models.user import User  # noqa: F401
from app.domains.core.models.center import Center  # noqa: F401
from app.domains.hms.models.risk import RiskAssessment  # noqa: F401
from app.domains.hms.models.internal_control import InternalControlCase  # noqa: F401
from app.domains.core.models.property import Property

SYNTHETIC_NOTE = "Alle eiendommer merkes som syntetiske"


async def mark_all_synthetic(dry_run: bool = False):
    print("Merker alle eiendommer som syntetiske")
    print("=" * 50)

    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        props = list(result.scalars().all())
        print(f"Fant {len(props)} eiendommer")

        updated = 0
        for prop in props:
            ext = dict(prop.external_data or {})
            if ext.get("synthetic") is True and ext.get("synthetic_note") == SYNTHETIC_NOTE:
                continue
            ext["synthetic"] = True
            ext["synthetic_note"] = SYNTHETIC_NOTE
            prop.external_data = ext
            db.add(prop)
            updated += 1
            if dry_run:
                print(f"  [dry-run] Ville merket: {prop.name or prop.address or prop.property_id}")

        if not dry_run:
            await db.commit()
            print(f"\n✅ Merket {updated} eiendommer som syntetiske")

    if dry_run:
        print(f"\n[dry-run] Ville merket {updated} eiendommer. Kjør uten --dry-run for å lagre.")


if __name__ == "__main__":
    import asyncio
    import argparse
    parser = argparse.ArgumentParser(description="Merk alle eiendommer som syntetiske")
    parser.add_argument("--dry-run", action="store_true", help="Vis bare hva som ville blitt gjort")
    args = parser.parse_args()
    asyncio.run(mark_all_synthetic(dry_run=args.dry_run))
