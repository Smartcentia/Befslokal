"""
Deep dive: konto 6630 og Statsbygg-leverandør i 2022.
Bruker statement_cache_size=0 for pgbouncer-kompatibilitet.
"""
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://", "postgresql+asyncpg://"
)

async def q(conn, sql):
    return await conn.execute(text(sql))

async def main():
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"statement_cache_size": 0},
    )
    async with engine.connect() as conn:

        print("=== konto 6630 per år ===")
        r = await q(conn, """
            SELECT ar, COUNT(*) AS linjer, ROUND(SUM(belop)) AS total,
                   ROUND(AVG(belop)) AS snitt
            FROM gl_transactions WHERE konto = '6630' AND ar BETWEEN 2021 AND 2025
            GROUP BY ar ORDER BY ar
        """)
        for row in r:
            print(f"  {row.ar}: {row.linjer} linjer  sum={int(row.total or 0):>12,}  snitt/linje={int(row.snitt or 0):>8,}")

        print()
        print("=== konto 6630 topp leverandører 2022 ===")
        r = await q(conn, """
            SELECT COALESCE(leverandor_navn, '(ingen)') AS lev,
                   COUNT(*) AS antall, ROUND(SUM(belop)) AS tot
            FROM gl_transactions WHERE konto = '6630' AND ar = 2022
            GROUP BY leverandor_navn ORDER BY tot DESC LIMIT 15
        """)
        for row in r:
            print(f"  {(row.lev or '')[:50]:<50}  {row.antall:>5}  {int(row.tot or 0):>12,}")

        print()
        print("=== konto 6630 topp leverandører 2023 ===")
        r = await q(conn, """
            SELECT COALESCE(leverandor_navn, '(ingen)') AS lev,
                   COUNT(*) AS antall, ROUND(SUM(belop)) AS tot
            FROM gl_transactions WHERE konto = '6630' AND ar = 2023
            GROUP BY leverandor_navn ORDER BY tot DESC LIMIT 15
        """)
        for row in r:
            print(f"  {(row.lev or '')[:50]:<50}  {row.antall:>5}  {int(row.tot or 0):>12,}")

        print()
        print("=== Statsbygg drift-kontoer 2021-2025 ===")
        r = await q(conn, """
            SELECT ar, konto, konto_navn, ROUND(SUM(belop)) AS tot
            FROM gl_transactions
            WHERE leverandor_navn ILIKE '%statsbygg%'
              AND (konto BETWEEN '6320' AND '6399' OR konto = '6630')
              AND ar BETWEEN 2021 AND 2025
            GROUP BY ar, konto, konto_navn ORDER BY ar, tot DESC
        """)
        for row in r:
            print(f"  {row.ar}  {row.konto}  {(row.konto_navn or '')[:40]:<40}  {int(row.tot or 0):>12,}")

        print()
        print("=== bilagsart for konto 6630 i 2022 ===")
        r = await q(conn, """
            SELECT COALESCE(bilagsart, '(ingen)') AS ba,
                   COUNT(*) AS antall, ROUND(SUM(belop)) AS tot
            FROM gl_transactions WHERE konto = '6630' AND ar = 2022
            GROUP BY bilagsart ORDER BY tot DESC
        """)
        for row in r:
            print(f"  bilagsart={row.ba:<6}  linjer={row.antall:>5}  sum={int(row.tot or 0):>12,}")

        print()
        print("=== Hvilke koststed/avdeling har størst 6630 i 2022? ===")
        r = await q(conn, """
            SELECT COALESCE(dim1_koststed, '(ingen)') AS koststed,
                   COALESCE(dim1_koststed_navn, '') AS koststed_navn,
                   COUNT(*) AS antall, ROUND(SUM(belop)) AS tot
            FROM gl_transactions WHERE konto = '6630' AND ar = 2022
            GROUP BY dim1_koststed, dim1_koststed_navn ORDER BY tot DESC LIMIT 15
        """)
        for row in r:
            print(f"  {row.koststed:<10} {(row.koststed_navn or '')[:40]:<40}  {row.antall:>5}  {int(row.tot or 0):>12,}")

        print()
        print("=== Er det negative beløp (kreditnota/ompostering) i 6630 2022? ===")
        r = await q(conn, """
            SELECT
              CASE WHEN belop > 0 THEN 'Positiv' ELSE 'Negativ/null' END AS retning,
              COUNT(*) AS antall, ROUND(SUM(belop)) AS tot
            FROM gl_transactions WHERE konto = '6630' AND ar = 2022
            GROUP BY retning ORDER BY retning
        """)
        for row in r:
            print(f"  {row.retning}  linjer={row.antall:>5}  sum={int(row.tot or 0):>12,}")

    await engine.dispose()

asyncio.run(main())
