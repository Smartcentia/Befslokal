"""
Import Agresso GL-data (Eiendomfebruar.csv) → gl_transactions-tabell.

SRS-logikk:
  - srs_kategori: 'Investering' (konto 1268/4960) | 'Drift' | 'Gjennomstrømning' (H1/H2/HB/RE)
  - is_statsbygg: leverandor_navn ILIKE '%statsbygg%'
  - dim6_anlegg_id: settes hvis konto er anleggskonto OG Dim6 ikke tom
  - property_id: slås opp via dim1_kode → koststed_mapping.property_id
  - belop: Numeric (fjerner mellomrom-tusensep, konverterer komma til punktum)

Kjøring:
    python scripts/import_gl_agresso.py [--dry-run] [--limit 1000]

Forutsetninger:
    - DATABASE_URL i .env
    - finans/Eiendomfebruar.csv finnes (136 055 linjer, latin-1)
"""
from __future__ import annotations
import asyncio
import csv
import os
import sys
import uuid
import datetime
import argparse
from pathlib import Path
from decimal import Decimal, InvalidOperation

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import asyncpg

# Kandidater i prioritert rekkefølge (semikolonseparert, latin-1)
_KANDIDATER = [
    Path(__file__).parent.parent.parent / "finans" / "Eiendom 202001 til 202512 til Øystein(AGRESSO).csv",
    Path(__file__).parent.parent.parent / "finans" / "Eiendom_2020_2025_full.csv",
    Path(__file__).parent.parent.parent / "finans" / "Eiendomfebruar.csv",
]
GL_FILE = next((p for p in _KANDIDATER if p.exists()), _KANDIDATER[-1])

# --- SRS-kategorisering ---
INVESTERING_KONTOER = {"1268", "4960"}
GJENNOMSTRØMNING_BILAGSARTER = {"H1", "H2", "HB", "RE"}

# Alle anleggskontoer (Dim6 = anleggsnr PÅKREVD iflg. SRS 17)
ANLEGG_KONTOER = {
    "1268", "4960",
    "1040", "1049", "1050", "1059", "1060", "1069", "1070", "1079",
    "1080", "1089", "1090", "1099", "1200", "1209", "1210", "1219",
    "1220", "1229", "1230", "1239", "1240", "1249", "1250", "1259",
    "1260", "1269", "1270", "1279", "1280", "1289", "1290", "1298",
    "3800", "3801", "3810",
    "4930", "4960", "4990", "4999",
    "6000", "6010", "6020", "6030", "6040", "6050", "6060", "6071",
    "6551", "7800",
}


def bestem_srs_kategori(konto: str, ba_kode: str) -> str:
    if ba_kode.upper() in GJENNOMSTRØMNING_BILAGSARTER:
        return "Gjennomstrømning"
    if konto in INVESTERING_KONTOER:
        return "Investering"
    return "Drift"


def rens_belop(raw: str) -> Decimal | None:
    """
    Saniterer Agresso-beløp til Decimal.

    Norsk CSV-format (semikolonseparert, latin-1):
      '806,00'       → 806.00     (komma=desimalsep)
      '30 000,00'    → 30000.00   (mellomrom=tusensep, komma=desimalsep)
      '-7 500,00'    → -7500.00   (negativ med mellomrom-tusensep)
      '(7 500,00)'   → -7500.00   (regnskapsnotasjon for negativt)
    """
    if not raw or not raw.strip():
        return None
    s = raw.strip()
    # Regnskapsnotasjon: (123,45) → -123,45
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    # Fjern mellomrom-tusenseparatorer, konverter norsk desimalskilletegn
    s = s.replace(" ", "").replace(",", ".")
    try:
        val = Decimal(s)
        return -val if negative else val
    except InvalidOperation:
        return None


