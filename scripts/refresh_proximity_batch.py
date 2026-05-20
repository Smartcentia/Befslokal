
import asyncio
import os
import sys
import logging
from uuid import UUID

# Legg til backend-mappen i sys.path slik at vi kan importere app-moduler
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

# Importer alle modeller via app.db.base for å sikre at registry er komplett
import app.db.base

from app.db.session import SessionLocal
from app.domains.core.models.property import Property as PropertyModel
from app.services.proximity.service import ProximityService
from sqlalchemy import select

# Oppsett av logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("batch_proximity")

async def refresh_all_proximity():
    """
    Script for å batch-oppdatere nærliggende tjenester for alle eiendommer
    som har koordinater.
    """
    logger.info("Starter batch-oppdatering av nærliggende tjenester...")
    
    async with SessionLocal() as db:
        # Finn alle eiendommer med koordinater
        stmt = select(PropertyModel).where(
            PropertyModel.latitude.isnot(None),
            PropertyModel.longitude.isnot(None)
        )
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        logger.info(f"Fant {len(properties)} eiendommer med koordinater.")
        
        service = ProximityService(db)
        updated_count = 0
        error_count = 0
        
        for prop in properties:
            try:
                logger.info(f"Behandler: {prop.name or prop.address} ({prop.property_id})")
                
                # Hent tjenester (force_refresh=True sikrer at vi henter nye data)
                await service.fetch_proximity_services(
                    property_id=prop.property_id,
                    latitude=float(prop.latitude),
                    longitude=float(prop.longitude),
                    force_refresh=True
                )
                
                updated_count += 1
                # Liten pause for å unngå for heftig rate-limiting mot eksterne API-er
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Feil ved oppdatering av property {prop.property_id}: {str(e)}")
                error_count += 1
        
        await db.commit()
        
    logger.info(f"Ferdig! Oppdatert: {updated_count}, Feil: {error_count}")

if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        print("FEIL: DATABASE_URL miljøvariabel er ikke satt.")
        sys.exit(1)
        
    asyncio.run(refresh_all_proximity())
