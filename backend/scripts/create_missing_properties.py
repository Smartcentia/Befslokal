#!/usr/bin/env python3
"""
Create stub property records for GL cost centers that exist in Agresso
but have no property in the properties table.
Links their GL transactions to the new property records.

Run: railway run bash -c 'cd backend && PYTHONPATH=. python3 scripts/create_missing_properties.py [--dry-run]'

Etter kjøring: PYTHONPATH=. python3 scripts/audit_koststed_property_gl.py
"""
import asyncio, sys, uuid, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.db.session import SessionLocal
from sqlalchemy import text

# These institutions are in the leie CSV but not in properties table
# dim1_kode → (name, expected_region)
MISSING_INSTITUTIONS = [
    # (dim1_kode, name_override or None)
    ("333801", None),   # Svenner           - 8.5M
    ("533201", None),   # Husafjellheimen ungdomsheim - 5.9M
    ("344101", None),   # Nyhuset           - 3.3M
    ("321404", None),   # Harebakken        - 2.5M
    ("541100", None),   # Trøndelag behandlingssenter for ungdom - 1.8M
    ("344100", None),   # Skjerven rusbehandling ungdom - 0.8M
    ("543501", None),   # MST Sunnmøre      - 0.6M
    ("623800", None),   # Indre finnmark FV - 0.6M
    ("225201", None),   # Familievernkontoret Nedre Romerike - 0.2M
    ("225301", None),   # Familievernkontoret Øvre Romerike  - 0.3M
]

# (dim1_kode, navn, gateadresse, postnr, poststed) — typisk fra leiekart / intern avklaring
MISSING_WITH_LOCATION: list[tuple[str, str, str, str, str]] = [
    ("624200", "Tromsø familievernkontor (FV)", "Kaigata 4", "9008", "Tromsø"),
    ("641800", "MST Tromsø", "Kaigata 4", "9008", "Tromsø"),
    ("614600", "Inntak nord", "Storgata 70", "9008", "Tromsø"),
    ("615900", "FHT RN – fosterhjemstjenesten", "Sørøygata 10", "9600", "Hammerfest"),
    ("635703", "Enhet for spesialiserte fosterhjem Nord", "Nordstrandveien 41", "8006", "Bodø"),
    ("520801", "Familievernkontoret Innherred", "Jernbanegata 11–13", "7600", "Levanger"),
    ("531002", "Karienborg ungdomsheim", "Jernbanegata 11–13", "7600", "Levanger"),
    ("540901", "MST Trøndelag Nord", "Jernbanegata 11–13", "7600", "Levanger"),
]

# Normalize region codes from GL to standard format
REGION_MAP = {
    "Region Midt-Norge": "Midt-Norge",
    "Region Nord": "Nord",
    "Region Sør": "Sør",
    "Region Vest": "Vest",
    "Region Øst": "Øst",
    "Bufdir": "Bufdir",
}


async def _property_exists(db, dim1: str) -> bool:
    r = await db.execute(
        text(
            """
            SELECT 1 FROM properties
            WHERE unit_id_erp = :uid OR koststed_kode = :uid
            LIMIT 1
            """
        ),
        {"uid": dim1},
    )
    return r.fetchone() is not None


async def _gl_meta(db, dim1: str):
    r2 = await db.execute(
        text("""
                SELECT dim1_navn, region,
                       SUM(belop) FILTER(WHERE ar=2025 AND belop>0) as gl25,
                       SUM(belop) FILTER(WHERE belop>0) as gl_any
                FROM gl_transactions
                WHERE dim1_kode = :uid
                GROUP BY dim1_navn, region
                ORDER BY gl25 DESC NULLS LAST
                LIMIT 1
            """),
        {"uid": dim1},
    )
    return r2.fetchone()


