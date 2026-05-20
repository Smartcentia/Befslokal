"""
OpenStreetMap Overpass API Client
Gratis POI-søk uten API-nøkkel!
Utmerket alternativ til Google Places.
"""
from typing import Dict, List, Optional
import asyncio
import httpx
import math
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.api_call_logs import ApiCallLog

logger = logging.getLogger(__name__)

# --- Circuit breaker (prosess-globalt) ---
_cb_failures = 0
_cb_open_until = 0.0
_CB_THRESHOLD = 3       # åpne kretsen etter 3 feil på rad
_CB_COOLDOWN  = 300.0   # hold kretsen åpen i 5 min


class OSMClient:
    """
    Klient for OpenStreetMap Overpass API.
    GRATIS - ingen API-nøkkel nødvendig!
    """
    
    # Mapping av våre service types til OSM tags
    OSM_TAG_MAPPING = {
        "hospital": {"amenity": "hospital"},
        "doctor": {"amenity": "doctors"},
        "pharmacy": {"amenity": "pharmacy"},
        "police": {"amenity": "police"},
        "fire_station": {"amenity": "fire_station"},
        "school": {"amenity": "school"},
        "supermarket": {"shop": "supermarket"},
        "transit_station": {"public_transport": "station"},
        "bus_station": {"amenity": "bus_station"},
        "train_station": {"railway": "station"},
        "subway_station": {"railway": "subway_entrance"},
        "movie_theater": {"amenity": "cinema"},
        "park": {"leisure": "park"},
        "gym": {"leisure": "fitness_centre"},
        "museum": {"tourism": "museum"},
        "library": {"amenity": "library"},
        # Utvidet for barnevern og tilgjengelighet
        "dentist": {"amenity": "dentist"},
        "psychologist": {"amenity": "psychologist"},
        "emergency_room": {"amenity": "emergency_ward"},
        "kindergarten": {"amenity": "kindergarten"},
        "high_school": {"amenity": "college"},
        "swimming_pool": {"leisure": "swimming_pool"},
        "playground": {"leisure": "playground"},
        "sports_facility": {"leisure": "sports_centre"},
        "youth_center": {"amenity": "youth_centre"},
        "leisure_center": {"leisure": "sports_centre"},
        "social_services": {"amenity": "social_facility"},
        "nav_office": {"office": "government"},
        "cafe": {"amenity": "cafe"},
        "church": {"amenity": "place_of_worship"},
    }
    
    def __init__(self):
        # Public Overpass API endpoints (fallback hvis en er nede)
        self.endpoints = [
            "https://overpass-api.de/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
        ]
        self.current_endpoint_idx = 0
    
    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        service_type: str = "hospital",
        db: Optional[AsyncSession] = None
    ) -> List[Dict]:
        # OSM disabled — Overpass API unreachable from Railway network
        return []

        # Få OSM tags for denne service typen
        osm_tags = self.OSM_TAG_MAPPING.get(service_type)
        if not osm_tags:
            logger.warning(f"Unknown service type: {service_type}")
            return []
        
        # Bygg Overpass QL query
        query = self._build_overpass_query(lat, lng, radius, osm_tags)
        
        global _cb_failures, _cb_open_until

        # Circuit breaker: returner tomt med én gang hvis kretsen er åpen
        if time.monotonic() < _cb_open_until:
            return []

        for attempt in range(len(self.endpoints)):
            endpoint = self.endpoints[self.current_endpoint_idx]

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        endpoint,
                        data=query,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        timeout=3.0,  # kort timeout — vi kan ikke blokkere workers
                    )

                    if response.status_code == 200:
                        _cb_failures = 0  # tilbakestill teller ved suksess
                        data = response.json()
                        results = self._parse_osm_response(data, lat, lng, service_type)
                        return results

                    elif response.status_code in [504, 503, 429]:
                        logger.warning(f"OSM {endpoint} returned {response.status_code}, trying next...")
                        self.current_endpoint_idx = (self.current_endpoint_idx + 1) % len(self.endpoints)
                        continue
                    else:
                        logger.error(f"OSM API Error: {response.status_code}")
                        return []

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"OSM endpoint {endpoint} timeout/error: {e}, trying next...")
                self.current_endpoint_idx = (self.current_endpoint_idx + 1) % len(self.endpoints)
                continue
            except Exception as e:
                logger.error(f"OSM Client Exception: {e}")
                return []

        # Alle endpoints feilet — åpne kretsen
        _cb_failures += 1
        if _cb_failures >= _CB_THRESHOLD:
            _cb_open_until = time.monotonic() + _CB_COOLDOWN
            logger.error(
                "OSM circuit breaker ÅPNET etter %d feil — pauser i %.0fs",
                _cb_failures, _CB_COOLDOWN,
            )
            _cb_failures = 0
        else:
            logger.error("All OSM endpoints failed (%d/%d)", _cb_failures, _CB_THRESHOLD)
        return []
    
    def _build_overpass_query(
        self,
        lat: float,
        lng: float,
        radius: int,
        tags: Dict[str, str]
    ) -> str:
        """
        Bygger Overpass QL query string.
        
        Example query:
        [out:json];
        node["amenity"="hospital"](around:1000,59.9139,10.7522);
        out center;
        """
        tag_filters = "".join([f'["{k}"="{v}"]' for k, v in tags.items()])
        
        query = f"""
        [out:json][timeout:25];
        (
          node{tag_filters}(around:{radius},{lat},{lng});
          way{tag_filters}(around:{radius},{lat},{lng});
        );
        out center;
        """
        return query.strip()
    
    def _parse_osm_response(
        self,
        data: Dict,
        origin_lat: float,
        origin_lng: float,
        service_type: str
    ) -> List[Dict]:
        """Parse OSM JSON response til vårt standardformat."""
        results = []
        
        elements = data.get("elements", [])
        
        for element in elements:
            # Hent koordinater (nodes har lat/lon direkte, ways har center)
            if element.get("type") == "node":
                elem_lat = element.get("lat")
                elem_lng = element.get("lon")
            elif element.get("type") == "way" and "center" in element:
                elem_lat = element["center"].get("lat")
                elem_lng = element["center"].get("lon")
            else:
                continue
            
            if elem_lat is None or elem_lng is None:
                continue
            
            # Hent tags
            tags = element.get("tags", {})
            name = tags.get("name", tags.get("operator", "Unnamed"))
            
            # Beregn avstand
            distance_m = self._haversine_distance(
                origin_lat, origin_lng, elem_lat, elem_lng
            )
            
            # Bygg adresse fra OSM tags
            address_parts = []
            if tags.get("addr:street"):
                street = tags["addr:street"]
                if tags.get("addr:housenumber"):
                    street += f" {tags['addr:housenumber']}"
                address_parts.append(street)
            if tags.get("addr:city"):
                address_parts.append(tags["addr:city"])
            
            address = ", ".join(address_parts) if address_parts else None
            
            results.append({
                "name": name,
                "latitude": elem_lat,
                "longitude": elem_lng,
                "distance_meters": int(distance_m),
                "address": address,
                "phone": tags.get("phone"),
                "website": tags.get("website"),
                "opening_hours": tags.get("opening_hours"),
                "category": service_type,
                "data_source": "openstreetmap"
            })
        
        # Sorter etter avstand
        results.sort(key=lambda x: x["distance_meters"])
        
        # Begrens til 10 nærmeste
        return results[:10]
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Beregn avstand mellom to koordinater i meter."""
        R = 6371000  # Jordens radius i meter
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def _log_usage(
        self,
        db: AsyncSession,
        status_code: int,
        result_count: int
    ):
        """Logger API-bruk (gratis, men bra å tracke for fair use)."""
        try:
            log = ApiCallLog(
                service_name="openstreetmap",
                endpoint="overpass/interpreter",
                request_count=1,
                cost_estimate=0.0,  # GRATIS!
                status_code=status_code,
                response_time_ms=0
            )
            db.add(log)
            # NOTE: Don't commit here - let the caller handle the transaction
            # This avoids "generator didn't stop" issues with nested commits
        except Exception as e:
            logger.error(f"Failed to log OSM usage: {e}")


# Convenience function
async def get_osm_nearby(
    lat: float,
    lng: float,
    service_type: str,
    radius: int = 1000,
    db: Optional[AsyncSession] = None
) -> List[Dict]:
    """
    Enkel funksjon for å hente POIs fra OpenStreetMap.
    
    Example:
        hospitals = await get_osm_nearby(59.9139, 10.7522, "hospital", 2000)
    """
    client = OSMClient()
    return await client.get_nearby_places(lat, lng, radius, service_type, db)
