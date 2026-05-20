#!/usr/bin/env python3
"""
Import av Innkjøpsanalyse 2026 lønnsutgifter.xlsx til BEFS-databasen.

Importerer to datasett:
  1. Lønnsutgifter (fane 8)  → salary_costs-tabellen
  2. Innkjøpskategorier (fan 2–7, 9) → innkjop_nasjonal_summary-tabellen

Kjøring:
    python scripts/import_innkjop_excel.py /path/to/fil.xlsx
    python scripts/import_innkjop_excel.py /path/to/fil.xlsx --dry-run
    python scripts/import_innkjop_excel.py /path/to/fil.xlsx --only-lonn
    python scripts/import_innkjop_excel.py /path/to/fil.xlsx --only-innkjop

Krav:
    pip install pandas openpyxl thefuzz python-Levenshtein
    DATABASE_URL satt i miljøet (eller .env i backend/)
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import os
import sys
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("import_innkjop")

# ── Konstanter ────────────────────────────────────────────────────────────────
YEAR_COLS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
PARTIAL_YEAR = 2026          # dette året er et delår i filen
FUZZY_CUTOFF = 75            # thefuzz score (0–100)
BATCH_ID = f"innkjopsanalyse_2026_excel_{datetime.date.today().isoformat()}"
DATA_SOURCE = "innkjopsanalyse_2026_excel"

# Region-navn (brukes til å identifisere hierarki-rader i lønnsarket)
REGION_NAMES = {
    "region midt-norge", "region nord", "region sør",
    "region vest", "region øst", "bufdir", "bufetat",
}

# Faner med regional pivottabell-struktur (fane-navn → kategori-navn)
PIVOT_SHEETS = {
    "Lokaler, repar og vedlikehold": "Lokaler og vedlikehold",
    "Varer og tjenester":            "Varer og tjenester",
    "Investeringer":                 "Investeringer",
    "Andre kostnader":               "Andre kostnader",
    "Klientrelaterte driftsutgifter": "Klientrelaterte driftsutgifter",
}

# Faner med enkel liste-struktur (Radetiketter | Kontantbeløp)
LIST_SHEETS = {
    "Kjøp av bv tjenester":  "Kjøp av barnevernstjenester",
    "Tilskudd":              "Tilskudd",
}

# ── Hjelpefunksjoner ─────────────────────────────────────────────────────────

def _safe_decimal(val) -> Decimal:
    """Konverter verdi til Decimal. Returnerer Decimal(0) ved feil/NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return Decimal(0)
    try:
        s = str(val).replace("\xa0", "").replace(" ", "").replace("\u2009", "").strip()
        if not s or s in ("-", "—", "nan", "None"):
            return Decimal(0)
        if "," in s and "." not in s:
            s = s.replace(",", ".")
        elif "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return Decimal(0)


def _is_header_row(row_val) -> bool:
    """True dersom raden er en hierarki-/gruppe-header (ingen tall)."""
    return row_val is None or (isinstance(row_val, float) and pd.isna(row_val))


# ── Del 1: Lønnsutgifter ─────────────────────────────────────────────────────

def parse_lonn_sheet(xl: pd.ExcelFile) -> list[dict]:
    """
    Parser 'Lønnsutgifter'-fanen.

    Returnerer liste av dicts:
        {institution_name, region, year, belop, is_partial_year}
    """
    # Header ligger på rad 7 (0-indeksert), metadata i rad 0–6
    df = xl.parse("Lønnsutgifter", header=7, dtype=object)

    # Kolonnenavn: første kolonne = institusjonsnavn, resten = år + Totalsum
    first_col = df.columns[0]
    year_cols: dict[int, object] = {}
    for col in df.columns[1:]:
        try:
            yr = int(float(str(col).strip()))
            if yr in YEAR_COLS:
                year_cols[yr] = col
        except (ValueError, TypeError):
            pass

    if not year_cols:
        log.error("Lønnsutgifter: fant ingen årskolonner!")
        return []

    records: list[dict] = []
    current_region: str = "Ukjent"

    for _, row in df.iterrows():
        inst_raw = str(row.get(first_col, "") or "").strip()
        lower = inst_raw.lower()

        if not inst_raw or lower == "totalsum":
            continue

        # Hierarki-deteksjon: rad uten tall i årskolonnene = gruppeheader
        has_any_value = any(
            not _is_header_row(row.get(col)) and _safe_decimal(row.get(col)) != 0
            for col in year_cols.values()
        )
        if not has_any_value:
            # Kan være region-header
            if lower in REGION_NAMES or lower.startswith("region "):
                current_region = inst_raw
            continue

        # Datarad – legg til per år
        for yr, col in year_cols.items():
            belop = _safe_decimal(row.get(col))
            if belop == 0:
                continue
            records.append({
                "institution_name": inst_raw,
                "region": current_region,
                "year": yr,
                "belop": belop,
                "is_partial_year": yr == PARTIAL_YEAR,
            })

    log.info("Lønnsutgifter: parsede %d institusjons-år-rader", len(records))
    return records


