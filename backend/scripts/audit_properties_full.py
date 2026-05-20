#!/usr/bin/env python3
"""
Helhetlig revisjon: eiendom, enheter, kontrakter, leietaker, GL (rullerende år),
manuelle poster og property_annual_costs.

Rapport:
  - backend/data/property_completeness_audit.md
  - backend/data/property_completeness_audit.csv (alle eiendommer + gap-felter)
  - backend/data/property_contract_finance_gaps.csv (kun rader som ikke er ok_*)

Kjør:
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_full.py
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_full.py --year-min 2022 --year-max 2026
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_full.py --ui-surface

Se docs/DATAKILDER_EIENDOM_FINANS.md for begreper.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

try:
    from dotenv import load_dotenv
    load_dotenv(_backend / ".env", override=False)
    load_dotenv(_backend.parent / ".env", override=False)
except Exception:
    pass

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.services.financials.property_data_completeness import (
    PropertyCompletenessRow,
    compute_all_property_completeness,
    row_to_dict,
)
from app.services.financials.property_ui_surface_audit import (
    compute_all_ui_surface_rows,
    ui_surface_row_to_dict,
)

DEFAULT_MD = _backend / "data" / "property_completeness_audit.md"
DEFAULT_CSV = _backend / "data" / "property_completeness_audit.csv"
DEFAULT_GAPS_CSV = _backend / "data" / "property_contract_finance_gaps.csv"
DEFAULT_UI_SURFACE_CSV = _backend / "data" / "property_ui_surface_gaps.csv"


def _gap_analysis(r: PropertyCompletenessRow) -> dict[str, Any]:
    """
    Utledet fra PropertyCompletenessRow:
    - Kostnadsspor: GL i vindu (ikke no_gl_in_window) eller manual eller property_annual_cost.
    - Leietaker: alle aktive kontrakter har party når det finnes kontrakter.
    """
    has_fin = (not r.no_gl_in_window) or (float(r.manual_expense_total or 0) > 0.0001) or r.has_property_annual_cost
    has_ctr = r.active_contract_count > 0
    tenant_ok = (r.active_contract_count == 0) or (r.contracts_missing_party == 0)

    # Leietaker-mangel først når det finnes kontrakter (uavhengig av finans-spor)
    if has_ctr and not tenant_ok:
        gap = "missing_tenant_party"
    elif not has_fin and not has_ctr:
        gap = "no_finance_no_contract"
    elif has_ctr and not has_fin:
        gap = "contract_without_finance_trace"
    elif has_fin and has_ctr and tenant_ok:
        gap = "ok_with_contract"
    elif has_fin and not has_ctr:
        gap = "ok_institution_gl_only"
    else:
        gap = "other"

    return {
        "has_finance_trace": has_fin,
        "has_active_contract": has_ctr,
        "tenant_complete": tenant_ok,
        "gap_category": gap,
    }


async def _validate_db_url() -> None:
    from app.core.config import settings
    url = str(settings.DATABASE_URL or "")
    host = ""
    if "@" in url:
        host = url.split("@")[1].split(":")[0].split("/")[0]
    if not url or host in ("", "host"):
        print("FEIL: DATABASE_URL mangler eller er placeholder.", file=sys.stderr)
        sys.exit(1)
    if host.endswith(".railway.internal"):
        print("FEIL: Railway intern host resolver ikke lokalt.", file=sys.stderr)
        sys.exit(1)


def _write_csv(path: Path, rows: list[PropertyCompletenessRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "property_id",
        "name",
        "region",
        "score",
        "masterdata_ok",
        "missing_accounting_linkage",
        "unit_count",
        "active_contract_count",
        "contract_rent_year",
        "contracts_missing_party",
        "contract_missing_rent_amount",
        "manual_expense_lines",
        "manual_expense_total",
        "has_property_annual_cost",
        "gl_last_year",
        "gl_faktisk_husleie",
        "gl_andre_kostnader",
        "no_gl_in_window",
        "double_hole_no_finance",
               "anomaly_contract_rent_no_gl_lease",
        "anomaly_gl_lease_no_contract",
        "issue_codes",
        "has_finance_trace",
        "has_active_contract",
        "tenant_complete",
        "gap_category",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            d = row_to_dict(r)
            d["issue_codes"] = ";".join(d["issue_codes"])
            d.update({k: v for k, v in _gap_analysis(r).items()})
            w.writerow({k: d.get(k) for k in fieldnames})


def _write_gaps_csv(path: Path, rows: list[PropertyCompletenessRow]) -> int:
    """Kun rader som ikke er praktisk OK (alle kategorier utenom ok_*)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "property_id",
        "name",
        "region",
        "gap_category",
        "has_finance_trace",
        "has_active_contract",
        "tenant_complete",
        "active_contract_count",
        "contracts_missing_party",
        "no_gl_in_window",
        "manual_expense_total",
        "has_property_annual_cost",
        "gl_last_year",
        "score",
        "issue_codes",
    ]
    n = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            g = _gap_analysis(r)
            if str(g["gap_category"]).startswith("ok_"):
                continue
            d = row_to_dict(r)
            d["issue_codes"] = ";".join(d["issue_codes"])
            d.update(g)
            w.writerow({k: d.get(k) for k in fieldnames})
            n += 1
    return n


