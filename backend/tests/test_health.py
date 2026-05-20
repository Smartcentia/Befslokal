"""Tester for health check endepunkter."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "knowme-backend", "db": "connected"}


# @pytest.mark.api
# @pytest.mark.regression
# @pytest.mark.asyncio
# async def test_readiness_check_without_db(client: TestClient):
#     """Test readiness check når database ikke er tilgjengelig."""
#     # Readiness check kan feile hvis DB ikke er tilgjengelig
#     # Dette er ok for nå siden vi ikke har faktisk DB i test-miljøet
#     response = client.get("/ready")
#     # Kan returnere 200 eller 503 avhengig av DB-tilgjengelighet
#     # assert response.status_code in [200, 503]
#     # assert "status" in response.json()

