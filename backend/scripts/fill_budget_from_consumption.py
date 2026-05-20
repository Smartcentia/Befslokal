#!/usr/bin/env python3
"""
Fyll budsjett-tabellen fra forbruk (manual_expenses) for 2024–2026 med ±variance per kategori.

Bruker cost_analysis_service for kategorisering og BudgetGenerationService.populate_budget_from_consumption.
Kjør fra backend-mappen:
  python3 scripts/fill_budget_from_consumption.py
  python3 scripts/fill_budget_from_consumption.py --years 2024,2025,2026
  python3 scripts/fill_budget_from_consumption.py --variance 0.15
  python3 scripts/fill_budget_from_consumption.py --property-ids <uuid1>,<uuid2>
  (Bruk ekte UUID-er; utelat --property-ids for alle eiendommer.)
"""

import argparse
import uuid
import asyncio
import os
import sys
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.db.session import SessionLocal
from app.services.budget_generation_service import budget_generation_service


DEFAULT_YEARS = [2024, 2025, 2026]


def parse_args():
    p = argparse.ArgumentParser(description="Fill budget table from consumption (manual_expenses) for 2024–2026")
    p.add_argument(
        "--years",
        type=str,
        default="2024,2025,2026",
        help="Comma-separated years (default: 2024,2025,2026)",
    )
    p.add_argument("--variance", type=float, default=0.2, help="Variance per category, default 0.2 (±20%%)")
    p.add_argument(
        "--property-ids",
        type=str,
        default=None,
        help="Comma-separated property UUIDs (default: all properties)",
    )
    return p.parse_args()


def _parse_years(s: str) -> List[int]:
    out = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            raise SystemExit(f"Ugyldig år i --years: {part!r}. Bruk f.eks. 2024,2025,2026")
    return out if out else DEFAULT_YEARS


async def run(years: List[int], variance: float, property_ids: Optional[List[str]]):
    async with SessionLocal() as db:
        total_budget = 0.0
        total_entries = 0
        results = []
        for year in years:
            result = await budget_generation_service.populate_budget_from_consumption(
                db=db,
                year=year,
                variance_pct=variance,
                property_ids=property_ids,
            )
            results.append(result)
            total_budget += result.get("total_budget_nok", 0)
            total_entries += result.get("entries_created", 0)
        return {"years": years, "results": results, "total_budget_nok": total_budget, "total_entries": total_entries}


def _validate_uuids(ids: List[str]) -> None:
    """Avbryt med tydelig feilmelding hvis noen verdier ikke er gyldige UUID-er."""
    invalid = []
    for s in ids:
        try:
            uuid.UUID(s)
        except (ValueError, TypeError):
            invalid.append(s)
    if invalid:
        raise SystemExit(
            f"Ugyldig property-ids (må være UUID-er): {invalid}. "
            "Kjør uten --property-ids for alle eiendommer, eller bruk UUID-er fra databasen."
        )


def main():
    args = parse_args()
    years = _parse_years(args.years)
    property_ids = None
    if args.property_ids:
        property_ids = [s.strip() for s in args.property_ids.split(",") if s.strip()]
        _validate_uuids(property_ids)

    out = asyncio.run(run(years=years, variance=args.variance, property_ids=property_ids))

    print(f"År: {out['years']}, variance: {args.variance}")
    for r in out["results"]:
        print(f"  {r['year']}: {r['total_budget_nok']:.2f} NOK, {r['entries_created']} rader")
    print(f"Totalt budsjett: {out['total_budget_nok']:.2f} NOK, rader opprettet: {out['total_entries']}")


if __name__ == "__main__":
    main()
