import asyncio
import sys
import os
import httpx
import json

# Ensure app is in pythonpath
sys.path.append(os.getcwd())

async def check_risk_api():
    # Test with a known company (Equinor - Low Risk)
    org_nr = "923609016" 
    
    print(f"Checking Risk Profile for {org_nr}...")
    
    # We will call the service directly to avoid needing a running server for this script
    from app.services.risk.risk_engine import risk_engine
    
    try:
        profile = await risk_engine.calculate_risk_score(org_nr)
        print("Risk Profile Calculated:")
        print(json.dumps(profile.to_dict(), indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")

    # MOCK SCENARIO: Simulate Bankruptcy
    print("\n--- Testing High Risk Scenario (Mock) ---")
    
    from app.services.external.brreg_service import brreg_service
    
    # Store original method
    original_method = brreg_service.get_kunngjoringer
    
    async def mock_get_kunngjoringer(org_nr):
        return [{
            "type": "Konkursåpning", 
            "dato": "2024-01-01",
            "beskrivelse": "Konkurs åpnet ved Oslo Tingrett.",
            "kilde": "Mock"
        }]
    
    # Patch
    brreg_service.get_kunngjoringer = mock_get_kunngjoringer
    
    try:
        profile = await risk_engine.calculate_risk_score("999999999") # Dummy orgnr
        print("Risk Profile (Mocked Bankruptcy):")
        print(json.dumps(profile.to_dict(), indent=2))
    except Exception as e:
        print(f"Mock Test Failed: {e}")
        
    # Restore
    brreg_service.get_kunngjoringer = original_method

if __name__ == "__main__":
    asyncio.run(check_risk_api())
