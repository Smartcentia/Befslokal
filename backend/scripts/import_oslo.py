import asyncio
import uuid
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.api_clients.kartverket_client import KartverketClient
from app.services.api_clients.nve_client import NVEClient
from app.domains.core.models.property import Property
from app.models.external_api_data import ExternalApiData
from sqlalchemy import select
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("import_oslo")

# Target Streets for "Real Data"
STREETS = [
    ("Karl Johans gate", "0159", "Oslo"),
    ("Storgata", "0184", "Oslo"),
    ("Dronning Eufemias gate", "0191", "Oslo"),
    ("Akersgata", "0158", "Oslo"),
]

async def import_data():
    logger.info("🚀 Starting Oslo Import Job...")
    
    # Init Clients
    kartverket = KartverketClient()
    nve = NVEClient(api_key=settings.NVE_API_KEY)
    
    # Init DB
    engine = create_async_engine(settings.DATABASE_URL or "", echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    total_imported = 0

    async with AsyncSessionLocal() as db:
        for street, zip_code, city in STREETS:
            logger.info(f"📍 Searching for: {street}, {zip_code}...")
            
            # 1. Search Address (Kartverket)
            # Note: Kartverket client might return single point or list. 
            # We'll use search_address which returns a lat/lon dict usually.
            # But we want MULTIPLE addresses.
            # existing client is simple. Let's do a raw lookup loop for numbers 1-20
            
            for num in range(1, 25):
                addr_str = f"{street} {num}"
                logger.info(f"  🔍 Looking up {addr_str}...")
                
                coords = await kartverket.search_address(f"{addr_str}, {zip_code}")
                if not coords:
                    continue
                
                lat = coords["latitude"]
                lon = coords["longitude"]
                
                # Check if exists
                existing = await db.execute(select(Property).where(Property.address == addr_str))
                if existing.scalar_one_or_none():
                    logger.info(f"  ⏭️  Skipping existing: {addr_str}")
                    continue

                # 2. Fetch Matrikkel Info (Kommune/Gnr/Bnr)
                kommune_info = await kartverket.get_kommune_from_point(lat, lon)
                
                # 3. Fetch NVE Risk Data
                logger.info("    🌊 Fetching Risk Data...")
                flood_zones = await nve.fetch_flood_zone(lat, lon)
                landslide = await nve.fetch_landslide_risk(lat, lon)
                # quick clay...
                
                # 4. create Property Object
                prop_id = uuid.uuid4()
                p = Property(
                    property_id=prop_id,
                    address=addr_str,
                    city=city,
                    postal_code=zip_code,
                    latitude=lat,
                    longitude=lon,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                # Enrich with generic data if missing from API
                p.external_data = {
                    "source": "import_oslo",
                    "kommune": kommune_info.get("kommunenavn", "Oslo"),
                    "matrikkel_knr": kommune_info.get("kommunenummer"),
                    "gnr": 1, # Placeholder if not fetched
                    "bnr": num, # Placeholder
                    "risk_summary": {
                        "flood": bool(flood_zones),
                        "landslide": bool(landslide)
                    }
                }
                
                db.add(p)
                
                # 5. Store Raw API Data
                risk_data = {
                    "flood_zones": flood_zones,
                    "landslide": landslide,
                    "kommune_info": kommune_info
                }
                
                ext = ExternalApiData(
                    api_data_id=uuid.uuid4(),
                    source_api="import_oslo_aggregated",
                    entity_type="property",
                    entity_id=prop_id,
                    data=risk_data,
                    fetched_at=datetime.now(timezone.utc)
                )
                db.add(ext)
                
                total_imported += 1
                if total_imported % 5 == 0:
                    await db.commit()
                    logger.info(f"💾 Committed {total_imported} properties so far...")
                    
        await db.commit()
        logger.info(f"✅ FINISHED! Total properties imported: {total_imported}")

if __name__ == "__main__":
    asyncio.run(import_data())
