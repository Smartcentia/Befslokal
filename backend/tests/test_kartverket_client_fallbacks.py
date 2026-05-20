import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.external.api_clients.kartverket_client import KartverketClient


@pytest.mark.asyncio
async def test_search_address_expands_compact_street_abbreviations():
    client = KartverketClient()

    empty_response = MagicMock()
    empty_response.raise_for_status.return_value = None
    empty_response.json.return_value = {"adresser": []}

    hit_response = MagicMock()
    hit_response.raise_for_status.return_value = None
    hit_response.json.return_value = {
        "adresser": [{"representasjonspunkt": {"lat": 68.800761, "lon": 16.54095}}]
    }

    side_effect = [empty_response, empty_response, empty_response, hit_response]
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=side_effect)) as mock_get:
        result = await client.search_address("Håkonsgt 4, Harstad")

    assert result == {"latitude": 68.800761, "longitude": 16.54095}
    attempted_queries = [call.kwargs["params"].get("sok") for call in mock_get.await_args_list]
    assert attempted_queries[-1] == "Håkons gate 4"


@pytest.mark.asyncio
async def test_search_address_strips_postal_and_city_noise():
    client = KartverketClient()

    empty_response = MagicMock()
    empty_response.raise_for_status.return_value = None
    empty_response.json.return_value = {"adresser": []}

    hit_response = MagicMock()
    hit_response.raise_for_status.return_value = None
    hit_response.json.return_value = {
        "adresser": [{"representasjonspunkt": {"lat": 59.950269, "lon": 11.048732}}]
    }

    side_effect = [empty_response, empty_response, empty_response, hit_response]
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=side_effect)) as mock_get:
        result = await client.search_address("Torget 6, 2000 Lillestrøm")

    assert result == {"latitude": 59.950269, "longitude": 11.048732}
    attempted_queries = [call.kwargs["params"].get("sok") for call in mock_get.await_args_list]
    assert attempted_queries[-1] == "Torget 6"
