import asyncio
import httpx
from app.core.config import settings

async def verify_admin_batch():
    # Import models to ensure ORM registry is populated correctly avoiding InvalidRequestError
    import app.domains.core.models.center
    import app.domains.core.models.property
    
    # We need a valid token for admin endpoint
    # For local test, we might bypass auth or generate a token if needed.
    # However, 'admin.py' uses 'get_current_active_superuser'.
    # For quick verification without mocking auth entirely, we can try to rely on 
    # the fact that in DEV/TEST environment we might have a bypass or we just unit test the router function directly.
    
    # OR simpler: Use the TestClient which can override dependencies!
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.deps import get_current_active_superuser
    
    # Mock superuser dependency
    from app.api.deps import get_current_active_superuser, get_current_user
    
    # Remove AuthMiddleware to bypass global auth check for this test
    app.user_middleware = [m for m in app.user_middleware if m.cls.__name__ != 'AuthMiddleware']
    
    # We must override essentially everything that might be called.
    # The routers usually depend on get_current_active_superuser
    app.dependency_overrides[get_current_active_superuser] = lambda: {"id": "admin", "is_superuser": True}
    app.dependency_overrides[get_current_user] = lambda: {"id": "admin", "is_superuser": True}
    
    # DEBUG: Print routes
    for route in app.routes:
        if hasattr(route, "path") and "risk" in route.path:
            print(f"Found route: {route.path} [{route.methods}]")
    
    client = TestClient(app)
    
    print("Testing POST /api/v1/admin/risk/batch...")
    # Note: this will trigger REAL batch processing on the DB configured in .env
    response = client.post("/api/v1/admin/risk/batch")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200 and "processed" in response.json():
        print("SUCCESS: Admin batch endpoint works.")
    else:
        print("FAILURE: Endpoint failed.")

if __name__ == "__main__":
    asyncio.run(verify_admin_batch())
