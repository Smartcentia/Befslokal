import jwt
import logging
from typing import Optional, Dict
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenValidator:
    """
    Validates JWT tokens using shared secret (NextAuth/HS256).

    """
    def __init__(self):
        pass

    async def verify_token(self, token: str) -> Dict:
        """
        Verifies the JWT token signature using the application's SECRET_KEY.
        """
        try:
            if not token:
                raise Exception("Token cannot be None/Empty")

            # Remove 'Bearer ' prefix if present
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            # 1. Try Shared Secret (NextAuth/HS256)
            if settings.SECRET_KEY:
                try:
                    # Attempt decode with HS256
                    decoded = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"],
                        options={
                            "verify_signature": True,
                            "verify_exp": True,
                            "verify_aud": False, # NextAuth tokens might not have audience
                            "verify_iss": False, 
                        }
                    )
                    # Validate that email exists and is valid
                    email = decoded.get("email")
                    if not email or "@" not in str(email):
                        # If email is missing, try sub as fallback (should be email after normalization)
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

            # 2. Dev Bypass (Only if NO other validation succeeded)
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

