from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.core.llm_factory import get_chat_llm
import logging

logger = logging.getLogger(__name__)

async def compress_context(context: str, question: str) -> str:
    """
    Hjelpefunksjon for å komprimere tekst via LLM.
    """
    if not context or len(context) < 1000:
        return context
        
    try:
        llm = get_chat_llm(temperature=0)
        prompt = f"""Komprimer dataene under slik at de er relevante for spørsmålet.
Behold alle ID-er (UUID), tall, beløp og navn nøyaktig. Fjern støy.

SPØRSMÅL: {question}
DATA: {context}"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Context compression failed: {e}")
        return context

async def context_compressor_node(state: AgentState):
    """
    LangGraph-node som renser og komprimerer kontekst før skriving.
    """
    logger.info("🗜️ Context Compressor: Renser data...")
    messages = state.get("messages", [])
    
    # Finn brukerens spørsmål
    last_user_msg = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
    question = last_user_msg.content if last_user_msg else "Oppsummer data."

    # Samle alle SystemMessages (verktøyresultater)
    context_parts = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            # Ikke ta med interne ruting-beskjeder
            if not any(x in msg.content for x in ["REFLECTOR_FEEDBACK", "MAX_MESSAGES_PRUNED"]):
                context_parts.append(msg.content)
    
    raw_context = "\n\n".join(context_parts)
    
    if len(raw_context) > 2000:
        compressed = await compress_context(raw_context, question)
        return {
            "messages": [SystemMessage(content=f"KOMPRIMERT_KONTEKST:\n{compressed}")],
            "current_agent": "compressor"
        }
    
    return {"current_agent": "compressor"}
