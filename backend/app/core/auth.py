from typing import List
from fastapi import HTTPException, status

class RBAC:
    """
    Role-Based Access Control helper.
    """
    @staticmethod
    def enforce_role(user_roles: List[str], required_roles: List[str]):
        """
        Checks if the user has at least one of the required roles.
        """
        # Admin bypass
        if "ADMIN" in [r.upper() for r in user_roles] or "GlobalAdmin" in user_roles:
            return True
            
        has_role = any(role.upper() in [r.upper() for r in user_roles] for role in required_roles)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return True

    @staticmethod
    def enforce_permission(user_permissions: List[str], required_permission: str):
        user_perms_upper = [p.upper() for p in user_permissions]
        if "ADMIN" in user_perms_upper: # Simplified admin content
            return True
        if required_permission.upper() not in user_perms_upper:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {required_permission}"
            )
        return True
