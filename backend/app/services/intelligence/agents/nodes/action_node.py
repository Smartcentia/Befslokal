import logging
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.agents.utils import TraceLogger

logger = logging.getLogger(__name__)

async def action_node(state: AgentState):
    """
    The Action Node.
    Forbereder og håndterer utførelse av verktøy (f.eks. Jira, E-post, Database mutasjoner).
    Hvis en handling foretås for første gang, forberedes den og returneres som `pending_action`
    for godkjenning fra brukeren.
    """
    TraceLogger.log_node("action", "Vurderer systemhandling og trenger brukergodkjenning...")
    messages = state["messages"]
    
    # Check if we already have an action result
    action_result = state.get("action_result")
    if action_result:
        logger.info(f"⚡ Action: Handling allerede utført, resultat: {action_result}")
        return {
            "messages": [SystemMessage(content=f"ACTION_RESULT: {action_result}")],
            "next_step": "writer",
            "sender": "action",
            "pending_action": None # Clear pending action
        }
    
    # Get last message to figure out what action is requested
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            last_user_msg = HumanMessage(content=msg[1])
            break
            
    content = last_user_msg.content if last_user_msg else ""
    if isinstance(last_user_msg, tuple):
        content = last_user_msg[1]

    # For now, we simulate detecting a Jira action
    # In a real setup, an LLM would extract the action and parameters
    pending_action = None
    
    if any(k in content.lower() for k in ["jira", "opprett sak", "lag en sak", "driftsmelding"]):
        logger.info("⚡ Action: Detekterte ønske om Jira-sak")
        pending_action = {
            "tool": "create_jira_ticket",
            "title": "Driftsmelding: " + content[:20] + "...",
            "description": "Automatisk generert sak basert på brukerforespørsel: " + content,
            "status": "pending_approval"
        }
    elif any(k in content.lower() for k in ["epost", "e-post", "send mail", "send epost"]):
        logger.info("⚡ Action: Detekterte ønske om E-post")
        pending_action = {
            "tool": "send_email",
            "title": "Utkast til E-post",
            "recipient": "ukjent@example.com",
            "status": "pending_approval"
        }
        
    if pending_action:
        return {
            "next_step": "writer", # End execution here and wait for user, writer will present the pending action
            "sender": "action",
            "pending_action": pending_action
        }
    else:
        logger.info("⚡ Action: Ingen spesifikk handling funnet, går til writer")
        return {
            "next_step": "writer",
            "sender": "action"
        }