def match_properties(db: Session, records: list[dict]) -> list[dict]:
    """
    Fuzzy-matcher institusjonsnavn mot properties.name / department_name.
    Setter property_id = None for umatchede rader (lagres uansett for revisjon).
    """
    try:
        from thefuzz import fuzz, process as fuzz_process
        use_fuzzy = True
    except ImportError:
        log.warning("thefuzz ikke installert – bruker kun eksakt matching. "
                    "Installer med: pip install thefuzz python-Levenshtein")
        use_fuzzy = False

    prop_rows = db.execute(text(
        "SELECT property_id::text, name, department_name FROM properties WHERE name IS NOT NULL"
    )).fetchall()

    # Bygg oppslagstabell: lower(navn) → property_id
    exact_map: dict[str, str] = {}
    fuzzy_choices: list[str] = []
    fuzzy_to_pid: dict[str, str] = {}

    for row in prop_rows:
        pid = row[0]
        for field in (row[1], row[2]):
            if field:
                key = field.strip().lower()
                exact_map[key] = pid
                fuzzy_choices.append(key)
                fuzzy_to_pid[key] = pid

    def _match(name: str) -> Optional[str]:
        n = name.strip().lower()
        if n in exact_map:
            return exact_map[n]
        # Substring-sjekk
        for prop_name, pid in exact_map.items():
            if prop_name in n or n in prop_name:
                return pid
        # Fuzzy (thefuzz)
        if use_fuzzy and fuzzy_choices:
            best = fuzz_process.extractOne(n, fuzzy_choices, scorer=fuzz.token_sort_ratio)
            if best and best[1] >= FUZZY_CUTOFF:
                return fuzzy_to_pid[best[0]]
        return None

    unmatched_names: set[str] = set()
    enriched: list[dict] = []
    match_count = 0

    for rec in records:
        pid = _match(rec["institution_name"])
        if pid:
            match_count += 1
        else:
            unmatched_names.add(rec["institution_name"])
        enriched.append({**rec, "property_id": pid})

    unique_institutions = len({r["institution_name"] for r in records})
    log.info(
        "Matching: %d unike institusjoner, %d matchet (%.1f%%), %d umatchet",
        unique_institutions,
        unique_institutions - len(unmatched_names),
        100 * (unique_institutions - len(unmatched_names)) / max(unique_institutions, 1),
        len(unmatched_names),
    )
    if unmatched_names:
        log.info("Umatchede navn (lagres med property_id=NULL):")
        for nm in sorted(unmatched_names)[:30]:
            log.info("  - %s", nm)
        if len(unmatched_names) > 30:
            log.info("  ... og %d til", len(unmatched_names) - 30)

    return enriched


