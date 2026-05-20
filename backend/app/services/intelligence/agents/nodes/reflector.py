from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.agents.utils import TraceLogger
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def reflector_node(state: AgentState):
    """
    The Critical Reflector.
    Vurderer om vi har nok data, og styrer loopen.
    """
    TraceLogger.log_node("reflector", "Vurderer datakvalitet og svar-evne...")
    
    messages = state.get("messages", [])
    research_data = state.get("research_data", {})
    analyst_data = state.get("script_results", {})
    retry_count = state.get("retry_count", 0)
    last_sender = state.get("sender", "unknown")
    
    # Finn opprinnelig spørsmål
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            last_user_msg = HumanMessage(content=msg[1])
            break
            
    question = last_user_msg.content if last_user_msg else "Ukjent spørsmål"

    # Oppsummering av hva som ble funnet
    data_summary = ""
    if research_data.get("results"):
        data_summary += f"\n- Researcher fant: {str(research_data['results'])[:400]}"
    if analyst_data:
        data_summary += f"\n- Analyst fant: {str(analyst_data)[:400]}"
        
    if not data_summary:
        data_summary = "INGEN DATA FUNNET."

    # Hvis vi har loopet for mye, stopp uansett
    if retry_count >= 2:
        logger.warning(f"🧐 Reflector: Maks retries ({retry_count}) nådd. Går til writer.")
        return {"next_step": "writer"}

    # NYHET: Fast-exit hvis vi allerede har prøvd én gang og har data.
    # Dette hindrer endeløse analyser som brukeren opplever som "slow".
    if retry_count >= 1 and analyst_data:
        logger.info("🧐 Reflector: Har analytiker-data etter retry. Går direkte til writer.")
        return {"next_step": "writer"}

    try:
        from app.core.llm_factory import get_chat_llm
        from app.services.intelligence.agents.prompts import get_reflector_system_prompt
        
        llm = get_chat_llm(temperature=0)
        system_prompt = get_reflector_system_prompt(question, data_summary)

        response = await llm.ainvoke([SystemMessage(content=system_prompt)])
        decision_text = response.content.upper()
        
        if "GODT_NOK" in decision_text:
            TraceLogger.log_decision("reflector", "writer", "Fant tilstrekkelig informasjon.")
            return {"next_step": "writer"}
            
        # Hvis mangler data, finn ut hvilken agent som skal prøve igjen
        # Prioriter det LLM foreslår, men fallback til last_sender hvis uklart
        next_agent = last_sender if last_sender in ["researcher", "analyst"] else "researcher" 
        if "analyst" in decision_text.lower():
            next_agent = "analyst"
        elif "researcher" in decision_text.lower():
            next_agent = "researcher"
        feedback = next((line.split("BEGRUNNELSE:")[1] for line in decision_text.splitlines() if "BEGRUNNELSE:" in line), "Prøv en annen tilnærming.")
        
        TraceLogger.log_decision("reflector", next_agent, f"Mangler data: {feedback}")
        return {
            "next_step": next_agent,
            "retry_count": retry_count + 1,
            "messages": [SystemMessage(content=f"REFLECTOR_FEEDBACK: {feedback}")]
        }
            
    except Exception as e:
        logger.error(f"🧐 Reflector feilet: {e}")
        return {"next_step": "writer"}
