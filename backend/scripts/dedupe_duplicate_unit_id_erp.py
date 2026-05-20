#!/usr/bin/env python3
"""
Fjern duplikat unit_id_erp på properties: behold én «vinner» per kode, null ut på øvrige.

Vinner velges etter: flest GL-rader (property_id), deretter flest aktive kontrakter.

  railway run bash -c 'cd backend && PYTHONPATH=. python3 scripts/dedupe_duplicate_unit_id_erp.py --dry-run'
  railway run bash -c 'cd backend && PYTHONPATH=. python3 scripts/dedupe_duplicate_unit_id_erp.py --apply'
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

try:
    from dotenv import load_dotenv

    load_dotenv(_backend / ".env", override=False)
except Exception:
    pass

from sqlalchemy import text

import app.db.base  # noqa: F401
from app.db.session import SessionLocal


async def main_async(args: argparse.Namespace) -> int:
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL mangler.", file=sys.stderr)
        return 2

    async with SessionLocal() as db:
        dup = (
            await db.execute(
                text("""
            SELECT unit_id_erp, COUNT(*)::int AS n
            FROM properties
            WHERE unit_id_erp IS NOT NULL AND TRIM(unit_id_erp) <> ''
            GROUP BY unit_id_erp
            HAVING COUNT(*) > 1
            ORDER BY unit_id_erp
        """)
            )
        ).fetchall()

        to_null: list[tuple[str, UUID, str]] = []

        for code, _n in dup:
            code = str(code).strip()
            rprops = (
                await db.execute(
                    text("""
                SELECT property_id::text FROM properties
                WHERE TRIM(unit_id_erp) = :code
            """),
                    {"code": code},
                )
            ).fetchall()
            pids = [UUID(row[0]) for row in rprops]

            scores: list[tuple[UUID, int, int]] = []
            for pid in pids:
                gl_n = (
                    await db.execute(
                        text(
                            "SELECT COUNT(*)::int FROM gl_transactions WHERE property_id = CAST(:p AS uuid)"
                        ),
                        {"p": str(pid)},
                    )
                ).scalar() or 0
                ctr_n = (
                    await db.execute(
                        text("""
                    SELECT COUNT(*)::int FROM contracts c
                    JOIN units u ON c.unit_id = u.unit_id
                    WHERE u.property_id = CAST(:p AS uuid) AND c.status = 'active'
                """),
                        {"p": str(pid)},
                    )
                ).scalar() or 0
                scores.append((pid, int(gl_n), int(ctr_n)))

            scores.sort(key=lambda x: (-x[1], -x[2], str(x[0])))
            winner = scores[0][0]
            for pid, gl_n, ctr_n in scores[1:]:
                to_null.append((code, pid, f"loser gl={gl_n} ctr={ctr_n} winner={winner}"))

        print(f"Duplikat-koder: {len(dup)} | properties som får NULL unit_id_erp: {len(to_null)}")
        for code, pid, note in to_null:
            print(f"  {code}  property_id={pid}  ({note})")

        if args.apply and to_null:
            for code, pid, _ in to_null:
                await db.execute(
                    text("UPDATE properties SET unit_id_erp = NULL WHERE property_id = CAST(:p AS uuid)"),
                    {"p": str(pid)},
                )
            await db.commit()
            print(f"Oppdatert {len(to_null)} rader (unit_id_erp satt til NULL).")
        elif args.apply:
            print("Ingen endringer.")
        else:
            print("[--dry-run] Bruk --apply for å skrive.")

    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
