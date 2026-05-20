import json
import logging
import os
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User
from app.domains.core.models.property import Property as PropertyModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Robust path resolution - look for file in backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_FILE = os.path.join(BASE_DIR, "bup_lokasjoner_og_lenker.json")

def load_bup_data() -> Dict[str, Any]:
    """Laster BUP-data fra JSON-fil med robust sti-håndtering."""
    file_path = DATA_FILE
    
    logger.debug("Leter etter BUP-data i: %s", file_path)

    if not os.path.exists(file_path):
        # Fallback to local if relative (for development)
        alt_path = "bup_lokasjoner_og_lenker.json"
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            logger.warning("BUP-datafil ikke funnet på %s eller %s", file_path, alt_path)
            return {"lokasjoner": {}}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Kunne ikke laste BUP-data fra %s: %s", file_path, e)
        return {"lokasjoner": {}}

def flatten_locations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Konverterer region-basert struktur til flat liste."""
    flat_list = []
    locations_map = data.get("lokasjoner", {})
    
    counter = 1
    for region_key, locations in locations_map.items():
        region_name = region_key.replace("_", " ").replace("sor ost", "Sør-øst").title()
        if region_key == "helse_sor_ost":
            region_name = "Helse Sør-øst"
        
        for loc in locations:
            flat_list.append({
                "id": f"bup_{counter}",
                "navn": loc.get("navn") or loc.get("adresse", ""),
                "adresse": loc.get("adresse"),
                "telefon": loc.get("telefon"),
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "region": region_name,
                "region_key": region_key
            })
            counter += 1
    return flat_list

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Beregn avstand mellom to koordinater i kilometer."""
    R = 6371  # Jordens radius i km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

@router.get("/bup-locations", response_model=Dict[str, Any])
async def get_bup_locations(
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Henter alle BUP-lokasjoner.
    """
    data = load_bup_data()
    locations = flatten_locations(data)
    
    if region:
        locations = [l for l in locations if l.get("region_key") == region]
        
    return {
        "total": len(locations),
        "locations": locations,
        "metadata": data.get("metadata", {})
    }


@router.get("/nearby-map", response_model=Dict[str, Any])
async def get_bup_nearby_map(
    property_ids: str = Query(..., description="Kommaseparert liste med property_id (UUID)"),
    max_distance_km: float = Query(30.0, ge=0.1, le=200.0, description="Maks avstand i km"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Henter BUP-lokasjoner innenfor max_distance_km av minst én av de angitte eiendommene.
    Brukes for å vise BUP som markører på eiendomsoversiktskartet.
    """
    if not property_ids or not property_ids.strip():
        return {"locations": [], "total": 0}

    # Parse UUIDs
    try:
        ids = [UUID(pid.strip()) for pid in property_ids.split(",") if pid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_ids-format (forventet UUID-er kommaseparert)")

    if not ids:
        return {"locations": [], "total": 0}

    # Hent eiendommer med koordinater
    stmt = select(PropertyModel).where(
        PropertyModel.property_id.in_(ids),
        PropertyModel.latitude.isnot(None),
        PropertyModel.longitude.isnot(None),
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()

    if not properties:
        return {"locations": [], "total": 0}

    # Last BUP-data
    data = load_bup_data()
    bup_locations = flatten_locations(data)

    # Finn BUP innenfor radius av minst én eiendom
    results = []
    for loc in bup_locations:
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if lat is None or lon is None:
            continue

        min_dist_km = float("inf")
        for prop in properties:
            d = haversine_distance_km(lat, lon, prop.latitude, prop.longitude)
            if d < min_dist_km:
                min_dist_km = d

        if min_dist_km <= max_distance_km:
            results.append({
                "id": loc.get("id"),
                "navn": loc.get("navn", loc.get("adresse", "")),
                "adresse": loc.get("adresse"),
                "latitude": lat,
                "longitude": lon,
                "nearest_property_distance_km": round(min_dist_km, 2),
            })

    return {"locations": results, "total": len(results)}


@router.get("/bup-locations/{location_id}/nearby-properties")
async def get_nearby_properties(
    location_id: str,
    max_distance_km: float = 5.0,
    current_user: User = Depends(get_current_user),
):
    """
    Finn nærliggende barnevernsinstitusjoner for en BUP-lokasjon.
    """
    data = load_bup_data()
    locations = flatten_locations(data)
    
    target_loc = next((l for l in locations if l["id"] == location_id), None)
    if not target_loc:
        raise HTTPException(status_code=404, detail="Location not found")
        
    if not target_loc.get("latitude") or not target_loc.get("longitude"):
         return {
            "location": target_loc,
            "max_distance_km": max_distance_km,
            "total_nearby": 0,
            "properties": [],
            "message": "BUP location has no coordinates"
        }

    # In a real scenario, we would inject a PropertyService here and query the database.
    # For now, we return empty list if not implemented, removing mock data.
    nearby = []
    
    return {
        "location": target_loc,
        "max_distance_km": max_distance_km,
        "total_nearby": 0,
        "properties": []
    }

from app.services.external.mapbox_client import MapboxClient

@router.post("/bup-locations/geocode")
async def geocode_locations(
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
):
    """Geokoder BUP-lokasjoner via Mapbox API."""
    data = load_bup_data()
    total = geocoded = failed = skipped = 0

    mapbox_client = MapboxClient()
    # MAPBOX_ACCESS_TOKEN må være satt i miljø
    if not mapbox_client.access_token:
        raise HTTPException(status_code=503, detail="MAPBOX_ACCESS_TOKEN mangler. Sett i .env.")

    for region, locations in data.get("lokasjoner", {}).items():
        for loc in locations:
            total += 1
            if not force_refresh and loc.get("latitude") and loc.get("longitude"):
                skipped += 1
                continue

            address = loc.get("adresse")
            if not address:
                failed += 1
                continue

            try:
                result = await mapbox_client.geocode_address(address)
                if result:
                    loc["latitude"] = result["latitude"]
                    loc["longitude"] = result["longitude"]
                    geocoded += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error("Error geocoding %s: %s", address, e)
                failed += 1

    if geocoded > 0:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save geocoded data: %s", e)
            raise HTTPException(status_code=500, detail="Failed to save geocoded data")

    return {
        "total_locations": total,
        "geocoded": geocoded,
        "failed": failed,
        "skipped": skipped,
        "message": f"Successfully geocoded {geocoded} locations"
    }
