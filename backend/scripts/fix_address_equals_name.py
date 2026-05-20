"""
Script for å rette eiendommer der address ble feilaktig satt til navn. Ved BIRK-import
ble tidligere navn brukt som fallback for adresse når CSV manglet adresse. Dette skal
være null – bruk dette scriptet for å rette eksisterende data.

Kjør:
  cd backend && PYTHONPATH=. python -m scripts.fix_address_equals_name [--dry-run]

For prod: sett Supabase Session Pooler-URL i .env (ikke railway run – intern URL resolver ikke lokalt).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

try:
    from dotenv import load_dotenv
    load_dotenv(_backend / ".env", override=True)
except Exception:
    pass

from sqlalchemy import select

from app.db.session import SessionLocal
import app.db.base  # noqa: F401
from app.domains.core.models.property import Property


async def run(dry_run: bool) -> dict:
    """Sett address=null for properties der address == name."""
    from app.core.config import settings
    url = str(settings.DATABASE_URL or "")
    host = ""
    if "@" in url:
        host = url.split("@")[1].split(":")[0].split("/")[0]
    if not url or host in ("", "host"):
        print("FEIL: DATABASE_URL mangler eller er placeholder. Sjekk backend/.env", file=sys.stderr)
        print("  Lokal: postgresql+asyncpg://postgres:postgres@localhost:5432/eiendom (docker compose up -d db)", file=sys.stderr)
        print("  Prod:  Supabase Session Pooler-URL (ikke .railway.internal – den resolver ikke lokalt)", file=sys.stderr)
        sys.exit(1)
    if host.endswith(".railway.internal"):
        print("FEIL: Railway intern host resolver ikke lokalt. Bruk Supabase Session Pooler-URL.", file=sys.stderr)
        sys.exit(1)

    async with SessionLocal() as db:
        result = await db.execute(
            select(Property).where(
                Property.address.isnot(None),
                Property.address != "",
                Property.address == Property.name,
            )
        )
        props = result.scalars().all()
        count = len(props)

        if count == 0:
            return {"fixed": 0, "message": "Ingen eiendommer å rette"}

        sample = [{"name": p.name, "address_was": p.address} for p in props[:5]]

        if not dry_run:
            for p in props:
                p.address = None
            await db.commit()

        return {
            "fixed": count,
            "dry_run": dry_run,
            "sample": sample,
        }


def main():
    parser = argparse.ArgumentParser(description="Rett address=null når address == name")
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    args = parser.parse_args()

    result = asyncio.run(run(dry_run=args.dry_run))
    print(f"Resultat: {result}")
    if args.dry_run and result.get("fixed", 0) > 0:
        print("(dry-run – kjør uten --dry-run for å lagre endringer)")


if __name__ == "__main__":
    main()
