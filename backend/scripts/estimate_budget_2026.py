#!/usr/bin/env python3
"""
Estimer budsjett for 2026 basert på Innkjøpsanalyse (property_husleie_csv).

Bruker Innkjøpsanalyse som primær kilde med riktig husleie/kostnadsdata per eiendom.
Fallback til kontrakter for eiendommer uten Innkjøpsanalyse-data.

Kjør fra backend-mappen:
  python3 scripts/estimate_budget_2026.py
  python3 scripts/estimate_budget_2026.py --dry-run
  python3 scripts/estimate_budget_2026.py --source gl   # Bruk GL i stedet
  railway run python3 scripts/estimate_budget_2026.py --dry-run

Se docs/BUDSJETT_2026_ESTIMERING.md for dokumentasjon.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend))
os.chdir(_backend)

from dotenv import load_dotenv

load_dotenv(_backend / ".env")

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.financial_models import Budget
from app.services.budget_generation_service import budget_generation_service


SOURCE_YEARS = [2024, 2025]
SOURCE_YEAR = 2025
TARGET_YEAR = 2026
DEFAULT_INFLATION = 0.035


def format_nok(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", " ")


def print_report(report: dict, source: str = "innkjøpsanalyse") -> None:
    title = "BUDSJETT 2026 – ESTIMERING FRA INNKJØPSANALYSE 2025" if source == "innkjøpsanalyse" else "BUDSJETT 2026 – ESTIMERING FRA REGNSKAP 2024 OG 2025"
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print(f"\nTotal budsjett: {format_nok(report['total'])} NOK")

    print("\n--- Per region ---")
    for region, total in report["by_region"].items():
        print(f"  {region}: {format_nok(total)} NOK")

    print("\n--- Topp 15 eiendommer (etter budsjett) ---")
    for i, p in enumerate(report["by_property"][:15], 1):
        print(f"  {i:2}. {p['name'][:40]:40} | {p['region']:12} | {format_nok(p['total'])} NOK")

    if len(report["by_property"]) > 15:
        print(f"  ... og {len(report['by_property']) - 15} flere eiendommer")


async def run(
    dry_run: bool = False,
    report_only: bool = False,
    inflation: float = DEFAULT_INFLATION,
    source: str = "innkjøpsanalyse",
) -> dict:
    async with SessionLocal() as db:
        if source == "gl":
            result = await budget_generation_service.estimate_budget_from_historical_years(
                db=db,
                source_years=SOURCE_YEARS,
                target_year=TARGET_YEAR,
                inflation_rate=inflation,
            )
            props_primary = result.get("properties_with_gl", 0)
        else:
            result = await budget_generation_service.estimate_budget_from_innkjøpsanalyse(
                db=db,
                source_year=SOURCE_YEAR,
                target_year=TARGET_YEAR,
                inflation_rate=inflation,
            )
            props_primary = result.get("properties_innkjøpsanalyse", 0)

        report = result["report"]
        print_report(report, source=source)

        print(f"\n--- Oppsummering ---")
        if source == "innkjøpsanalyse":
            print(f"  Eiendommer med Innkjøpsanalyse: {props_primary}")
        else:
            print(f"  Eiendommer med GL-data: {props_primary}")
        print(f"  Eiendommer (fallback):  {result['properties_fallback']}")
        print(f"  Budsjettrader:         {result['entries_created']}")

        if not dry_run and not report_only and result["budget_entries"]:
            # Slett eksisterende budsjett for 2026, deretter insert i batcher
            # (PostgreSQL begrenser til 32767 argumenter per spørring)
            await db.execute(text("DELETE FROM budget WHERE year = :year"), {"year": TARGET_YEAR})
            entries = result["budget_entries"]
            batch_size = 500
            for i in range(0, len(entries), batch_size):
                batch = entries[i : i + batch_size]
                stmt = insert(Budget).values(batch)
                await db.execute(stmt)
            await db.commit()
            print(f"\n  Lagret {len(result['budget_entries'])} budsjettrader til budget-tabellen.")
        elif dry_run:
            print("\n  [DRY RUN] Ingen endringer skrevet til databasen.")
        elif report_only:
            print("\n  [REPORT ONLY] Kun rapport vist, ingen endringer.")

        return result


def main():
    parser = argparse.ArgumentParser(
        description="Estimer budsjett 2026 fra regnskap 2024 og 2025"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Beregn og vis rapport uten å skrive til database",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Vis kun rapport (samme som --dry-run for visning)",
    )
    parser.add_argument(
        "--inflation",
        type=float,
        default=DEFAULT_INFLATION,
        help=f"Inflasjonsjustering (default {DEFAULT_INFLATION})",
    )
    parser.add_argument(
        "--source",
        choices=["innkjøpsanalyse", "gl"],
        default="innkjøpsanalyse",
        help="Datakilde: innkjøpsanalyse (default) eller gl",
    )
    args = parser.parse_args()

    asyncio.run(run(
        dry_run=args.dry_run,
        report_only=args.report_only,
        inflation=args.inflation,
        source=args.source,
    ))


if __name__ == "__main__":
    main()
