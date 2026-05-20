
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import SystemMessage, HumanMessage
from app.services.agents.nodes.analyst import analyst_node
from app.services.agents.state import AgentState

@pytest.mark.asyncio
async def test_analyst_node_selects_script():
    # Setup state with a clear request including "cost" and "compare"
    state = {
        "messages": [HumanMessage(content="Analyze cost comparison for properties")],
        "next_step": "analyst",
        "current_agent": "supervisor", 
        "research_data": {},
        "error": None
    }
    
    # Mock execute_analysis_script
    with patch("app.services.agents.nodes.analyst.execute_analysis_script", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "SCRIPT OUTPUT: Costs compared successfully."
        
        # Run node
        result = await analyst_node(state)
        
        # Verify result
        assert "script_results" in result
        assert "messages" in result
        assert "SCRIPT OUTPUT" in result["messages"][0].content
        
        # Verify script selection logic
        # Based on "cost" and "compare", it might pick cost_analyzer_compare if logic matches "compare"
        # Or fall back to cost_analyzer_top if logic is simple
        # Let's inspect call args to see what it picked
        call_args = mock_exec.call_args
        assert call_args is not None
        script_name = call_args[0][0]
        assert "cost" in script_name or "compare" in script_name

@pytest.mark.asyncio
async def test_analyst_node_fallback():
    # Setup state with generic risk request
    state = {
        "messages": [HumanMessage(content="Check risk status")],
        "next_step": "analyst",
        "current_agent": "supervisor",
        "research_data": {},
        "error": None
    }
    
    with patch("app.services.agents.nodes.analyst.execute_analysis_script", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "AUDIT OUTPUT: Risks found."
        
        result = await analyst_node(state)
        
        # Should fallback to audit_contracts based on "risk"
        script_name = mock_exec.call_args[0][0]
        assert script_name == "audit_contracts"
        assert result["script_results"]["audit_contracts"] == "AUDIT OUTPUT: Risks found."

@pytest.mark.asyncio
async def test_analyst_node_no_match():
    # Setup state with totally unrelated request
    state = {
        "messages": [HumanMessage(content="What is the weather?")],
        "next_step": "analyst",
        "current_agent": "supervisor",
        "research_data": {},
        "error": None
    }
    
    with patch("app.services.agents.nodes.analyst.execute_analysis_script", new_callable=AsyncMock) as mock_exec:
        result = await analyst_node(state)
        
        # Should not execute anything
        mock_exec.assert_not_called()
        
        # Should return a message asking for clarity
        assert "Could not identify" in result["messages"][0].content
