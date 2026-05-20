"""Tester for properties API."""
import pytest
from fastapi.testclient import TestClient
from uuid import UUID


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_property(client: TestClient):
    """Test opprettelse av eiendom."""
    property_data = {
        "address": "Testveien 1",
        "postal_code": "0001",
        "city": "Oslo",
        "latitude": 59.9139,
        "longitude": 10.7522,
    }
    
    response = await client.post("/api/v1/properties", json=property_data)
    assert response.status_code == 201
    data = response.json()
    assert data["address"] == property_data["address"]
    assert UUID(data["property_id"])


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_properties(client: TestClient, sample_property):
    """Test henting av eiendommer."""
    # Opprett eiendom først
    response = await client.post("/api/v1/properties", json=sample_property)
    assert response.status_code == 201
    
    # Hent alle eiendommer
    response = await client.get("/api/v1/properties")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_property_by_id(client: TestClient, sample_property):
    """Test henting av eiendom ved ID."""
    # Opprett eiendom
    response = await client.post("/api/v1/properties", json=sample_property)
    assert response.status_code == 201
    property_id = response.json()["property_id"]
    
    # Hent eiendom
    response = await client.get(f"/api/v1/properties/{property_id}")
    assert response.status_code == 200
    assert response.json()["property_id"] == property_id


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_get_property_not_found(client: TestClient):
    """Test henting av ikke-eksisterende eiendom."""
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    response = await client.get(f"/api/v1/properties/{fake_id}")
    assert response.status_code == 404

