import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.services.risk.external_risk_service import ExternalRiskService
from app.services.external.api_clients.lovdata_client import LovdataClient

async def main():
    print("--- Verifying External Services ---")
    
    # 1. Verify Config
    print(f"Lovdata API Key Present: {'Yes' if settings.LOVDATA_API_KEY else 'No'}")
    print(f"NVE API Key Present: {'Yes' if settings.NVE_API_KEY else 'No'}")
    
    # 2. Verify ExternalRiskService
    try:
        risk_service = ExternalRiskService()
        print("✅ ExternalRiskService instantiated successfully.")
        
        # Mock assessment
        print("Testing assess_property_risk structure...")
        # We won't actually call external APIs to avoid hitting limits/errors in this restricted env,
        # but we check if the method exists and runs without immediate error on instantiation.
        # To truly test we'd need to mock the clients or allow network calls.
        # For now, let's just check the class structure.
        import inspect
        if inspect.iscoroutinefunction(risk_service.assess_property_risk):
             print("✅ assess_property_risk is an async function.")
        else:
             print("❌ assess_property_risk is NOT an async function.")
             
    except Exception as e:
        print(f"❌ ExternalRiskService instantiation failed: {e}")

    # 3. Verify LovdataClient
    try:
        lovdata = LovdataClient()
        print("✅ LovdataClient instantiated successfully.")
    except Exception as e:
        print(f"❌ LovdataClient instantiation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
