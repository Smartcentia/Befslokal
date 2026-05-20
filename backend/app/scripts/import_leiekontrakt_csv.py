"""
Import leiekontrakter og eiendomsportefølje fra CSV til BEFS-databasen.

Primærkilde: Eiendomsportefølje per okt 2025 (Sheet1).csv  (CSV2)
Supplement:  Oversikt over leiekontrakter (Ark1).csv       (CSV1)

Regler:
- Kun fyll TOMME felt — aldri overskriv eksisterende DB-data
- ALDRI rør finance_budget-tabellen eller gl_rent_2025
- --dry-run: vis rapport uten å skrive til DB

Kjøring:
    python3 backend/app/scripts/import_leiekontrakt_csv.py \
        --csv2 "/Users/frank/Downloads/Eiendomsportefølje per okt 2025(Sheet1).csv" \
        --csv1 "/Users/frank/Downloads/Oversikt over leiekontrakter -(Ark1).csv" \
        --dry-run

    # Skriv til DB:
    python3 backend/app/scripts/import_leiekontrakt_csv.py \
        --csv2 "..." --csv1 "..." --execute
"""

import argparse
import asyncio
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ─── Hjelpefunksjoner for datarensing ────────────────────────────────────────

def _strip(val: str) -> str:
    return (val or "").strip()

def parse_amount(raw: str) -> Optional[float]:
    """
    Hent første tall fra fritekstfelt.
    '360000 fra nov.2020'      → 360000.0
    '606000 + 38000 fra 2006'  → 606000.0  (første tall)
    '1 560 000'                → 1560000.0
    '80000,-'                  → 80000.0
    ''                         → None
    """
    s = _strip(raw)
    if not s:
        return None
    # Fjern norske tusen-mellomrom og bytt komma-desimal
    s = s.replace("\xa0", " ")
    # Hent første tall-sekvens (inkl. mellomrom som tusenskilletegn)
    m = re.match(r"([\d][\d\s]*)", s)
    if not m:
        return None
    num_str = m.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None

def parse_date(raw: str) -> Optional[str]:
    """
    DD.MM.YYYY (med evt. * og tekst-noter) → 'YYYY-MM-DD' streng.
    Returnerer None ved feil eller prospektiv tekst.
    """
    s = _strip(raw).replace("*", "")
    # Forkast prospektive tekster
    if "antatt" in s.lower() or "oppstart" in s.lower():
        return None
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if not m:
        return None
    d, mo, yr = m.groups()
    # Forkast åpenbare årstallsfeil
    if int(yr) < 1950 or int(yr) > 2060:
        return None
    return f"{yr}-{mo.zfill(2)}-{d.zfill(2)}"

def parse_int_first(raw: str) -> Optional[int]:
    """Hent første heltall fra felt (bnr/gnr/plasser)."""
    s = _strip(raw)
    if not s:
        return None
    m = re.match(r"(\d+)", s.replace(" ", ""))
    if not m:
        return None
    return int(m.group(1))

def parse_float_first(raw: str) -> Optional[float]:
    """Hent første desimaltall fra felt (areal)."""
    s = _strip(raw).replace("\xa0", " ").replace(",", ".")
    # Ta bare siste ord/tall-gruppe i parenteser bort
    s = re.sub(r"\(.*?\)", "", s).strip()
    m = re.match(r"([\d][\d\s\.]*)", s)
    if not m:
        return None
    num = m.group(1).replace(" ", "")
    try:
        return float(num)
    except ValueError:
        return None

def parse_utleier_kategori(raw: str) -> Optional[int]:
    """'Statsbygg' / 'Statlig' → 2, andre → 1."""
    s = _strip(raw).lower()
    if "statsbygg" in s or "statlig" in s:
        return 2
    if s:
        return 1
    return None

def parse_status(raw: str) -> Optional[str]:
    """CSV-status → DB-status ('active' eller 'terminated')."""
    s = _strip(raw).lower()
    if not s:
        return None
    if any(x in s for x in ["aktiv", "active", "pågående"]):
        return "active"
    if any(x in s for x in ["avsluttet", "terminated", "utløpt", "inaktiv"]):
        return "terminated"
    return None

# ─── CSV-lesing ───────────────────────────────────────────────────────────────

