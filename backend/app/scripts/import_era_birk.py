"""
Import ERA Birk-register (Enhetsregister for barneverninstitusjoner) inn i institution_plasser.

Kilde: «Institusjoner i og utenfor staten - Formålsbygg» eksportert fra ERA/Birk.
CSV-format: latin-1, semikolon, første linje er tom, andre linje er header.

Kolonner brukt:
  Region, EnhetID, Enhetsnavn, TilhørighetEnhetID, Tilhørighet,
  Enhetstype (Utledet), Antall G/K - plasser, Hjemler,
  Eierskapenhet, Lokasjonskode, Fylke, Kommune, Adresse

Kjør:
  cd /path/to/BEFS_CLEAN
  railway run --service BEFS1 python3 backend/app/scripts/import_era_birk.py <CSV_PATH>
"""
import sys
import os
import csv
import uuid
import asyncio
import re
from datetime import date
from typing import Optional

# Bootstrap path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else (
    "/Users/frank/Downloads/"
    "Institusjoner  i og utenfor staten - Formålsbygg"
    "(ERA-01 Enhetsregister (Birk) Fl) (5).csv"
)
RAPPORT_DATO = date(2026, 1, 1)
DATA_KILDE = "era_birk_2026"


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="latin-1") as f:
        lines = f.readlines()
    # First line is blank, second is header
    reader = csv.DictReader(lines[1:], delimiter=";")
    rows = []
    for r in reader:
        if not r.get("EnhetID", "").strip():
            continue  # skip blank/summary rows
        rows.append(r)
    return rows


def normalize_eierskap(raw: str) -> str:
    """Normalize ownership field to canonical values."""
    raw = raw.strip()
    mapping = {
        "kommunal": "Kommunal",
        "Kommunal": "Kommunal",
        "Statlig": "Statlig",
        "Privat, ideell": "Privat, ideell",
        "Privat, kommersiell": "Privat, kommersiell",
    }
    return mapping.get(raw, raw or "Ukjent")


def extract_hjemler(hjemler_str: str) -> Optional[str]:
    """Extract § references as compact string, e.g. '§4-2 §5-1'."""
    paragraphs = re.findall(r"§\s*([\d-]+)", hjemler_str or "")
    if not paragraphs:
        return None
    return " ".join(f"§{p}" for p in paragraphs[:5])


async def run():
    rows = load_csv(CSV_PATH)
    print(f"Loaded {len(rows)} valid rows from ERA CSV")

    batch_id = str(uuid.uuid4())

    async with SessionLocal() as db:
        # Check columns exist
        col_check = await db.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'institution_plasser'
        """))
        existing_cols = {r[0] for r in col_check.fetchall()}
        if "eierskap" not in existing_cols or "data_kilde" not in existing_cols:
            print("ERROR: eierskap/data_kilde columns missing — run alembic migration first")
            print("  railway run --service BEFS1 alembic upgrade head")
            return

        # Delete existing ERA records for this date (idempotent)
        deleted = await db.execute(text(
            "DELETE FROM institution_plasser WHERE data_kilde = :kilde AND rapport_dato = :dato"
        ), {"kilde": DATA_KILDE, "dato": RAPPORT_DATO})
        print(f"Deleted {deleted.rowcount} existing ERA records for {RAPPORT_DATO}")

        inserted = 0
        matched = 0
        skipped_no_plasser = 0

        for r in rows:
            plasser_raw = r.get("Antall G/K - plasser", "").strip()
            if not plasser_raw.isdigit():
                skipped_no_plasser += 1
                continue

            antall_kval = int(plasser_raw)
            lok_kode = r.get("Lokasjonskode", "").strip() or None
            eierskap = normalize_eierskap(r.get("Eierskapenhet", ""))
            region = r.get("Region", "").strip() or None
            enhet_id_raw = r.get("EnhetID", "").strip()
            enhetsnr = int(enhet_id_raw) if enhet_id_raw.isdigit() else None
            inst_navn = r.get("Tilhørighet", "").strip() or r.get("Enhetsnavn", "").strip()
            avd_navn = r.get("Enhetsnavn", "").strip()
            hjemler = extract_hjemler(r.get("Hjemler", ""))
            adresse = r.get("Adresse", "").strip() or None
            kommune = r.get("Kommune", "").strip() or None
            fylke = r.get("Fylke", "").strip() or None

            # Try to find matching property_id via Lokasjonskode
            property_id = None
            if lok_kode:
                res = await db.execute(text("""
                    SELECT property_id FROM properties
                    WHERE unit_id_erp = :kode OR koststed_kode = :kode
                    LIMIT 1
                """), {"kode": lok_kode})
                row_db = res.fetchone()
                if row_db:
                    property_id = str(row_db.property_id)
                    matched += 1

            # Build address string for geocoding later
            full_adresse = None
            if adresse:
                parts = [adresse]
                if kommune:
                    parts.append(kommune)
                full_adresse = ", ".join(parts)

            await db.execute(text("""
                INSERT INTO institution_plasser (
                    id, koststed_kode, property_id, region, malgruppe,
                    enhetsnr, institusjons_navn, avdelings_navn,
                    antall_kvalitetssikrede, antall_budsjetterte,
                    rapport_dato, eierskap, data_kilde,
                    import_batch_id, imported_by,
                    adresse, kommune, fylke
                ) VALUES (
                    :id, :kost, :pid, :region, :malgruppe,
                    :enhetsnr, :inst_navn, :avd_navn,
                    :kval, NULL,
                    :dato, :eierskap, :kilde,
                    :batch, :by,
                    :adresse, :kommune, :fylke
                )
            """), {
                "id": str(uuid.uuid4()),
                "kost": lok_kode or f"ERA-{enhet_id_raw}",
                "pid": property_id,
                "region": region,
                "malgruppe": hjemler,
                "enhetsnr": enhetsnr,
                "inst_navn": inst_navn[:200] if inst_navn else None,
                "avd_navn": avd_navn[:200] if avd_navn else None,
                "kval": antall_kval,
                "dato": RAPPORT_DATO,
                "eierskap": eierskap,
                "kilde": DATA_KILDE,
                "batch": batch_id,
                "by": "era-birk-import-2026",
                "adresse": full_adresse[:300] if full_adresse else None,
                "kommune": kommune[:100] if kommune else None,
                "fylke": fylke[:100] if fylke else None,
            })
            inserted += 1

        await db.commit()

        print(f"\nInserted: {inserted} rows")
        print(f"Matched to property_id: {matched}")
        print(f"Skipped (no plasser-tall): {skipped_no_plasser}")

        # Verify totals
        res = await db.execute(text("""
            SELECT eierskap,
                   COUNT(*) AS avd,
                   SUM(antall_kvalitetssikrede) AS kval
            FROM institution_plasser
            WHERE data_kilde = :kilde AND rapport_dato = :dato
            GROUP BY eierskap
            ORDER BY kval DESC
        """), {"kilde": DATA_KILDE, "dato": RAPPORT_DATO})
        print("\nTotals per eierskap (ERA):")
        for row in res.fetchall():
            print(f"  {row.eierskap}: {row.avd} avd, {row.kval} kval plasser")


if __name__ == "__main__":
    asyncio.run(run())
