"""
Normaliser properties.region til kanoniske verdier.

Bruker COUNTY_TO_REGION-mappingen fra region_mapping.py til å oppdatere
alle properties der region-feltet er ikke-kanonisk (f.eks. "Midt" → "Midt-Norge",
"01 - Nordland" → "Nord" osv.).

Kjøring:
    railway run python -m app.scripts.normalize_property_regions
    # eller direkte:
    DATABASE_URL=... python -m app.scripts.normalize_property_regions
"""

import asyncio
import logging
import os
from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.domains.core.utils.region_mapping import COUNTY_TO_REGION, REGIONS_AND_DIRECTORATE

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CANONICAL = set(REGIONS_AND_DIRECTORATE)


async def run(db: AsyncSession) -> None:
    # Finn alle unike region-verdier som er ikke-kanoniske og har en mapping
    result = await db.execute(text(
        "SELECT region, COUNT(*) AS n FROM properties WHERE region IS NOT NULL GROUP BY region ORDER BY n DESC"
    ))
    rows = result.all()

    updates: dict[str, str] = {}
    for row in rows:
        raw = row.region
        canonical = COUNTY_TO_REGION.get(raw)
        if canonical and raw not in CANONICAL:
            updates[raw] = canonical

    if not updates:
        logger.info("Ingen ikke-kanoniske region-verdier funnet – ingenting å oppdatere.")
        return

    total = 0
    for raw, canonical in updates.items():
        res = await db.execute(
            text("UPDATE properties SET region = :canonical WHERE region = :raw"),
            {"canonical": canonical, "raw": raw},
        )
        n = res.rowcount
        total += n
        logger.info("  '%s' → '%s'  (%d rad%s oppdatert)", raw, canonical, n, "er" if n != 1 else "")

    await db.commit()
    logger.info("Ferdig: %d rader oppdatert totalt.", total)

    # Vis ny fordeling
    result2 = await db.execute(text(
        "SELECT region, COUNT(*) AS n FROM properties GROUP BY region ORDER BY n DESC"
    ))
    logger.info("\nNy region-fordeling:")
    for row in result2.all():
        logger.info("  %-30s %d", row.region or "(NULL)", row.n)


async def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise SystemExit("DATABASE_URL ikke satt.")
    # asyncpg-driver
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False, connect_args={"statement_cache_size": 0})
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await run(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
