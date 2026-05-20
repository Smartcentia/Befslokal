#!/usr/bin/env python3
"""
Genererer en presentasjonsklar analyse basert på:
- stprp_bufdir.json
- bufdir_arsrapporter.json
- ssb_bufetat_bufdir_tables.json

Output:
- backend/data/barnevern_reports_analysis.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "backend" / "data"
OUT_FILE = DATA_DIR / "barnevern_reports_analysis.json"


def _load(name: str) -> Dict[str, Any]:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_analysis() -> Dict[str, Any]:
    stprp = _load("stprp_bufdir.json")
    annual = _load("bufdir_arsrapporter.json")
    ssb = _load("ssb_bufetat_bufdir_tables.json")

    stprp_items: List[Dict[str, Any]] = stprp.get("items") or []
    annual_items: List[Dict[str, Any]] = annual.get("items") or []
    ssb_items: List[Dict[str, Any]] = ssb.get("items") or []

    stprp_count = len(stprp_items)
    annual_total = len(annual_items)
    annual_pdf_count = sum(1 for r in annual_items if (r.get("status") or "").startswith("ok"))
    ssb_count = len(ssb_items)

    keyword_hits: Dict[str, int] = {}
    for item in stprp_items:
        for term in item.get("match_terms") or []:
            keyword_hits[term] = keyword_hits.get(term, 0) + 1
    top_keywords = sorted(keyword_hits.items(), key=lambda x: x[1], reverse=True)[:6]

    highlights = [
        f"Datagrunnlaget inneholder {stprp_count} relevante St.prp./Prop-saker for Bufdir/Bufetat-relaterte tema.",
        f"Årsrapportdekning er {annual_pdf_count} av {annual_total} siste år med funnet PDF-lenke.",
        f"SSB-kortlisten inneholder {ssb_count} tabeller som støtter analyse av barnevern/fosterhjem/familievern.",
    ]
    if top_keywords:
        joined = ", ".join([f"{k} ({v})" for k, v in top_keywords])
        highlights.append(f"Mest fremtredende tematreff i St.prp.-utvalget: {joined}.")

    risks = []
    if annual_pdf_count < annual_total:
        missing_years = [str(r.get("year")) for r in annual_items if not (r.get("status") or "").startswith("ok")]
        risks.append(f"Manglende direkte PDF-treff for årsrapport i år: {', '.join(missing_years)}.")
    if stprp_count < 10:
        risks.append("Lavt antall St.prp.-treff kan indikere for streng filtrering eller behov for flere sesjoner.")
    if not risks:
        risks.append("Ingen kritiske datagap identifisert i nåværende grunnlag.")

    recommended_actions = [
        "Valider manuelt at alle St.prp.-saker er direkte relevante for BFD/Bufdir før endelig publisering.",
        "Utvid årsrapport-fallback med historiske arkivkilder for år som mangler PDF-lenker.",
        "Prioriter 5-10 SSB-tabeller fra kortlisten for faste KPI-er i månedlig styringsrapport.",
        "Bruk KI-Kollega-verktøyene for rapportoversikt og analysetekst i ledermøter.",
    ]

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "summary": {
            "stprp_count": stprp_count,
            "annual_report_total": annual_total,
            "annual_report_pdf_count": annual_pdf_count,
            "ssb_table_count": ssb_count,
        },
        "highlights": highlights,
        "risks": risks,
        "recommended_actions": recommended_actions,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_analysis()
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Skrev analyse til {OUT_FILE}")


if __name__ == "__main__":
    main()
