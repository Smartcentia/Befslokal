"""
update_husleie_2026.py
======================
Les BEFS_husleie_2026_KPI.csv og skriv husleie_2026 + husleie_2026_kpi_note
til properties-tabellen for alle eiendommer med beregnet KPI-justert husleie.

Kjøres med:
    python3 backend/app/scripts/update_husleie_2026.py [--dry-run|--execute]
"""
import asyncio
import csv
import os
import sys
from pathlib import Path

# Default: csv ved siden av scriptet, eller fra Downloads
CSV_CANDIDATES = [
    Path.home() / "Downloads" / "BEFS_husleie_2026_KPI.csv",
    Path(__file__).parent / "BEFS_husleie_2026_KPI.csv",
]

dry_run = "--execute" not in sys.argv

async def main():
    # Finn CSV
    csv_path = None
    for c in CSV_CANDIDATES:
        if c.exists():
            csv_path = c
            break
    if not csv_path:
        print("FEIL: Finner ikke BEFS_husleie_2026_KPI.csv. "
              "Legg den i ~/Downloads/ eller pass stien.")
        sys.exit(1)

    print(f"Leser: {csv_path}")

    rows = list(csv.DictReader(
        open(csv_path, encoding="utf-8-sig"), delimiter=";"
    ))

    # Filtrer rader med faktisk KPI-verdi (kolonnenavnet i CSV er husleie_2026_KPI)
    kpi_col = "husleie_2026_KPI" if "husleie_2026_KPI" in rows[0] else "husleie_2026"
    to_update = [
        r for r in rows
        if r.get(kpi_col) and r[kpi_col].strip()
    ]
    print(f"Totalt {len(rows)} rader, {len(to_update)} med KPI-justert husleie (kolonne: {kpi_col})")

    if dry_run:
        print("\n[DRY-RUN] Ingen DB-endringer gjøres.")
        print("Eksempel (de 5 første):")
        for r in to_update[:5]:
            print(f"  {r['property_id']} | {r['navn'][:40]} | "
                  f"husleie_2026={r[kpi_col]} | {r['kpi_note']}")
        print(f"\nKjør med --execute for å skrive til DB.")
        return

    # DB
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("FEIL: DATABASE_URL mangler. Kjør via: railway run python3 ...")
        sys.exit(1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated = 0
    skipped = 0
    errors = 0

    # Forbered data-liste for batch-update
    params_list = []
    for r in to_update:
        pid = r["property_id"].strip()
        try:
            val = float(r[kpi_col])
            note = r.get("kpi_note", "").strip()
            params_list.append({"val": val, "note": note, "pid": pid})
        except Exception:
            errors += 1

    # Batch-update: én transaksjon, unngår prepared statement duplikater
    upd_sql = sa.text("""
        UPDATE properties
        SET husleie_2026 = :val,
            husleie_2026_kpi_note = :note
        WHERE property_id = CAST(:pid AS uuid)
    """)

    async with async_session() as db:
        for params in params_list:
            try:
                res = await db.execute(upd_sql, params)
                if res.rowcount > 0:
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  FEIL {params['pid']}: {e}")
                await db.rollback()
                errors += 1
                # Re-open session after rollback
                continue

        await db.commit()

    print(f"\n✅ Ferdig: {updated} oppdatert, {skipped} ikke funnet, {errors} feil")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
