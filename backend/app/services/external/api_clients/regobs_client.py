
import httpx
from typing import Dict, Any, List, Optional
from app.services.external.api_clients.base_client import BaseApiClient, logger

class RegObsClient(BaseApiClient):
    """
    Client for RegObs API (https://test-api.regobs.no/v5)
    """
    def __init__(self):
        super().__init__(
            base_url="https://test-api.regobs.no/v5",
            source_name="regobs"
        )

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch required by BaseApiClient.
        Identifier could be "lat,lon" for this client.
        """
        parts = identifier.split(",")
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0]), float(parts[1])
                return await self.fetch_observations(lat, lon, radius=5000)
            except ValueError:
                pass
        return {}

    async def fetch_observations(self, latitude: float, longitude: float, radius: int = 5000) -> Dict[str, Any]:
        """
        Fetch observations within a radius using the generic Search endpoint (POST).
        """
        url = f"{self.base_url}/Search"
        
        payload = {
            "Radius": {
                "Position": {
                    "Latitude": latitude,
                    "Longitude": longitude
                },
                "Radius": radius
            },
            "NumberOfRecords": 10,
            "SelectedRegistrationTypes": [] # Empty = all kinds
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # data is usually a list of records
                return {
                    "count": len(data),
                    "observations": data,
                    "status": "OK"
                }
            except Exception as e:
                logger.error(f"Error fetching RegObs data: {e}")
                return {"error": str(e)}
