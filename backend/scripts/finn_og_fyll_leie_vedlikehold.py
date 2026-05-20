#!/usr/bin/env python3
"""
Finn eiendommer som mangler Leie (YTD) eller Vedlikehold, og fyll med syntetisk data.
Med --all: berik ALLE eiendommer (sikrer at hver har financials; fyll manglende).

- Leie (YTD) = sum av aktive kontrakters amount_per_year.
- Vedlikehold = total_manual_expenses + total_spend_csv (eller total_maintenance).

Syntetisk logikk:
- Vedlikehold: utgifter med norske typer som cost_analysis forstår (Strøm og oppvarming, Renhold, etc.).
- Leie: Estimat fra areal (NOK/kvm) eller vedlikehold * multiplikator.

Kjør fra backend:
  python3 scripts/finn_og_fyll_leie_vedlikehold.py --dry-run
  python3 scripts/finn_og_fyll_leie_vedlikehold.py
  python3 scripts/finn_og_fyll_leie_vedlikehold.py --all    # berik alle eiendommer
"""

import sys
import os
import asyncio
import json
import random
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import text
from app.db.session import SessionLocal

# Norske utgiftstyper som cost_analysis_service forstår (EXPENSE_CATEGORY_MAP)
# Fordeling: drift ~50%, eiendom/felles ~35%, investering ~15%
SYNTHETIC_EXPENSE_TYPES = [
    {"type": "Strøm og oppvarming", "share": 0.22, "supplier": "Strømleverandør"},
    {"type": "Renhold lokaler", "share": 0.18, "supplier": "Renholdstjenester"},
    {"type": "Fellesutgifter", "share": 0.25, "supplier": "Fellesutgifter"},
    {"type": "Reparasjon og vedlikehold leide lokaler", "share": 0.15, "supplier": "Vedlikehold"},
    {"type": "Renovasjon, vann, avløp o.l.", "share": 0.10, "supplier": "Kommunale tjenester"},
    {"type": "Annen kostnad lokaler", "share": 0.05, "supplier": "Diverse"},
    {"type": "Oppgradering og påkostning leide lokaler - under kr 50 000", "share": 0.05, "supplier": "Vedlikehold"},
]

# Estimat leie NOK/kvm når vi ikke har kontrakter (lavt konservativt)
RENT_NOK_PER_SQM = 1200
RENT_VARIANCE = 0.25

# Når vedlikehold > 0 men leie = 0: anta at kostnader er ~10–15 % av leie -> leie ≈ kostnader * 8
RENT_FROM_COST_MULTIPLIER = 8


def _parse_ext(row):
    ext = row.get("external_data")
    if ext is None:
        return {}
    if isinstance(ext, str):
        try:
            return json.loads(ext) if ext else {}
        except Exception:
            return {}
    return dict(ext)


def _vedlikehold(ext):
    fin = ext.get("financials") or {}
    total_m = float(fin.get("total_manual_expenses") or 0)
    total_csv = float(fin.get("total_spend_csv") or 0)
    total_main = fin.get("total_maintenance")
    if total_main is not None:
        try:
            return float(total_main)
        except (TypeError, ValueError):
            pass
    return total_m + total_csv


def _area(ext, total_area_field):
    try:
        if total_area_field is not None and float(total_area_field) > 0:
            return float(total_area_field)
    except (TypeError, ValueError):
        pass
    try:
        v = ext.get("area") or ext.get("sqm") or ext.get("total_area") or 0
        return float(v) if v else 500.0
    except (TypeError, ValueError):
        return 500.0


def _generate_synthetic_expenses(area_sqm):
    """Generer utgifter med norske typer som cost_analysis forstår. Basert på areal (NOK/m²)."""
    # Total vedlikehold per m² (lavt konservativt)
    base_per_sqm = random.uniform(400, 700)
    total_budget = area_sqm * base_per_sqm
    today = datetime.now().strftime("%Y-%m-%d")
    # Fordel med små variasjoner; normaliser slik at sum = 1
    shares = [cfg["share"] * random.uniform(0.9, 1.1) for cfg in SYNTHETIC_EXPENSE_TYPES]
    s = sum(shares)
    shares = [x / s for x in shares]
    expenses = []
    for cfg, share in zip(SYNTHETIC_EXPENSE_TYPES, shares):
        amount = round(total_budget * share, 2)
        expenses.append({
            "type": cfg["type"],
            "account": cfg["type"],
            "supplier": cfg.get("supplier", "Ukjent"),
            "provider": cfg.get("supplier", "Ukjent"),
            "amount": amount,
            "date": today,
            "is_synthetic": True,
        })
    total = sum(e["amount"] for e in expenses)
    return expenses, round(total, 2)


def _estimate_rent(area_sqm, vedlikehold_total):
    if vedlikehold_total and vedlikehold_total > 0:
        return round(vedlikehold_total * RENT_FROM_COST_MULTIPLIER * random.uniform(0.9, 1.1), 0)
    return round(area_sqm * RENT_NOK_PER_SQM * random.uniform(1 - RENT_VARIANCE, 1 + RENT_VARIANCE), 0)


