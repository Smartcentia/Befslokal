import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
import app.db.base # Register all models
from app.domains.core.services.party_service import PartyService
from sqlalchemy import select
from app.domains.core.models.party import Party

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_brreg_persistence():
    # org_nr = "986161189" # Bufetat Region Midt-Norge (Seems problematic or deleted)
    org_nr = "889640782" # Arbeids- og velferdsetaten (Known valid)
    
    logger.info(f"--- Starting Verification for OrgNr: {org_nr} ---")
    
    async with SessionLocal() as db:
        # 1. Fetch and Store using the new Service
        logger.info("1. Calling PartyService.fetch_and_store_party...")
        data = await PartyService.fetch_and_store_party(org_nr, db)
        
        if not data:
            logger.error("❌ Failed to fetch data from BRRG via PartyService.")
            return
            
        logger.info(f"✅ Data fetched successfully: {data.get('name')}")
        
        # 2. Verify Persistence in DB
        logger.info("2. Verifying persistence in PostgreSQL...")
        query = select(Party).filter(Party.orgnr == org_nr)
        result = await db.execute(query)
        party = result.scalar_one_or_none()
        
        if party:
            logger.info(f"✅ Party found in DB!")
            logger.info(f"   Name: {party.name}")
            logger.info(f"   Updated At: {party.updated_at}")
            logger.info(f"   External Data: {party.external_data.keys()}")
            
            if party.name == data.get('name'):
                logger.info("✅ DB Name matches BRRG Name.")
            else:
                logger.warning(f"⚠️ DB Name ({party.name}) differs from BRRG Name ({data.get('name')})")
        else:
            logger.error("❌ Party NOT found in DB after fetch_and_store_party.")

    logger.info("--- Verification Finished ---")

if __name__ == "__main__":
    asyncio.run(verify_brreg_persistence())
