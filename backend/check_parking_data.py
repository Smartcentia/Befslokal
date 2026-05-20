import asyncio
import sys
import os
from sqlalchemy import select, func, text, or_

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.session import SessionLocal
from app.models.text_content import TextContent
from app.domains.core.models.property import Property
from app.domains.core.models.center import Center
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User # Fix for relationship error

async def check_parking():
    print("Checking Parking Data in PostgreSQL...\n")
    
    async with SessionLocal() as db:
        # 1. Count text content related to parking
        keywords = ["parkering", "garasje", "lading", "p-plass"]
        conditions = [TextContent.content.ilike(f"%{kw}%") for kw in keywords]
        
        stmt = select(func.count(TextContent.text_id)).where(or_(*conditions))
        text_count = (await db.execute(stmt)).scalar() or 0
        
        # 2. Check Property insights
        # Assuming we store it in external_data->'ai_insights'->'parking'
        prop_stmt = select(func.count(Property.property_id)).where(
            text("external_data->'ai_insights'->'parking' IS NOT NULL")
        )
        prop_count = (await db.execute(prop_stmt)).scalar() or 0
        
        print(f"Parking-related documents found: {text_count}")
        print(f"Properties with AI Parking Insights: {prop_count}")
        
        # 3. List sample properties
        if prop_count > 0:
            print("\nSample Properties with Parking Data:")
            sample_stmt = select(Property).where(
                text("external_data->'ai_insights'->'parking' IS NOT NULL")
            ).limit(5)
            samples = (await db.execute(sample_stmt)).scalars().all()
            
            for p in samples:
                parking = p.external_data.get('ai_insights', {}).get('parking', {})
                print(f"- {p.address}: {parking.get('summary', 'No summary')}")

        if text_count == 0:
            print("\n⚠️ No parking documents found. Run 'structure_parking_data.py' or check import.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_parking())
