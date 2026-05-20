"""Tester for CSV importer service."""
import pytest
from pathlib import Path
import csv
import tempfile

from app.services.csv_importer import (
    parse_csv_file,
    import_csv_to_db
)


@pytest.mark.unit
@pytest.mark.importer
def test_parse_csv_file(tmp_path):
    """Test CSV parsing."""
    test_file = tmp_path / "test.csv"
    
    # Opprett test CSV
    with open(test_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "city"])
        writer.writeheader()
        writer.writerow({"name": "Eiendom 1", "address": "Gate 1", "city": "Oslo"})
        writer.writerow({"name": "Eiendom 2", "address": "Gate 2", "city": "Bergen"})
    
    rows = parse_csv_file(test_file.read_bytes())
    
    assert len(rows) == 2
    assert rows[0]["name"] == "Eiendom 1"
    assert rows[0]["address"] == "Gate 1"
    assert rows[1]["city"] == "Bergen"


@pytest.mark.unit
@pytest.mark.importer
def test_parse_csv_file_semicolon(tmp_path):
    """Test CSV med semikolon-delimiter."""
    test_file = tmp_path / "test.csv"
    
    with open(test_file, "w", encoding="utf-8", newline="") as f:
        f.write("name;address;city\n")
        f.write("Test;Gate 1;Oslo\n")
    
    rows = parse_csv_file(test_file.read_bytes(), delimiter=";")
    
    assert len(rows) == 1
    assert rows[0]["name"] == "Test"
