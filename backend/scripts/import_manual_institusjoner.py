"""Importer det manuale institusjonssettet fra `data/manual_institusjoner.json`."""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import tempfile
from pathlib import Path

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from import_institusjoner_csv import run_import

HEADER = [
    "Region",
    "Målgruppe",
    "Enhetsnr.",
    "Enhetens/Institusjonens navn",
    "Avdelingens koststed",
    "Navn på avdeling",
    "Antall kvalitetssikrede institusjonsplasser avd. pr. 01.01",
    "Antall budsjetterte institusjonsplasser avd. per 01.01",
]


def _write_csv_from_json(json_path: Path, csv_path: Path) -> None:
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    with csv_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(HEADER)
        for row in data:
            writer.writerow([
                row.get("region"),
                row.get("affiliation"),
                row.get("lokalisering_id"),
                row.get("name"),
                row.get("department_code"),
                row.get("unit_name"),
                row.get("approved_places"),
                row.get("budgeted_places"),
            ])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importer det manuelle institusjonssettet til BEFS."
    )
    parser.add_argument(
        "--json",
        default="data/manual_institusjoner.json",
        help="Path to the JSON dataset (relative to repo root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kun kjør parser og lag CSV, ikke skriv til DB",
    )
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        parser.error(f"JSON-fil ikke funnet: {json_path}")

    with tempfile.NamedTemporaryFile(
        prefix="manual_institusjoner_",
        suffix=".csv",
        dir=json_path.parent,
        delete=False,
        mode="w",
        encoding="utf-8",
        newline="",
    ) as tmp:
        tmp_path = Path(tmp.name)
        _write_csv_from_json(json_path, tmp_path)

    try:
        if args.dry_run:
            print(f"Kun CSV generert: {tmp_path}")
            return

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_import(str(tmp_path)))
    finally:
        tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
