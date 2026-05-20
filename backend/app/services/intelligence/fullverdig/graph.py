"""
Fullverdig graf: Orchestrator → Domeneagent → Writer.

Fase 1: internkontroll-agent.
Fase 2: kontrakter-agent, eiendommer-agent.
Avansert rutes til END (service delegerer til ki_kollega).
"""

from langgraph.graph import StateGraph, END

from app.services.intelligence.fullverdig.state import FullverdigState
from app.services.intelligence.fullverdig.orchestrator import orchestrator_node
from app.services.intelligence.fullverdig.agents.internkontroll import internkontroll_agent_node
from app.services.intelligence.fullverdig.agents.kontrakter import kontrakter_agent_node
from app.services.intelligence.fullverdig.agents.eiendommer import eiendommer_agent_node
from app.services.intelligence.fullverdig.agents.oekonomi import oekonomi_agent_node
from app.services.intelligence.agents.nodes.writer import writer_node


def _avansert_node(state: FullverdigState) -> dict:
    return {}


def route_orchestrator(state: FullverdigState) -> str:
    choice = state.get("orchestrator_choice", "avansert")
    if choice == "internkontroll":
        return "internkontroll_agent"
    if choice == "kontrakter":
        return "kontrakter_agent"
    if choice == "eiendommer":
        return "eiendommer_agent"
    if choice in ("oekonomi", "analyst"):
        return "oekonomi_agent"
    return "avansert"


workflow = StateGraph(FullverdigState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("internkontroll_agent", internkontroll_agent_node)
workflow.add_node("kontrakter_agent", kontrakter_agent_node)
workflow.add_node("eiendommer_agent", eiendommer_agent_node)
workflow.add_node("oekonomi_agent", oekonomi_agent_node)
workflow.add_node("avansert", _avansert_node)
workflow.add_node("writer", writer_node)

workflow.set_entry_point("orchestrator")
workflow.add_conditional_edges("orchestrator", route_orchestrator, {
    "internkontroll_agent": "internkontroll_agent",
    "kontrakter_agent": "kontrakter_agent",
    "eiendommer_agent": "eiendommer_agent",
    "oekonomi_agent": "oekonomi_agent",
    "avansert": "avansert",
})
workflow.add_edge("internkontroll_agent", "writer")
workflow.add_edge("kontrakter_agent", "writer")
workflow.add_edge("eiendommer_agent", "writer")
workflow.add_edge("oekonomi_agent", "writer")
workflow.add_edge("writer", END)
workflow.add_edge("avansert", END)

fullverdig_graph = workflow.compile()
