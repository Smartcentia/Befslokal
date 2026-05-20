import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_party(client: TestClient, sample_party):
    """Test opprettelse av part."""
    response = await client.post("/api/v1/parties", json=sample_party)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_party["name"]
    assert data["orgnr"] == sample_party["orgnr"]


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_create_party_duplicate_orgnr(client: TestClient, sample_party):
    """Test opprettelse av part med duplisert orgnr."""
    # Opprett første part
    response = await client.post("/api/v1/parties", json=sample_party)
    assert response.status_code == 201
    
    # Prøv å opprette ny part med samme orgnr
    response = await client.post("/api/v1/parties", json=sample_party)
    assert response.status_code == 400












