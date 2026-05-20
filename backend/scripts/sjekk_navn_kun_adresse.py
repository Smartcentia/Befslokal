#!/usr/bin/env python3
"""
Sjekk eiendommer som kun har adresse som navn (ingen egentlig eiendomsnavn).

Kriterier for "kun adresse":
- name == address (eksakt)
- name matcher norsk adresseformat: ", NNNN Sted" (postnummer + poststed)
- name er lik eller svært lik address (normalisert)

Kjør: cd backend && railway run python3 scripts/sjekk_navn_kun_adresse.py
eller: DATABASE_URL=... python3 scripts/sjekk_navn_kun_adresse.py

Samlet revisjon (Bufdir + rapport): se scripts/audit_properties_quality_bufdir.py
"""
import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.db.base  # noqa: F401 - laster alle modeller
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

# Norsk adresse: "Gateadresse, 1234 Sted" – komma, 4 siffer, poststed
ADDRESS_PATTERN = re.compile(r",\s*\d{4}\s+", re.IGNORECASE)


def _normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def is_address_only_name(name: Optional[str], address: Optional[str]) -> bool:
    """Sjekk om name ser ut til å være kun adresse (ingen egentlig eiendomsnavn)."""
    if not name or not name.strip():
        return False
    name = name.strip()
    addr = (address or "").strip()

    # 1. Eksakt match name == address
    if addr and _normalize(name) == _normalize(addr):
        return True

    # 2. Name matcher norsk adresseformat ", NNNN Sted" og er kort/ligner adresse
    if ADDRESS_PATTERN.search(name):
        # Hvis name også inneholder address som substring, er det sannsynligvis kun adresse
        if addr and addr.lower() in name.lower():
            return True
        # Hvis name er "gatenavn X, 1234 Sted" uten annen beskrivelse (kort, ingen " - ")
        # Typiske adresser har ikke " - " i seg (som i "Institusjon - Sted - Adresse")
        if " - " not in name and len(name) < 80:
            return True

    # 3. Name er lik address med evt. postnummer/poststed lagt til
    if addr and name.lower().startswith(addr.lower()):
        rest = name[len(addr) :].strip()
        if not rest or re.match(r"^[,\s\d]+", rest):  # kun rest av adresse
            return True

    return False


async def main():
    async with SessionLocal() as s:
        r = await s.execute(select(Property).where(Property.name.isnot(None)))
        props = r.scalars().all()

        total = len(props)
        address_only = []

        for p in props:
            if is_address_only_name(p.name, p.address):
                address_only.append(p)

        print("Eiendommer med kun adresse som navn")
        print("=" * 60)
        print(f"Eiendommer med name satt: {total}")
        print(f"Kun adresse som navn:      {len(address_only)}")
        print()

        if address_only:
            print("Eksempler (første 25):")
            for p in address_only[:25]:
                print(f"  name:    {p.name}")
                print(f"  address: {p.address}")
                print(f"  lok_id:  {p.lokalisering_id}")
                print()


if __name__ == "__main__":
    asyncio.run(main())
