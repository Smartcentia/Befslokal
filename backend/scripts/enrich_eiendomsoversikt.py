"""
enrich_eiendomsoversikt.py — Beriker BEFS-properties med felter fra eiendomsoversikt-CSV

STRATEGI (VIKTIG):
  • Aldri overskriv eksisterende (ikke-NULL) verdier
  • Alle UPDATE-setninger sjekker NULL i Python FØR de sender til DB
  • Aldri berør: region, address, postal_code, city, municipality,
    start_date, end_date, contract_name, status, party_id, amount, belop

SAFE-felter som IKKE røres:
  Region, Adresselinje 1, Postnr, Poststed, Startdato, Sluttdato,
  Utleier, Status, Kommunenavn, Lok: Område

Felter som berikes:
  properties.malgruppe              ← Målgruppe (ny kolonne)
  properties.contract_rent_nok      ← Kontraktsleie kr/år (ny kolonne)
  properties.contract_maint_nok     ← Indre vedlikehold kr/år (ny kolonne)
  properties.contract_common_nok    ← Felleskostnader kr/år (ny kolonne)
  properties.contract_user_ops_nok  ← Brukeravhengige driftskostnader (ny kolonne)
  properties.extension_terms        ← Adgang til forlengelse (ny kolonne)
  properties.price_adj_clause       ← Prisjusteringsfaktor (ny kolonne)
  properties.lokasjon_type          ← Institusjonstype (kun WHERE NULL)
  properties.approved_places        ← Antall G/K-plasser (kun WHERE NULL)
  properties.budgeted_places        ← Antall budsjetterte plasser (kun WHERE NULL)
  properties.legal_basis            ← Hjemmel § (kun WHERE NULL)

Kjøring:
  DATABASE_URL="postgresql+asyncpg://..." \\
  OVERSIKT_CSV="/Users/frank/Downloads/1 (1).csv" \\
  python scripts/enrich_eiendomsoversikt.py [--dry-run]
"""

import asyncio
import csv
import os
import re
import sys

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
OVERSIKT_CSV = os.environ.get(
    "OVERSIKT_CSV",
    "/Users/frank/Downloads/1 (1).csv",
)
DRY_RUN = "--dry-run" in sys.argv

# Felter vi aldri rører
SAFE_FIELDS = {
    "region", "address", "postal_code", "city", "municipality",
    "name", "owner_name", "org_number",
}


# ── Parsing helpers ────────────────────────────────────────────────────────────

def extract_lok_code(s: str) -> str | None:
    m = re.match(r"^(\d+)", s.strip())
    return m.group(1) if m else None


def parse_nok(s: str) -> float | None:
    """'1 234 567' or '1234567' → 1234567.0"""
    s = s.replace("\xa0", "").replace(" ", "").replace(" ", "").strip()
    if not s or s in ("0", "-"):
        return None
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def parse_int_places(s: str) -> int | None:
    """'4' → 4, 'Avd. X: 4' → 4 (first number), '0' → None"""
    s = s.strip()
    if not s or s == "0":
        return None
    m = re.search(r"(\d+)", s)
    if m:
        v = int(m.group(1))
        return v if v > 0 else None
    return None


def clean_text(s: str, max_len: int = 300) -> str | None:
    s = s.strip()
    if not s or s.lower() in ("ikke oppgitt", "-", ""):
        return None
    return s[:max_len]


# ── CSV loader ─────────────────────────────────────────────────────────────────

def load_csv(path: str) -> list[dict]:
    with open(path, encoding="latin-1") as f:
        lines = f.readlines()
    # Row 1: group headers (skip), Row 2: column names
    headers = lines[1].strip().split(";")
    rows = []
    for line in lines[2:]:
        vals = line.strip().split(";")
        while len(vals) < len(headers):
            vals.append("")
        rows.append(dict(zip(headers, vals)))
    return rows


# ── Main enrichment ────────────────────────────────────────────────────────────