def read_csv2(path: str) -> list[dict]:
    """Les Eiendomsportefølje (CSV2) — semikolon, ISO-8859-1."""
    rows = []
    with open(path, encoding="iso-8859-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(dict(row))
    logger.info("CSV2: %d rader lest fra %s", len(rows), path)
    return rows

def read_csv1(path: str) -> list[dict]:
    """Les Oversikt leiekontrakter (CSV1) — semikolon, ISO-8859-1, header på rad 2."""
    rows = []
    with open(path, encoding="iso-8859-1", newline="") as f:
        lines = f.readlines()
    # Rad 0 er bare skilletegn, rad 1 er headers
    reader = csv.DictReader(lines[1:], delimiter=";")
    for row in reader:
        rows.append(dict(row))
    logger.info("CSV1: %d rader lest fra %s", len(rows), path)
    return rows

# ─── DB-kobling ───────────────────────────────────────────────────────────────

async def get_db_session():
    """Hent async DB-session fra app-konfig."""
    import os, sys
    # Legg til backend-rot i path
    backend_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_root))

    from app.db.session import SessionLocal
    async with SessionLocal() as session:
        return session

# ─── Match-logikk ─────────────────────────────────────────────────────────────

def extract_lokalisering_id(lokalisering: str) -> Optional[str]:
    """
    '1101 - FHT, ESF, MST...' → '1101'
    '1102 - Bodø Behandlingssenter' → '1102'
    """
    m = re.match(r"^(\d+)\s*[-–]", _strip(lokalisering))
    return m.group(1) if m else None

# ─── Hoved-importlogikk ──────────────────────────────────────────────────────

async def run_import(csv2_path: str, csv1_path: Optional[str], dry_run: bool):
    import os, sys
    backend_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_root))

    # Sett DATABASE_URL fra .env hvis ikke satt
    env_file = backend_root / ".env"
    if env_file.exists() and not os.environ.get("DATABASE_URL"):
        for line in env_file.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip().strip('"')
                break

    from sqlalchemy import text
    from app.db.session import SessionLocal

    rows2 = read_csv2(csv2_path)
    rows1 = read_csv1(csv1_path) if csv1_path else []

    # Bygg org.nr-supplement fra CSV1 (bedre dekning)
    orgnr_by_name: dict[str, str] = {}
    for r in rows1:
        name = _strip(r.get("Utleier", "") or r.get("Utleier ", ""))
        orgnr = _strip(r.get("Org.nr: Utleier", "") or r.get("Org.nr: Utleier ", ""))
        if name and orgnr:
            orgnr_by_name[name.lower()] = orgnr

    stats = {
        "rader_lest": len(rows2),
        "matchet": 0,
        "ikke_matchet": 0,
        "properties_oppdatert": 0,
        "contracts_funnet": 0,
        "contracts_oppdatert": 0,
        "felt_satt": 0,
        "feil": [],
    }
    unmatched = []

    async with SessionLocal() as db:
        for row in rows2:
            try:
                await _process_row(db, row, orgnr_by_name, stats, unmatched, dry_run)
            except Exception as e:
                stats["feil"].append(f"{row.get('Lokalisering','?')}: {e}")
                logger.warning("Feil på rad %s: %s", row.get("Lokalisering"), e)

        if not dry_run:
            await db.commit()
            logger.info("DB commit utført.")
        else:
            await db.rollback()
            logger.info("DRY-RUN: ingen endringer skrevet til DB.")

    # ─── Rapport ───────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("IMPORTRAPPORT" + (" [DRY-RUN]" if dry_run else " [FAKTISK]"))
    print("="*60)
    print(f"Rader lest (CSV2):          {stats['rader_lest']}")
    print(f"Matchet mot DB:             {stats['matchet']}")
    print(f"Ikke matchet:               {stats['ikke_matchet']}")
    print(f"Properties oppdatert:       {stats['properties_oppdatert']}")
    print(f"Kontrakter funnet:          {stats['contracts_funnet']}")
    print(f"Kontrakter oppdatert:       {stats['contracts_oppdatert']}")
    print(f"Totalt felt satt:           {stats['felt_satt']}")
    print(f"Feil:                       {len(stats['feil'])}")

    if unmatched:
        print(f"\nIKKE MATCHET ({len(unmatched)} rader):")
        for u in unmatched[:30]:
            print(f"  - {u}")
        if len(unmatched) > 30:
            print(f"  ... og {len(unmatched)-30} til")

    if stats["feil"]:
        print(f"\nFEIL ({len(stats['feil'])}):")
        for e in stats["feil"][:20]:
            print(f"  ! {e}")

    print("="*60)


