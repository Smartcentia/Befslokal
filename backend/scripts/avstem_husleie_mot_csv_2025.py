#!/usr/bin/env python3
"""
Avstemning: BEFS faktisk husleie (GL) mot Innkjøpsanalyse-CSV 2025.

CSV-struktur:
- Radetiketter | Region Midt-Norge | Region Nord | Region Sør | Region Vest | Region Øst | (tom) | Bufdir | Totalsum
- Under "Leie lokaler andre utleiere" og "Leie lokaler fra Statsbygg" finner vi eiendommer/enheter med faktisk husleie

Bruker kun husleie-kategorier (Leie lokaler andre utleiere + Leie lokaler fra Statsbygg)
for å matche BEFS is_lease_account.

Kjør:
  cd backend
  python -m scripts.avstem_husleie_mot_csv_2025 --csv /path/to/Innkjøpsanalyse....csv [--year 2025]
"""

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Last .env for DATABASE_URL
_backend = Path(__file__).resolve().parents[1]
_env = _backend / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.financial_models import GLTransaction
from app.models.gl_constants import is_lease_account
from app.domains.core.models.property import Property
from app.domains.core.utils.region_mapping import COUNTY_TO_REGION

REGION_COLS = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"]
REGION_ORDER = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"]


def parse_amount(s: str) -> float:
    """Parse Norwegian number: '  1 915 964' -> 1915964."""
    if not s or not str(s).strip():
        return 0.0
    cleaned = str(s).strip().replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def normalize_region(raw: Optional[str]) -> str:
    """Map region_name/region_code to standardformat."""
    if not raw or not str(raw).strip():
        return "Øvrig"
    r = str(raw).strip()
    return COUNTY_TO_REGION.get(r, COUNTY_TO_REGION.get(r.replace("Region ", ""), r))


def load_csv_husleie(csv_path: Path) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """
    Parse CSV and extract husleie (Leie lokaler andre utleiere + Leie lokaler fra Statsbygg).
    Returns:
      - by_radetikett: { radetikett: { region: amount } }
      - by_region: { region: total }
    """
    by_radetikett: Dict[str, Dict[str, float]] = {}
    by_region: Dict[str, float] = {r: 0.0 for r in REGION_ORDER}

    HUSLEIE_SECTIONS = {"Leie lokaler andre utleiere", "Leie lokaler fra Statsbygg"}
    SECTION_END = {"Fellesutgifter (BAD) Statsbygg", "Fellesutgifter andre utleiere", "Fellesutgifter", "Reparasjon og vedlikehold"}

    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                reader = csv.reader(f, delimiter=";")
                rows = list(reader)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Kunne ikke lese CSV med noen av encodings: utf-8-sig, utf-8, latin-1, cp1252")

    header_idx = None
    for i, row in enumerate(rows):
        if len(row) > 0 and "Radetiketter" in (row[0] or ""):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Fant ikke header-rad med 'Radetiketter'")

    # Kolonner: 0=Radetiketter, 1=Midt-Norge, 2=Nord, 3=Sør, 4=Vest, 5=Øst, 6=Bufdir, 7=Totalsum
    col_map = {"Midt-Norge": 1, "Nord": 2, "Sør": 3, "Vest": 4, "Øst": 5, "Bufdir": 6}

    current_section = ""
    for i in range(header_idx + 1, len(rows)):
        row = rows[i]
        if len(row) < 2:
            continue
        radetikett = (row[0] or "").strip()
        if not radetikett:
            continue

        if radetikett in HUSLEIE_SECTIONS:
            current_section = radetikett
            continue
        if radetikett in SECTION_END or (radetikett.startswith("Fellesutgifter") and "Statsbygg" not in radetikett):
            current_section = ""
            continue
        if radetikett == "Leie av lokaler og tilknyttede utgifter":
            current_section = ""
            continue
        if radetikett == "Totalsum":
            break

        if current_section not in HUSLEIE_SECTIONS:
            continue

        if radetikett not in by_radetikett:
            by_radetikett[radetikett] = {r: 0.0 for r in REGION_ORDER}

        for region, col in col_map.items():
            if col < len(row):
                amt = parse_amount(row[col])
                by_radetikett[radetikett][region] += amt
                by_region[region] += amt

    return by_radetikett, by_region


