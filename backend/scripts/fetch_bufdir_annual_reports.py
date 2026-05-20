#!/usr/bin/env python3
"""
Hent Bufdir årsrapporter (PDF-lenker) for siste N år og lagre i JSON.

Kjør fra prosjektrot:
  python backend/scripts/fetch_bufdir_annual_reports.py --years 10
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT_FILE = BACKEND / "data" / "bufdir_arsrapporter.json"
USER_AGENT = "BEFS-Eiendomsbase/1.0 (bufdir annual reports)"


def _extract_pdf_urls(html: str) -> List[str]:
    urls = re.findall(r"https?://[^\"' <>()]+\.pdf", html, flags=re.IGNORECASE)
    # Dedup, bevar rekkefølge
    seen = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _pick_best_pdf(urls: List[str], year: int) -> Optional[str]:
    if not urls:
        return None
    y = str(year)
    preferred_patterns = [
        f"arsrapport-for-{y}",
        f"arsrapport-bufdir-{y}",
        f"årsrapport-for-{y}",
        f"/arsrapport-{y}/",
    ]
    for pat in preferred_patterns:
        for u in urls:
            if pat.lower() in u.lower():
                return u
    # fallback: første url som inneholder årstall
    for u in urls:
        if y in u:
            return u
    return urls[0]


def _fetch_html(url: str, timeout: float = 25.0) -> Optional[str]:
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = client.get(url)
            if r.status_code != 200:
                return None
            return r.text
    except Exception:
        return None


def _candidate_pages(year: int) -> List[str]:
    return [
        f"https://www.bufdir.no/om/aarsrapport{year}/",
        f"https://www.bufdir.no/om/arsrapport{year}/",
        f"https://www.bufdir.no/aktuelt/her-er-bufdirs-arsrapport-for-{year}/",
        f"https://www.bufdir.no/aktuelt/bufdirs-arsrapport-for-{year}/",
    ]


def _candidate_pdf_urls(year: int) -> List[str]:
    y = str(year)
    return [
        f"https://www.bufdir.no/siteassets/om-bufdir-og-bufetat/arsrapport-{y}/bufdirs-arsrapport-for-{y}.pdf",
        f"https://www.bufdir.no/siteassets/rapporter/arsrapport-bufdir-{y}.pdf",
        f"https://www.bufdir.no/globalassets/global/nbbf/arsrapporter/bufdirs-arsrapport-{y}.pdf",
    ]


def _url_exists(url: str, timeout: float = 15.0) -> bool:
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            r = client.head(url)
            if r.status_code == 200:
                return True
            if r.status_code in (403, 405):
                r2 = client.get(url)
                return r2.status_code == 200
            return False
    except Exception:
        return False


def fetch_reports(years: int = 10) -> List[Dict[str, object]]:
    now_year = datetime.now(tz=timezone.utc).year
    start = now_year - 1  # siste publiserte er vanligvis året før
    results: List[Dict[str, object]] = []

    for y in range(start, start - years, -1):
        row: Dict[str, object] = {
            "year": y,
            "title": f"Bufdirs årsrapport {y}",
            "page_url": None,
            "pdf_url": None,
            "status": "not_found",
        }

        for page in _candidate_pages(y):
            html = _fetch_html(page)
            if not html:
                continue
            pdfs = _extract_pdf_urls(html)
            best = _pick_best_pdf(pdfs, y)
            row["page_url"] = page
            row["pdf_url"] = best
            row["status"] = "ok" if best else "page_found_no_pdf"
            if best:
                break

        # Fallback: prøv kjente PDF-mønstre direkte
        if not row["pdf_url"]:
            for direct in _candidate_pdf_urls(y):
                if _url_exists(direct):
                    row["pdf_url"] = direct
                    row["status"] = "ok_direct_pattern"
                    break

        results.append(row)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Hent Bufdir årsrapporter")
    parser.add_argument("--years", type=int, default=10, help="Antall år bakover (default: 10)")
    args = parser.parse_args()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = fetch_reports(years=args.years)
    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source": "bufdir.no",
        "count": len(rows),
        "items": rows,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Skrev {len(rows)} rader til {OUT_FILE}")


if __name__ == "__main__":
    main()
