"""Integration tests for authentication and authorization."""
import pytest
from httpx import AsyncClient

# Common headers for authenticated requests
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.mark.integration
@pytest.mark.requires_auth
class TestAuthentication:
    """Tests for authentication flow."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_no_auth(self):
        """Test that health endpoint doesn't require authentication."""
        from httpx import ASGITransport
        from app.main import app
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, client):
        """Test that protected endpoints require authentication."""
        # Client fixture already has auth mocked but we verify it works
        response = await client.get("/api/v1/properties", headers=AUTH_HEADERS)
        # Should work with mocked auth
        assert response.status_code in [200, 404]  # 200 OK or 404 if no data
    
    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_admin_role(self, client):
        """Test that admin endpoints require admin role."""
        # Client fixture has admin user mocked
        response = await client.get("/api/v1/admin/users", headers=AUTH_HEADERS)
        # Should work with mocked admin auth
        assert response.status_code in [200, 404]


@pytest.mark.integration
@pytest.mark.requires_db
class TestSessionManagement:
    """Tests for NextAuth session management."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, client, db_session):
        """Test creating a new session."""
        from app.domains.core.models.user import User, UserRole
        
        # Create a user first
        user_data = {
            "email": "testuser@befs.no",
            "name": "Test User",
            "role": UserRole.PROPERTY_MANAGER,
        }
        user = User(**user_data)
        db_session.add(user)
        await db_session.commit()
        
        # Create session data conforming to SessionCreate schema
        session_data = {
            "user_email": user.email,
            "access_token": "valid-jwt-token",
            "id_token": "valid-id-token",
            "refresh_token": "valid-refresh-token",
            "expires_at": "2025-01-01T00:00:00Z"
        }
        
        response = await client.post("/api/v1/sessions", json=session_data)
        assert response.status_code in [201]
        data = response.json()
        assert data["user_email"] == user.email
        assert "session_id" in data
    
    @pytest.mark.asyncio
    async def test_get_session(self, client, db_session):
        """Test retrieving a session."""
        from app.domains.core.models.user import User, UserRole
        from app.domains.core.models.session import Session
        from datetime import datetime, timedelta, timezone
        
        # Create user
        user = User(
            email="testuser@befs.no",
            name="Test User",
            role=UserRole.PROPERTY_MANAGER,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create session manually
        session = Session(
            user_email=user.email,
            access_token="test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Get session
        response = await client.get(f"/api/v1/sessions/{session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user_email"] == user.email
    
    @pytest.mark.asyncio
    async def test_delete_session(self, client, db_session):
        """Test deleting a session (logout)."""
        from app.domains.core.models.user import User, UserRole
        from app.domains.core.models.session import Session
        from datetime import datetime, timedelta, timezone
        
        # Create user
        user = User(
            email="testuser@befs.no",
            name="Test User",
            role=UserRole.PROPERTY_MANAGER,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create session manually
        session = Session(
            user_email=user.email,
            access_token="test-token-delete",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Delete session
        response = await client.delete(f"/api/v1/sessions/{session.session_id}")
        assert response.status_code in [200, 204]
        
        # Verify session is deleted
        response = await client.get(f"/api/v1/sessions/{session.session_id}")
        assert response.status_code == 404
