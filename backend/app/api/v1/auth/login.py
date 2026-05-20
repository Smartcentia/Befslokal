from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api import deps
from app.domains.core.models.user import User
from app.core.security.pwd import verify_password


from datetime import timedelta
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

from typing import Optional

class LoginResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    detail: Optional[str] = None
    assigned_property_ids: Optional[list[str]] = None

@router.post("/validate-credentials", response_model=LoginResponse)
async def validate_credentials(
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Validate user credentials (email/password) for NextAuth.
    This endpoint is called by the NextAuth 'authorize' callback.
    """
    try:
        # Normalize email
        email = login_data.email.lower().strip()
        
        # Fetch user
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Login failed: User {email} not found")
            return LoginResponse(success=False, detail="Invalid credentials")
            
        if not user.is_active:
             logger.warning(f"Login failed: User {email} is inactive")
             return LoginResponse(success=False, detail="User account is inactive")

        # Verify password
        if not user.hashed_password:
             logger.warning(f"Login failed: User {email} has no password set")
             return LoginResponse(success=False, detail="Invalid credentials")
             
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Login failed: Invalid password for {email}")
            return LoginResponse(success=False, detail="Invalid credentials")
            
        # Success! Return user data necessary for NextAuth session
        user_data = {
            "id": str(user.user_id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "mfa_verified": False, # Always starts as False upon login
            "mfa_enabled": user.mfa_enabled,
            "assigned_properties": [str(p.property_id) for p in user.properties] if user.properties else []
        }
        
        logger.info(f"Credentials validated for user {email}")
        return LoginResponse(success=True, user=user_data)
        
    except Exception as e:
        logger.error(f"Error validating credentials: {e}")
        return LoginResponse(success=False, detail=str(e))