async def enrich(csv_rows: list[dict]) -> None:
    pg_url = DATABASE_URL
    if not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(pg_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # Hent alle properties med lokalisering_id + relevante nåværende felter
        result = await session.execute(sa.text("""
            SELECT
                property_id::text,
                lokalisering_id,
                malgruppe,
                contract_rent_nok,
                contract_maint_nok,
                contract_common_nok,
                contract_user_ops_nok,
                extension_terms,
                price_adj_clause,
                lokasjon_type,
                approved_places,
                budgeted_places,
                legal_basis,
                lok_omrade,
                egnethet_lokalisering,
                egnethet_bygg,
                prioritert_videroforing,
                ar_videreutvikling,
                kostnader_videreutvikling
            FROM properties
            WHERE lokalisering_id IS NOT NULL
        """))
        db_props = {
            str(p["lokalisering_id"]).strip(): dict(p)
            for p in result.mappings().all()
            if p["lokalisering_id"]
        }

        print(f"DB: {len(db_props)} properties med lokalisering_id")
        print(f"CSV: {len(csv_rows)} rader")

        updated = 0
        no_change = 0
        no_match = 0
        errors = 0
        field_counts: dict[str, int] = {}

        for row in csv_rows:
            lok_code = extract_lok_code(row.get("Lokalisering", ""))
            if not lok_code:
                no_match += 1
                continue

            prop = db_props.get(lok_code)
            if not prop:
                no_match += 1
                continue

            prop_id = prop["property_id"]
            updates: dict[str, object] = {}

            # ── Ny kolonne: malgruppe (alltid oppdater fra denne kilden) ──────
            maalgruppe = clean_text(row.get("Målgruppe ", ""), 100)
            if maalgruppe and prop["malgruppe"] is None:
                updates["malgruppe"] = maalgruppe

            # ── Ny kolonne: contract_rent_nok ─────────────────────────────────
            leie = parse_nok(row.get("Kontraktsleie", ""))
            if leie is not None and prop["contract_rent_nok"] is None:
                updates["contract_rent_nok"] = leie

            # ── Ny kolonne: contract_maint_nok ────────────────────────────────
            vedl = parse_nok(row.get("Indre vedlikehold", ""))
            if vedl is not None and prop["contract_maint_nok"] is None:
                updates["contract_maint_nok"] = vedl

            # ── Ny kolonne: contract_common_nok ───────────────────────────────
            felles = parse_nok(row.get("Felleskostnader", ""))
            if felles is not None and prop["contract_common_nok"] is None:
                updates["contract_common_nok"] = felles

            # ── Ny kolonne: contract_user_ops_nok ─────────────────────────────
            drift = parse_nok(row.get("Brukeravhengige driftskostnader", ""))
            if drift is not None and prop["contract_user_ops_nok"] is None:
                updates["contract_user_ops_nok"] = drift

            # ── Ny kolonne: extension_terms ───────────────────────────────────
            ext = clean_text(row.get("Adgang til forlengelse og vilkår", ""), 500)
            if ext and prop["extension_terms"] is None:
                updates["extension_terms"] = ext

            # ── Ny kolonne: price_adj_clause ──────────────────────────────────
            kpi = clean_text(row.get("Årlig prisjusteringsfaktaktor", ""), 300)
            if kpi and prop["price_adj_clause"] is None:
                updates["price_adj_clause"] = kpi

            # ── Eksisterende kolonne: lokasjon_type (kun WHERE NULL) ──────────
            inst_type = clean_text(row.get("Institusjonstype /Type lokasjon", ""), 50)
            if inst_type and prop["lokasjon_type"] is None:
                updates["lokasjon_type"] = inst_type

            # ── Eksisterende kolonne: approved_places (kun WHERE NULL) ────────
            gk = parse_int_places(row.get("Antall G/K - plasser", ""))
            if gk is not None and prop["approved_places"] is None:
                updates["approved_places"] = gk

            # ── Eksisterende kolonne: budgeted_places (kun WHERE NULL) ────────
            bud = parse_int_places(row.get("Antall budsjetterte plasser", ""))
            if bud is not None and prop["budgeted_places"] is None:
                updates["budgeted_places"] = bud

            # ── Eksisterende kolonne: legal_basis (kun WHERE NULL) ────────────
            hjemmel = clean_text(row.get("Hjemmel §", ""), 1000)
            if hjemmel and prop["legal_basis"] is None:
                updates["legal_basis"] = hjemmel

            # ── Ny kolonne: lok_omrade (f.eks. "03 - Trøndelag") ─────────────
            lok_omr = clean_text(row.get("Lok: Område", ""), 50)
            if lok_omr and prop["lok_omrade"] is None:
                updates["lok_omrade"] = lok_omr

            # ── Ny kolonne: egnethet_lokalisering (kun WHERE NULL) ────────────
            egn_lok = clean_text(row.get("Egnethet lokalisering ", ""), 100)
            if egn_lok and prop["egnethet_lokalisering"] is None:
                updates["egnethet_lokalisering"] = egn_lok

            # ── Ny kolonne: egnethet_bygg (kun WHERE NULL) ────────────────────
            egn_bygg = clean_text(row.get("Egnethet bygg", ""), 100)
            if egn_bygg and prop["egnethet_bygg"] is None:
                updates["egnethet_bygg"] = egn_bygg

            # ── Ny kolonne: prioritert_videroforing (kun WHERE NULL) ──────────
            prioritert = clean_text(row.get("Priortert viderført /utviklet ", ""), 50)
            if prioritert and prop["prioritert_videroforing"] is None:
                updates["prioritert_videroforing"] = prioritert

            # ── Ny kolonne: ar_videreutvikling (kun WHERE NULL) ───────────────
            ar_str = row.get("År for videreutvikling ", "").strip()
            if ar_str and prop["ar_videreutvikling"] is None:
                try:
                    ar_val = int(ar_str)
                    if 2020 <= ar_val <= 2050:
                        updates["ar_videreutvikling"] = ar_val
                except ValueError:
                    pass

            # ── Ny kolonne: kostnader_videreutvikling (kun WHERE NULL) ────────
            kost = parse_nok(row.get("Kostnader til videreutvikling ", ""))
            if kost is not None and prop["kostnader_videreutvikling"] is None:
                updates["kostnader_videreutvikling"] = kost

            if not updates:
                no_change += 1
                continue

            # Telle hvilke felt som faktisk oppdateres
            for k in updates:
                field_counts[k] = field_counts.get(k, 0) + 1

            if DRY_RUN:
                print(f"  [DRY] {lok_code} ({prop_id[:8]}…): {list(updates.keys())}")
            else:
                set_sql = ", ".join(f"{k} = :{k}" for k in updates)
                updates["prop_id"] = prop_id
                try:
                    await session.execute(
                        sa.text(f"""
                            UPDATE properties
                            SET {set_sql}
                            WHERE property_id::text = :prop_id
                        """),
                        updates,
                    )
                except Exception as exc:
                    errors += 1
                    print(f"  ⚠️  FEIL {lok_code} ({prop_id[:8]}…): {exc}")
                    await session.rollback()
                    continue
            updated += 1

        if not DRY_RUN:
            try:
                await session.commit()
            except Exception as exc:
                print(f"  ⚠️  COMMIT FEIL: {exc}")
                await session.rollback()

    await engine.dispose()

    prefix = "[DRY RUN] " if DRY_RUN else ""
    print(f"\n{prefix}Resultat:")
    print(f"  ✅ Oppdatert:       {updated}")
    print(f"  ⏭️  Ingen endring:   {no_change}")
    print(f"  ❌ Ingen match:     {no_match}")
    print(f"  💥 Feil:            {errors}")
    print()
    print(f"{prefix}Felt oppdatert (antall eiendommer per felt):")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"  {field}: {count}")
    print()
    print("Felter som IKKE ble berørt (safe):")
    print("  region, address, postal_code, city, municipality, name,")
    print("  start_date, end_date, contract_name, status, party_id, amount")


async def main() -> None:
    if not DATABASE_URL:
        print("ERROR: Set DATABASE_URL environment variable")
        sys.exit(1)

    rows = load_csv(OVERSIKT_CSV)
    print(f"Loaded {len(rows)} rader fra: {OVERSIKT_CSV}")
    if DRY_RUN:
        print("*** DRY RUN — ingen data endres ***\n")
    await enrich(rows)


if __name__ == "__main__":
    asyncio.run(main())