async def get_befs_husleie(db: AsyncSession, year: int) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """
    Get faktisk husleie from gl_transactions (is_lease_account) per department_name+region and per region.
    Uses region_name from gl_transactions when available; else property.region.
    """
    # GL per department_name + region_name
    stmt = text("""
        SELECT
            COALESCE(g.department_name, '') AS dept_name,
            COALESCE(g.region_name, p.region, '') AS region_raw,
            SUM(g.amount) AS total
        FROM gl_transactions g
        LEFT JOIN properties p ON g.property_id = p.property_id
        WHERE g.year = :yr
          AND g.amount > 0
          AND (
            g.account_name IN ('Leie lokaler fra Statsbygg', 'Leie lokaler andre utleiere', 'Leie parkeringsplass', 'Husleie')
            OR g.account_name ILIKE 'Leie %'
          )
        GROUP BY COALESCE(g.department_name, ''), COALESCE(g.region_name, p.region, '')
    """)
    result = await db.execute(stmt, {"yr": year})
    rows = result.fetchall()

    by_dept: Dict[str, Dict[str, float]] = {}
    by_region: Dict[str, float] = {r: 0.0 for r in REGION_ORDER}

    for r in rows:
        dept = (r[0] or "").strip() or "(uten koststed)"
        reg_raw = (r[1] or "").strip()
        reg = normalize_region(reg_raw)
        amt = float(r[2] or 0)
        if reg not in REGION_ORDER and reg != "Øvrig":
            reg = "Øvrig"
        if dept not in by_dept:
            by_dept[dept] = {rr: 0.0 for rr in REGION_ORDER}
        if reg in by_dept[dept]:
            by_dept[dept][reg] += amt
        by_region[reg] = by_region.get(reg, 0) + amt

    return by_dept, by_region


def fuzzy_match(a: str, b: str) -> float:
    """Simple similarity 0-1. Normalize and compare word overlap."""
    def norm(s: str) -> set:
        return set(re.sub(r"[^a-zæøå0-9]", " ", s.lower()).split()) - {"", "og", "i", "for", "av", "til"}
    sa, sb = norm(a), norm(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa), len(sb))


