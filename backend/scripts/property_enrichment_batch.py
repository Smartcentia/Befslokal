#!/usr/bin/env python3
"""
Property enrichment pipeline (baseline + auto updates).

What it does:
1) Builds a baseline for data quality:
   - missing name
   - name equals address
   - name looks like address
   - missing description
   - missing image (from external_data.bufdir.image_path)
2) Enriches properties using bufdir_matches_robust.json:
   - auto-updates property name (score-gated)
   - updates description (empty only unless --force-description)
   - downloads image to frontend/public/bufdir_images
   - stores source/confidence/timestamp in external_data
3) Enriches provider context from contracts/parties.

Default mode is dry-run. Use --apply to persist changes.

Run examples:
  cd backend && PYTHONPATH=. .venv/bin/python scripts/property_enrichment_batch.py
  cd backend && PYTHONPATH=. .venv/bin/python scripts/property_enrichment_batch.py --apply --min-score 0.65
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
MATCHES_FILE = BACKEND_DIR / "bufdir_matches_robust.json"
DEFAULT_REPORT_FILE = BACKEND_DIR / "data" / "property_enrichment_report.json"
IMAGES_DIR = PROJECT_ROOT / "frontend" / "public" / "bufdir_images"

try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from lib.db_env import require_database_url_for_local_scripts
from lib.property_name_quality import is_address_only_name


@dataclass
class Stats:
    total_properties: int = 0
    missing_name: int = 0
    name_equals_address: int = 0
    name_looks_like_address: int = 0
    missing_description: int = 0
    missing_image: int = 0


def _norm(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_image_path(external_data: Optional[dict[str, Any]]) -> Optional[str]:
    if not isinstance(external_data, dict):
        return None
    bufdir = external_data.get("bufdir") or {}
    if not isinstance(bufdir, dict):
        return None
    path = (bufdir.get("image_path") or "").strip()
    return path or None


async def _download_image(url: str, property_id: str) -> Optional[str]:
    if not url:
        return None
    try:
        import httpx
    except Exception:
        return None

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    ext = url.split(".")[-1].split("?")[0].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"

    filename = f"{property_id}.{ext}"
    filepath = IMAGES_DIR / filename

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
        return f"/bufdir_images/{filename}"
    except Exception:
        return None


def _load_matches() -> dict[str, dict[str, Any]]:
    if not MATCHES_FILE.exists():
        raise FileNotFoundError(f"Match file not found: {MATCHES_FILE}")

    rows = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))
    best_by_property: dict[str, dict[str, Any]] = {}

    for row in rows:
        pid = str(row.get("property_id") or "").strip()
        if not pid:
            continue

        score = float(row.get("score") or 0.0)
        existing = best_by_property.get(pid)
        if existing is None or score > float(existing.get("score") or 0.0):
            best_by_property[pid] = row

    return best_by_property


async def _collect_baseline(db) -> Stats:
    result = await db.execute(select(Property))
    props = result.scalars().all()

    stats = Stats(total_properties=len(props))

    for p in props:
        name = (p.name or "").strip()
        addr = (p.address or "").strip()
        desc = (p.description or "").strip()

        if not name:
            stats.missing_name += 1
        if name and addr and _norm(name) == _norm(addr):
            stats.name_equals_address += 1
        if is_address_only_name(name, addr):
            stats.name_looks_like_address += 1
        if not desc:
            stats.missing_description += 1
        if not _current_image_path(p.external_data):
            stats.missing_image += 1

    return stats


async def _collect_providers(db, property_id: UUID) -> list[dict[str, Any]]:
    stmt = (
        select(Party.name, Party.orgnr, Contract.category)
        .join(Contract, Contract.party_id == Party.party_id)
        .join(Unit, Unit.unit_id == Contract.unit_id)
        .where(Unit.property_id == property_id)
    )
    rows = (await db.execute(stmt)).all()

    providers: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for r in rows:
        name = (r.name or "").strip()
        orgnr = (r.orgnr or "").strip()
        category = (r.category or "").strip()

        if not name:
            continue

        key = (_norm(name), orgnr, category)
        if key in seen:
            continue
        seen.add(key)

        providers.append(
            {
                "name": name,
                "orgnr": orgnr or None,
                "category": category or None,
            }
        )

    providers.sort(key=lambda x: x["name"].lower())
    return providers


async def run_enrichment(
    apply: bool,
    min_score: float,
    force_description: bool,
    download_images: bool,
    limit: Optional[int],
    report_file: Path,
) -> dict[str, Any]:
    require_database_url_for_local_scripts()

    best_matches = _load_matches()

    report: dict[str, Any] = {
        "started_at": _utc_iso(),
        "apply": apply,
        "min_score": min_score,
        "force_description": force_description,
        "download_images": download_images,
        "baseline_before": {},
        "baseline_after": {},
        "updated": {
            "properties_touched": 0,
            "names": 0,
            "descriptions": 0,
            "images": 0,
            "providers": 0,
        },
        "skipped_low_score": 0,
        "skipped_no_match": 0,
        "samples": [],
    }

    async with SessionLocal() as db:
        baseline_before = await _collect_baseline(db)
        report["baseline_before"] = baseline_before.__dict__

        result = await db.execute(select(Property))
        properties = result.scalars().all()
        if limit is not None:
            properties = properties[:limit]

        touched = 0

        for prop in properties:
            prop_id_str = str(prop.property_id)
            match = best_matches.get(prop_id_str)

            # Provider enrichment runs independently of Bufdir match.
            providers = await _collect_providers(db, prop.property_id)

            if prop.external_data is None or not isinstance(prop.external_data, dict):
                prop.external_data = {}

            old_name = prop.name
            old_desc = prop.description
            old_img = _current_image_path(prop.external_data)

            changed = False

            if providers:
                existing_providers = prop.external_data.get("providers")
                if existing_providers != providers:
                    prop.external_data["providers"] = providers
                    report["updated"]["providers"] += 1
                    changed = True

            if not match:
                report["skipped_no_match"] += 1
            else:
                score = float(match.get("score") or 0.0)
                if score < min_score:
                    report["skipped_low_score"] += 1
                else:
                    buf = match.get("bufdir_data") or {}

                    official_name = (buf.get("name") or "").strip()
                    description = (buf.get("description") or "").strip()
                    image_url = (buf.get("image_url") or "").strip()

                    if official_name and _norm(official_name) != _norm(prop.name):
                        prop.name = official_name
                        report["updated"]["names"] += 1
                        changed = True

                    if description and (force_description or not (prop.description or "").strip()):
                        if _norm(description) != _norm(prop.description):
                            prop.description = description
                            report["updated"]["descriptions"] += 1
                            changed = True

                    image_path = old_img
                    if download_images and image_url and not old_img:
                        downloaded = await _download_image(image_url, prop_id_str)
                        if downloaded:
                            image_path = downloaded
                            report["updated"]["images"] += 1
                            changed = True

                    bufdir_blob = {
                        "bufdir_id": buf.get("id"),
                        "institution_name": official_name or None,
                        "description": description or None,
                        "legal_bases": buf.get("legal_bases") or [],
                        "owner_type": buf.get("owner_type"),
                        "bufdir_url": buf.get("bufdir_url"),
                        "email": buf.get("email"),
                        "phone": buf.get("phone"),
                        "location": buf.get("location"),
                        "image_url": image_url or None,
                        "image_path": image_path,
                        "match_score": score,
                        "matched_property_name": match.get("property_name"),
                        "matched_institution_name": match.get("institution_name"),
                        "enriched_at": _utc_iso(),
                    }

                    current_blob = prop.external_data.get("bufdir")
                    if current_blob != bufdir_blob:
                        prop.external_data["bufdir"] = bufdir_blob
                        changed = True

            if changed:
                prop.external_data.setdefault("enrichment_meta", {})
                prop.external_data["enrichment_meta"]["latest_run_at"] = _utc_iso()
                prop.external_data["enrichment_meta"]["run_mode"] = "apply" if apply else "dry_run"
                flag_modified(prop, "external_data")
                touched += 1

            if changed and len(report["samples"]) < 25:
                report["samples"].append(
                    {
                        "property_id": prop_id_str,
                        "before": {
                            "name": old_name,
                            "description": old_desc,
                            "image_path": old_img,
                        },
                        "after": {
                            "name": prop.name,
                            "description": prop.description,
                            "image_path": _current_image_path(prop.external_data),
                        },
                    }
                )

        report["updated"]["properties_touched"] = touched

        if apply:
            await db.commit()
        else:
            await db.rollback()

        baseline_after = await _collect_baseline(db)
        report["baseline_after"] = baseline_after.__dict__

    report["finished_at"] = _utc_iso()

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Property enrichment batch complete")
    print(f"Mode: {'APPLY' if apply else 'DRY RUN'}")
    print(f"Report: {report_file}")
    print("Before:", report["baseline_before"])
    print("After:", report["baseline_after"])
    print("Updated:", report["updated"])
    print(
        "Skipped:",
        {
            "no_match": report["skipped_no_match"],
            "low_score": report["skipped_low_score"],
        },
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Property enrichment batch")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist changes. Without this flag, script runs in dry-run mode.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.65,
        help="Minimum match score required for automatic Bufdir enrichment.",
    )
    parser.add_argument(
        "--force-description",
        action="store_true",
        help="Overwrite existing description with Bufdir description.",
    )
    parser.add_argument(
        "--no-download-images",
        action="store_true",
        help="Skip image downloads.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process first N properties only (useful for pilot run).",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=str(DEFAULT_REPORT_FILE),
        help="Path to JSON report file.",
    )

    args = parser.parse_args()

    asyncio.run(
        run_enrichment(
            apply=args.apply,
            min_score=args.min_score,
            force_description=args.force_description,
            download_images=not args.no_download_images,
            limit=args.limit,
            report_file=Path(args.report_file),
        )
    )


if __name__ == "__main__":
    main()
