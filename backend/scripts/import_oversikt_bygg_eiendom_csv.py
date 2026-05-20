"""
Import fra «Oversikt bygg og eiendom - GK og Budsjetterte» eller «Eiendomsportefølje- Bufdir» CSV til BEFS.

Oppdaterer properties (affiliation, approved_places, budgeted_places, legal_basis,
external_data med egnethet, videreutvikling) og contracts (amount, external_data, party_id).

Støtter både semikolon og komma som separator, samt DD.MM.YYYY og M/D/YYYY datoformat.
Matching: Multi-pass (lokalisering_id, navn_contains, adresse_exact, adresse_heuristic, adresse_fuzzy, navn_fuzzy).

Eiendomsportefølje-CSV: Støtter kolonner som «Kontraktsleie ved oppstart (per år)» og
«KPI-justert kontraktsleie til okt 2025». Ved flere rader per Lokalisering prioriteres hovedkontrakt.

Bruker enten Supabase REST API eller DATABASE_URL (--use-db).

Kjør:
  SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/import_oversikt_bygg_eiendom_csv.py [--csv PATH] [--dry-run]
  DATABASE_URL=... python3 scripts/import_oversikt_bygg_eiendom_csv.py --use-db [--csv PATH] [--dry-run] [--report]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import difflib
import io
import os
import re
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vwvhxcqxadblrftuvsds.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
REST_URL = f"{SUPABASE_URL}/rest/v1"

try:
    import requests
except ImportError:
    requests = None

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
} if SERVICE_KEY else {}


from app.domains.core.utils.property_matcher import build_property_index, match_property

def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    t = (s or "").strip()
    return t if t else None


# Strenger som indikerer at beløp ikke er numerisk (refererer til hovedkontrakt)
_SKIP_AMOUNT_STRINGS = (
    "se hovedkontrakt",
    "se hovedavtale",
    "se hovedavtalen",
    "inkludert i hovedkontrakt",
    "inkludert i hovedavtale",
    "vedlikeholdsavtale",
    "ny kontrakt fra",
    "tillegg til kontrakt",
    "lt innhenter kontrakt",
)


def _parse_amount(val: str | None) -> float | None:
    """Parse beløp fra streng. Håndterer 'se hovedkontrakt', '4025842 etter...', '2720000 og 31000'."""
    if not val or not str(val).strip():
        return None
    s = str(val).strip().replace("\xa0", "").replace(",", ".")
    s_lower = s.lower()
    for skip in _SKIP_AMOUNT_STRINGS:
        if skip in s_lower:
            return None
    # Ekstraher tall (uten mellomrom)
    s_clean = s.replace(" ", "")
    numbers = re.findall(r"\d+", s_clean)
    if not numbers:
        return None
    # Bruk første tall >= 1000 (filterer datoer som 01, 07, 2013)
    for n in numbers:
        try:
            val = float(n)
            if val >= 1000:
                return val
        except ValueError:
            pass
    try:
        return float(numbers[0])
    except ValueError:
        pass
    return None


def _parse_date(val: str | None) -> str | None:
    """Returnerer YYYY-MM-DD eller None."""
    if not val or not str(val).strip():
        return None
    s = str(val).strip()
    # M/D/YYYY eller M/D/YY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})$", s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            dt = datetime(y, mo, d)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # DD.MM.YYYY
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = datetime(y, mo, d)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def _parse_lokalisering_id(lok_raw: str | None) -> str | None:
    """Hent kode fra 'XXXX - Navn' eller 'XXXX - Navn, adresse'."""
    if not lok_raw:
        return None
    m = re.match(r"^(\d{4})", str(lok_raw).strip())
    return m.group(1) if m else None


def _parse_lokalisering_navn(lok_raw: str | None) -> str | None:
    """Hent navn fra 'XXXX - Navn' (delen etter ' - ')."""
    if not lok_raw:
        return None
    s = str(lok_raw).strip()
    if " - " in s:
        return _norm(s.split(" - ", 1)[1].split(",")[0])
    return _norm(s) if s else None


def _normalize_address_canonical(val: str | None) -> str:
    """Normaliser adresse for matching: lowercase, fjern punktum/komma."""
    if val is None:
        return ""
    s = str(val).strip().lower()
    s = re.sub(r"[\s\t\r\n]+", " ", s)
    s = re.sub(r"[.,;:-]", "", s)
    return s.strip()


def _normalize_address_heuristic(val: str | None) -> str:
    """Suffix-equivalence for lookup: gata→gt, veien→vg."""
    s = _normalize_address_canonical(val)
    s = s.replace("gata", "gt").replace("gaten", "gt")
    s = s.replace("veien", "vg").replace("vegen", "vg")
    return s


def _safe_int(val: str | None) -> int | None:
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(str(val).replace(",", ".").replace(" ", "")))
    except (ValueError, TypeError):
        return None


# Kolonnenavn for Eiendomsportefølje-CSV (fallback for Oversikt bygg)
_COL_KONTRAKTSLEIE = (
    "Kontraktsleie",
    "Kontraktsleie ved oppstart (per år)",
    "Kontaktsleie ved oppstart (gyldig kontrakt)",
    "KPI-justert kontraktsleie til okt 2025",
)
_COL_INDRE_VEDLIKEHOLD = ("Indre vedlikehold", "KPI-justert indre vedlikehold")
_COL_FELLESKOSTNADER = (
    "Felleskostnader",
    "Felleskostnader per år (ved kontraktsinngåelse) ",
    "KPI-justert: Felleskostnader",
)
_COL_BRUKERAVHENGIGE = (
    "Brukeravhengige driftskostnader",
    "Brukeravhengige driftskostander - Første driftsår",
    "KPI-justert: Brukeravhengige driftskostnader",
)
_COL_REGULATION = ("Årlig prisjusteringsfaktaktor", "leieregulering")
_COL_EXTENSION = ("Adgang til forlengelse og vilkår", "adgang til forlengelse og vilkår")


def _get_col(row: dict, candidates: tuple[str, ...]) -> str | None:
    """Hent verdi fra row med første matchende kolonnenavn."""
    for col in candidates:
        val = row.get(col)
        if val is not None and str(val).strip():
            return _norm(str(val))
    return None


def _get_amount(row: dict, candidates: tuple[str, ...]) -> float | None:
    """Hent og parse beløp fra row."""
    for col in candidates:
        val = row.get(col)
        if val is not None:
            parsed = _parse_amount(str(val))
            if parsed is not None:
                return parsed
    return None


def _is_hovedkontrakt(avtalenavn: str | None) -> bool:
    """Sjekk om Avtalenavn indikerer hovedkontrakt."""
    if not avtalenavn:
        return False
    an = avtalenavn.lower()
    return "hovedkontrakt" in an or "hovedleiekontrakt" in an or "hovedavtale" in an


def _preprocess_eiendomsportefolje_rows(rows: list[dict]) -> list[dict]:
    """
    Ved flere rader per Lokalisering: velg hovedkontrakt-rad.
    Fallback: første rad med numerisk Kontraktsleie.
    """
    by_lok: dict[str, list[dict]] = {}
    for row in rows:
        lok = _norm(row.get("Lokalisering"))
        if not lok:
            continue
        by_lok.setdefault(lok, []).append(row)

    result = []
    for lok, group in by_lok.items():
        if len(group) == 1:
            result.append(group[0])
            continue
        # Prioriter hovedkontrakt
        hoved = [r for r in group if _is_hovedkontrakt(_norm(r.get("Avtalenavn")))]
        if len(hoved) == 1:
            result.append(hoved[0])
            continue
        if len(hoved) > 1:
            result.append(hoved[0])
            continue
        # Fallback: første rad med numerisk Kontraktsleie
        for r in group:
            if _get_amount(r, _COL_KONTRAKTSLEIE) is not None:
                result.append(r)
                break
        else:
            result.append(group[0])
    return result


def _is_eiendomsportefolje_format(fieldnames: list[str] | None) -> bool:
    """Sjekk om CSV er Eiendomsportefølje-format (har portefølje-spesifikke kolonner)."""
    if not fieldnames:
        return False
    fn = [f.strip() for f in fieldnames]
    return "Kontraktsleie ved oppstart (per år)" in fn or "KPI-justert kontraktsleie til okt 2025" in fn


def load_csv(csv_path: str) -> list[dict]:
    """Les CSV. Støtter semikolon og komma, flere encodings. Eiendomsportefølje har header på rad 1."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for delim in (";", ","):
            try:
                with open(csv_path, newline="", encoding=enc) as f:
                    lines = f.readlines()
                if not lines:
                    continue
                # Eiendomsportefølje: header på rad 1 (første linje inneholder Lokalisering)
                first_col = (lines[0].split(delim)[0] or "").strip()
                if first_col == "Lokalisering":
                    content = "".join(lines)
                else:
                    content = "".join(lines[1:]) if len(lines) > 1 else ""
                if not content:
                    continue
                reader = csv.DictReader(io.StringIO(content), delimiter=delim)
                if reader.fieldnames and "Lokalisering" in reader.fieldnames:
                    rows = []
                    for row in reader:
                        if _norm(row.get("Lokalisering")):
                            rows.append(row)
                    if rows:
                        if _is_eiendomsportefolje_format(reader.fieldnames):
                            rows = _preprocess_eiendomsportefolje_rows(rows)
                        return rows
            except (UnicodeDecodeError, csv.Error):
                continue
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
        content = "".join(lines[1:]) if len(lines) > 1 else "".join(lines)
        reader = csv.DictReader(io.StringIO(content), delimiter=";")
        return [r for r in reader if _norm(r.get("Lokalisering"))]