async def run(dry_run: bool, all_properties: bool = False):
    async with SessionLocal() as db:
        # Rent per property (aktive kontrakter)
        rent_sql = text("""
            SELECT u.property_id, COALESCE(SUM(
                (NULLIF(TRIM(c.amount->>'amount_per_year'), ''))::numeric
            ), 0) AS rent_ytd
            FROM units u
            JOIN contracts c ON c.unit_id = u.unit_id
            WHERE c.status = 'active'
            GROUP BY u.property_id
        """)
        rent_result = await db.execute(rent_sql)
        rent_by_id = {str(r[0]): float(r[1]) for r in rent_result.fetchall()}

        # Alle eiendommer med external_data
        props_sql = text("""
            SELECT property_id, name, address, total_area, external_data
            FROM properties
            ORDER BY name
        """)
        props_result = await db.execute(props_sql)
        rows = [dict(r) for r in props_result.mappings().all()]

    # Bygg liste: (property_id, name, rent_ytd, vedlikehold, area, ext)
    out = []
    for r in rows:
        pid = str(r["property_id"])
        ext = _parse_ext(r)
        ved = _vedlikehold(ext)
        rent = rent_by_id.get(pid, 0.0)
        area = _area(ext, r.get("total_area"))
        out.append({
            "property_id": pid,
            "name": r.get("name") or "",
            "address": r.get("address") or "",
            "rent_ytd": rent,
            "vedlikehold": ved,
            "area": area,
            "external_data": ext,
        })

    missing_rent = [x for x in out if x["rent_ytd"] == 0]
    missing_ved = [x for x in out if x["vedlikehold"] == 0]
    missing_either = [x for x in out if x["rent_ytd"] == 0 or x["vedlikehold"] == 0]
    # Med --all: inkluder alle som mangler financials-struktur eller har 0
    to_fill = list(missing_either) if not all_properties else [
        x for x in out if x["rent_ytd"] == 0 or x["vedlikehold"] == 0 or not (x["external_data"] or {}).get("financials")
    ]

    print()
    print("=" * 70)
    print("EIendommer som får syntetisk berikelse" + (" (--all: alle som mangler noe)" if all_properties else ""))
    print("=" * 70)
    print(f"Totalt eiendommer:        {len(out)}")
    print(f"Med 0 Leie (YTD):         {len(missing_rent)}")
    print(f"Med 0 Vedlikehold:       {len(missing_ved)}")
    print(f"Skal fylles:              {len(to_fill)}")
    print()

    if not to_fill:
        print("Ingen eiendommer trenger syntetisk fyll.")
        return

    # Fyll syntetisk for hver
    updates = []
    for x in to_fill:
        ext = dict(x["external_data"]) if x["external_data"] else {}
        if "financials" not in ext:
            ext["financials"] = {}
        fin = dict(ext["financials"])
        area = x["area"]
        changed = False

        # Vedlikehold = 0 -> generer manual_expenses (norske typer for cost_analysis)
        if x["vedlikehold"] == 0:
            expenses, total = _generate_synthetic_expenses(area)
            fin["manual_expenses"] = expenses
            fin["total_manual_expenses"] = total
            fin["total_spend_csv"] = 0  # backend summerer total_manual_expenses + total_spend_csv
            ext["data_source"] = ext.get("data_source") or "synthetic"
            changed = True

        # Leie = 0 -> sett rent_summary (estimat) slik at API/visning kan bruke det
        if x["rent_ytd"] == 0:
            ved_now = fin.get("total_manual_expenses") or 0
            try:
                ved_now = float(ved_now)
            except (TypeError, ValueError):
                ved_now = 0
            rent_est = _estimate_rent(area, ved_now)
            fin["rent_summary"] = rent_est
            fin["synthetic_rent_ytd"] = True
            changed = True

        if changed:
            ext["financials"] = fin
            updates.append({"property_id": x["property_id"], "name": x["name"], "external_data": ext})

    # Rapporter
    print("-" * 70)
    print("Eiendommer som får syntetisk fyll")
    print("-" * 70)
    for u in updates[:30]:
        print(f"  {u['name']}")
        print(f"    property_id: {u['property_id']}")
    if len(updates) > 30:
        print(f"  ... og {len(updates) - 30} til")
    print()

    if dry_run:
        print("(Dry-run: ingen endringer skrevet til DB.)")
        return

    # Skriv til DB (raw UPDATE for å unngå å laste ORM-modeller)
    async with SessionLocal() as db:
        for u in updates:
            await db.execute(
                text("UPDATE properties SET external_data = CAST(:ed AS jsonb) WHERE property_id = :pid"),
                {"ed": json.dumps(u["external_data"]), "pid": u["property_id"]}
            )
        await db.commit()
    print(f"Oppdatert {len(updates)} eiendommer i databasen.")
    print()
    print("Merk: Leie (YTD) vises i frontend fra kontrakter. Syntetisk leie er lagret i")
    print("external_data.financials.rent_summary og .synthetic_rent_ytd – evt. vis som fallback i UI.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Berik eiendommer med syntetisk leie/vedlikehold der data mangler")
    parser.add_argument("--dry-run", action="store_true", help="Kun rapporter, ikke skriv til DB")
    parser.add_argument("--all", dest="all_properties", action="store_true",
                        help="Inkluder alle eiendommer som mangler financials eller har 0 leie/vedlikehold")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, all_properties=args.all_properties))
