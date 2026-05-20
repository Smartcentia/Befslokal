#!/usr/bin/env python3
"""
Import Innkjøpsanalyse-CSV Total kost til property_husleie_csv.

Parser HELE blokken «Leie av lokaler og tilknyttede utgifter» (alle kategorier),
matcher radetikett mot property (fuzzy + eiendom/avdeling-mapping), lagrer per (property_id, year, region).
Genererer sluttrapport for umatchbare rader og total_kost_per_region JSON for UI.

Kjør:
  cd backend
  python -m scripts.import_innkjøpsanalyse_husleie --csv /path/to/Innkjøpsanalyse....csv [--year 2025] [--dry-run] [--backup]
"""
import argparse
import asyncio
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_backend = Path(__file__).resolve().parents[1]
_data_dir = _backend / "data"
_env = _backend / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
import app.db.base  # noqa: F401 - load all models for Property relationships
from sqlalchemy.orm.attributes import flag_modified

from app.domains.core.models.property import Property
from app.domains.core.models.property_husleie_csv import PropertyHusleieCsv
from app.domains.core.utils.region_mapping import get_operational_region
from app.domains.core.utils.property_matcher import add_property_alias, get_property_aliases

REGION_ORDER = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"]
SOURCE = "innkjøpsanalyse_2025"
MIN_SCORE = 0.55
MIN_SCORE_WHEN_REGION_MISMATCH = 0.7
LOW_SCORE_WARN_THRESHOLD = 0.7

# Alle kategorier under «Leie av lokaler og tilknyttede utgifter»
ALL_SECTIONS = {
    "Leie lokaler andre utleiere",
    "Leie lokaler fra Statsbygg",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter andre utleiere",
    "Strøm og oppvarming",
    "Renhold lokaler",
    "Reparasjon og vedlikehold leide lokaler",
    "Annen kostnad lokaler",
    "Fellesutgifter Statsbygg - indre vedlikehold",
    "Leie parkeringsplass",
    "Vakthold lokaler",
    "Vaktmestertjenester",
    "Renovasjon, vann, avløp o.l.",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Fast bygningsinventar over kr 50 000",
    "Reparasjon og vedlikehold av verktøy og maskiner, inkl serviceavtaler",
    "Reparasjon og vedlikehold av datautstyr, inkl. serviceavtaler",
}
col_map = {"Midt-Norge": 1, "Nord": 2, "Sør": 3, "Vest": 4, "Øst": 5, "Bufdir": 6}


def parse_amount(s: str) -> float:
    if not s or not str(s).strip():
        return 0.0
    cleaned = str(s).strip().replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_csv_total_kost(csv_path: Path) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, Dict[str, float]]]]:
    """
    Parse CSV, return:
    - by_radetikett: { radetikett: { region: amount } }  (sum over all categories, for matching)
    - by_category_region_radetikett: { category: { region: { radetikett: amount } } }  (for region view)
    Støtter både komma og semikolon som delimiter (auto-detect).
    """
    by_radetikett: Dict[str, Dict[str, float]] = {}
    by_category: Dict[str, Dict[str, Dict[str, float]]] = {}

    rows = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for delim in (",", ";"):
            try:
                with open(csv_path, "r", encoding=enc, newline="") as f:
                    cand = list(csv.reader(f, delimiter=delim))
                hi = next((i for i, row in enumerate(cand) if len(row) > 0 and "Radetiketter" in (row[0] or "")), None)
                if hi is not None and len(cand) > hi + 5:
                    rows = cand
                    break
            except (UnicodeDecodeError, StopIteration):
                pass
        if rows is not None:
            break
    if rows is None:
        raise ValueError("Kunne ikke lese CSV")

    header_idx = next((i for i, row in enumerate(rows) if len(row) > 0 and "Radetiketter" in (row[0] or "")), None)
    if header_idx is None:
        raise ValueError("Fant ikke header Radetiketter")

    in_block = False
    current_section = ""

    for i in range(header_idx + 1, len(rows)):
        row = rows[i]
        if len(row) < 2:
            continue
        radetikett = (row[0] or "").strip()

        if radetikett == "Leie av lokaler og tilknyttede utgifter":
            in_block = True
            continue
        if radetikett == "Totalsum":
            break
        if not in_block:
            continue

        if radetikett in ALL_SECTIONS:
            current_section = radetikett
            continue

        # Parse amounts per region
        region_amounts: Dict[str, float] = {}
        for region, col in col_map.items():
            if col < len(row):
                amt = parse_amount(row[col])
                region_amounts[region] = amt

        total = sum(region_amounts.values())
        if total <= 0:
            continue

        # Subtotal rows (empty radetikett) – Bufdir etc. kun i disse
        if not radetikett:
            if current_section:
                if current_section not in by_category:
                    by_category[current_section] = {}
                for region, amt in region_amounts.items():
                    if amt <= 0:
                        continue
                    if region not in by_category[current_section]:
                        by_category[current_section][region] = {}
                    by_category[current_section][region]["__subtotal__"] = (
                        by_category[current_section][region].get("__subtotal__", 0) + amt
                    )
            continue

        # Data row – aggregate for matching (sum across categories)
        if radetikett not in by_radetikett:
            by_radetikett[radetikett] = {r: 0.0 for r in REGION_ORDER}
        for region, amt in region_amounts.items():
            by_radetikett[radetikett][region] += amt

        # Per category for region view
        if current_section:
            if current_section not in by_category:
                by_category[current_section] = {}
            for region, amt in region_amounts.items():
                if amt <= 0:
                    continue
                if region not in by_category[current_section]:
                    by_category[current_section][region] = {}
                by_category[current_section][region][radetikett] = (
                    by_category[current_section][region].get(radetikett, 0) + amt
                )

    return by_radetikett, by_category


