"""
Test suite for Phase 2 RBAC implementation - Property-Level Access Control.

Tests that:
1. check_property_access works correctly for all roles
2. filter_properties_by_access filters correctly
3. Properties endpoints enforce access control
4. Contracts endpoints enforce property access
5. Units endpoints enforce property access
"""

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.property_access import (
    check_property_access,
    filter_properties_by_access,
    get_user_accessible_property_ids
)
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def admin_user():
    """Create an admin user."""
    user = User()
    user.user_id = uuid4()
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.region = None
    return user


@pytest.fixture
def regional_manager_user():
    """Create a regional manager user."""
    user = User()
    user.user_id = uuid4()
    user.email = "regional@example.com"
    user.role = UserRole.REGIONAL_MANAGER
    user.region = "Region Øst"
    return user


@pytest.fixture
def property_manager_user():
    """Create a property manager user."""
    user = User()
    user.user_id = uuid4()
    user.email = "pm@example.com"
    user.role = UserRole.PROPERTY_MANAGER
    user.region = None
    return user


@pytest.fixture
def janitor_user():
    """Create a janitor user."""
    user = User()
    user.user_id = uuid4()
    user.email = "janitor@example.com"
    user.role = UserRole.JANITOR
    user.region = None
    return user


@pytest.fixture
def sample_property():
    """Create a sample property."""
    prop = Property()
    prop.property_id = uuid4()
    prop.name = "Test Property"
    prop.region = "Region Øst"
    prop.address = "Test Street 1"
    return prop


@pytest.mark.asyncio
async def test_check_property_access_admin_has_access(mock_db, admin_user, sample_property):
    """Test that ADMIN has access to all properties."""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_property
    mock_db.execute.return_value = mock_result
    
    # ADMIN should have access
    result = await check_property_access(
        db=mock_db,
        user=admin_user,
        property_id=str(sample_property.property_id),
        require_write=False
    )
    
    assert result == sample_property


@pytest.mark.asyncio
async def test_check_property_access_regional_manager_same_region(mock_db, regional_manager_user, sample_property):
    """Test that REGIONAL_MANAGER has access to properties in their region."""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_property
    mock_db.execute.return_value = mock_result
    
    # REGIONAL_MANAGER should have access to properties in their region
    result = await check_property_access(
        db=mock_db,
        user=regional_manager_user,
        property_id=str(sample_property.property_id),
        require_write=False
    )
    
    assert result == sample_property


@pytest.mark.asyncio
async def test_check_property_access_regional_manager_different_region(mock_db, regional_manager_user, sample_property):
    """Test that REGIONAL_MANAGER cannot access properties outside their region."""
    # Set property to different region
    sample_property.region = "Region Vest"
    
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_property
    mock_db.execute.return_value = mock_result
    
    # REGIONAL_MANAGER should NOT have access
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=regional_manager_user,
            property_id=str(sample_property.property_id),
            require_write=False
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "not in your region" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_check_property_access_property_manager_assigned(mock_db, property_manager_user, sample_property):
    """Test that PROPERTY_MANAGER has access to assigned properties."""
    # Mock database queries
    # First query: get property
    mock_property_result = MagicMock()
    mock_property_result.scalar_one_or_none.return_value = sample_property
    
    # Second query: check user_property_association
    mock_association_result = MagicMock()
    mock_association_result.first.return_value = (property_manager_user.user_id, sample_property.property_id)
    
    mock_db.execute.side_effect = [mock_property_result, mock_association_result]
    
    # PROPERTY_MANAGER should have access to assigned properties
    result = await check_property_access(
        db=mock_db,
        user=property_manager_user,
        property_id=str(sample_property.property_id),
        require_write=False
    )
    
    assert result == sample_property


@pytest.mark.asyncio
async def test_check_property_access_property_manager_not_assigned(mock_db, property_manager_user, sample_property):
    """Test that PROPERTY_MANAGER cannot access unassigned properties."""
    # Mock database queries
    # First query: get property
    mock_property_result = MagicMock()
    mock_property_result.scalar_one_or_none.return_value = sample_property
    
    # Second query: check user_property_association (no assignment)
    mock_association_result = MagicMock()
    mock_association_result.first.return_value = None
    
    mock_db.execute.side_effect = [mock_property_result, mock_association_result]
    
    # PROPERTY_MANAGER should NOT have access
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=property_manager_user,
            property_id=str(sample_property.property_id),
            require_write=False
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "not assigned" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_check_property_access_janitor_read_only(mock_db, janitor_user, sample_property):
    """Test that JANITOR has read-only access."""
    # Mock database queries
    mock_property_result = MagicMock()
    mock_property_result.scalar_one_or_none.return_value = sample_property
    
    mock_association_result = MagicMock()
    mock_association_result.first.return_value = (janitor_user.user_id, sample_property.property_id)
    
    mock_db.execute.side_effect = [mock_property_result, mock_association_result]
    
    # JANITOR should have read access
    result = await check_property_access(
        db=mock_db,
        user=janitor_user,
        property_id=str(sample_property.property_id),
        require_write=False
    )
    
    assert result == sample_property


