"""
Import budsjettt2026ver04(Sammenligning 2026).csv → befs_budsjett_sammenligning

Kilde: Den autoritative filen med kontant 2025 (øk.), BEFS prediksjon og budsjett 2026 (øk.)
Kjøres med:
    railway run --service BEFS1 python3 backend/app/scripts/import_budsjett_sammenligning.py [--dry-run]
    python3 backend/app/scripts/import_budsjett_sammenligning.py --file /path/to/file.csv [--dry-run]
"""
import asyncio
import csv
import re
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

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
    Path.home() / "Downloads" / "budsjettt2026ver04(Sammenligning 2026).csv"
)
BATCH_ID = f"sammenligning_2026_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def parse_nok(s: str) -> "float | None":
    """
    Parse norsk tallformat med mellomrom som tusenskilletegn.
    Parentes = negativt: (3 931 773) → -3931773
    Returnerer None for tomme/ugyldig celler.
    """
    if not s or not s.strip() or s.strip() in ("-", "—", ""):
        return None
    s = s.strip()
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    s = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    # Fjern evt. % og andre tegn
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        val = float(s)
        return -val if neg else val
    except ValueError:
        return None


async def run(csv_path: str, dry_run: bool) -> None:
    engine = create_async_engine(
        DATABASE_URL, echo=False,
        connect_args={"statement_cache_size": 0},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # ── 1. Les CSV ──────────────────────────────────────────────────────────
    logger.info("Leser CSV: %s", csv_path)
    rows_to_insert: list[dict] = []
    n_skipped = 0
    totals = {"regn_2025": 0.0, "befs": 0.0, "bud_2026": 0.0}

    for enc in ["utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                content = f.read()
            logger.info("Fil lest med encoding=%s", enc)
            break
        except UnicodeDecodeError:
            continue

    lines = content.splitlines()
    # Hopp over linje 1 (beskrivelseslinje), bruk linje 2 som header
    reader = csv.DictReader(lines[1:], delimiter=";")

    for row in reader:
        eiendom = (row.get("Eiendom") or "").strip()
        region = (row.get("Region") or "").strip()

        # Hopp over totallinje og tomme rader
        if not eiendom or eiendom.upper() == "TOTAL" or eiendom.upper() == "TOTALT":
            n_skipped += 1
            continue

        regn_2025 = parse_nok(row.get("Regn. 2025 (Øk.)") or row.get("Regn. 2025 (øk.)") or "")
        befs_pred = parse_nok(row.get("BEFS Prediksjon 2026") or "")
        bud_2026 = parse_nok(row.get("Budsjett 2026 (Økonomi)") or row.get("Budsjett 2026 (økonomi)") or "")
        merknad = (row.get("Merknad") or "").strip() or None

        rows_to_insert.append({
            "eiendom": eiendom,
            "region": region or None,
            "regn_2025_ok": regn_2025,
            "befs_pred_2026": befs_pred,
            "budsjett_2026_ok": bud_2026,
            "merknad": merknad,
            "import_batch_id": BATCH_ID,
        })

        if regn_2025:
            totals["regn_2025"] += regn_2025
        if befs_pred:
            totals["befs"] += befs_pred
        if bud_2026:
            totals["bud_2026"] += bud_2026

    logger.info(
        "CSV: %d rader importklare, %d hoppet over",
        len(rows_to_insert), n_skipped,
    )
    logger.info(
        "CSV-summer: Regn.2025=%.1f M | BEFS 2026=%.1f M | Budsjett 2026=%.1f M",
        totals["regn_2025"] / 1e6, totals["befs"] / 1e6, totals["bud_2026"] / 1e6,
    )

    if dry_run:
        logger.info("DRY-RUN — ingen skriving til DB")
        for r in rows_to_insert[:5]:
            logger.info("  EKS: %s | %s | 2025=%.0f | befs=%.0f | øk=%.0f",
                r["eiendom"][:50], r["region"],
                r["regn_2025_ok"] or 0, r["befs_pred_2026"] or 0, r["budsjett_2026_ok"] or 0)
        return

    # ── 2. Slett gammel batch og insert ny ──────────────────────────────────
    async with async_session() as db:
        # Slett alle tidligere rader (erstatt med ny batch)
        del_result = await db.execute(
            text("DELETE FROM befs_budsjett_sammenligning")
        )
        logger.info("Slettet eksisterende rader fra tabellen")

        # Bulk insert
        for r in rows_to_insert:
            await db.execute(
                text("""
                    INSERT INTO befs_budsjett_sammenligning
                        (eiendom, region, regn_2025_ok, befs_pred_2026,
                         budsjett_2026_ok, merknad, import_batch_id)
                    VALUES
                        (:eiendom, :region, :regn_2025_ok, :befs_pred_2026,
                         :budsjett_2026_ok, :merknad, :import_batch_id)
                """),
                r,
            )

        await db.commit()
        logger.info("Inserted %d rader med batch_id=%s", len(rows_to_insert), BATCH_ID)

    # ── 3. Verifisering ─────────────────────────────────────────────────────
    async with async_session() as db:
        res = await db.execute(text("""
            SELECT
                region,
                COUNT(*) AS antall,
                SUM(regn_2025_ok) AS sum_2025,
                SUM(befs_pred_2026) AS sum_befs,
                SUM(budsjett_2026_ok) AS sum_2026
            FROM befs_budsjett_sammenligning
            GROUP BY region
            ORDER BY sum_2025 DESC NULLS LAST
        """))
        logger.info("=" * 70)
        logger.info("%-20s %6s %12s %12s %12s", "Region", "Ant.", "Regn.2025", "BEFS 2026", "Øk.Bud.2026")
        logger.info("-" * 70)
        t25 = t_befs = t26 = 0
        for row in res.all():
            r25 = float(row.sum_2025 or 0)
            rb = float(row.sum_befs or 0)
            r26 = float(row.sum_2026 or 0)
            t25 += r25; t_befs += rb; t26 += r26
            logger.info("%-20s %6d %12.1f M %12.1f M %12.1f M",
                (row.region or "Ukjent")[:20], row.antall,
                r25/1e6, rb/1e6, r26/1e6)
        logger.info("-" * 70)
        logger.info("%-20s %6s %12.1f M %12.1f M %12.1f M",
            "TOTALT", "", t25/1e6, t_befs/1e6, t26/1e6)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    csv_path = DEFAULT_CSV
    for i, arg in enumerate(sys.argv):
        if arg == "--file" and i + 1 < len(sys.argv):
            csv_path = sys.argv[i + 1]

    if not Path(csv_path).exists():
        logger.error("CSV-fil ikke funnet: %s", csv_path)
        sys.exit(1)

    logger.info("Modus: %s", "DRY-RUN" if dry_run else "LIVE")
    asyncio.run(run(csv_path, dry_run))
