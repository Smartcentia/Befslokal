"""Tester for NGU client."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.api_clients.ngu_client import NGUClient


@pytest.fixture
def ngu_client():
    """NGU client instance."""
    return NGUClient(api_key="test_key")


@pytest.mark.asyncio
async def test_fetch_bedrock_data(ngu_client):
    """Test henting av berggrunnsdata."""
    result = await ngu_client.fetch_bedrock_data(59.91, 10.75)
    
    assert result["source_api"] == "ngu"
    assert result["data_type"] == "bedrock"
    assert result["latitude"] == 59.91
    assert result["longitude"] == 10.75


@pytest.mark.asyncio
async def test_fetch_soil_data(ngu_client):
    """Test henting av løsmassedata."""
    result = await ngu_client.fetch_soil_data(59.91, 10.75)
    
    assert result["source_api"] == "ngu"
    assert result["data_type"] == "soil"


@pytest.mark.asyncio
async def test_fetch_geohazard_data(ngu_client):
    """Test henting av geofaredata."""
    result = await ngu_client.fetch_geohazard_data(59.91, 10.75)
    
    assert result["source_api"] == "ngu"
    assert result["data_type"] == "geohazard"


@pytest.mark.asyncio
async def test_fetch_comprehensive_geological_data(ngu_client):
    """Test henting av komplett geologisk data."""
    with patch.object(ngu_client, "fetch_bedrock_data", new_callable=AsyncMock) as mock_bedrock, \
         patch.object(ngu_client, "fetch_soil_data", new_callable=AsyncMock) as mock_soil, \
         patch.object(ngu_client, "fetch_groundwater_data", new_callable=AsyncMock) as mock_gw, \
         patch.object(ngu_client, "fetch_geohazard_data", new_callable=AsyncMock) as mock_hazard:
        
        mock_bedrock.return_value = {"data_type": "bedrock"}
        mock_soil.return_value = {"data_type": "soil"}
        mock_gw.return_value = {"data_type": "groundwater"}
        mock_hazard.return_value = {"data_type": "geohazard"}
        
        result = await ngu_client.fetch_comprehensive_geological_data(59.91, 10.75)
        
        assert result["source_api"] == "ngu"
        assert "bedrock" in result
        assert "soil" in result
        assert "groundwater" in result
        assert "geohazard" in result