def main():
    parser = argparse.ArgumentParser(description="Avstem BEFS husleie mot Innkjøpsanalyse-CSV 2025")
    parser.add_argument("--csv", required=True, type=Path, help="Sti til CSV-fil")
    parser.add_argument("--year", type=int, default=2025, help="År for GL-data")
    parser.add_argument("--report", type=Path, help="Skriv rapport til fil (Markdown)")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Feil: CSV-fil ikke funnet: {args.csv}")
        sys.exit(1)

    print("Laster CSV...")
    csv_by_rad, csv_by_region = load_csv_husleie(args.csv)
    csv_total = sum(csv_by_region.values())
    print(f"  CSV: {len(csv_by_rad)} radetiketter, total husleie {csv_total:,.0f} kr")
    print(f"  Per region: {', '.join(f'{r}: {csv_by_region[r]:,.0f}' for r in REGION_ORDER)}")

    befs_by_dept = {}
    befs_by_region = {r: 0.0 for r in REGION_ORDER}

    if settings.DATABASE_URL:
        async def run():
            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as db:
                print("\nHenter BEFS GL husleie...")
                dept, reg = await get_befs_husleie(db, args.year)
                print(f"  BEFS: {len(dept)} enheter, total husleie {sum(reg.values()):,.0f} kr")
                print(f"  Per region: {', '.join(f'{r}: {reg[r]:,.0f}' for r in REGION_ORDER)}")
            await engine.dispose()
            return dept, reg

        befs_by_dept, befs_by_region = asyncio.run(run())
    else:
        print("\nDATABASE_URL ikke satt – hopper over BEFS-henting. Sett .env eller miljøvariabel.")

    # Rapport
    lines = [
        "# Avstemning: Faktisk husleie 2025 – BEFS vs Innkjøpsanalyse-CSV",
        "",
        "## 1. Oppsummering per region",
        "",
        "| Region | CSV (Innkjøpsanalyse) | BEFS (GL) | Differanse |",
        "|--------|------------------------|-----------|------------|",
    ]
    for r in REGION_ORDER:
        csv_val = csv_by_region.get(r, 0)
        befs_val = befs_by_region.get(r, 0)
        diff = befs_val - csv_val
        lines.append(f"| {r} | {csv_val:,.0f} | {befs_val:,.0f} | {diff:+,.0f} |")

    lines.extend([
        f"| **Total** | **{csv_total:,.0f}** | **{sum(befs_by_region.values()):,.0f}** | **{sum(befs_by_region.values()) - csv_total:+,.0f}** |",
        "",
        "## 2. CSV total (fra Totalsum-rad)",
        "",
        f"CSV total husleie (kun Leie lokaler andre utleiere + Leie lokaler fra Statsbygg): **{csv_total:,.0f} kr**",
        "",
        "Ekstern referanse (Totalsum fra hele regnskapet): 79 627 494 + 80 961 634 + 98 714 318 + 77 825 300 + 135 314 782 + 31 636 305 = **504 079 834 kr**",
        "",
        "> Merk: CSV-filen inneholder flere kategorier (fellesutgifter, reparasjon, etc.). Vi sammenligner kun *husleie*-kategorier.
> Bufdir-beløp som kun forekommer i underordnede totalrader (uten radetikett) inkluderes ikke i CSV-summen her.",
        "",
        "## 3. Matching radetikett ↔ BEFS department_name",
        "",
        "| Radetikett (CSV) | BEFS match | CSV total | BEFS total | Diff |",
        "|------------------|------------|----------|------------|------|",
    ])

    matched_rad = set()
    for rad, csv_regs in sorted(csv_by_rad.items(), key=lambda x: -sum(x[1].values())):
        rad_total = sum(csv_regs.values())
        if rad_total <= 0:
            continue
        best_match = None
        best_score = 0.0
        for dept, befs_regs in befs_by_dept.items():
            if not dept or dept == "(uten koststed)":
                continue
            score = fuzzy_match(rad, dept)
            if score > best_score and score >= 0.4:
                best_score = score
                best_match = dept
        if best_match:
            matched_rad.add(rad)
            befs_match_total = sum(befs_by_dept[best_match].values())
            diff = befs_match_total - rad_total
            lines.append(f"| {rad[:40]} | {best_match[:35]} | {rad_total:,.0f} | {befs_match_total:,.0f} | {diff:+,.0f} |")

    lines.extend([
        "",
        "## 4. Radetiketter uten god BEFS-match",
        "",
    ])
    unmatched = [r for r in sorted(csv_by_rad.keys(), key=lambda x: -sum(csv_by_rad[x].values())) if r not in matched_rad and sum(csv_by_rad[r].values()) > 0]
    for r in unmatched[:50]:
        lines.append(f"- **{r}**: {sum(csv_by_rad[r].values()):,.0f} kr")
    if len(unmatched) > 50:
        lines.append(f"- ... og {len(unmatched) - 50} flere")

    lines.extend([
        "",
        "## 5. Konklusjon",
        "",
        f"- CSV husleie (Leie lokaler andre + Statsbygg): **{csv_total:,.0f} kr**",
        f"- BEFS GL husleie (is_lease_account): **{sum(befs_by_region.values()):,.0f} kr**",
        f"- Differanse: **{sum(befs_by_region.values()) - csv_total:+,.0f} kr**",
        "",
        "Mulige årsaker til avvik:",
        "- Forskjellig definisjon av husleie (CSV vs GL account_name)",
        "- Transaksjoner uten property_id/department_code i BEFS",
        "- Forskjellig region-mapping (region_name i GL vs property.region)",
        "- Tidsrom/perioder (hele 2025 vs delvis)",
        "",
    ])

    report_text = "\n".join(lines)
    print("\n" + report_text)

    if args.report:
        args.report.write_text(report_text, encoding="utf-8")
        print(f"\nRapport skrevet til {args.report}")


if __name__ == "__main__":
    main()
