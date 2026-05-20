from typing import AsyncGenerator, Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError, TimeoutError as SATimeoutError
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole
from sqlalchemy import text
from app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)
from starlette.requests import Request
from contextlib import asynccontextmanager

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency with reconnect handling.
    
    NOTE: This uses a simpler pattern to avoid "generator didn't stop after athrow()"
    errors that occur with BaseHTTPMiddleware + async generators.
    """
    # pool_pre_ping=True on the engine already validates connections before use,
    # so no explicit SELECT 1 probe is needed here. Just acquire and yield.
    db: Optional[AsyncSession] = None
    try:
        db = SessionLocal()
        yield db
    except SATimeoutError as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection pool exhausted. Please retry shortly."
        ) from e
    finally:
        if db is not None:
            await db.close()

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Retrieves the current user based on the authentication state set by AuthMiddleware.
    """
    user_data = getattr(request.state, "user", None)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    email = user_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data in token",
        )

    # Check for existing user in database (unngå tung properties-join lokalt)
    from sqlalchemy import select
    from sqlalchemy.orm import noload
    result = await db.execute(
        select(User).options(noload(User.properties)).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Ensure system user always has Admin role if bypass is used
    if user and email == "system@befs.no" and user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        await db.commit()
        logger.info("Upgraded existing system user to ADMIN role")

    if user and not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deactivated",
        )

    # Upgrade existing users to ADMIN if their email is in the admin list
    # (handles users migrated from legacy DB that may have wrong role)
    if user and user.role != UserRole.ADMIN:
        is_admin = (
            email in settings.ADMIN_EMAILS or
            email in ["admin@befs.no", "system@befs.no", "frankvevle@gmail.com", "frankvevle@hotmail.com"]
        )
        if is_admin:
            user.role = UserRole.ADMIN
            await db.commit()
            await db.refresh(user)
            logger.info("Upgraded existing user %s to ADMIN role (admin email list)", email)

    if not user:
        # Auto-create user for både Credentials og Google OAuth
        # Get user name from token if available, otherwise use email prefix
        user_name = user_data.get("name") or email.split("@")[0]
        
        # Determine role based on admin email list
        is_admin = (
            email in settings.ADMIN_EMAILS or 
            email in ["admin@befs.no", "system@befs.no", "frankvevle@gmail.com", "frankvevle@hotmail.com"]
        )
        
        user = User()
        user.user_id = uuid.uuid4()  # Generate new UUID for all users
        user.email = email
        user.name = user_name
        user.role = UserRole.ADMIN if is_admin else UserRole.PROPERTY_MANAGER
        user.email_verified = False  # New users must verify email
        user.mfa_enabled = True  # MFA enabled by default
        user.is_active = True

        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Auto-created user: %s (role: %s, email_verified: %s)", email, user.role, user.email_verified)

    # Apply simulated role if present (Admin only feature)
    simulated_role = user_data.get("simulated_role")
    if simulated_role and (user.role == UserRole.ADMIN or email in settings.ADMIN_EMAILS):
        try:
            # Map string role to enum
            if isinstance(simulated_role, str):
                # Handle potential case variations
                sim_role_upper = simulated_role.upper()
                if hasattr(UserRole, sim_role_upper):
                    # Preserve original admin status so access control can fall back correctly
                    user._is_admin_simulating = True
                    user.role = getattr(UserRole, sim_role_upper)
                    logger.info("Applied simulated role %s for user %s", user.role, email)
        except Exception as e:
            logger.warning("Failed to apply simulated role %s: %s", simulated_role, e)

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require ADMIN role for superuser access.
    Only administrators can access endpoints that use this dependency.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint"
        )
    return current_user

# Alias for compatibility
get_current_admin_user = get_current_active_superuser
