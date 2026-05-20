
import time
import jwt
import httpx
import uuid
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class MaskinportenClient:
    """
    Client for obtaining Access Tokens from Maskinporten via JWT Grant.
    """
    
    TOKEN_URL = "https://maskinporten.no/token" # Production
    # TOKEN_URL_TEST = "https://test.maskinporten.no/token" # Test
    
    _token_cache: Dict[str, Any] = {}

    @staticmethod
    def _load_private_key() -> str:
        """
        Loads the private key from settings. support file path or raw string.
        """
        key_path = settings.RRH_MASKINPORTEN_KEY_PATH
        if not key_path:
            raise ValueError("RRH_MASKINPORTEN_KEY_PATH is not set in settings")

        # Check if it's a file path
        try:
            with open(key_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            # Maybe it's the raw key content or base64?
            # For now, let's assume it might be raw key if file fails, 
            # or raise error if strict file path expected.
            # Given the env var name ends in _PATH, we warn.
            logger.warning(f"Could not open key path {key_path}. Treating as raw key content not implemented for safety.")
            raise

    @staticmethod
    def _create_jwt_assertion(client_id: str, scope: str, aud: str) -> str:
        private_key_pem = MaskinportenClient._load_private_key()
        
        now = int(time.time())
        expiry = now + 120 # 2 minutes validity for assertion
        
        headers = {
            "alg": "RS256",
            "typ": "JWT"
            # "kid": "might be needed if multiple certs"
        }
        
        payload = {
            "aud": aud,
            "iss": client_id,
            "scope": scope,
            "iat": now,
            "exp": expiry,
            "jti": str(uuid.uuid4())
        }
        
        encoded_jwt = jwt.encode(payload, private_key_pem, algorithm="RS256", headers=headers)
        return encoded_jwt

    @staticmethod
    async def get_access_token(scope: Optional[str] = None) -> Optional[str]:
        client_id = settings.RRH_MASKINPORTEN_CLIENT_ID
        # Use provided scope or default to settings (RRH)
        scope = scope or settings.RRH_MASKINPORTEN_SCOPES or "brreg:reelle/offentlig"
        
        if not client_id:
            logger.error("RRH_MASKINPORTEN_CLIENT_ID is missing.")
            return None

        # Check cache
        cache_key = f"{client_id}:{scope}"
        cached = MaskinportenClient._token_cache.get(cache_key)
        if cached:
            if cached['expires_at'] > time.time() + 60: # Buffer
                return cached['access_token']

        # Determine Environment (Prod vs Test) - Ideally driven by config
        # Defaulting to Prod URL for now as per previous context
        aud = MaskinportenClient.TOKEN_URL

        try:
            grant = MaskinportenClient._create_jwt_assertion(client_id, scope, aud)
        except Exception as e:
            logger.error(f"Failed to create JWT assertion: {e}")
            return None

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": grant
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(aud, data=data, timeout=10.0)
            
            if resp.status_code == 200:
                token_data = resp.json()
                access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                
                # Cache it
                MaskinportenClient._token_cache[cache_key] = {
                    'access_token': access_token,
                    'expires_at': time.time() + expires_in
                }
                return access_token
            else:
                logger.error(f"Maskinporten Error {resp.status_code}: {resp.text}")
                return None
                
        except Exception as e:
            logger.error(f"Excpetion calling Maskinporten: {e}")
            return None
