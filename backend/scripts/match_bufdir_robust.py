#!/usr/bin/env python3
"""
Robust matching av Bufdir-institusjoner til eiendommer.

Scoring vektlegger både navn og adresse slik at eiendommer der `name` bare er gateadresse
fortsatt kan kobles til riktig Bufdir-rad når adressen stemmer.

Pipeline (kjør fra prosjektrot):
  1. python backend/scripts/fetch_bufdir_data.py   → backend/bufdir_institutions.json
  2. python backend/scripts/match_bufdir_robust.py → bufdir_matches_robust.json (+ usikre)

Krever DATABASE_URL (lastes fra .env hvis tilgjengelig).
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

from sqlalchemy import select

# Last .env før app-import (så DATABASE_URL er satt)
try:
    from dotenv import load_dotenv

    _backend = Path(__file__).resolve().parent.parent
    load_dotenv(_backend / ".env")
    load_dotenv(_backend.parent / ".env")
except ImportError:
    pass

_backend = Path(__file__).resolve().parent.parent
_scripts = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts))
sys.path.insert(0, str(_backend))

from lib.db_env import require_database_url_for_local_scripts

from app.db.session import SessionLocal
import app.domains.core.models.user  # noqa: F401
from app.domains.core.models.property import Property
import app.domains.core.models.contract  # noqa: F401
import app.domains.core.models.audit  # noqa: F401
import app.domains.core.models.unit  # noqa: F401
import app.domains.core.models.party  # noqa: F401
import app.domains.core.models.center  # noqa: F401
import app.domains.hms.models.risk  # noqa: F401
import app.domains.hms.models.internal_control  # noqa: F401
import app.models.file_meta  # noqa: F401


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _full_prop_address(prop: Property) -> str:
    parts = [prop.address, prop.postal_code, prop.city]
    return " ".join(str(p) for p in parts if p and str(p).strip())


def compute_match_scores(inst: dict, prop: Property) -> tuple[float, float, float, float]:
    """
    Returnerer (combined, name_score, addr_score, loc_score).
    """
    inst_name = (inst.get("name") or "").strip()
    inst_addr = (inst.get("address") or "").strip()
    inst_loc = (inst.get("location") or "").strip()

    prop_name = (prop.name or "").strip()
    prop_addr = (prop.address or "").strip()
    prop_city = (prop.city or "").strip()
    prop_pc = str(prop.postal_code or "").strip()

    name_score = similarity(inst_name, prop_name)
    if not prop_name and prop_addr:
        name_score = max(name_score, similarity(inst_name, prop_addr) * 0.9)

    addr_score = 0.0
    if inst_addr and prop_addr:
        addr_score = max(addr_score, similarity(inst_addr, prop_addr))
    if inst_addr:
        full = _full_prop_address(prop)
        if full.strip():
            addr_score = max(addr_score, similarity(inst_addr, full))
        inst_first = inst_addr.split(",")[0].strip()
        if inst_first and prop_addr:
            addr_score = max(addr_score, similarity(inst_first, prop_addr))

    loc_score = 0.0
    if inst_loc and prop_city:
        loc_score = similarity(inst_loc, prop_city)

    if inst_addr and prop_pc and prop_pc in re.sub(r"\s+", "", inst_addr):
        addr_score = min(1.0, addr_score + 0.07)

    combined = name_score
    if addr_score > 0.65:
        combined = max(combined, addr_score * 0.9 + 0.1 * max(loc_score, name_score * 0.25))
    if addr_score > 0.55 and loc_score > 0.72:
        combined = max(combined, 0.42 * name_score + 0.48 * addr_score + 0.1 * loc_score)
    if name_score > 0.48 and loc_score > 0.8:
        combined = max(combined, (name_score + loc_score) / 2)
    if addr_score > 0.78 and name_score < 0.45:
        combined = max(combined, addr_score * 0.93 + 0.07 * loc_score)

    return combined, name_score, addr_score, loc_score


CONFIDENT_THRESHOLD = 0.72
UNCERTAIN_LOW = 0.52


async def match_bufdir_robust():
    require_database_url_for_local_scripts()

    print("🤝 Matching Bufdir Institutions to Properties")
    print("=" * 60)

    inst_path = _backend / "bufdir_institutions.json"
    try:
        institutions = json.loads(inst_path.read_text(encoding="utf-8"))
        print(f"Loaded {len(institutions)} institutions from {inst_path.name}")
    except FileNotFoundError:
        print(f"❌ Could not find {inst_path}")
        return

    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        print(f"Loaded {len(properties)} properties from database")

        candidates: list[dict] = []

        for idx, inst in enumerate(institutions):
            best_prop = None
            best_combined = 0.0
            best_name = 0.0
            best_addr = 0.0
            best_loc = 0.0

            for prop in properties:
                combined, ns, ads, ls = compute_match_scores(inst, prop)
                if combined > best_combined:
                    best_combined = combined
                    best_prop = prop
                    best_name = ns
                    best_addr = ads
                    best_loc = ls

            if best_prop is None:
                continue

            inst_name = (inst.get("name") or "")[:80]
            candidates.append(
                {
                    "institution_name": inst.get("name"),
                    "property_name": best_prop.name,
                    "property_address": best_prop.address,
                    "property_id": str(best_prop.property_id),
                    "score": round(best_combined, 4),
                    "name_score": round(best_name, 4),
                    "addr_score": round(best_addr, 4),
                    "loc_score": round(best_loc, 4),
                    "bufdir_data": inst,
                    "_sort": best_combined,
                }
            )
            if idx < 25 or best_combined >= CONFIDENT_THRESHOLD:
                print(
                    f"✓ {inst_name[:40]}... → prop {str(best_prop.property_id)[:8]}… "
                    f"(combined={best_combined:.2f} name={best_name:.2f} addr={best_addr:.2f})"
                )

        candidates.sort(key=lambda x: x["_sort"], reverse=True)

        used_props: set[str] = set()
        matches: list[dict] = []
        uncertain: list[dict] = []
        unmatched_insts: list[dict] = []

        for c in candidates:
            pid = c["property_id"]
            sc = c["_sort"]
            if pid in used_props:
                unmatched_insts.append(
                    {
                        "reason": "property_already_matched_to_higher_score",
                        "institution_name": c.get("institution_name"),
                        "would_be_score": sc,
                        "bufdir_data": c.get("bufdir_data"),
                    }
                )
                continue
            if sc >= CONFIDENT_THRESHOLD:
                used_props.add(pid)
                c.pop("_sort", None)
                matches.append(c)
            elif sc >= UNCERTAIN_LOW:
                used_props.add(pid)
                c.pop("_sort", None)
                uncertain.append(c)
            else:
                unmatched_insts.append(
                    {
                        "reason": "below_threshold",
                        "institution_name": c.get("institution_name"),
                        "best_score": sc,
                    }
                )

        print(f"\n✅ Matched (confident ≥{CONFIDENT_THRESHOLD}): {len(matches)}")
        print(f"⚠️  Uncertain ({UNCERTAIN_LOW}–{CONFIDENT_THRESHOLD}): {len(uncertain)}")
        print(f"❌ Below threshold / dropped: {len(unmatched_insts)}")

        matches_path = _backend / "bufdir_matches_robust.json"
        matches_path.write_text(
            json.dumps(
                [{k: v for k, v in m.items() if not k.startswith("_")} for m in matches],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"Saved matches to {matches_path}")

        uncertain_path = _backend / "bufdir_matches_uncertain.json"
        uncertain_path.write_text(
            json.dumps(
                [{k: v for k, v in m.items() if not k.startswith("_")} for m in uncertain],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"Saved uncertain matches to {uncertain_path} (manual review)")

        matched_inst_ids: set = set()
        for m in matches + uncertain:
            bid = (m.get("bufdir_data") or {}).get("id")
            if bid is not None:
                matched_inst_ids.add(bid)

        truly_unmatched = [inst for inst in institutions if inst.get("id") not in matched_inst_ids]
        unmatched_path = _backend / "bufdir_unmatched.json"
        unmatched_path.write_text(json.dumps(truly_unmatched, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {len(truly_unmatched)} institutions with no property match to {unmatched_path}")

        conflict_path = _backend / "bufdir_match_conflicts.json"
        conflict_path.write_text(json.dumps(unmatched_insts, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved {len(unmatched_insts)} dedupe/conflict notes to {conflict_path}")


if __name__ == "__main__":
    asyncio.run(match_bufdir_robust())
