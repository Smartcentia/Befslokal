"""Tester for Frost API Client."""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from app.services.api_clients.frost_client import FrostClient


class TestFrostClient:
    """Tester for FrostClient."""
    
    def test_init_with_client_id(self):
        """Test at klient initialiseres med client_id."""
        client = FrostClient(client_id="test_client_id")
        assert client.client_id == "test_client_id"
        assert client.base_url == "https://frost.met.no"
    
    def test_init_without_client_id(self):
        """Test at klient initialiseres uten client_id."""
        client = FrostClient()
        assert client.client_id is None
    
    @pytest.mark.asyncio
    async def test_find_nearest_station_success(self):
        """Test at find_nearest_station returnerer stasjon."""
        client = FrostClient(client_id="test_id")
        
        mock_response = {
            "data": [{
                "id": "SN18700",
                "name": "Geilo",
                "geometry": {
                    "coordinates": [8.2, 60.1]
                }
            }]
        }
        
        with patch.object(client, "_get", return_value=mock_response):
            result = await client.find_nearest_station(60.1, 8.2)
            
            assert result["station_id"] == "SN18700"
            assert result["name"] == "Geilo"
            assert result["latitude"] == 60.1
            assert result["longitude"] == 8.2
    
    @pytest.mark.asyncio
    async def test_find_nearest_station_no_stations(self):
        """Test at find_nearest_station håndterer ingen stasjoner."""
        client = FrostClient(client_id="test_id")
        
        with patch.object(client, "_get", return_value={"data": []}):
            result = await client.find_nearest_station(60.1, 8.2)
            
            assert result["station_id"] is None
            assert result["total_found"] == 0
    
    @pytest.mark.asyncio
    async def test_fetch_property_data_success(self):
        """Test at fetch_property_data returnerer normalisert data."""
        client = FrostClient(client_id="test_id")
        
        mock_station = {
            "station_id": "SN18700",
            "name": "Geilo",
            "latitude": 60.1,
            "longitude": 8.2
        }
        
        mock_obs = {
            "data": [{
                "referenceTime": "2024-01-01T12:00:00Z",
                "observations": [{
                    "elementId": "air_temperature",
                    "value": 5.0,
                    "unit": "celsius"
                }]
            }]
        }
        
        with patch.object(client, 'find_nearest_station', return_value=mock_station), \
             patch.object(client, 'get_observations', return_value=mock_obs):
            
            result = await client.fetch_property_data(60.1, 8.2)
            
            assert result["source_api"] == "frost"
            assert result["data_type"] == "measured"
            assert result["station_id"] == "SN18700"
            assert len(result["observations"]) > 0
    
    @pytest.mark.asyncio
    async def test_fetch_property_data_no_station(self):
        """Test at fetch_property_data håndterer ingen stasjon."""
        client = FrostClient(client_id="test_id")
        
        # Calling find_nearest_station returns dict, we patch it
        with patch.object(client, 'find_nearest_station', return_value={"station_id": None}):
            result = await client.fetch_property_data(60.1, 8.2)
            
            assert result["source_api"] == "frost"
            assert result["station_id"] is None
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_fetch_data_with_coordinates(self):
        """Test at fetch_data parser koordinater korrekt."""
        client = FrostClient(client_id="test_id")
        
        with patch.object(client, 'fetch_property_data') as mock_fetch:
            mock_fetch.return_value = {"source_api": "frost"}
            result = await client.fetch_data("60.1,8.2")
            
            mock_fetch.assert_called_once_with(60.1, 8.2)
            assert result["source_api"] == "frost"
    
    @pytest.mark.asyncio
    async def test_fetch_data_invalid_format(self):
        """Test at fetch_data håndterer ugyldig koordinat-format."""
        client = FrostClient(client_id="test_id")
        
        with pytest.raises(ValueError, match="Ugyldig koordinat-format"):
            await client.fetch_data("invalid")





