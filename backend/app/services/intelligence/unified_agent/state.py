"""
State for Unified Agent (ReAct loop).
"""

from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def _merge_script_results(
    left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    if not left:
        left = {}
    if not right:
        return dict(left)
    return {**left, **right}


class UnifiedAgentState(TypedDict, total=False):
    """State for the ReAct agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    blocked: Optional[bool]  # Set by guardian when request is blocked
    collected_sources: Optional[List[Dict[str, Any]]]  # Sources from tools (for API response)
    script_results: Annotated[Dict[str, Any], _merge_script_results]  # Tabell/diagram fra verktøy
