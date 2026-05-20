"""
Import 2025 GL data from 01.txt into gl_transactions.

Usage:
    cd backend
    python -m app.scripts.import_gl_2025 [--file path/to/01.txt] [--dry-run]

The file format is space-separated with the following columns:
    BA  Region  Koststed  EnhetNavn  [ProjNr]  [ProjTekst]  Formål  Art  [Leverandør]  Beløp

Linking: Koststed (6-digit) → properties.unit_id_erp → property_id
"""

import asyncio
import argparse
import re
import sys
import os
from decimal import Decimal
from pathlib import Path

# Add backend to path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.financial_models import GLTransaction
from app.domains.core.models.property import Property

SOURCE_SYSTEM = "gl_2025_midt"
DATA_YEAR = 2025

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "docs" / "01.txt"

KNOWN_FORMALS = [
    "Barnevernsinstitusjoner",
    "Fosterhjem",
    "Hjelpetiltak i hjemmet",
    "Fosterhjemstjenesten",
    "Inntak",
    "Regionale fellesfunksjoner",
    "Familieverntjeneste",
    "Sentre for foreldre og barn",
]

# Art values sorted longest-first for greedy matching
KNOWN_ART = sorted([
    "Leie lokaler fra Statsbygg",
    "Leie lokaler andre utleiere",
    "Leie parkeringsplass",
    "Strøm og oppvarming",
    "Renhold lokaler",
    "Renovasjon, vann, avløp o.l.",
    "Reparasjon og vedlikehold leide lokaler",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Vakthold lokaler",
    "Vaktmestertjenester",
    "Fellesutgifter Statsbygg - indre vedlikehold",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter andre utleiere",
    "Fellesutgifter",
    "Annen kostnad lokaler",
    "Fast bygningsinventar og påkostning, leide bygg",
    "Oppgradering og påkostning leide lokaler - under kr 50 000",
], key=len, reverse=True)

LEASE_ARTS = {
    "Leie lokaler fra Statsbygg",
    "Leie lokaler andre utleiere",
    "Leie parkeringsplass",
}


def parse_line(line: str):
    """Parse one line from 01.txt into a dict of GL fields."""
    tokens = line.strip().split()
    if len(tokens) < 6:
        return None

    ba = tokens[0]
    region = tokens[1] + " " + tokens[2]
    koststed = tokens[3]

    # Validate koststed is a 6-digit number
    if not re.fullmatch(r"\d{6}", koststed):
        return None

    # Last token is amount (Norwegian decimal: comma)
    amount_str = tokens[-1].replace(",", ".")
    try:
        amount = float(amount_str)
    except ValueError:
        return None

    # Middle = everything between koststed and amount
    middle = " ".join(tokens[4:-1])

    # --- Find Art by scanning middle, then verify Formål precedes it ---
    # This handles cases where Formål keywords appear in the unit name
    found = None
    for art in KNOWN_ART:
        pos = 0
        while True:
            idx = middle.find(art, pos)
            if idx == -1:
                break
            # Art must be preceded by space or start-of-string
            if idx > 0 and middle[idx - 1] != " ":
                pos = idx + 1
                continue
            before = middle[:idx].rstrip()
            # Check if before ends with a known Formål
            for formal in sorted(KNOWN_FORMALS, key=len, reverse=True):
                if before.endswith(formal):
                    vendor_raw = middle[idx + len(art):].strip()
                    prefix = before[: -len(formal)].strip()
                    found = {
                        "art": art,
                        "formal": formal,
                        "vendor": vendor_raw or None,
                        "prefix": prefix,
                    }
                    break
            if found:
                break
            pos = idx + 1
        if found:
            break

    if not found:
        return None

    # --- Parse prefix for unit name and optional project number/text ---
    prefix = found["prefix"]
    unit_name = prefix
    proj_nr = None
    proj_tekst = None

    # Project number: 5-6 digits NOT starting with 5 (Koststed starts with 5)
    m = re.search(r"\b(\d{5,6})\b", prefix)
    if m and not m.group(1).startswith("5"):
        unit_name = prefix[: m.start()].strip()
        rest = prefix[m.start():].strip()
        proj_nr = m.group(1)
        proj_tekst = rest[len(proj_nr):].strip() or None

    return {
        "ba": ba,
        "region": region,
        "koststed": koststed,
        "unit_name": unit_name or None,
        "proj_nr": proj_nr,
        "proj_tekst": proj_tekst,
        "formal": found["formal"],
        "art": found["art"],
        "vendor": found["vendor"],
        "amount": amount,
    }


