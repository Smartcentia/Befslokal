#!/usr/bin/env python3
"""
Find and backfill GL rows for properties that match unmapped cost centers by name.
Only handles cases where a SINGLE property matches a given dim1_kode name.

Run: railway run --service striking-insight python3 scripts/backfill_gl_name_match.py [--dry-run]
"""
import asyncio, sys, re, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.db.session import SessionLocal
from sqlalchemy import text


def normalize(s):
    if not s: return ""
    s = str(s).lower().strip()
    s = re.sub(r"[^\w\sæøå]", " ", s)
    return " ".join(s.split())


def words(s, min_len=4):
    return [w for w in normalize(s).split() if len(w) >= min_len]


def score(a, b):
    an, bn = normalize(a), normalize(b)
    if an == bn: return 1.0
    if an in bn or bn in an: return 0.9
    aw = set(words(a))
    bw = set(words(b))
    if not aw or len(aw) < 2: return 0.0
    return len(aw & bw) / len(aw)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-score", type=float, default=0.7)
    args = parser.parse_args()

    async with SessionLocal() as db:
        # Get all unmapped GL 2025 cost centers with meaningful volume
        r = await db.execute(text("""
            SELECT dim1_kode, dim1_navn, SUM(belop) as gl25
            FROM gl_transactions
            WHERE ar = 2025 AND belop > 0 AND property_id IS NULL
            GROUP BY dim1_kode, dim1_navn
            HAVING SUM(belop) > 500000
            ORDER BY gl25 DESC
        """))
        unmapped = [(row[0], row[1] or "", float(row[2] or 0)) for row in r.fetchall()]
        print(f"Unmapped GL cost centers (gl25 > 0.5M): {len(unmapped)}")

        # Get properties NOT in prediction
        r2 = await db.execute(text("""
            SELECT property_id::text, name
            FROM properties
            WHERE property_id NOT IN (
                SELECT DISTINCT property_id FROM budget WHERE year=2027 AND is_synthetic=true
            )
            AND (closed_at IS NULL OR closed_at > NOW())
            AND name IS NOT NULL
        """))
        missing_props = [(row[0], row[1]) for row in r2.fetchall()]

        # Match
        matches = []
        for dim1, dim1_name, gl25 in unmapped:
            best_props = []
            for pid, pname in missing_props:
                sc = score(pname, dim1_name)
                if sc >= args.min_score:
                    best_props.append((pid, pname, sc))
            if len(best_props) == 1:
                matches.append((dim1, dim1_name, gl25, best_props[0][0], best_props[0][1], best_props[0][2]))
            elif len(best_props) > 1:
                best = max(best_props, key=lambda x: x[2])
                if best[2] >= 0.85:  # Only take if very high score
                    matches.append((dim1, dim1_name, gl25, best[0], best[1], best[2]))

        print(f"\nUnambiguous matches (score>={args.min_score}): {len(matches)}")
        for dim1, dim1_name, gl25, pid, pname, sc in sorted(matches, key=lambda x: -x[2]):
            print(f"  score={sc:.2f}  '{dim1_name[:40]}'  →  '{pname[:40]}'  gl25={gl25/1e6:.2f}M")

        if not args.dry_run and matches:
            total_rows = 0
            for dim1, dim1_name, gl25, pid, pname, sc in matches:
                r3 = await db.execute(text("""
                    UPDATE gl_transactions
                    SET property_id = CAST(:pid AS uuid)
                    WHERE dim1_kode = :dim1 AND property_id IS NULL
                    RETURNING transaction_id
                """), {"pid": pid, "dim1": dim1})
                n = len(r3.fetchall())
                total_rows += n
                print(f"  Updated {n} GL rows: {dim1_name[:40]} → {pname[:40]}")
            await db.commit()
            print(f"\nTotal GL rows backfilled: {total_rows}")
        elif args.dry_run:
            print(f"\n[--dry-run] Would backfill {len(matches)} cost centers.")

asyncio.run(main())
