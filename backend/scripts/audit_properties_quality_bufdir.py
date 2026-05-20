#!/usr/bin/env python3
"""
Grundig gjennomgang av alle eiendommer: avvik mot Bufdir (bufdir_institutions.json) og datakvalitet.

Sjekker bl.a.:
  - Navn som ser ut som ren adresse (samme logikk som sjekk_navn_kun_adresse.py)
  - address == name (feil fra eldre import – samme som fix_address_equals_name.py)
  - Koblet Bufdir (external_data.bufdir / bufdir_institution): sammenligning med offisiell JSON
  - Manglende geodata: ingen gateadresse og ingen poststed (postnr/by/kommune) – samme som «Adresse mangler» + «Sted ukjent» i UI
  - Manglende region
  - Mulige duplikatnavn (samme normaliserte navn på flere eiendommer)
  - Mangler kobling til regnskap: ingen av unit_id_erp, department_code, koststed_kode

Rapport: backend/data/properties_quality_audit.md (standard)

Kjør:
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_quality_bufdir.py
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_quality_bufdir.py --apply-safe-fixes --dry-run
  cd backend && PYTHONPATH=. python3 scripts/audit_properties_quality_bufdir.py --apply-safe-fixes

Krever DATABASE_URL (f.eks. `backend/.env` med Supabase Session Pooler – ikke `*.railway.internal` lokalt).
Alternativt fra repo-rot: `railway run bash -c 'cd backend && PYTHONPATH=. python3 scripts/audit_properties_quality_bufdir.py'`
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

try:
    from dotenv import load_dotenv
    # override=False: la f.eks. railway run / eksisterende DATABASE_URL i miljøet vinne over .env-fil
    load_dotenv(_backend / ".env", override=False)
    load_dotenv(_backend.parent / ".env", override=False)
except Exception:
    pass

from sqlalchemy import select

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

BUFDIR_JSON = _backend / "bufdir_institutions.json"
DEFAULT_REPORT = _backend / "data" / "properties_quality_audit.md"

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
from lib.property_name_quality import is_address_only_name  # noqa: E402


def _normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.lower().strip().split())


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _has_postal_place(p: Property) -> bool:
    return bool(
        (p.postal_code and str(p.postal_code).strip())
        or (p.city and str(p.city).strip())
        or (p.municipality and str(p.municipality).strip())
    )


def _missing_geolocation(p: Property) -> bool:
    """True når UI viser både «Adresse mangler» og «Sted ukjent»."""
    no_street = not (p.address and str(p.address).strip())
    return no_street and not _has_postal_place(p)


def _get_bufdir_blob(ed: Optional[dict]) -> dict:
    if not ed or not isinstance(ed, dict):
        return {}
    return (ed.get("bufdir") or ed.get("bufdir_institution") or {}) or {}


def _bufdir_id_from_blob(buf: dict) -> Optional[int]:
    raw = buf.get("bufdir_id") if buf.get("bufdir_id") is not None else buf.get("id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@dataclass
class PropertyIssue:
    property_id: str
    name: str
    address: Optional[str]
    city: Optional[str]
    codes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    suggested_name: Optional[str] = None


async def _validate_db_url() -> None:
    from app.core.config import settings
    url = str(settings.DATABASE_URL or "")
    host = ""
    if "@" in url:
        host = url.split("@")[1].split(":")[0].split("/")[0]
    if not url or host in ("", "host"):
        print("FEIL: DATABASE_URL mangler eller er placeholder. Sjekk backend/.env", file=sys.stderr)
        sys.exit(1)
    if host.endswith(".railway.internal"):
        print("FEIL: Railway intern host resolver ikke lokalt. Bruk Supabase Session Pooler-URL.", file=sys.stderr)
        sys.exit(1)


def _load_bufdir_institutions() -> tuple[dict[int, dict[str, Any]], list[dict]]:
    if not BUFDIR_JSON.exists():
        print(f"Advarsel: {BUFDIR_JSON} finnes ikke – Bufdir-sammenligning uten JSON.", file=sys.stderr)
        return {}, []
    data = json.loads(BUFDIR_JSON.read_text(encoding="utf-8"))
    by_id: dict[int, dict[str, Any]] = {}
    for row in data:
        try:
            iid = int(row.get("id"))
        except (TypeError, ValueError):
            continue
        by_id[iid] = row
    return by_id, data


async def collect_issues() -> tuple[list[PropertyIssue], dict[str, int]]:
    bufdir_by_id, _ = _load_bufdir_institutions()
    stats: dict[str, int] = {}

    async with SessionLocal() as db:
        r = await db.execute(select(Property))
        props = r.scalars().all()

    # Duplikatnavn: normalisert navn -> liste av property_id
    name_to_ids: dict[str, list[str]] = {}
    for p in props:
        raw = (p.name or "").strip()
        if len(raw) < 4:
            continue
        key = _normalize(raw)
        if not key:
            continue
        name_to_ids.setdefault(key, []).append(str(p.property_id))

    issues: list[PropertyIssue] = []

    for p in props:
        ed = p.external_data if isinstance(p.external_data, dict) else {}
        buf = _get_bufdir_blob(ed)
        bid = _bufdir_id_from_blob(buf)
        inst = bufdir_by_id.get(bid) if bid is not None else None

        pi = PropertyIssue(
            property_id=str(p.property_id),
            name=(p.name or "")[:500],
            address=p.address,
            city=p.city,
        )

        # 0) Geodata / region (liste-synlige hull)
        if _missing_geolocation(p):
            pi.codes.append("missing_geolocation")
            pi.notes.append("Mangler gateadresse og poststed (postnr/by/kommune).")
            stats["missing_geolocation"] = stats.get("missing_geolocation", 0) + 1
        elif not (p.address and str(p.address).strip()) and _has_postal_place(p):
            pi.codes.append("missing_street_address_only")
            pi.notes.append("Har poststed men mangler gateadresse.")
            stats["missing_street_address_only"] = stats.get("missing_street_address_only", 0) + 1

        if not (p.region and str(p.region).strip()):
            pi.codes.append("missing_region")
            pi.notes.append("Region ikke satt.")
            stats["missing_region"] = stats.get("missing_region", 0) + 1

        if not (
            (p.unit_id_erp and str(p.unit_id_erp).strip())
            or (p.department_code and str(p.department_code).strip())
            or (p.koststed_kode and str(p.koststed_kode).strip())
        ):
            pi.codes.append("missing_accounting_linkage")
            pi.notes.append(
                "Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme)."
            )
            stats["missing_accounting_linkage"] = stats.get("missing_accounting_linkage", 0) + 1

        raw_name = (p.name or "").strip()
        if raw_name and len(raw_name) >= 4:
            nk = _normalize(raw_name)
            dup_ids = name_to_ids.get(nk) or []
            if len(dup_ids) > 1:
                pi.codes.append("duplicate_property_name")
                others = [x for x in dup_ids if x != str(p.property_id)][:5]
                pi.notes.append(
                    f"Samme navn som {len(dup_ids) - 1} annen(e) eiendom: {', '.join(others)}"
                    + (" …" if len(dup_ids) > 6 else "")
                )
                stats["duplicate_property_name"] = stats.get("duplicate_property_name", 0) + 1

        # 1) address == name
        if p.address and p.name and _normalize(p.address) == _normalize(p.name):
            pi.codes.append("address_equals_name")
            pi.notes.append("Adresse og navn er identiske (typisk importfeil).")
            stats["address_equals_name"] = stats.get("address_equals_name", 0) + 1

        # 2) Navn ser ut som adresse
        if is_address_only_name(p.name, p.address):
            pi.codes.append("name_looks_like_address")
            stats["name_looks_like_address"] = stats.get("name_looks_like_address", 0) + 1
            if inst and (inst.get("name") or "").strip():
                official = (inst["name"] or "").strip()
                if similarity(p.name or "", official) < 0.75:
                    pi.suggested_name = official
                    pi.notes.append(f"Bufdir offisielt navn (JSON): {official[:120]}")

        # 3) Bufdir-kobling
        if buf:
            if bid is None:
                pi.codes.append("bufdir_blob_without_id")
                stats["bufdir_blob_without_id"] = stats.get("bufdir_blob_without_id", 0) + 1
            elif inst is None:
                pi.codes.append("bufdir_id_missing_in_json")
                pi.notes.append(f"bufdir_id={bid} finnes ikke i {BUFDIR_JSON.name} (kjør fetch_bufdir_data.py / oppdater JSON).")
                stats["bufdir_id_missing_in_json"] = stats.get("bufdir_id_missing_in_json", 0) + 1
            else:
                json_name = (inst.get("name") or "").strip()
                cached = (
                    buf.get("institution_name")
                    or buf.get("bufdir_name")
                    or buf.get("name")
                    or ""
                ).strip()
                if json_name and cached and similarity(json_name, cached) < 0.9:
                    pi.codes.append("bufdir_cache_name_differs_from_json")
                    pi.notes.append(f"Lagret institution_name avviker fra JSON (cache utdatert?). JSON: {json_name[:80]}")
                    stats["bufdir_cache_name_differs_from_json"] = stats.get("bufdir_cache_name_differs_from_json", 0) + 1

                json_addr = (inst.get("address") or "").strip()
                if json_addr and p.address and similarity(json_addr, p.address) < 0.55:
                    pi.codes.append("address_differs_from_bufdir_json")
                    pi.notes.append(f"Bufdir JSON-adresse: {json_addr[:100]}")
                    stats["address_differs_from_bufdir_json"] = stats.get("address_differs_from_bufdir_json", 0) + 1

                if json_name and p.name and similarity(json_name, p.name) < 0.5 and len(json_name) > 3:
                    pi.codes.append("property_name_differs_from_bufdir_official")
                    pi.notes.append("Eiendomsnavn i DB ligner ikke Bufdir offisielt navn.")
                    stats["property_name_differs_from_bufdir_official"] = (
                        stats.get("property_name_differs_from_bufdir_official", 0) + 1
                    )

        if pi.codes:
            issues.append(pi)

    stats["total_properties"] = len(props)
    stats["properties_with_any_issue"] = len(issues)
    return issues, stats


def _write_report(
    path: Path,
    issues: list[PropertyIssue],
    stats: dict[str, int],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Eiendomskvalitet – revisjon (Bufdir, navn/adresse, geodata, duplikater)",
        "",
        f"_Generert: {iso}_",
        "",
        "## Sammendrag",
        "",
        f"- Totalt eiendommer: **{stats.get('total_properties', 0)}**",
        f"- Minst ett avvik: **{stats.get('properties_with_any_issue', 0)}**",
        "",
    ]
    for key in sorted(stats.keys()):
        if key in ("total_properties", "properties_with_any_issue"):
            continue
        lines.append(f"- `{key}`: **{stats[key]}**")
    lines.extend(["", "---", ""])

    # Grupper på kode
    by_code: dict[str, list[PropertyIssue]] = {}
    for iss in issues:
        for c in iss.codes:
            by_code.setdefault(c, []).append(iss)

    for code in sorted(by_code.keys()):
        lines.append(f"## {code}")
        lines.append("")
        lines.append("| property_id | Navn (kort) | Adresse | Merknad |")
        lines.append("|---|---|---|---|")
        seen: set[str] = set()
        for iss in by_code[code]:
            key = f"{iss.property_id}:{code}"
            if key in seen:
                continue
            seen.add(key)
            n = (iss.name or "")[:60].replace("|", "/")
            a = (iss.address or "–")[:40].replace("|", "/")
            note = " ".join(iss.notes)[:200].replace("|", "/")
            if iss.suggested_name and code == "name_looks_like_address":
                note = (note + f" **Forslag navn:** {iss.suggested_name[:80]}").strip()
            lines.append(f"| `{iss.property_id}` | {n} | {a} | {note} |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


async def apply_safe_fixes(dry_run: bool) -> dict[str, Any]:
    """1) address=null når address==name. 2) name=Bufdir offisielt navn når navn er adresse-lignende og JSON har bedre navn."""
    await _validate_db_url()
    bufdir_by_id, _ = _load_bufdir_institutions()

    fixed_addr = 0
    fixed_name = 0
    samples: list[dict[str, str]] = []

    async with SessionLocal() as db:
        r = await db.execute(select(Property))
        props = r.scalars().all()

        for p in props:
            ed = p.external_data if isinstance(p.external_data, dict) else {}
            buf = _get_bufdir_blob(ed)
            bid = _bufdir_id_from_blob(buf)
            inst = bufdir_by_id.get(bid) if bid is not None else None

            # A) address duplicate of name
            if p.address and p.name and _normalize(p.address) == _normalize(p.name):
                if len(samples) < 15:
                    samples.append({"type": "address_cleared", "id": str(p.property_id), "was": (p.name or "")[:80]})
                if not dry_run:
                    p.address = None
                fixed_addr += 1

            # B) name from Bufdir when name looks like address only
            official = (inst.get("name") or "").strip() if inst else ""
            if (
                official
                and is_address_only_name(p.name, p.address)
                and similarity(p.name or "", official) < 0.75
            ):
                old_name = p.name
                if not dry_run:
                    p.name = official
                fixed_name += 1
                if len(samples) < 15:
                    samples.append(
                        {
                            "type": "name_from_bufdir_json",
                            "id": str(p.property_id),
                            "from": (old_name or "")[:80],
                            "to": official[:80],
                        }
                    )

        if not dry_run:
            await db.commit()

    return {
        "dry_run": dry_run,
        "fixed_address_duplicate": fixed_addr,
        "fixed_name_from_bufdir": fixed_name,
        "samples": samples,
    }


async def main_async(args: argparse.Namespace) -> None:
    await _validate_db_url()

    if args.apply_safe_fixes:
        result = await apply_safe_fixes(dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    issues, stats = await collect_issues()
    out = Path(args.output)
    _write_report(out, issues, stats)
    print(f"Rapport skrevet: {out}")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Revisjon av eiendommer mot Bufdir og navn/adresse-kvalitet")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT),
        help="Markdown-rapportfil",
    )
    parser.add_argument(
        "--apply-safe-fixes",
        action="store_true",
        help="Bruk sikre automatiske rettinger (adresse==name, navn fra Bufdir JSON ved adresse-navn)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ved --apply-safe-fixes: ikke lagre",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
