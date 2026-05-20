"""
SSB PxWebApi v2 – Statistics Norway Statbank integration.

Endpoints for searching tables, fetching metadata and data,
and combining SSB data with BEFS data.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import json
from pathlib import Path

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.services.external.api_clients.ssb_pxweb_client import SSBPxWebClient
from app.services.external.ssb_curated_tables import search_curated_tables
from app.services.external.ssb_table_taxonomy import CATEGORY_ORDER

router = APIRouter(tags=["SSB Statistikk"])

_CURATED_KEYS = frozenset(CATEGORY_ORDER)


# --- Request/Response schemas ---


class SSBDataSelectionItem(BaseModel):
    variableCode: str
    valueCodes: List[str]


class SSBCombineRequest(BaseModel):
    table_id: str
    value_codes: Optional[Dict[str, str]] = None
    selection: Optional[List[SSBDataSelectionItem]] = None
    befs_dataset: str  # region_costs | properties | contracts
    join_key: str  # region | kommune | year
    year: Optional[int] = None  # for BEFS data year


# --- Helpers ---


def _load_befs_region_costs(year: int) -> Dict[str, Any]:
    """Load total kost per region from JSON file."""
    data_dir = Path(__file__).resolve().parents[3] / "data"
    json_path = data_dir / f"total_kost_per_region_{year}.json"
    if not json_path.exists():
        return {"year": year, "by_region": {}}
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        by_category = data.get("by_category", {})
        by_region: Dict[str, float] = {}
        for cat, cat_data in by_category.items():
            region_totals = cat_data.get("by_region_totals", {})
            for region, amount in region_totals.items():
                by_region[region] = by_region.get(region, 0) + amount
        return {"year": year, "by_region": by_region}
    except Exception:
        return {"year": year, "by_region": {}}


# --- Endpoints ---


@router.get("/tables")
async def search_tables(
    query: Optional[str] = Query(None, description="Søk i tabelltitler og variabler"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lang: str = Query("no"),
    catalog: Optional[str] = Query(
        None,
        description="curated = kun Bufetat/Bufdir-kuraterte tabeller (alle eller filtrert med category)",
    ),
    category: Optional[str] = Query(
        None,
        description="Filtrer kuratert katalog (f.eks. utdanning, utenforskap). Aktiverer kuratert modus når verdien er kjent.",
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Søk tabeller i SSB Statbank Norge, eller i lokalt kuratert utvalg (catalog=curated / category=…).
    """
    cat = (catalog or "").strip().lower()
    ck = (category or "").strip().lower() or None
    use_curated = cat == "curated" or (ck is not None and ck in _CURATED_KEYS)
    if use_curated:
        return search_curated_tables(
            query=query,
            page=page,
            page_size=page_size,
            lang=lang,
            category=ck,
        )
    client = SSBPxWebClient()
    return await client.search_tables(
        query=query,
        page=page,
        page_size=page_size,
        lang=lang,
    )


@router.get("/tables/{table_id}")
async def get_table(
    table_id: str,
    lang: str = Query("no"),
    current_user: User = Depends(get_current_user),
):
    """
    Hent basisinfo for en tabell.
    """
    client = SSBPxWebClient()
    return await client.get_table(table_id, lang=lang)


@router.get("/tables/{table_id}/metadata")
async def get_table_metadata(
    table_id: str,
    lang: str = Query("no"),
    current_user: User = Depends(get_current_user),
):
    """
    Hent metadata (variabler, verdikoder) for en tabell.
    """
    client = SSBPxWebClient()
    return await client.get_metadata(table_id, lang=lang)


