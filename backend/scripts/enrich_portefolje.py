"""
enrich_portefolje.py — Beriker BEFS-properties fra Eiendomsportefølje CSV

STRATEGI:
  • Aldri overskriv eksisterende (ikke-NULL) verdier
  • Alle UPDATE-setninger sjekker NULL i Python FØR de sender til DB
  • Aldri berør: region, address, postal_code, city, municipality,
    start_date, end_date, contract_name, status, party_id, amount, belop

CSV-kilde: "Eiendomsportefølje per okt 2025 - ekstra(Sheet1).csv"
Én header-rad (linje 0), datarader fra linje 1.

Felter som berikes:
  properties.lok_omrade          ← Lok: Område
  properties.lok_distrikt        ← Lok: Distrikt
  properties.lokasjon_type       ← Type lokasjon
  properties.fylke                ← Fylke
  properties.total_area          ← Areal (kvm)
  properties.leased_area_kvm     ← Areal inkl fellesareal i leiekontrakt
  properties.malgruppe           ← Målgruppe
  properties.gnr                 ← Matrikkel Gnr
  properties.bnr                 ← Matrikkel Bnr
  properties.municipality_code   ← Matrikkel Knr
  properties.org_number          ← org nr utleier
  properties.elements_id         ← Elements saksnummer
  properties.utleier_kategori    ← Utleier kategori (1/2)
  properties.contract_rent_nok   ← KPI-justert kontraktsleie til okt 2025
  properties.contract_maint_nok  ← Indre vedlikehold
  properties.contract_common_nok ← Felleskostnader
  properties.contract_user_ops_nok ← Brukeravhengige driftskostander
  properties.extension_terms     ← forlengelse & vilkår
  properties.price_adj_clause    ← leieregulering

Kjøring:
  DATABASE_URL="postgresql+asyncpg://..." \\
  PORTEFOLJE_CSV="/Users/frank/Downloads/Eiendomsportefølje per okt 2025 - ekstra(Sheet1).csv" \\
  python scripts/enrich_portefolje.py [--dry-run]
"""

import asyncio
import os
import re
import sys

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
PORTEFOLJE_CSV = os.environ.get(
    "PORTEFOLJE_CSV",
    "/Users/frank/Downloads/Eiendomsportefølje per okt 2025 - ekstra(Sheet1).csv",
)
DRY_RUN = "--dry-run" in sys.argv


# ── Parsing helpers ────────────────────────────────────────────────────────────

def extract_lok_code(s: str) -> str | None:
    m = re.match(r"^(\d+)", s.strip())
    return m.group(1) if m else None


def parse_nok(s: str) -> float | None:
    """'1 234 567' eller '1234567' → 1234567.0.
    Strip spaces FØR konvertering: '850 000' → '850000' → 850000.0 (IKKE 850.0 via regex).
    """
    s = s.replace("\xa0", "").replace(" ", "").replace(" ", "").strip()
    if not s or s in ("0", "-", "*tomt"):
        return None
    s = s.replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def parse_float(s: str) -> float | None:
    """Areal: '424' → 424.0"""
    s = s.replace("\xa0", "").replace(" ", "").strip()
    if not s or s in ("0", "-"):
        return None
    try:
        v = float(s.replace(",", "."))
        return v if v > 0 else None
    except ValueError:
        return None


def parse_int(s: str) -> int | None:
    s = s.strip()
    if not s:
        return None
    m = re.match(r"^(\d+)", s)
    if m:
        v = int(m.group(1))
        return v if v > 0 else None
    return None


def clean_text(s: str, max_len: int = 300) -> str | None:
    s = s.strip()
    if not s or s.lower() in ("ikke oppgitt", "-", "", "mangler kontrakt", "mangler kontrakt "):
        return None
    return s[:max_len]


# ── CSV loader ─────────────────────────────────────────────────────────────────

