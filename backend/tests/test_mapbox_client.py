import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.external.mapbox_client import MapboxClient


class FakeMapboxClient:
    """Fake httpx.AsyncClient for testing."""

    def __init__(self, response_data):
        self._response = MagicMock(status_code=200, json=lambda: response_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, *args, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_mapbox_client_success():
    """Test MapboxClient get_nearby_places success (Search Box API format)."""
    client = MapboxClient()
    client.access_token = "test_token"

    mock_response = {
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [10.75, 59.91]},
                "properties": {
                    "name": "Coffee Shop",
                    "full_address": "Gate 1, Oslo",
                },
            }
        ]
    }

    def make_fake_client(*args, **kwargs):
        return FakeMapboxClient(mock_response)

    with patch("app.services.external.mapbox_client.httpx.AsyncClient", side_effect=make_fake_client):
        results = await client.get_nearby_places(59.91, 10.75, service_type="cafe")

        assert len(results) == 1
        assert results[0]["name"] == "Coffee Shop"
        assert results[0]["vicinity"] == "Gate 1, Oslo"


@pytest.mark.asyncio
async def test_mapbox_client_no_token():
    """Test MapboxClient without token."""
    client = MapboxClient()
    client.access_token = None

    results = await client.get_nearby_places(59.91, 10.75)
    assert results == []


@pytest.mark.asyncio
async def test_mapbox_client_api_error():
    """Test MapboxClient API error handling."""
    client = MapboxClient()
    client.access_token = "test_token"

    class Fake401Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, *args, **kwargs):
            return MagicMock(status_code=401)

    with patch("app.services.external.mapbox_client.httpx.AsyncClient", return_value=Fake401Client()):
        results = await client.get_nearby_places(59.91, 10.75)
        assert results == []
