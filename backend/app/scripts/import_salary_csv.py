"""
Import lønnsdataCSV (Innkjøpsanalyse 2026 lønnsutgifter) → salary_costs-tabellen.

CSV-struktur (Windows-1252):
    Radetiketter ; 2020 ; 2021 ; 2022 ; 2023 ; 2024 ; 2025 ; 2026 ; Totalsum

22 seksjoner (lønnkomponenter):
    Faste stillinger → faste_stillinger
    Lønn vikarer     → vikarer
    Alt annet        → arbeidsgiveravgift (AGA, overtid, tillegg, pensjon, ...)

Hvert lønnkomponent har full hierarki:
    Bufetat → Region X → Institusjon

Scriptet:
    1. Parser CSV og akkumulerer per (institusjonnavn, år, kolonne)
    2. Matcher institusjonsnavn → property_id (Dim1+master først, deretter fuzzy på navn)
    3. Upsert til salary_costs (år 2020–2025; 2026 ignoreres = delårsdata)

Flagg:
    --replace              ON CONFLICT erstatter beløp (ikke akkumulerer med eksisterende)
    --master-xlsx PATH     Master_enheter: Dim1 → navn for sikrere matching
    --delete-batch-before  Slett eksisterende rader med denne import_batch_id for 2020–2025 før insert

Skriving (inkl. --delete-batch-before) krever BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1.

Kjøring:
    railway run -- bash -c 'cd backend && python -m app.scripts.import_salary_csv /sti/csv --replace --dry-run'
"""

import asyncio
import argparse
import os
import sys
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# ─── Konstantar ──────────────────────────────────────────────────────────────

IMPORT_BATCH_ID = "csv_import_lonnsdata_2026"
TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]  # 2026 = delårsdata, hoppes over


def _writes_ok() -> bool:
    return os.environ.get("BEFS_DATABASE_TIER", "").lower() == "staging" or (
        os.environ.get("BEFS_ALLOW_PROD_WRITE", "").strip() == "1"
    )


