"""
Import KPI-justert kontraktsleie til okt 2025 fra CSV → properties.husleie_2026

Kilde: Eiendomsportefølje per okt 2025 - ekstra(Sheet1) (3).csv
Kjøres med:
    railway run --service BEFS1 python3 backend/app/scripts/import_kpi_husleie_csv.py [--dry-run]
    python3 backend/app/scripts/import_kpi_husleie_csv.py --file /path/to/file.csv [--dry-run]
"""
import asyncio
import csv
import re
import sys
import os
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Legg til prosjektrot i sys.path ───────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var mangler")

# Railway gir postgresql:// — asyncpg trenger postgresql+asyncpg://
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

DEFAULT_CSV = str(
    Path.home()
    / "Downloads"
    / "Eiendomsportefølje per okt 2025 - ekstra(Sheet1) (3).csv"
)

# ── Parse-hjelpefunksjoner ─────────────────────────────────────────────────────

def parse_amount(s: str) -> Optional[float]:
    """Hent første sammenhengende siffersekvens ≥ 3 siffer fra fritekstfelt."""
    if not s or not s.strip():
        return None
    clean = s.replace("\xa0", "").replace(" ", "")
    m = re.search(r"\d{3,}", clean)
    return float(m.group()) if m else None


def parse_date(s: str) -> Optional[date]:
    """
    Parse DD.MM.YYYY. Ved flere datoer (slash-separert), ta siste (nyeste grunnlag).
    """
    if not s or not s.strip():
        return None
    parts = re.findall(r"\d{2}\.\d{2}\.\d{4}", s)
    if not parts:
        return None
    try:
        return datetime.strptime(parts[-1], "%d.%m.%Y").date()
    except ValueError:
        return None


# ── Hovedlogikk ───────────────────────────────────────────────────────────────