def parse_dato(raw: str) -> datetime.date | None:
    if not raw or not raw.strip():
        return None
    # Formater: "3/31/2023" eller "31.03.2023"
    for fmt in ("%m/%d/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


async def main(dry_run: bool = False, limit: int | None = None):
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL ikke satt i .env")
        sys.exit(1)

    conn_str = db_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"Kobler til database...")
    conn = await asyncpg.connect(conn_str, ssl="require")

    # Last inn koststed → property_id mapping
    km_rows = await conn.fetch("SELECT koststed_kode, property_id FROM koststed_mapping")
    koststed_map: dict[str, str | None] = {r["koststed_kode"]: str(r["property_id"]) if r["property_id"] else None for r in km_rows}
    print(f"Lastet {len(koststed_map)} koststed-mappinger")

    batch_id = f"agresso_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_Eiendomfebruar"
    imported_by = "system_import"

    print(f"Leser {GL_FILE}...")
    rows_to_insert: list[dict] = []
    errors: list[str] = []
    skipped = 0

    with open(GL_FILE, encoding="latin-1") as f:
        reader = csv.DictReader(f, delimiter=";")

        for i, row in enumerate(reader):
            if limit and i >= limit:
                break

            # --- Beløp-sanering (KRITISK) ---
            belop = rens_belop(row.get("Beløp", ""))
            if belop is None:
                errors.append(f"Rad {i+2}: ugyldig beløp '{row.get('Beløp', '')}'")
                skipped += 1
                continue

            konto = row.get("Konto", "").strip()
            ba_kode = row.get("BA", "").strip()
            dim1_kode = row.get("Dim1", "").strip()
            dim6_raw = row.get("Dim6", "").strip()

            # Kategori-felt (nytt format 2025+)
            innkjopskategori_kode = row.get("Innkjøpskategorier", "").strip() or None
            innkjopskategori_navn = row.get("Innkjøpskategorier(T)", "").strip() or None
            underkategori_kode    = row.get("Underkategorier", "").strip() or None
            underkategori_navn    = row.get("Underkategorier(T)", "").strip() or None

            # --- SRS-kategori ---
            srs_kategori = bestem_srs_kategori(konto, ba_kode)

            # --- Dim6: skill mellom anlegg og ansatt ---
            dim6_anlegg_id = None
            dim6_ansatt_id = None
            if dim6_raw:
                if konto in ANLEGG_KONTOER:
                    dim6_anlegg_id = dim6_raw
                else:
                    dim6_ansatt_id = dim6_raw

            # --- Leverandør-flagg ---
            leverandor_navn = row.get("Resk.nr(T)", "").strip() or None
            is_statsbygg = bool(leverandor_navn and "statsbygg" in leverandor_navn.lower())

            # --- Periode og år ---
            periode = row.get("Periode", "").strip() or None
            ar = None
            maaned = None
            if periode and len(periode) == 6:
                try:
                    ar = int(periode[:4])
                    maaned = int(periode[4:])
                except ValueError:
                    pass

            # --- Property lookup via koststed ---
            property_id = koststed_map.get(dim1_kode) if dim1_kode else None

            rows_to_insert.append({
                "transaction_id": str(uuid.uuid4()),
                "batch_id": batch_id,
                "imported_by": imported_by,
                "source_file_ref": GL_FILE.name,
                "ba_kode": ba_kode or None,
                "bilagsnr": row.get("Bilagsnr", "").strip() or None,
                "bilagsdato": parse_dato(row.get("Bilagsdato", "")),
                "periode": periode,
                "ar": ar,
                "maaned": maaned,
                "konto": konto or None,
                "konto_navn": row.get("Konto(T)", "").strip() or None,
                "av_konto": row.get("AV", "").strip() or None,
                "region": row.get("Region", "").strip() or None,
                "dim1_kode": dim1_kode or None,
                "dim1_navn": row.get("Dim1(T)", "").strip() or None,
                "dim2_kode": row.get("Dim2", "").strip() or None,
                "dim2_navn": row.get("Dim2(T)", "").strip() or None,
                "dim3_kode": row.get("Dim3", "").strip() or None,
                "dim4_kode": row.get("Dim4", "").strip() or None,
                "dim5_kode": row.get("Dim5", "").strip() or None,
                "dim6_anlegg_id": dim6_anlegg_id,
                "dim6_ansatt_id": dim6_ansatt_id,
                "dim7_kode": row.get("Dim7", "").strip() or None,
                "innkjopskategori_kode": innkjopskategori_kode,
                "innkjopskategori_navn": innkjopskategori_navn,
                "underkategori_kode": underkategori_kode,
                "underkategori_navn": underkategori_navn,
                "tekst": (row.get("Tekst", "") or "").strip()[:500] or None,
                "belop": belop,
                "leverandor_id": row.get("Resk.nr", "").strip() or None,
                "leverandor_navn": leverandor_navn,
                "property_id": property_id,
                "srs_kategori": srs_kategori,
                "is_statsbygg": is_statsbygg,
                "created_at": datetime.datetime.now(datetime.timezone.utc),
            })

            if (i + 1) % 10000 == 0:
                print(f"  Lest {i+1} rader...")

    print(f"\nLest ferdig: {len(rows_to_insert)} gyldige rader, {skipped} hoppet over, {len(errors)} feil")

    if errors[:5]:
        print("Eksempel-feil:")
        for e in errors[:5]:
            print(f"  {e}")

    if dry_run:
        print("\n[DRY RUN] Ingen data lagret.")
        # Vis statistikk
        kategorier = {}
        for r in rows_to_insert:
            k = r["srs_kategori"]
            kategorier[k] = kategorier.get(k, 0) + 1
        print("SRS-kategorier:", kategorier)
        statsbygg_count = sum(1 for r in rows_to_insert if r["is_statsbygg"])
        print(f"Statsbygg-linjer: {statsbygg_count}")
        anlegg_count = sum(1 for r in rows_to_insert if r["dim6_anlegg_id"])
        print(f"Anleggslinjer med dim6: {anlegg_count}")
        return

    # --- Slett eksisterende data ---
    print("\nSletter eksisterende GL-data...")
    await conn.execute("DELETE FROM gl_transactions")

    # --- Batchinsert 1000 rader om gangen ---
    print("Setter inn data (batch=1000)...")
    inserted = 0
    insert_errors = 0

    COLS = [
        "transaction_id", "batch_id", "imported_by", "source_file_ref",
        "ba_kode", "bilagsnr", "bilagsdato", "periode", "ar", "maaned",
        "konto", "konto_navn", "av_konto", "region",
        "innkjopskategori_kode", "innkjopskategori_navn",
        "underkategori_kode", "underkategori_navn",
        "dim1_kode", "dim1_navn", "dim2_kode", "dim2_navn", "dim3_kode",
        "dim4_kode", "dim5_kode", "dim6_anlegg_id", "dim6_ansatt_id", "dim7_kode",
        "tekst", "belop", "leverandor_id", "leverandor_navn",
        "property_id", "srs_kategori", "is_statsbygg", "created_at",
    ]

    BATCH_SIZE = 1000
    for start in range(0, len(rows_to_insert), BATCH_SIZE):
        batch = rows_to_insert[start:start + BATCH_SIZE]
        try:
            await conn.executemany(
                f"""INSERT INTO gl_transactions ({", ".join(COLS)})
                    VALUES ({", ".join(f"${i+1}" for i in range(len(COLS)))})""",
                [tuple(r[c] for c in COLS) for r in batch],
            )
            inserted += len(batch)
            if inserted % 20000 == 0:
                print(f"  Satt inn {inserted} rader...")
        except Exception as e:
            print(f"  BATCH FEIL ved rad {start}: {e}")
            insert_errors += len(batch)

    print(f"\nFerdig: {inserted} satt inn, {insert_errors} feil")

    # --- Balansesjekk ---
    print("\nKjører balansesjekk (sum per bilagsnr = 0)...")
    ubalanserte = await conn.fetch("""
        SELECT bilagsnr, SUM(belop) as sum_belop, COUNT(*) as antall
        FROM gl_transactions
        WHERE ba_kode IN ('IV', 'IW', 'LE')
        GROUP BY bilagsnr
        HAVING ABS(SUM(belop)) > 0.01
        ORDER BY ABS(SUM(belop)) DESC
        LIMIT 10
    """)
    if ubalanserte:
        print(f"  ADVARSEL: {len(ubalanserte)} ubalanserte bilag (viser topp 10):")
        for r in ubalanserte:
            print(f"    Bilag {r['bilagsnr']}: sum={r['sum_belop']:.2f}, {r['antall']} linjer")
    else:
        print("  Alle bilag er balanserte ✓")

    # --- Statistikk ---
    stats = await conn.fetchrow("""
        SELECT
            COUNT(*) as totalt,
            SUM(CASE WHEN srs_kategori = 'Investering' THEN 1 ELSE 0 END) as investering,
            SUM(CASE WHEN srs_kategori = 'Drift' THEN 1 ELSE 0 END) as drift,
            SUM(CASE WHEN srs_kategori = 'Gjennomstrømning' THEN 1 ELSE 0 END) as gjennomstromning,
            SUM(CASE WHEN is_statsbygg THEN 1 ELSE 0 END) as statsbygg,
            SUM(CASE WHEN property_id IS NOT NULL THEN 1 ELSE 0 END) as koblet_eiendom
        FROM gl_transactions
    """)
    print(f"""
Statistikk:
  Totalt:          {stats['totalt']}
  Investering:     {stats['investering']}
  Drift:           {stats['drift']}
  Gjennomstrøm.:   {stats['gjennomstromning']}
  Statsbygg-linjer:{stats['statsbygg']}
  Koblet eiendom:  {stats['koblet_eiendom']} ({100*stats['koblet_eiendom']//max(stats['totalt'],1)}%)
""")

    await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer Agresso GL-data til Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Les og valider uten å lagre")
    parser.add_argument("--limit", type=int, default=None, help="Begrens antall rader (for testing)")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, limit=args.limit))
