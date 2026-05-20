"""Nasjonal katalog barnevernsinstitusjoner (Bufdir) med valgfri kobling til BEFS-eiendom."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.domains.core.models.user import User

router = APIRouter(tags=["Bufdir catalog"])

BACKEND_ROOT = Path(__file__).resolve().parents[3]
INSTITUTIONS_FILE = BACKEND_ROOT / "bufdir_institutions.json"
MATCHES_FILE = BACKEND_ROOT / "bufdir_matches_robust.json"


class BufdirCatalogItem(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    owner_type: Optional[str] = None
    bufdir_url: Optional[str] = None
    image_url: Optional[str] = None
    legal_bases: List[str] = Field(default_factory=list)
    property_id: Optional[str] = None
    in_befs_portfolio: bool = False


class BufdirCatalogResponse(BaseModel):
    generated_at: str
    source_file: str
    matches_file: str
    count: int
    matched_count: int
    items: List[BufdirCatalogItem]


def _load_id_to_property() -> dict[int, str]:
    if not MATCHES_FILE.exists():
        return {}
    try:
        with open(MATCHES_FILE, encoding="utf-8") as f:
            matches = json.load(f)
    except Exception:
        return {}
    out: dict[int, str] = {}
    for m in matches:
        if not isinstance(m, dict):
            continue
        bd = m.get("bufdir_data") or {}
        bid = bd.get("id")
        pid = m.get("property_id")
        if bid is not None and pid:
            try:
                out[int(bid)] = str(pid)
            except (TypeError, ValueError):
                continue
    return out


@router.get("/institutions", response_model=BufdirCatalogResponse)
async def list_bufdir_institutions_catalog(
    current_user: User = Depends(get_current_user),
):
    """
    Full liste fra `bufdir_institutions.json` (synket fra bufdir.no), uavhengig av om institusjonen er «egen» eiendom eller kjøp av plass hos privat/frivillig sektor.

    `property_id` settes når `match_bufdir_robust.py` har funnet treff mot en eiendom i BEFS.
    """
    if not INSTITUTIONS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Mangler bufdir_institutions.json. Kjør: "
                "python backend/scripts/fetch_bufdir_data.py --default-filters"
            ),
        )
    try:
        raw = json.loads(INSTITUTIONS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Kunne ikke lese bufdir_institutions.json: {exc}",
        ) from exc

    if not isinstance(raw, list):
        raise HTTPException(
            status_code=500,
            detail="bufdir_institutions.json har uventet format (forventet liste).",
        )

    id_to_prop = _load_id_to_property()
    items: list[BufdirCatalogItem] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        bid = row.get("id")
        try:
            iid = int(bid) if bid is not None else None
        except (TypeError, ValueError):
            iid = None
        pid = id_to_prop.get(iid) if iid is not None else None
        lb = row.get("legal_bases") or []
        if not isinstance(lb, list):
            lb = []
        items.append(
            BufdirCatalogItem(
                id=iid,
                name=row.get("name"),
                address=row.get("address"),
                location=row.get("location"),
                owner_type=row.get("owner_type"),
                bufdir_url=row.get("bufdir_url"),
                image_url=row.get("image_url"),
                legal_bases=[str(x) for x in lb],
                property_id=pid,
                in_befs_portfolio=bool(pid),
            )
        )

    matched = sum(1 for it in items if it.in_befs_portfolio)
    return BufdirCatalogResponse(
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        source_file=str(INSTITUTIONS_FILE.name),
        matches_file=str(MATCHES_FILE.name) if MATCHES_FILE.exists() else "(mangler)",
        count=len(items),
        matched_count=matched,
        items=items,
    )
