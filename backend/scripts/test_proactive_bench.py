
import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Load env before imports
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)

# Adjust path to find backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.ki_kollega.service import ki_kollega_service, ChatContext
from app.db.session import SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_benchmark():
    print("🚀 Starting Proactive Assistant Benchmark...\n")
    
    async with SessionLocal() as db:
        # Scenario 1: Property Context (Expiring Contracts)
        # We need to find a property that actually has contracts, or mock it if needed.
        # For now, let's try a known property ID if possible, or search for one.
        
        print("[1/3] Scenario: Viewing Property (Check for Expiring Contracts)")
        # Let's try to query a property with contracts first to get a valid ID
        from sqlalchemy import text
        result = await db.execute(text("""
            SELECT p.property_id, p.name 
            FROM properties p
            JOIN units u ON p.property_id = u.property_id
            JOIN contracts c ON u.unit_id = c.unit_id
            LIMIT 1
        """))
        prop = result.fetchone()
        
        if prop:
            prop_id = str(prop.property_id)
            print(f"   Context: User is viewing property '{prop.name}' (ID: {prop_id})")
            
            context = ChatContext(
                page="property_detail",
                entity_type="property",
                entity_id=prop_id
            )
            
            insights = await ki_kollega_service.get_proactive_insights(db, context)
            
            if insights:
                print(f"✅ AI Generated {len(insights)} insights:")
                for i in insights:
                    print(f"   - [{i['type'].upper()}] {i['content']}")
            else:
                print("⚠️ No insights generated (might be expected if no contracts are expiring).")
        else:
            print("⚠️ No suitable test data found in properties.")

        print("-" * 50)

        # Scenario 2: Dashboard Context
        print("[2/3] Scenario: Dashboard (Portfolio Summary)")
        context = ChatContext(
            page="dashboard"
        )
        
        insights = await ki_kollega_service.get_proactive_insights(db, context)
        if insights:
            print(f"✅ AI Generated {len(insights)} insights:")
            for i in insights:
                 print(f"   - [{i['type'].upper()}] {i['content']}")
        else:
             print("❌ No dashboard insights generated.")

        print("-" * 50)
        
        # Scenario 3: Empty Context
        print("[3/3] Scenario: No Context")
        context = ChatContext()
        insights = await ki_kollega_service.get_proactive_insights(db, context)
        if not insights:
            print("✅ Correctly generated no insights for empty context.")
        else:
            print(f"⚠️ Generated unexpected insights: {insights}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
