"""Tester for Varsom client."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.api_clients.varsom_client import VarsomClient


@pytest.fixture
def varsom_client():
    """Varsom client instance."""
    return VarsomClient(api_key="test_key")


@pytest.mark.asyncio
async def test_fetch_avalanche_warnings(varsom_client):
    """Test henting av snøskredvarsler."""
    result = await varsom_client.fetch_avalanche_warnings(59.91, 10.75, 50)
    
    assert result["source_api"] == "varsom"
    assert result["warning_type"] == "avalanche"
    assert result["latitude"] == 59.91
    assert result["longitude"] == 10.75
    # Stub returns 0
    assert result["danger_level"] == 0


@pytest.mark.asyncio
async def test_fetch_flood_warnings(varsom_client):
    """Test henting av flomvarsler."""
    result = await varsom_client.fetch_flood_warnings(59.91, 10.75, 50)
    
    assert result["source_api"] == "varsom"
    assert result["warning_type"] == "flood"
    # Stub returns 0
    assert result["danger_level"] == 0


@pytest.mark.asyncio
async def test_fetch_landslide_warnings(varsom_client):
    """Test henting av jordskredvarsler."""
    result = await varsom_client.fetch_landslide_warnings(59.91, 10.75, 50)
    
    assert result["source_api"] == "varsom"
    assert result["warning_type"] == "landslide"


@pytest.mark.asyncio
async def test_fetch_all_active_warnings(varsom_client):
    """Test henting av alle aktive varsler."""
    # We mock the internal calls to verify aggregation logic
    with patch.object(varsom_client, "fetch_avalanche_warnings", new_callable=AsyncMock) as mock_avalanche, \
         patch.object(varsom_client, "fetch_flood_warnings", new_callable=AsyncMock) as mock_flood, \
         patch.object(varsom_client, "fetch_landslide_warnings", new_callable=AsyncMock) as mock_landslide:
        
        mock_avalanche.return_value = {"warning_type": "avalanche"}
        mock_flood.return_value = {"warning_type": "flood"}
        mock_landslide.return_value = {"warning_type": "landslide"}
        
        result = await varsom_client.fetch_all_active_warnings(59.91, 10.75, 50)
        
        assert result["source_api"] == "varsom"
        assert "avalanche" in result
        assert "flood" in result
        assert "landslide" in result