def load_csv(path: str) -> list[dict]:
    with open(path, encoding="latin-1") as f:
        lines = f.readlines()
    # Én header-rad (linje 0) — strip trailing spaces fra headernavn for robusthet
    headers = [h.strip() for h in lines[0].strip().split(";")]
    rows = []
    for line in lines[1:]:
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
        result = await session.execute(sa.text("""
            SELECT
                property_id::text,
                lokalisering_id,
                lok_omrade,
                lok_distrikt,
                lokasjon_type,
                fylke,
                total_area,
                leased_area_kvm,
                malgruppe,
                gnr,
                bnr,
                municipality_code,
                org_number,
                elements_id,
                utleier_kategori,
                contract_rent_nok,
                contract_maint_nok,
                contract_common_nok,
                contract_user_ops_nok,
                extension_terms,
                price_adj_clause
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

            # ── lok_omrade ────────────────────────────────────────────────────
            lok_omr = clean_text(row.get("Lok: Område", ""), 50)
            if lok_omr and prop["lok_omrade"] is None:
                updates["lok_omrade"] = lok_omr

            # ── lok_distrikt ──────────────────────────────────────────────────
            lok_dist = clean_text(row.get("Lok: Distrikt", ""), 50)
            if lok_dist and prop["lok_distrikt"] is None:
                updates["lok_distrikt"] = lok_dist

            # ── lokasjon_type ─────────────────────────────────────────────────
            lok_type = clean_text(row.get("Type lokasjon", ""), 50)
            if lok_type and prop["lokasjon_type"] is None:
                updates["lokasjon_type"] = lok_type

            # ── fylke ─────────────────────────────────────────────────────────
            fylke = clean_text(row.get("Fylke", ""), 50)
            if fylke and prop["fylke"] is None:
                updates["fylke"] = fylke

            # ── total_area ────────────────────────────────────────────────────
            areal = parse_float(row.get("Areal", ""))
            if areal is not None and prop["total_area"] is None:
                updates["total_area"] = areal

            # ── leased_area_kvm ───────────────────────────────────────────────
            leid_areal = parse_float(row.get("Areal inkl fellesareal i leiekontrakt (kvm)", ""))
            if leid_areal is not None and prop["leased_area_kvm"] is None:
                updates["leased_area_kvm"] = leid_areal

            # ── malgruppe ─────────────────────────────────────────────────────
            malgruppe = clean_text(row.get("Målgruppe", ""), 100)
            if malgruppe and prop["malgruppe"] is None:
                updates["malgruppe"] = malgruppe

            # ── gnr ───────────────────────────────────────────────────────────
            gnr = parse_int(row.get("Matrikkel Gnr", ""))
            if gnr is not None and prop["gnr"] is None:
                updates["gnr"] = gnr

            # ── bnr ───────────────────────────────────────────────────────────
            bnr = parse_int(row.get("Matrikkel Bnr", ""))
            if bnr is not None and prop["bnr"] is None:
                updates["bnr"] = bnr

            # ── municipality_code ─────────────────────────────────────────────
            knr = clean_text(row.get("Matrikkel Knr", ""), 10)
            if knr and prop["municipality_code"] is None:
                updates["municipality_code"] = knr

            # ── org_number ────────────────────────────────────────────────────
            org_nr = clean_text(row.get("org nr utleier", ""), 20)
            if org_nr and prop["org_number"] is None:
                updates["org_number"] = org_nr

            # ── elements_id ───────────────────────────────────────────────────
            elements = clean_text(row.get("Elements", ""), 200)
            if elements and prop["elements_id"] is None:
                updates["elements_id"] = elements

            # ── utleier_kategori ──────────────────────────────────────────────
            utl_kat = parse_int(row.get("Utleier kategori", ""))
            if utl_kat in (1, 2) and prop["utleier_kategori"] is None:
                updates["utleier_kategori"] = utl_kat

            # ── contract_rent_nok (KPI-justert til okt 2025) ─────────────────
            leie = parse_nok(row.get("KPI-justert kontraktsleie til okt 2025", ""))
            if leie is not None and prop["contract_rent_nok"] is None:
                updates["contract_rent_nok"] = leie

            # ── contract_maint_nok ────────────────────────────────────────────
            vedl = parse_nok(row.get("Indre vedlikehold", ""))
            if vedl is not None and prop["contract_maint_nok"] is None:
                updates["contract_maint_nok"] = vedl

            # ── contract_common_nok ───────────────────────────────────────────
            felles = parse_nok(row.get("Felleskostnader per år (ved kontraktsinngåelse)", ""))
            if felles is not None and prop["contract_common_nok"] is None:
                updates["contract_common_nok"] = felles

            # ── contract_user_ops_nok ─────────────────────────────────────────
            drift = parse_nok(row.get("Brukeravhengige driftskostander - Første driftsår", ""))
            if drift is not None and prop["contract_user_ops_nok"] is None:
                updates["contract_user_ops_nok"] = drift

            # ── extension_terms ───────────────────────────────────────────────
            ext = clean_text(row.get("forlengelse &vilkår", ""), 500)
            if ext and prop["extension_terms"] is None:
                updates["extension_terms"] = ext

            # ── price_adj_clause ──────────────────────────────────────────────
            kpi = clean_text(row.get("leieregulering", ""), 300)
            if kpi and prop["price_adj_clause"] is None:
                updates["price_adj_clause"] = kpi

            if not updates:
                no_change += 1
                continue

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

    rows = load_csv(PORTEFOLJE_CSV)
    print(f"Loaded {len(rows)} rader fra: {PORTEFOLJE_CSV}")
    if DRY_RUN:
        print("*** DRY RUN — ingen data endres ***\n")
    await enrich(rows)


if __name__ == "__main__":
    asyncio.run(main())
