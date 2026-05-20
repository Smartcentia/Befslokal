#!/usr/bin/env python3
"""
Revisjon: kostnadsdata per eiendom (alle rader i properties).

For hver eiendom rapporteres:
- Antall GL-linjer og sum positive beløp for 2024 og 2025 (COALESCE year/ar, amount/belop)
- Totalt GL per eiendom (alle år)
- Antall poster i external_data.financials.manual_expenses
- EnhetID (ERP) og koststed_kode
- Aktiv kontrakt: antall og aggregert årsleie (forenklet)

Kjøring:
  cd backend && source .venv/bin/activate  # valgfritt
  python3 scripts/audit_property_cost_coverage.py
  python3 scripts/audit_property_cost_coverage.py --csv rapport.csv

Krever DATABASE_URL (f.eks. backend/.env).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db.base  # noqa: F401 — modellregistrering
from app.db.session import SessionLocal
from sqlalchemy import text


AUDIT_SQL = """
WITH rent AS (
    SELECT
        u.property_id,
        COUNT(c.contract_id) AS active_contracts,
        COALESCE(SUM(
            COALESCE(
                (c.amount->>'total_per_year')::numeric,
                (c.amount->>'amount_per_year')::numeric,
                (c.amount->>'monthly_rent')::numeric * 12,
                0
            )
        ), 0) AS annual_rent_hint
    FROM contracts c
    JOIN units u ON u.unit_id = c.unit_id
    WHERE c.status = 'active'
    GROUP BY u.property_id
),
gl_base AS (
    SELECT
        g.property_id,
        g.belop,
        COALESCE(
            g.ar,
            CASE
                WHEN trim(COALESCE(g.periode::text, '')) ~ '^[0-9]{6}$'
                THEN substring(trim(COALESCE(g.periode::text, '')) from 1 for 4)::int
                ELSE NULL
            END
        ) AS yr
    FROM gl_transactions g
    WHERE g.property_id IS NOT NULL
),
gl_y AS (
    SELECT
        property_id,
        SUM(CASE WHEN yr = 2024 AND belop > 0 THEN belop::numeric ELSE 0 END) AS sum_pos_2024,
        COUNT(*) FILTER (WHERE yr = 2024) AS rows_2024,
        SUM(CASE WHEN yr = 2025 AND belop > 0 THEN belop::numeric ELSE 0 END) AS sum_pos_2025,
        COUNT(*) FILTER (WHERE yr = 2025) AS rows_2025,
        SUM(CASE WHEN belop > 0 THEN belop::numeric ELSE 0 END) AS sum_pos_all_years,
        COUNT(*) AS rows_all_years
    FROM gl_base
    GROUP BY property_id
)
SELECT
    p.property_id::text AS property_id,
    COALESCE(NULLIF(TRIM(p.name), ''), NULLIF(TRIM(p.address), ''), '(uten navn)') AS visningsnavn,
    COALESCE(p.region, '') AS region,
    p.unit_id_erp,
    p.koststed_kode,
    CASE        WHEN jsonb_typeof(p.external_data #> '{financials,manual_expenses}') = 'array'
        THEN jsonb_array_length(COALESCE(p.external_data #> '{financials,manual_expenses}', '[]'::jsonb))
        ELSE 0
    END AS manual_expenses_count,
    COALESCE(r.active_contracts, 0) AS active_contracts,
    COALESCE(r.annual_rent_hint, 0) AS annual_rent_hint,
    COALESCE(y.sum_pos_2024, 0) AS gl_sum_pos_2024,
    COALESCE(y.rows_2024, 0) AS gl_rows_2024,
    COALESCE(y.sum_pos_2025, 0) AS gl_sum_pos_2025,
    COALESCE(y.rows_2025, 0) AS gl_rows_2025,
    COALESCE(y.sum_pos_all_years, 0) AS gl_sum_pos_all_years,
    COALESCE(y.rows_all_years, 0) AS gl_rows_all_years
FROM properties p
LEFT JOIN rent r ON r.property_id = p.property_id
LEFT JOIN gl_y y ON y.property_id = p.property_id
ORDER BY p.region NULLS LAST, visningsnavn;
"""


def _flag(row: dict) -> str:
    parts = []
    if row["gl_rows_all_years"] == 0 and row["manual_expenses_count"] == 0:
        parts.append("INGEN_KOST_KILDE")
    elif row["gl_rows_2025"] == 0 and row["gl_rows_2024"] == 0 and row["gl_rows_all_years"] > 0:
        parts.append("GL_IKKE_24_25")
    elif row["gl_sum_pos_2025"] > 0 and row["annual_rent_hint"] > 0:
        ratio = float(row["gl_sum_pos_2025"]) / float(row["annual_rent_hint"])
        if ratio < 0.05:
            parts.append("LAV_GL_VS_LEIE")
    if row["gl_rows_all_years"] > 0 and row["gl_sum_pos_2025"] == 0:
        parts.append("GL_MEN_0_2025")
    if row["active_contracts"] > 0 and row["gl_rows_all_years"] == 0:
        parts.append("KONTRAKT_UTEN_GL")
    return ";".join(parts) if parts else "OK"


async def run_audit(csv_path: str | None) -> None:
    print("=" * 72)
    print("BEFS — revisjon kostnadsdata per eiendom")
    print(f"Start: {datetime.now().isoformat(timespec='seconds')}")
    print("=" * 72)

    rows_out: list[dict] = []

    async with SessionLocal() as db:
        try:
            result = await db.execute(text(AUDIT_SQL))
        except Exception as e:
            print(f"\nFeil ved spørring (sjekk DATABASE_URL og at tabellen gl_transactions finnes): {e}")
            raise SystemExit(2) from e
        cols = result.keys()
        for r in result.mappings().all():
            d = {k: r[k] for k in cols}
            # Normaliser numeriske felt for CSV
            for k in list(d.keys()):
                v = d[k]
                if hasattr(v, "quantize"):
                    d[k] = float(v)
            d["flag"] = _flag(d)
            rows_out.append(d)

    n = len(rows_out)
    if n == 0:
        print("\nIngen eiendommer funnet i databasen.")
        return

    ingen = sum(1 for r in rows_out if r["flag"] == "INGEN_KOST_KILDE")
    ikke_24_25 = sum(1 for r in rows_out if "GL_IKKE_24_25" in r["flag"])
    lav = sum(1 for r in rows_out if "LAV_GL_VS_LEIE" in r["flag"])
    kontr_uten_gl = sum(1 for r in rows_out if "KONTRAKT_UTEN_GL" in r["flag"])

    print(f"\nEiendommer totalt: {n}")
    print(f"  INGEN_KOST_KILDE (verken GL eller manual_expenses): {ingen}")
    print(f"  GL_MEN_IKKE_I_2024_ELLER_2025: {ikke_24_25}")
    print(f"  LAV_GL_VS_LEIE (2025-pos / årsleie < 5 %): {lav}")
    print(f"  KONTRAKT_UTEN_GL: {kontr_uten_gl}")
    print(f"  OK (etter heuristikk): {sum(1 for r in rows_out if r['flag'] == 'OK')}")

    if csv_path:
        fieldnames = list(rows_out[0].keys()) if rows_out else []
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows_out)
        print(f"\nCSV skrevet: {csv_path}")
    else:
        print("\n--- Første 25 med avvik (sortert: ikke OK først) ---")
        def sort_key(r: dict):
            return (0 if r["flag"] == "OK" else 1, r.get("region") or "", r.get("visningsnavn") or "")
        preview = sorted(rows_out, key=sort_key)[:25]
        for r in preview:
            print(
                f"  [{r['flag']}] {r['visningsnavn'][:50]} | "
                f"GL25={r['gl_sum_pos_2025']:.0f} ({r['gl_rows_2025']} linjer) | "
                f"manual={r['manual_expenses_count']} | id={r['property_id'][:8]}…"
            )


def main() -> None:
    ap = argparse.ArgumentParser(description="Revisjon kostnadsdata alle eiendommer")
    ap.add_argument("--csv", metavar="FIL", help="Skriv full rapport til CSV")
    args = ap.parse_args()
    asyncio.run(run_audit(args.csv))


if __name__ == "__main__":
    main()
