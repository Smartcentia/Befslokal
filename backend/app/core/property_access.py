"""
Property Access Control Helper

Provides functions to check and filter property access based on user roles:
- ADMIN: Access to all properties
- REGIONAL_MANAGER: Access to properties in their region
- PROPERTY_MANAGER: Access to assigned properties (via user_property_association)
- TENANT: Read-only access to assigned properties
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from fastapi import HTTPException, status

from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property
from app.domains.core.models.user import user_property_association


async def check_property_access(
    db: AsyncSession,
    user: User,
    property_id: str,
    require_write: bool = False
) -> Property:
    """
    Check if user has access to a property.
    
    Rules:
    - ADMIN: Access to all properties
    - REGIONAL_MANAGER: Access to properties in their region
    - PROPERTY_MANAGER: Access to assigned properties (via user_property_association)
    - TENANT: Read-only access to assigned properties
    
    Args:
        db: Database session
        user: Current user
        property_id: Property ID to check access for
        require_write: If True, requires write access (TENANT cannot write)
    
    Returns:
        Property object if access granted
        
    Raises:
        HTTPException(404) if property not found
        HTTPException(403) if access denied
    """
    # Convert property_id to UUID if it's a string
    try:
        property_uuid = UUID(property_id) if isinstance(property_id, str) else property_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid property ID format"
        )
    
    # Get property
    stmt = select(Property).where(Property.property_id == property_uuid)
    result = await db.execute(stmt)
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # ADMIN has access to everything
    # Check both enum and string comparison (case-insensitive) for safety
    user_role_str = str(user.role).upper() if user.role else ""
    if user.role == UserRole.ADMIN or user_role_str == "ADMIN":
        return property_obj
    
    # REGIONAL_MANAGER has access to properties in their region
    if user.role == UserRole.REGIONAL_MANAGER:
        if user.region and property_obj.region == user.region:
            return property_obj
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Property not in your region"
        )
    
    # PROPERTY_MANAGER and JANITOR: Check user_property_association
    if user.role in [UserRole.PROPERTY_MANAGER, UserRole.JANITOR]:
        # Check if user is assigned to this property
        stmt = select(user_property_association).where(
            user_property_association.c.user_id == user.user_id,
            user_property_association.c.property_id == property_uuid
        )
        result = await db.execute(stmt)
        assignment = result.first()
        
        if assignment:
            # JANITOR has read-only access (vaktmester)
            if user.role == UserRole.JANITOR and require_write:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Janitors have read-only access"
                )
            return property_obj
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not assigned to this property"
        )
    
    # Default: Deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Insufficient permissions"
    )


async def filter_properties_by_access(
    db: AsyncSession,
    user: User,
    properties: List[Property]
) -> List[Property]:
    """
    Filter a list of properties based on user access.
    
    Returns only properties the user has access to.
    
    Args:
        db: Database session
        user: Current user
        properties: List of properties to filter
    
    Returns:
        Filtered list of properties user has access to
    """
    if not properties:
        return []
    
    # ADMIN has access to everything
    user_role_val = getattr(user.role, "value", str(user.role))
    user_role_str = str(user_role_val).upper()
    
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Checking Access: User={user.email}, Role={user.role} (Parsed: {user_role_str}), Region={user.region}")

    if user.role == UserRole.ADMIN or user_role_str == "ADMIN":
        return properties

    # REGIONAL_MANAGER has access to properties in their region
    if user.role == UserRole.REGIONAL_MANAGER or user_role_str == "REGIONAL_MANAGER":
        if user.region:
            filtered = [p for p in properties if p.region == user.region]
            return filtered
        logger.warning(f"Access Denied: REGIONAL_MANAGER {user.email} has no region set")
        return []

    # PROPERTY_MANAGER and JANITOR: Check user_property_association
    if user.role in [UserRole.PROPERTY_MANAGER, UserRole.JANITOR] or user_role_str in ["PROPERTY_MANAGER", "JANITOR"]:
        # Get all property IDs user is assigned to
        stmt = select(user_property_association.c.property_id).where(
            user_property_association.c.user_id == user.user_id
        )
        result = await db.execute(stmt)
        allowed_property_ids = {row[0] for row in result}

        filtered = [p for p in properties if p.property_id in allowed_property_ids]
        return filtered

    logger.warning(f"Access Denied: User {user.email} with role {user.role} has no matching filters")
    # Default: No access
    return []


async def get_user_accessible_property_ids(
    db: AsyncSession,
    user: User
) -> set:
    """
    Get set of property IDs that the user has access to.

    Useful for filtering queries at the database level.

    Args:
        db: Database session
        user: Current user

    Returns:
        Set of property UUIDs user has access to
    """
    # ADMIN has access to everything - return None to indicate "all"
    # Also catches admins who are simulating a lower role (flagged by get_current_user)
    user_role_str = str(user.role).upper() if user.role else ""
    is_real_admin = (
        user.role == UserRole.ADMIN
        or user_role_str == "ADMIN"
        or getattr(user, "_is_admin_simulating", False)
    )
    if is_real_admin:
        return None  # None means "all properties"
    
    # REGIONAL_MANAGER: Get properties in their region
    if user.role == UserRole.REGIONAL_MANAGER:
        if not user.region:
            return set()
        stmt = select(Property.property_id).where(Property.region == user.region)
        result = await db.execute(stmt)
        return {row[0] for row in result}
    
    # PROPERTY_MANAGER and JANITOR: Get assigned properties
    if user.role in [UserRole.PROPERTY_MANAGER, UserRole.JANITOR]:
        stmt = select(user_property_association.c.property_id).where(
            user_property_association.c.user_id == user.user_id
        )
        result = await db.execute(stmt)
        return {row[0] for row in result}
    
    # Default: No access
    return set()
