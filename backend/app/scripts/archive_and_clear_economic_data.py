"""
Arkiverer alle økonomidata til CSV-filer, deretter sletter dem fra databasen.

Kjøres fra backend-mappen:
    python -m app.scripts.archive_and_clear_economic_data

Arkivfiler lagres i: app/scripts/archive/YYYYMMDD_HHMMSS/
"""
import asyncio
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy import text, select

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from app.services.data_management import DataManagementService

ARCHIVE_BASE = Path(__file__).parent / "archive"


async def archive_and_clear():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = ARCHIVE_BASE / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Arkivmappe: {archive_dir}")
    print()

    async with SessionLocal() as db:

        # --- 1. gl_transactions ---
        rows = (await db.execute(text("SELECT * FROM gl_transactions"))).mappings().all()
        _write_csv(archive_dir / "gl_transactions.csv", rows)
        print(f"✅ gl_transactions     : {len(rows)} rader")

        # --- 2. budget ---
        rows = (await db.execute(text("SELECT * FROM budget"))).mappings().all()
        _write_csv(archive_dir / "budget.csv", rows)
        print(f"✅ budget              : {len(rows)} rader")

        # --- 3. text_content ---
        rows = (await db.execute(text("SELECT * FROM text_content"))).mappings().all()
        _write_csv(archive_dir / "text_content.csv", rows)
        print(f"✅ text_content        : {len(rows)} rader")

        # --- 4. socioeconomic_data ---
        rows = (await db.execute(text("SELECT * FROM socioeconomic_data"))).mappings().all()
        _write_csv(archive_dir / "socioeconomic_data.csv", rows)
        print(f"✅ socioeconomic_data  : {len(rows)} rader")

        # --- 5. properties.external_data['financials'] ---
        rows = (await db.execute(
            text("SELECT property_id, name, external_data->'financials' AS financials "
                 "FROM properties WHERE external_data ? 'financials'")
        )).mappings().all()
        _write_json(archive_dir / "properties_financials.json", rows)
        print(f"✅ properties financials: {len(rows)} eiendommer")

        # --- 6. contracts cost fields ---
        rows = (await db.execute(
            text("""SELECT contract_id, caretaker_cost, cleaning_cost, parking_cost,
                          card_reader_cost,
                          external_data->'common_costs' AS common_costs,
                          external_data->'internal_maintenance_cost' AS internal_maintenance_cost,
                          external_data->'municipal_fees' AS municipal_fees,
                          external_data->'energy_cost' AS energy_cost,
                          external_data->'heating_cost' AS heating_cost
                   FROM contracts
                   WHERE caretaker_cost IS NOT NULL
                      OR cleaning_cost IS NOT NULL
                      OR parking_cost IS NOT NULL
                      OR card_reader_cost IS NOT NULL
                      OR external_data IS NOT NULL""")
        )).mappings().all()
        _write_json(archive_dir / "contracts_costs.json", rows)
        print(f"✅ contracts costs     : {len(rows)} kontrakter")

        # --- 7. forecast_cache ---
        try:
            rows = (await db.execute(text("SELECT * FROM forecast_cache"))).mappings().all()
            _write_json(archive_dir / "forecast_cache.json", rows)
            print(f"✅ forecast_cache      : {len(rows)} rader")
        except Exception:
            print("⚠️  forecast_cache: tabell finnes ikke, hopper over")

        # --- 8. maintenance_records med kostnad ---
        try:
            rows = (await db.execute(
                text("SELECT * FROM maintenance_records WHERE cost IS NOT NULL")
            )).mappings().all()
            _write_csv(archive_dir / "maintenance_records_costs.csv", rows)
            print(f"✅ maintenance costs   : {len(rows)} rader")
        except Exception:
            print("⚠️  maintenance_records: ingen kostnadsdata")

        print()
        print("🗑️  Starter sletting...")
        result = await DataManagementService.clear_all_economic_data(db)

        if result["status"] == "success":
            print(f"✅ {result['message']}")
            print()
            print(f"📦 Arkiv lagret i: {archive_dir}")
        else:
            print(f"❌ Sletting feilet: {result['message']}")


def _write_csv(path: Path, rows: list) -> None:
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow({k: v for k, v in row.items()})


def _write_json(path: Path, rows: list) -> None:
    data = [dict(r) for r in rows]
    # Konverter ikke-serialiserbare typer
    for item in data:
        for k, v in item.items():
            if hasattr(v, "isoformat"):
                item[k] = v.isoformat()
            elif hasattr(v, "__str__") and not isinstance(v, (str, int, float, bool, type(None))):
                item[k] = str(v)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(archive_and_clear())
