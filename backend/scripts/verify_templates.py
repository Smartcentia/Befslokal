import asyncio
import logging
import sys
import os
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
import app.db.base 
from app.domains.hms.services.internal_control_service import InternalControlService
from app.domains.hms.models.internal_control import InternalControlCase
from sqlalchemy import select, delete

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_templates():
    # Setup test data
    property_id = uuid.uuid4() 
    user_id = uuid.uuid4()
    
    # We need a property in DB for the service to work (it fetches prop address)
    # But since we are testing the Service logic locally, we might need to mock or insert a dummy prop.
    # The service does: `result = await db.execute(select(Property).filter(Property.property_id == str(property_id)))`
    # Let's insert a dummy property first.
    
    from app.domains.core.models.property import Property
    
    logger.info("--- Starting Template Verification ---")

    # Use expire_on_commit=False to avoid MissingGreenlet error when accessing objects after commit
    async with SessionLocal() as db:
        db.expire_on_commit = False
        
        # 1. Create Dummy Property
        prop = Property(
            property_id=property_id,
            name="Test Institution RKL6",
            address="Testveien 1",
            postal_code="0101",
            city="Oslo",
            municipality_code="0301",
            latitude=59.9,
            longitude=10.7
        )
        db.add(prop)

        # 1b. Create Dummy User
        from app.domains.core.models.user import User
        unique_email = f"test_{uuid.uuid4()}@example.com"
        user = User(
            user_id=user_id,
            email=unique_email,
            name="Test User"
        )
        db.add(user)

        await db.commit()
        
        try:
            # 2. Call Service to Create Cases
            logger.info("Calling create_mock_cases_for_property...")
            await InternalControlService.create_mock_cases_for_property(db, property_id, user_id)
            
            # 3. Verify Results (Re-fetch to avoid detached objects)
            stmt = select(InternalControlCase).where(InternalControlCase.property_id == property_id)
            result = await db.execute(stmt)
            cases = result.scalars().all()
            
            logger.info(f"Created {len(cases)} cases.")
            
            rkl6_found = False
            checklist_found = False
            
            for c in cases:
                logger.info(f"Case: {c.title} (Type: {c.case_type})")
                if "Risikoklasse 6" in c.title:
                    rkl6_found = True
                
                if c.process_data and "checklist" in c.process_data:
                    checklist = c.process_data["checklist"]
                    logger.info(f"  Checklist items: {len(checklist)}")
                    if len(checklist) > 0:
                        checklist_found = True
                        logger.info(f"  Sample Item: {checklist[0]}")

            if rkl6_found and checklist_found:
                logger.info("✅ SUCCESS: RKL 6 templates loaded and checklist structured correctly.")
            else:
                logger.error("❌ FAILURE: RKL 6 templates NOT found or structure missing.")

        finally:
            # Cleanup
            from app.domains.hms.models.internal_control import Notification
            await db.execute(delete(Notification).where(Notification.user_id == user_id))
            await db.execute(delete(InternalControlCase).where(InternalControlCase.property_id == property_id))
            await db.execute(delete(Property).where(Property.property_id == property_id))
            from app.domains.core.models.user import User
            await db.execute(delete(User).where(User.user_id == user_id))
            await db.commit()

if __name__ == "__main__":
    asyncio.run(verify_templates())
