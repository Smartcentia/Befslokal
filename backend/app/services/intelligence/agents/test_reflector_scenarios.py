import asyncio
import sys
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. Mock app.core.config BEFORE importing anything else
# This prevents the real config (and .env loading) from running
mock_settings = MagicMock()
mock_settings.OPENAI_API_KEY = "mock-key-for-testing"
mock_config_module = MagicMock()
mock_config_module.settings = mock_settings
sys.modules["app.core.config"] = mock_config_module

# 2. Import the code under test (now safe)
from app.services.intelligence.agents.nodes.reflector import reflector_node

async def run_scenario(name, question, research_data, analyst_data, mock_llm_response, expected_next):
    print(f"\n🧪 Scenario: {name}")
    print(f"   ❓ Question: {question}")
    
    # Mock State
    state = {
        "messages": [HumanMessage(content=question)],
        "research_data": {"results": research_data},
        "script_results": analyst_data,
        "retry_count": 0,
        "sender": "researcher" 
    }

    # Mock LLM
    mock_response = AIMessage(content=mock_llm_response)
    
    with patch("langchain_openai.ChatOpenAI") as MockChat:
        instance = MockChat.return_value
        instance.ainvoke = MagicMock(return_value=asyncio.Future())
        instance.ainvoke.return_value.set_result(mock_response)
        
        # Run Node
        result = await reflector_node(state)
        
        # Verify
        next_step = result.get("next_step")
        print(f"   👉 Reflector Decision: {next_step}")
        
        if next_step == expected_next:
            print("   ✅ SUCCESS")
        else:
            print(f"   ❌ FAILED (Expected {expected_next}, got {next_step})")

async def main():
    print("🚀 Starting Reflector Logic Verification")
    
    # Scenario 1: Complex Query - Data Found, Analysis Missing
    # User asks for average rent, we have the list but no average.
    await run_scenario(
        name="Missing Analysis routing",
        question="Finn kontrakter i Oslo og beregn snittpris.",
        research_data="Kontrakt A: 100kr, Kontrakt B: 200kr",
        analyst_data=None, # No analysis done yet
        mock_llm_response="BESLUTNING: MERE_DATA_TRENGS\nBEGRUNNELSE: Har data, mangler snitt.\nNESTE_STEG: analyst",
        expected_next="analyst"
    )

    # Scenario 2: Simple Query - All Good
    # User asks for address, we found it.
    await run_scenario(
        name="Simple Fact Retrieval",
        question="Hva er adressen til Bygg A?",
        research_data="Adressen er Storgata 1.",
        analyst_data=None,
        mock_llm_response="BESLUTNING: GODT_NOK\nBEGRUNNELSE: Adressen er funnet.\nNESTE_STEG: writer",
        expected_next="writer"
    )
    
    # Scenario 3: Missing Data completely
    # User asks for X, we found nothing.
    await run_scenario(
        name="Missing Data routing",
        question="Hvem eier Månen?",
        research_data="",
        analyst_data=None,
        mock_llm_response="BESLUTNING: MER_DATA_TRENGS\nBEGRUNNELSE: Fant ingenting.\nNESTE_STEG: researcher",
        expected_next="researcher"
    )

if __name__ == "__main__":
    asyncio.run(main())
