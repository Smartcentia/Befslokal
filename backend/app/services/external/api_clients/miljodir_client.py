from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.external.api_clients.base_client import BaseApiClient, logger
from app.core.config import settings
import httpx

class MiljodirClient(BaseApiClient):
    """
    Async Client for Miljødirektoratet (Vannmiljø) API.
    Base URL: https://vannmiljoapi.miljodirektoratet.no
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Use MILJODIR_API_KEY from settings if not provided
        key = api_key or settings.MILJODIR_API_KEY
        super().__init__(
            base_url="https://vannmiljoapi.miljodirektoratet.no", 
            api_key=key, 
            source_name="miljodir"
        )

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch (Required by BaseApiClient).
        """
        return {}

    def _get_headers(self) -> Dict[str, str]:
        """
        Override headers to support the specific 'api_key' header or other auth mechanisms if needed.
        Swagger UI showed 'api_key' in header.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BEFS-Eiendomsforvaltning/1.0"
        }
        if self.api_key:
            headers["api_key"] = self.api_key
            # Also try standard Authorization just in case, or X-API-Key
            # But browser research said 'api_key' input field in Swagger header.
        return headers

    async def fetch_water_features(self, lat: float, lon: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
        """
        Fetch water locations/bodies near coordinates using a bounding box.
        Endpoint: POST /api/Public/GetWaterLocations
        """
        # Create a bounding box from lat/lon and radius
        # Rough approximation: 1 deg lat ~ 111km, 1 deg lon ~ 111km * cos(lat)
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * 0.6) # approx for Norway south
        
        payload = {
            "BoundingBox": {
                "XMin": lon - delta_lon,
                "XMax": lon + delta_lon,
                "YMin": lat - delta_lat,
                "YMax": lat + delta_lat
            },
            "ReturnAll": False
        }
        
        url = f"{self.base_url}/api/Public/GetWaterLocations"
        
        try:
            # We strictly use the new _get_headers for the API key
            headers = self._get_headers()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                
            if resp.status_code == 200:
                data = resp.json()
                # Determine what to return. The API returns a structure with rows.
                return data.get("Rows", []) if isinstance(data, dict) else data
            else:
                logger.warning(f"MiljodirClient: GetWaterLocations failed {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            logger.exception(f"MiljodirClient: Exception fetching water locations: {e}")
            return []

    async def fetch_species_registrations(self, lat: float, lon: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
        """
        Fetch species registrations near coordinates.
        Endpoint: POST /api/Public/GetRegistrations
        """
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * 0.6)
        
        payload = {
            "BoundingBox": {
                "XMin": lon - delta_lon,
                "XMax": lon + delta_lon,
                "YMin": lat - delta_lat,
                "YMax": lat + delta_lat
            },
            # We can filter by "MediumID" or "ParameterID" if we knew them.
            # For now, get all registrations in the area.
            "ReturnAll": False 
        }
        
        url = f"{self.base_url}/api/Public/GetRegistrations"
        
        try:
            headers = self._get_headers()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                
            if resp.status_code == 200:
                return resp.json().get("Rows", [])
            else:
                logger.warning(f"MiljodirClient: GetRegistrations failed {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            logger.exception(f"MiljodirClient: Exception fetching species: {e}")
            return []

    async def fetch_medium_list(self) -> List[Dict[str, Any]]:
        """
        Fetch list of media (MediumID lookup).
        """
        url = f"{self.base_url}/api/Public/GetMediumList"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception:
            return []

    async def fetch_parameter_list(self) -> List[Dict[str, Any]]:
        """
        Fetch list of parameters (ParameterID lookup).
        """
        url = f"{self.base_url}/api/Public/GetParameterList"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception:
            return []

    async def fetch_unit_list(self) -> List[Dict[str, Any]]:
        """
        Fetch list of units (Enhet lookup).
        """
        url = f"{self.base_url}/api/Public/GetUnitList"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception:
            return []

    async def fetch_air_quality(self, lat: float, lon: float, radius_km: float = 2.0) -> List[Dict[str, Any]]:
        """
        Fetch air quality data from NILU API.
        """
        url = f"https://api.nilu.no/aq/utd/{lat}/{lon}/{radius_km}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return []
        except Exception as e:
            logger.error(f"MiljodirClient: Air Quality fetch failed: {e}")
            return []

    async def fetch_contaminated_sites(self, lat: float, lon: float, radius_km: float = 0.5) -> List[Dict[str, Any]]:
        """
        Fetch contaminated sites from Miljødirektoratet ArcGIS MapServer.
        """
        base_url = "https://kart.miljodirektoratet.no/arcgis/rest/services/grunnforurensning2/MapServer"
        # Layer 0 is points, Layer 1 is polygons. We'll query both or simplify to Layer 0 for risk proxy.
        return await self._query_arcgis(base_url, 0, lat, lon, radius_km)

    async def fetch_noise_data(self, lat: float, lon: float, radius_km: float = 0.5) -> List[Dict[str, Any]]:
        """
        Fetch noise data from Miljødirektoratet ArcGIS MapServer.
        Uses strategic road noise (veg) as a primary source.
        """
        base_url = "https://kart.miljodirektoratet.no/arcgis/rest/services/stoy/stoykart_strategisk_veg/MapServer"
        # Layer mapping varies, but layer 0 is usually Lden (Day-Evening-Night).
        return await self._query_arcgis(base_url, 0, lat, lon, radius_km)

    async def _query_arcgis(self, base_url: str, layer_id: int, lat: float, lon: float, radius_km: float) -> List[Dict[str, Any]]:
        """
        Helper to query ArcGIS REST API with spatial filtering.
        """
        # Approx bounding box
        delta = radius_km / 111.0
        geometry = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
        
        params = {
            "geometry": geometry,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json"
        }
        
        url = f"{base_url}/{layer_id}/query"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    return [f.get("attributes", {}) for f in features]
                return []
        except Exception as e:
            logger.error(f"ArcGIS query failed for {url}: {e}")
            return []


# End of MiljodirClient

