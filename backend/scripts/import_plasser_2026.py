"""
Import av budsjetterte institusjonsplasser for 2026 til institution_plasser-tabellen.

Kjøres via: railway run python backend/scripts/import_plasser_2026.py <excel-fil>

Excel-format (fane: Ark1):
  Region | Målgruppe | Enhetsnr. | Enhetens/Institusjonens navn
  | Avdelingens koststed | Navn på avdeling
  | Antall kvalitetssikrede institusjonsplasser avd. pr. 01.01
  | Antall budsjetterte institusjonsplasser avd. per 01.01

Kobling: koststed_kode → koststed_mapping → property_id
Rapport-dato: 2026-01-01 (per 01.01 i filen)
"""
import sys
import uuid
import asyncio
from datetime import date
from pathlib import Path

import pandas as pd

# Legg til backend-rot i path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
os.environ.setdefault("DATABASE_URL",
    "postgresql+asyncpg://postgres.vwvhxcqxadblrftuvsds:Sunnyowl_6533@aws-1-eu-west-1.pooler.supabase.com:5432/postgres")

from sqlalchemy import text
from app.db.session import SessionLocal


RAPPORT_DATO = date(2026, 1, 1)

COL_REGION = "Region "
COL_MALGRUPPE = "Målgruppe"
COL_ENHETSNR = "Enhetsnr."
COL_INSTITUSJONS_NAVN = "Enhetens/Institusjonens navn"
COL_KOSTSTED = "Avdelingens koststed"
COL_AVDELINGS_NAVN = "Navn på avdeling"
COL_KVAL = "Antall kvalitetssikrede institusjonsplasser avd. pr. 01.01"
COL_BUD = "Antall budsjetterte institusjonsplasser avd. per 01.01"


async def _load_koststed_map(db) -> dict:
    res = await db.execute(text(
        "SELECT koststed_kode, property_id FROM koststed_mapping WHERE property_id IS NOT NULL"
    ))
    return {str(r.koststed_kode): str(r.property_id) for r in res.fetchall()}


async def import_plasser(filepath: str):
    df = pd.read_excel(filepath, sheet_name="Ark1")
    print(f"Lest {len(df)} rader fra {filepath}")

    batch_id = uuid.uuid4()

    async with SessionLocal() as db:
        # Last koststed-kart
        koststed_map = await _load_koststed_map(db)
        print(f"Koststed-kart: {len(koststed_map)} koststeder med property_id")

        # Slett eksisterende rader for denne rapport-datoen (idempotent)
        del_res = await db.execute(text(
            "DELETE FROM institution_plasser WHERE rapport_dato = :dato"
        ), {"dato": RAPPORT_DATO})
        print(f"Slettet {del_res.rowcount} eksisterende rader for {RAPPORT_DATO}")

        inserted = 0
        skipped_no_koststed = 0
        skipped_no_match = 0

        for _, row in df.iterrows():
            koststed_raw = row.get(COL_KOSTSTED)
            if pd.isna(koststed_raw):
                skipped_no_koststed += 1
                continue

            koststed_kode = str(int(float(koststed_raw)))
            property_id = koststed_map.get(koststed_kode)
            if not property_id:
                skipped_no_match += 1
                print(f"  Ingen match: koststed {koststed_kode}")
                continue

            region = str(row.get(COL_REGION) or "").strip() or None
            malgruppe = str(row.get(COL_MALGRUPPE) or "").strip() or None
            enhetsnr_raw = row.get(COL_ENHETSNR)
            enhetsnr = int(float(enhetsnr_raw)) if pd.notna(enhetsnr_raw) else None
            institusjons_navn = str(row.get(COL_INSTITUSJONS_NAVN) or "").strip() or None
            avdelings_navn = str(row.get(COL_AVDELINGS_NAVN) or "").strip() or None
            kval_raw = row.get(COL_KVAL)
            bud_raw = row.get(COL_BUD)
            antall_kval = int(float(kval_raw)) if pd.notna(kval_raw) else None
            antall_bud = int(float(bud_raw)) if pd.notna(bud_raw) else None

            await db.execute(text("""
                INSERT INTO institution_plasser (
                    id, koststed_kode, property_id, region, malgruppe,
                    enhetsnr, institusjons_navn, avdelings_navn,
                    antall_kvalitetssikrede, antall_budsjetterte,
                    rapport_dato, import_batch_id, imported_by
                ) VALUES (
                    gen_random_uuid(), :koststed_kode, :property_id, :region, :malgruppe,
                    :enhetsnr, :institusjons_navn, :avdelings_navn,
                    :antall_kval, :antall_bud,
                    :rapport_dato, :batch_id, 'import_script'
                )
            """), {
                "koststed_kode": koststed_kode,
                "property_id": property_id,
                "region": region,
                "malgruppe": malgruppe,
                "enhetsnr": enhetsnr,
                "institusjons_navn": institusjons_navn,
                "avdelings_navn": avdelings_navn,
                "antall_kval": antall_kval,
                "antall_bud": antall_bud,
                "rapport_dato": RAPPORT_DATO,
                "batch_id": str(batch_id),
            })
            inserted += 1

        await db.commit()

    print(f"\n✅ Ferdig:")
    print(f"  Importert:        {inserted}")
    print(f"  Uten koststed:    {skipped_no_koststed}")
    print(f"  Uten match:       {skipped_no_match}")

    # Sjekk totaler
    async with SessionLocal() as db:
        res = await db.execute(text("""
            SELECT
                SUM(antall_budsjetterte) AS bud_total,
                SUM(antall_kvalitetssikrede) AS kval_total,
                COUNT(*) AS rader
            FROM institution_plasser
            WHERE rapport_dato = :dato
        """), {"dato": RAPPORT_DATO})
        r = res.fetchone()
        print(f"\n  Totaler i DB:")
        print(f"    Budsjetterte plasser: {r.bud_total}")
        print(f"    Kval.sikrede plasser: {r.kval_total}")
        print(f"    Rader:                {r.rader}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Bruk: python {sys.argv[0]} <excel-fil>")
        sys.exit(1)
    asyncio.run(import_plasser(sys.argv[1]))