@router.get("/tables/{table_id}/data")
async def get_table_data_get(
    request: Request,
    table_id: str,
    output_format: str = Query("json-stat2"),
    lang: str = Query("no"),
    current_user: User = Depends(get_current_user),
):
    """
    Hent data fra tabell via GET.
    Bruk valueCodes[Tid]=2024* etc. som query-params for filtrering.
    """
    value_codes: Dict[str, str] = {}
    for key, val in request.query_params.items():
        if "valuecodes[" in key.lower() or "valueCodes[" in key:
            start = key.index("[") + 1
            end = key.index("]")
            var = key[start:end]
            value_codes[var] = val
    client = SSBPxWebClient()
    result = await client.get_data(
        table_id=table_id,
        value_codes=value_codes,
        output_format=output_format,
        lang=lang,
    )
    if output_format in ("csv", "html", "xlsx"):
        from fastapi.responses import Response
        content_type = {
            "csv": "text/csv",
            "html": "text/html",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }.get(output_format, "application/octet-stream")
        return Response(content=result, media_type=content_type)
    return result


@router.post("/tables/{table_id}/data")
async def get_table_data_post(
    table_id: str,
    body: Optional[Dict[str, Any]] = None,
    output_format: str = Query("json-stat2"),
    lang: str = Query("no"),
    current_user: User = Depends(get_current_user),
):
    """
    Hent data fra tabell via POST med selection-body.
    Body: {"selection": [{"variableCode": "Tid", "valueCodes": ["top(3)"]}]}
    """
    client = SSBPxWebClient()
    selection = None
    if body and "selection" in body:
        selection = body["selection"]
    result = await client.get_data(
        table_id=table_id,
        selection=selection,
        output_format=output_format,
        lang=lang,
    )
    if output_format in ("csv", "html", "xlsx"):
        from fastapi.responses import Response
        content_type = {
            "csv": "text/csv",
            "html": "text/html",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }.get(output_format, "application/octet-stream")
        return Response(content=result, media_type=content_type)
    return result


@router.post("/combine")
async def combine_ssb_befs(
    req: SSBCombineRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kombiner SSB-data med BEFS-data.
    befs_dataset: region_costs | properties | contracts
    join_key: region | kommune | year
    """
    client = SSBPxWebClient()
    year = req.year or 2025

    # 1. Fetch SSB data
    selection = None
    if req.selection:
        selection = [{"variableCode": s.variableCode, "valueCodes": s.valueCodes} for s in req.selection]
    ssb_raw = await client.get_data(
        table_id=req.table_id,
        value_codes=req.value_codes,
        selection=selection,
        output_format="json-stat2",
    )

    # 2. Fetch BEFS data
    if req.befs_dataset == "region_costs":
        befs_data = _load_befs_region_costs(year)
        befs_by_key = befs_data.get("by_region", {})
    elif req.befs_dataset == "properties":
        from sqlalchemy import select, func
        from app.domains.core.models.property import Property
        from app.core.property_access import filter_properties_by_access

        result = await db.execute(select(Property))
        all_props = result.scalars().all()
        accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))
        by_region: Dict[str, int] = {}
        for p in accessible:
            r = (p.region or "Ukjent")
            by_region[r] = by_region.get(r, 0) + 1
        befs_by_key = by_region
    elif req.befs_dataset == "contracts":
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.domains.core.models.contract import Contract
        from app.domains.core.models.unit import Unit
        from app.domains.core.models.property import Property
        from app.core.property_access import filter_properties_by_access

        stmt = select(Contract).options(selectinload(Contract.unit).selectinload(Unit.property))
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        all_props = []
        for c in contracts:
            if c.unit and c.unit.property:
                all_props.append(c.unit.property)
        unique_props = list({p.property_id: p for p in all_props}.values())
        filtered = await filter_properties_by_access(db=db, user=current_user, properties=unique_props)
        allowed = {p.property_id for p in filtered}
        by_region: Dict[str, int] = {}
        for c in contracts:
            if c.unit and c.unit.property and c.unit.property.property_id in allowed:
                r = (c.unit.property.region or "Ukjent")
                by_region[r] = by_region.get(r, 0) + 1
        befs_by_key = by_region
    else:
        raise HTTPException(status_code=400, detail=f"Unknown befs_dataset: {req.befs_dataset}")

    # 3. Parse json-stat2 and join (simplified – flatten to rows for frontend)
    combined = {
        "ssb": ssb_raw,
        "befs": {"by_key": befs_by_key, "join_key": req.join_key, "year": year},
    }
    return combined