def _norm_dim(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return str(int(float(s)))
    except (TypeError, ValueError):
        return None


def load_master_dim_to_official_name(master_path: str) -> Dict[str, str]:
    """Dim1 (str) → Enhet_navn_AGRESSO fra arket Master_enheter."""
    import openpyxl

    path = Path(master_path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Master_enheter"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return {}
    header = [str(h) if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(header) if h}
    out: Dict[str, str] = {}
    for r in rows[1:]:
        if not r or "Dim1" not in idx or "Enhet_navn_AGRESSO" not in idx:
            continue
        nk = _norm_dim(r[idx["Dim1"]])
        if not nk:
            continue
        raw = r[idx["Enhet_navn_AGRESSO"]]
        name = str(raw).strip() if raw is not None else ""
        if name:
            out[nk] = name
    return out


# Seksjons-linjenummer (0-basert) i CSV (etter metadata-header):
# Detektert automatisk basert på kjente seksjonsnavnmønstre
SALARY_COMPONENT_KEYWORDS = [
    "faste stillinger",
    "lønn vikarer",
    "arbeidsgiveravgift",
    "turnustillegg",
    "pensjonspremie",
    "midlertidige stillinger",
    "overtid",
    "naturalytelser",
    "feriepenger",
    "bonus",
    "tillegg",
    "honorar",
    "ventelønn",
    "mst-tillegg",
    "gaver",
    "reisekostnad",
    "andre offentlige",
]

# Navn som er region/subtotal-noder — SKIP
SKIP_NAMES = frozenset({
    "", "Bufetat", "Bufdir",
    "Region Midt-Norge", "Region Nord", "Region Sør",
    "Region Vest", "Region Øst", "Region Øst Behandling",
})

def is_skip(name: str) -> bool:
    return (
        name in SKIP_NAMES
        or name.startswith("Region ")
        or name.startswith("Bufdir")
        or name == "Bufetat"
    )

def section_to_col(section_name: str) -> str:
    lower = section_name.lower()
    if lower == "faste stillinger":
        return "faste_stillinger"
    elif lower in ("lønn vikarer", "vikarer"):
        return "vikarer"
    else:
        return "arbeidsgiveravgift"  # catch-all

def parse_amount(s: str) -> float:
    """Konverter norsk tallformat '  5 739 235' → 5739235.0"""
    s = s.strip().replace("\xa0", "").replace("\u00a0", "").replace(" ", "")
    if not s or s in ("-", ""):
        return 0.0
    # Håndter negative: '-   22 990' allerede strippet til '-22990'
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return 0.0


# ─── CSV-parsing ─────────────────────────────────────────────────────────────

def parse_csv(filepath: str) -> Dict[str, Dict[int, Dict[str, float]]]:
    """
    Returnerer: institusjonnavn → år → kolonne → beløp
    """
    with open(filepath, encoding="windows-1252") as f:
        lines = f.readlines()

    # Finn header-rad (inneholder 'Radetiketter')
    header_idx = None
    for i, line in enumerate(lines):
        if "Radetiketter" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Fant ikke Radetiketter-header i CSV")

    data_lines = lines[header_idx + 1:]

    # ── Steg 1: Finn seksjons-grenser ──────────────────────────────────────

    def is_empty_vals(parts: list[str]) -> bool:
        vals = [p.strip().replace("\xa0", "").replace(" ", "") for p in parts[1:8]]
        return all(not v or not v.replace("-", "") for v in vals)

    # Finne faktiske seksjonshoveder (lønnkomponenter)
    section_boundaries: List[Tuple[int, str]] = []  # (abs_line_idx, section_name)

    for i, line in enumerate(data_lines):
        parts = line.strip().split(";")
        name = parts[0].strip()
        if not name:
            continue
        if is_empty_vals(parts):
            name_lower = name.lower()
            if any(kw in name_lower for kw in SALARY_COMPONENT_KEYWORDS):
                section_boundaries.append((i, name))

    if not section_boundaries:
        raise ValueError("Ingen seksjoner funnet — sjekk CSV-format")

    print(f"Fant {len(section_boundaries)} lønnseksjoner:")
    for _, sname in section_boundaries:
        col = section_to_col(sname)
        print(f"  '{sname}' → {col}")

    # ── Steg 2: Parse institusjonsrader per seksjon ──────────────────────

    # data[name][year][col] += amount
    data: Dict[str, Dict[int, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"faste_stillinger": 0.0, "vikarer": 0.0, "arbeidsgiveravgift": 0.0})
    )

    boundaries_ext = section_boundaries + [(len(data_lines), "__end__")]

    for seg_idx, (start_i, sname) in enumerate(section_boundaries):
        end_i = boundaries_ext[seg_idx + 1][0]
        col = section_to_col(sname)

        for i in range(start_i + 1, end_i):
            parts = data_lines[i].strip().split(";")
            name = parts[0].strip()

            if not name or is_skip(name):
                continue

            vals_raw = parts[1:8]  # 2020, 2021, 2022, 2023, 2024, 2025, 2026
            amounts = [parse_amount(v) for v in vals_raw]

            # Hopp over rader uten data
            if not any(a != 0 for a in amounts):
                continue

            # Akkumuler år 2020–2025 (ignorér 2026 = delårsdata)
            for yr_idx, yr in enumerate(TARGET_YEARS):
                amt = amounts[yr_idx]
                if amt != 0:
                    data[name][yr][col] += amt

    return dict(data)


# ─── Name matching ──────────────────────────────────────────────────────────

def fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(
    csv_name: str,
    db_names: List[Tuple[str, str]],  # [(property_id, name), ...]
    cutoff: float = 0.75,
) -> Tuple[Optional[str], float]:
    """Returnerer (property_id, score) for beste treff, eller (None, 0)."""
    best_id, best_score = None, 0.0
    csv_lower = csv_name.lower().strip()

    for pid, pname in db_names:
        pname_lower = pname.lower().strip()

        # Eksakt treff
        if csv_lower == pname_lower:
            return pid, 1.0

        score = fuzzy_ratio(csv_lower, pname_lower)

        # Boost: sjekk om ett er substring av det andre
        # Krev minimum 6 tegn for å unngå falske treff på korte stedsnavn (Ra, Vik, Nes, ...)
        if len(pname_lower) >= 6 and len(csv_lower) >= 6:
            if csv_lower in pname_lower or pname_lower in csv_lower:
                score = max(score, 0.85)

        if score > best_score:
            best_score = score
            best_id = pid

    if best_score >= cutoff:
        return best_id, best_score
    return None, best_score


def match_csv_institution(
    csv_name: str,
    prop_rows: List[Tuple[str, str, Optional[str], Optional[str]]],
    master_dim_to_name: Optional[Dict[str, str]],
    cutoff: float,
) -> Tuple[Optional[str], float, str]:
    """
    Returnerer (property_id, score, metode) der metode er dim1_master, fuzzy eller none.
    """
    if master_dim_to_name:
        csv_lower = csv_name.lower().strip()
        best_id: Optional[str] = None
        best_sc = 0.0
        for pid, _pname, uerp, ks in prop_rows:
            dim = _norm_dim(uerp) or _norm_dim(ks)
            if not dim or dim not in master_dim_to_name:
                continue
            official = master_dim_to_name[dim].strip()
            if not official:
                continue
            off_l = official.lower().strip()
            if csv_lower == off_l:
                return pid, 1.0, "dim1_master"
            sc = fuzzy_ratio(csv_name, official)
            if len(off_l) >= 6 and len(csv_lower) >= 6:
                if csv_lower in off_l or off_l in csv_lower:
                    sc = max(sc, 0.9)
            if sc > best_sc:
                best_sc = sc
                best_id = pid
        if best_id is not None and best_sc >= 0.88:
            return best_id, best_sc, "dim1_master"

    name_pairs = [(pid, pname) for pid, pname, _u, _k in prop_rows if pname]
    fid, fsc = find_best_match(csv_name, name_pairs, cutoff=cutoff)
    if fid:
        return fid, fsc, "fuzzy"
    return None, 0.0, "none"


# ─── DB-operasjoner ─────────────────────────────────────────────────────────

async def fetch_property_names(db: AsyncSession) -> List[Tuple[str, str]]:
    """Henter [(property_id, name)] fra properties-tabellen."""
    rows = await fetch_property_rows(db)
    return [(pid, pname) for pid, pname, _u, _k in rows]


async def fetch_property_rows(
    db: AsyncSession,
) -> List[Tuple[str, str, Optional[str], Optional[str]]]:
    """property_id, name, unit_id_erp, koststed_kode"""
    result = await db.execute(
        text(
            """
            SELECT property_id::text, name, unit_id_erp, koststed_kode
            FROM properties
            WHERE name IS NOT NULL AND TRIM(name) <> ''
            ORDER BY name
            """
        )
    )
    return [
        (str(r[0]), str(r[1]), r[2], r[3])
        for r in result.fetchall()
    ]


async def delete_salary_batch_for_target_years(
    db: AsyncSession,
    batch_id: str,
    dry_run: bool,
) -> int:
    if dry_run:
        return 0
    total = 0
    for y in TARGET_YEARS:
        r = await db.execute(
            text(
                """
                DELETE FROM salary_costs
                WHERE import_batch_id = :b AND year = :y
                """
            ),
            {"b": batch_id, "y": y},
        )
        total += r.rowcount or 0
    return total


async def upsert_salary_costs(
    db: AsyncSession,
    property_id: str,
    year: int,
    faste: float,
    vikarer: float,
    aga: float,
    institution_name_raw: str,
    dry_run: bool = False,
    accumulate: bool = True,
    import_batch_id: Optional[str] = None,
) -> None:
    if dry_run:
        return

    batch_id = import_batch_id or IMPORT_BATCH_ID
    if accumulate:
        conflict_sql = """
        ON CONFLICT (property_id, year) DO UPDATE SET
            faste_stillinger = salary_costs.faste_stillinger + EXCLUDED.faste_stillinger,
            vikarer = salary_costs.vikarer + EXCLUDED.vikarer,
            arbeidsgiveravgift = salary_costs.arbeidsgiveravgift + EXCLUDED.arbeidsgiveravgift,
            import_batch_id = EXCLUDED.import_batch_id,
            imported_at = EXCLUDED.imported_at
        """
    else:
        conflict_sql = """
        ON CONFLICT (property_id, year) DO UPDATE SET
            faste_stillinger = EXCLUDED.faste_stillinger,
            vikarer = EXCLUDED.vikarer,
            arbeidsgiveravgift = EXCLUDED.arbeidsgiveravgift,
            import_batch_id = EXCLUDED.import_batch_id,
            imported_at = EXCLUDED.imported_at
        """

    await db.execute(
        text(
            f"""
        INSERT INTO salary_costs (
            salary_cost_id, property_id, year,
            faste_stillinger, vikarer, arbeidsgiveravgift,
            institution_name_raw, import_batch_id, imported_at
        )
        VALUES (
            :id, :pid, :year,
            :faste, :vikarer, :aga,
            :name_raw, :batch_id, now()
        )
        {conflict_sql}
    """
        ),
        {
            "id": str(uuid.uuid4()),
            "pid": property_id,
            "year": year,
            "faste": round(faste, 2),
            "vikarer": round(vikarer, 2),
            "aga": round(aga, 2),
            "name_raw": institution_name_raw[:500],
            "batch_id": batch_id,
        },
    )


# ─── Hovedlogikk ─────────────────────────────────────────────────────────────

async def run_import(
    filepath: str,
    dry_run: bool,
    cutoff: float,
    *,
    replace: bool,
    master_xlsx: Optional[str],
    delete_batch_before: bool,
    import_batch_id: str,
) -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"statement_cache_size": 0},  # Påkrevd for PgBouncer (Supabase)
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    master_map: Optional[Dict[str, str]] = None
    if master_xlsx:
        master_map = load_master_dim_to_official_name(master_xlsx)
        print(f"Master: {len(master_map)} Dim1→navn fra {master_xlsx}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Parser {filepath} ...")
    print(f"  Modus ON CONFLICT: {'erstatt' if replace else 'akkumuler'}")
    csv_data = parse_csv(filepath)
    print(f"Leste {len(csv_data)} unike institusjonsnavn fra CSV\n")

    async with async_session() as db:
        if delete_batch_before:
            if dry_run:
                print(f"[DRY RUN] ville slette salary_costs import_batch_id={import_batch_id} år {TARGET_YEARS}")
            else:
                if not _writes_ok():
                    raise SystemExit(
                        "delete-batch-before krever BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1"
                    )
                n_del = await delete_salary_batch_for_target_years(
                    db, import_batch_id, dry_run=False
                )
                await db.commit()
                print(f"Slettet {n_del} eksisterende rader (batch={import_batch_id}, år {TARGET_YEARS}).")

        prop_rows = await fetch_property_rows(db)
        db_names = [(pid, pname) for pid, pname, _u, _k in prop_rows]
        print(f"Hentet {len(db_names)} eiendommer fra DB\n")

        matched = 0
        unmatched = 0
        inserted = 0
        unmatched_names: List[str] = []
        dim1_hits = 0

        for csv_name, year_data in csv_data.items():
            property_id, score, metode = match_csv_institution(
                csv_name, prop_rows, master_map, cutoff=cutoff
            )

            if property_id is None:
                unmatched += 1
                unmatched_names.append(csv_name)
                continue

            matched += 1
            if metode == "dim1_master":
                dim1_hits += 1
            db_name = next((n for pid, n in db_names if pid == property_id), "?")
            if metode == "fuzzy" or (metode == "dim1_master" and score < 0.999):
                print(f"  {metode.upper()} {score:.2f}: '{csv_name}' → '{db_name}'")

            for year, cols in year_data.items():
                faste = cols["faste_stillinger"]
                vikarer = cols["vikarer"]
                aga = cols["arbeidsgiveravgift"]
                total = faste + vikarer + aga

                if total == 0:
                    continue

                await upsert_salary_costs(
                    db,
                    property_id,
                    year,
                    faste,
                    vikarer,
                    aga,
                    institution_name_raw=csv_name,
                    dry_run=dry_run,
                    accumulate=not replace,
                    import_batch_id=import_batch_id,
                )
                inserted += 1

        if not dry_run:
            if not _writes_ok():
                raise SystemExit(
                    "Import krever BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1"
                )
            await db.commit()

    # ─── Rapport ────────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"{'[DRY RUN] ' if dry_run else ''}IMPORT FERDIG")
    print(f"  Institusjoner i CSV:  {len(csv_data)}")
    print(f"  Matchet til eiendom:  {matched}")
    print(f"  Davon dim1_master:    {dim1_hits}")
    print(f"  Ikke matchet:         {unmatched}")
    print(f"  Rader upsert:         {inserted} (property_id × år-kombinasjoner)")

    if unmatched_names:
        print(f"\nUmatchede institusjonsnavn ({len(unmatched_names)}):")
        for n in sorted(unmatched_names):
            print(f"  - {n}")
    print(f"{'=' * 60}")

    await engine.dispose()


