"""
Rebuild BEFS 2026 predictions using regional growth rates (reverse-engineered from økonomi).

Methodology:
- Source: kontant_2025 (actual 2025 expenses per property/month/category)
- Apply regional growth rates derived from økonomi's finance_dept_2026 / kontant_2025 ratio
- New data_source: 'okonomi_regional_2026'

Regional growth rates (from ratio analysis 2026-05-07):
  Øst:       +17.01%  (×1.1701)
  Sør:       -10.78%  (×0.8922)
  Nord:      +26.62%  (×1.2662)
  Vest:      -14.92%  (×0.8508)
  Midt-Norge: +2.13%  (×1.0213)
  Bufdir:    +14.23%  (×1.1423)
  Nasjonal:   +3.50%  (×1.0350)  ← fallback for NULL/unknown region

These rates were reverse-engineered by comparing økonomi's finance_dept_2026 budget
against kontant_2025 actual spend, grouped by region via koststed_mapping.

Kjøres: DATABASE_URL=... python3 backend/scripts/rebuild_befs_2026_regional.py
"""
import sys
import uuid
import asyncio
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres.vwvhxcqxadblrftuvsds:Sunnyowl_6533@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
)

from sqlalchemy import text
from app.db.session import SessionLocal

# Regional growth rates (ratio økonomi 2026 / regnskap 2025)
REGIONAL_RATES: dict[str, float] = {
    "Øst":        1.1701,
    "Sør":        0.8922,
    "Nord":       1.2662,
    "Vest":       0.8508,
    "Midt-Norge": 1.0213,
    "Bufdir":     1.1423,
}
FALLBACK_RATE = 1.0350  # Nasjonal / ukjent region

NEW_DATA_SOURCE = "okonomi_regional_2026"
OLD_DATA_SOURCE = "kontant_2025_plus_3.5pct"


async def rebuild():
    async with SessionLocal() as db:
        # 1. Hent region per property_id fra koststed_mapping
        print("Henter region per property_id fra koststed_mapping...")
        res = await db.execute(text("""
            SELECT DISTINCT property_id::text, region
            FROM koststed_mapping
            WHERE property_id IS NOT NULL AND region IS NOT NULL
        """))
        prop_region: dict[str, str] = {}
        for r in res.fetchall():
            if r.property_id not in prop_region:
                prop_region[r.property_id] = r.region
        print(f"  {len(prop_region)} eiendommer med region")

        # 2. Hent alle kontant_2025-rader aggregert per property/month/category
        print("Henter kontant_2025 aggregert per property/måned/kategori...")
        res = await db.execute(text("""
            SELECT
                property_id::text,
                month,
                category,
                SUM(amount)::float AS total_amount
            FROM finance_budget
            WHERE data_source = 'kontant_2025'
              AND property_id IS NOT NULL
              AND year = 2025
            GROUP BY property_id, month, category
        """))
        rows = res.fetchall()
        print(f"  {len(rows)} rader (property/måned/kategori-kombinasjoner)")

        # 3. Slett eksisterende rader for begge data_source i budget-tabellen for 2026
        print(f"Sletter eksisterende budget-rader for year=2026, data_source IN ('{OLD_DATA_SOURCE}', '{NEW_DATA_SOURCE}')...")
        del_res = await db.execute(text(f"""
            DELETE FROM budget
            WHERE year = 2026
              AND data_source IN ('{OLD_DATA_SOURCE}', '{NEW_DATA_SOURCE}')
        """))
        print(f"  Slettet {del_res.rowcount} rader")

        # 4. Bygg nye rader med regionale rater
        inserted = 0
        missing_region = set()
        rate_stats: dict[str, int] = {}

        # Batch-insert for ytelse
        batch: list[dict] = []

        for r in rows:
            prop_id = r.property_id
            region = prop_region.get(prop_id)
            if region:
                rate = REGIONAL_RATES.get(region, FALLBACK_RATE)
                if region not in REGIONAL_RATES:
                    missing_region.add(f"{prop_id}:{region}")
            else:
                rate = FALLBACK_RATE
                missing_region.add(f"{prop_id}:NULL")

            region_label = region or "Nasjonal"
            rate_stats[region_label] = rate_stats.get(region_label, 0) + 1

            new_amount = round(float(r.total_amount) * rate, 4)

            batch.append({
                "budget_id": str(uuid.uuid4()),
                "property_id": prop_id,
                "year": 2026,
                "month": r.month,
                "category": r.category,
                "amount": new_amount,
                "is_synthetic": True,
                "data_source": NEW_DATA_SOURCE,
            })

        # Kjør insert én og én (asyncpg-kompatibelt — ingen :: cast på bind params)
        for row in batch:
            await db.execute(text("""
                INSERT INTO budget (budget_id, property_id, year, month, category, amount, is_synthetic, data_source)
                VALUES (
                    CAST(:budget_id AS uuid),
                    CAST(:property_id AS uuid),
                    :year,
                    :month,
                    :category,
                    :amount,
                    :is_synthetic,
                    :data_source
                )
            """), row)
            inserted += 1
            if inserted % 500 == 0:
                print(f"  ... {inserted}/{len(batch)} rader insertet")

        await db.commit()

    print(f"\n✅ Ferdig: {inserted} nye rader med data_source='{NEW_DATA_SOURCE}'")
    print(f"\nRader per region:")
    for reg, cnt in sorted(rate_stats.items()):
        rate = REGIONAL_RATES.get(reg, FALLBACK_RATE)
        pct = (rate - 1) * 100
        print(f"  {reg:15s} {cnt:5d} rader  (×{rate:.4f} = {pct:+.2f}%)")

    if missing_region:
        print(f"\n⚠️  {len(missing_region)} properties manglet region-match (brukte fallback {FALLBACK_RATE}×):")
        for x in sorted(missing_region)[:20]:
            print(f"    {x}")

    # 5. Verifiser totaler
    async with SessionLocal() as db:
        res = await db.execute(text(f"""
            SELECT
                category,
                SUM(amount)::float AS total,
                COUNT(DISTINCT property_id) AS props,
                COUNT(*) AS rader
            FROM budget
            WHERE year = 2026 AND data_source = '{NEW_DATA_SOURCE}'
            GROUP BY category
            ORDER BY total DESC
        """))
        print(f"\nTotaler per kategori (budget year=2026, data_source='{NEW_DATA_SOURCE}'):")
        grand_total = 0.0
        for r in res.fetchall():
            print(f"  {r.category:15s}  {r.total/1e6:8.2f} MNOK  ({r.props} props, {r.rader} rader)")
            grand_total += r.total
        print(f"  {'TOTALT':15s}  {grand_total/1e6:8.2f} MNOK")

        # Sammenlign med gammel metode
        res2 = await db.execute(text("""
            SELECT SUM(amount)::float AS total FROM budget
            WHERE year = 2026 AND data_source = 'kontant_2025_plus_3.5pct'
        """))
        old_total = res2.scalar() or 0
        if old_total:
            print(f"\n  (Gammel 3.5%-metode: {old_total/1e6:.2f} MNOK)")

        # Sammenlign med kontant_2025
        res3 = await db.execute(text("""
            SELECT SUM(amount)::float AS total FROM finance_budget
            WHERE year = 2025 AND data_source = 'kontant_2025'
        """))
        k2025 = res3.scalar() or 0
        print(f"  (Kontant 2025 total:    {k2025/1e6:.2f} MNOK)")
        if k2025 > 0:
            print(f"  (Vekst ny metode:      {(grand_total/k2025 - 1)*100:+.2f}%)")


if __name__ == "__main__":
    asyncio.run(rebuild())
