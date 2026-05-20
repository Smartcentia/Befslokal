"""
enrich_lydia_contracts.py — Beriker BEFS-data med felter fra Lydia-uttrekk

STRATEGI (VIKTIG):
  • Aldri overskriv eksisterende (ikke-NULL) verdier
  • Alle UPDATE-setninger bruker WHERE felt IS NULL (eller sjekker i Python)
  • Aldri berør: status, start_date, end_date, contract_name, address, city,
    postal_code, municipality, party_id, utleier, region, belop

Felter som berikes (kun NULL-felter):
  properties.gnr              ← Gårdsnummer
  properties.bnr              ← Bruksnummer
  properties.municipality_code← Kommunenummer
  properties.lokasjon_type    ← Type lokasjon (ny kolonne)
  properties.formaalsbygg     ← Formålsbygg (ny kolonne)
  properties.lydia_id         ← Lydia Id (ny kolonne)

Kjøring:
  DATABASE_URL="postgresql+asyncpg://..." \
  LYDIA_CSV="/Users/frank/Downloads/Uttrekk Lydia 23.04 (3).csv" \
  python scripts/enrich_lydia_contracts.py [--dry-run]
"""

import asyncio
import csv
import os
import re
import sys
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")
LYDIA_CSV = os.environ.get(
    "LYDIA_CSV",
    "/Users/frank/Downloads/Uttrekk Lydia 23.04 (3).csv",
)
DRY_RUN = "--dry-run" in sys.argv


def extract_lokalisering_code(lok: str) -> str | None:
    """'2401 - Senter for familie...' → '2401'"""
    m = re.match(r"^(\d+)", lok.strip())
    return m.group(1) if m else None


def to_int(s: str) -> int | None:
    s = s.strip()
    return int(s) if s and s.isdigit() else None


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


async def enrich(rows: list[dict]) -> None:
    # Use SQLAlchemy async to match project patterns
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    pg_url = DATABASE_URL
    if not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(pg_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Fetch all properties with lokalisering_id
        result = await session.execute(sa.text("""
            SELECT property_id::text, lokalisering_id,
                   gnr, bnr, municipality_code,
                   lokasjon_type, formaalsbygg, lydia_id
            FROM properties
            WHERE lokalisering_id IS NOT NULL
        """))
        prop_rows = result.mappings().all()

        prop_by_lok: dict[str, dict] = {}
        for p in prop_rows:
            lok = (p["lokalisering_id"] or "").strip()
            if lok:
                prop_by_lok[lok] = dict(p)

        print(f"DB: {len(prop_by_lok)} properties med lokalisering_id")
        print(f"CSV: {len(rows)} rader fra Lydia")

        updated = 0
        skipped_no_match = 0
        skipped_no_change = 0

        for row in rows:
            lok_code = extract_lokalisering_code(row.get("Lokalisering", ""))
            if not lok_code:
                skipped_no_match += 1
                continue

            prop = prop_by_lok.get(lok_code)
            if not prop:
                skipped_no_match += 1
                continue

            prop_id = prop["property_id"]
            lydia_id = row.get("Id", "").strip() or None

            # Build update dict — ONLY for NULL fields
            updates: dict[str, object] = {}

            gnr = to_int(row.get("Gårdsnummer", ""))
            if gnr is not None and prop["gnr"] is None:
                updates["gnr"] = gnr

            bnr = to_int(row.get("Bruksnummer", ""))
            if bnr is not None and prop["bnr"] is None:
                updates["bnr"] = bnr

            komnr = row.get("Kommunenummer", "").strip() or None
            if komnr and prop["municipality_code"] is None:
                updates["municipality_code"] = komnr

            lok_type = row.get("Type lokasjon", "").strip() or None
            if lok_type and prop["lokasjon_type"] is None:
                updates["lokasjon_type"] = lok_type

            formaals = row.get("Formålsbygg", "").strip() or None
            if formaals and prop["formaalsbygg"] is None:
                updates["formaalsbygg"] = formaals

            if lydia_id and prop["lydia_id"] is None:
                updates["lydia_id"] = lydia_id

            if not updates:
                skipped_no_change += 1
                continue

            set_sql = ", ".join(f"{k} = :{k}" for k in updates)
            updates["prop_id"] = prop_id

            if DRY_RUN:
                print(f"  [DRY] {prop_id} ({lok_code}): {list(updates.keys())}")
            else:
                await session.execute(
                    sa.text(f"""
                        UPDATE properties
                        SET {set_sql}
                        WHERE property_id::text = :prop_id
                    """),
                    updates,
                )
            updated += 1

        if not DRY_RUN:
            await session.commit()

    await engine.dispose()

    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Resultat:")
    print(f"  ✅ Oppdatert:       {updated}")
    print(f"  ⏭️  Ingen endring:   {skipped_no_change}")
    print(f"  ❌ Ingen match:     {skipped_no_match}")
    print()
    print("Felter som BLE berørt (kun NULL-felter):")
    print("  properties.gnr, .bnr, .municipality_code, .lokasjon_type, .formaalsbygg, .lydia_id")
    print()
    print("Felter som IKKE ble berørt (safe):")
    print("  status, start_date, end_date, contract_name, address, city,")
    print("  postal_code, municipality, party_id, region, amount, belop")


async def main() -> None:
    if not DATABASE_URL:
        print("ERROR: Set DATABASE_URL environment variable")
        sys.exit(1)

    rows = load_csv(LYDIA_CSV)
    print(f"Loaded {len(rows)} rader fra: {LYDIA_CSV}")
    if DRY_RUN:
        print("*** DRY RUN — ingen data endres ***\n")
    await enrich(rows)


if __name__ == "__main__":
    asyncio.run(main())
