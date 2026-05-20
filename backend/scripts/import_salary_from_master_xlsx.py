#!/usr/bin/env python3
"""
Importer lønn fra Master_enheter (kolonner Lønn_YYYY_INNJKOP) → salary_costs.

Total per år legges i faste_stillinger (vikarer/AGA = 0). Kobling Dim1 → property
via TRIM(unit_id_erp) eller TRIM(koststed_kode).

Krever: BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1 for skriving.

  railway run -- bash -c 'cd backend && BEFS_ALLOW_PROD_WRITE=1 python3 scripts/import_salary_from_master_xlsx.py \\
    --master /path/Master_enheter_register.xlsx'
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

import openpyxl
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db.base  # noqa: F401
from app.db.session import SessionLocal

BATCH_ID = "master_enheter_innkjop_xlsx"
TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
YEAR_2026 = 2026


def _writes_ok() -> bool:
    return os.environ.get("BEFS_DATABASE_TIER", "").lower() == "staging" or (
        os.environ.get("BEFS_ALLOW_PROD_WRITE", "").strip() == "1"
    )


def _norm_dim(v: Any) -> str | None:
    if v is None or v == "":
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        return str(int(float(s)))
    except (TypeError, ValueError):
        return None


def _f(x: Any) -> float | None:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_master_salary_rows(path: Path) -> list[dict[str, Any]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Master_enheter"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return []
    header = [str(h) if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(header) if h}
    ycols: list[int] = []
    for h in header:
        m = re.match(r"^Lønn_(\d{4})_INNJKOP$", h)
        if m:
            ycols.append(int(m.group(1)))
    out: list[dict[str, Any]] = []
    for r in rows[1:]:
        if not r or "Dim1" not in idx:
            continue
        dim = _norm_dim(r[idx["Dim1"]])
        if not dim:
            continue
        name = ""
        if "Enhet_navn_AGRESSO" in idx and r[idx["Enhet_navn_AGRESSO"]]:
            name = str(r[idx["Enhet_navn_AGRESSO"]]).strip()
        rec: dict[str, Any] = {"dim1": dim, "navn": name, "years": {}}
        for y in ycols:
            col = f"Lønn_{y}_INNJKOP"
            if col in idx:
                v = _f(r[idx[col]])
                if v is not None:
                    rec["years"][y] = v
        if rec["years"]:
            out.append(rec)
    return out


def _fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _find_property_by_name(
    navn: str,
    name_pairs: list[tuple[str, str]],
    used: set[str],
    cutoff: float = 0.88,
) -> Optional[str]:
    if not navn or not navn.strip():
        return None
    best_id: Optional[str] = None
    best_sc = 0.0
    nl = navn.lower().strip()
    for pid, pname in name_pairs:
        if pid in used or not pname:
            continue
        pl = pname.lower().strip()
        if nl == pl:
            return pid
        sc = _fuzzy_ratio(navn, pname)
        if len(pl) >= 6 and len(nl) >= 6 and (nl in pl or pl in nl):
            sc = max(sc, 0.9)
        if sc > best_sc:
            best_sc = sc
            best_id = pid
    if best_id is not None and best_sc >= cutoff:
        return best_id
    return None


async def map_dim_to_property(db) -> dict[str, str]:
    sql = text(
        """
        SELECT property_id::text, unit_id_erp, koststed_kode
        FROM properties
        WHERE (unit_id_erp IS NOT NULL AND TRIM(unit_id_erp) <> '')
           OR (koststed_kode IS NOT NULL AND TRIM(koststed_kode) <> '')
        """
    )
    result = await db.execute(sql)
    by_dim: dict[str, str] = {}
    for row in result.mappings().all():
        pid = row["property_id"]
        for key in ("unit_id_erp", "koststed_kode"):
            d = _norm_dim(row[key])
            if d and d not in by_dim:
                by_dim[d] = pid
    return by_dim


async def fetch_property_names(db) -> list[tuple[str, str]]:
    r = await db.execute(
        text(
            """
            SELECT property_id::text, COALESCE(NULLIF(TRIM(name), ''), '') AS n
            FROM properties
            """
        )
    )
    return [(str(row[0]), str(row[1])) for row in r.fetchall() if row[1]]


UPSERT = text(
    """
    INSERT INTO salary_costs (
        salary_cost_id, property_id, year,
        faste_stillinger, vikarer, arbeidsgiveravgift,
        institution_name_raw, import_batch_id, imported_at,
        data_source, is_partial_year
    )
    VALUES (
        :id, CAST(:pid AS uuid), :year,
        :faste, 0, 0,
        :name_raw, :batch_id, now(),
        :data_source, :partial
    )
    ON CONFLICT (property_id, year) DO UPDATE SET
        faste_stillinger = EXCLUDED.faste_stillinger,
        vikarer = EXCLUDED.vikarer,
        arbeidsgiveravgift = EXCLUDED.arbeidsgiveravgift,
        institution_name_raw = EXCLUDED.institution_name_raw,
        import_batch_id = EXCLUDED.import_batch_id,
        imported_at = EXCLUDED.imported_at,
        data_source = EXCLUDED.data_source,
        is_partial_year = EXCLUDED.is_partial_year
    """
)


async def run(master: Path, dry_run: bool) -> None:
    master_rows = load_master_salary_rows(master)
    print(f"Master-rader med lønntall: {len(master_rows)}")

    async with SessionLocal() as db:
        dim_to_pid = await map_dim_to_property(db)
        name_pairs = await fetch_property_names(db)

    matched_dim = 0
    matched_name = 0
    skipped_no_prop = 0
    pending: list[tuple[str, int, float, str, bool]] = []
    used_name_match: set[str] = set()

    for rec in master_rows:
        navn = rec["navn"] or rec["dim1"]
        pid = dim_to_pid.get(rec["dim1"])
        if not pid:
            pid = _find_property_by_name(navn, name_pairs, used_name_match, cutoff=0.88)
            if pid:
                matched_name += 1
                used_name_match.add(pid)
            else:
                skipped_no_prop += 1
                continue
        else:
            matched_dim += 1
        for year, amount in rec["years"].items():
            if year in TARGET_YEARS:
                partial = False
            elif year == YEAR_2026:
                partial = True
            else:
                continue
            pending.append((pid, year, amount, navn, partial))

    merged: dict[tuple[str, int], list[Any]] = {}
    for pid, year, amount, navn, partial in pending:
        k = (pid, year)
        if k not in merged:
            merged[k] = [0.0, navn, partial]
        merged[k][0] += float(amount)
        merged[k][1] = navn

    pending_final = [
        (pid, year, vals[0], vals[1], vals[2]) for (pid, year), vals in merged.items()
    ]

    print(
        f"Matchet Dim1→eiendom: {matched_dim}  via navn: {matched_name}  "
        f"Uten eiendom: {skipped_no_prop}"
    )
    print(f"Planlagte upserts (aggregert per eiendom×år): {len(pending_final)}")

    if dry_run:
        print("[DRY RUN] Ingen skriving.")
        return

    if not _writes_ok():
        raise SystemExit(
            "Skriving nektet — sett BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1"
        )

    async with SessionLocal() as db:
        for pid, year, amount, navn, partial in pending_final:
            await db.execute(
                UPSERT,
                {
                    "id": str(uuid.uuid4()),
                    "pid": pid,
                    "year": year,
                    "faste": round(amount, 2),
                    "name_raw": navn[:500],
                    "batch_id": BATCH_ID,
                    "data_source": "master_enheter_innkjop",
                    "partial": partial,
                },
            )
        await db.commit()
    print(f"OK — skrev {len(pending_final)} rader.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Importer lønn fra Master_enheter xlsx")
    ap.add_argument("--master", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(args.master, args.dry_run))


if __name__ == "__main__":
    main()
