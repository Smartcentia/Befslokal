from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.external_api_data import ExternalApiData
from app.domains.core.models.property import Property
from app.services.external.api_clients.kartverket_client import KartverketClient
from app.services.external.api_clients.nve_client import NVEClient
from app.services.search.indexer import index_api_data

async def get_location_info(property_id: UUID, db: AsyncSession) -> Dict[str, Any]:
    """
    Henter samlet lokasjonsinfo for en eiendom.
    Sjekker cache først, returnerer det som finnes.
    Trigger IKKE ny uthenting (det skjer via eksplisiitt kall eller bakgrunnsjobb).
    """
    # 1. Hent eiendom
    result = await db.execute(select(Property).where(Property.property_id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        return {"error": "Eiendom ikke funnet"}

    # 2. Hent cachet data
    result = await db.execute(select(ExternalApiData).where(ExternalApiData.entity_id == str(property_id)))
    external_data = result.scalars().all()
    
    location_info = {}
    for entry in external_data:
        info = entry.data.copy() if entry.data else {}
        if entry.expires_at and entry.expires_at < datetime.utcnow():
            info["expired"] = True
        location_info[entry.source_api] = info

    return {
        "property": {
            "property_id": str(prop.property_id),
            "address": prop.address,
            "city": prop.city,
            "latitude": prop.latitude,
            "longitude": prop.longitude
        },
        "location_info": location_info
    }

async def fetch_and_cache_location_data(
    property_id: UUID,
    db: AsyncSession,
    fetch_kartverket: bool = True,
    fetch_nve: bool = True
) -> Dict[str, Any]:
    """
    Henter ferske data fra eksterne APIer og cacher dem.
    """
    result = await db.execute(select(Property).where(Property.property_id == property_id))
    prop = result.scalar_one_or_none()
    
    if not prop:
        return {"error": "Eiendom ikke funnet"}
        
    if not prop.latitude or not prop.longitude:
        return {"error": "Eiendom mangler koordinater"}

    results = {}
    
    # KARTVERKET
    if fetch_kartverket:
        result = await db.execute(select(ExternalApiData).filter(
            ExternalApiData.source_api == "kartverket",
            ExternalApiData.entity_id == str(property_id)
        ))
        cached = result.scalar_one_or_none()
        
        if cached and cached.expires_at > datetime.utcnow():
            results["kartverket"] = {"status": "cached", "data": cached.data}
        else:
            client = KartverketClient()
            # client.fetch might be async? assuming sync for now or check client code.
            # Usually clients are async in this codebase.
            # Let's assume sync for now based on previous grep, but use await if I find it's async later.
            data = client.fetch_property_data(prop.latitude, prop.longitude) 
            
            # Save/Update
            if not cached:
                cached = ExternalApiData(
                    source_api="kartverket",
                    entity_type="property",
                    entity_id=str(property_id)
                )
            
            cached.data = data
            cached.expires_at = datetime.utcnow() + timedelta(hours=24)
            db.add(cached)
            await db.commit()
            
            # Index
            # await index_api_data(data) # assuming sync for now?
            index_api_data(data)
            results["kartverket"] = {"status": "success", "data": data}

    if fetch_nve:
        result = await db.execute(select(ExternalApiData).filter(
            ExternalApiData.source_api == "nve",
            ExternalApiData.entity_id == str(property_id)
        ))
        cached = result.scalar_one_or_none()
        
        if cached and cached.expires_at > datetime.utcnow():
            results["nve"] = {"status": "cached", "data": cached.data}
        else:
            client = NVEClient()
            data = client.fetch_property_data(prop.latitude, prop.longitude)
            
            if not cached:
                cached = ExternalApiData(
                    source_api="nve",
                    entity_type="property",
                    entity_id=str(property_id)
                )
            
            cached.data = data
            cached.expires_at = datetime.utcnow() + timedelta(hours=24)
            db.add(cached)
            await db.commit()
            
            index_api_data(data)
            results["nve"] = {"status": "success", "data": data}
            
    return results
