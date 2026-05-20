#!/usr/bin/env python3
"""
Match GL-/koststed-navn (f.eks. umappede dim1-tekster) mot Bufdir familievernkontor.

Leser backend/data/familievernkontor_bufdir.json (kjør scrape_familievernkontor_bufdir.py ved behov).
For hvert søkenavn: fuzzy-match mot official_name, slug og listetekst; foreslår adresse(r) fra
samme logikk som familievernkontor_bufdir_mapping.extract_auto_mappings_from_office.

Ingen database-skriving — kun JSON/CSV for manuell opprettelse av Property.

  cd backend && python3 scripts/suggest_gl_names_from_bufdir_familievern.py
  cd backend && python3 scripts/suggest_gl_names_from_bufdir_familievern.py --queries-file mine_navn.txt
  cd backend && python3 scripts/suggest_gl_names_from_bufdir_familievern.py -q "Familievernkontoret X" -q "..."
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from familievernkontor_bufdir_mapping import _contact_section, extract_auto_mappings_from_office

BUFDIR_JSON = _BACKEND / "data" / "familievernkontor_bufdir.json"
# Når hoved-regex ikke treffer (f.eks. «gate – nr, postnr sted»)
_FALLBACK_ADDR = re.compile(
    r"(.+?),\s*(\d{4})\s+(\S+)",
    re.MULTILINE,
)
DEFAULT_OUT_JSON = _BACKEND / "data" / "gl_name_bufdir_suggestions.json"
DEFAULT_OUT_CSV = _BACKEND / "data" / "gl_name_bufdir_suggestions.csv"

_STOP = frozenset(
    "og i for av den det en et ei på til som er med fra ved ut inn mot om "
    "no å de ja nei avd avdeling".split()
)

# Typiske umappede koststed-navn fra kartlegging (kan overstyres med --queries / fil)
DEFAULT_QUERIES: list[str] = [
    "Familievernkontoret Innherred",
    "Telemark barne- og familiesenter",
    "FHT RN - adm",
    "Fosterhjemstjenesten",
    "Tromsø familievernkontor",
    "MST Trøndelag Nord",
    "MST Tromsø",
    "MST Vestfold 1",
    "Agder barne- og familiesenter",
]


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[\s\-–—]+", " ", s)
    return s


def _tokens(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9æøå\s]", " ", _norm(s))
    return {t for t in s.split() if len(t) > 2 and t not in _STOP}


def _haystack(office: dict[str, Any]) -> str:
    parts = [
        office.get("official_name") or "",
        (office.get("slug") or "").replace("-", " "),
        office.get("list_page_link_text") or "",
    ]
    return _norm(" ".join(parts))


def _score(query: str, office: dict[str, Any]) -> float:
    qn = _norm(query)
    if not qn:
        return 0.0
    official = _norm(office.get("official_name") or "")
    hay = _haystack(office)

    r1 = SequenceMatcher(None, qn, official).ratio() if official else 0.0
    r2 = SequenceMatcher(None, qn, hay).ratio() if hay else 0.0
    r_sub = 0.95 if qn in hay or qn in official else 0.0

    tq, to = _tokens(query), _tokens(official + " " + hay)
    if not tq or not to:
        j = 0.0
    else:
        inter = tq & to
        j = len(inter) / len(tq | to)

    return max(r1, r2, r_sub, min(1.0, j * 1.15))


def _fallback_from_contact(office: dict[str, Any]) -> list[dict[str, Any]]:
    text = _contact_section(office)
    if not text:
        return []
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for m in _FALLBACK_ADDR.finditer(text):
        street = m.group(1).strip().strip("–—-").strip()
        postal = m.group(2).strip()
        if len(street) < 4 or not postal.isdigit():
            continue
        low = street.lower()
        if "postboks" in low or low.startswith("boks "):
            continue
        if "personopplysning" in low or "journal" in low:
            continue
        key = (low, postal)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "address_pattern": street,
                "postal": postal,
                "source": "bufdir_contact_fallback",
            }
        )
    return out


def _pick_addresses(office: dict[str, Any]) -> list[dict[str, Any]]:
    raw = extract_auto_mappings_from_office(office)
    raw.extend(_fallback_from_contact(office))
    physical: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for m in raw:
        pat = (m.get("address_pattern") or "").strip()
        post = (m.get("postal") or "").strip()
        key = (pat.lower(), post)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        low = pat.lower()
        if "postboks" in low or low.startswith("boks "):
            continue
        physical.append(m)
    if physical:
        return physical
    return raw


def _rank_offices(
    query: str, offices: list[dict[str, Any]], top_n: int
) -> list[tuple[float, dict[str, Any]]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for o in offices:
        if o.get("error"):
            continue
        s = _score(query, o)
        if s > 0:
            scored.append((s, o))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_n]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Foreslå Bufdir familievern-treff + adresser for GL/koststed-navn"
    )
    ap.add_argument(
        "-q",
        "--query",
        action="append",
        dest="queries",
        help="Søkestreng (gjenta for flere)",
    )
    ap.add_argument(
        "--queries-file",
        type=Path,
        help="Én søkestreng per linje (# starter kommentar)",
    )
    ap.add_argument(
        "--bufdir-json",
        type=Path,
        default=BUFDIR_JSON,
        help="Path til familievernkontor_bufdir.json",
    )
    ap.add_argument("--top", type=int, default=5, help="Antall forslag per navn")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    ap.add_argument(
        "--no-default-queries",
        action="store_true",
        help="Ikke bruk innebygd liste (krever -q eller --queries-file)",
    )
    args = ap.parse_args()

    queries: list[str] = []
    if args.queries:
        queries.extend(args.queries)
    if args.queries_file:
        text = args.queries_file.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            queries.append(line)
    if not queries and not args.no_default_queries:
        queries = list(DEFAULT_QUERIES)
    if not queries:
        print("Ingen søkestrenger. Bruk -q, --queries-file eller fjern --no-default-queries.", file=sys.stderr)
        return 1

    if not args.bufdir_json.exists():
        print(
            f"Mangler {args.bufdir_json}. Kjør: cd backend && python3 scripts/scrape_familievernkontor_bufdir.py",
            file=sys.stderr,
        )
        return 1

    data = json.loads(args.bufdir_json.read_text(encoding="utf-8"))
    offices: list[dict[str, Any]] = list(data.get("offices") or [])

    results: list[dict[str, Any]] = []
    for q in queries:
        ranked = _rank_offices(q, offices, args.top)
        suggestions: list[dict[str, Any]] = []
        for rank, (sc, o) in enumerate(ranked, start=1):
            addrs = _pick_addresses(o)
            suggestions.append(
                {
                    "rank": rank,
                    "score": round(sc, 4),
                    "official_name": o.get("official_name"),
                    "slug": o.get("slug"),
                    "region": o.get("region"),
                    "url": o.get("url"),
                    "phones": o.get("phones"),
                    "address_suggestions": [
                        {
                            "street_or_pattern": a.get("address_pattern"),
                            "postal": a.get("postal"),
                            "source": a.get("source"),
                        }
                        for a in addrs[:8]
                    ],
                }
            )
        best = ranked[0][0] if ranked else 0.0
        results.append(
            {
                "query": q,
                "best_score": round(best, 4),
                "bufdir_likely_match": best >= 0.42,
                "note": None
                if best >= 0.42
                else "Lav score — sjekk manuelt (kan være MST/BFS/adm; ikke i familievern-lista).",
                "suggestions": suggestions,
            }
        )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_json": str(args.bufdir_json),
        "queries": results,
    }
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "query",
                "best_score",
                "likely_match",
                "rank",
                "matched_name",
                "url",
                "address",
                "postal",
            ]
        )
        for block in results:
            q = block["query"]
            bs = block["best_score"]
            likely = block["bufdir_likely_match"]
            for sug in block["suggestions"]:
                addrs = sug.get("address_suggestions") or []
                if addrs:
                    for a in addrs:
                        w.writerow(
                            [
                                q,
                                bs,
                                likely,
                                sug["rank"],
                                sug.get("official_name"),
                                sug.get("url"),
                                a.get("street_or_pattern"),
                                a.get("postal"),
                            ]
                        )
                else:
                    w.writerow(
                        [
                            q,
                            bs,
                            likely,
                            sug["rank"],
                            sug.get("official_name"),
                            sug.get("url"),
                            "",
                            "",
                        ]
                    )

    print(f"Skrev {args.out_json} og {args.out_csv} ({len(queries)} søk)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
