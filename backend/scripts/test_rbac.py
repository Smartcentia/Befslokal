#!/usr/bin/env python3
"""
Quick RBAC test script.

Kjører grunnleggende tester for å verifisere at RBAC implementeringen fungerer.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domains.core.models.user import User, UserRole
from app.api.deps import get_current_active_superuser
from fastapi import HTTPException


def test_user_role_enum():
    """Test UserRole enum."""
    print("Testing UserRole enum...")
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.REGIONAL_MANAGER.value == "REGIONAL_MANAGER"
    assert UserRole.PROPERTY_MANAGER.value == "PROPERTY_MANAGER"
    assert UserRole.JANITOR.value == "JANITOR"
    print("✅ UserRole enum OK")


def test_role_comparison():
    """Test role comparison."""
    print("Testing role comparison...")
    user = User()
    user.role = UserRole.ADMIN
    
    assert user.role == UserRole.ADMIN
    assert user.role != UserRole.PROPERTY_MANAGER
    print("✅ Role comparison OK")


async def test_get_current_active_superuser():
    """Test get_current_active_superuser."""
    print("Testing get_current_active_superuser...")
    
    # Test admin access
    admin_user = User()
    admin_user.role = UserRole.ADMIN
    result = await get_current_active_superuser(current_user=admin_user)
    assert result == admin_user
    print("✅ Admin access OK")
    
    # Test non-admin denied
    pm_user = User()
    pm_user.role = UserRole.PROPERTY_MANAGER
    try:
        await get_current_active_superuser(current_user=pm_user)
        print("❌ ERROR: Non-admin should be denied!")
        return False
    except HTTPException as e:
        assert e.status_code == 403
        print("✅ Non-admin correctly denied")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("RBAC Quick Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test enum
        test_user_role_enum()
        print()
        
        # Test comparison
        test_role_comparison()
        print()
        
        # Test superuser function
        import asyncio
        success = asyncio.run(test_get_current_active_superuser())
        print()
        
        if success:
            print("=" * 60)
            print("✅ All basic tests passed!")
            print("=" * 60)
            return 0
        else:
            print("=" * 60)
            print("❌ Some tests failed!")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