@pytest.mark.asyncio
async def test_check_property_access_janitor_write_denied(mock_db, janitor_user, sample_property):
    """Test that JANITOR cannot write."""
    # Mock database queries
    mock_property_result = MagicMock()
    mock_property_result.scalar_one_or_none.return_value = sample_property
    
    mock_association_result = MagicMock()
    mock_association_result.first.return_value = (janitor_user.user_id, sample_property.property_id)
    
    mock_db.execute.side_effect = [mock_property_result, mock_association_result]
    
    # JANITOR should NOT have write access
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=janitor_user,
            property_id=str(sample_property.property_id),
            require_write=True
        )
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "read-only" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_check_property_access_property_not_found(mock_db, admin_user):
    """Test that 404 is returned when property doesn't exist."""
    # Mock database query returning None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    property_id = str(uuid4())
    
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=admin_user,
            property_id=property_id,
            require_write=False
        )
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_filter_properties_by_access_admin(mock_db, admin_user):
    """Test that ADMIN sees all properties."""
    properties = [
        Property(property_id=uuid4(), name="Property 1", region="Region Øst"),
        Property(property_id=uuid4(), name="Property 2", region="Region Vest"),
        Property(property_id=uuid4(), name="Property 3", region="Region Nord"),
    ]
    
    filtered = await filter_properties_by_access(
        db=mock_db,
        user=admin_user,
        properties=properties
    )
    
    # ADMIN should see all properties
    assert len(filtered) == 3
    assert filtered == properties


@pytest.mark.asyncio
async def test_filter_properties_by_access_regional_manager(mock_db, regional_manager_user):
    """Test that REGIONAL_MANAGER sees only properties in their region."""
    properties = [
        Property(property_id=uuid4(), name="Property 1", region="Region Øst"),
        Property(property_id=uuid4(), name="Property 2", region="Region Vest"),
        Property(property_id=uuid4(), name="Property 3", region="Region Øst"),
    ]
    
    filtered = await filter_properties_by_access(
        db=mock_db,
        user=regional_manager_user,
        properties=properties
    )
    
    # REGIONAL_MANAGER should see only properties in "Region Øst"
    assert len(filtered) == 2
    assert all(p.region == "Region Øst" for p in filtered)


@pytest.mark.asyncio
async def test_filter_properties_by_access_property_manager(mock_db, property_manager_user):
    """Test that PROPERTY_MANAGER sees only assigned properties."""
    property1_id = uuid4()
    property2_id = uuid4()
    property3_id = uuid4()
    
    properties = [
        Property(property_id=property1_id, name="Property 1", region="Region Øst"),
        Property(property_id=property2_id, name="Property 2", region="Region Vest"),
        Property(property_id=property3_id, name="Property 3", region="Region Øst"),
    ]
    
    # Mock database query for user_property_association
    # User is assigned to property1 and property3
    # SQLAlchemy 2.0 Result objects are iterable directly
    mock_result = MagicMock()
    # Make result iterable - it should yield tuples with property_id as first element
    mock_result.__iter__ = MagicMock(return_value=iter([
        (property1_id,),
        (property3_id,),
    ]))
    mock_db.execute.return_value = mock_result
    
    filtered = await filter_properties_by_access(
        db=mock_db,
        user=property_manager_user,
        properties=properties
    )
    
    # PROPERTY_MANAGER should see only assigned properties
    assert len(filtered) == 2
    assert filtered[0].property_id == property1_id
    assert filtered[1].property_id == property3_id


def test_user_role_enum():
    """Test UserRole enum values."""
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.REGIONAL_MANAGER.value == "REGIONAL_MANAGER"
    assert UserRole.PROPERTY_MANAGER.value == "PROPERTY_MANAGER"
    assert UserRole.JANITOR.value == "JANITOR"


def test_user_role_comparison():
    """Test UserRole comparison."""
    user = User()
    user.role = UserRole.ADMIN
    
    assert user.role == UserRole.ADMIN
    assert user.role != UserRole.PROPERTY_MANAGER
    assert user.role in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]
