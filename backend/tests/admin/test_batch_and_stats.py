
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import BackgroundTasks

# Mock Environment before imports
import os
import sys
os.environ["DATABASE_URL"] = "postgresql+asyncpg://dummy:dummy@localhost/dummy"
sys.path.append(os.getcwd())

from app.domains.core.models.user import UserRole
from app.domains.innsikt.routers.agent import batch_risk_update
from app.domains.hms.routers.risk import get_external_risk_stats

@pytest.mark.asyncio
async def test_batch_and_stats_integration():
    print("Testing Batch Risk Update (Async Background Task)...")
    
    # 1. Test Batch Update is Executed Synchronously
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.role = UserRole.ADMIN

    # Mock return value of service
    with patch("app.domains.hms.services.risk_service.RiskService.batch_update_risks", new_callable=AsyncMock) as mock_service:
        mock_service.return_value = {"status": "completed", "updated": 10}

        response = await batch_risk_update(db=mock_db, _admin=mock_user)
        
        print(f"Batch Response: {response}")
        assert response["status"] == "completed"
        assert response["updated"] == 10
        
    print("SUCCESS: Batch update correctly executed synchronously.")

    # 2. Test Stats Aggregation
    print("Testing External Risk Stats Aggregation...")
    
    mock_db = AsyncMock()
    
    # Mock row objects from SQLAlchemy result
    class MockRow:
        def __init__(self, name, count):
            self.factor_name = name
            self.count = count
            
    mock_rows = [
        MockRow("Flomfare stor", 5),
        MockRow("NVE Flomsone", 3),
        MockRow("Skredfare", 10),
        MockRow("Høy alder på bygningsmasse (50 år)", 2),
        MockRow("Random Risk", 1)
    ]
    
    mock_result = MagicMock()
    mock_result.all.return_value = mock_rows
    mock_db.execute.return_value = mock_result
    
    stats = await get_external_risk_stats(db=mock_db, current_user=mock_user)
    
    print(f"Stats Result: {stats}")
    
    assert stats["total_external_issues"] == 21 # 5+3+10+2+1
    assert stats["by_category"]["flood"] == 8 # 5+3
    assert stats["by_category"]["landslide"] == 10
    assert stats["by_category"]["building_age"] == 2
    
    print("SUCCESS: Stats aggregation logic verified.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_batch_and_stats_integration())