def load_mapping() -> List[Dict[str, Any]]:
    """Load eiendom/avdeling mapping."""
    path = _data_dir / "eiendom_avdeling_mapping.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def norm_words(s: str) -> set:
    return set(re.sub(r"[^a-zæøå0-9]", " ", s.lower()).split()) - {"", "og", "i", "for", "av", "til"}


def fuzzy_score(a: str, b: str) -> float:
    sa, sb = norm_words(a), norm_words(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa), len(sb))


def _primary_region_from_amounts(region_amounts: Dict[str, float]) -> Optional[str]:
    best_reg = None
    best_amt = 0.0
    for reg, amt in region_amounts.items():
        if amt > best_amt:
            best_amt = amt
            best_reg = reg
    return best_reg


def _property_region(p: Property) -> str:
    if p.external_data and (p.external_data.get("bufdir") or p.external_data.get("bufdir_institution")):
        return "Bufdir"
    return get_operational_region(p.region or "") or ""


def _region_from_mapping(mapping_region: str) -> str:
    """Map mapping region (Midt, Øst, etc) to our standard."""
    if mapping_region == "Midt":
        return "Midt-Norge"
    return mapping_region


async def match_radetikett_to_property(
    db: AsyncSession,
    radetikett: str,
    properties: List[Property],
    region_amounts: Optional[Dict[str, float]] = None,
    mapping: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Tuple[Property, float]]:
    """
    Return (best_matching_property, score) or None.
    Uses mapping for avdeling->institusjon, then fuzzy match against property.name.
    """
    primary_csv_region = _primary_region_from_amounts(region_amounts) if region_amounts else None

    # 1. Try mapping: avdelingsnavn -> institusjonsnavn, or direct institusjonsnavn
    institusjonsnavn_to_match = None
    if mapping:
        for m in mapping:
            inst = (m.get("institusjonsnavn") or "").strip()
            avd = (m.get("avdelingsnavn") or "").strip()
            if not inst:
                continue
            if radetikett == inst or fuzzy_score(radetikett, inst) >= 0.9:
                institusjonsnavn_to_match = inst
                break
            if avd and (radetikett == avd or fuzzy_score(radetikett, avd) >= 0.9):
                institusjonsnavn_to_match = inst
                break
            if inst in radetikett or radetikett in inst:
                institusjonsnavn_to_match = inst
                break

    best = None
    best_score = 0.0
    for p in properties:
        name = (p.name or "").strip()
        aliases = get_property_aliases(p)
        candidates = [name] if name else []
        candidates.extend(aliases)
        if not candidates:
            continue
        score = max(fuzzy_score(radetikett, c) for c in candidates)
        if institusjonsnavn_to_match and fuzzy_score(institusjonsnavn_to_match, name) >= 0.8:
            score = max(score, 0.85)
        if score <= 0:
            continue

        prop_region = _property_region(p)
        if primary_csv_region and prop_region and primary_csv_region != prop_region:
            if score < MIN_SCORE_WHEN_REGION_MISMATCH:
                continue
        elif score < MIN_SCORE:
            continue

        if score > best_score:
            best_score = score
            best = p

    return (best, best_score) if best else None