def _write_md(path: Path, rows: list[PropertyCompletenessRow], year_min: int, year_max: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n = len(rows)
    low = sum(1 for r in rows if r.score < 50)
    code_counts: Counter[str] = Counter()
    for r in rows:
        for c in r.issue_codes:
            code_counts[c] += 1

    lines = [
        "# Helhetlig eiendomsrevisjon (datakompletthet)",
        "",
        f"_Generert: {iso}_",
        "",
        f"GL-vindu: **{year_min}**–**{year_max}** (siste år med aktivitet per eiendom brukes i kolonnene GL_*).",
        "",
        "## Sammendrag",
        "",
        f"- Eiendommer totalt: **{n}**",
        f"- Score under 50: **{low}**",
        "",
        "### Avvikskoder (antall eiendommer)",
        "",
    ]
    for code, cnt in sorted(code_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{code}`: **{cnt}**")

    gap_counts: Counter[str] = Counter()
    for r in rows:
        gap_counts[_gap_analysis(r)["gap_category"]] += 1
    lines.extend(
        [
            "",
            "### Kontrakt / kostnad / leietaker (gap_category)",
            "",
        ]
    )
    for cat, cnt in sorted(gap_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{cat}`: **{cnt}**")
    lines.extend(
        [
            "",
            f"Arbeidsliste (kun hull): `{DEFAULT_GAPS_CSV.name}`",
            "",
            "---",
            "",
            "## Laveste score (topp 40)",
            "",
            "| Score | Navn | Region | Kontraktsleie | GL-år | Husleie (GL) | Koder |",
            "|---:|---|---|---|---:|---:|---|",
        ]
    )
    worst = sorted(rows, key=lambda r: (r.score, r.name or ""))[:40]
    for r in worst:
        ic = ", ".join(r.issue_codes[:5]) + ("…" if len(r.issue_codes) > 5 else "")
        lines.append(
            f"| {r.score} | {(r.name or '')[:50]} | {r.region or '–'} | {r.contract_rent_year:,.0f} | "
            f"{r.gl_last_year or '–'} | {r.gl_faktisk_husleie:,.0f} | {ic} |"
        )
    lines.extend(
        [
            "",
            f"Full CSV: `{DEFAULT_CSV.name}` (inkl. `has_finance_trace`, `gap_category` m.m.)",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_ui_surface_csv(path: Path, rows: list) -> int:
    """Eiendomsside / finansår-risiko + informative masterdata-flagg."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "property_id",
        "name",
        "region",
        "issue_codes",
        "gl_last_year",
        "no_gl_in_window",
        "has_owner_or_master",
        "has_land_area",
        "has_matrikkel",
        "has_org_number",
        "has_prop_description",
        "has_dept_or_koststed",
        "has_lease_expiry",
        "has_regulation",
        "has_project",
    ]
    n_issues = 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            d = ui_surface_row_to_dict(r)
            if d.get("issue_codes"):
                n_issues += 1
            w.writerow({k: d.get(k) for k in fieldnames})
    return n_issues


async def main_async(args: argparse.Namespace) -> None:
    await _validate_db_url()
    async with SessionLocal() as db:
        rows = await compute_all_property_completeness(
            db, year_min=args.year_min, year_max=args.year_max
        )

    _write_csv(Path(args.csv), rows)
    gaps_path = Path(args.gaps_csv)
    n_gaps = _write_gaps_csv(gaps_path, rows)
    _write_md(Path(args.markdown), rows, args.year_min, args.year_max)
    print(f"CSV:       {args.csv}")
    print(f"Hull-CSV:  {args.gaps_csv}  ({n_gaps} rader)")
    print(f"MD:        {args.markdown}")
    print(f"Rader:     {len(rows)}")

    if getattr(args, "ui_surface", False):
        cmap = {
            str(r.property_id): (r.gl_last_year, r.no_gl_in_window)
            for r in rows
        }
        async with SessionLocal() as db:
            ui_rows = await compute_all_ui_surface_rows(db, cmap)
        uip = Path(args.ui_surface_csv)
        n_ui = _write_ui_surface_csv(uip, ui_rows)
        print(f"UI-flate:  {args.ui_surface_csv}  ({n_ui} eiendommer med issue_codes)")


def main() -> None:
    p = argparse.ArgumentParser(description="Helhetlig eiendomsrevisjon (finans + kontrakt)")
    p.add_argument("--year-min", type=int, default=2020)
    p.add_argument("--year-max", type=int, default=2030)
    p.add_argument("--csv", default=str(DEFAULT_CSV))
    p.add_argument("--gaps-csv", default=str(DEFAULT_GAPS_CSV), dest="gaps_csv")
    p.add_argument("--markdown", default=str(DEFAULT_MD))
    p.add_argument(
        "--ui-surface",
        action="store_true",
        help="Skriv property_ui_surface_gaps.csv (finansår vs GL, masterdata-flagg)",
    )
    p.add_argument("--ui-surface-csv", default=str(DEFAULT_UI_SURFACE_CSV), dest="ui_surface_csv")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
