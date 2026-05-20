from typing import Dict, Any, Optional, List
import math
import httpx
from app.services.external.api_clients.base_client import BaseApiClient, logger

class NVEClient(BaseApiClient):
    """
    Async Client for NVE API (HydAPI & Flood Forecast).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # HydAPI base URL
        super().__init__(
            base_url="https://hydapi.nve.no/api/v1", 
            api_key=api_key, 
            source_name="nve",
            api_key_header_name="X-API-Key"
        )
        self.flood_api_url = "https://api01.nve.no/hydrology/forecast/flood/v1.0.10/api"
        self.landslide_api_url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.6/api"
        self.gts_api_url = "https://gts.nve.no/api"

    async def fetch_data(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """
        Generic fetch. Identifier is typically "lat,lon".
        """
        parts = identifier.split(",")
        if len(parts) == 2:
            return await self.fetch_flood_risk(float(parts[0]), float(parts[1]))
        return {}
        
    async def fetch_landslide_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Fetch landslide forecast (Jordskredvarsling).
        Endpoint similar to flood: /Warning/Region/{...} or /Warning/County/...
        We will try to map lat/lon to region/county, otherwise default to a known region (e.g. Oslo - 03).
        """
        # For simplicity in this iteration, we default to county 03 (Oslo) like Flood.
        county_code = "03"
        url = f"{self.landslide_api_url}/Warning/County/{county_code}"
        
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return {"warnings": data, "county_code": county_code, "status": "OK"}
            except Exception as e:
                logger.error(f"Error fetching landslide forecast: {e}")
                return {"error": str(e)}

    async def fetch_nearby_stations(self, latitude: float, longitude: float, max_distance_km: float = 10.0) -> List[Dict[str, Any]]:
        """
        Fetch nearby hydrological stations.
        """
        try:
            params = {
                "Lat": str(latitude),
                "Lon": str(longitude),
                "Radius": str(int(max_distance_km * 1000)),  # meters
                "Active": "OnlyActive",
            }
            # HydAPI still needs key, handled by base client headers if set
            response = await self._get("/Stations", params=params)
            stations = response.get("data", [])
            
            # Filter and sort manually to be safe or if API radius fails
            valid_stations = []
            for st in stations:
                st_lat = st.get("latitude")
                st_lon = st.get("longitude")
                if st_lat is not None and st_lon is not None:
                    dist = self._calculate_distance_km(latitude, longitude, st_lat, st_lon)
                    st["distance_km"] = round(dist, 2)
                    if dist <= max_distance_km:
                        valid_stations.append(st)
            
            valid_stations.sort(key=lambda x: x["distance_km"])
            return valid_stations[:5]  # Top 5
        except Exception as e:
            logger.error(f"Error fetching NVE stations: {e}")
            return []

    async def fetch_flood_forecast(
        self,
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None,
        county_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch flood forecast. 
        Endpoint: /Warning/County/{county_code}
        """
        
        if not county_code and (latitude is not None and longitude is not None):
            # Try to resolve county from coords
            # region_info = await self._get_region_for_flood_forecast(latitude, longitude)
            # if region_info:
            #     county_code = region_info.get("county_code")
            pass

        if not county_code:
            # Default to Oslo (03) if unknown for now, or skip
            # return {"status": "skipped", "reason": "Missing county_code"}
            county_code = "03"

        # Correct endpoint structure based on v1.0.10 docs
        url = f"{self.flood_api_url}/Warning/County/{county_code}"
        
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # API returns a list of warnings
                return {"warnings": data, "county_code": county_code}
            except Exception as e:
                logger.error(f"Error fetching flood forecast: {e}")
                return {"error": str(e)}

    async def fetch_grid_time_series(self, x: int, y: int, start_date: str, end_date: str, theme: str = "rr") -> Dict[str, Any]:
        """
        Fetch Grid Time Series data (GTS).
        Coordinates must be UTM Zone 33N.
        Theme 'rr' = Precipitation (Døgnnedbør).
        Dates format: YYYY-MM-DD
        Endpoint: /GridTimeSeries/{x}/{y}/{start_date}/{end_date}/{theme}.json
        """
        # Proper path construction as discovered: https://gts.nve.no/api/GridTimeSeries/x/y/start/end/theme.json
        endpoint = f"/GridTimeSeries/{x}/{y}/{start_date}/{end_date}/{theme}.json"
        
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # self.gts_api_url is "https://gts.nve.no/api"
                # Avoid double slash
                base = self.gts_api_url.rstrip("/")
                url = f"{base}{endpoint}"
                
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Error fetching GTS data {url}: {e}")
                return {"error": str(e)}

    async def _get_region_for_flood_forecast(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Helper to map coordinates to flood forecast region/county.
        To be implemented in future phase.
        """
        return None

    async def fetch_flood_risk(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Aggregated flood risk data for a property.
        """
        stations = await self.fetch_nearby_stations(latitude, longitude)
        
        # We try to fetch forecast for Oslo (03) as default behavior if mapping missing
        forecast = await self.fetch_flood_forecast(latitude, longitude, county_code="03")
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "stations_nearby": len(stations),
            "stations": stations,
            "forecast": forecast
        }

    @staticmethod
    def _calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    async def fetch_property_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Wrapper to fetch all relevant property data from NVE.
        """
        risk_data = await self.fetch_flood_risk(latitude, longitude)
        return {
            "source_api": "nve",
            **risk_data
        }
