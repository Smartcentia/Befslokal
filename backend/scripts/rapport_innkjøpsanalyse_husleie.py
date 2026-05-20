#!/usr/bin/env python3
"""
Rapport: Eiendommer og avdelinger med husleie fra Innkjøpsanalyse.

Viser at property_husleie_csv og total_kost_per_region er korrekt populert.
Kjør: railway run python scripts/rapport_innkjøpsanalyse_husleie.py [--year 2025]
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend))

from dotenv import load_dotenv
load_dotenv(_backend / ".env")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


async def run(year: int):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    data_dir = _backend / "data"
    json_path = data_dir / f"total_kost_per_region_{year}.json"

    # 1. property_husleie_csv: eiendommer med Innkjøpsanalyse
    async with async_session() as db:
        result = await db.execute(text("""
            SELECT p.property_id, p.name, p.region,
                   SUM(ph.amount) as total,
                   COUNT(DISTINCT ph.region) as region_count
            FROM property_husleie_csv ph
            JOIN properties p ON p.property_id = ph.property_id
            WHERE ph.year = :year AND ph.source = 'innkjøpsanalyse_2025'
            GROUP BY p.property_id, p.name, p.region
            ORDER BY SUM(ph.amount) DESC
        """), {"year": year})
        rows = result.fetchall()

        total_db = sum(float(r[3]) for r in rows)
        n_props = len(rows)

    # 2. total_kost_per_region JSON
    total_json = 0.0
    by_region_json = {}
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        for cat_data in (data.get("by_category") or {}).values():
            totals = cat_data.get("by_region_totals") or {}
            for reg, amt in totals.items():
                by_region_json[reg] = by_region_json.get(reg, 0) + float(amt or 0)
        total_json = sum(by_region_json.values())

    # 3. Avdelingsmapping
    mapping_path = data_dir / "eiendom_avdeling_mapping.json"
    n_avdelinger = 0
    if mapping_path.exists():
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
        n_avdelinger = len(mapping)

    # Output rapport
    lines = [
        "# Rapport: Husleie fra Innkjøpsanalyse",
        "",
        f"**År:** {year}",
        "",
        "## 1. Oppsummering",
        "",
        "| Kilde | Beløp | Beskrivelse |",
        "|-------|-------|-------------|",
        f"| property_husleie_csv (matchede eiendommer) | {total_db/1e6:.1f} MNOK | {n_props} eiendommer med direkte match |",
        f"| total_kost_per_region_{year}.json | {total_json/1e6:.1f} MNOK | Full oversikt (alle radetiketter inkl. Bufdir, Regionkontor) |",
        f"| eiendom_avdeling_mapping.json | — | {n_avdelinger} avdelinger mappet til eiendommer |",
        "",
        "## 2. Eiendommer med Innkjøpsanalyse-husleie",
        "",
        "Disse eiendommer har fått husleie fra Innkjøpsanalyse-CSV (lagret i property_husleie_csv):",
        "",
        "| Eiendom | Region | Total (NOK) |",
        "|---------|--------|-------------|",
    ]
    for r in rows[:50]:
        name = (r[1] or "-")[:50]
        reg = r[2] or "-"
        amt = float(r[3])
        lines.append(f"| {name} | {reg} | {amt:,.0f} |")
    if len(rows) > 50:
        lines.append(f"| ... og {len(rows)-50} flere | | |")

    lines.extend([
        "",
        "## 3. Total kost per region (fra JSON)",
        "",
        "| Region | Beløp (NOK) |",
        "|--------|--------------|",
    ])
    for reg, amt in sorted(by_region_json.items(), key=lambda x: -x[1]):
        lines.append(f"| {reg} | {amt:,.0f} |")
    lines.append(f"| **Total** | **{total_json:,.0f}** |")

    lines.extend([
        "",
        "## 4. Dataflyt",
        "",
        "```",
        "Innkjøpsanalyse-CSV",
        "       │",
        "       ├── match radetikett → eiendom (fuzzy + eiendom_avdeling_mapping)",
        "       │         └── property_husleie_csv (property_id, year, region, amount)",
        "       │",
        "       └── alle radetiketter (inkl. subtotaler)",
        "                 └── total_kost_per_region_{year}.json (by_category, by_region_totals)",
        "```",
        "",
        "**API-endepunkter:**",
        "- `GET /api/v1/properties/innkjoepsanalyse-husleie?year={year}` → by_property (fra property_husleie_csv)",
        "- `GET /api/v1/properties/total-kost-per-region?year={year}` → by_category (fra JSON)",
        "",
        "**Bruk i frontend:**",
        "- Financials: Total kost 2025 bruker total_kost_per_region når tilgjengelig (504 MNOK)",
        "- Eiendomsside: Total kost 2025 bruker innkjøpsanalyse.by_property[property_id].aggregert",
        "- Budsjett 2026: Eiendommer med property_husleie_csv får eksakte beløp; resten fordeles fra regionale restbeløp",
        "",
    ])

    report = "\n".join(lines)
    out_path = _backend / "data" / f"rapport_innkjøpsanalyse_husleie_{year}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\nRapport lagret: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Rapport: Eiendommer med husleie fra Innkjøpsanalyse")
    parser.add_argument("--year", type=int, default=2025)
    args = parser.parse_args()
    asyncio.run(run(args.year))


if __name__ == "__main__":
    main()