def write_sluttrapport(
    unmatched: List[Tuple[str, float, Dict[str, float]]],
    matched_count: int,
    matched_amount: float,
    total_csv: float,
    csv_path: Path,
    year: int,
) -> Path:
    """Write sluttrapport to backend/import_sluttrapport_2025_YYYYMMDD_HHMMSS.md"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _backend / f"import_sluttrapport_{year}_{ts}.md"
    unmatched_amount = sum(u[1] for u in unmatched)
    lines = [
        f"# Import sluttrapport – Total kost {year}",
        "",
        f"**Dato:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**CSV:** {csv_path}",
        f"**År:** {year}",
        "",
        "## Oppsummering",
        "",
        "| | Antall | Beløp (kr) |",
        "|---|---|---|",
        f"| Matchbare radetiketter | {matched_count} | {matched_amount:,.0f} |",
        f"| Umatchbare radetiketter | {len(unmatched)} | {unmatched_amount:,.0f} |",
        f"| **Total CSV** | | **{total_csv:,.0f}** |",
        "",
        "## Umatchbare radetiketter (sortert etter beløp)",
        "",
        "| Radetikett | Midt | Nord | Sør | Vest | Øst | Bufdir | Total |",
        "|------------|------|------|-----|------|-----|--------|-------|",
    ]
    for rad, total, by_reg in sorted(unmatched, key=lambda x: -x[1])[:80]:
        midt = by_reg.get("Midt-Norge", 0) or 0
        nord = by_reg.get("Nord", 0) or 0
        sor = by_reg.get("Sør", 0) or 0
        vest = by_reg.get("Vest", 0) or 0
        ost = by_reg.get("Øst", 0) or 0
        bufdir = by_reg.get("Bufdir", 0) or 0
        lines.append(f"| {rad[:50]} | {midt:,.0f} | {nord:,.0f} | {sor:,.0f} | {vest:,.0f} | {ost:,.0f} | {bufdir:,.0f} | {total:,.0f} |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def build_region_view_json(by_category: Dict[str, Dict[str, Dict[str, float]]], year: int) -> Dict[str, Any]:
    """Build structure for API: by_category with region totals and enhet breakdown."""
    result: Dict[str, Any] = {"year": year, "by_category": {}}
    for category, by_region in by_category.items():
        region_totals: Dict[str, float] = {}
        region_radetikett: Dict[str, List[Dict[str, Any]]] = {}
        for region, by_rad in by_region.items():
            total = sum(by_rad.values())
            region_totals[region] = total
            sorted_rad = sorted(by_rad.items(), key=lambda x: -x[1])
            region_radetikett[region] = [{"radetikett": r, "amount": round(a, 0)} for r, a in sorted_rad]
        result["by_category"][category] = {
            "by_region_totals": region_totals,
            "by_region_radetikett": region_radetikett,
        }
    return result


async def run_import(csv_path: Path, year: int, dry_run: bool, backup: bool):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    mapping = load_mapping()

    async with async_session() as db:
        result = await db.execute(select(Property))
        properties = list(result.scalars().all())

        by_rad, by_category = load_csv_total_kost(csv_path)
        total_csv = sum(sum(r.values()) for r in by_rad.values())
        print(f"CSV: {len(by_rad)} radetiketter, total {total_csv:,.0f} kr")
        print(f"Kategorier: {len(by_category)}")

        if not dry_run:
            if backup:
                backup_result = await db.execute(
                    select(PropertyHusleieCsv).where(
                        PropertyHusleieCsv.year == year, PropertyHusleieCsv.source == SOURCE
                    )
                )
                rows = backup_result.scalars().all()
                backup_data = [
                    {"property_id": str(r.property_id), "year": r.year, "region": r.region, "amount": r.amount, "source": r.source}
                    for r in rows
                ]
                backup_path = _backend / f"property_husleie_csv_backup_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                print(f"Backup: {len(backup_data)} rader lagret til {backup_path}")

            await db.execute(delete(PropertyHusleieCsv).where(PropertyHusleieCsv.year == year, PropertyHusleieCsv.source == SOURCE))

        inserted = 0
        unmatched: List[Tuple[str, float, Dict[str, float]]] = []
        low_score_matches: List[Tuple[str, str, float]] = []
        matched_amount = 0.0

        for radetikett, region_amounts in by_rad.items():
            rad_total = sum(region_amounts.values())
            if rad_total <= 0:
                continue
            match_result = await match_radetikett_to_property(db, radetikett, properties, region_amounts, mapping)
            if not match_result:
                unmatched.append((radetikett, rad_total, region_amounts))
                continue
            prop, score = match_result
            if score < LOW_SCORE_WARN_THRESHOLD:
                low_score_matches.append((radetikett, prop.name or "-", score))
            matched_amount += rad_total
            # Lagre radetikett som alias for fremtidig matching (property_matcher bruker aliases)
            if not dry_run:
                add_property_alias(prop, radetikett, SOURCE)
                flag_modified(prop, "external_data")
            if dry_run:
                print(f"  [dry-run] {radetikett[:45]} -> {prop.name} ({rad_total:,.0f} kr)")
                inserted += 1
                continue
            for region, amount in region_amounts.items():
                if amount <= 0:
                    continue
                rec = PropertyHusleieCsv(
                    property_id=prop.property_id,
                    year=year,
                    region=region,
                    amount=amount,
                    source=SOURCE,
                )
                db.add(rec)
                inserted += 1

        if not dry_run:
            await db.commit()

            # Sluttrapport
            report_path = write_sluttrapport(unmatched, len(by_rad) - len(unmatched), matched_amount, total_csv, csv_path, year)
            print(f"Sluttrapport: {report_path}")

            # Total kost per region JSON for API/UI
            region_view = build_region_view_json(by_category, year)
            json_path = _data_dir / f"total_kost_per_region_{year}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(region_view, f, indent=2, ensure_ascii=False)
            print(f"Region-visning: {json_path}")

        if low_score_matches:
            print(f"\nMatcher med lav score (score < {LOW_SCORE_WARN_THRESHOLD}, vurder manuelt):")
            for rad, prop_name, sc in sorted(low_score_matches, key=lambda x: x[2])[:15]:
                print(f"  - {rad[:40]} -> {prop_name[:35]} (score {sc:.2f})")

        if unmatched:
            print(f"\nUmatchbare radetiketter ({len(unmatched)}):")
            for r, amt, _ in sorted(unmatched, key=lambda x: -x[1])[:15]:
                print(f"  - {r}: {amt:,.0f} kr")

    await engine.dispose()
    return inserted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true", help="Vis hva som vil importeres uten å endre database")
    parser.add_argument("--backup", action="store_true", help="Eksporter eksisterende data til JSON før sletting")
    parser.add_argument("--parse-only", action="store_true", help="Kun parse CSV - ingen DB (for testing)")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Feil: {args.csv} ikke funnet")
        sys.exit(1)

    if args.parse_only:
        by_rad, by_category = load_csv_total_kost(args.csv)
        total = sum(sum(r.values()) for r in by_rad.values())
        print(f"Parse-only: {len(by_rad)} radetiketter, total {total:,.0f} kr")
        print(f"Kategorier: {list(by_category.keys())}")
        return

    if not settings.DATABASE_URL:
        print("Feil: DATABASE_URL ikke satt")
        sys.exit(1)

    n = asyncio.run(run_import(args.csv, args.year, args.dry_run, args.backup))
    print(f"\n{'[dry-run] ' if args.dry_run else ''}Importert {n} rader til property_husleie_csv")


if __name__ == "__main__":
    main()