async def _distinct_gl_property_ids(db, dim1: str) -> list[str]:
    r = await db.execute(
        text(
            """
            SELECT DISTINCT property_id::text FROM gl_transactions
            WHERE dim1_kode = :uid AND property_id IS NOT NULL
            """
        ),
        {"uid": dim1},
    )
    return [row[0] for row in r.fetchall() if row[0]]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only-location-list",
        action="store_true",
        help="Bare prosesser MISSING_WITH_LOCATION (ikke MISSING_INSTITUTIONS)",
    )
    args = parser.parse_args()

    async with SessionLocal() as db:
        created: list[tuple] = []

        work_items: list[tuple] = []
        if not args.only_location_list:
            for dim1, name_override in MISSING_INSTITUTIONS:
                work_items.append(
                    (dim1, name_override, None, None, None)
                )
        for dim1, name, addr, post, city in MISSING_WITH_LOCATION:
            work_items.append((dim1, name, addr, post, city))

        seen_dim1: set[str] = set()
        for dim1, name_override, addr, post, city in work_items:
            if dim1 in seen_dim1:
                continue
            seen_dim1.add(dim1)

            if await _property_exists(db, dim1):
                print(f"  SKIP {dim1}: finnes allerede (unit_id_erp eller koststed_kode)")
                continue

            gl_pids = await _distinct_gl_property_ids(db, dim1)
            if len(gl_pids) == 1:
                print(
                    f"  SKIP {dim1}: GL allerede koblet til property_id={gl_pids[0]} "
                    f"(oppdater adresse/koststed på eksisterende rad ved behov)"
                )
                continue
            if len(gl_pids) > 1:
                print(
                    f"  SKIP {dim1}: GL har flere ulike property_id — kjør "
                    f"audit_koststed_property_gl.py og rydd først: {gl_pids[:5]}"
                )
                continue

            row = await _gl_meta(db, dim1)
            if not row:
                print(f"  SKIP {dim1}: ingen GL-data")
                continue

            if addr and post and city:
                display_name = name_override
            else:
                display_name = name_override or str(row[0] or dim1)
            region_raw = str(row[1] or "")
            region = REGION_MAP.get(region_raw, region_raw)
            gl25 = float(row[2] or 0)

            new_pid = str(uuid.uuid4())
            extra = ""
            if addr:
                extra = f"  addr={addr}, {post} {city}"
            print(
                f"  CREATE {dim1}: '{display_name}'  region={region}  gl25={gl25/1e6:.2f}M  pid={new_pid}{extra}"
            )
            created.append((dim1, display_name, region, new_pid, gl25, addr, post, city))

        if not args.dry_run and created:
            for dim1, name, region, new_pid, gl25, addr, post, city in created:
                if addr and post:
                    await db.execute(
                        text("""
                    INSERT INTO properties (
                        property_id, name, address, postal_code, city,
                        unit_id_erp, koststed_kode, region, unit_type_derived
                    )
                    VALUES (
                        CAST(:pid AS uuid), :name, :addr, :post, :city,
                        :uid, :uid, :region, 'Barnevernsinstitusjon'
                    )
                    """),
                        {
                            "pid": new_pid,
                            "name": name,
                            "addr": addr,
                            "post": post,
                            "city": city,
                            "uid": dim1,
                            "region": region,
                        },
                    )
                else:
                    await db.execute(
                        text("""
                    INSERT INTO properties (
                        property_id, name, unit_id_erp, koststed_kode, region, unit_type_derived
                    )
                    VALUES (
                        CAST(:pid AS uuid), :name, :uid, :uid, :region, 'Barnevernsinstitusjon'
                    )
                    """),
                        {
                            "pid": new_pid,
                            "name": name,
                            "uid": dim1,
                            "region": region,
                        },
                    )

                r = await db.execute(
                    text("""
                    UPDATE gl_transactions
                    SET property_id = CAST(:pid AS uuid)
                    WHERE dim1_kode = :uid AND property_id IS NULL
                    RETURNING transaction_id
                    """),
                    {"pid": new_pid, "uid": dim1},
                )
                n = len(r.fetchall())
                print(f"    Linked {n} GL rows to {name}")

            await db.commit()
            print(f"\nCreated {len(created)} new properties and linked GL data.")
        elif args.dry_run:
            print(f"\n[--dry-run] Would create {len(created)} new properties.")

asyncio.run(main())
