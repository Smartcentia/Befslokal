#!/usr/bin/env python3
"""
Foreslår property_id for rader i koststed_mapping uten kobling, ved å matche
Dim1-kode mot felter på properties:

  - koststed_kode (SRS / Agresso)
  - unit_id_erp (e-don2 EnhetID)
  - department_code (avdelingens koststed)
  - lokalisering_id (lokasjonskode)

Standard: dry-run (kun print/JSON). Bruk --apply for å skrive forslag med
én entydig treff til koststed_mapping (krever DATABASE_URL).

Eksempel:
  cd backend && source .venv/bin/activate
  python scripts/suggest_koststed_property_mapping.py
  python scripts/suggest_koststed_property_mapping.py --json --out /tmp/forslag.json
  python scripts/suggest_koststed_property_mapping.py --apply

Etter --apply: kjør POST /api/v1/admin/economic-import/link-koststed-properties
eller tilsvarende for å propagere til gl_transactions (se economic_import.py).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.base  # noqa: F401 — registers all ORM models (resolves Center relationship)
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.models.financial_models import KoststedMapping


def _norm_code(v: Any) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    return s


def _match_properties_for_code(code: str, rows: list) -> dict[UUID, list[str]]:
    """Returner {property_id: [match-grunn, ...]} for eksakt kode-match."""
    code = _norm_code(code)
    if not code:
        return {}
    hits: dict[UUID, list[str]] = {}
    for p in rows:
        pid = p.property_id
        if _norm_code(p.koststed_kode) == code:
            hits.setdefault(pid, []).append("properties.koststed_kode")
        if _norm_code(p.unit_id_erp) == code:
            hits.setdefault(pid, []).append("properties.unit_id_erp")
        if _norm_code(p.department_code) == code:
            hits.setdefault(pid, []).append("properties.department_code")
        if _norm_code(p.lokalisering_id) == code:
            hits.setdefault(pid, []).append("properties.lokalisering_id")
    return hits


async def _load_properties(db: AsyncSession):
    stmt = select(
        Property.property_id,
        Property.koststed_kode,
        Property.unit_id_erp,
        Property.department_code,
        Property.lokalisering_id,
        Property.name,
    )
    return (await db.execute(stmt)).all()


async def _load_unmapped_koststed(db: AsyncSession):
    stmt = select(KoststedMapping.koststed_kode, KoststedMapping.koststed_navn, KoststedMapping.region).where(
        KoststedMapping.property_id.is_(None)
    )
    return (await db.execute(stmt)).fetchall()


async def main_async(args: argparse.Namespace) -> int:
    async with SessionLocal() as db:
        props = await _load_properties(db)
        unmapped = await _load_unmapped_koststed(db)

        # Rad-objekter for matching (enkle tupler med attributter som _match forventer)
        class _P:
            __slots__ = ("property_id", "koststed_kode", "unit_id_erp", "department_code", "lokalisering_id", "name")

            def __init__(self, row):
                self.property_id = row[0]
                self.koststed_kode = row[1]
                self.unit_id_erp = row[2]
                self.department_code = row[3]
                self.lokalisering_id = row[4]
                self.name = row[5]

        prop_objs = [_P(r) for r in props]

        results: list[dict[str, Any]] = []
        to_apply: list[tuple[str, UUID, str]] = []

        for row in unmapped:
            kode, navn, region = row[0], row[1], row[2]
            kode_s = _norm_code(kode)
            hits = _match_properties_for_code(kode_s, prop_objs)
            pids = list(hits.keys())

            if len(pids) == 0:
                status = "ingen_treff"
                suggestion = None
            elif len(pids) > 1:
                status = "flertydig"
                suggestion = {str(pid): hits[pid] for pid in pids}
            else:
                pid = pids[0]
                grunner = hits[pid]
                status = "entydig"
                suggestion = {"property_id": str(pid), "match_via": grunner}
                to_apply.append((kode_s, pid, ",".join(sorted(set(grunner)))))

            results.append(
                {
                    "koststed_kode": kode_s,
                    "koststed_navn": navn or "",
                    "region": region or "",
                    "status": status,
                    "forslag": suggestion,
                }
            )

        entydige = sum(1 for r in results if r["status"] == "entydig")
        print(
            f"Ukoblede koststed: {len(results)} | "
            f"Entydige treff: {entydige} | "
            f"Ingen treff: {sum(1 for r in results if r['status'] == 'ingen_treff')} | "
            f"Flertydige: {sum(1 for r in results if r['status'] == 'flertydig')}",
            file=sys.stderr,
        )

        if args.json:
            out = {"summary": {"total": len(results), "entydige": entydige}, "rader": results}
            if args.out:
                Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"Skrev {args.out}", file=sys.stderr)
            else:
                print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for r in sorted(results, key=lambda x: (x["status"] != "entydig", x["koststed_kode"])):
                if r["status"] == "entydig" and r["forslag"]:
                    print(
                        f"{r['koststed_kode']}\t{r['koststed_navn'][:50]}\t"
                        f"{r['forslag']['property_id']}\t{r['forslag']['match_via']}"
                    )
                elif args.verbose:
                    print(f"# {r['koststed_kode']}\t{r['status']}\t{r.get('forslag')}")

        if args.apply:
            if not to_apply:
                print("Ingen entydige treff å skrive.", file=sys.stderr)
            else:
                n = 0
                for kode_s, pid, _via in to_apply:
                    await db.execute(
                        update(KoststedMapping)
                        .where(KoststedMapping.koststed_kode == kode_s, KoststedMapping.property_id.is_(None))
                        .values(property_id=pid)
                    )
                    n += 1
                await db.commit()
                print(f"Oppdatert property_id for {n} koststed-rader.", file=sys.stderr)

    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Foreslå koststed → eiendom-kobling")
    ap.add_argument("--json", action="store_true", help="Skriv full JSON")
    ap.add_argument("--out", type=str, default="", help="Fil ved --json")
    ap.add_argument("--verbose", "-v", action="store_true", help="Vis også ikke-entydige (tekstmodus)")
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Skriv entydige treff til koststed_mapping (commit)",
    )
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
