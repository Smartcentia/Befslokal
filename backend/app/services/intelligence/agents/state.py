from typing import TypedDict, Annotated, List, Union, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The shared state of the agent graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    next_step: str
    current_agent: str
    research_data: Dict[str, Any]
    discovered_tools: List[Dict[str, Any]]
    persona: Optional[str]
    available_scripts: List[str]
    script_results: Dict[str, Any]
    error: Union[str, None]
    usage: Optional[Dict[str, Any]]
    use_lovdata: Optional[bool]
    retry_count: int  # For loop-håndtering
    sender: str       # For å vite hvem som sendte meldingen
    context: Optional[Dict[str, Any]] # Sidekontekst (type, id, navn) fra frontend
    memories: Optional[str]           # Hentet fra langtidsminne
    pending_action: Optional[Dict[str, Any]] # Handling som venter på brukergodkjenning
    action_result: Optional[str]      # Resultatet av en utført handling
