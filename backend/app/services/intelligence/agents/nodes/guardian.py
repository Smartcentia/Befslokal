from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
import logging

logger = logging.getLogger(__name__)

async def guardian_node(state: AgentState):
    """
    The Guardian Agent.
    Acts as a firewall for privacy and security.
    Checks the LAST message from the Researcher/Supervisor.
    If it attempts to search for PII or sensitive numeric data, it REJECTS it.
    """
    logger.info("🛡️ Guardian Access Control: Checking request...")
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # Simple Heuristic Check (can be replaced with a stronger LLM call later)
    # 1. Check for Social Security Number patterns (naïve check)
    # 2. Check for explicit "Ola Nordmann" style names in search queries
    # For now, we simulate a check on the 'content' of the message.
    
    content = last_message.content.lower()
    
    # FAIL CONDITIONS
    forbidden_terms = ["fødselsnummer", "ssn", "kontonummer", "passord"]
    
    for term in forbidden_terms:
        if term in content:
            logger.warning(f"🛡️ Guardian BLOCKED request containing: {term}")
            return {
                "messages": [SystemMessage(content=f"GUARDIAN_BLOCK: Beklager, jeg kan ikke søke etter sensitiv informasjon som {term}. Er det noe annet jeg kan hjelpe deg med?")],
                "error": "Privacy Violation",
                "next_step": "writer" 
            }

    # If we are here, it passes the basic filter.
    # We can also add an LLM-based check here if we want to be smarter.
    logger.info("🛡️ Guardian APPROVED request.")
    return {"error": None}
