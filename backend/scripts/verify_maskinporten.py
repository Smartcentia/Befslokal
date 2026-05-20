
import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.auth.maskinporten_client import MaskinportenClient
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_maskinporten():
    print("--- Verifying Maskinporten Configuration ---")
    print(f"Current Working Directory: {os.getcwd()}")
    env_path = os.path.join(os.getcwd(), '.env')
    print(f"checking for .env at: {env_path} -> Exists: {os.path.exists(env_path)}")
    
    # Reload settings to be sure (though script run is fresh process)
    from app.core.config import settings
    
    client_id = settings.RRH_MASKINPORTEN_CLIENT_ID
    key_path = settings.RRH_MASKINPORTEN_KEY_PATH
    
    print(f"Raw Env Var 'RRH_MASKINPORTEN_CLIENT_ID': {os.environ.get('RRH_MASKINPORTEN_CLIENT_ID', 'Not Set in OS Env')}")
    print(f"Settings 'RRH_MASKINPORTEN_CLIENT_ID': {client_id}")
    print(f"Settings 'RRH_MASKINPORTEN_KEY_PATH': {key_path}")
    
    if not client_id or not key_path:
        print("\n❌ Cannot proceed without credentials.")
        return

    print("\nAttempting to load Private Key...")
    try:
        MaskinportenClient._load_private_key()
        print("✅ Private Key loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load Private Key: {e}")
        return

    print("\nAttempting to get Access Token...")
    token = await MaskinportenClient.get_access_token()
    
    if token:
        print("✅ Access Token obtained successfully!")
        print(f"Token preview: {token[:20]}...")
    else:
        print("❌ Failed to obtain Access Token.")

if __name__ == "__main__":
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_maskinporten())