def api_get(table: str, params: dict) -> list:
    if not requests:
        return []
    resp = requests.get(f"{REST_URL}/{table}", headers=HEADERS, params=params, timeout=60)
    if resp.status_code == 401:
        print("Feil: 401 Unauthorized. Bruk SUPABASE_SERVICE_ROLE_KEY (service_role).")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def api_patch(table: str, filter_key: str, filter_val: str, data: dict) -> list:
    if not requests:
        return []
    resp = requests.patch(
        f"{REST_URL}/{table}",
        headers=HEADERS,
        params={filter_key: f"eq.{filter_val}"},
        json=data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() if resp.text else []


def api_post(table: str, data: dict) -> list:
    if not requests:
        return []
    resp = requests.post(f"{REST_URL}/{table}", headers=HEADERS, json=data, timeout=30)
    resp.raise_for_status()
    return resp.json() if resp.text else []


def get_or_create_party(name: str, dry_run: bool) -> str | None:
    """Finn eller opprett party. Returnerer party_id."""
    if not name:
        return None
    existing = api_get("parties", {"select": "party_id", "name": f"eq.{name}"})
    if existing:
        return str(existing[0]["party_id"])
    if dry_run:
        return None
    new = api_post("parties", {"name": name})
    if new:
        return str(new[0]["party_id"])
    return None


def _find_property_for_row(row: dict, idx: dict) -> tuple:
    """
    Finn eiendom for CSV-rad. Bruker property_matcher.
    Returnerer (prop, method) eller (None, None).
    """
    postnr = _norm(row.get("Postnr") or row.get("Postnr "))
    if not postnr:
        addr_post = _norm(row.get("Adresse og Postnummer ") or row.get("Adresse og Postnummer"))
        if addr_post:
            m = re.search(r",\s*(\d{4})\b", addr_post)
            if m:
                postnr = m.group(1)
    return match_property(
        idx,
        lokalisering_raw=row.get("Lokalisering"),
        address=row.get("Adresselinje 1"),
        postal_code=postnr,
        city=row.get("Poststed"),
    )


def _run_match_report(rows: list, idx: dict) -> None:
    """Kjør match-rapport uten DB-endringer."""
    counts = {
        "lokalisering_id": 0,
        "navn_contains": 0,
        "adresse_exact": 0,
        "adresse_heuristic": 0,
        "adresse_fuzzy": 0,
        "navn_fuzzy": 0,
        "ingen": 0,
    }
    no_match_examples = []
    all_props = idx.get("all_props", [])

    for i, row in enumerate(rows, 1):
        lok_raw = row.get("Lokalisering", "")
        if not _norm(lok_raw):
            continue
        prop, method = _find_property_for_row(row, idx)
        if method:
            counts[method] = counts.get(method, 0) + 1
        else:
            counts["ingen"] += 1
            if len(no_match_examples) < 15:
                addr = _norm(row.get("Adresselinje 1"))
                postnr = _norm(row.get("Postnr"))
                poststed = _norm(row.get("Poststed"))
                no_match_examples.append((i, lok_raw, f"{addr or ''}, {postnr or ''} {poststed or ''}".strip()))

    lok_to_props = idx.get("lok_to_props", {})
    print("\nRapport: Oversikt bygg CSV vs database")
    print("=" * 50)
    print(f"Lest {len(rows)} rader fra CSV.")
    print(f"Eiendommer i DB: {len(all_props)}")
    print(f"Med lokalisering_id: {len(lok_to_props)}")
    print()
    print("Treff per metode:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print()
    if no_match_examples:
        print("Eksempler uten match:")
        for idx, lok, addr in no_match_examples:
            print(f"  [{idx}] {lok} | {addr}")


async def run_db_import(csv_path: str, dry_run: bool, report_only: bool = False) -> None:
    """Import via DATABASE_URL (async SQLAlchemy)."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.domains.core.models.user import User  # noqa: F401 - required for ORM resolution
    from app.domains.core.models.party import Party
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.unit import Unit
    from app.domains.hms.models.risk import RiskAssessment  # noqa: F401
    from app.domains.hms.models.internal_control import InternalControlCase  # noqa: F401
    from app.domains.core.models.center import Center  # noqa: F401
    from app.domains.core.models.property import Property
    from sqlalchemy.orm.attributes import flag_modified

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Mangler DATABASE_URL i miljøet.")
        sys.exit(1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    rows = load_csv(csv_path)
    print(f"Lest {len(rows)} rader fra CSV.")
    if rows and _is_eiendomsportefolje_format(list(rows[0].keys()) if rows else None):
        print("Format: Eiendomsportefølje (hovedkontrakt prioriteres ved flere rader per Lokalisering)")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Property))
        all_props = result.scalars().all()
        idx = build_property_index(all_props)

        if report_only:
            _run_match_report(rows, idx)
            await engine.dispose()
            return

        props_updated = 0
        contracts_updated = 0
        skipped_no_prop = 0
        skipped_no_contract = 0

        for i, row in enumerate(rows, 1):
            lok_raw = row.get("Lokalisering", "")
            if not _norm(lok_raw):
                skipped_no_prop += 1
                continue

            prop, _method = _find_property_for_row(row, idx)
            if not prop:
                skipped_no_prop += 1
                continue

            ext = dict(prop.external_data or {})
            egnethet_lok = _safe_int(row.get("Egnethet lokalisering ") or row.get("Egnethet lokalisering"))
            egnethet_bygg = _safe_int(row.get("Egnethet bygg"))
            if egnethet_lok is not None and 1 <= egnethet_lok <= 4:
                ext["egnethet_lokalisering"] = egnethet_lok
            if egnethet_bygg is not None and 1 <= egnethet_bygg <= 4:
                ext["egnethet_bygg"] = egnethet_bygg

            priortert = _norm(row.get("Priortert viderført /utviklet ") or row.get("Priortert viderført /utviklet"))
            if priortert:
                ext["priortert_viderført"] = priortert
            år_vid = _norm(row.get("År for videreutvikling ") or row.get("År for videreutvikling"))
            if år_vid:
                ext["år_videreutvikling"] = år_vid
            kost_vid = _parse_amount(row.get("Kostnader til videreutvikling ") or row.get("Kostnader til videreutvikling"))
            if kost_vid is not None:
                ext["kostnader_videreutvikling"] = kost_vid

            has_prop = bool(ext)
            if affiliation := _norm(row.get("Målgruppe ") or row.get("Målgruppe")):
                prop.affiliation = affiliation
                has_prop = True
            if (ap := _safe_int(row.get("Antall G/K - plasser") or row.get("Antall godkjente plasser"))) is not None:
                prop.approved_places = ap
                has_prop = True
            if (bp := _safe_int(row.get("Antall budsjetterte plasser"))) is not None:
                prop.budgeted_places = bp
                has_prop = True
            legal = _norm(row.get("Hjemmel §") or row.get("Hjemmel § "))
            if legal:
                prop.legal_basis = legal
                has_prop = True
            if ext:
                prop.external_data = ext
                flag_modified(prop, "external_data")

            if has_prop:
                props_updated += 1

            # Contract
            result_u = await session.execute(select(Unit).where(Unit.property_id == prop.property_id))
            units = result_u.scalars().all()
            if not units:
                continue

            contracts = []
            for u in units:
                result_c = await session.execute(
                    select(Contract).where(Contract.unit_id == u.unit_id)
                )
                contracts.extend(result_c.scalars().all())

            start_iso = _parse_date(row.get("Startdato"))
            amount_val = _get_amount(row, _COL_KONTRAKTSLEIE)
            avtalenavn = _norm(row.get("Avtalenavn"))

            matched = None
            for c in contracts:
                c_start = (c.start_date[:10] if c.start_date else None) if isinstance(c.start_date, str) else (str(c.start_date)[:10] if c.start_date else None)
                c_amt = None
                amt = c.amount
                if isinstance(amt, dict) and amt.get("amount_per_year"):
                    c_amt = float(amt["amount_per_year"])
                elif isinstance(amt, (int, float)):
                    c_amt = float(amt)
                if start_iso and c_start == start_iso:
                    if amount_val is not None and c_amt is not None and abs(amount_val - c_amt) < 1:
                        matched = c
                        break
                    elif amount_val is None or c_amt is None:
                        matched = c
                        break
                if start_iso and c_start == start_iso:
                    matched = c
                    break
            if not matched and contracts and len(contracts) == 1:
                matched = contracts[0]
            if not matched:
                skipped_no_contract += 1
                continue

            ext_c = dict(matched.external_data or {})
            if regulation := _get_col(row, _COL_REGULATION):
                ext_c["regulation_type"] = regulation
            if (ext_terms := _get_col(row, _COL_EXTENSION)):
                ext_c["extension_terms"] = ext_terms
            if (im := _get_amount(row, _COL_INDRE_VEDLIKEHOLD)) is not None:
                ext_c["internal_maintenance_cost"] = im
            if (fc := _get_amount(row, _COL_FELLESKOSTNADER)) is not None:
                ext_c["common_costs"] = fc
            if (bd := _get_amount(row, _COL_BRUKERAVHENGIGE)) is not None:
                ext_c["user_dependent_costs"] = bd
            if avtalenavn:
                ext_c["contract_name"] = avtalenavn

            if amount_val is not None:
                matched.amount = {"currency": "NOK", "amount_per_year": amount_val}
            if ext_c:
                matched.external_data = ext_c
                flag_modified(matched, "external_data")

            utleier = _norm(row.get("Utleier"))
            if utleier:
                party_res = await session.execute(select(Party).where(Party.name == utleier))
                party = party_res.scalar_one_or_none()
                if not party and not dry_run:
                    party = Party(name=utleier)
                    session.add(party)
                    await session.flush()
                if party:
                    matched.party_id = party.party_id

            contracts_updated += 1

        if not dry_run:
            await session.commit()

        print(f"\nFerdig. Properties oppdatert: {props_updated}, Contracts oppdatert: {contracts_updated}")
        if skipped_no_prop:
            print(f"Rader uten matchende eiendom: {skipped_no_prop}")
        if skipped_no_contract:
            print(f"Rader uten matchende kontrakt: {skipped_no_contract}")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Import Oversikt bygg og eiendom CSV")
    default_csv = os.path.expanduser(
        "~/Downloads/Oversikt bygg og eiendom - GK og Budsjetterte(Ark1) (2).csv"
    )
    parser.add_argument(
        "--csv",
        default=default_csv,
        help="Full path til CSV (Oversikt bygg eller Eiendomsportefølje- Bufdir)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    parser.add_argument("--report", action="store_true", help="Vis match-rapport uten import (kun --use-db)")
    parser.add_argument("--use-db", action="store_true", help="Bruk DATABASE_URL i stedet for Supabase REST")
    args = parser.parse_args()

    if args.use_db:
        if not os.path.isfile(args.csv):
            print(f"Fil ikke funnet: {args.csv}")
            sys.exit(1)
        asyncio.run(run_db_import(args.csv, args.dry_run, report_only=args.report))
        return

    if not SERVICE_KEY:
        print("Mangler SUPABASE_SERVICE_ROLE_KEY i miljøet.")
        sys.exit(1)

    if not os.path.isfile(args.csv):
        print(f"Fil ikke funnet: {args.csv}")
        sys.exit(1)

    rows = load_csv(args.csv)
    print(f"Lest {len(rows)} rader fra CSV.")
    if rows and _is_eiendomsportefolje_format(list(rows[0].keys()) if rows else None):
        print("Format: Eiendomsportefølje (hovedkontrakt prioriteres ved flere rader per Lokalisering)")

    # Hent alle properties med lokalisering_id for matching
    all_props = []
    offset = 0
    while True:
        params = {
            "select": "property_id,lokalisering_id,name,address,postal_code,city",
            "offset": offset,
            "limit": 500,
        }
        chunk = api_get("properties", params)
        if not chunk:
            break
        all_props.extend(chunk)
        if len(chunk) < 500:
            break
        offset += 500

    lok_to_props = {}
    for p in all_props:
        lid = _norm(p.get("lokalisering_id"))
        if lid:
            lok_to_props.setdefault(lid, []).append(p)

    props_updated = 0
    contracts_updated = 0
    skipped_no_prop = 0
    skipped_no_contract = 0

    for i, row in enumerate(rows, 1):
        lok_raw = row.get("Lokalisering", "")
        lok_id = _parse_lokalisering_id(lok_raw)
        if not lok_id:
            skipped_no_prop += 1
            continue

        props = lok_to_props.get(lok_id)
        if not props:
            skipped_no_prop += 1
            if i <= 5:
                print(f"  [{i}] SKIP: ingen eiendom for lokalisering_id={lok_id}")
            continue

        prop = props[0]
        property_id = str(prop["property_id"])

        # Bygg property external_data
        ext = prop.get("external_data") or {}
        if isinstance(ext, str):
            try:
                import json
                ext = json.loads(ext) if ext else {}
            except Exception:
                ext = {}

        egnethet_lok = _safe_int(row.get("Egnethet lokalisering ") or row.get("Egnethet lokalisering"))
        egnethet_bygg = _safe_int(row.get("Egnethet bygg"))
        if egnethet_lok is not None and 1 <= egnethet_lok <= 4:
            ext["egnethet_lokalisering"] = egnethet_lok
        if egnethet_bygg is not None and 1 <= egnethet_bygg <= 4:
            ext["egnethet_bygg"] = egnethet_bygg

        priortert = _norm(row.get("Priortert viderført /utviklet ") or row.get("Priortert viderført /utviklet"))
        if priortert:
            ext["priortert_viderført"] = priortert

        år_vid = _norm(row.get("År for videreutvikling ") or row.get("År for videreutvikling"))
        if år_vid:
            ext["år_videreutvikling"] = år_vid

        kost_vid = _parse_amount(row.get("Kostnader til videreutvikling ") or row.get("Kostnader til videreutvikling"))
        if kost_vid is not None:
            ext["kostnader_videreutvikling"] = kost_vid

        # Property payload
        prop_payload = {}
        if ext:
            prop_payload["external_data"] = ext

        affiliation = _norm(row.get("Målgruppe ") or row.get("Målgruppe"))
        if affiliation:
            prop_payload["affiliation"] = affiliation

        ap = _safe_int(row.get("Antall G/K - plasser") or row.get("Antall godkjente plasser"))
        if ap is not None:
            prop_payload["approved_places"] = ap

        bp = _safe_int(row.get("Antall budsjetterte plasser"))
        if bp is not None:
            prop_payload["budgeted_places"] = bp

        legal = _norm(row.get("Hjemmel §"))
        if legal:
            prop_payload["legal_basis"] = legal

        if prop_payload and not args.dry_run:
            api_patch("properties", "property_id", property_id, prop_payload)
            props_updated += 1
        elif prop_payload and args.dry_run:
            props_updated += 1

        # Contract: finn unit for property, deretter contract
        units = api_get("units", {"select": "unit_id", "property_id": f"eq.{property_id}"})
        if not units:
            continue

        unit_ids = [str(u["unit_id"]) for u in units]
        # Hent kontrakter for disse enhetene
        contracts = []
        for uid in unit_ids:
            c = api_get("contracts", {"select": "contract_id,unit_id,start_date,amount,external_data,party_id", "unit_id": f"eq.{uid}"})
            contracts.extend(c)

        # Match contract: start_date + amount (eller avtalenavn)
        start_iso = _parse_date(row.get("Startdato"))
        amount_val = _get_amount(row, _COL_KONTRAKTSLEIE)
        avtalenavn = _norm(row.get("Avtalenavn"))

        matched = None
        for c in contracts:
            c_start = None
            if c.get("start_date"):
                c_start = c["start_date"][:10] if isinstance(c["start_date"], str) else str(c.get("start_date"))[:10]
            c_amt = None
            amt = c.get("amount")
            if isinstance(amt, dict) and amt.get("amount_per_year"):
                c_amt = float(amt["amount_per_year"])
            elif isinstance(amt, (int, float)):
                c_amt = float(amt)

            if start_iso and c_start == start_iso:
                if amount_val is not None and c_amt is not None and abs(amount_val - c_amt) < 1:
                    matched = c
                    break
                elif amount_val is None or c_amt is None:
                    matched = c
                    break
            if start_iso and c_start == start_iso:
                matched = c
                break

        if not matched and contracts and len(contracts) == 1:
            matched = contracts[0]

        if not matched:
            skipped_no_contract += 1
            continue

        contract_id = str(matched["contract_id"])

        # Contract payload
        contract_payload = {}

        if amount_val is not None:
            contract_payload["amount"] = {"currency": "NOK", "amount_per_year": amount_val}

        ext_c = matched.get("external_data") or {}
        if isinstance(ext_c, str):
            try:
                import json
                ext_c = json.loads(ext_c) if ext_c else {}
            except Exception:
                ext_c = {}

        regulation = _get_col(row, _COL_REGULATION)
        if regulation:
            ext_c["regulation_type"] = regulation
        ext_terms = _get_col(row, _COL_EXTENSION)
        if ext_terms:
            ext_c["extension_terms"] = ext_terms

        im = _get_amount(row, _COL_INDRE_VEDLIKEHOLD)
        if im is not None:
            ext_c["internal_maintenance_cost"] = im
        fc = _get_amount(row, _COL_FELLESKOSTNADER)
        if fc is not None:
            ext_c["common_costs"] = fc
        bd = _get_amount(row, _COL_BRUKERAVHENGIGE)
        if bd is not None:
            ext_c["user_dependent_costs"] = bd

        if ext_c:
            contract_payload["external_data"] = ext_c

        utleier = _norm(row.get("Utleier"))
        if utleier:
            party_id = get_or_create_party(utleier, args.dry_run)
            if party_id:
                contract_payload["party_id"] = party_id

        if avtalenavn:
            ext_c["contract_name"] = avtalenavn
            contract_payload["external_data"] = ext_c

        if contract_payload and not args.dry_run:
            api_patch("contracts", "contract_id", contract_id, contract_payload)
            contracts_updated += 1
        elif contract_payload and args.dry_run:
            contracts_updated += 1

    print(f"\nFerdig. Properties oppdatert: {props_updated}, Contracts oppdatert: {contracts_updated}")
    if skipped_no_prop:
        print(f"Rader uten matchende eiendom: {skipped_no_prop}")
    if skipped_no_contract:
        print(f"Rader uten matchende kontrakt: {skipped_no_contract}")


if __name__ == "__main__":
    main()
