"""Test data factories for generating test objects."""
from uuid import uuid4
from datetime import datetime, timedelta
import random


def create_property_data(overrides=None):
    """Factory for creating property test data."""
    default = {
        "property_id": str(uuid4()),
        "address": f"Testveien {random.randint(1, 100)}",
        "postal_code": f"{random.randint(1000, 9999):04d}",
        "city": random.choice(["Oslo", "Bergen", "Trondheim", "Stavanger"]),
        "latitude": round(random.uniform(59.0, 61.0), 4),
        "longitude": round(random.uniform(10.0, 12.0), 4),
    }
    if overrides:
        default.update(overrides)
    return default


def create_unit_data(property_id=None, overrides=None):
    """Factory for creating unit test data."""
    default = {
        "unit_id": str(uuid4()),
        "property_id": property_id or str(uuid4()),
        "purpose": random.choice(["Leilighet", "Kontor", "Lager", "Butikk"]),
        "area_sqm": round(random.uniform(20.0, 200.0), 2),
        "floor": random.randint(0, 10),
    }
    if overrides:
        default.update(overrides)
    return default


def create_party_data(overrides=None):
    """Factory for creating party test data."""
    default = {
        "party_id": str(uuid4()),
        "name": f"Test Firma {random.randint(1, 1000)} AS",
        "orgnr": f"{random.randint(100000000, 999999999)}",
        "contact_email": f"test{random.randint(1, 1000)}@example.com",
        "contact_phone": f"+47{random.randint(10000000, 99999999)}",
    }
    if overrides:
        default.update(overrides)
    return default


def create_contract_data(unit_id=None, party_id=None, overrides=None):
    """Factory for creating contract test data."""
    start_date = datetime.now() - timedelta(days=random.randint(0, 365))
    end_date = start_date + timedelta(days=random.randint(365, 730))
    
    default = {
        "contract_id": str(uuid4()),
        "unit_id": unit_id or str(uuid4()),
        "party_id": party_id or str(uuid4()),
        "status": random.choice(["active", "expired", "pending"]),
        "periods": [
            {
                "start_date": start_date.isoformat() + "Z",
                "end_date": end_date.isoformat() + "Z",
                "index_name": random.choice(["KPI", "KPI-JAE", "Lønnsoppgjør"]),
            }
        ],
        "amount": {
            "currency": "NOK",
            "amount_per_year": round(random.uniform(50000.0, 500000.0), 2),
        },
        "signed_at": (start_date - timedelta(days=30)).isoformat() + "Z",
    }
    if overrides:
        default.update(overrides)
    return default


def create_text_content_data(overrides=None):
    """Factory for creating text content test data."""
    default = {
        "text_id": str(uuid4()),
        "source_type": random.choice(["file", "api", "json"]),
        "content": f"Dette er en test tekst {random.randint(1, 1000)}. Den inneholder viktig informasjon som skal indekseres.",
        "metadata": {"filename": f"test_{random.randint(1, 1000)}.txt", "test": True},
        "contract_id": str(uuid4()),
        "unit_id": None,
        "property_id": None,
    }
    if overrides:
        default.update(overrides)
    return default


def create_external_api_data(overrides=None):
    """Factory for creating external API data test data."""
    default = {
        "api_data_id": str(uuid4()),
        "source_api": random.choice(["bronnoysund", "nve", "kartverket"]),
        "entity_type": random.choice(["property", "unit", "contract", "party"]),
        "entity_id": str(uuid4()),
        "data": {
            "test": "data",
            "timestamp": datetime.now().isoformat(),
        },
        "fetched_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=1),
    }
    if overrides:
        default.update(overrides)
    return default


def create_csv_row_data(overrides=None):
    """Factory for creating CSV row test data."""
    default = {
        "address": f"Gate {random.randint(1, 100)}",
        "postal_code": f"{random.randint(1000, 9999):04d}",
        "city": random.choice(["Oslo", "Bergen", "Trondheim"]),
        "purpose": random.choice(["Kontor", "Lager", "Butikk"]),
        "area_sqm": str(random.randint(20, 200)),
        "party_name": f"Firma {random.randint(1, 1000)} AS",
        "orgnr": str(random.randint(100000000, 999999999)),
        "status": random.choice(["active", "pending"]),
    }
    if overrides:
        default.update(overrides)
    return default

