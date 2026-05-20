from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.domains.core.models.user import User, UserRole
from pydantic import BaseModel

router = APIRouter()

from typing import List, Optional
from sqlalchemy.future import select
from app.db.session import SessionLocal

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    role: str
    region: Optional[str] = None
    email_verified: bool = False
    mfa_enabled: bool = True
    mfa_verified_at: Optional[str] = None
    is_active: bool = True

@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the current authenticated user profile.
    """
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "name": current_user.name or "Ukjent Bruker",
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "region": current_user.region,
        "email_verified": current_user.email_verified,
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_verified_at": current_user.mfa_verified_at.isoformat() if current_user.mfa_verified_at else None,
        "is_active": getattr(current_user, "is_active", True),
    }

@router.get("/", response_model=List[UserProfile])
async def list_users(current_user: User = Depends(get_current_user)):
    """
    List all users (Admin only).
    """
    # Faktisk sjekk - kun ADMIN kan liste alle brukere
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list all users"
        )

    async with SessionLocal() as db:
        stmt = select(User).where(User.is_active == True).order_by(User.email)
        result = await db.execute(stmt)
        users = result.scalars().all()
    
    return [
        {
            "user_id": str(u.user_id),
            "email": u.email,
            "name": u.name,
            "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
            "region": u.region,
            "email_verified": u.email_verified,
            "mfa_enabled": u.mfa_enabled,
            "mfa_verified_at": u.mfa_verified_at.isoformat() if u.mfa_verified_at else None,
            "is_active": getattr(u, "is_active", True),
        }
        for u in users
    ]
