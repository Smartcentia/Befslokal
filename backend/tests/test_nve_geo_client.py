
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.api_clients.nve_geo_client import NVEGeoClient

@pytest.fixture
def mock_arcgis_hit():
    """Mock response for a hit in the zone."""
    return {
        "features": [
            {
                "attributes": {
                    "OBJECTID": 123,
                    "navn": "Test Zone"
                }
            }
        ]
    }

@pytest.fixture
def mock_arcgis_miss():
    """Mock response for no hit."""
    return {
        "features": []
    }

@pytest.mark.asyncio
async def test_check_flood_zone_hit(mock_arcgis_hit):
    """Test checking flood zone with a hit."""
    client = NVEGeoClient()
    
    with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_arcgis_hit
        
        result = await client.check_flood_zone(59.9, 10.7)
        
        assert result["hit"] is True
        assert result["message"] == "Inside Flomaktsomhet zone"
        assert result["details"]["navn"] == "Test Zone"
        
        # Verify endpoint
        args, kwargs = mock_get.call_args
        assert "FlomAktsomhet/MapServer/0/query" in args[0]

@pytest.mark.asyncio
async def test_check_quick_clay_zone_miss(mock_arcgis_miss):
    """Test checking quick clay zone with no hit."""
    client = NVEGeoClient()
    
    with patch.object(client, "_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_arcgis_miss
        
        result = await client.check_quick_clay_zone(59.9, 10.7)
        
        assert result["hit"] is False
        assert result["message"] == "Outside Kvikkleire zone"

@pytest.mark.asyncio
async def test_fetch_data_integration():
    """Test the fetch_data wrapper calls individual checks."""
    client = NVEGeoClient()
    
    # Patch the individual check methods
    with patch.object(client, "check_flood_zone", new_callable=AsyncMock) as mock_flood, \
         patch.object(client, "check_quick_clay_zone", new_callable=AsyncMock) as mock_clay:
        
        mock_flood.return_value = {"hit": True}
        mock_clay.return_value = {"hit": False}
        
        result = await client.fetch_data("59.9,10.7")
        
        assert result["flood_zone"]["hit"] is True
        assert result["quick_clay_zone"]["hit"] is False
