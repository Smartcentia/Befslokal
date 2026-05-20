"""Integration tests for external API integrations."""
import pytest
from unittest.mock import patch, AsyncMock
from tests.helpers import MockExternalAPIs

# Common headers for authenticated requests
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

@pytest.mark.integration
@pytest.mark.external
class TestExternalAPIIntegrations:
    """Tests for external API integrations."""
    
    @pytest.mark.asyncio
    async def test_lookup_company_by_orgnr(self, client):
        """Test looking up company information by organization number."""
        orgnr = "123456789"
        mock_response = {"name": "Test AS", "org_number": orgnr}
        
        # Patching the Service (not Client directly cause it's wrapped in brreg_service)
        with patch("app.services.brreg_service.BrregService.get_company_details",
                   return_value=mock_response): # Not async method in BrregService
            
            response = await client.get(f"/api/external/brreg/{orgnr}", headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert data["org_number"] == orgnr
            assert "name" in data
            
    @pytest.mark.asyncio
    async def test_geocode_address(self, client):
        """Test geocoding an address."""
        mock_response = MockExternalAPIs.kartverket_response() 
        # Mocking Client method geocode_address (async)
        with patch("app.services.api_clients.kartverket_client.KartverketClient.geocode_address",
                   new_callable=AsyncMock, return_value=mock_response):
            
            params = {"address": "Karl Johans gate 1, Oslo"}
            response = await client.get("/api/external/kartverket/geocode", params=params, headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert "adresser" in data
            assert len(data["adresser"]) > 0

    @pytest.mark.asyncio
    async def test_reverse_geocode(self, client):
        """Test reverse geocoding."""
        mock_response = MockExternalAPIs.kartverket_response()
        
        with patch("app.services.api_clients.kartverket_client.KartverketClient.fetch_property_data",
                   new_callable=AsyncMock, return_value=mock_response):
            
            params = {"lat": 59.9139, "lon": 10.7522}
            response = await client.get("/api/external/kartverket/reverse", params=params, headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert "adresser" in data

    @pytest.mark.asyncio
    async def test_nve_flood_zones(self, client):
        """Test getting flood zones."""
        mock_response = {"latitude": 59.9139, "longitude": 10.7522, "forecast": {}, "stations": []}
        
        with patch("app.services.api_clients.nve_client.NVEClient.fetch_flood_risk",
                   new_callable=AsyncMock, return_value=mock_response):
            
            params = {"lat": 59.9139, "lon": 10.7522}
            response = await client.get("/api/external/nve/flood-zones", params=params, headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert "forecast" in data

    @pytest.mark.asyncio
    async def test_nve_energy(self, client):
        """Test getting energy infrastructure (nearby stations)."""
        mock_response = [{"name": "Station 1", "distance_km": 1.5}]
        
        with patch("app.services.api_clients.nve_client.NVEClient.fetch_nearby_stations",
                   new_callable=AsyncMock, return_value=mock_response):
            
            params = {"lat": 59.9139, "lon": 10.7522, "radius": 2000}
            response = await client.get("/api/external/nve/energy", params=params, headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert "energiinfrastruktur" in data
            assert len(data["energiinfrastruktur"]) == 1

    @pytest.mark.asyncio
    async def test_frost_observations(self, client):
        """Test getting weather observations."""
        mock_response = MockExternalAPIs.frost_response()
        
        with patch("app.services.api_clients.frost_client.FrostClient.get_observations",
                   new_callable=AsyncMock, return_value=mock_response):
            
            params = {
                "lat": 59.9139,
                "lon": 10.7522,
                "element": "heat"
            }
            response = await client.get("/api/external/frost/observations", params=params, headers=AUTH_HEADERS)
            assert response.status_code == 200
            
            data = response.json()
            assert "data" in data
