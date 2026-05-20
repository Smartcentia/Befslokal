"""
Eksporter alle eiendommer til CSV (navn, adresse, region m.m.).

Kjør fra backend med DATABASE_URL i .env:
  cd backend && python scripts/export_properties_csv.py

Valgfri utdatafil:
  cd backend && python scripts/export_properties_csv.py -o /tmp/eiendommer.csv

Standardfil: eiendommer_liste.csv i repo-roten (én mappe over backend/).
"""
import argparse
import asyncio
import csv
import os
import sys

if __name__ == "__main__":
    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.core.config import settings


COLUMNS = [
    "property_id",
    "name",
    "address",
    "postal_code",
    "city",
    "region",
    "lokalisering_id",
    "municipality",
    "usage",
]


async def run(out_path: str) -> int:
    if not settings.DATABASE_URL:
        print("DATABASE_URL er ikke satt.", file=sys.stderr)
        return 1

    async with SessionLocal() as session:
        result = await session.execute(
            select(Property).order_by(
                Property.region.nulls_last(),
                Property.city.nulls_last(),
                Property.name.nulls_last(),
                Property.address.nulls_last(),
            )
        )
        rows = result.scalars().all()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for p in rows:
            w.writerow(
                {
                    "property_id": str(p.property_id) if p.property_id else "",
                    "name": (p.name or "").replace("\n", " ").strip(),
                    "address": (p.address or "").replace("\n", " ").strip(),
                    "postal_code": p.postal_code or "",
                    "city": (p.city or "").strip(),
                    "region": (p.region or "").strip(),
                    "lokalisering_id": p.lokalisering_id or "",
                    "municipality": (p.municipality or "").strip(),
                    "usage": (p.usage or "").strip(),
                }
            )

    print(f"Skrev {len(rows)} rader til {out_path}")
    return 0


def main() -> None:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(backend_dir)
    default_out = os.path.join(root_dir, "eiendommer_liste.csv")

    parser = argparse.ArgumentParser(description="Eksporter eiendommer til CSV.")
    parser.add_argument(
        "-o",
        "--output",
        default=default_out,
        help=f"Output CSV (default: {default_out})",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.output)))


if __name__ == "__main__":
    main()
