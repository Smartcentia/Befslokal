"""
Admin endpoint to manage users: create, read, update, delete (soft), roles, property assignments.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User, UserRole, user_property_association

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    role: UserRole
    region: Optional[str] = None
    property_ids: Optional[List[UUID]] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    region: Optional[str] = None
    property_ids: Optional[List[UUID]] = None  # None = don't change, [] = remove all


class UserRoleUpdate(BaseModel):
    user_id: UUID
    new_role: UserRole


def _require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )


async def _set_user_properties(db: AsyncSession, user_id: UUID, property_ids: List[UUID]) -> None:
    """Replace user's property assignments."""
    await db.execute(delete(user_property_association).where(user_property_association.c.user_id == user_id))
    for pid in property_ids:
        await db.execute(user_property_association.insert().values(user_id=user_id, property_id=pid))


@router.get("/users", response_model=List[dict])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users. Only ADMIN."""
    _require_admin(current_user)

    result = await db.execute(select(User).order_by(User.email))
    users = result.scalars().all()

    return [
        {
            "user_id": str(u.user_id),
            "email": u.email,
            "name": u.name,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "region": u.region,
            "email_verified": u.email_verified,
            "mfa_enabled": u.mfa_enabled,
            "is_active": getattr(u, "is_active", True),
        }
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user. Only ADMIN."""
    _require_admin(current_user)

    # Check email unique
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    user = User(
        email=data.email,
        name=data.name or data.email.split("@")[0],
        role=data.role,
        region=data.region,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    if data.property_ids and data.role in (UserRole.PROPERTY_MANAGER, UserRole.JANITOR):
        await _set_user_properties(db, user.user_id, data.property_ids)

    await db.commit()
    await db.refresh(user)

    return {
        "message": "User created successfully",
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single user with property assignments. Only ADMIN."""
    _require_admin(current_user)

    result = await db.execute(
        select(User).where(User.user_id == user_id).options(selectinload(User.properties))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "region": user.region,
        "email_verified": user.email_verified,
        "mfa_enabled": user.mfa_enabled,
        "is_active": getattr(user, "is_active", True),
        "property_ids": [str(p.property_id) for p in user.properties] if user.properties else [],
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user. Only ADMIN."""
    _require_admin(current_user)

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        user.role = data.role
    if data.region is not None:
        user.region = data.region

    if data.property_ids is not None:
        if user.role in (UserRole.PROPERTY_MANAGER, UserRole.JANITOR):
            await _set_user_properties(db, user_id, data.property_ids)

    await db.commit()
    await db.refresh(user)

    return {
        "message": "User updated successfully",
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a user (set is_active=false). Only ADMIN."""
    _require_admin(current_user)

    if user_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.commit()

    return {"message": "User deactivated successfully", "user_id": str(user_id)}


@router.post("/users/update-role")
async def update_user_role(
    update: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user's role. Only ADMIN. (Legacy endpoint - use PATCH /users/{id} instead.)"""
    _require_admin(current_user)

    result = await db.execute(select(User).where(User.user_id == update.user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_role = target_user.role
    target_user.role = update.new_role
    await db.commit()

    return {
        "message": "Role updated successfully",
        "user_email": target_user.email,
        "old_role": old_role.value,
        "new_role": target_user.role.value,
    }


@router.get("/users/me/role")
async def get_my_role(current_user: User = Depends(get_current_user)):
    """Get current user's role."""
    return {
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "user_id": str(current_user.user_id),
    }