def upsert_lonn(db: Session, records: list[dict], dry_run: bool) -> int:
    """Upsert lønn-rader til salary_costs. Returnerer antall upsertede rader."""
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    for rec in records:
        params = {
            "id": str(uuid.uuid4()),
            "property_id": rec["property_id"],
            "year": rec["year"],
            "faste": float(rec["belop"]),   # total lagres i faste_stillinger
            "vikarer": 0.0,
            "aga": 0.0,
            "inst_name": rec["institution_name"],
            "batch_id": BATCH_ID,
            "imported_at": now,
            "data_source": DATA_SOURCE,
            "is_partial_year": rec["is_partial_year"],
        }

        if dry_run:
            count += 1
            continue

        if rec["property_id"]:
            db.execute(text("""
                INSERT INTO salary_costs
                    (salary_cost_id, property_id, year,
                     faste_stillinger, vikarer, arbeidsgiveravgift,
                     institution_name_raw, import_batch_id, imported_at,
                     data_source, is_partial_year)
                VALUES
                    (:id, :property_id, :year,
                     :faste, :vikarer, :aga,
                     :inst_name, :batch_id, :imported_at,
                     :data_source, :is_partial_year)
                ON CONFLICT (property_id, year) DO UPDATE
                  SET faste_stillinger    = EXCLUDED.faste_stillinger,
                      vikarer             = EXCLUDED.vikarer,
                      arbeidsgiveravgift  = EXCLUDED.arbeidsgiveravgift,
                      institution_name_raw = EXCLUDED.institution_name_raw,
                      import_batch_id     = EXCLUDED.import_batch_id,
                      imported_at         = EXCLUDED.imported_at,
                      data_source         = EXCLUDED.data_source,
                      is_partial_year     = EXCLUDED.is_partial_year
            """), params)
        else:
            # Lagre umatchede med property_id=NULL (for revisjonsspor)
            db.execute(text("""
                INSERT INTO salary_costs
                    (salary_cost_id, property_id, year,
                     faste_stillinger, vikarer, arbeidsgiveravgift,
                     institution_name_raw, import_batch_id, imported_at,
                     data_source, is_partial_year)
                VALUES
                    (:id, NULL, :year,
                     :faste, :vikarer, :aga,
                     :inst_name, :batch_id, :imported_at,
                     :data_source, :is_partial_year)
            """), params)
        count += 1

    return count


# ── Del 2: Innkjøpskategorier ─────────────────────────────────────────────────

def parse_pivot_sheet(xl: pd.ExcelFile, sheet_name: str, kategori: str, ar: int) -> list[dict]:
    """
    Parser en fane med regional pivot-struktur.

    Strukturen er splittet over to header-rader:
        Rad N:   "Bufetat" | "Bufdir" | "Totalsum"   (org-nivå)
        Rad N+1: "Radetiketter" | "Region X" | "Region Y" ...  (region-kolonner)
        Rad N+2+: datarader

    Strategi: finn rad med "Radetiketter" – den er kolonneheaderen.
    Kombiner med raden over for å finne Bufdir- og Totalsum-kolonner.
    """
    df = xl.parse(sheet_name, header=None, dtype=object)

    # Finn rad med "Radetiketter" (alltid første kolonne i region-header)
    region_header_idx = None
    for i, row in df.iterrows():
        first = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ""
        if first == "radetiketter":
            region_header_idx = i
            break

    if region_header_idx is None:
        log.warning("%s: fant ikke 'Radetiketter'-rad", sheet_name)
        return []

    # Rad over "Radetiketter" inneholder "Bufetat" (org), "Bufdir", "Totalsum"
    upper_row = df.iloc[region_header_idx - 1] if region_header_idx > 0 else None
    region_row = df.iloc[region_header_idx]

    # Bygg kolonne-kart: col_idx → kolonnenavn
    # Prioriter region_row; for Totalsum/Bufdir fall tilbake til upper_row
    col_map: dict[int, str] = {}
    for col_idx, val in enumerate(region_row):
        if pd.notna(val):
            s = str(val).strip()
            if s and s.lower() not in ("radetiketter", "nan"):
                col_map[col_idx] = s

    # Hent Totalsum og Bufdir fra raden over (de er bare der)
    if upper_row is not None:
        for col_idx, val in enumerate(upper_row):
            if pd.notna(val):
                s = str(val).strip()
                if s.lower() in ("totalsum", "bufdir") and col_idx not in col_map:
                    col_map[col_idx] = s

    # Finn Totalsum-kolonne (siste numeriske kolonne)
    totalsum_col = None
    for col_idx, name in col_map.items():
        if name.lower() == "totalsum":
            totalsum_col = col_idx
            break

    records: list[dict] = []

    for i in range(region_header_idx + 1, len(df)):
        row = df.iloc[i]
        underkategori_raw = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""

        if not underkategori_raw or underkategori_raw.lower() in ("totalsum", "nan", ""):
            continue

        # Nasjonal total
        if totalsum_col is not None:
            belop = _safe_decimal(row.iloc[totalsum_col])
            if belop != 0:
                records.append({
                    "ar": ar,
                    "kategori": kategori,
                    "underkategori": underkategori_raw,
                    "region": None,
                    "belop": belop,
                    "kilde_fane": sheet_name,
                })

        # Per region/enhet
        for col_idx, col_name in col_map.items():
            if col_name.lower() == "totalsum":
                continue
            belop = _safe_decimal(row.iloc[col_idx])
            if belop != 0:
                records.append({
                    "ar": ar,
                    "kategori": kategori,
                    "underkategori": underkategori_raw,
                    "region": col_name,
                    "belop": belop,
                    "kilde_fane": sheet_name,
                })

    log.info("%s: parsede %d rader", sheet_name, len(records))
    return records


