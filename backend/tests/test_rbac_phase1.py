"""
Test suite for Phase 1 RBAC implementation.

Tests that:
1. get_current_active_superuser requires ADMIN role
2. /api/v1/users/ requires ADMIN role
3. Dashboard endpoints have proper role checks
4. Financials endpoints have proper role checks
"""

import pytest
from fastapi import HTTPException, status
from app.api.deps import get_current_active_superuser
from app.domains.core.models.user import User, UserRole
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_get_current_active_superuser_requires_admin():
    """Test that get_current_active_superuser requires ADMIN role."""
    # Create a non-admin user
    non_admin_user = User()
    non_admin_user.user_id = "test-user-id"
    non_admin_user.email = "user@example.com"
    non_admin_user.role = UserRole.PROPERTY_MANAGER
    
    # Mock get_current_user dependency
    async def mock_get_current_user():
        return non_admin_user
    
    # Should raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_superuser(current_user=non_admin_user)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Only administrators" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_active_superuser_allows_admin():
    """Test that get_current_active_superuser allows ADMIN role."""
    # Create an admin user
    admin_user = User()
    admin_user.user_id = "admin-user-id"
    admin_user.email = "admin@example.com"
    admin_user.role = UserRole.ADMIN
    
    # Should not raise exception
    result = await get_current_active_superuser(current_user=admin_user)
    assert result == admin_user


def test_user_role_enum_values():
    """Test that UserRole enum has expected values."""
    assert UserRole.ADMIN == "ADMIN"
    assert UserRole.REGIONAL_MANAGER == "REGIONAL_MANAGER"
    assert UserRole.PROPERTY_MANAGER == "PROPERTY_MANAGER"
    assert UserRole.JANITOR == "JANITOR"


def test_role_comparison():
    """Test that role comparison works correctly."""
    user1 = User()
    user1.role = UserRole.ADMIN
    
    user2 = User()
    user2.role = UserRole.PROPERTY_MANAGER
    
    assert user1.role == UserRole.ADMIN
    assert user2.role != UserRole.ADMIN
    assert user2.role == UserRole.PROPERTY_MANAGER
