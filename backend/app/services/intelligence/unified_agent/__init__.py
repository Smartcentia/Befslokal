"""
Unified Agent - ReAct-based KI Kollega with function calling.

Replaces rigid pipeline (Supervisor -> Researcher -> Analyst -> Writer) with
a single LLM that chooses tools dynamically.
"""

from .graph import create_unified_graph
from .state import UnifiedAgentState
from .tools import create_befs_tools

__all__ = ["create_unified_graph", "UnifiedAgentState", "create_befs_tools"]
