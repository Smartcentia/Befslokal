"""
Import Elements-saksnummer fra CSV → properties.elements_id

Kilde: Eiendomsportefølje per okt 2025 - ekstra(Sheet1) (4).csv
Kjøres med:
    railway run --service BEFS1 python3 backend/app/scripts/import_elements_id.py [--dry-run]
    python3 backend/app/scripts/import_elements_id.py --file /path/to/file.csv [--dry-run]
"""
import asyncio
import csv
import sys
import os
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var mangler")
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

DEFAULT_CSV = str(
    Path.home()
    / "Downloads"
    / "Eiendomsportefølje per okt 2025 - ekstra(Sheet1) (4).csv"
)


def parse_elements(s: str) -> "str | None":
    """
    Hent første saksnummer på formen YYYY/NNNNN[-N] fra fritekstfelt.
    Eksempler:
      "2023/80050"           → "2023/80050"
      "2019/51834-5 og 19"  → "2019/51834-5"
      "2005/7144 og 2016/..." → "2005/7144"
    """
    if not s or not s.strip():
        return None
    m = re.search(r"\d{4}/\d{3,}(?:-\d+)?", s.strip())
    return m.group() if m else None


async def run(csv_path: str, dry_run: bool) -> None:
    engine = create_async_engine(
        DATABASE_URL, echo=False,
        connect_args={"statement_cache_size": 0},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ── 1. Les CSV ──────────────────────────────────────────────────────────
    logger.info("Leser CSV: %s", csv_path)
    rows: list[tuple[str, str]] = []  # (name, elements_id)

    for enc in ["utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                content = f.read()
            logger.info("Fil lest med encoding=%s", enc)
            break
        except UnicodeDecodeError:
            continue

    reader = csv.DictReader(content.splitlines(), delimiter=";")
    n_skipped = 0

    for row in reader:
        name = (row.get("Lokalisering") or "").strip()
        elements_raw = (row.get("Elements") or row.get("Elements ") or "").strip()

        if not name:
            n_skipped += 1
            continue

        elements = parse_elements(elements_raw)
        if elements:
            rows.append((name, elements))
        else:
            n_skipped += 1
            if elements_raw:
                logger.debug("Ingen gyldig Elements-ref for '%s': '%s'", name, elements_raw)

    logger.info("CSV: %d rader med Elements-saksnummer, %d hoppet over", len(rows), n_skipped)

    # ── 2. Match mot DB og oppdater ─────────────────────────────────────────
    n_matched = 0
    n_updated = 0
    not_found: list[str] = []

    async with async_session() as db:
        for name, elements in rows:
            result = await db.execute(
                text(
                    "SELECT property_id, elements_id FROM properties "
                    "WHERE lower(name) = lower(:name) "
                    "ORDER BY (elements_id IS NOT NULL) DESC, created_at ASC "
                    "LIMIT 1"
                ),
                {"name": name},
            )
            prop = result.fetchone()

            if not prop:
                not_found.append(name)
                continue

            n_matched += 1
            logger.info(
                "%s '%s' → elements_id=%s%s",
                "[DRY-RUN]" if dry_run else "OPPDATERER",
                name,
                elements,
                f" (var: {prop.elements_id})" if prop.elements_id else "",
            )

            if not dry_run:
                await db.execute(
                    text(
                        "UPDATE properties SET elements_id = :elements "
                        "WHERE property_id = :pid"
                    ),
                    {"elements": elements, "pid": prop.property_id},
                )
                n_updated += 1

        if not dry_run:
            await db.commit()

    # ── 3. Rapport ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("RAPPORT%s", " (DRY-RUN)" if dry_run else "")
    logger.info("  Rader med Elements i CSV:  %d", len(rows))
    logger.info("  Matchet i DB:              %d", n_matched)
    logger.info("  Oppdatert:                 %d", n_updated if not dry_run else n_matched)
    logger.info("  Ikke funnet i DB:          %d", len(not_found))
    if not_found:
        logger.info("  Manglende i DB:")
        for n in not_found[:15]:
            logger.info("    - %s", n)
        if len(not_found) > 15:
            logger.info("    ... og %d til", len(not_found) - 15)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    csv_path = DEFAULT_CSV
    for i, arg in enumerate(sys.argv):
        if arg == "--file" and i + 1 < len(sys.argv):
            csv_path = sys.argv[i + 1]

    if not Path(csv_path).exists():
        logger.error("CSV-fil ikke funnet: %s", csv_path)
        sys.exit(1)

    logger.info("Modus: %s", "DRY-RUN" if dry_run else "LIVE (skriver til DB)")
    asyncio.run(run(csv_path, dry_run))
