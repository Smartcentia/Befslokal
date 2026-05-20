import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.mcp.handler import check_internal_control_tool, check_anomalies_tool
import uuid

@pytest.mark.asyncio
async def test_check_internal_control_global_execution(monkeypatch):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    mock_case = MagicMock()
    mock_case.case_id = uuid.uuid4()
    mock_case.title = "Global Leaks"
    mock_case.process_state = "New"
    mock_case.updated_at = "2024-01-13"
    
    # Property attributes
    mock_property = MagicMock()
    mock_property.address = "Global Ave 123"
    
    # Result content
    mock_result.all.return_value = [(mock_case, mock_property)]
    mock_session.execute.return_value = mock_result
    
    # Mock the async context manager
    mock_sess_ctx = AsyncMock()
    mock_sess_ctx.__aenter__.return_value = mock_session
    mock_sess_ctx.__aexit__.return_value = None
    
    # Patch get_session
    mock_get_session = MagicMock(return_value=mock_sess_ctx)
    monkeypatch.setattr("app.services.mcp.handler.get_session", mock_get_session)

    # Call the tool without arguments
    result = await check_internal_control_tool(property_id=None)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["property"] == "Global Ave 123"
    assert result[0]["title"] == "Global Leaks"

@pytest.mark.asyncio
async def test_check_anomalies_global_execution(monkeypatch):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    
    mock_risk = MagicMock()
    mock_risk.assessment_date = "2024-01-10"
    mock_risk.risk_category = "Critical"
    mock_risk.overall_risk_score = 95
    mock_risk.notes = "Immediate action required"
    
    mock_property = MagicMock()
    mock_property.address = "Hazard Lane 666"
    mock_property.city = "Oslo"
    
    mock_result.all.return_value = [(mock_risk, mock_property)]
    mock_session.execute.return_value = mock_result
    
    mock_sess_ctx = AsyncMock()
    mock_sess_ctx.__aenter__.return_value = mock_session
    mock_sess_ctx.__aexit__.return_value = None
    
    mock_get_session = MagicMock(return_value=mock_sess_ctx)
    monkeypatch.setattr("app.services.mcp.handler.get_session", mock_get_session)
    
    result = await check_anomalies_tool(property_id=None)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["property"] == "Hazard Lane 666"
    assert result[0]["level"] == "Critical"
