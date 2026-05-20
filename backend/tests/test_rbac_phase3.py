"""
Test Phase 3: Region-Based Access Control Validation

Tests for REGIONAL_MANAGER logic to ensure region filtering works correctly.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from fastapi import HTTPException

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
    return AsyncMock()


@pytest.fixture
def admin_user():
    """Admin user."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.ADMIN
    user.region = None
    return user


@pytest.fixture
def regional_manager_user():
    """Regional manager user."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.REGIONAL_MANAGER
    user.region = "02 - Øst"
    return user


@pytest.fixture
def property_manager_user():
    """Property manager user."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.PROPERTY_MANAGER
    user.region = None
    return user


@pytest.fixture
def property_east():
    """Property in Øst region."""
    prop = MagicMock(spec=Property)
    prop.property_id = uuid4()
    prop.region = "02 - Øst"
    return prop


@pytest.fixture
def property_vest():
    """Property in Vest region."""
    prop = MagicMock(spec=Property)
    prop.property_id = uuid4()
    prop.region = "04 - Vest"
    return prop


@pytest.mark.asyncio
async def test_regional_manager_access_same_region(mock_db, regional_manager_user, property_east):
    """Test REGIONAL_MANAGER can access properties in their region."""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = property_east
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Test access
    result = await check_property_access(
        db=mock_db,
        user=regional_manager_user,
        property_id=str(property_east.property_id),
        require_write=False
    )
    
    assert result == property_east
    assert regional_manager_user.region == property_east.region


@pytest.mark.asyncio
async def test_regional_manager_access_different_region(mock_db, regional_manager_user, property_vest):
    """Test REGIONAL_MANAGER cannot access properties in different region."""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = property_vest
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Test access - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=regional_manager_user,
            property_id=str(property_vest.property_id),
            require_write=False
        )
    
    assert exc_info.value.status_code == 403
    assert "region" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_regional_manager_no_region(mock_db):
    """Test REGIONAL_MANAGER without region set cannot access properties."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.REGIONAL_MANAGER
    user.region = None  # No region set
    
    property_east = MagicMock(spec=Property)
    property_east.property_id = uuid4()
    property_east.region = "02 - Øst"
    
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = property_east
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Test access - should raise 403
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=user,
            property_id=str(property_east.property_id),
            require_write=False
        )
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_filter_properties_by_access_regional_manager(mock_db, regional_manager_user):
    """Test filter_properties_by_access filters correctly for REGIONAL_MANAGER."""
    # Create properties in different regions
    prop_east1 = MagicMock(spec=Property)
    prop_east1.property_id = uuid4()
    prop_east1.region = "02 - Øst"
    
    prop_east2 = MagicMock(spec=Property)
    prop_east2.property_id = uuid4()
    prop_east2.region = "02 - Øst"
    
    prop_vest = MagicMock(spec=Property)
    prop_vest.property_id = uuid4()
    prop_vest.region = "04 - Vest"
    
    properties = [prop_east1, prop_east2, prop_vest]
    
    # Filter
    result = await filter_properties_by_access(
        db=mock_db,
        user=regional_manager_user,
        properties=properties
    )
    
    # Should only return properties in Øst region
    assert len(result) == 2
    assert prop_east1 in result
    assert prop_east2 in result
    assert prop_vest not in result


@pytest.mark.asyncio
async def test_get_user_accessible_property_ids_regional_manager(mock_db, regional_manager_user):
    """Test get_user_accessible_property_ids for REGIONAL_MANAGER."""
    # Mock properties in Øst region
    prop_east1_id = uuid4()
    prop_east2_id = uuid4()
    
    # Mock database query result
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([
        (prop_east1_id,),
        (prop_east2_id,)
    ]))
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Get accessible property IDs
    result = await get_user_accessible_property_ids(mock_db, regional_manager_user)
    
    # Should return set with property IDs in Øst region
    assert isinstance(result, set)
    assert prop_east1_id in result
    assert prop_east2_id in result


@pytest.mark.asyncio
async def test_get_user_accessible_property_ids_regional_manager_no_region(mock_db):
    """Test get_user_accessible_property_ids for REGIONAL_MANAGER without region."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.REGIONAL_MANAGER
    user.region = None  # No region set
    
    # Get accessible property IDs
    result = await get_user_accessible_property_ids(mock_db, user)
    
    # Should return empty set
    assert result == set()


@pytest.mark.asyncio
async def test_regional_manager_write_access(mock_db, regional_manager_user, property_east):
    """Test REGIONAL_MANAGER can write to properties in their region."""
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = property_east
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Test write access
    result = await check_property_access(
        db=mock_db,
        user=regional_manager_user,
        property_id=str(property_east.property_id),
        require_write=True
    )
    
    # REGIONAL_MANAGER should have write access to properties in their region
    assert result == property_east


@pytest.mark.asyncio
async def test_region_case_sensitivity(mock_db):
    """Test that region matching is case-sensitive (current implementation)."""
    user = MagicMock(spec=User)
    user.user_id = uuid4()
    user.role = UserRole.REGIONAL_MANAGER
    user.region = "02 - Øst"  # Exact match
    
    prop = MagicMock(spec=Property)
    prop.property_id = uuid4()
    prop.region = "02 - øst"  # Lowercase
    
    # Mock database query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = prop
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    # Test access - should fail due to case mismatch
    with pytest.raises(HTTPException) as exc_info:
        await check_property_access(
            db=mock_db,
            user=user,
            property_id=str(prop.property_id),
            require_write=False
        )
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_bypasses_region_check(mock_db, admin_user, property_east, property_vest):
    """Test ADMIN can access properties regardless of region."""
    # Mock database query for property_east
    mock_result_east = MagicMock()
    mock_result_east.scalar_one_or_none.return_value = property_east
    mock_db.execute = AsyncMock(return_value=mock_result_east)
    
    # Test access to property in Øst
    result = await check_property_access(
        db=mock_db,
        user=admin_user,
        property_id=str(property_east.property_id),
        require_write=False
    )
    assert result == property_east
    
    # Mock database query for property_vest
    mock_result_vest = MagicMock()
    mock_result_vest.scalar_one_or_none.return_value = property_vest
    mock_db.execute = AsyncMock(return_value=mock_result_vest)
    
    # Test access to property in Vest
    result = await check_property_access(
        db=mock_db,
        user=admin_user,
        property_id=str(property_vest.property_id),
        require_write=False
    )
    assert result == property_vest