def parse_list_sheet(xl: pd.ExcelFile, sheet_name: str, kategori: str, ar: int) -> list[dict]:
    """
    Parser en fane med liste-struktur:
        Metadata i rad 0–5, header på rad 6 (Radetiketter | Kontantbeløp)
    """
    df = xl.parse(sheet_name, header=None, dtype=object)

    # Finn header-rad: leter etter rad med "Radetiketter" eller "Kontantbeløp"
    header_row_idx = None
    for i, row in df.iterrows():
        row_vals = [str(v).strip().lower() for v in row if pd.notna(v)]
        if any("radetiketter" in v or "kontantbeløp" in v for v in row_vals):
            header_row_idx = i
            break

    if header_row_idx is None:
        log.warning("%s: fant ikke header-rad", sheet_name)
        return []

    # Kolonne-indekser
    header_row = df.iloc[header_row_idx]
    name_col = 0
    amount_col = 1
    for ci, val in enumerate(header_row):
        if pd.notna(val):
            low = str(val).strip().lower()
            if "kontantbeløp" in low or "beløp" in low:
                amount_col = ci
            elif "radetiketter" in low or "navn" in low:
                name_col = ci

    records: list[dict] = []
    for i in range(header_row_idx + 1, len(df)):
        row = df.iloc[i]
        underkategori_raw = str(row.iloc[name_col]).strip() if pd.notna(row.iloc[name_col]) else ""
        if not underkategori_raw or underkategori_raw.lower() in ("totalsum", "nan", ""):
            continue
        belop = _safe_decimal(row.iloc[amount_col])
        if belop == 0:
            continue
        records.append({
            "ar": ar,
            "kategori": kategori,
            "underkategori": underkategori_raw,
            "region": None,
            "belop": belop,
            "kilde_fane": sheet_name,
        })

    log.info("%s: parsede %d rader", sheet_name, len(records))
    return records


def upsert_innkjop(db: Session, records: list[dict], dry_run: bool) -> int:
    """Upsert innkjøp-rader til innkjop_nasjonal_summary."""
    now = datetime.datetime.now(datetime.timezone.utc)
    count = 0

    for rec in records:
        params = {
            "id": str(uuid.uuid4()),
            "ar": rec["ar"],
            "kategori": rec["kategori"],
            "underkategori": rec.get("underkategori"),
            "region": rec.get("region"),
            "belop": float(rec["belop"]),
            "kilde_fane": rec.get("kilde_fane"),
            "batch_id": BATCH_ID,
            "imported_at": now,
        }
        if dry_run:
            count += 1
            continue

        db.execute(text("""
            INSERT INTO innkjop_nasjonal_summary
                (id, ar, kategori, underkategori, region, belop,
                 kilde_fane, import_batch_id, imported_at)
            VALUES
                (:id, :ar, :kategori, :underkategori, :region, :belop,
                 :kilde_fane, :batch_id, :imported_at)
            ON CONFLICT (ar, kategori, underkategori, region) DO UPDATE
              SET belop           = EXCLUDED.belop,
                  kilde_fane      = EXCLUDED.kilde_fane,
                  import_batch_id = EXCLUDED.import_batch_id,
                  imported_at     = EXCLUDED.imported_at
        """), params)
        count += 1

    return count


# ── Verifisering ──────────────────────────────────────────────────────────────

def verify(db: Session) -> None:
    """Kjør enkle kontrollspørringer etter import."""
    log.info("\n── Verifikasjon ──────────────────────────────────────")

    r = db.execute(text("""
        SELECT COUNT(*), SUM(faste_stillinger)
        FROM salary_costs
        WHERE data_source = :src
    """), {"src": DATA_SOURCE}).fetchone()
    log.info("salary_costs: %d rader, sum lønn = %.0f kr", r[0] or 0, float(r[1] or 0))

    r2 = db.execute(text("""
        SELECT year, COUNT(*), SUM(faste_stillinger)
        FROM salary_costs
        WHERE data_source = :src
        GROUP BY year ORDER BY year
    """), {"src": DATA_SOURCE}).fetchall()
    for row in r2:
        partial = " (delår)" if row[0] == PARTIAL_YEAR else ""
        log.info("  %d%s: %d rader, %.0f kr", row[0], partial, row[1], float(row[2] or 0))

    r3 = db.execute(text("""
        SELECT COUNT(*), SUM(belop)
        FROM innkjop_nasjonal_summary
        WHERE import_batch_id = :batch
    """), {"batch": BATCH_ID}).fetchone()
    log.info("innkjop_nasjonal_summary: %d rader, total = %.0f kr", r3[0] or 0, float(r3[1] or 0))

    r4 = db.execute(text("""
        SELECT kategori, SUM(belop) AS sum
        FROM innkjop_nasjonal_summary
        WHERE import_batch_id = :batch AND region IS NULL
        GROUP BY kategori ORDER BY sum DESC
    """), {"batch": BATCH_ID}).fetchall()
    log.info("Nasjonal sum per kategori:")
    for row in r4:
        log.info("  %-40s  %.0f kr", row[0], float(row[1] or 0))


