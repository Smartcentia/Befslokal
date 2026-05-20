#!/usr/bin/env python3
"""
Tøm regnskapsdata for 2026.

Regnskap for 2026 er ikke på plass ennå – dette scriptet fjerner:
- gl_transactions WHERE year = 2026
- budget WHERE year = 2026
- manual_expenses med date i 2026 (fra properties.external_data.financials)

Kjør: cd backend && railway run env PYTHONPATH=. python3 scripts/clear_regnskap_2026.py [--force]
"""
import asyncio
import argparse
from sqlalchemy import text, select
from sqlalchemy.orm import attributes

from app.db.session import SessionLocal
from app.models.financial_models import Budget, GLTransaction
from app.db.base import Property


def _is_2026_date(date_val) -> bool:
    """Sjekk om date-feltet er 2026 (f.eks. 2026-01-01, 2026-Q1, 01.01.2026)."""
    if not date_val:
        return False
    s = str(date_val).strip()
    if len(s) >= 4 and s[:4] == "2026":
        return True
    if "-Q" in s and "2026" in s:
        return True
    if "." in s:
        parts = s.split(".")
        if len(parts) >= 3 and parts[-1] == "2026":
            return True
    return False


async def clear_2026(dry_run: bool = True):
    async with SessionLocal() as db:
        print("=" * 60)
        print("TØM REGNSKAPSDATA FOR 2026")
        print("=" * 60)

        # 1. Tell og slett gl_transactions
        gl_count = await db.execute(text("SELECT COUNT(*) FROM gl_transactions WHERE year = 2026"))
        gl_n = gl_count.scalar() or 0
        print(f"\n1. gl_transactions (year=2026): {gl_n} rader")
        if not dry_run and gl_n > 0:
            await db.execute(text("DELETE FROM gl_transactions WHERE year = 2026"))
            print(f"   Slettet {gl_n} rader")

        # 2. Tell og slett budget (BEHOLDER estimert budsjett fra estimate_budget_2026.py)
        budget_count = await db.execute(text("""
            SELECT COUNT(*) FROM budget WHERE year = 2026
            AND (data_source IS NULL OR data_source NOT LIKE 'estimate_2026%')
        """))
        budget_n = budget_count.scalar() or 0
        kept = await db.execute(text("""
            SELECT COUNT(*) FROM budget WHERE year = 2026 AND data_source LIKE 'estimate_2026%'
        """))
        kept_n = kept.scalar() or 0
        print(f"\n2. budget (year=2026): {budget_n} rader å slette (feilaktig import)")
        if kept_n > 0:
            print(f"   Beholder {kept_n} rader (estimert budsjett fra estimate_budget_2026.py)")
        if not dry_run and budget_n > 0:
            await db.execute(text("""
                DELETE FROM budget WHERE year = 2026
                AND (data_source IS NULL OR data_source NOT LIKE 'estimate_2026%')
            """))
            print(f"   Slettet {budget_n} rader")

        # 3. Fjern 2026-utgifter fra manual_expenses
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        props = result.scalars().all()
        props_updated = 0
        expenses_removed = 0
        for prop in props:
            ext = prop.external_data or {}
            fin = ext.get("financials", {})
            expenses = fin.get("manual_expenses", [])
            if not expenses:
                continue
            kept = [e for e in expenses if not _is_2026_date(e.get("date"))]
            removed = len(expenses) - len(kept)
            if removed > 0:
                expenses_removed += removed
                fin["manual_expenses"] = kept
                total = sum(float(e.get("amount", 0) or 0) for e in kept)
                fin["total_manual_expenses"] = total
                ext["financials"] = fin
                prop.external_data = ext
                attributes.flag_modified(prop, "external_data")
                props_updated += 1
        print(f"\n3. manual_expenses (date=2026): {expenses_removed} utgifter fjernet fra {props_updated} eiendommer")

        if dry_run:
            print("\n--- DRY RUN: Ingen endringer utført. Bruk --force for å kjøre. ---")
        else:
            await db.commit()
            print("\n--- Ferdig. Regnskapsdata for 2026 er tømt. ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tøm regnskapsdata for 2026")
    parser.add_argument("--force", action="store_true", help="Utfør slettingen (uten --force = dry-run)")
    args = parser.parse_args()
    asyncio.run(clear_2026(dry_run=not args.force))