# ─── CLI-entry ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Importer lønnsdataCSV til salary_costs")
    parser.add_argument("filepath", help="Sti til CSV-fil (Windows-1252-kodet)")
    parser.add_argument("--dry-run", action="store_true", help="Parser og matcher uten å skrive til DB")
    parser.add_argument("--cutoff", type=float, default=0.75, help="Fuzzy match-terskel (default: 0.75)")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Erstatt beløp ved konflikt (ikke legg sammen med eksisterende)",
    )
    parser.add_argument(
        "--master-xlsx",
        type=str,
        default=None,
        help="Master_enheter_register.xlsx for Dim1-basert matching",
    )
    parser.add_argument(
        "--delete-batch-before",
        action="store_true",
        help=f"Slett eksisterende rader med import_batch_id (default {IMPORT_BATCH_ID}) for {TARGET_YEARS} før import",
    )
    parser.add_argument(
        "--import-batch-id",
        type=str,
        default=IMPORT_BATCH_ID,
        help="import_batch_id på innlagte rader (default: csv_import_lonnsdata_2026)",
    )
    args = parser.parse_args()

    asyncio.run(
        run_import(
            args.filepath,
            dry_run=args.dry_run,
            cutoff=args.cutoff,
            replace=args.replace,
            master_xlsx=args.master_xlsx,
            delete_batch_before=args.delete_batch_before,
            import_batch_id=args.import_batch_id,
        )
    )


if __name__ == "__main__":
    main()
