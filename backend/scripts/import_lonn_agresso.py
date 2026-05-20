"""
Import av lønnsdata fra Agresso pivot-CSV til salary_costs-tabellen.

Kjør:
    cd backend
    DATABASE_URL=... python scripts/import_lonn_agresso.py [--dry-run]

Kilde: «Innkjøpsanalyse 2026 lønnsutgifter(Lønnsutgifter).csv»
Format: Pivot — enhet × år, gruppert under lønnskategori og region.

Matching-logikk:
    1. Oppslag på property.name (exact, case-insensitive)
    2. Oppslag på property.institution_name_raw (tidligere import)
    3. Fuzzy-match med difflib (score ≥ 0.75)
    4. Umatched poster lagres med property_id=NULL for manuell gjennomgang
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
import chardet
from datetime import datetime
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

# ── Bootstrap sys.path ───────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL mangler")
    sys.exit(1)

DRY_RUN = "--dry-run" in sys.argv

# ── CSV-fil ───────────────────────────────────────────────────────────────────
_KANDIDATER = [
    Path(__file__).parent.parent.parent / "finans" / "Innkjøpsanalyse 2026 lønnsutgifter(Lønnsutgifter).csv",
    Path.home() / "Downloads" / "Innkjøpsanalyse 2026 lønnsutgifter(Lønnsutgifter).csv",
]
CSV_FILE = next((p for p in _KANDIDATER if p.exists()), _KANDIDATER[-1])

# ── Lønnskategorier (rekkefølge som i CSV-seksjonene) ─────────────────────────
MAIN_CATS = [
    "Faste stillinger",
    "Lønn vikarer",
    "Arbeidsgiveravgift",
    "Turnustillegg",
    "Pensjonspremie (virksomheter som betaler pensjonspremie)",
    "Midlertidige stillinger (hel- og deltid)",
    "Turnustillegg, vikarer",
    "Overtid faste stillinger",
    "Overtid midlertidige ansatte og vikarer",
    "AGA på arbeidsgivertilskudd til SPK",
]

# CSV-kategori → DB-kolonne
CAT_TO_COL: dict[str, str] = {
    "Faste stillinger":                                                  "faste_stillinger",
    "Lønn vikarer":                                                      "vikarer",
    "Arbeidsgiveravgift":                                                "arbeidsgiveravgift",
    "Turnustillegg":                                                     "turnustillegg",
    "Pensjonspremie (virksomheter som betaler pensjonspremie)":          "pensjonspremie",
    "Midlertidige stillinger (hel- og deltid)":                         "midlertidige",
    "Turnustillegg, vikarer":                                            "turnustillegg_vik",
    "Overtid faste stillinger":                                          "overtid_faste",
    "Overtid midlertidige ansatte og vikarer":                           "overtid_midl",
    "AGA på arbeidsgivertilskudd til SPK":                               "aga_spk",
}

REGIONS = {"Region Midt-Norge", "Region Nord", "Region Sør", "Region Vest", "Region Øst"}
YEARS   = [2020, 2021, 2022, 2023, 2024, 2025]

BATCH_ID = f"lonn_agresso_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


# ── CSV-parser ────────────────────────────────────────────────────────────────
def parse_amount(s: str) -> Optional[Decimal]:
    s = s.strip()
    if not s or s == "-":
        return None
    neg = s.lstrip().startswith("-")
    cleaned = s.replace("-", "").replace(" ", "").replace(",", ".")
    try:
        v = Decimal(cleaned)
        return -v if neg else v
    except Exception:
        return None


def parse_csv(path: Path) -> list[dict]:
    """
    Returnerer liste av:
      { cat, region, enhet, 2020: Decimal|None, ..., 2025: Decimal|None }
    """
    with open(path, "rb") as f:
        enc = chardet.detect(f.read(20000))["encoding"] or "latin-1"

    with open(path, encoding=enc, errors="replace") as f:
        raw_lines = f.readlines()

    rows: list[dict] = []
    current_cat: Optional[str] = None
    current_region: Optional[str] = None

    for line in raw_lines:
        cols = line.rstrip("\n").split(";")
        label = cols[0].strip()
        if not label:
            continue

        if label in MAIN_CATS:
            current_cat = label
            current_region = None
            continue

        if label in ("Bufetat", "Bufdir"):
            continue

        if label in REGIONS:
            current_region = label
            continue

        # Data-rad
        amounts = {yr: parse_amount(cols[1 + i]) if (1 + i) < len(cols) else None
                   for i, yr in enumerate(YEARS)}
        has_any = any(v is not None for v in amounts.values())

        if current_cat and current_region and has_any:
            rows.append({
                "cat": current_cat,
                "region": current_region,
                "enhet": label,
                **amounts,
            })

    return rows


# ── Fuzzy matching ─────────────────────────────────────────────────────────────
def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


async def build_property_index(session: AsyncSession) -> dict[str, str]:
    """Returnerer {navn_lower: property_id_str}"""
    result = await session.execute(text(
        "SELECT property_id::text, name FROM properties WHERE name IS NOT NULL"
    ))
    index: dict[str, str] = {}
    for row in result.fetchall():
        pid, name = row
        if name:
            index[name.strip().lower()] = pid
    return index


def match_property(enhet: str, index: dict[str, str], threshold: float = 0.75) -> Optional[str]:
    key = enhet.strip().lower()
    if key in index:
        return index[key]
    # Fuzzy
    best_score = 0.0
    best_pid: Optional[str] = None
    for name, pid in index.items():
        sc = similarity(key, name)
        if sc > best_score:
            best_score = sc
            best_pid = pid
    if best_score >= threshold:
        return best_pid
    return None


# ── Aggregering per (enhet, år) på tvers av kategorier ───────────────────────
def aggregate_rows(csv_rows: list[dict]) -> dict[tuple[str, str, int], dict[str, Decimal]]:
    """
    Slår sammen alle kategorier per (enhet, region, år).
    Returnerer { (enhet, region, år): { col: Decimal } }
    """
    agg: dict[tuple[str, str, int], dict[str, Decimal]] = {}
    for row in csv_rows:
        enhet  = row["enhet"]
        region = row["region"]
        col    = CAT_TO_COL.get(row["cat"])
        if not col:
            continue
        for yr in YEARS:
            amt = row.get(yr)
            if amt is None:
                continue
            key = (enhet, region, yr)
            if key not in agg:
                agg[key] = {}
            agg[key][col] = agg[key].get(col, Decimal(0)) + amt
    return agg


# ── Upsert til DB ─────────────────────────────────────────────────────────────
async def upsert_salary(session: AsyncSession, agg: dict, prop_index: dict) -> dict:
    stats = {"matched": 0, "unmatched": 0, "skipped": 0, "upserted": 0}

    for (enhet, _region, yr), cols in agg.items():
        pid = match_property(enhet, prop_index)

        if pid is None:
            stats["unmatched"] += 1
            # Lagre uansett med property_id=NULL for sporbarhet
            pid_val = "NULL"
        else:
            stats["matched"] += 1
            pid_val = f"'{pid}'"

        cols_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols)
        cols_insert = ", ".join(cols.keys())
        placeholders = ", ".join(f":{c}" for c in cols)

        bind = {c: v for c, v in cols.items()}
        bind["yr"] = yr
        bind["enhet"] = enhet
        bind["batch"] = BATCH_ID

        if DRY_RUN:
            stats["upserted"] += 1
            continue

        await session.execute(text(f"""
            INSERT INTO salary_costs
                (salary_cost_id, property_id, year, {cols_insert},
                 institution_name_raw, import_batch_id, imported_at)
            VALUES
                (gen_random_uuid(), {pid_val}, :yr, {placeholders},
                 :enhet, :batch, NOW())
            ON CONFLICT (property_id, year)
            DO UPDATE SET
                {cols_sql},
                institution_name_raw = EXCLUDED.institution_name_raw,
                import_batch_id      = EXCLUDED.import_batch_id,
                imported_at          = EXCLUDED.imported_at
        """), bind)
        stats["upserted"] += 1

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    if not CSV_FILE.exists():
        print(f"❌ CSV ikke funnet: {CSV_FILE}")
        sys.exit(1)

    print(f"📂 CSV: {CSV_FILE}")
    print(f"🔁 Batch: {BATCH_ID}")
    print(f"{'🔍 DRY-RUN' if DRY_RUN else '✍️  SKRIVER TIL DB'}\n")

    csv_rows = parse_csv(CSV_FILE)
    print(f"   Leste {len(csv_rows)} CSV-rader")

    agg = aggregate_rows(csv_rows)
    print(f"   Aggregert til {len(agg)} (enhet, år)-kombinasjoner")

    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        prop_index = await build_property_index(session)
        print(f"   Fant {len(prop_index)} eiendommer i DB")

        stats = await upsert_salary(session, agg, prop_index)
        if not DRY_RUN:
            await session.commit()

    await engine.dispose()

    print(f"\n✅ Ferdig:")
    print(f"   Matchet:    {stats['matched']}")
    print(f"   Umatched:   {stats['unmatched']} (lagret med property_id=NULL)")
    print(f"   Upserted:   {stats['upserted']}")


if __name__ == "__main__":
    asyncio.run(main())
