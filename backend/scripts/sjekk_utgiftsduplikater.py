#!/usr/bin/env python3
"""
Sjekk duplikater i løpende utgifter (manual_expenses) per eiendom
=================================================================
Rapport-only: finner mulige duplikater (samme type, beløp, leverandør, dato).
Endrer ikke databasen. For å fjerne duplikater, kjør: remove_financial_duplicates.py

Kjør fra backend: python3 scripts/sjekk_utgiftsduplikater.py
"""

import sys
import os
import asyncio
import json
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import text
from app.db.session import SessionLocal


def _get_expenses_from_row(row):
    ext = row.get("external_data") or {}
    if isinstance(ext, str):
        try:
            ext = json.loads(ext) if ext else {}
        except Exception:
            ext = {}
    return ext.get("financials", {}).get("manual_expenses", [])


def _signature(exp):
    """Unik nøkkel for en utgiftspost (brukes for å oppdage duplikater)."""
    amount = exp.get("amount")
    try:
        amount = float(amount) if amount is not None else 0.0
    except (ValueError, TypeError):
        amount = 0.0
    return (
        amount,
        (exp.get("type") or "Ukjent").strip(),
        (exp.get("provider") or "Ukjent").strip(),
        (exp.get("date") or "Unknown").strip(),
    )


def _find_duplicates(expenses):
    """Returner (antall unike duplikater, liste med (signatur, antall forekomster))."""
    seen = defaultdict(list)  # sig -> list of indices
    for i, exp in enumerate(expenses):
        sig = _signature(exp)
        seen[sig].append(i)
    duplicates = [(sig, indices) for sig, indices in seen.items() if len(indices) > 1]
    return duplicates


async def run():
    async with SessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT property_id, name, address, external_data FROM properties ORDER BY name"
            )
        )
        raw_rows = result.mappings().all()

    total_props_with_expenses = 0
    props_with_duplicates = []
    total_duplicate_groups = 0
    total_duplicate_entries = 0  # antall poster som er «ekstra» (duplikater)

    for r in raw_rows:
        expenses = _get_expenses_from_row(dict(r))
        if not expenses:
            continue
        total_props_with_expenses += 1
        dups = _find_duplicates(expenses)
        if not dups:
            continue
        # Antall «ekstra» poster = for hver gruppe (count - 1)
        n_extra = sum(len(indices) - 1 for _, indices in dups)
        total_duplicate_groups += len(dups)
        total_duplicate_entries += n_extra
        props_with_duplicates.append(
            (r["property_id"], r["name"] or "", r["address"] or "", len(expenses), dups, n_extra)
        )

    # ---- Rapporter ----
    print()
    print("=" * 70)
    print("SJEKK DUPLIKATER I LØPENDE UTGIFTER (manual_expenses)")
    print("=" * 70)
    print(f"Eiendommer med utgifter:        {total_props_with_expenses}")
    print(f"Eiendommer med minst 1 duplikat: {len(props_with_duplicates)}")
    print(f"Totalt duplikatgrupper:          {total_duplicate_groups}")
    print(f"Totalt ekstra poster (kan fjernes): {total_duplicate_entries}")
    print()
    print("(Duplikat = samme type, beløp, leverandør og dato.)")
    print()

    if not props_with_duplicates:
        print("Ingen duplikater funnet.")
        print()
        return

    print("-" * 70)
    print("Eiendommer med duplikater (navn, antall utgifter, antall ekstra poster)")
    print("-" * 70)
    for pid, name, addr, n_exp, dups, n_extra in sorted(
        props_with_duplicates, key=lambda x: -x[5]
    ):
        name = name or "(uten navn)"
        print(f"  {name}")
        print(f"    Adresse: {addr}")
        print(f"    Utgiftsposter: {n_exp}  |  Ekstra (duplikater): {n_extra}  |  Duplikatgrupper: {len(dups)}")
        print(f"    property_id: {pid}")
        # Eksempel: vis én duplikatgruppe
        if dups:
            sig, indices = dups[0]
            amount, typ, provider, date = sig
            print(f"    Eksempel duplikat: type={typ!r}, beløp={amount}, leverandør={provider!r}, dato={date!r} ({len(indices)} ganger)")
        print()
    print("-" * 70)
    print("For å Fjerne duplikater (oppdaterer DB):")
    print("  cd backend && python3 scripts/remove_financial_duplicates.py")
    print()
    print("Ferdig.")


if __name__ == "__main__":
    asyncio.run(run())