async def _process_row(db, row: dict, orgnr_by_name: dict, stats: dict, unmatched: list, dry_run: bool):
    from sqlalchemy import text

    lokalisering = _strip(row.get("Lokalisering", ""))
    lok_id = extract_lokalisering_id(lokalisering)

    # ─── Match mot property ──────────────────────────────────────────────
    property_row = None

    if lok_id:
        res = await db.execute(
            text("SELECT property_id, name, address, municipality_code, gnr, bnr, "
                 "total_area, leased_area_kvm, land_area, malgruppe, approved_places, "
                 "regulation_type, extension_terms, lok_distrikt, lok_omrade, "
                 "utleier_kategori, contract_rent_nok, contract_maint_nok, "
                 "contract_common_nok, contract_user_ops_nok, elements_id, "
                 "municipality, postal_code, city "
                 "FROM properties WHERE lokalisering_id = :lid LIMIT 1"),
            {"lid": lok_id}
        )
        property_row = res.fetchone()

    if not property_row:
        # Fallback: match på adresse + kommunenummer
        addr = _strip(row.get("Adresselinje 1", ""))
        knr  = _strip(row.get("Matrikkel Knr", ""))
        if addr and knr:
            res = await db.execute(
                text("SELECT property_id, name, address, municipality_code, gnr, bnr, "
                     "total_area, leased_area_kvm, land_area, malgruppe, approved_places, "
                     "regulation_type, extension_terms, lok_distrikt, lok_omrade, "
                     "utleier_kategori, contract_rent_nok, contract_maint_nok, "
                     "contract_common_nok, contract_user_ops_nok, elements_id, "
                     "municipality, postal_code, city "
                     "FROM properties WHERE municipality_code = :knr "
                     "AND LOWER(address) LIKE LOWER(:addr) LIMIT 1"),
                {"knr": knr, "addr": f"%{addr.split(',')[0].strip()}%"}
            )
            property_row = res.fetchone()

    if not property_row:
        stats["ikke_matchet"] += 1
        unmatched.append(lokalisering or row.get("Avtalenavn", "?"))
        return

    stats["matchet"] += 1
    prop_id = str(property_row.property_id)
    felt_satt = 0
    updates: dict = {}

    # ─── Bygg oppdatering (kun tomme felt) ──────────────────────────────

    def _set_if_empty(db_val, csv_raw, parser, col: str):
        nonlocal felt_satt
        if db_val is not None and str(db_val).strip():
            return  # DB-felt har allerede verdi — ikke overskriv
        parsed = parser(csv_raw) if callable(parser) else csv_raw
        if parsed is not None and str(parsed).strip():
            updates[col] = parsed
            felt_satt += 1

    # Identifikasjon
    _set_if_empty(property_row.municipality,      row.get("kommunenavn",""),           _strip,              "municipality")
    _set_if_empty(property_row.postal_code,       row.get("Adresse og Postnummer",""), lambda s: _strip(s).split()[-1] if _strip(s) else None, "postal_code")
    _set_if_empty(property_row.city,              row.get("Poststed",""),              _strip,              "city")
    _set_if_empty(property_row.municipality_code, row.get("Matrikkel Knr",""),         _strip,              "municipality_code")
    _set_if_empty(property_row.gnr,               row.get("Matrikkel Gnr",""),         parse_int_first,     "gnr")
    _set_if_empty(property_row.bnr,               row.get("Matrikkel Bnr",""),         parse_int_first,     "bnr")
    _set_if_empty(property_row.elements_id,       row.get("Elements",""),              _strip,              "elements_id")

    # Lok-info
    _set_if_empty(property_row.lok_distrikt, row.get("Lok: Distrikt",""), _strip, "lok_distrikt")
    _set_if_empty(property_row.lok_omrade,   row.get("Lok: Område",""),   _strip, "lok_omrade")

    # Areal
    _set_if_empty(property_row.total_area,      row.get("Areal",""),                              parse_float_first, "total_area")
    _set_if_empty(property_row.leased_area_kvm, row.get("Areal inkl fellesareal i leiekontrakt (kvm)",""), parse_float_first, "leased_area_kvm")
    _set_if_empty(property_row.land_area,       row.get("tomteareal",""),                         parse_float_first, "land_area")

    # Kapasitet & type
    _set_if_empty(property_row.malgruppe,       row.get("Type lokasjon","") or row.get("Målgruppe",""), _strip,         "malgruppe")
    _set_if_empty(property_row.approved_places, row.get("Antall godkjente plasser",""),                 parse_int_first, "approved_places")

    # Utleier
    _set_if_empty(property_row.utleier_kategori, row.get("Utleier kategori",""), parse_utleier_kategori, "utleier_kategori")

    # Leievilkår
    _set_if_empty(property_row.regulation_type, row.get("leieregulering",""),        _strip, "regulation_type")
    _set_if_empty(property_row.extension_terms, row.get("forlengelse &vilkår",""),   _strip, "extension_terms")

    # Kontraktskostnader (startverdier — ikke økonomibudsjett)
    _set_if_empty(property_row.contract_rent_nok,     row.get("Kontraktsleie ved oppstart (per år)",""), parse_amount, "contract_rent_nok")
    _set_if_empty(property_row.contract_common_nok,   row.get("Felleskostnader per år (ved kontraktsinngåelse)",""), parse_amount, "contract_common_nok")
    _set_if_empty(property_row.contract_user_ops_nok, row.get("Brukeravhengige driftskostander - Første driftsår",""), parse_amount, "contract_user_ops_nok")
    _set_if_empty(property_row.contract_maint_nok,    row.get("Kostnad til indre vedlikehold per år",""), parse_amount, "contract_maint_nok")

    # ─── Kjør UPDATE på properties ──────────────────────────────────────
    if updates:
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["prop_id"] = prop_id
        if not dry_run:
            await db.execute(
                text(f"UPDATE properties SET {set_clause}, updated_at = NOW() WHERE property_id = :prop_id"),
                updates
            )
        stats["properties_oppdatert"] += 1
        stats["felt_satt"] += felt_satt
        if dry_run:
            logger.debug("DRY property %s: %s", prop_id, list(updates.keys()))

    # ─── Kontrakt-oppdatering ───────────────────────────────────────────
    start_date = parse_date(row.get("Startdato", ""))
    end_date   = parse_date(row.get("Sluttdato", ""))
    status_csv = parse_status(row.get("Status", ""))
    avtalenavn = _strip(row.get("Avtalenavn", ""))

    # Finn kontrakt via property
    res2 = await db.execute(
        text("""SELECT c.contract_id, c.start_date, c.end_date, c.status,
                       c.contract_name, c.amount
                FROM contracts c
                JOIN units u ON u.unit_id = c.unit_id
                WHERE u.property_id = :pid
                ORDER BY c.created_at DESC LIMIT 1"""),
        {"pid": prop_id}
    )
    contract_row = res2.fetchone()

    if contract_row:
        stats["contracts_funnet"] += 1
        cont_updates: dict = {}
        c_felt = 0

        def _c_set(db_val, csv_val, col: str):
            nonlocal c_felt
            if db_val is not None and str(db_val).strip():
                return
            if csv_val is not None and str(csv_val).strip():
                cont_updates[col] = csv_val
                c_felt += 1

        _c_set(contract_row.start_date,    start_date, "start_date")
        _c_set(contract_row.end_date,      end_date,   "end_date")
        _c_set(contract_row.status,        status_csv, "status")
        _c_set(contract_row.contract_name, avtalenavn, "contract_name")

        # amount.amount_per_year
        csv_rent = parse_amount(row.get("Kontraktsleie ved oppstart (per år)", ""))
        if csv_rent and contract_row.amount:
            import json
            amt = contract_row.amount if isinstance(contract_row.amount, dict) else {}
            if not amt.get("amount_per_year"):
                cont_updates["amount"] = json.dumps({"currency": "NOK", "amount_per_year": csv_rent})
                c_felt += 1
        elif csv_rent and not contract_row.amount:
            import json
            cont_updates["amount"] = json.dumps({"currency": "NOK", "amount_per_year": csv_rent})
            c_felt += 1

        if cont_updates:
            set_clause = ", ".join(f"{k} = :{k}" for k in cont_updates)
            cont_updates["cid"] = str(contract_row.contract_id)
            if not dry_run:
                await db.execute(
                    text(f"UPDATE contracts SET {set_clause}, updated_at = NOW() WHERE contract_id = :cid"),
                    cont_updates
                )
            stats["contracts_oppdatert"] += 1
            stats["felt_satt"] += c_felt

    # ─── Party (utleier) ────────────────────────────────────────────────
    utleier_name = _strip(row.get("Utleier", ""))
    utleier_orgnr = _strip(row.get("org nr utleier", ""))
    if not utleier_orgnr and utleier_name:
        utleier_orgnr = orgnr_by_name.get(utleier_name.lower(), "")

    if utleier_name and utleier_orgnr:
        res3 = await db.execute(
            text("SELECT party_id, orgnr FROM parties WHERE LOWER(name) = LOWER(:nm) LIMIT 1"),
            {"nm": utleier_name}
        )
        party_row = res3.fetchone()
        if party_row and not party_row.orgnr and utleier_orgnr:
            if not dry_run:
                await db.execute(
                    text("UPDATE parties SET orgnr = :orgnr WHERE party_id = :pid"),
                    {"orgnr": utleier_orgnr, "pid": str(party_row.party_id)}
                )
            stats["felt_satt"] += 1


# ─── CLI-entry ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import leiekontrakt CSV til BEFS DB")
    parser.add_argument("--csv2", required=True, help="Eiendomsportefølje CSV (primær)")
    parser.add_argument("--csv1", default=None, help="Leiekontrakt CSV (supplement, valgfri)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run",  dest="dry_run",  action="store_true",  help="Vis rapport uten å skrive til DB")
    group.add_argument("--execute",  dest="dry_run",  action="store_false", help="Skriv til DB")
    args = parser.parse_args()

    asyncio.run(run_import(args.csv2, args.csv1, args.dry_run))


if __name__ == "__main__":
    main()