async def run(csv_path: str, dry_run: bool) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ── 1. Les CSV ──────────────────────────────────────────────────────────
    logger.info("Leser CSV: %s", csv_path)
    rows_by_name: dict[str, dict] = {}  # name (lower) → aggregert data

    encodings = ["utf-8-sig", "latin-1", "cp1252"]
    file_content = None
    for enc in encodings:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                file_content = f.read()
            logger.info("Fil lest med encoding=%s", enc)
            break
        except UnicodeDecodeError:
            continue

    if file_content is None:
        raise RuntimeError(f"Klarte ikke lese fil med noen av encodings: {encodings}")

    reader = csv.DictReader(file_content.splitlines(), delimiter=";")
    n_csv = 0
    n_skipped = 0

    for row in reader:
        raw_name = (row.get("Lokalisering") or "").strip()
        if not raw_name:
            n_skipped += 1
            continue

        kpi_val = parse_amount(row.get("KPI-justert kontraktsleie til okt 2025") or "")
        oppstart_val = parse_amount(row.get("Kontaktsleie ved oppstart (gyldig kontrakt)") or "")
        dato_val = parse_date(row.get("Oppstartsdato (KPI-grunnlag) - Gyldig kontrakt") or "")

        key = raw_name.lower()
        if key not in rows_by_name:
            rows_by_name[key] = {
                "name": raw_name,
                "husleie_2026": kpi_val,
                "kontraktsleie_ved_oppstart_kr": oppstart_val,
                "kpi_oppstartsdato": dato_val,
            }
        else:
            # Summér husleie ved flere kontrakter for samme eiendom
            existing = rows_by_name[key]
            if kpi_val is not None:
                existing["husleie_2026"] = (existing["husleie_2026"] or 0) + kpi_val
            # Oppstartsdato: ta nyeste
            if dato_val and (existing["kpi_oppstartsdato"] is None or dato_val > existing["kpi_oppstartsdato"]):
                existing["kpi_oppstartsdato"] = dato_val
            # Kontraktsleie: summér
            if oppstart_val is not None:
                existing["kontraktsleie_ved_oppstart_kr"] = (
                    existing["kontraktsleie_ved_oppstart_kr"] or 0
                ) + oppstart_val
        n_csv += 1

    logger.info(
        "CSV: %d rader lest, %d unik eiendomsnavn, %d rader hoppet over",
        n_csv, len(rows_by_name), n_skipped,
    )

    # ── 2. Match mot DB og oppdater ─────────────────────────────────────────
    n_matched = 0
    n_updated = 0
    n_no_husleie = 0
    not_found: list[str] = []

    async with async_session() as db:
        for key, data in rows_by_name.items():
            name = data["name"]
            husleie = data["husleie_2026"]
            oppstart = data["kontraktsleie_ved_oppstart_kr"]
            dato = data["kpi_oppstartsdato"]

            if husleie is None:
                n_no_husleie += 1
                logger.debug("Ingen husleie-verdi for '%s' — hopper over", name)
                continue

            # Finn alle rader med dette navnet
            result = await db.execute(
                text(
                    "SELECT property_id, husleie_2026 FROM properties "
                    "WHERE lower(name) = lower(:name) "
                    "ORDER BY (husleie_2026 IS NOT NULL) DESC, created_at ASC"
                ),
                {"name": name},
            )
            props = result.fetchall()

            if not props:
                not_found.append(name)
                continue

            n_matched += 1
            # Prioriter raden som allerede har husleie_2026 satt, ellers første
            target_id = props[0].property_id

            logger.info(
                "%s '%s' → husleie_2026=%.0f%s",
                "[DRY-RUN]" if dry_run else "OPPDATERER",
                name,
                husleie,
                f", oppstart={oppstart:.0f}" if oppstart else "",
            )

            if not dry_run:
                await db.execute(
                    text(
                        "UPDATE properties SET "
                        "husleie_2026 = :husleie, "
                        "kontraktsleie_ved_oppstart_kr = COALESCE(:oppstart, kontraktsleie_ved_oppstart_kr), "
                        "kpi_oppstartsdato = COALESCE(:dato, kpi_oppstartsdato) "
                        "WHERE property_id = :pid"
                    ),
                    {
                        "husleie": husleie,
                        "oppstart": oppstart,
                        "dato": dato,
                        "pid": target_id,
                    },
                )
                n_updated += 1

        if not dry_run:
            await db.commit()

    # ── 3. Rapport ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("RAPPORT%s", " (DRY-RUN)" if dry_run else "")
    logger.info("  CSV-rader lest:            %d", n_csv)
    logger.info("  Unike eiendomsnavn i CSV:  %d", len(rows_by_name))
    logger.info("  Matchet i DB:              %d", n_matched)
    logger.info("  Uten husleie-verdi (skip): %d", n_no_husleie)
    logger.info("  Oppdatert:                 %d", n_updated if not dry_run else n_matched)
    logger.info("  Ikke funnet i DB:          %d", len(not_found))
    if not_found:
        logger.info("  Manglende i DB:")
        for n in not_found[:20]:
            logger.info("    - %s", n)
        if len(not_found) > 20:
            logger.info("    ... og %d til", len(not_found) - 20)

    # ── 4. Spot-sjekk ───────────────────────────────────────────────────────
    if not dry_run:
        engine2 = create_async_engine(DATABASE_URL, echo=False)
        s2 = sessionmaker(engine2, class_=AsyncSession, expire_on_commit=False)
        async with s2() as db:
            res = await db.execute(
                text(
                    "SELECT SUM(husleie_2026)::bigint AS total, "
                    "COUNT(*) FILTER (WHERE husleie_2026 IS NOT NULL) AS antall "
                    "FROM properties"
                )
            )
            row = res.fetchone()
            logger.info("=" * 60)
            logger.info(
                "DB etter import: husleie_2026 sum=%.1f M, antall=%d eiendommer",
                (row.total or 0) / 1_000_000,
                row.antall,
            )


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
