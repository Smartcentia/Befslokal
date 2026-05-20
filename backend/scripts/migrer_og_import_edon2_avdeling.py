#!/usr/bin/env python3
"""
Kjør migrering for unit_short_type/unit_type_derived, deretter e-don2-import
slik at eiendommer får satt Enhetskorttype (Avdeling/Barnevernsinstitusjon) og Enhetstype (Utledet).

Krever: DATABASE_URL i backend/.env (eller miljøvariabel).
Modell-imports må matche app/scripts/import_edon2_data.py slik at SQLAlchemy-mapper løses.

Bruk:
  cd backend && python scripts/migrer_og_import_edon2_avdeling.py
  # Med Railway: railway run -- python scripts/migrer_og_import_edon2_avdeling.py
"""
import os
import sys
import asyncio
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Last .env før noen app-import
from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

if not os.environ.get("DATABASE_URL"):
    print("FEIL: DATABASE_URL er ikke satt. Sett den i backend/.env eller som miljøvariabel.")
    sys.exit(1)


def run_migration():
    """Kjør alembic upgrade head."""
    print("1. Kjører migrering (alembic upgrade head)...")
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print("STDOUT:", r.stdout)
        print("STDERR:", r.stderr)
        return False
    print("   Migrering OK.")
    return True


async def run_edon2_import():
    """Kjør e-don2-import (leser e-don2.txt / e-dom.txt fra backend/)."""
    print("2. Kjører e-don2-import...")
    from app.db.session import SessionLocal
    from app.services.data_management import DataManagementService
    # Samme modell-imports som import_edon2_data.py – må være registrert for Property-mapper
    from app.domains.core.models.property import Property  # noqa: F401
    from app.domains.core.models.unit import Unit  # noqa: F401
    from app.domains.core.models.contract import Contract  # noqa: F401
    from app.domains.core.models.party import Party  # noqa: F401
    from app.domains.core.models.center import Center  # noqa: F401
    from app.domains.hms.models.risk import RiskAssessment  # noqa: F401
    from app.domains.hms.models.internal_control import InternalControlCase  # noqa: F401
    from app.models.file_meta import FileMeta  # noqa: F401
    from app.domains.core.models.user import User  # noqa: F401
    from app.domains.core.models.audit import AuditLog  # noqa: F401

    source_files = ["e-don2.txt", "e-dom.txt", "e-don.txt", "e-dom2.txt"]
    all_contents = []
    for name in source_files:
        p = os.path.join(BACKEND_DIR, name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                content = f.read()
                if content:
                    all_contents.append(content)
                    print(f"   Lastet {name} ({len(content)} bytes)")

    if not all_contents:
        print("   ADVARSEL: Ingen e-don2/e-dom-filer funnet i backend/. Hopper over import.")
        return True

    async with SessionLocal() as db:
        result = await DataManagementService.import_edon2_csv(db, all_contents)

    if result.get("status") == "success":
        print(f"   Import OK. Oppdatert {result.get('updated', 0)} eiendommer.")
    else:
        print(f"   Import feilet: {result.get('message')}")
        return False
    return True


def main():
    if not run_migration():
        sys.exit(2)
    if not asyncio.run(run_edon2_import()):
        sys.exit(3)
    print("Ferdig. unit_short_type og unit_type_derived er satt for matchende eiendommer.")


if __name__ == "__main__":
    main()
