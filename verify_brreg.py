import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import settings
from app.services.external.brreg_service import BrregService
from app.services.auth.maskinporten_client import MaskinportenClient

async def main():
    print("--- Verifying Brreg & Maskinporten Integration ---")
    
    # 1. Verify Config Presence
    print(f"Brreg Username: {'Set' if settings.BRREG_KR_USERNAME else 'Missing/Default'}")
    print(f"Brreg Password: {'Set' if settings.BRREG_KR_PASSWORD else 'Missing/Default'}")
    print(f"Maskinporten Client ID: {'Set' if settings.RRH_MASKINPORTEN_CLIENT_ID else 'Missing'}")
    print(f"Maskinporten Key Path: {'Set' if settings.RRH_MASKINPORTEN_KEY_PATH else 'Missing'}")
    
    # 2. Verify Service Instantiation
    try:
        service = BrregService()
        print("✅ BrregService instantiated successfully.")
        
        # Check specific restricted methods exist
        import inspect
        if inspect.iscoroutinefunction(service.get_aarsregnskap):
             print("✅ get_aarsregnskap is an async function (Restricted - Basic Auth).")
        if inspect.iscoroutinefunction(service.get_reelle_rettighetshavere):
             print("✅ get_reelle_rettighetshavere is an async function (Restricted - Maskinporten).")
             
    except Exception as e:
        print(f"❌ BrregService instantiation failed: {e}")

    # 3. Verify MaskinportenClient
    try:
        # Just check class existence, not token fetch as that requires valid cert
        mp = MaskinportenClient()
        print("✅ MaskinportenClient class is available.")
        
        if not settings.RRH_MASKINPORTEN_KEY_PATH:
             print("⚠️  Maskinporten Key Path is missing. Token fetch will fail.")
        else:
             print("✅ Maskinporten Key Path is configured.")
             
    except Exception as e:
        print(f"❌ MaskinportenClient check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
