import asyncio
import os
import sys
import uuid
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Add backend to path
sys.path.append(os.getcwd())

import app.db.base # Ensure all models are registered
from app.domains.hms.services.risk_service import RiskService
from app.services.external_data_orchestrator import ExternalDataOrchestrator
from app.models.external_api_data import ExternalApiData
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_fixes")

async def verify():
    async with SessionLocal() as db:
        # 1. Pick a property from the DB
        result = await db.execute(text("SELECT property_id, address FROM properties LIMIT 1"))
        prop = result.fetchone()
        if not prop:
            logger.error("No properties found in DB to test with.")
            return

        prop_id = str(prop[0])
        address = prop[1]
        logger.info(f"Testing with property: {address} ({prop_id})")

        # 2. Cleanup previous cache for this property to ensure clean start
        await db.execute(text(f"DELETE FROM external_api_data WHERE entity_id = '{prop_id}'"))
        await db.commit()
        logger.info("Cleared previous cache entries.")

        # 3. First call to RiskService (should trigger real API calls)
        logger.info("First call to RiskService (triggering API calls)...")
        risk1 = await RiskService.calculate_risk_for_property(prop_id, db)
        if risk1 is None:
            logger.error("FAILED: risk1 is None.")
            return
        logger.info(f"Risk1 factors: {risk1['factors']}")

        # 4. Verify data in DB
        result = await db.execute(text(f"SELECT COUNT(*) FROM external_api_data WHERE entity_id = '{prop_id}'"))
        count = result.scalar()
        logger.info(f"Cache entries in DB: {count}")
        if count == 0:
            logger.error("FAILED: No cache entry created in DB.")
        else:
            logger.info("SUCCESS: Cache entry created in DB.")

        # 5. Second call to RiskService (should use cache)
        logger.info("Second call to RiskService (should use cache)...")
        risk2 = await RiskService.calculate_risk_for_property(prop_id, db)
        
        # In a real environment, we'd check logs for "Using cached risk data"
        # Since we can't easily capture logs, we check if factors are identical
        if risk1['factors'] == risk2['factors']:
            logger.info("SUCCESS: Risk factors are consistent across calls.")
        else:
            logger.warning("Risk factors differed. This might happen if randomness still exists or cache failed.")

        # 6. Verify factors are not 'simulated'
        for factor in risk1['factors']:
            if "(simulert" in factor:
                logger.error(f"FAILED: Found simulated factor: {factor}")
            else:
                logger.info(f"Verified real factor: {factor}")

if __name__ == "__main__":
    asyncio.run(verify())
