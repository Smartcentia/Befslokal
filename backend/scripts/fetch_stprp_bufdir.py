#!/usr/bin/env python3
"""
Hent siste St.prp./Prop-saker relevante for Bufdir/Bufetat/barnevern
fra Stortingets åpne data og lagre som JSON.

Kjør fra prosjektrot:
  python backend/scripts/fetch_stprp_bufdir.py --limit 10
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
OUT_FILE = BACKEND / "data" / "stprp_bufdir.json"

sys.path.insert(0, str(BACKEND))

from app.services.external.api_clients.stortinget_open_data_client import StortingetOpenDataClient  # noqa: E402

STRONG_KEYWORDS = [
    "bufdir",
    "bufetat",
    "barnevern",
    "fosterhjem",
]

MEDIUM_KEYWORDS = [
    "familievern",
    "barnevernsinstitusjon",
    "institusjon",
    "barn",
    "familie",
    "oppvekst",
]


def _dotnet_date_to_iso(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None
    m = re.search(r"/Date\((\d+)", value)
    if not m:
        return None
    ms = int(m.group(1))
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def _is_proposition_case(case: Dict[str, Any]) -> bool:
    # dokumentgruppe=1 er "proposisjon" i Stortingets data
    if case.get("dokumentgruppe") == 1:
        return True
    ref = (case.get("henvisning") or "").lower()
    return "prop." in ref or "st.prp" in ref


def _relevance(case: Dict[str, Any]) -> Tuple[int, List[str]]:
    text = " ".join(
        [
            str(case.get("tittel") or ""),
            str(case.get("korttittel") or ""),
            str(case.get("henvisning") or ""),
            " ".join((e.get("navn") or "") for e in (case.get("emne_liste") or [])),
        ]
    ).lower()
    score = 0
    terms: List[str] = []
    for k in STRONG_KEYWORDS:
        if k in text:
            score += 3
            terms.append(k)
    for k in MEDIUM_KEYWORDS:
        if k in text:
            score += 1
            terms.append(k)
    return score, sorted(set(terms))


def _get_prop_url_from_sak_detail(detail: Dict[str, Any]) -> str | None:
    refs = detail.get("publikasjon_referanse_liste") or []
    for ref in refs:
        if ref.get("type") == 1 or str(ref.get("undertype") or "").lower() == "proposisjon":
            url = ref.get("lenke_url")
            if isinstance(url, str) and url.strip():
                if url.startswith("//"):
                    return f"https:{url}"
                return url
    return None


def fetch(limit: int = 10, max_sessions: int = 14) -> List[Dict[str, Any]]:
    client = StortingetOpenDataClient(timeout=90.0)
    sesjoner = client.list_sesjon_ids(max_sessions=max_sessions)

    candidates: List[Dict[str, Any]] = []
    for sesjon_id in sesjoner:
        payload = client.saker(sesjon_id)
        for case in payload.get("saker_liste") or []:
            if not _is_proposition_case(case):
                continue
            relevance_score, matched_terms = _relevance(case)
            if relevance_score < 3:
                continue
            case["_match_score"] = relevance_score
            case["_match_terms"] = matched_terms
            candidates.append(case)

    # Nyeste først
    candidates.sort(
        key=lambda x: (
            _dotnet_date_to_iso(x.get("sist_oppdatert_dato") or x.get("dato")) or "",
            int(x.get("_match_score") or 0),
        ),
        reverse=True,
    )

    out: List[Dict[str, Any]] = []
    seen_ids = set()
    for case in candidates:
        sakid = case.get("id")
        if sakid in seen_ids:
            continue
        seen_ids.add(sakid)

        detail = client.sak(int(sakid))
        out.append(
            {
                "sak_id": sakid,
                "sesjon": case.get("behandlet_sesjon_id") or case.get("sak_sesjon"),
                "title": case.get("tittel"),
                "short_title": case.get("korttittel"),
                "reference": case.get("henvisning"),
                "dokumentgruppe": case.get("dokumentgruppe"),
                "updated_date": _dotnet_date_to_iso(case.get("sist_oppdatert_dato")),
                "date": _dotnet_date_to_iso(case.get("dato")),
                "match_score": case.get("_match_score"),
                "match_terms": case.get("_match_terms"),
                "prop_url": _get_prop_url_from_sak_detail(detail),
                "storting_sak_url": f"https://data.stortinget.no/eksport/sak?sakid={sakid}",
            }
        )
        if len(out) >= limit:
            break

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Hent siste St.prp./Prop relevante for Bufdir")
    parser.add_argument("--limit", type=int, default=10, help="Antall saker (default: 10)")
    parser.add_argument("--sessions", type=int, default=14, help="Antall sesjoner å skanne bakover")
    args = parser.parse_args()

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = fetch(limit=args.limit, max_sessions=args.sessions)
    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source": "Stortinget åpne data",
        "count": len(rows),
        "items": rows,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Skrev {len(rows)} saker til {OUT_FILE}")


if __name__ == "__main__":
    main()
