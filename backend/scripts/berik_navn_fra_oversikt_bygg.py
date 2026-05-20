#!/usr/bin/env python3
"""
Berik eiendommer som kun har adresse som navn, med navn fra «Oversikt bygg og eiendom» CSV.

Leser CSV, matcher på lokalisering_id eller adresse, og oppdaterer properties.name
kun når CSV-navnet er et egentlig eiendomsnavn (ikke bare adresse).

Kjør: cd backend && railway run python3 scripts/berik_navn_fra_oversikt_bygg.py [--csv PATH] [--dry-run]
"""
import argparse
import asyncio
import csv
import difflib
import io
import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.db.base  # noqa: F401
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

ADDRESS_PATTERN = re.compile(r",\s*\d{4}\s+", re.IGNORECASE)


def _normalize_str(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def is_address_only_name(name: Optional[str], address: Optional[str]) -> bool:
    """Sjekk om name ser ut til å være kun adresse (ingen egentlig eiendomsnavn)."""
    if not name or not name.strip():
        return False
    name = name.strip()
    addr = (address or "").strip()
    if addr and _normalize_str(name) == _normalize_str(addr):
        return True
    if ADDRESS_PATTERN.search(name):
        if addr and addr.lower() in name.lower():
            return True
        if " - " not in name and len(name) < 80:
            return True
    if addr and name.lower().startswith(addr.lower()):
        rest = name[len(addr):].strip()
        if not rest or re.match(r"^[,\s\d]+", rest):
            return True
    return False
DEFAULT_CSV = os.path.expanduser("~/Downloads/Oversikt bygg og eiendom - GK og Budsjetterte(Ark1) (2).csv")


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    t = (s or "").strip()
    return t if t else None


def _parse_lokalisering_id(lok_raw: Optional[str]) -> Optional[str]:
    if not lok_raw:
        return None
    m = re.match(r"^(\d{4})", str(lok_raw).strip())
    return m.group(1) if m else None


def _parse_lokalisering_navn(lok_raw: Optional[str]) -> Optional[str]:
    """Hent navn fra 'XXXX - Navn' – delen etter ' - ', før evt. komma (postnummer)."""
    if not lok_raw:
        return None
    s = str(lok_raw).strip()
    if " - " in s:
        navn_full = s.split(" - ", 1)[1].strip()
        # Ta bort postnummer-delen ", 1234 Sted" for renere navn
        if "," in navn_full and ADDRESS_PATTERN.search(navn_full):
            navn_full = navn_full.split(",")[0].strip()
        return _norm(navn_full) if navn_full else None
    return _norm(s) if s else None


def _normalize_address_canonical(val: Optional[str]) -> str:
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"[\s\t\r\n]+", " ", s)
    s = re.sub(r"[.,;:-]", "", s)
    return s.strip()


def _normalize_address_heuristic(val: Optional[str]) -> str:
    s = _normalize_address_canonical(val)
    s = s.replace("gata", "gt").replace("gaten", "gt")
    s = s.replace("veien", "vg").replace("vegen", "vg")
    return s


