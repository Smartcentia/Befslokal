from typing import Optional, Literal
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.ki_kollega.query_normalizer import normalize_query, expand_query_terms
from app.services.intelligence.agents.utils import TraceLogger
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Hybrid routing: Kombinerer keyword matching (rask) med LLM-klassifisering (når uklart)
USE_HYBRID_ROUTING = True  
LLM_ROUTING_CONFIDENCE_THRESHOLD = 0.7 

# Semantisk routing: embedding-basert matching mot agent-beskrivelser
USE_SEMANTIC_ROUTING = True
SEMANTIC_ROUTE_THRESHOLD = 0.65 

AGENT_DESCRIPTIONS = {
    "researcher": "Søk i dokumenter, oppslag eiendommer kontrakter, Lovdata, fulltekst, finn informasjon",
    "analyst": "Dataanalyse, statistikk, SQL, kostnad, tellinger, sammenligninger, tall, rapporter",
    "memory": "Husk dette, lagre i minnet, merk deg dette, husk at jeg heter X, min favoritt-eiendom er Y",
    "writer": "Hilsninger, generell samtale, ingen data nødvendig, småprat",
    "action": "Når brukeren ber systemet utføre en konkret handling (opprette sak, sende e-post, oppdatere noe)",
}

class IntentClassification(BaseModel):
    """Klassifisering av brukerens intensjon."""
    intent: Literal["researcher", "analyst", "memory", "writer", "action"] = Field(
        description="Hvilken agent som er best egnet til å svare."
    )
    complexity: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Hvor kompleks er forespørselen? (low: enkel fakta/hilsen, high: sammenligning/analyse)"
    )
    reasoning: str = Field(
        description="Kort begrunnelse for valget."
    )
    use_lovdata: bool = Field(
        default=False,
        description="Om dette er et juridisk spørsmål som krever Lovdata-søk."
    )

def _cosine_similarity(a: list, b: list) -> float:
    """Cosine similarity mellom to vektorer."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def supervisor_node(state: AgentState):
    """
    The Supervisor.
    Decides WHO should act next based on the user's input.
    """
    TraceLogger.log_node("supervisor", "Analyserer forespørsel for ruting...")
    messages = state["messages"]
    
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            last_user_msg = HumanMessage(content=msg[1])
            break
            
    last_msg = last_user_msg or messages[-1]
    
    # Handle both BaseMessage and tuple
    if isinstance(last_msg, tuple):
        raw_text = last_msg[1]
    else:
        raw_text = getattr(last_msg, "content", "") or ""
    text = expand_query_terms(normalize_query(raw_text))
    
    # 1. Quick route for greetings
    greetings = ["hei", "hallo", "god dag", "morn", "hvordan går det", "hvem er du"]
    if any(g in text for g in greetings) and len(text.split()) < 5:
        logger.info("--> Greeting detected, routing to WRITER")
        return {"next_step": "writer"}

    # 2. Check Discovered Tools (Toolbox)
    discovered_tools = state.get("discovered_tools", [])
    if discovered_tools:
        tool_names = [t["name"] for t in discovered_tools]
        if "run_sql_query" in tool_names and any(k in text for k in ["kostnad", "kvm", "statistikk"]):
            logger.info("--> Toolbox match: routing to ANALYST")
            return {"next_step": "analyst"}

    # 3. AI-First Routing (Primary)
    classification = await _llm_classify_intent(text, raw_text)
    
    # Update state with classification info and reset retry_count for new request
    return {
        "next_step": classification.intent,
        "use_lovdata": classification.use_lovdata,
        "complexity": classification.complexity,
        "retry_count": 0,
        "sender": "supervisor"
    }


async def _llm_classify_intent(text: str, original_question: str) -> IntentClassification:
    """
    Bruker LLM med strukturert output for å klassifisere brukerens intent.
    """
    try:
        from app.core.llm_factory import get_chat_llm
        from app.services.intelligence.agents.prompts import get_supervisor_system_prompt
        
        llm = get_chat_llm(temperature=0)
        
        structured_llm = llm.with_structured_output(IntentClassification)
        
        system_prompt = get_supervisor_system_prompt()

        result = await structured_llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Klassifiser dette: {original_question}")
        ])
        
        TraceLogger.log_decision("supervisor", result.intent, result.reasoning)
        return result
            
    except Exception as e:
        logger.error(f"LLM routing feilet: {e}")
        return IntentClassification(intent="researcher", reasoning=f"Error: {e}")