async def resolve_property_id(db: AsyncSession, koststed: str, unit_name):
    """Try to map Koststed → property_id via unit_id_erp, then name fallback."""
    # Pass 1: direct unit_id_erp match
    result = await db.execute(
        select(Property.property_id).where(Property.unit_id_erp == koststed).limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return str(row)

    # Pass 2: name matching (unit_name contains or is contained in property.name)
    if unit_name:
        # Try exact name match first
        result = await db.execute(
            select(Property.property_id).where(Property.name == unit_name).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            return str(row)

        # Try substring: unit_name words in property.name
        words = [w for w in unit_name.split() if len(w) > 4]
        if words:
            from sqlalchemy import and_
            conditions = [
                Property.name.ilike(f"%{w}%") for w in words[:2]
            ]
            result = await db.execute(
                select(Property.property_id).where(and_(*conditions)).limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                return str(row)

    return None


async def run_import(filepath: Path, dry_run: bool = False) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    lines = filepath.read_text(encoding="utf-8").splitlines()
    total = len([l for l in lines if l.strip()])

    parsed_ok = 0
    parse_errors = 0
    inserted = 0
    mapped = 0
    unmapped_koststed: dict[str, str] = {}  # koststed → unit_name

    async with AsyncSessionLocal() as db:
        # Wipe existing batch for idempotent re-import
        if not dry_run:
            await db.execute(
                delete(GLTransaction).where(GLTransaction.source_system == SOURCE_SYSTEM)
            )
            await db.commit()
            print(f"Cleared existing '{SOURCE_SYSTEM}' records.")

        for i, raw in enumerate(lines, 1):
            if not raw.strip():
                continue

            parsed = parse_line(raw)
            if not parsed:
                parse_errors += 1
                print(f"  PARSE ERROR line {i}: {raw[:100]}", file=sys.stderr)
                continue

            parsed_ok += 1
            koststed = parsed["koststed"]
            unit_name = parsed["unit_name"]

            property_id = await resolve_property_id(db, koststed, unit_name)
            if property_id:
                mapped += 1
            else:
                if koststed not in unmapped_koststed:
                    unmapped_koststed[koststed] = unit_name or ""

            if not dry_run:
                if property_id is None:
                    continue  # skip rows that can't be linked to a property
                gl = GLTransaction(
                    property_id=property_id,
                    region_name=parsed["region"],
                    department_code=koststed,
                    department_name=unit_name,
                    dim2_code=parsed["proj_nr"],
                    dim2_name=parsed["proj_tekst"],
                    purpose_name=parsed["formal"],
                    account_name=parsed["art"],
                    supplier_name=parsed["vendor"],
                    amount=parsed["amount"],
                    year=DATA_YEAR,
                    ba_code=parsed["ba"],
                    ba_name="Bufetat",
                    source_system=SOURCE_SYSTEM,
                    category="lease" if parsed["art"] in LEASE_ARTS else "other",
                    vendor=parsed["vendor"],
                )
                db.add(gl)
                inserted += 1

                if inserted % 200 == 0:
                    await db.flush()

        if not dry_run:
            await db.commit()

    print()
    print("=" * 50)
    print(f"Fil:           {filepath.name}")
    print(f"Rader totalt:  {total}")
    print(f"Parset ok:     {parsed_ok}")
    print(f"Parse-feil:    {parse_errors}")
    print(f"Importert:     {inserted}" + (" (dry-run)" if dry_run else ""))
    print(f"Koblet til eiendom: {mapped} ({100*mapped//max(parsed_ok,1)}%)")
    print(f"Uten kobling:  {len(unmapped_koststed)}")
    if unmapped_koststed:
        print()
        print("Umappede Koststed-koder:")
        for k, name in sorted(unmapped_koststed.items()):
            print(f"  {k}  {name}")
    print("=" * 50)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import 2025 GL data from 01.txt")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE,
                        help=f"Path to 01.txt (default: {DEFAULT_FILE})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and map without writing to DB")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run_import(args.file, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
