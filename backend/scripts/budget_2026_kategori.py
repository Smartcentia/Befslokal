#!/usr/bin/env python3
"""
Budsjett 2026 – kategori-basert estimering fra GL 2025.

Metodikk:
  - Husleie-kontoer:  faktisk 2025 × 1.047  (+4.7% – kontraktsjusteringer)
  - Andre kostnader:  faktisk 2025 × 1.100  (+10.0% – tjenester/materiell)

Kostnadsfordeling:
  84 % av GL-kostnadene er bokført på sentrale Koststed-koder uten property_id.
  Disse er reelle eiendomskostnader (husleie, strøm, renhold m.m.) som bokføres
  sentralt (per region/direktørområde). Disse kostnadene fordeles proporsjonalt
  til kjente eiendommer basert på eiendommens andel av direkte kostnader.

  Husleie fordeles likt over 12 måneder.
  Andre kostnader fordeles med sesongfaktor (høy vinter, lav sommer).

Kjør:
  cd backend
  python3 scripts/budget_2026_kategori.py --dry-run
  python3 scripts/budget_2026_kategori.py
"""

import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path

_backend = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend))
os.chdir(_backend)

from dotenv import load_dotenv
load_dotenv(_backend / ".env")

from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.financial_models import Budget


def is_lease_account(account_name) -> bool:
    if not account_name or not str(account_name).strip():
        return False
    s = str(account_name).strip()
    lease_names = {"Leie lokaler fra Statsbygg", "Leie lokaler andre utleiere",
                   "Leie parkeringsplass", "Leie av lager/naust/garsjer og lignende", "Husleie"}
    if s in lease_names:
        return True
    if s.lower().startswith("leie "):
        return True
    if s.lower() == "husleie":
        return True
    return False


TARGET_YEAR = 2026
SOURCE_YEAR = 2025
HUSLEIE_RATE = 0.047   # +4.7%
DRIFT_RATE   = 0.100   # +10.0%

# Sesongfaktorer for driftskostnader (sum = 12.0)
DRIFT_SEASONAL = {
    1: 1.15, 2: 1.15, 3: 1.05,  # Vinter/vår
    4: 0.95, 5: 0.90, 6: 0.80,  # Vår/sommer
    7: 0.75, 8: 0.80, 9: 0.95,  # Sommer/høst
    10: 1.05, 11: 1.15, 12: 1.15, # Høst/vinter
}

def fmt(v: float) -> str:
    return f"{v:>14,.0f}".replace(",", " ")


