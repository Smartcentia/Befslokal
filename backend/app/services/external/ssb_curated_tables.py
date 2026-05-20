"""
Kuraterte SSB-tabeller for barnevern, familievern m.m.

Datafil: backend/data/ssb_bufetat_bufdir_tables.json (bygges med ssb_bufdir_relevant_tables.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.external.ssb_table_taxonomy import classify_ssb_table

CURATED_SSB_FILE = Path(__file__).resolve().parents[3] / "data" / "ssb_bufetat_bufdir_tables.json"
SSB_TABLES_PUBLIC_BASE = "https://data.ssb.no/api/pxwebapi/v2/tables"


def load_curated_ssb_items() -> List[Dict[str, Any]]:
    if not CURATED_SSB_FILE.exists():
        return []
    try:
        with open(CURATED_SSB_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return list(data.get("items") or [])
    except Exception:
        return []


def shortlist_row_to_table(item: Dict[str, Any], lang: str) -> Dict[str, Any]:
    tid = str(item.get("id", ""))
    sq = (item.get("sourceQuery") or "").strip() or "barnevern"
    cats = item.get("categories")
    if not isinstance(cats, list) or not cats:
        cats = classify_ssb_table(item.get("label"), item.get("variableNames"), tid)
    return {
        "id": tid,
        "label": item.get("label") or "",
        "description": "",
        "firstPeriod": item.get("firstPeriod"),
        "lastPeriod": item.get("lastPeriod"),
        "variableNames": item.get("variableNames") or [],
        "categories": cats,
        "paths": [[{"id": "", "label": "Barnevern og familievern", "sortCode": ""}]],
        "subjectCode": sq,
        "links": [
            {"rel": "self", "href": f"{SSB_TABLES_PUBLIC_BASE}/{tid}?lang={lang}"},
            {
                "rel": "data",
                "href": item.get("dataUrl")
                or f"{SSB_TABLES_PUBLIC_BASE}/{tid}/data?lang={lang}&outputFormat=json-stat2",
            },
            {
                "rel": "metadata",
                "href": item.get("metadataUrl") or f"{SSB_TABLES_PUBLIC_BASE}/{tid}/metadata?lang={lang}",
            },
        ],
    }


def filter_items_by_category(items: List[Dict[str, Any]], category: Optional[str]) -> List[Dict[str, Any]]:
    if not category or not str(category).strip():
        return items
    ck = str(category).strip().lower()
    out: List[Dict[str, Any]] = []
    for it in items:
        cats = it.get("categories")
        if not isinstance(cats, list) or not cats:
            cats = classify_ssb_table(
                it.get("label"),
                it.get("variableNames"),
                str(it.get("id", "")),
            )
        if ck in cats:
            out.append(it)
    return out


def filter_curated_items(items: List[Dict[str, Any]], query: Optional[str]) -> List[Dict[str, Any]]:
    if not query or not str(query).strip():
        return list(items)
    q = str(query).strip().lower()
    out: List[Dict[str, Any]] = []
    for it in items:
        label = (it.get("label") or "").lower()
        sq = (it.get("sourceQuery") or "").lower()
        vars_blob = " ".join(str(v) for v in (it.get("variableNames") or [])).lower()
        tid = str(it.get("id", "")).lower()
        if q in label or q in sq or q in vars_blob or q in tid:
            out.append(it)
    return out


def page_curated_tables(
    items: List[Dict[str, Any]],
    page: int,
    page_size: int,
    lang: str,
) -> Dict[str, Any]:
    items = sorted(items, key=lambda x: (x.get("label") or ""))
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    start = (page - 1) * page_size
    slice_ = items[start : start + page_size]
    tables = [shortlist_row_to_table(it, lang) for it in slice_]
    return {
        "language": lang,
        "tables": tables,
        "page": {
            "pageNumber": page,
            "pageSize": page_size,
            "totalElements": total,
            "totalPages": total_pages,
        },
    }


def search_curated_tables(
    query: Optional[str],
    page: int,
    page_size: int,
    lang: str,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    raw = load_curated_ssb_items()
    filtered = filter_curated_items(raw, query)
    filtered = filter_items_by_category(filtered, category)
    return page_curated_tables(filtered, page=page, page_size=page_size, lang=lang)
