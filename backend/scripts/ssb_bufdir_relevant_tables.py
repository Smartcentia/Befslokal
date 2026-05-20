#!/usr/bin/env python3
"""
Finn og lagre SSB-tabeller som er relevante for Bufetat/Bufdir-tema
(barnevern/fosterhjem/institusjon/familievern).

Kjør fra prosjektrot:
  python backend/scripts/ssb_bufdir_relevant_tables.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT_FILE = BACKEND / "data" / "ssb_bufetat_bufdir_tables.json"

sys.path.insert(0, str(BACKEND))

from app.services.external.api_clients.ssb_pxweb_client import SSBPxWebClient  # noqa: E402

QUERIES = [
    "barnevern",
    "fosterhjem",
    "institusjon barnevern",
    "familievern",
    "adopsjon",
    "NEET",
]

KEYWORDS = [
    "barnevern",
    "fosterhjem",
    "familievern",
    "adopsjon",
    "institusjon",
]


def _is_relevant(label: str) -> bool:
    s = (label or "").lower()
    return any(k in s for k in KEYWORDS)


async def build_shortlist() -> List[Dict[str, Any]]:
    client = SSBPxWebClient()
    by_id: Dict[str, Dict[str, Any]] = {}

    for q in QUERIES:
        page = 1
        while page <= 5:  # begrens API-belastning
            res = await client.search_tables(query=q, page=page, page_size=50, lang="no")
            tables = res.get("tables") or []
            if not tables:
                break
            for t in tables:
                tid = str(t.get("id"))
                label = t.get("label") or ""
                if not _is_relevant(label):
                    continue
                by_id[tid] = {
                    "id": tid,
                    "label": label,
                    "updated": t.get("updated"),
                    "firstPeriod": t.get("firstPeriod"),
                    "lastPeriod": t.get("lastPeriod"),
                    "variableNames": t.get("variableNames") or [],
                    "sourceQuery": q,
                    "dataUrl": next((l.get("href") for l in (t.get("links") or []) if l.get("rel") == "data"), None),
                    "metadataUrl": next((l.get("href") for l in (t.get("links") or []) if l.get("rel") == "metadata"), None),
                }
            page_info = res.get("page") or {}
            total_pages = int(page_info.get("totalPages") or 1)
            if page >= total_pages:
                break
            page += 1

    rows = list(by_id.values())
    rows.sort(key=lambda x: (x.get("lastPeriod") or "", x.get("updated") or "", x.get("id") or ""), reverse=True)
    return rows[:40]


async def main_async() -> None:
    rows = await build_shortlist()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source": "SSB PxWebApi v2",
        "queries": QUERIES,
        "count": len(rows),
        "items": rows,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Skrev {len(rows)} tabeller til {OUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main_async())
