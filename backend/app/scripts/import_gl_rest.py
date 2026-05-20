"""
Import 2025 GL data via Supabase REST API (HTTPS only, no direct DB connection).

Usage:
    cd backend
    SUPABASE_SERVICE_KEY=... python app/scripts/import_gl_rest.py [--file path] [--dry-run]

Reads 01.txt, resolves property_id via REST, inserts gl_transactions in batches.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SUPABASE_URL = "https://vwvhxcqxadblrftuvsds.supabase.co"
SERVICE_KEY = os.environ.get(
    "SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3dmh4Y3F4YWRibHJmdHV2c2RzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTMzODUwMiwiZXhwIjoyMDg2OTE0NTAyfQ.h071E-xhKw1uPPuNzxtyv2a1oAXK1eJF8NXZ9EpMlWc",
)

DATA_YEAR = 2025
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
DEFAULT_FILE = DOCS_DIR / "01.txt"
BATCH_SIZE = 100


def source_system_for(filepath: Path) -> str:
    """Derive a stable source_system key from the filename."""
    stem = filepath.stem  # e.g. "01", "02", ...
    if stem == "01":
        return "gl_2025_midt"  # keep existing name for backward compat
    return f"gl_2025_{stem}"

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# ---------------------------------------------------------------------------
# Parser (same logic as import_gl_2025.py)
# ---------------------------------------------------------------------------
KNOWN_FORMALS = [
    "Barnevernsinstitusjoner",
    "Fosterhjem",
    "Hjelpetiltak i hjemmet",
    "Fosterhjemstjenesten",
    "Inntak",
    "Regionale fellesfunksjoner",
    "Familieverntjeneste",
    "Sentre for foreldre og barn",
    "Omsorgssentre for mindreårige asylsøkere",
    "Adopsjon",
]

KNOWN_ART = sorted([
    "Leie lokaler fra Statsbygg",
    "Leie lokaler andre utleiere",
    "Leie parkeringsplass",
    "Strøm og oppvarming",
    "Renhold lokaler",
    "Renovasjon, vann, avløp o.l.",
    "Reparasjon og vedlikehold leide lokaler",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Vakthold lokaler",
    "Vaktmestertjenester",
    "Fellesutgifter Statsbygg - indre vedlikehold",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter andre utleiere",
    "Fellesutgifter",
    "Annen kostnad lokaler",
    "Fast bygningsinventar og påkostning, leide bygg",
    "Fast bygningsinventar over kr 50 000",
    "Oppgradering og påkostning leide lokaler - under kr 50 000",
], key=len, reverse=True)

LEASE_ARTS = {
    "Leie lokaler fra Statsbygg",
    "Leie lokaler andre utleiere",
    "Leie parkeringsplass",
}


def parse_line(line: str):
    tokens = line.strip().split()
    if len(tokens) < 6:
        return None

    ba = tokens[0]
    region = tokens[1] + " " + tokens[2]
    koststed = tokens[3]
    amount_raw = tokens[-1].replace(",", ".").replace(" ", "")
    try:
        amount = float(amount_raw)
    except ValueError:
        return None

    middle = tokens[4:-1]
    middle_str = " ".join(middle)

    found = None
    for art in KNOWN_ART:
        idx = middle_str.find(art)
        if idx == -1:
            continue
        prefix_str = middle_str[:idx].rstrip()
        # Check that the prefix ends with a known Formål
        for formal in KNOWN_FORMALS:
            if prefix_str.endswith(formal):
                vendor_str = middle_str[idx + len(art):].strip() or None
                before_formal = prefix_str[: len(prefix_str) - len(formal)].strip()
                found = {
                    "art": art,
                    "formal": formal,
                    "vendor": vendor_str,
                    "prefix": before_formal,
                }
                break
        if found:
            break

    if not found:
        return None

    prefix = found["prefix"]
    unit_name = prefix
    proj_nr = None
    proj_tekst = None

    m = re.search(r"\b(\d{5,6})\b", prefix)
    if m and not m.group(1).startswith("5"):
        unit_name = prefix[: m.start()].strip()
        rest = prefix[m.start():].strip()
        proj_nr = m.group(1)
        proj_tekst = rest[len(proj_nr):].strip() or None

    return {
        "ba": ba,
        "region": region,
        "koststed": koststed,
        "unit_name": unit_name or None,
        "proj_nr": proj_nr,
        "proj_tekst": proj_tekst,
        "formal": found["formal"],
        "art": found["art"],
        "vendor": found["vendor"],
        "amount": amount,
    }


# ---------------------------------------------------------------------------
# REST helpers
# ---------------------------------------------------------------------------
def rest_get(path: str, params: str = "") -> list:
    url = f"{SUPABASE_URL}/rest/v1/{path}{'?' + params if params else ''}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def rest_post(path: str, data: list) -> int:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {body[:300]}", file=sys.stderr)
        raise


def rest_delete(path: str, params: str) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{path}?{params}"
    req = urllib.request.Request(url, headers=HEADERS, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            pass
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  DELETE HTTP {e.code}: {body[:300]}", file=sys.stderr)
        raise


# ---------------------------------------------------------------------------
# Property lookup cache
# ---------------------------------------------------------------------------
_property_cache: dict = {}  # koststed → property_id or None
_name_cache: dict = {}       # unit_name → property_id or None


def load_all_properties() -> list:
    """Load all properties with unit_id_erp and name."""
    rows = rest_get("properties", "select=property_id,unit_id_erp,name")
    return rows


def resolve_property_id(props: list, koststed: str, unit_name):
    if koststed in _property_cache:
        return _property_cache[koststed]

    # Pass 1: unit_id_erp exact match
    for p in props:
        if p.get("unit_id_erp") == koststed:
            _property_cache[koststed] = p["property_id"]
            return p["property_id"]

    # Pass 2: name match
    if unit_name:
        key = unit_name.lower().strip()
        for p in props:
            pname = (p.get("name") or "").lower()
            if pname == key:
                _property_cache[koststed] = p["property_id"]
                return p["property_id"]
        # substring fallback
        words = [w for w in unit_name.split() if len(w) > 4]
        if words:
            for p in props:
                pname = (p.get("name") or "").lower()
                if all(w.lower() in pname for w in words[:2]):
                    _property_cache[koststed] = p["property_id"]
                    return p["property_id"]

    _property_cache[koststed] = None
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_import(filepath: Path, dry_run: bool = False, props: list = None) -> None:
    source_system = source_system_for(filepath)
    if props is None:
        print(f"Loading properties from Supabase...")
        props = load_all_properties()
        print(f"  Found {len(props)} properties.")

    lines = filepath.read_text(encoding="utf-8").splitlines()
    total = len([l for l in lines if l.strip()])

    parsed_ok = 0
    parse_errors = 0
    mapped = 0
    skipped_unmapped = 0
    rows_to_insert = []
    unmapped: dict = {}

    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            continue

        parsed = parse_line(raw)
        if not parsed:
            parse_errors += 1
            print(f"  PARSE ERROR line {i}: {raw[:100]}", file=sys.stderr)
            continue

        parsed_ok += 1
        koststed = parsed["koststed"]
        unit_name = parsed["unit_name"]

        property_id = resolve_property_id(props, koststed, unit_name)
        if property_id:
            mapped += 1
        else:
            skipped_unmapped += 1
            if koststed not in unmapped:
                unmapped[koststed] = unit_name or ""
            continue  # skip unmapped rows

        rows_to_insert.append({
            "transaction_id": str(uuid.uuid4()),
            "property_id": property_id,
            "region_name": parsed["region"],
            "department_code": koststed,
            "department_name": unit_name,
            "dim2_code": parsed["proj_nr"],
            "dim2_name": parsed["proj_tekst"],
            "purpose_name": parsed["formal"],
            "account_name": parsed["art"],
            "supplier_name": parsed["vendor"],
            "amount": str(parsed["amount"]),
            "year": DATA_YEAR,
            "ba_code": parsed["ba"],
            "ba_name": "Bufetat",
            "source_system": source_system,
            "category": "lease" if parsed["art"] in LEASE_ARTS else "other",
            "vendor": parsed["vendor"],
        })

    print()
    print("=" * 50)
    print(f"Fil:               {filepath.name}")
    print(f"Rader totalt:      {total}")
    print(f"Parset ok:         {parsed_ok}")
    print(f"Parse-feil:        {parse_errors}")
    print(f"Mappet→eiendom:    {mapped}")
    print(f"Hoppet over:       {skipped_unmapped}")
    print(f"Klare for import:  {len(rows_to_insert)}")

    if unmapped:
        print("\nUmappede koststed:")
        for k, v in sorted(unmapped.items()):
            print(f"  {k}  {v}")

    if dry_run:
        print("\n[DRY RUN - ingen data lagret]")
        return

    # Wipe existing batch
    print(f"\nSletter eksisterende '{source_system}' rader...")
    rest_delete("gl_transactions", f"source_system=eq.{source_system}")
    print("  Slettet.")

    # Insert in batches
    inserted = 0
    for start in range(0, len(rows_to_insert), BATCH_SIZE):
        batch = rows_to_insert[start: start + BATCH_SIZE]
        rest_post("gl_transactions", batch)
        inserted += len(batch)
        print(f"  Insertet {inserted}/{len(rows_to_insert)}...", end="\r")

    print(f"\nFerdig! {inserted} rader importert.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import GL 2025 data via Supabase REST")
    parser.add_argument("--file", type=Path, default=None,
                        help="Enkeltfil å importere (default: alle *.txt i docs/)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    def is_gl_file(p: Path) -> bool:
        """Return True if file looks like raw GL transaction data."""
        try:
            first = p.read_text(encoding="utf-8").split("\n", 1)[0].strip()
            tokens = first.split()
            # GL files start with: BA(digit) Region XXXXX koststed(digits) ...
            return len(tokens) > 3 and tokens[0].isdigit() and tokens[1] == "Region"
        except Exception:
            return False

    if args.file:
        files = [args.file]
    else:
        files = sorted(DOCS_DIR.glob("*.txt"))
        # Only numeric stems (01.txt, 02.txt, ...), skip docs/analysis files
        files = [f for f in files if f.stem.isdigit() and is_gl_file(f)]

    if not files:
        print("Ingen .txt filer funnet", file=sys.stderr)
        sys.exit(1)

    # Load properties once for all files
    print(f"Loading properties from Supabase...")
    all_props = load_all_properties()
    print(f"  Found {len(all_props)} properties.\n")

    for filepath in files:
        if not filepath.exists():
            print(f"Fant ikke fil: {filepath}", file=sys.stderr)
            continue
        print(f"\n{'='*60}")
        print(f"Importerer: {filepath.name}  (source_system={source_system_for(filepath)})")
        print(f"{'='*60}")
        run_import(filepath, dry_run=args.dry_run, props=all_props)
