"""
Mapbox API Client
Brukes for geocoding og nærliggende POI-søk.
- Geocoding API v5: adresse → koordinater
- Search Box API: POI-søk på kategori
"""
import logging
import math
from urllib.parse import quote
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Norsk/engelsk søkeord for POI-typer (Search Box /forward)
# Utvidet for barnevernsinstitusjoner: helse, utdanning, fritid, offentlige tjenester
POI_QUERY_MAPPING = {
    # Helse & omsorg
    "hospital": "sykehus",
    "pharmacy": "apotek",
    "doctor": "lege",
    "dentist": "tannlege",
    "psychologist": "psykolog",
    "emergency_room": "legevakt",
    "health_station": "helsestasjon",
    # Sikkerhet
    "police": "politi",
    "fire_station": "brannstasjon",
    # Utdanning
    "school": "skole",
    "kindergarten": "barnehage",
    "high_school": "videregående skole",
    # Dagligvarer
    "supermarket": "matbutikk",
    # Transport
    "transit_station": "kollektivtransport",
    "bus_station": "bussholdeplass",
    "train_station": "togstasjon",
    "subway_station": "t-bane",
    # Fritid & aktivitet
    "movie_theater": "kino",
    "park": "park",
    "gym": "treningssenter",
    "museum": "museum",
    "library": "bibliotek",
    "swimming_pool": "svømmehall",
    "playground": "lekeplass",
    "sports_facility": "idrettsplass",
    "youth_center": "ungdomsklubb",
    "leisure_center": "fritidsklubb",
    # Offentlige tjenester
    "nav_office": "NAV",
    "social_services": "sosialkontor",
    # Andre
    "church": "kirke",
    "cafe": "kafé",
}


class MapboxClient:
    """Klient for Mapbox Geocoding og Search Box API."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or getattr(settings, "MAPBOX_ACCESS_TOKEN", None)

    async def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Konverter adresse til koordinater via Mapbox Geocoding API v5.
        Returns: {"latitude": float, "longitude": float} eller None
        """
        if not self.access_token:
            logger.warning("Mapbox token mangler for geocoding")
            return None

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
        params = {
            "access_token": self.access_token,
            "limit": 1,
            "country": "no",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                if resp.status_code != 200:
                    logger.error(f"Mapbox geocoding error: {resp.status_code}")
                    return None

                data = resp.json()
                features = data.get("features", [])
                if not features:
                    return None

                coords = features[0].get("center") or features[0].get("geometry", {}).get("coordinates")
                if not coords or len(coords) < 2:
                    return None

                return {"longitude": coords[0], "latitude": coords[1]}
        except Exception as e:
            logger.error(f"Mapbox geocoding exception: {e}")
            return None

    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        service_type: Optional[str] = None,
        radius: int = 5000,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Hent nærliggende POIs via Mapbox Search Box API.
        Bruker /category for kjente typer, ellers /forward med types=poi.

        Returns: Liste med {"name", "vicinity"/"address", "latitude", "longitude", "distance_meters"}
        """
        if not self.access_token:
            logger.warning("Mapbox token mangler for POI-søk")
            return []

        query = POI_QUERY_MAPPING.get(service_type, service_type or "point_of_interest")
        proximity = f"{lng},{lat}"

        try:
            url = "https://api.mapbox.com/search/searchbox/v1/forward"
            params = {
                "q": query,
                "access_token": self.access_token,
                "proximity": proximity,
                "limit": min(limit, 10),
                "types": "poi",
                "country": "no",
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                if resp.status_code != 200:
                    logger.error(f"Mapbox POI error: {resp.status_code} - {resp.text[:200]}")
                    return []

                data = resp.json()
                features = data.get("features", [])

                if not features and service_type:
                    logger.debug(
                        "Mapbox POI empty for type=%s query=%s proximity=%s",
                        service_type, query, proximity
                    )

            results = []
            for f in features:
                props = f.get("properties", {})
                geom = f.get("geometry", {})
                coords = geom.get("coordinates") or props.get("coordinates")
                elem_lat, elem_lng = None, None
                if isinstance(coords, dict):
                    elem_lat = coords.get("latitude") or coords.get("lat")
                    elem_lng = coords.get("longitude") or coords.get("lon") or coords.get("lng")
                elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
                    # GeoJSON Point: [longitude, latitude]
                    elem_lng, elem_lat = coords[0], coords[1]
                if elem_lat is None or elem_lng is None:
                    continue

                name = props.get("name") or f.get("text", "Unknown")
                address = props.get("full_address") or props.get("address") or props.get("place_formatted", "")

                dist_m = self._haversine_meters(lat, lng, elem_lat, elem_lng)
                if radius and dist_m > radius:
                    continue

                results.append({
                    "name": name,
                    "vicinity": address,
                    "latitude": elem_lat,
                    "longitude": elem_lng,
                    "distance_meters": int(dist_m),
                })

            results.sort(key=lambda x: x["distance_meters"])
            return results[:limit]

        except Exception as e:
            logger.error(f"Mapbox POI exception: {e}")
            return []

    def _haversine_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Beregn avstand i meter (Haversine)."""
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
