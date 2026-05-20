import asyncio
import os
import sys

# Add backend to path - assuming running from backend dir
sys.path.append(os.getcwd())

from dotenv import load_dotenv
import os

# Explicitly load .env
load_dotenv('.env', override=True)

# Patch environment for Pydantic if missing
if not os.getenv("POSTGRES_SERVER"):
    print("⚠️ POSTGRES_SERVER not found in env, using default 'localhost'")
    os.environ["POSTGRES_SERVER"] = "localhost"
if not os.getenv("POSTGRES_USER"):
    os.environ["POSTGRES_USER"] = "postgres"
if not os.getenv("POSTGRES_PASSWORD"):
    os.environ["POSTGRES_PASSWORD"] = "password"
if not os.getenv("POSTGRES_DB"):
    os.environ["POSTGRES_DB"] = "knowme"

# Now import app modules
from app.db.session import SessionLocal
from app.services.analytics.financial_analytics import financial_analytics_service
from app.domains.core.models.property import Property
from sqlalchemy import select

async def main():
    print("🚀 Starting Financial Analysis Verification")
    async with SessionLocal() as db:
        # Find a property to test
        stmt = select(Property).limit(5)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        target_prop = None
        for p in properties:
            if p.external_data and p.external_data.get('financial_history'):
                target_prop = p
                break
        
        if not target_prop:
            print("❌ No property with financial history found using first available.")
            target_prop = properties[0] if properties else None
            
        if not target_prop:
             print("❌ No properties found in DB.")
             return

        print(f"📊 Testing Analysis for: {target_prop.name}")
        
        print("\n--- 1. History ---")
        history = await financial_analytics_service.get_property_financial_history(db, str(target_prop.property_id))
        print(f"Found {len(history) if history else 0} historical data points")

        print("\n--- 2. Forecast ---")
        try:
            forecast = await financial_analytics_service.forecast_future_costs(db, str(target_prop.property_id))
            print("Result:", forecast)
        except ImportError:
            print("❌ scikit-learn not found")
        except Exception as e:
            print(f"❌ Forecast Error: {e}")

        print("\n--- 3. Anomalies ---")
        try:
            anomalies = await financial_analytics_service.detect_spending_anomalies(db, str(target_prop.property_id))
            print("Result:", anomalies)
        except Exception as e:
            print(f"❌ Anomaly Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