# ── Hovedprogram ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Import Innkjøpsanalyse Excel til BEFS")
    parser.add_argument("fil", help="Sti til Excel-filen (.xlsx)")
    parser.add_argument("--dry-run", action="store_true", help="Parse men ikke skriv til DB")
    parser.add_argument("--only-lonn",    action="store_true", help="Importer kun lønnsdata")
    parser.add_argument("--only-innkjop", action="store_true", help="Importer kun innkjøpskategorier")
    parser.add_argument("--ar", type=int, default=2024, help="Regnskapsår for innkjøpskategoriene (default 2024)")
    args = parser.parse_args()

    excel_path = Path(args.fil)
    if not excel_path.exists():
        log.error("Filen finnes ikke: %s", excel_path)
        sys.exit(1)

    # DATABASE_URL fra miljø eller backend/.env
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not db_url:
        log.error("DATABASE_URL ikke satt. Sett miljøvariabelen eller legg i backend/.env")
        sys.exit(1)

    # Sync engine (script kjøres utenfor async-kontekst)
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url, echo=False)

    log.info("Åpner %s", excel_path.name)
    xl = pd.ExcelFile(excel_path, engine="openpyxl")
    log.info("Faner: %s", xl.sheet_names)

    do_lonn    = not args.only_innkjop
    do_innkjop = not args.only_lonn

    with Session(engine) as db:

        # ── 1. Lønnsdata ───────────────────────────────────────────────────
        if do_lonn:
            log.info("\n── Del 1: Lønnsutgifter ──────────────────────────────")
            lonn_records = parse_lonn_sheet(xl)
            lonn_enriched = match_properties(db, lonn_records)

            if args.dry_run:
                log.info("DRY-RUN: ville upsertert %d lønn-rader", len(lonn_enriched))
                matched = sum(1 for r in lonn_enriched if r["property_id"])
                log.info("  Matchet property_id: %d / %d", matched, len(lonn_enriched))
            else:
                n = upsert_lonn(db, lonn_enriched, dry_run=False)
                db.commit()
                log.info("Upserterte %d lønn-rader til salary_costs", n)

        # ── 2. Innkjøpskategorier ──────────────────────────────────────────
        if do_innkjop:
            log.info("\n── Del 2: Innkjøpskategorier ─────────────────────────")
            all_innkjop: list[dict] = []

            for sheet_name, kategori in PIVOT_SHEETS.items():
                if sheet_name in xl.sheet_names:
                    all_innkjop.extend(parse_pivot_sheet(xl, sheet_name, kategori, args.ar))
                else:
                    log.warning("Fane '%s' ikke funnet i filen", sheet_name)

            for sheet_name, kategori in LIST_SHEETS.items():
                if sheet_name in xl.sheet_names:
                    all_innkjop.extend(parse_list_sheet(xl, sheet_name, kategori, args.ar))
                else:
                    log.warning("Fane '%s' ikke funnet i filen", sheet_name)

            total_sum = sum(r["belop"] for r in all_innkjop if r["region"] is None)
            log.info("Total innkjøp (nasjonale summer): %.0f kr", float(total_sum))

            if args.dry_run:
                log.info("DRY-RUN: ville upsertert %d innkjøp-rader", len(all_innkjop))
            else:
                n = upsert_innkjop(db, all_innkjop, dry_run=False)
                db.commit()
                log.info("Upserterte %d innkjøp-rader til innkjop_nasjonal_summary", n)

        # ── 3. Verifikasjon ────────────────────────────────────────────────
        if not args.dry_run:
            verify(db)

    log.info("\nFerdig!")


if __name__ == "__main__":
    main()
