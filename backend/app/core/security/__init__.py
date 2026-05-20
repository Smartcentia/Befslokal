import jwt
import logging
from typing import Optional, Dict
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenValidator:
    """
    Validates JWT tokens using Supabase JWT secret or shared secret (HS256).
    """
    def __init__(self):
        pass

    async def verify_token(self, token: str) -> Dict:
        """
        Verifies the JWT token signature.
        Tries Supabase JWT secret first, then falls back to SECRET_KEY.
        """
        try:
            if not token:
                raise Exception("Token cannot be None/Empty")

            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            # 1. Try Supabase JWT Secret (primary for Supabase auth)
            if settings.SUPABASE_JWT_SECRET:
                try:
                    decoded = jwt.decode(
                        token,
                        settings.SUPABASE_JWT_SECRET,
                        algorithms=["HS256"],
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_aud": False,
                            "verify_iss": False,
                        }
                    )
                    email = decoded.get("email")
                    if not email or "@" not in str(email):
                        user_meta = decoded.get("user_metadata") or {}
                        email = user_meta.get("email")
                    if not email or "@" not in str(email):
                        raise Exception("Invalid token: email missing or invalid")
                    # Supabase stores user role in app_metadata or user_metadata
                    app_meta = decoded.get("app_metadata", {})
                    user_meta = decoded.get("user_metadata", {})
                    role = app_meta.get("role") or user_meta.get("role") or "PROPERTY_MANAGER"
                    decoded["email"] = email
                    decoded["roles"] = [role]
                    return decoded
                except jwt.InvalidSignatureError:
                    pass  # Not a Supabase token, try next
                except jwt.DecodeError:
                    pass
                except Exception as e:
                    logger.warning("Supabase JWT check failed: %s", e)

            # 2. Try Shared Secret / legacy SECRET_KEY (HS256)
            if settings.SECRET_KEY:
                try:
                    decoded = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"],
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_aud": False,
                            "verify_iss": False,
                        }
                    )
                    email = decoded.get("email")
                    if not email or "@" not in str(email):
                        email = decoded.get("sub")
                        if not email or "@" not in str(email):
                            raise Exception("Invalid token: email missing or invalid")
                    decoded["email"] = email
                    return decoded
                except jwt.InvalidSignatureError:
                    raise Exception("Invalid signature")
                except jwt.DecodeError:
                    raise Exception("Decode error")
                except Exception as e:
                    logger.warning("HS256 check failed: %s", e)
                    raise

            # 3. Dev Bypass (Only if NO other validation succeeded)
            if settings.ENVIRONMENT == "development":
                return {"sub": "dev-user", "roles": ["admin"], "email": "dev@example.com"}

            raise Exception("Token verification failed (No valid method matched)")

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.warning("Token verification failed: %s", type(e).__name__)
            detail = "Invalid authentication credentials"
            if settings.ENVIRONMENT != "production":
                detail = f"{detail}. Error: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )

security_validator = TokenValidator()
