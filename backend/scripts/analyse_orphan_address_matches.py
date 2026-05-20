#!/usr/bin/env python3
"""
Analyser GL-transaksjoner for koststeder uten eiendom.
Identifiserer poster der Leverandør eller Dim2 ser ut som adresser,
og matcher disse mot eiendommer i BEFS.

Bruk:
    cd backend
    railway run python scripts/analyse_orphan_address_matches.py --dept 204416 --year 2025 [--csv output.csv]
    railway run python scripts/analyse_orphan_address_matches.py --all --year 2025 [--csv output.csv]
    railway run python scripts/analyse_orphan_address_matches.py --all --year 2025 --apply   # Oppdater gl_transactions.property_id
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import text
from fuzzywuzzy import fuzz

from app.db.session import SessionLocal


# Kjente leverandørtyper som ikke er adresser (unngå å matche stedsnavn som Lillestrøm)
KNOWN_SUPPLIER_PATTERNS = [
    r"statsbygg",
    r"nettleie",
    r"kommunale",
    r"bufetat",
    r"regionkontor",
    r"posten",
    r"telenor",
    r"telia",
    r"nve",
    r"nettverk",
    r"strømleverandør",
    r"felleskostnad",
    r"fellesutgift",
    r"^as\s",  # AS som start
    r"\sas$",   # AS som slutt
]

# Fellesbyg – adresser hvor Dim2/supplier IKKE skal matche til eiendom.
# Kostnader tilhører avdelingen, ikke eiendommen.
FELLESBYGG_ADDRESSES = frozenset({
    "tærudgata 16",
    "tærudgata 16, 2004 lillestrøm",
    "tærudgata 16 2004 lillestrøm",
})


def _is_fellesbyg_address(val: str | None) -> bool:
    if not val or len(str(val).strip()) < 5:
        return False
    s = str(val).strip().lower()
    clean = s.split(",")[0].strip()
    return clean in FELLESBYGG_ADDRESSES or s in FELLESBYGG_ADDRESSES


# Adresse-heuristikk: mønstre som tyder på adresse
ADDRESS_PATTERNS = [
    r",\s*\d{4}\s+",           # ", 1234 Poststed"
    r"\d{4}\s+[a-zæøå]+",      # "1234 Oslo"
    r"\b(gata|gate|veien|vei|vegen|vegen|allé|plass|storgata|storgaten)\s+\d+",  # Gate 12, Veien 5
    r"\b\d+\s+(gata|gate|veien|vei|vegen)\b",  # 12 Gata
    r"\d{1,3}[a-z]?\s*,",      # "16A," eller "12,"
]


def _normalize_address_canonical(val: str | None) -> str:
    """Normaliser adresse for matching: lowercase, fjern punktum/komma."""
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"[\s\t\r\n]+", " ", s)
    s = re.sub(r"[.,;:-]", "", s)
    return s.strip()


def _normalize_address_heuristic(val: str | None) -> str:
    """Suffix-equivalence for lookup: gata→gt, veien→vg."""
    s = _normalize_address_canonical(val)
    s = s.replace("gata", "gt").replace("gaten", "gt")
    s = s.replace("veien", "vg").replace("vegen", "vg")
    return s


def looks_like_address(s: str | None) -> bool:
    """Sjekk om strengen ser ut som en adresse (ikke leverandør)."""
    if not s or len(str(s).strip()) < 5:
        return False
    s_lower = str(s).strip().lower()
    # Ekskluder kjente leverandørtyper
    for pat in KNOWN_SUPPLIER_PATTERNS:
        if re.search(pat, s_lower):
            return False
    # Inkluder hvis adresse-mønster matcher
    for pat in ADDRESS_PATTERNS:
        if re.search(pat, s_lower, re.IGNORECASE):
            return True
    # Ekstra: inneholder 4-sifret postnummer med poststed-format
    if re.search(r",\s*\d{4}\s", s):
        return True
    return False


def find_best_property_match(
    addr_candidate: str,
    properties: list[dict],
    threshold: int = 80,
) -> tuple[Optional[dict], float]:
    """Finn beste eiendom-match for adresse-lignende streng. properties = list of {property_id, name, address}."""
    if not addr_candidate or not properties:
        return None, 0.0
    norm_cand = _normalize_address_heuristic(addr_candidate)
    if len(norm_cand) < 5:
        return None, 0.0
    best_match = None
    best_score = 0.0
    for p in properties:
        addr = p.get("address") or ""
        if not addr:
            continue
        norm_prop = _normalize_address_heuristic(addr)
        if not norm_prop:
            continue
        score = fuzz.ratio(norm_cand, norm_prop)
        if score > best_score:
            best_score = score
            best_match = p
    if best_match and best_score >= threshold:
        return best_match, best_score
    return None, 0.0


async def get_orphan_departments(db, year: int) -> list[dict]:
    """Hent alle koststeder uten eiendom (department_code ikke i property.unit_id_erp)."""
    rows = await db.execute(text("""
        SELECT g.department_code, g.department_name, SUM(g.amount)::float as total, COUNT(*)::int as tx_count
        FROM gl_transactions g
        WHERE g.year = :yr AND g.amount > 0 AND g.department_code IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM properties p WHERE p.unit_id_erp = g.department_code)
        GROUP BY g.department_code, g.department_name
        HAVING SUM(g.amount) > 0
        ORDER BY SUM(g.amount) DESC
    """), {"yr": year})
    return [
        {"department_code": str(r[0]), "department_name": r[1] or "", "total": float(r[2] or 0), "tx_count": int(r[3] or 0)}
        for r in rows.fetchall()
    ]


async def run_analysis_single(
    db,
    dept: str,
    dept_name: str,
    year: int,
    all_props: list[dict],
) -> tuple[int, int, list[dict]]:
    """Kjør analyse for ett koststed. Returnerer (tx_count, match_count, matches)."""
    rows = await db.execute(text("""
        SELECT transaction_id, period, account_name, supplier_name, dim2_name, amount, invoice_number
        FROM gl_transactions
        WHERE department_code = :dept AND year = :yr AND amount > 0
        ORDER BY amount DESC
    """), {"dept": dept, "yr": year})
    transactions = rows.fetchall()

    matches: list[dict] = []
    for r in transactions:
        tx_id, period, account_name, supplier_name, dim2_name, amount, invoice_number = r
        amount_f = float(amount or 0)
        supplier = (supplier_name or "").strip()
        dim2 = (dim2_name or "").strip()

        candidates = []
        if looks_like_address(supplier) and not _is_fellesbyg_address(supplier):
            candidates.append(("supplier_name", supplier))
        if looks_like_address(dim2) and not _is_fellesbyg_address(dim2):
            candidates.append(("dim2_name", dim2))

        for source, val in candidates:
            prop, score = find_best_property_match(val, all_props)
            if prop and not _is_fellesbyg_address(prop.get("address") or prop.get("name") or ""):
                matches.append({
                    "department_code": dept,
                    "department_name": dept_name,
                    "transaction_id": str(tx_id) if tx_id else "",
                    "period": period or "",
                    "account_name": account_name or "",
                    "source_field": source,
                    "source_value": val,
                    "supplier_name": supplier,
                    "dim2_name": dim2,
                    "amount": amount_f,
                    "invoice_number": invoice_number or "",
                    "matched_property_id": str(prop["property_id"]),
                    "matched_property_name": prop.get("name") or "",
                    "matched_property_address": prop.get("address") or "",
                    "match_score": round(score, 1),
                })

    seen_tx = {}
    for m in matches:
        tid = m["transaction_id"]
        if tid not in seen_tx or m["match_score"] > seen_tx[tid]["match_score"]:
            seen_tx[tid] = m
    unique_matches = list(seen_tx.values())
    return len(transactions), len(unique_matches), unique_matches


async def apply_matches(db, matches: list[dict]) -> int:
    """Oppdater gl_transactions.property_id for matchende transaksjoner. Returnerer antall oppdatert."""
    if not matches:
        return 0
    seen_tx = {}
    for m in matches:
        tid = m.get("transaction_id")
        pid = m.get("matched_property_id")
        if not tid or not pid or tid == "None":
            continue
        if tid not in seen_tx or m.get("match_score", 0) > seen_tx[tid].get("match_score", 0):
            seen_tx[tid] = m
    updated = 0
    for tid, m in seen_tx.items():
        pid = m["matched_property_id"]
        try:
            r = await db.execute(text("""
                UPDATE gl_transactions SET property_id = CAST(:pid AS uuid) WHERE transaction_id = CAST(:tid AS uuid)
            """), {"pid": pid, "tid": tid})
            updated += r.rowcount
        except Exception as e:
            print(f"  ADVARSEL: Kunne ikke oppdatere {tid}: {e}")
    return updated


async def run_analysis(dept: str | None, year: int, csv_path: str | None, dry_run: bool, all_depts: bool, apply: bool):
    async with SessionLocal() as db:
        # Hent eiendommer én gang (brukes for alle koststeder)
        props_rows = await db.execute(text("""
            SELECT property_id::text, name, address FROM properties WHERE address IS NOT NULL AND address != ''
        """))
        all_props = [
            {"property_id": r[0], "name": r[1] or "", "address": r[2] or ""}
            for r in props_rows.fetchall()
        ]

        if all_depts:
            # --all: kjør for alle orphan-koststeder
            orphans = await get_orphan_departments(db, year)
            print(f"\n{'='*70}")
            print(f"Analyse ALLE koststeder uten eiendom ({year})")
            print(f"{'='*70}")
            print(f"Orphan-koststeder: {len(orphans)}")
            print(f"Eiendommer med adresse: {len(all_props)}")

            all_matches: list[dict] = []
            depts_with_matches = 0
            for i, o in enumerate(orphans):
                dept = o["department_code"]
                dept_name = o["department_name"]
                tx_count, match_count, matches = await run_analysis_single(db, dept, dept_name, year, all_props)
                if matches:
                    depts_with_matches += 1
                    all_matches.extend(matches)
                if (i + 1) % 20 == 0 or i == len(orphans) - 1:
                    print(f"  Prosessert {i + 1}/{len(orphans)} koststeder...")

            # Samlet rapport
            total_matched = sum(m["amount"] for m in all_matches)
            print(f"\n--- SAMLET RAPPORT ---")
            print(f"Koststeder med minst én match: {depts_with_matches} av {len(orphans)}")
            print(f"Totalt matcher: {len(all_matches)}")
            print(f"Sum beløp matchet: {total_matched:,.0f} kr")

            # Beløp per koststed
            by_dept: dict[str, list] = {}
            for m in all_matches:
                d = m["department_code"]
                if d not in by_dept:
                    by_dept[d] = []
                by_dept[d].append(m)
            print(f"\n--- Beløp per koststed (topp 15) ---")
            for dept_code, ms in sorted(by_dept.items(), key=lambda x: -sum(m["amount"] for m in x[1]))[:15]:
                m0 = ms[0]
                s = sum(m["amount"] for m in ms)
                print(f"  {dept_code} {m0['department_name'][:40]:40} | {s:>12,.0f} kr | {len(ms)} poster")

            # Beløp per eiendom
            by_prop: dict[str, list] = {}
            for m in all_matches:
                pid = m["matched_property_id"]
                if pid not in by_prop:
                    by_prop[pid] = []
                by_prop[pid].append(m)
            print(f"\n--- Beløp per matchet eiendom (topp 15) ---")
            for pid, ms in sorted(by_prop.items(), key=lambda x: -sum(m["amount"] for m in x[1]))[:15]:
                m0 = ms[0]
                s = sum(m["amount"] for m in ms)
                print(f"  {m0['matched_property_name'][:50]:50} | {s:>12,.0f} kr | {len(ms)} poster")

            if csv_path and not dry_run and all_matches:
                fieldnames = [
                    "department_code", "department_name", "transaction_id", "period", "account_name",
                    "source_field", "source_value", "supplier_name", "dim2_name", "amount", "invoice_number",
                    "matched_property_id", "matched_property_name", "matched_property_address", "match_score"
                ]
                with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                    writer.writeheader()
                    writer.writerows(all_matches)
                print(f"\nCSV skrevet til: {csv_path} ({len(all_matches)} rader)")

            if apply and all_matches:
                updated = await apply_matches(db, all_matches)
                await db.commit()
                print(f"\n--- OPPDATERING ---")
                print(f"Oppdatert property_id på {updated} transaksjoner i gl_transactions.")
            return len(all_matches), len(all_matches)

        # Enkelt koststed
        dept = dept or "204416"
        name_row = await db.execute(text(
            "SELECT department_name FROM gl_transactions WHERE department_code = :dept AND year = :yr LIMIT 1"
        ), {"dept": dept, "yr": year})
        nr = name_row.fetchone()
        dept_name = nr[0] if nr and nr[0] else ""

        tx_count, match_count, unique_matches = await run_analysis_single(
            db, dept, dept_name, year, all_props
        )

        print(f"\n{'='*70}")
        print(f"Analyse: Koststed {dept} ({year})")
        print(f"{'='*70}")
        print(f"Transaksjoner: {tx_count}")
        print(f"Eiendommer med adresse: {len(all_props)}")
        print(f"Matcher mot eiendommer: {match_count}")

        if unique_matches:
            total_matched = sum(m["amount"] for m in unique_matches)
            print(f"Sum beløp matchet: {total_matched:,.0f} kr")

            by_prop: dict[str, list] = {}
            for m in unique_matches:
                pid = m["matched_property_id"]
                if pid not in by_prop:
                    by_prop[pid] = []
                by_prop[pid].append(m)

            print(f"\n--- Beløp per matchet eiendom ---")
            for pid, ms in sorted(by_prop.items(), key=lambda x: -sum(m["amount"] for m in x[1])):
                m0 = ms[0]
                s = sum(m["amount"] for m in ms)
                print(f"  {m0['matched_property_name'][:50]:50} | {s:>14,.0f} kr | {len(ms)} poster")

            print(f"\n--- Eksempelmatcher (første 15) ---")
            for m in unique_matches[:15]:
                print(f"  {m['source_value'][:40]:40} -> {m['matched_property_name'][:35]:35} (score {m['match_score']}) | {m['amount']:,.0f} kr")

            if csv_path and not dry_run:
                fieldnames = [
                    "department_code", "department_name", "transaction_id", "period", "account_name",
                    "source_field", "source_value", "supplier_name", "dim2_name", "amount", "invoice_number",
                    "matched_property_id", "matched_property_name", "matched_property_address", "match_score"
                ]
                with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                    writer.writeheader()
                    writer.writerows(unique_matches)
                print(f"\nCSV skrevet til: {csv_path}")

            if apply and unique_matches:
                updated = await apply_matches(db, unique_matches)
                await db.commit()
                print(f"\n--- OPPDATERING ---")
                print(f"Oppdatert property_id på {updated} transaksjoner i gl_transactions.")
        else:
            print("\nIngen matcher funnet.")

        return tx_count, match_count


def main():
    parser = argparse.ArgumentParser(description="Analyser kostnader uten eiendom – adresse-matching")
    parser.add_argument("--dept", help="Koststedskode (ignoreres ved --all)")
    parser.add_argument("--all", action="store_true", help="Kjør for alle koststeder uten eiendom")
    parser.add_argument("--year", type=int, default=2025, help="År")
    parser.add_argument("--csv", help="CSV-fil for eksport")
    parser.add_argument("--dry-run", action="store_true", help="Kjør uten å skrive CSV")
    parser.add_argument("--apply", action="store_true", help="Oppdater gl_transactions.property_id for matcher")
    args = parser.parse_args()

    dept = None if args.all else (args.dept or "204416")
    asyncio.run(run_analysis(dept, args.year, args.csv, args.dry_run, args.all, args.apply))


if __name__ == "__main__":
    main()
