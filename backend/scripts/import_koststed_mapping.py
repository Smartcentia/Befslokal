"""
Import koststed_eiendom_mapping.csv → koststed_mapping-tabell i Supabase.

Kjøring:
    python scripts/import_koststed_mapping.py

Forutsetninger:
    - DATABASE_URL i .env (postgresql+asyncpg://...)
    - finans/koststed_eiendom_mapping.csv finnes (572 rader, UTF-8)
"""
import asyncio
import csv
import os
import sys
from pathlib import Path

# Legg til backend-roten i path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import asyncpg
from decimal import Decimal

MAPPING_FILE = Path(__file__).parent.parent.parent / "finans" / "koststed_eiendom_mapping.csv"


async def main():
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL ikke satt i .env")
        sys.exit(1)

    # Konverter asyncpg URL
    conn_str = db_url.replace("postgresql+asyncpg://", "postgresql://")

    print(f"Kobler til database...")
    conn = await asyncpg.connect(conn_str, ssl="require")

    # Les mapping-fil
    print(f"Leser {MAPPING_FILE}...")
    rows = []
    with open(MAPPING_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kode = row.get("Koststed_Kode", "").strip()
            if not kode:
                continue
            rows.append({
                "koststed_kode": kode,
                "koststed_navn": row.get("Koststed_Navn", "").strip() or None,
                "region": _normalize_region(row.get("Region", "").strip()),
                "eksempel_adresse": row.get("Eksempel_Adresse", "").strip() or None,
            })

    print(f"Lest {len(rows)} koststed-rader")

    # Slett eksisterende (idempotent)
    deleted = await conn.execute("DELETE FROM koststed_mapping")
    print(f"Slettet eksisterende rader")

    # Sett inn alle
    inserted = 0
    errors = 0
    for r in rows:
        try:
            await conn.execute(
                """
                INSERT INTO koststed_mapping (koststed_kode, koststed_navn, region, eksempel_adresse)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (koststed_kode) DO UPDATE
                  SET koststed_navn = EXCLUDED.koststed_navn,
                      region = EXCLUDED.region,
                      eksempel_adresse = EXCLUDED.eksempel_adresse
                """,
                r["koststed_kode"], r["koststed_navn"],
                r["region"], r["eksempel_adresse"],
            )
            inserted += 1
        except Exception as e:
            print(f"  FEIL på {r['koststed_kode']}: {e}")
            errors += 1

    print(f"\nResultat: {inserted} satt inn, {errors} feil")

    # Vis region-fordeling
    rows_db = await conn.fetch(
        "SELECT region, COUNT(*) as n FROM koststed_mapping GROUP BY region ORDER BY n DESC"
    )
    print("\nRegion-fordeling:")
    for r in rows_db:
        print(f"  {r['region'] or 'Ukjent':15s}: {r['n']} koststed")

    await conn.close()
    print("\nFerdig!")


def _normalize_region(raw: str) -> str:
    """Normaliser regionkoder fra CSV til standard BEFS-navn."""
    mapping = {
        "Øst": "Øst",
        "ost": "Øst",
        "Sør": "Sør",
        "sor": "Sør",
        "Vest": "Vest",
        "Midt": "Midt-Norge",
        "Nord": "Nord",
        "Bufdir": "Bufdir",
        "7": "Ukjent",
        "": "Ukjent",
    }
    return mapping.get(raw, raw)


if __name__ == "__main__":
    asyncio.run(main())
