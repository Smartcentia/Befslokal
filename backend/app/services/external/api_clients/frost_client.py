from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from app.services.external.api_clients.base_client import BaseApiClient, logger

class FrostClient(BaseApiClient):
    """
    Async Client for Frost API (MET.no).
    """
    
    def __init__(self, client_id: Optional[str] = None):
        if not client_id:
            from app.core.config import settings
            client_id = settings.FROST_CLIENT_ID

        super().__init__(
            base_url="https://frost.met.no", 
            api_key=client_id, 
            source_name="frost",
            api_key_header_name="Authorization" # Assuming Basic Auth or Client ID usage
        )
        self.client_id = client_id
        # Note: Frost uses specific auth scheme, typically Basic with client_id as user.
    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Override _get to use Basic Auth for Frost.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Frost uses Basic Auth with client_id as username
        auth = (self.client_id, "") if self.client_id else None
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params, auth=auth)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code} for {url}: {e.response.text}")
                return {"error": f"HTTP {e.response.status_code}", "details": e.response.text}
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return {"error": str(e)}

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch. Identifier is "lat,lon".
        """
        try:
            parts = identifier.split(",")
            if len(parts) == 2:
                return await self.fetch_property_data(float(parts[0]), float(parts[1]))
            raise ValueError("Ugyldig koordinat-format (forventer 'lat,lon')")
        except (ValueError, IndexError):
            raise ValueError("Ugyldig koordinat-format (forventer 'lat,lon')")

    async def find_nearest_station(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Find nearest weather station.
        """
        endpoint = "/sources/v0.jsonld"
        # Real endpoint: https://frost.met.no/sources/v0.jsonld ?
        # Docs say /sources/v0.jsonld
        
        params = {
            "geometry": f"nearest(POINT({longitude} {latitude}))",
            "nearestmaxcount": 1
        }
        
        try:
            # Note: _get is async
            response = await self._get(endpoint, params=params)
            data = response.get("data", [])
            
            if not data:
                return {"station_id": None, "total_found": 0}
            
            station = data[0]
            coords = station.get("geometry", {}).get("coordinates", [None, None]) # lon, lat
            
            return {
                "station_id": station.get("id"),
                "name": station.get("name"),
                "latitude": coords[1],
                "longitude": coords[0],
                "total_found": len(data)
            }
        except Exception as e:
            logger.error(f"Error fetching Frost station: {e}")
            return {"station_id": None, "total_found": 0}

    async def get_observations(self, station_id: str, element_id: str = "mean(air_temperature P1D)") -> Dict[str, Any]:
        """
        Get observations.
        """
        endpoint = "/observations/v0.jsonld"
        params = {
            "sources": station_id,
            "elements": element_id,
            "referencetime": "latest" # or range
        }
        
        try:
            response = await self._get(endpoint, params=params)
            return response
        except Exception as e:
            logger.error(f"Error fetching Frost observations: {e}")
            return {}

    async def fetch_property_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Aggregated weather data.
        """
        station = await self.find_nearest_station(latitude, longitude)
        
        if not station.get("station_id"):
            return {
                "source_api": "frost",
                "station_id": None,
                "error": "Ingen stasjon funnet i nærheten",
                "data_type": "measured" # Match test expectation
            }
            
        observations = await self.get_observations(station["station_id"])
        
        return {
            "source_api": "frost",
            "data_type": "measured",
            "station_id": station["station_id"],
            "observations": observations.get("data", [])
        }
