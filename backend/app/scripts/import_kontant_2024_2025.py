"""
Éngangsimport: 'Til eiendom - Kontant 202400 - 202510(Grunnlag).csv'

Dekker 202401–202510 (januar 2024 – oktober 2025) for alle 6 regioner.
Format: Xledger/ok1-stil med semikolon, Windows-1252.

Bruk:
    cd backend
    # Lokalt mot Railway-DB (via DATABASE_URL i .env):
    python -m app.scripts.import_kontant_2024_2025 --file "/path/to/file.csv"

    # Via railway run:
    railway run python -m app.scripts.import_kontant_2024_2025 --file "/path/to/file.csv"
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings
# Import all models in correct order so SQLAlchemy mapper can resolve lazy string references
import app.db.base  # noqa: F401
from app.services.data_management import DataManagementService

DEFAULT_FILE = Path.home() / "Downloads" / "Til eiendom - Kontant 202400 - 202510(Grunnlag).csv"


async def main(csv_path: Path, dry_run: bool = False) -> None:
    if not csv_path.exists():
        print(f"ERROR: Fil ikke funnet: {csv_path}")
        sys.exit(1)

    size_kb = csv_path.stat().st_size / 1024
    print(f"Les: {csv_path.name}  ({size_kb:.0f} KB)")

    file_content = csv_path.read_bytes()

    db_url = settings.DATABASE_URL
    print(f"DB: {db_url[:50]}...")

    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        # Tell brukeren hva som allerede er i DB
        rows = await db.execute(
            text("SELECT year, COUNT(*) as cnt FROM gl_transactions GROUP BY year ORDER BY year")
        )
        existing = rows.fetchall()
        if existing:
            print("\nEksisterende gl_transactions per år:")
            for row in existing:
                print(f"  {row[0]}: {row[1]:,} rader")
        else:
            print("\nIngen eksisterende gl_transactions.")

        if dry_run:
            print("\n[DRY RUN] Stopper her – ingen skriving til DB.")
            await engine.dispose()
            return

        bekreft = input("\nStart import av 35 000+ rader? [y/N] ").strip().lower()
        if bekreft != "y":
            print("Avbrutt.")
            await engine.dispose()
            return

        print("\nImporterer – dette tar litt tid...")
        result = await DataManagementService.import_financial_csv(db, file_content)
        print("\n=== IMPORTRESULTAT ===")
        for k, v in result.items():
            print(f"  {k}: {v}")

        # Vis ny fordeling per år
        rows2 = await db.execute(
            text("SELECT year, COUNT(*) as cnt, ROUND(SUM(amount)::numeric, 0) as total FROM gl_transactions GROUP BY year ORDER BY year")
        )
        print("\ngl_transactions etter import:")
        for row in rows2.fetchall():
            print(f"  {row[0]}: {row[1]:,} rader  |  SUM = {int(row[2]):,} NOK")

    await engine.dispose()
    print("\nFerdig!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer kontant GL-data 2024+2025")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FILE,
        help="Sti til CSV-filen (standard: ~/Downloads/Til eiendom - Kontant 202400 - 202510(Grunnlag).csv)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse og vis DB-status, men ikke importer")
    args = parser.parse_args()
    asyncio.run(main(args.file, args.dry_run))
