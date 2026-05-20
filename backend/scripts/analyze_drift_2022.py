"""
Analyze why Drift- og vedlikeholdskostnader was 133.8 MNOK in 2022
vs 92-104 MNOK in 2023-2025.

Account codes for drift/vedlikehold (from procurement.py mapping):
  6320-6399: facility operations (not lease)
  6630: other facility costs
"""
import asyncio
import os
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

DRIFT_ACCOUNTS_SQL = """
(konto >= '6320' AND konto <= '6399') OR konto = '6630'
"""

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.connect() as conn:

        # 1. Totaler per år + syntetisk-flagg
        print("=" * 70)
        print("1. TOTALER PER ÅR (drift-kontoer 6320-6399 + 6630)")
        print("=" * 70)
        result = await conn.execute(text(f"""
            SELECT ar, COUNT(*) AS linjer, ROUND(SUM(belop)) AS total
            FROM gl_transactions
            WHERE ({DRIFT_ACCOUNTS_SQL})
              AND ar BETWEEN 2021 AND 2025
            GROUP BY ar
            ORDER BY ar
        """))
        for row in result:
            print(f"  {row.ar}: {row.linjer:,} linjer  →  {int(row.total or 0):>15,} NOK")

        # 2. Konto-fordeling per år
        print()
        print("=" * 70)
        print("2. TOPP KONTOER 2022 vs 2023-2025 (syntetiske ekskl.)")
        print("=" * 70)
        result = await conn.execute(text(f"""
            SELECT ar, konto, konto_navn,
                   COUNT(*) AS linjer,
                   ROUND(SUM(belop)) AS total
            FROM gl_transactions
            WHERE ({DRIFT_ACCOUNTS_SQL})
              AND ar IN (2022, 2023, 2024, 2025)
                        GROUP BY ar, konto, konto_navn
            ORDER BY ar, total DESC
        """))
        current_year = None
        for row in result:
            if row.ar != current_year:
                current_year = row.ar
                print(f"\n  --- {current_year} ---")
            navn = (row.konto_navn or "")[:35]
            print(f"  {row.konto}  {navn:<35}  {row.linjer:>5} linjer  {int(row.total or 0):>12,} NOK")

        # 3. Topp leverandører 2022 vs 2023
        print()
        print("=" * 70)
        print("3. TOPP 15 LEVERANDØRER 2022 vs 2023 (ikke-syntetiske)")
        print("=" * 70)
        for year in [2022, 2023]:
            print(f"\n  --- {year} ---")
            result = await conn.execute(text(f"""
                SELECT COALESCE(leverandor_navn, '(ingen)') AS leverandor,
                       COUNT(*) AS linjer,
                       ROUND(SUM(belop)) AS total
                FROM gl_transactions
                WHERE ({DRIFT_ACCOUNTS_SQL})
                  AND ar = :year
                                GROUP BY leverandor_navn
                ORDER BY total DESC
                LIMIT 15
            """), {"year": year})
            for row in result:
                lev = (row.leverandor or "")[:45]
                print(f"  {lev:<45}  {row.linjer:>5}  {int(row.total or 0):>12,} NOK")

        # 4. Eiendommer som drev mest i 2022 men ikke i 2023
        print()
        print("=" * 70)
        print("4. EIENDOMMER – 2022 vs 2023 (topp 20 per år)")
        print("=" * 70)
        result = await conn.execute(text(f"""
            SELECT g.ar,
                   COALESCE(p.name, p.property_name, 'INGEN EIENDOM') AS eiendom,
                   COUNT(*) AS linjer,
                   ROUND(SUM(g.belop)) AS total
            FROM gl_transactions g
            LEFT JOIN properties p ON g.property_id::text = p.id::text
            WHERE ({DRIFT_ACCOUNTS_SQL.replace('konto', 'g.konto')})
              AND g.ar IN (2022, 2023)
            GROUP BY g.ar, p.name, p.property_name, g.property_id
            ORDER BY g.ar, total DESC
            LIMIT 40
        """))
        current_year = None
        count = 0
        for row in result:
            if row.ar != current_year:
                current_year = row.ar
                count = 0
                print(f"\n  --- {current_year} ---")
            count += 1
            if count <= 20:
                eiendom = (row.eiendom or "")[:55]
                print(f"  {eiendom:<55}  {row.linjer:>5}  {int(row.total or 0):>12,} NOK")

        # 5. Sjekk bilagsart-fordeling 2022 – er det omposteringer/engangsbilag?
        print()
        print("=" * 70)
        print("5. BILAGSART-FORDELING 2022 (alle drift-kontoer)")
        print("=" * 70)
        result = await conn.execute(text(f"""
            SELECT COALESCE(bilagsart, '(ingen)') AS bilagsart,
                   COUNT(*) AS linjer,
                   ROUND(SUM(belop)) AS total
            FROM gl_transactions
            WHERE ({DRIFT_ACCOUNTS_SQL})
              AND ar = 2022
                        GROUP BY bilagsart
            ORDER BY total DESC
        """))
        for row in result:
            print(f"  Bilagsart {row.bilagsart:<8}  {row.linjer:>6} linjer  {int(row.total or 0):>12,} NOK")

        # 6. Månedlig fordeling 2022 – spesielt store måneder?
        print()
        print("=" * 70)
        print("6. MÅNEDLIG FORDELING 2022 (drift-kontoer)")
        print("=" * 70)
        result = await conn.execute(text(f"""
            SELECT
                EXTRACT(MONTH FROM bilagsdato)::int AS maned,
                COUNT(*) AS linjer,
                ROUND(SUM(belop)) AS total
            FROM gl_transactions
            WHERE ({DRIFT_ACCOUNTS_SQL})
              AND ar = 2022
              AND bilagsdato IS NOT NULL
                        GROUP BY maned
            ORDER BY maned
        """))
        for row in result:
            bar = "█" * min(int((row.total or 0) / 1_000_000), 30)
            print(f"  Måned {row.maned:>2}: {int(row.total or 0):>12,} NOK  {bar}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
