"""Leser ferdiggenererte dokumentlister for barnevern/Bufdir."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_current_user
from app.domains.core.models.user import User

router = APIRouter(tags=["Barnevern Documents"])

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
STPRP_FILE = DATA_DIR / "stprp_bufdir.json"
ANNUAL_FILE = DATA_DIR / "bufdir_arsrapporter.json"
SSB_FILE = DATA_DIR / "ssb_bufetat_bufdir_tables.json"
ANALYSIS_FILE = DATA_DIR / "barnevern_reports_analysis.json"
STATSBUDSJETTET_FILE = DATA_DIR / "statsbudsjettet_bfd_barnevern.json"
FINANS_DIR = Path(__file__).resolve().parents[4] / "finans"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Mangler datafil: {path.name}")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Kunne ikke lese {path.name}: {exc}") from exc


def _generate_analysis_payload() -> Dict[str, Any]:
    stprp = _read_json(STPRP_FILE) if STPRP_FILE.exists() else {}
    annual = _read_json(ANNUAL_FILE) if ANNUAL_FILE.exists() else {}
    ssb = _read_json(SSB_FILE) if SSB_FILE.exists() else {}

    stprp_items = stprp.get("items") or []
    annual_items = annual.get("items") or []
    ssb_items = ssb.get("items") or []

    stprp_count = len(stprp_items)
    annual_total = len(annual_items)
    annual_pdf_count = sum(1 for r in annual_items if str(r.get("status") or "").startswith("ok"))
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
        missing_years = [str(r.get("year")) for r in annual_items if not str(r.get("status") or "").startswith("ok")]
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


@router.get("/stprp")
async def get_stprp(current_user: User = Depends(get_current_user)):
    return _read_json(STPRP_FILE)


@router.get("/annual-reports")
async def get_annual_reports(current_user: User = Depends(get_current_user)):
    return _read_json(ANNUAL_FILE)


@router.get("/ssb-shortlist")
async def get_ssb_shortlist(current_user: User = Depends(get_current_user)):
    return _read_json(SSB_FILE)


@router.get("/statsbudsjettet")
async def get_statsbudsjettet_bfd(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """BFD-bevilgninger fra statsbudsjettet for barnevern/familievern, per kapittelpost."""
    data = _read_json(STATSBUDSJETTET_FILE)
    if year is not None:
        year_str = str(year)
        aar_data = data.get("aar", {})
        if year_str not in aar_data:
            raise HTTPException(
                status_code=404,
                detail=f"År {year} ikke funnet. Tilgjengelige: {sorted(aar_data.keys())}",
            )
        return {
            "kilde": data.get("kilde"),
            "enhet": data.get("enhet"),
            "sist_oppdatert": data.get("sist_oppdatert"),
            "year": year,
            "kapitler": aar_data[year_str]["kapitler"],
        }
    return data


@router.get("/analysis")
async def get_analysis(current_user: User = Depends(get_current_user)):
    return _read_json(ANALYSIS_FILE)


@router.post("/analysis/regenerate")
async def regenerate_analysis(current_user: User = Depends(get_current_user)):
    payload = _generate_analysis_payload()
    ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", "analysis": payload}


@router.get("/prediction-excel")
async def list_prediction_excel(current_user: User = Depends(get_current_user)):
    patterns = [
        "Prediksjon_*_Økonomi.xlsx",
        "Prediksjon_*_Lønn.xlsx",
    ]
    files: List[Dict[str, Any]] = []
    for pattern in patterns:
        for p in sorted(FINANS_DIR.glob(pattern), reverse=True):
            files.append(
                {
                    "filename": p.name,
                    "size_bytes": p.stat().st_size,
                    "updated_at": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                    "download_url": f"/api/v1/barnevern-docs/prediction-excel/{p.name}",
                }
            )
    return {"count": len(files), "items": files}


@router.get("/prediction-excel/{filename}")
async def download_prediction_excel(filename: str, current_user: User = Depends(get_current_user)):
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Ugyldig filnavn")
    path = FINANS_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    if not filename.startswith("Prediksjon_") or not filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Kun prediksjonsfiler er tillatt")
    return FileResponse(path=str(path), filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
