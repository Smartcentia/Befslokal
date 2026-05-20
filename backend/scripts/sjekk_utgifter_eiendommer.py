#!/usr/bin/env python3
"""
Sjekk løpende utgifter per eiendom
=================================
Finner eiendommer som mangler utgifter (0 poster) og eiendommer med uvanlig mange poster.
Kjør fra backend: python scripts/sjekk_utgifter_eiendommer.py
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


def _count_expenses_from_row(row):
    ext = row.get("external_data") or {}
    if isinstance(ext, str):
        try:
            ext = json.loads(ext) if ext else {}
        except Exception:
            ext = {}
    expenses = ext.get("financials", {}).get("manual_expenses", [])
    return len(expenses), expenses


async def run():
    async with SessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT property_id, name, address, external_data FROM properties ORDER BY name"
            )
        )
        raw_rows = result.mappings().all()

    # (property_id, name, address, count, expenses_list)
    rows = []
    for r in raw_rows:
        n, expenses = _count_expenses_from_row(dict(r))
        rows.append(
            (r["property_id"], r["name"] or "", r["address"] or "", n, expenses)
        )

    total_props = len(rows)
    counts = [r[3] for r in rows]  # r = (property_id, name, address, count, expenses)
    no_expenses = [r for r in rows if r[3] == 0]
    with_expenses = [r for r in rows if r[3] > 0]

    # "For mange": over 90. percentil av antall poster (minst 1), eller fast terskel 50+
    if with_expenses:
        sorted_counts = sorted([r[3] for r in with_expenses], reverse=True)
        idx_90 = max(0, int(len(sorted_counts) * 0.10) - 1)  # top 10% = "mange"
        threshold_90 = sorted_counts[idx_90] if sorted_counts else 0
        threshold_cap = 50
        too_many_threshold = max(threshold_90, threshold_cap)
        too_many = [r for r in rows if r[3] >= too_many_threshold]
    else:
        too_many_threshold = 0
        too_many = []

    # ---- Rapporter ----
    print()
    print("=" * 60)
    print("SJEKK LØPENDE UTGIFTER PER EIENDOM")
    print("=" * 60)
    print(f"Totalt antall eiendommer: {total_props}")
    print(f"Eiendommer med minst 1 utgift: {len(with_expenses)}")
    print(f"Eiendommer uten utgifter:     {len(no_expenses)}")
    if with_expenses:
        print(f"Terskel «for mange» (>=):     {too_many_threshold} poster")
    print()

    # Mangler utgifter
    print("-" * 60)
    print("Eiendommer UTEN løpende utgifter (mangler)")
    print("-" * 60)
    if not no_expenses:
        print("Ingen – alle eiendommer har minst én utgiftspost.")
    else:
        for pid, name, addr, n, _ in sorted(no_expenses, key=lambda x: x[1]):
            name = name or "(uten navn)"
            print(f"  {name}")
            print(f"    Adresse: {addr}")
            print(f"    property_id: {pid}")
            print()
    print()

    # For mange
    print("-" * 60)
    print(f"Eiendommer med MANGE utgifter (>= {too_many_threshold} poster)")
    print("-" * 60)
    if not too_many:
        print("Ingen – ingen eiendommer over terskelen.")
    else:
        for pid, name, addr, n, expenses in sorted(too_many, key=lambda x: -x[3]):
            name = name or "(uten navn)"
            total_kr = sum(float(e.get("amount", 0) or 0) for e in expenses)
            print(f"  {name}")
            print(f"    Adresse: {addr}")
            print(f"    Antall utgiftsposter: {n}  (sum: {total_kr:,.0f} kr)")
            print(f"    property_id: {pid}")
            print()
    print()

    # Fordeling (valgfritt)
    print("-" * 60)
    print("Fordeling antall utgifter per eiendom")
    print("-" * 60)
    buckets = defaultdict(int)
    for r in rows:
        n = r[3]
        if n == 0:
            buckets["0"] += 1
        elif n <= 5:
            buckets["1–5"] += 1
        elif n <= 20:
            buckets["6–20"] += 1
        elif n <= 50:
            buckets["21–50"] += 1
        else:
            buckets["51+"] += 1
    for label in ["0", "1–5", "6–20", "21–50", "51+"]:
        print(f"  {label:>6} poster: {buckets[label]} eiendommer")
    print()
    print("Ferdig.")


if __name__ == "__main__":
    asyncio.run(run())
