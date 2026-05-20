#!/usr/bin/env python3
"""
Hent HTML for hver institusjon i bufdir_institutions.json og parse detaljer(galleri, sammendrag, kontakt, tekstseksjoner). Skriver bufdir_institutions_detailed.json.

Kjør fra prosjektrot etter fetch_bufdir_data.py:
  python backend/scripts/scrape_bufdir_institution_pages.py
  python backend/scripts/scrape_bufdir_institution_pages.py --limit 5
  python backend/scripts/scrape_bufdir_institution_pages.py --only-id 12345
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
INPUT_FILE = BACKEND_DIR / "bufdir_institutions.json"
OUTPUT_FILE = BACKEND_DIR / "bufdir_institutions_detailed.json"

USER_AGENT = "BEFS-Eiendomsbase/1.0 (bufdir institusjonsdetaljer)"

sys.path.insert(0, str(SCRIPT_DIR))
from lib.bufdir_detail_parse import parse_institution_detail_html

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


def fetch_html(url: str, retries: int = 3) -> Optional[str]:
    try:
        import httpx
    except ImportError:
        logger.error("httpx mangler")
        return None
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(
                timeout=60.0,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                r = client.get(url)
                r.raise_for_status()
                return r.text
        except Exception as e:
            last_err = e
            logger.warning("GET %s forsøk %s/%s: %s", url, attempt + 1, retries, e)
            time.sleep(2**attempt)
    logger.error("GET feilet endelig %s: %s", url, last_err)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Bufdir institusjonssider")
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=INPUT_FILE,
        help=f"JSON fra fetch_bufdir (default: {INPUT_FILE})",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        type=Path,
        default=OUTPUT_FILE,
        help=f"Utdata (default: {OUTPUT_FILE})",
    )
    parser.add_argument("--delay", type=float, default=1.2, help="Sekunder mellom forespørsler")
    parser.add_argument("--limit", type=int, default=0, help="Maks antall (0 = alle)")
    parser.add_argument("--only-id", type=str, default=None, help="Kun denne bufdir-id (som streng)")
    args = parser.parse_args()

    if not args.in_path.exists():
        logger.error("Fant ikke %s — kjør fetch_bufdir_data.py først", args.in_path)
        sys.exit(1)

    institutions: list[dict[str, Any]] = json.loads(
        args.in_path.read_text(encoding="utf-8")
    )
    scraped_at = datetime.now(timezone.utc).isoformat()
    out_rows: list[dict[str, Any]] = []
    count = 0

    for inst in institutions:
        iid = inst.get("id")
        if args.only_id is not None and str(iid) != str(args.only_id):
            continue
        url = inst.get("bufdir_url") or inst.get("linkToInstitution")
        if not url:
            row = {**inst, "detail": {"parse_error": "missing_bufdir_url", "scraped_at": scraped_at}}
            out_rows.append(row)
            continue

        if not str(url).startswith("http"):
            url = f"https://www.bufdir.no{url}" if str(url).startswith("/") else url

        logger.info("Henter %s (%s)", iid, url)
        html = fetch_html(str(url))
        if not html:
            detail = {
                "source_detail_url": str(url),
                "scraped_at": scraped_at,
                "parse_error": "http_fetch_failed",
                "gallery": [],
                "summary": {},
                "contact": {},
                "content_sections": [],
            }
        else:
            detail = parse_institution_detail_html(html, str(url))
            detail["scraped_at"] = scraped_at

        out_rows.append({**inst, "detail": detail})
        count += 1
        if args.limit and count >= args.limit:
            break
        time.sleep(max(0.0, args.delay))

    payload = {
        "scraped_at": scraped_at,
        "institutions": out_rows,
    }
    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    args.out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Lagret %s institusjoner med detaljer til %s", len(out_rows), args.out_path)


if __name__ == "__main__":
    main()
