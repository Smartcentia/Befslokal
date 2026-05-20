#!/usr/bin/env python3
"""
Revisjon: eiendommer der EnhetID (unit_id_erp) ser ut som Agresso Dim1,
men koststed_kode mangler eller er ulik — typisk årsak til feil DB-sammenligning.

Valgfritt: --master Master_enheter_register.xlsx markerer rader som finnes i master.

  railway run -- bash -c 'cd backend && python3 scripts/audit_koststed_unit_erp_mismatch.py'
  railway run -- bash -c 'cd backend && python3 scripts/audit_koststed_unit_erp_mismatch.py --master /path/Master.xlsx --csv rapport.csv'
"""

from __future__ import annotations

import argparse
import asyncio
import csv
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


def _load_master_dim1(path: Path) -> dict[str, str]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Master_enheter"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return {}
    header = [str(h) if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(header) if h}
    out: dict[str, str] = {}
    for r in rows[1:]:
        if not r or "Dim1" not in idx:
            continue
        nk = _norm_dim(r[idx["Dim1"]])
        if not nk:
            continue
        name = ""
        if "Enhet_navn_AGRESSO" in idx and r[idx["Enhet_navn_AGRESSO"]]:
            name = str(r[idx["Enhet_navn_AGRESSO"]]).strip()
        out[nk] = name
    return out


AUDIT_SQL = text(
    """
    SELECT
        p.property_id::text AS property_id,
        COALESCE(NULLIF(TRIM(p.name), ''), NULLIF(TRIM(p.address), ''), '') AS visningsnavn,
        p.region,
        p.unit_id_erp,
        p.koststed_kode,
        CASE
            WHEN p.koststed_kode IS NULL OR TRIM(p.koststed_kode) = '' THEN true
            ELSE false
        END AS koststed_mangler,
        CASE
            WHEN p.unit_id_erp IS NOT NULL
 AND TRIM(p.unit_id_erp) <> ''
                 AND TRIM(p.unit_id_erp) ~ '^[0-9]+$'
 THEN true
            ELSE false
        END AS unit_erp_er_numerisk
    FROM properties p
    WHERE p.unit_id_erp IS NOT NULL AND TRIM(p.unit_id_erp) <> ''
    ORDER BY p.region NULLS LAST, visningsnavn
    """
)


async def run(master: Path | None, csv_path: Path | None) -> None:
    master_dim: dict[str, str] = _load_master_dim1(master) if master else {}

    async with SessionLocal() as db:
        rows = (await db.execute(AUDIT_SQL)).mappings().all()

    numerisk = [dict(r) for r in rows if r["unit_erp_er_numerisk"]]
    mangler_koststed = [r for r in numerisk if r["koststed_mangler"]]
    feil_koststed = []
    for r in numerisk:
        if r["koststed_mangler"]:
            continue
        u = _norm_dim(r["unit_id_erp"])
        k = _norm_dim(r["koststed_kode"])
        if u and k and u != k:
            feil_koststed.append({**r, "dim1_fra_unit_erp": u, "koststed_norm": k})

    i_master_mangler_koststed = [
        r
        for r in mangler_koststed
        if _norm_dim(r["unit_id_erp"]) in master_dim
    ]

    print("=== Koststed vs unit_id_erp (numerisk EnhetID) ===")
    print(f"Eiendommer med numerisk unit_id_erp: {len(numerisk)}")
    print(f"  davon koststed_kode tom: {len(mangler_koststed)}")
    print(f"  davon koststed_kode satt men ulik unit_id_erp: {len(feil_koststed)}")
    if master_dim:
        print(
            f"  davon også Dim1 i master-fil (via unit_id_erp): "
            f"{len(i_master_mangler_koststed)} (koststed tom — typisk «mange feil»-mønster)"
        )

    if csv_path:
        out_rows: list[dict[str, Any]] = []
        for r in mangler_koststed:
            uid = _norm_dim(r["unit_id_erp"])
            out_rows.append(
                {
                    "problem": "koststed_mangler",
                    "property_id": r["property_id"],
                    "visningsnavn": r["visningsnavn"],
                    "region": r["region"] or "",
                    "unit_id_erp": r["unit_id_erp"],
                    "koststed_kode": r["koststed_kode"] or "",
                    "i_master_dim1": "ja" if uid and uid in master_dim else "nei",
                    "master_enhet_navn": master_dim.get(uid or "", ""),
                }
            )
        for r in feil_koststed:
            out_rows.append(
                {
                    "problem": "koststed_ulik_unit_erp",
                    "property_id": r["property_id"],
                    "visningsnavn": r["visningsnavn"],
                    "region": r["region"] or "",
                    "unit_id_erp": r["unit_id_erp"],
                    "koststed_kode": r["koststed_kode"] or "",
                    "i_master_dim1": "",
                    "master_enhet_navn": "",
                }
            )
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()) if out_rows else [])
            if out_rows:
                w.writeheader()
                w.writerows(out_rows)
        print(f"\nCSV: {csv_path} ({len(out_rows)} rader)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", type=Path, help="Master_enheter_register.xlsx")
    ap.add_argument("--csv", type=Path, help="Rapportfil")
    args = ap.parse_args()
    asyncio.run(run(args.master, args.csv))


if __name__ == "__main__":
    main()
