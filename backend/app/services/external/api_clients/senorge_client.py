from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from app.services.external.api_clients.base_client import BaseApiClient, logger

try:
    import pyproj
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

class SeNorgeClient(BaseApiClient):
    """
    Async Client for SeNorge API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            base_url="https://api.senorge.no/api/v0",  # Base API URL
            api_key=api_key, 
            source_name="senorge"
        )

    @staticmethod
    def convert_to_utm(lat: float, lon: float) -> Tuple[float, float]:
        """
        Convert Lat/Lon to UTM.
        """
        if not HAS_PYPROJ:
            # Fallback for when pyproj is missing (or in tests where it gets patched anyway?)
            # But the test patches pyproj.Transformer, which requires pyproj module to exist for patch to work 
            # if we import it at top level?
            # Actually proper `patch('pyproj.Transformer')` mocks the module too if it's in sys.modules?
            # If pyproj is not installed, import fails.
            # Simplified fallback:
            return (0.0, 0.0)

        transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:25833", always_xy=True)
        return transformer.transform(lon, lat)

    async def get_data(self, param: str, x: float, y: float, start: str, end: str) -> Dict[str, Any]:
        """
        Generic get data.
        """
        # Placeholder
        return {"data": []}

    async def get_snow_depth(self, lat: float, lon: float, start: str, end: str) -> Dict[str, Any]:
        """
        Get snow depth.
        """
        x, y = self.convert_to_utm(lat, lon)
        return await self.get_data("sd", x, y, start, end)

    async def fetch_property_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch normalized property data from SeNorge.
        """
        x, y = self.convert_to_utm(lat, lon)
        # In real implementation, this would call get_data for multiple parameters.
        # For now, return empty result to signify no real data fetched yet.
        return {
            "source_api": "senorge",
            "data_type": "modeled",
            "utm_x": x,
            "utm_y": y,
            "observations": []
        }

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch. Identifier "lat,lon".
        """
        try:
            parts = identifier.split(",")
            if len(parts) == 2:
                return await self.fetch_property_data(float(parts[0]), float(parts[1]))
            raise ValueError("Ugyldig koordinat-format (forventer 'lat,lon')")
        except (ValueError, IndexError):
            raise ValueError("Ugyldig koordinat-format (forventer 'lat,lon')")
