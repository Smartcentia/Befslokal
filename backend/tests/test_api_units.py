import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_unit(client: TestClient, sample_property, sample_unit):
    """Test opprettelse av enhet."""
    # Opprett eiendom først
    property_response = await client.post("/api/v1/properties", json=sample_property)
    assert property_response.status_code == 201
    property_id = property_response.json()["property_id"]
    
    # Update sample_unit with actual property_id
    sample_unit["property_id"] = property_id
    
    # Opprett enhet
    response = await client.post("/api/v1/units", json=sample_unit)
    assert response.status_code == 201
    data = response.json()
    assert data["purpose"] == sample_unit["purpose"]


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_units_by_property(client: TestClient, sample_property, sample_unit):
    """Test henting av enheter for eiendom."""
    # Opprett eiendom
    property_response = await client.post("/api/v1/properties", json=sample_property)
    property_id = property_response.json()["property_id"]
    
    # Opprett enhet
    sample_unit["property_id"] = property_id
    unit_response = await client.post("/api/v1/units", json=sample_unit)
    assert unit_response.status_code == 201
    
    # Hent enheter for eiendom
    response = await client.get(f"/api/v1/units?property_id={property_id}")
    assert response.status_code == 200
    assert len(response.json()) > 0












