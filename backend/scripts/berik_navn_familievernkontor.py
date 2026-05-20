#!/usr/bin/env python3
"""
Berik eiendommer med navn fra familievernkontor-mapping (Bufdir.no).

Leser backend/data/familievernkontor_mapping.json (manuelle treff) og
backend/data/familievernkontor_bufdir.json (auto: offisielt navn + besøksadresser
fra skraping). Oppdaterer properties.name når adresse/postnr matcher.

Manuelle rader vinner ved lik adresse-nøkkel. Kjør skrape først ved behov:
  python3 scripts/scrape_familievernkontor_bufdir.py

Kjør: cd backend && railway run python3 scripts/berik_navn_familievernkontor.py [--dry-run]
"""
import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

import app.db.base  # noqa: F401
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

from familievernkontor_bufdir_mapping import load_bufdir_auto_mappings, merge_mappings

MAPPING_FILE = BACKEND_DIR / "data" / "familievernkontor_mapping.json"
BUFDIR_JSON = BACKEND_DIR / "data" / "familievernkontor_bufdir.json"


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    return str(s).strip().lower()


def _mapping_matches_address(m: dict, addr: str, postal: str) -> bool:
    """True hvis eiendommens adresse/postnr matcher mapping (inkl. bufdir-auto uten postnr)."""
    pattern = _norm(m.get("address_pattern", ""))
    m_postal = (m.get("postal") or "").strip()
    name = (m.get("name") or "").strip()
    if not pattern or not name:
        return False
    if pattern not in addr:
        return False
    if m_postal:
        return m_postal in postal
    # Auto fra Bufdir uten postnr: krever tydelig adresse for å unngå feiltreff
    if len(pattern) < 12 and not re.search(r"\d", pattern):
        return False
    return True


async def main():
    parser = argparse.ArgumentParser(description="Berik eiendomsnavn fra familievernkontor-mapping")
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    args = parser.parse_args()

    if not MAPPING_FILE.exists():
        print(f"Mapping-fil ikke funnet: {MAPPING_FILE}")
        sys.exit(1)

    data = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    manual = data.get("mappings", [])
    auto = load_bufdir_auto_mappings(BUFDIR_JSON)
    if not auto and BUFDIR_JSON.exists():
        print(
            f"Advarsel: {BUFDIR_JSON} finnes men ga ingen auto-mapping. "
            "Kjør: python3 scripts/scrape_familievernkontor_bufdir.py",
        )
    elif not BUFDIR_JSON.exists():
        print(
            f"Info: {BUFDIR_JSON} mangler — kun manuelle oppføringer i {MAPPING_FILE.name} brukes.",
        )
    mappings = merge_mappings(manual, auto)

    async with SessionLocal() as s:
        r = await s.execute(select(Property))
        all_props = r.scalars().all()

        updates = []
        for prop in all_props:
            addr = _norm(prop.address or "")
            postal = _norm(prop.postal_code or "")
            if not addr:
                continue

            for m in mappings:
                name = m.get("name", "").strip()
                if not name:
                    continue
                if _mapping_matches_address(m, addr, postal):
                    updates.append((prop, name))
                    break

        if not updates:
            print("Ingen eiendommer matchet familievernkontor-mapping.")
            return

        print(f"Funn: {len(updates)} eiendommer kan få nytt navn.")
        for prop, new_name in updates[:15]:
            print(f"  {prop.address} -> {new_name!r}")

        if not args.dry_run:
            for prop, new_name in updates:
                prop.name = new_name
            await s.commit()
            print(f"\nOppdatert {len(updates)} eiendommer.")
        else:
            print(f"\n[--dry-run] Ville oppdatere {len(updates)} eiendommer.")


if __name__ == "__main__":
    asyncio.run(main())
