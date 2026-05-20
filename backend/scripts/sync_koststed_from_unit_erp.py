#!/usr/bin/env python3
"""
Sett properties.koststed_kode fra unit_id_erp (Dim1) med validering.

Moduser:
  master-only  — kun der TRIM(unit_id_erp) finnes som Dim1 i Master_enheter-register (xlsx)
  all-numeric  — alle eiendommer med rent numerisk unit_id_erp og tom/mangler koststed

Krever for faktisk UPDATE:
  BEFS_DATABASE_TIER=staging  ELLER  BEFS_ALLOW_PROD_WRITE=1 railway run -- bash -c 'cd backend && BEFS_DATABASE_TIER=staging python3 scripts/sync_koststed_from_unit_erp.py \\
    --master /path/Master_enheter_register.xlsx --mode master-only --dry-run --csv /tmp/koststed_sync.csv'
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from pathlib import Path
from typing import Any

import openpyxl
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db.base  # noqa: F401
from app.db.session import SessionLocal


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


def _load_master_dim1_set(path: Path) -> set[str]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Master_enheter"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return set()
    header = [str(h) if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(header) if h}
    out: set[str] = set()
    for r in rows[1:]:
        if not r or "Dim1" not in idx:
            continue
        nk = _norm_dim(r[idx["Dim1"]])
        if nk:
            out.add(nk)
    return out


def _writes_ok() -> bool:
    return os.environ.get("BEFS_DATABASE_TIER", "").lower() == "staging" or (
        os.environ.get("BEFS_ALLOW_PROD_WRITE", "").strip() == "1"
    )


PROPS_SQL = text(
    """
    SELECT
        property_id::text,
        COALESCE(NULLIF(TRIM(name), ''), NULLIF(TRIM(address), ''), '') AS visningsnavn,
        unit_id_erp,
        koststed_kode
    FROM properties
    WHERE unit_id_erp IS NOT NULL AND TRIM(unit_id_erp) <> ''
    ORDER BY region NULLS LAST, visningsnavn
    """
)


async def run(
    master: Path | None,
    mode: str,
    dry_run: bool,
    csv_path: Path | None,
) -> None:
    master_dims: set[str] = _load_master_dim1_set(master) if master else set()
    if mode == "master-only" and not master_dims:
        raise SystemExit("master-only krever --master som peker på gyldig Master_enheter-register.")

    async with SessionLocal() as db:
        rows = (await db.execute(PROPS_SQL)).mappings().all()

    planned: list[dict[str, Any]] = []
    for r in rows:
        uid = str(r["unit_id_erp"]).strip()
        if not uid.isdigit():
            continue
        dim = _norm_dim(uid)
        if not dim:
            continue
        if mode == "master-only" and dim not in master_dims:
            continue
        k = r["koststed_kode"]
        ktrim = (k or "").strip()
        if ktrim == dim:
            continue
        planned.append(
            {
                "property_id": r["property_id"],
                "visningsnavn": r["visningsnavn"],
                "unit_id_erp": uid,
                "koststed_foer": ktrim or "",
                "koststed_etter": dim,
            }
        )

    print(f"Modus: {mode}")
    print(f"Rader som får oppdatert koststed_kode: {len(planned)}")
    if csv_path and planned:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(planned[0].keys()))
            w.writeheader()
            w.writerows(planned)
        print(f"CSV: {csv_path}")

    if dry_run:
        print("[DRY RUN] Ingen UPDATE utført.")
        return

    if not _writes_ok():
        print(
            "FEIL: Oppdatering nektet — sett BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1"
        )
        raise SystemExit(1)

    sql = text(
        """
        UPDATE properties
        SET koststed_kode = :ks, updated_at = now()
        WHERE property_id = CAST(:pid AS uuid)
        """
    )
    n = 0
    async with SessionLocal() as db:
        for p in planned:
            await db.execute(
                sql, {"ks": p["koststed_etter"], "pid": p["property_id"]}
            )
            n += 1
        await db.commit()
    print(f"OK — oppdatert {n} eiendommer.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Synk koststed_kode fra unit_id_erp")
    ap.add_argument(
        "--master",
        type=Path,
        help="Master_enheter_register.xlsx (påkrevd for mode=master-only)",
    )
    ap.add_argument(
        "--mode",
        choices=("master-only", "all-numeric"),
        default="master-only",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--csv", type=Path, help="Skriv planlagte endringer til CSV")
    args = ap.parse_args()
    if args.mode == "master-only" and not args.master:
        ap.error("master-only krever --master")
    asyncio.run(run(args.master, args.mode, args.dry_run, args.csv))


if __name__ == "__main__":
    main()
