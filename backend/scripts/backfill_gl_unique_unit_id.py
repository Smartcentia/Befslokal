#!/usr/bin/env python3
"""
Backfill gl_transactions.property_id for properties where unit_id_erp
maps UNIQUELY to a single property (no cost-center sharing).
Skips cases where multiple properties share the same unit_id_erp.

Run: railway run --service striking-insight python3 scripts/backfill_gl_unique_unit_id.py [--dry-run]
"""
import asyncio, sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.db.session import SessionLocal
from sqlalchemy import text


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    async with SessionLocal() as db:
        # Find properties NOT in prediction with unit_id_erp matching GL
        r = await db.execute(text("""
            SELECT p.property_id::text, p.name, p.unit_id_erp,
                   SUM(g.belop) FILTER(WHERE g.ar=2025 AND g.belop>0) as gl25
            FROM properties p
            JOIN gl_transactions g ON g.dim1_kode = p.unit_id_erp
            WHERE p.property_id NOT IN (
                SELECT DISTINCT property_id FROM budget WHERE year=2027 AND is_synthetic=true
            )
            AND (p.closed_at IS NULL OR p.closed_at > NOW())
            GROUP BY p.property_id, p.name, p.unit_id_erp
            HAVING SUM(g.belop) FILTER(WHERE g.belop>0) > 0
            ORDER BY gl25 DESC NULLS LAST
        """))
        candidates = [(row[0], row[1], row[2], float(row[3] or 0)) for row in r.fetchall()]
        print(f"Candidates: {len(candidates)}")

        # Check which unit_id_erp values are unique (1 property per cost center)
        from collections import Counter
        uid_count = Counter(c[2] for c in candidates)

        unique = [(pid, name, uid, gl25) for pid, name, uid, gl25 in candidates
                  if uid_count[uid] == 1]
        shared = [(pid, name, uid, gl25) for pid, name, uid, gl25 in candidates
                  if uid_count[uid] > 1]

        print(f"Unique unit_id_erp: {len(unique)}")
        print(f"Shared unit_id_erp (skipping): {len(shared)}")
        print()

        total_gl_rows = 0
        for pid, name, uid, gl25 in unique:
            # Count GL rows for this unit_id_erp
            r2 = await db.execute(text(
                "SELECT COUNT(*) FROM gl_transactions WHERE dim1_kode = :uid AND property_id IS NULL"
            ), {"uid": uid})
            n_rows = r2.scalar()
            total_gl_rows += n_rows
            print(f"  {name[:42]:<44} uid={uid}  gl25={gl25/1e6:.2f}M  gl_rows={n_rows}")

        print(f"\nTotal GL rows to backfill: {total_gl_rows}")

        if not args.dry_run and unique:
            for pid, name, uid, gl25 in unique:
                await db.execute(text("""
                    UPDATE gl_transactions
                    SET property_id = CAST(:pid AS uuid)
                    WHERE dim1_kode = :uid AND property_id IS NULL
                """), {"pid": pid, "uid": uid})
            await db.commit()
            print(f"Backfilled GL rows for {len(unique)} properties.")
        elif args.dry_run:
            print(f"[--dry-run] Would backfill {len(unique)} properties.")

        print("\nShared unit_id_erp (skipped):")
        for pid, name, uid, gl25 in shared:
            print(f"  {name[:42]:<44} uid={uid}  gl25={gl25/1e6:.2f}M  (shared with {uid_count[uid]-1} others)")

asyncio.run(main())
