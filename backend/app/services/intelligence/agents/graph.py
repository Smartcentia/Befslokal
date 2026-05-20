from langgraph.graph import StateGraph, END
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.agents.nodes.supervisor import supervisor_node
from app.services.intelligence.agents.nodes.guardian import guardian_node
from app.services.intelligence.agents.nodes.researcher import web_research_node
from app.services.intelligence.agents.nodes.analyst import analyst_node
from app.services.intelligence.agents.nodes.writer import writer_node
from app.services.intelligence.agents.nodes.reflector import reflector_node
from app.services.intelligence.agents.nodes.context_compressor import context_compressor_node
from app.services.intelligence.agents.nodes.memory import memory_node
from app.services.intelligence.agents.nodes.action_node import action_node

# Define the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("guardian_research", guardian_node) 
workflow.add_node("researcher", web_research_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("memory", memory_node)
workflow.add_node("reflector", reflector_node)
workflow.add_node("compressor", context_compressor_node)
workflow.add_node("action", action_node)
workflow.add_node("writer", writer_node)

# Set Entry Point
workflow.set_entry_point("supervisor")

def route_supervisor(state: AgentState):
    nxt = state.get("next_step")
    if nxt == "researcher":
        return "guardian_research"
    elif nxt == "analyst":
        return "analyst"
    elif nxt == "action":
        return "action"
    elif nxt == "memory":
        return "memory"
    else:
        return "writer"

workflow.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "guardian_research": "guardian_research",
        "analyst": "analyst",
        "action": "action",
        "memory": "memory",
        "writer": "writer"
    }
)

# Conditional Edges from Guardian
def route_guardian(state: AgentState):
    if state.get("error"):
        return "writer" 
    return "researcher"

workflow.add_conditional_edges(
    "guardian_research",
    route_guardian,
    {
        "writer": "writer",      
        "researcher": "researcher" 
    }
)

# Conditional Edges from Researcher
def route_researcher(state: AgentState):
    nxt = state.get("next_step")
    if nxt == "analyst":
        return "analyst"
    # Skip reflector if complexity is low
    if nxt == "reflector" and state.get("complexity") == "low":
        return "writer"
    elif nxt == "reflector":
        return "reflector"
    else:
        return "writer"

workflow.add_conditional_edges(
    "researcher",
    route_researcher,
    {
        "analyst": "analyst",
        "reflector": "reflector",
        "writer": "writer"
    }
)

# Conditional Edges from Analyst
def route_analyst(state: AgentState):
    nxt = state.get("next_step")
    # Skip reflector if complexity is low
    if nxt == "reflector" and state.get("complexity") == "low":
        return "writer"
    elif nxt == "reflector":
        return "reflector"
    return "writer"

workflow.add_conditional_edges(
    "analyst",
    route_analyst,
    {
        "reflector": "reflector",
        "writer": "writer"
    }
)

# Conditional Edges from Reflector (The Loop!)
def route_reflector(state: AgentState):
    nxt = state.get("next_step")
    if nxt == "researcher":
        return "guardian_research"
    elif nxt == "analyst":
        return "analyst"
    elif nxt == "action":
        return "action"
    return "compressor"

workflow.add_conditional_edges(
    "reflector",
    route_reflector,
    {
        "guardian_research": "guardian_research",
        "analyst": "analyst",
        "action": "action",
        "compressor": "compressor"
    }
)

# Conditional Edges from Action
def route_action(state: AgentState):
    # Action node will return writer as next step
    return state.get("next_step", "writer")

workflow.add_conditional_edges(
    "action",
    route_action,
    {
        "writer": "writer"
    }
)

# Parallel or sequential extraction
workflow.add_edge("compressor", "writer")
workflow.add_edge("writer", "memory")
workflow.add_edge("memory", END)

# Compile
app = workflow.compile()
