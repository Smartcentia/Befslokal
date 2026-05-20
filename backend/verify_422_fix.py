import asyncio
import httpx
from uuid import UUID

async def verify_internal_control_cases():
    url = "http://localhost:8000/api/v1/internal-control/cases"
    
    print(f"Testing GET {url} without property_id...")
    async with httpx.AsyncClient() as client:
        try:
            # Test without property_id
            response = await client.get(url)
            print(f"Response Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS: Endpoint returned 200 OK without property_id.")
                cases = response.json()
                print(f"Number of cases returned: {len(cases)}")
            else:
                print(f"FAILURE: Received status code {response.status_code}")
                print(f"Response body: {response.text}")

            # Test with a mock property_id
            mock_property_id = "00000000-0000-0000-0000-000000000000"
            print(f"\nTesting GET {url}?property_id={mock_property_id}...")
            response = await client.get(url, params={"property_id": mock_property_id})
            print(f"Response Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS: Endpoint returned 200 OK with property_id.")
            else:
                print(f"FAILURE: Received status code {response.status_code}")

        except Exception as e:
            print(f"Error during verification: {e}")

if __name__ == "__main__":
    # Ensure the server is running or mock the app call
    # For now, we assume the server is NOT running and we should use TestClient or run the app.
    # But since I want to verify the logic, I can also test the service directly.
    
    # Let's try to test the service directly to avoid needing a running server.
    pass

import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.db.base # Ensure all models are registered
from app.domains.hms.services.internal_control_service import InternalControlService
from app.db.session import SessionLocal

async def test_service_logic():
    print("Testing InternalControlService.get_property_cases logic...")
    async with SessionLocal() as db:
        # Test without property_id
        cases = await InternalControlService.get_property_cases(db, property_id=None)
        print(f"SUCCESS: Fetched {len(cases)} cases without property_id.")
        
        # Test with property_id (even if it doesn't exist)
        mock_id = UUID("00000000-0000-0000-0000-000000000000")
        cases = await InternalControlService.get_property_cases(db, property_id=mock_id)
        print(f"SUCCESS: Fetched {len(cases)} cases for property_id {mock_id}.")

if __name__ == "__main__":
    asyncio.run(test_service_logic())
