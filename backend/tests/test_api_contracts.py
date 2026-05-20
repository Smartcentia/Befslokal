"""Tester for contracts API."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_contract(
    client: TestClient,
    sample_property,
    sample_unit,
    sample_party,
    sample_contract,
):
    """Test opprettelse av kontrakt."""
    # Opprett avhengige entiteter
    property_response = await client.post("/api/v1/properties", json=sample_property)
    assert property_response.status_code == 201
    property_id = property_response.json()["property_id"]
    
    sample_unit["property_id"] = property_id
    unit_response = await client.post("/api/v1/units", json=sample_unit)
    assert unit_response.status_code == 201
    unit_id = unit_response.json()["unit_id"]
    
    party_response = await client.post("/api/v1/parties", json=sample_party)
    assert party_response.status_code == 201
    party_id = party_response.json()["party_id"]
    
    # Oppdater kontrakt med riktige IDer
    sample_contract["unit_id"] = unit_id
    sample_contract["party_id"] = party_id
    
    # Opprett kontrakt
    response = await client.post("/api/v1/contracts", json=sample_contract)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == sample_contract["status"]


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_contracts_by_status(
    client: TestClient,
    sample_property,
    sample_unit,
    sample_party,
    sample_contract,
):
    """Test henting av kontrakter filtrert på status."""
    # Opprett avhengige entiteter og kontrakt
    property_response = await client.post("/api/v1/properties", json=sample_property)
    sample_unit["property_id"] = property_response.json()["property_id"]
    
    unit_response = await client.post("/api/v1/units", json=sample_unit)
    
    party_response = await client.post("/api/v1/parties", json=sample_party)
    
    sample_contract["unit_id"] = unit_response.json()["unit_id"]
    sample_contract["party_id"] = party_response.json()["party_id"]
    sample_contract["status"] = "active"
    
    # Opprett kontrakt
    await client.post("/api/v1/contracts", json=sample_contract)
    
    # Hent aktive kontrakter
    response = await client.get("/api/v1/contracts?status=active")
    assert response.status_code == 200
    contracts = response.json()
    assert len(contracts) > 0
    assert all(c["status"] == "active" for c in contracts)












