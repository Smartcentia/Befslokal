"""
Fullverdig graf state – delt mellom Orchestrator, domeneagenter og Writer.
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
import operator


class FullverdigState(TypedDict):
    """State for Fullverdig-grafen."""

    messages: Annotated[List[BaseMessage], operator.add]
    orchestrator_choice: str  # internkontroll | kontrakter | eiendommer | analyst | avansert
    context: Optional[Dict[str, Any]]  # page, entity_type, entity_id, region
    next_step: str
    agent_result: Optional[str]  # Resultat fra domeneagent (f.eks. INTERNKONTROLL_RESULTAT)
    usage: Optional[Dict[str, Any]]
    error: Optional[str]
