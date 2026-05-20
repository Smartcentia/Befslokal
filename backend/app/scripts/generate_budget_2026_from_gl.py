"""
Generate 2026 budget entries from GL 2025 transactions.

Strategy:
- Aggregate GL 2025 by (property_id, account_name, month)
- Apply 3.5% inflation
- Insert into budget table for year=2026
- Idempotent: deletes existing gl_2025_baseline entries first

Usage:
    railway run python app/scripts/generate_budget_2026_from_gl.py
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

import app.db.base  # noqa: F401 – loads all models for SQLAlchemy mapper

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

INFLATION = 1.035  # 3.5% KPI-justering
DATA_SOURCE = "gl_2025_baseline"
BUDGET_YEAR = 2026
GL_YEAR = 2025


async def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 1. Delete existing synthetic budget for 2026
        del_res = await db.execute(
            text("DELETE FROM budget WHERE year = :year AND data_source = :src"),
            {"year": BUDGET_YEAR, "src": DATA_SOURCE}
        )
        print(f"Deleted {del_res.rowcount} existing budget rows for {BUDGET_YEAR}/{DATA_SOURCE}")

        # 2. Check GL data availability
        check = await db.execute(
            text("SELECT COUNT(*), SUM(amount) FROM gl_transactions WHERE year = :yr AND amount > 0"),
            {"yr": GL_YEAR}
        )
        row = check.fetchone()
        print(f"GL {GL_YEAR}: {row[0]} transactions, SUM = {row[1]:,.0f} NOK")

        if not row[0]:
            print("ERROR: No GL data for {GL_YEAR}. Aborting.")
            sys.exit(1)

        # 3. Insert budget entries: aggregate by (property_id, account_name, month)
        insert_sql = text("""
            INSERT INTO budget (budget_id, property_id, year, month, category, amount,
                                is_synthetic, data_source, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                property_id,
                :budget_year,
                COALESCE(month, 1),
                account_name,
                ROUND(SUM(amount) * :inflation, 2),
                true,
                :data_source,
                NOW(),
                NOW()
            FROM gl_transactions
            WHERE year = :gl_year
              AND property_id IS NOT NULL
              AND account_name IS NOT NULL
              AND amount > 0
            GROUP BY property_id, COALESCE(month, 1), account_name
        """)

        ins_res = await db.execute(insert_sql, {
            "budget_year": BUDGET_YEAR,
            "gl_year": GL_YEAR,
            "inflation": INFLATION,
            "data_source": DATA_SOURCE,
        })
        await db.commit()
        print(f"Inserted {ins_res.rowcount} budget rows for {BUDGET_YEAR}")

        # 4. Verify
        verify = await db.execute(
            text("SELECT COUNT(DISTINCT property_id), SUM(amount) FROM budget WHERE year = :yr"),
            {"yr": BUDGET_YEAR}
        )
        v = verify.fetchone()
        print(f"Budget {BUDGET_YEAR}: {v[0]} properties, TOTAL = {v[1]:,.0f} NOK")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
