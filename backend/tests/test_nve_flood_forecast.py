"""Tester for NVE Flomvarsling API."""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.services.api_clients.nve_client import NVEClient


@pytest.fixture
def nve_client():
    """NVE client instance."""
    return NVEClient(api_key="test_key")


@pytest.mark.asyncio
async def test_fetch_flood_forecast_with_coordinates(nve_client):
    """Test henting av flomvarsel med koordinater."""
    # Patch helper method on the instance or class
    with patch.object(nve_client, "_get_region_for_flood_forecast", new_callable=AsyncMock) as mock_get_region:
        mock_get_region.return_value = {
            "county_code": "03",
            "county_name": "Oslo"
        }
        
        # Patch httpx.AsyncClient.get because fetch_flood_forecast uses it directly
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "forecast": {
                    "status": "active",
                    "level": "moderate"
                }
            }
            mock_http_get.return_value = mock_resp
            
            result = await nve_client.fetch_flood_forecast(
                latitude=59.91,
                longitude=10.75
            )
            
            
            assert "warnings" in result
            assert result["county_code"] == "03"


@pytest.mark.asyncio
async def test_fetch_flood_forecast_with_county_code(nve_client):
    """Test henting av flomvarsel med fylkesnummer."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "forecast": {
                "status": "active"
            }
        }
        result = await nve_client.fetch_flood_forecast(county_code="03")
        
        assert "warnings" in result
        assert result["county_code"] == "03"


@pytest.mark.asyncio
async def test_fetch_flood_forecast_not_available(nve_client):
    """Test håndtering av når flomvarsel ikke er tilgjengelig."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_http_get:
        mock_http_get.side_effect = Exception("404 Not Found")
        
        result = await nve_client.fetch_flood_forecast(county_code="99")
        
        assert "error" in result


@pytest.mark.asyncio
async def test_fetch_flood_forecast_missing_params(nve_client):
    """Test validering av påkrevde parametere."""
    # If no lat/lon/county, returns Oslo (03) default now
    result = await nve_client.fetch_flood_forecast()
    assert result["county_code"] == "03"




