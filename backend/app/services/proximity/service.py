
import json
import logging
import math
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set

import httpx
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.models.proximity import ProximityService as ProximityServiceModel
from app.domains.core.models.property import Property as PropertyModel
from app.services.external.mapbox_client import MapboxClient
from app.services.external.osm_client import OSMClient

logger = logging.getLogger(__name__)

# Tjenester der bil er primærtransport – bruk ~500 m/min (30 km/t i by/vei)
# Øvrige tjenester: gange ~80 m/min (~5 km/t)
_CAR_SERVICE_TYPES = frozenset({
    "hospital", "police", "fire_station", "emergency_room",
    "ambulance", "bup",
})


def _estimate_travel_time(distance_meters: float, service_type: str) -> float:
    """Estimerer reisetid (min) basert på tjenestetype og typisk transport.

    Blålys/sykehus beregnes med bilhastighet (~30 km/t i by).
    Gange brukes for lokal-tjenester (apotek, butikk, park).
    """
    speed = 500 if service_type in _CAR_SERVICE_TYPES else 80  # m/min
    return round(distance_meters / speed, 1)


DEFAULT_SERVICE_TYPES = [
    # Kritiske (proximity_requirements)
    "police",
    "hospital",
    "doctor",
    "pharmacy",
    "fire_station",
    "school",
    "supermarket",
    # Transport
    "transit_station",
    "bus_station",
    "train_station",
    "subway_station",
    # Fritid & aktivitet
    "movie_theater",
    "park",
    "gym",
    "museum",
    "library",
    "swimming_pool",
    "playground",
    "sports_facility",
    "youth_center",
    # Helse (utvidet for barnevern)
    "dentist",
    "psychologist",
    "emergency_room",
    # Utdanning
    "kindergarten",
    "high_school",
    # Offentlige tjenester
    "social_services",
    "nav_office",
    # Andre
    "leisure_center",
    "cafe",
    "bup",  # Custom type for BUP (Child & Adolescent Psych)
]

class ProximityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_proximity_services(
        self,
        property_id: UUID,
        latitude: float,
        longitude: float,
        service_types: Optional[List[str]] = None,
        radius: int = 5000,
        force_refresh: bool = False,
    ) -> List[ProximityServiceModel]:
        """
        Fetch nearby services for a property.
        Checks cache first, then calls Mapbox / BUP data.
        """
        mapbox_client = MapboxClient()
        if service_types is None:
            service_types = DEFAULT_SERVICE_TYPES

        # 1. Check Cache
        if not force_refresh:
            cached = await self.get_cached_services(property_id)
            if cached:
                # Check coverage - specifically if BUP is requested but missing (new feature)
                cached_types = {s.service_type for s in cached}
                missing_bup = "bup" in service_types and "bup" not in cached_types
                
                if not missing_bup:
                    return cached
        new_services = []
        mapbox_has_token = bool(getattr(mapbox_client, "access_token", None))
        osm_client = OSMClient()
        
        # Mapbox POI Data (with OSM fallback when Mapbox returns empty or token missing)
        for stype in service_types:
            if stype == "bup":
                continue  # BUP håndteres separat nedenfor
            
            places = []
            data_source = "mapbox"
            
            if mapbox_has_token:
                try:
                    places = await mapbox_client.get_nearby_places(
                        lat=latitude,
                        lng=longitude,
                        service_type=stype,
                        radius=radius,
                        limit=10
                    )
                    if places:
                        logger.info(f"Fetched {len(places)} {stype} from Mapbox")
                except Exception as e:
                    logger.error(f"Error fetching {stype} from Mapbox: {e}")
            
            # OSM fallback: when Mapbox token missing or returned empty
            if not places and stype in osm_client.OSM_TAG_MAPPING:
                try:
                    osm_places = await osm_client.get_nearby_places(
                        lat=latitude,
                        lng=longitude,
                        radius=radius,
                        service_type=stype,
                        db=self.db
                    )
                    if osm_places:
                        places = osm_places
                        data_source = "openstreetmap"
                        logger.info(f"Fetched {len(places)} {stype} from OSM (fallback)")
                except Exception as e:
                    logger.error(f"Error fetching {stype} from OSM: {e}")
            
            for place in places:
                # Skip places without valid coordinates
                if place.get("latitude") is None or place.get("longitude") is None:
                    continue
                
                distance = place.get("distance_meters") or 0
                travel_time = _estimate_travel_time(distance, stype) if distance > 0 else None
                
                # OSM uses "address", Mapbox uses "vicinity"
                address = place.get("vicinity") or place.get("address")
                
                new_services.append({
                    "service_type": stype,
                    "name": place.get("name") or "Unknown",
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "distance_meters": distance,
                    "travel_time_minutes": travel_time,
                    "rating": None,
                    "address": address,
                    "phone": place.get("phone"),
                    "data_source": data_source
                })

        # BUP Data (Custom Source)
        if "bup" in service_types:
            try:
                # BUP radius is fixed to 100 km (10 mil) as per requirements
                bup_results = self._fetch_bup_locations(latitude, longitude, radius=100000)
                new_services.extend(bup_results)
            except Exception as e:
                logger.error(f"Error fetching BUP data: {e}")

        # 3. Save to DB (Replace existing) with proper transaction handling
        if new_services:
            try:
                # Delete old entries
                await self.db.execute(
                    delete(ProximityServiceModel).where(
                        ProximityServiceModel.property_id == property_id
                    )
                )
                
                # Prepare objects
                cache_days = getattr(settings, 'RISK_CACHE_EXPIRY_DAYS', 30)
                expires = datetime.utcnow() + timedelta(days=cache_days)
                
                for svc in new_services:
                    db_obj = ProximityServiceModel(
                        property_id=property_id,
                        service_type=svc["service_type"],
                        service_name=svc["name"],
                        latitude=svc["latitude"],
                        longitude=svc["longitude"],
                        distance_meters=svc["distance_meters"],
                        travel_time_minutes=svc.get("travel_time_minutes"),
                        rating=svc.get("rating"),
                        address=svc.get("address"),
                        phone=svc.get("phone"),
                        data_source=svc["data_source"],
                        fetched_at=datetime.utcnow(),
                        expires_at=expires
                    )
                    self.db.add(db_obj)
                
                await self.db.commit()
                
                # Re-fetch to return with IDs
                return await self.get_cached_services(property_id)
                
            except Exception as e:
                logger.error(f"Error saving proximity services to DB: {e}")
                await self.db.rollback()
                raise
        
        return []

    async def get_cached_services(
        self, property_id: UUID, service_type: Optional[str] = None
    ) -> List[ProximityServiceModel]:
        """Get cached services from DB."""
        query = select(ProximityServiceModel).where(
            ProximityServiceModel.property_id == property_id,
            ProximityServiceModel.expires_at > datetime.utcnow()
        )
        
        if service_type:
            query = query.where(ProximityServiceModel.service_type == service_type)
            
        query = query.order_by(ProximityServiceModel.distance_meters)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_accessibility_summary(self, property_id: UUID) -> Dict[str, Any]:
        """Calculate accessibility metrics."""
        # Use fetch to ensure data is present (checks cache internally)
        # We need property coords for fetch, but this method only has ID.
        # We'd need to look up property. For now, let's keep it simple:
        # If we rely on get_cached_services, we assume it's already populated.
        # But if we want auto-population, we need to pass lat/long.
        # Let's delegate this responsibility to the router or caller if possible.
        # Reverting to simple get_cached mainly, but strictly better to use fetch if we had coords.
        # Since we don't have coords here easily without DB lookup, let's skip for now 
        # and rely on the frontend calling the list endpoint which we will fix to fetch.
        services = await self.get_cached_services(property_id)
        if not services:
            return {
                "total_services": 0,
                "service_counts": {},
                "nearest_by_type": {},
                "average_distance": 0,
                "average_travel_time": 0
            }

        total = len(services)
        counts = {}
        nearest = {}
        total_dist = 0
        total_time = 0
        time_count = 0

        for svc in services:
            # Counts
            counts[svc.service_type] = counts.get(svc.service_type, 0) + 1
            
            # Nearest
            if svc.service_type not in nearest:
                nearest[svc.service_type] = {
                    "name": svc.service_name,
                    "distance_meters": svc.distance_meters,
                    "travel_time_minutes": svc.travel_time_minutes
                }
            
            # Averages
            if svc.distance_meters:
                total_dist += svc.distance_meters
            
            if svc.travel_time_minutes:
                total_time += svc.travel_time_minutes
                time_count += 1

        return {
            "total_services": total,
            "service_counts": counts,
            "nearest_by_type": nearest,
            "average_distance": round(total_dist / total, 1) if total > 0 else 0,
            "average_travel_time": round(total_time / time_count, 1) if time_count > 0 else 0
        }

    # --- Internal Helpers ---



    def _fetch_bup_locations(
        self, lat: float, lon: float, radius: int
    ) -> List[Dict[str, Any]]:
        """Fetch BUP locations from local JSON with robust path resolution."""
        # Resolve path to backend root where the JSON file is located
        # backend/app/services/proximity/service.py -> backend/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        file_path = os.path.join(base_dir, "bup_lokasjoner_og_lenker.json")
        
        if not os.path.exists(file_path):
            # Fallback to current working directory
            alt_path = "bup_lokasjoner_og_lenker.json"
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                logger.warning(f"BUP JSON file not found at {file_path} or {alt_path}")
                return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading BUP data from {file_path}: {e}")
            return []

        results = []
        # Flatten structure "lokasjoner" -> "Region" -> list
        for region, locs in data.get("lokasjoner", {}).items():
            for loc in locs:
                if "latitude" not in loc or "longitude" not in loc:
                    continue
                    
                dist = self._haversine_distance_meters(
                    lat, lon, loc["latitude"], loc["longitude"]
                )
                
                if dist <= radius:
                    results.append({
                        "service_type": "bup",
                        "name": loc.get("navn", f"BUP - {loc.get('adresse')}"),
                        "latitude": loc["latitude"],
                        "longitude": loc["longitude"],
                        "distance_meters": dist,
                        "travel_time_minutes": dist / 500, # Rough est
                        "rating": None,
                        "address": loc.get("adresse"),
                        "phone": loc.get("telefon"),
                        "data_source": "bup"
                    })
        return results

    def _haversine_distance_meters(self, lat1, lon1, lat2, lon2):
        """Calculate Haversine distance in meters."""
        R = 6371000  # Radius of Earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