def load_csv(csv_path: str) -> list:
    """Les Oversikt bygg CSV. Støtter semikolon/komma, flere encodings."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for delim in (";", ","):
            try:
                with open(csv_path, newline="", encoding=enc) as f:
                    lines = f.readlines()
                if len(lines) < 2:
                    continue
                content = "".join(lines[1:])
                reader = csv.DictReader(io.StringIO(content), delimiter=delim)
                if reader.fieldnames and "Lokalisering" in (reader.fieldnames or []):
                    rows = [r for r in reader if _norm(r.get("Lokalisering"))]
                    if rows:
                        return rows
            except (UnicodeDecodeError, csv.Error, OSError):
                continue
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        content = "".join(lines[1:]) if len(lines) > 1 else "".join(lines)
        reader = csv.DictReader(io.StringIO(content), delimiter=";")
        return [r for r in reader if _norm(r.get("Lokalisering"))]


async def main():
    parser = argparse.ArgumentParser(description="Berik eiendomsnavn fra Oversikt bygg CSV")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Sti til Oversikt bygg CSV")
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        print(f"CSV-fil ikke funnet: {args.csv}")
        print("Last ned «Oversikt bygg og eiendom - GK og Budsjetterte» og legg i ~/Downloads.")
        sys.exit(1)

    rows = load_csv(args.csv)
    print(f"Lest {len(rows)} rader fra CSV.")

    # Bygg indeks: lokalisering_id -> (navn, adresse), adresse -> (navn, lok_id)
    by_lok_id = {}
    by_address_norm = {}
    by_address_heur = {}

    for row in rows:
        lok_raw = row.get("Lokalisering", "")
        lok_id = _parse_lokalisering_id(lok_raw)
        navn = _parse_lokalisering_navn(lok_raw)
        addr = _norm(row.get("Adresselinje 1") or row.get("Adresselinje 1 "))
        postnr = _norm(row.get("Postnr") or row.get("Postnr "))
        poststed = _norm(row.get("Poststed") or row.get("Poststed "))

        if lok_id and navn:
            by_lok_id[lok_id] = (navn, addr)

        if addr:
            addr_full = f"{addr} {postnr or ''} {poststed or ''}".strip()
            can = _normalize_address_canonical(addr_full)
            if can:
                by_address_norm[can] = (navn, lok_id)
            can_short = _normalize_address_canonical(addr)
            if can_short and can_short not in by_address_norm:
                by_address_norm[can_short] = (navn, lok_id)
            heur = _normalize_address_heuristic(addr)
            if heur and heur not in by_address_heur:
                by_address_heur[heur] = (navn, lok_id)

    async with SessionLocal() as s:
        r = await s.execute(select(Property).where(Property.name.isnot(None)))
        all_props = r.scalars().all()

        address_only = [p for p in all_props if is_address_only_name(p.name, p.address)]
        print(f"Eiendommer med kun adresse som navn: {len(address_only)}")

        updates = []
        for prop in address_only:
            candidate_navn = None
            source = None

            # 1. Match på lokalisering_id
            if prop.lokalisering_id and prop.lokalisering_id in by_lok_id:
                navn, _ = by_lok_id[prop.lokalisering_id]
                if navn and not is_address_only_name(navn, prop.address):
                    candidate_navn = navn
                    source = "lokalisering_id"

            # 2. Match på adresse
            if not candidate_navn and prop.address:
                can = _normalize_address_canonical(prop.address)
                if can and can in by_address_norm:
                    navn, _ = by_address_norm[can]
                    if navn and not is_address_only_name(navn, prop.address):
                        candidate_navn = navn
                        source = "adresse_exact"
                if not candidate_navn:
                    heur = _normalize_address_heuristic(prop.address)
                    if heur and heur in by_address_heur:
                        navn, _ = by_address_heur[heur]
                        if navn and not is_address_only_name(navn, prop.address):
                            candidate_navn = navn
                            source = "adresse_heuristic"

            # 3. Fuzzy adresse
            if not candidate_navn and prop.address:
                row_can = _normalize_address_canonical(prop.address)
                if row_can and len(row_can) >= 5:
                    best_match, best_score = None, 0.0
                    for (can, (navn, _)) in by_address_norm.items():
                        if not can or not navn:
                            continue
                        sc = difflib.SequenceMatcher(None, row_can, can).ratio()
                        if sc > best_score and sc >= 0.85:
                            best_score = sc
                            best_match = navn
                    if best_match and not is_address_only_name(best_match, prop.address):
                        candidate_navn = best_match
                        source = "adresse_fuzzy"

            if candidate_navn:
                updates.append((prop, candidate_navn, source))

        if not updates:
            print("Ingen eiendommer funnet som kan berikes fra CSV.")
            return

        print(f"\nFunn: {len(updates)} eiendommer kan få nytt navn.")
        for prop, new_name, src in updates[:20]:
            print(f"  [{src}] {prop.name!r} -> {new_name!r}")

        if not args.dry_run and updates:
            for prop, new_name, _ in updates:
                prop.name = new_name
            await s.commit()
            print(f"\nOppdatert {len(updates)} eiendommer.")
        elif args.dry_run:
            print(f"\n[--dry-run] Ville oppdatere {len(updates)} eiendommer.")


if __name__ == "__main__":
    asyncio.run(main())