async def run(dry_run: bool = False) -> None:
    async with SessionLocal() as db:

        # 0. Bygg dept_code → property_id mapping via raw SQL
        dept_rows = (await db.execute(text(
            "SELECT unit_id_erp, department_code, property_id FROM properties"
        ))).fetchall()
        dept_to_prop = {}
        for r in dept_rows:
            pid = str(r.property_id)
            for code in [r.unit_id_erp, r.department_code]:
                if code and str(code).strip():
                    dept_to_prop[str(code).strip().lstrip("0")] = pid

        # 1. Hent ALL GL 2025 per (property_id / dept_code, account_name)
        rows = (await db.execute(text("""
            SELECT property_id, department_code, account_name,
                   SUM(amount) AS total
            FROM gl_transactions
            WHERE year = :year
            GROUP BY property_id, department_code, account_name
        """), {"year": SOURCE_YEAR})).fetchall()

        # Aggreger per property + orphan-pool (sentrale Koststed-koder)
        by_prop = {}          # pid → {husleie, drift}
        orphan_husleie = 0.0  # sentralt bokført husleie
        orphan_drift   = 0.0  # sentralt bokført drift

        for r in rows:
            amt = float(r.total or 0)
            is_lease = is_lease_account(r.account_name)

            if r.property_id:
                pid = str(r.property_id)
            elif r.department_code:
                norm = str(r.department_code).strip().lstrip("0")
                pid = dept_to_prop.get(norm)
            else:
                pid = None

            if pid:
                if pid not in by_prop:
                    by_prop[pid] = {"husleie": 0.0, "drift": 0.0}
                if is_lease:
                    by_prop[pid]["husleie"] += amt
                else:
                    by_prop[pid]["drift"] += amt
            else:
                # Bokført sentralt – samles i orphan-pool
                if is_lease:
                    orphan_husleie += amt
                else:
                    orphan_drift += amt

        # 2. Fordel orphan-kostnader proporsjonalt til kjente eiendommer
        total_linked_husleie = sum(v["husleie"] for v in by_prop.values())
        total_linked_drift   = sum(v["drift"]   for v in by_prop.values())
        total_linked         = total_linked_husleie + total_linked_drift

        n_props = len(by_prop)

        # Allokér orphan proporsjonalt (basert på eiendommes andel av totale kjente kostnader)
        for pid, cats in by_prop.items():
            prop_share = (cats["husleie"] + cats["drift"]) / total_linked if total_linked else 1.0 / n_props
            cats["husleie"] += orphan_husleie * prop_share
            cats["drift"]   += orphan_drift   * prop_share

        # 3. Bygg budsjettlinjer
        entries = []
        total_husleie_2025 = 0.0
        total_drift_2025   = 0.0
        total_husleie_2026 = 0.0
        total_drift_2026   = 0.0

        seasonal_sum = sum(DRIFT_SEASONAL.values())  # = 12.0

        for pid, cats in by_prop.items():
            h_base = cats["husleie"] * (1 + HUSLEIE_RATE)
            d_base = cats["drift"]   * (1 + DRIFT_RATE)

            total_husleie_2025 += cats["husleie"]
            total_drift_2025   += cats["drift"]
            total_husleie_2026 += h_base
            total_drift_2026   += d_base

            # Husleie: likt fordelt 12 mnd
            h_monthly = h_base / 12.0
            for month in range(1, 13):
                entries.append({
                    "budget_id":    uuid.uuid4(),
                    "property_id":  pid,
                    "year":         TARGET_YEAR,
                    "month":        month,
                    "category":     "husleie",
                    "amount":       round(h_monthly, 2),
                    "is_synthetic": True,
                    "data_source":  f"gl_{SOURCE_YEAR}_husleie+{HUSLEIE_RATE*100:.1f}pct_alloc",
                })

            # Drift: sesongfordelt
            for month in range(1, 13):
                factor = DRIFT_SEASONAL[month] / seasonal_sum
                entries.append({
                    "budget_id":    uuid.uuid4(),
                    "property_id":  pid,
                    "year":         TARGET_YEAR,
                    "month":        month,
                    "category":     "drift",
                    "amount":       round(d_base * factor, 2),
                    "is_synthetic": True,
                    "data_source":  f"gl_{SOURCE_YEAR}_drift+{DRIFT_RATE*100:.1f}pct_alloc",
                })

        # 4. Rapport
        total_2025 = total_husleie_2025 + total_drift_2025
        total_2026 = total_husleie_2026 + total_drift_2026
        total_orphan = orphan_husleie + orphan_drift

        print("\n" + "=" * 70)
        print("BUDSJETT 2026 – KATEGORI-BASERT FRA GL 2025")
        print("=" * 70)
        print(f"\nBasis: GL {SOURCE_YEAR} – {n_props} eiendommer")
        print(f"\nGL 2025 kostnadsoversikt:")
        print(f"  Direkte eiendomslinket:  {fmt(total_linked_husleie + total_linked_drift)} NOK")
        print(f"  Sentrale Koststed-koder: {fmt(total_orphan)} NOK  ← fordelt proporsjonalt")
        print(f"  TOTAL GL 2025:           {fmt(total_2025)} NOK")

        print(f"\n{'Kategori':<22} {'2025 basis':>16} {'Rate':>8} {'2026 budsjett':>16}")
        print("-" * 66)
        print(f"{'Husleie':<22} {fmt(total_husleie_2025)} {HUSLEIE_RATE*100:>7.1f}% {fmt(total_husleie_2026)}")
        print(f"{'Drift/andre kost.':<22} {fmt(total_drift_2025)} {DRIFT_RATE*100:>7.1f}% {fmt(total_drift_2026)}")
        print("-" * 66)
        print(f"{'TOTALT':<22} {fmt(total_2025)}          {fmt(total_2026)}")
        print(f"\nVekst totalt: {(total_2026/total_2025 - 1)*100:.1f}%")
        print(f"Antall budsjettlinjer: {len(entries):,} ({n_props} props × 12 mnd × 2 kat)")
        print(f"\nGammel budsjett (kontrakter): 523 MNOK")
        print(f"Nytt budsjett (GL-basert):    {total_2026/1e6:.0f} MNOK")

        if dry_run:
            print("\n[DRY RUN] Ingen endringer skrevet til database.")
            return

        # 5. Skriv til DB
        print("\nSletter eksisterende budsjett 2026 ...")
        await db.execute(text("DELETE FROM budget WHERE year = :y"), {"y": TARGET_YEAR})

        print(f"Skriver {len(entries):,} linjer ...")
        batch_size = 500
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            await db.execute(Budget.__table__.insert(), batch)

        await db.commit()
        print(f"Ferdig! Budsjett 2026 oppdatert til {total_2026/1e6:.0f} MNOK.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Vis rapport uten å skrive til DB")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
