from app.core.llm_factory import get_chat_llm
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.core.config import settings
from app.services.api_usage_tracker import calculate_cost
from app.services.intelligence.ki_kollega.service import get_befs_instruksjoner
from app.services.intelligence.agents.nodes.context_compressor import compress_context
from app.services.intelligence.agents.utils import TraceLogger
import logging
import gc

logger = logging.getLogger(__name__)

async def writer_node(state: AgentState):
    """
    The Writer.
    Synthesizes the final answer based on all gathered data including Agent Memory.
    
    VIKTIG: Strukturerer meldingskjeden korrekt for LLM:
    1. Finner brukerens opprinnelige spørsmål (HumanMessage)
    2. Samler kontekst fra andre agenter (SystemMessages)
    3. Bygger en klar System -> User struktur
    """
    TraceLogger.log_node("writer", "Formulerer endelig svar til bruker...")
    
    # Prøv å frigjøre litt minne før tung LLM-prosessering
    gc.collect()
    
    messages = state["messages"]
    
    # 1. Valider at vi har API-nøkkel
    if not settings.OPENAI_API_KEY:
        logger.error("Writer: OPENAI_API_KEY is not configured!")
        return {
            "messages": [AIMessage(content="Beklager, AI-tjenesten er ikke konfigurert. Kontakt administrator.")],
            "next_step": "end"
        }
    
    # 2. Finn brukerens nåværende spørsmål (siste HumanMessage for oppfølgingsspørsmål og historikk)
    user_question = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_question = msg.content
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            user_question = msg[1]
            break

    if not user_question:
        logger.warning("Writer: Could not find user's original question in messages")
        user_question = "Ukjent spørsmål"
    
    # 3. Samle kontekst fra andre agenter (Researcher, Analyst, Memory)
    context_parts = []
    memory_context = None
    for msg in messages:
        if isinstance(msg, SystemMessage):
            content = msg.content
            
            # Kategoriser konteksten
            if "RELEVANT LANGTIDSHUKOMMELSE" in content or "RELATERTE TIDLIGERE SAMTALER" in content:
                memory_context = content
            elif any(prefix in content for prefix in [
                "BRUKEREN SER PÅ", "DU SNAKKER MED", "Brukerinformasjon", "TOOL_RESULT", "PARTER_OG_KONTRAKTER",
                "DOKUMENTER_FUNNET", "EIENDOMER_FUNNET", "EIENDOMER_SØK_INGEN_TREFF", "WEB_RESULTATER",
                "LOVDATA_RESULTATER", "ANALYST_RESULT", "DATABASE_RAPPORT", "INTERNKONTROLL_RESULTAT",
                "KONTRAKTER_RESULTAT", "EIENDOMMER_RESULTAT", "OEKONOMI_RESULTAT", "KOMPRIMERT_KONTEKST"
            ]):
                context_parts.append(content)
            elif "ANALYST_FEIL" in content or "INGEN_RESULTATER" in content:
                context_parts.append(content)
    
    # Sjekk om dette er en hilsen uten kontekst - gi et enkelt svar
    greetings = ["hei", "hallo", "god dag", "morn", "hi", "hello"]
    is_greeting = any(g in user_question.lower() for g in greetings) and len(user_question) < 30
    if is_greeting and not context_parts:
        logger.info("Writer: Simple greeting detected, returning direct response")
        return {
            "messages": [AIMessage(content="Hei! Jeg er KI Kollega, din assistent for eiendomsdata. Hva kan jeg hjelpe deg med i dag?")],
            "next_step": "end"
        }
    
    # 4. Bygg strukturert kontekst for LLM
    gathered_context = ""
    if context_parts:
        # Sjekk om vi allerede har komprimert kontekst (prioriter denne)
        compressed = next((c for c in context_parts if "KOMPRIMERT_KONTEKST" in c), None)
        if compressed:
            gathered_context = compressed
        else:
            gathered_context = "\n\n".join(context_parts)
    
    # Samle kildereferanser (IDer) fra alle kilder i state for å hjelpe LLM med å lage lenker
    sources = []
    seen_ids = set()
    
    # Sjekk research_data
    if "research_data" in state and "structured_sources" in state["research_data"]:
        for s in state["research_data"]["structured_sources"]:
            sid = str(s.get("id") or s.get("url", ""))
            if sid and sid not in seen_ids:
                sources.append(s)
                seen_ids.add(sid)
                
    # Sjekk script_results (fra Analyst)
    if "script_results" in state:
        for script_name, res in state["script_results"].items():
            if isinstance(res, dict) and "structured_sources" in res:
                for s in res["structured_sources"]:
                    sid = str(s.get("id") or s.get("url", ""))
                    if sid and sid not in seen_ids:
                        sources.append(s)
                        seen_ids.add(sid)

    if sources:
        source_refs = "\n".join([f"- {s['name']} (ID: {s['id']}, type: {s['type']})" for s in sources if s.get('id')])
        # Legg også til Lovdata-lenker hvis de finnes
        lovdata_refs = "\n".join([f"- {s['name']} (URL: {s['url']})" for s in sources if s.get('type') == 'lovdata' and s.get('url')])
        
        gathered_context += f"\n\nTILGJENGELIGE LENKE-REFERANSER (Bruk disse for å lage markdown-lenker):\n{source_refs}"
        if lovdata_refs:
            gathered_context += f"\n\nLOVDATA REFERANSER:\n{lovdata_refs}"
    
    # 5. Prepare messages for LLM med klar struktur
    from app.services.intelligence.agents.prompts import get_writer_system_prompt
    
    persona = state.get("persona")
    system_prompt = get_writer_system_prompt(persona)
    
    llm_messages = []
    
    # Legg til memory context hvis tilgjengelig
    if memory_context:
        system_prompt += f"\n\n{memory_context}"
    
    # Legg til samlet data-kontekst hvis tilgjengelig
    if gathered_context:
        system_prompt += f"\n\nDATA FRA SØKET:\n{gathered_context}"
    
    llm_messages.append(SystemMessage(content=system_prompt))
    
    # Legg til brukerens spørsmål som HumanMessage
    llm_messages.append(HumanMessage(content=user_question))
    
    logger.info(f"Writer: Structured {len(llm_messages)} messages for LLM. User question: '{user_question[:50]}...'")
    
    # 2. Call LLM
    try:
        llm = get_chat_llm(temperature=0.3)

        # Use astream for token-level streaming (events emitted for chat_stream endpoint)
        full_content = ""
        usage_data = None
        async for chunk in llm.astream(llm_messages):
            if hasattr(chunk, "content") and chunk.content:
                full_content += chunk.content
            if hasattr(chunk, "response_metadata") and chunk.response_metadata and "token_usage" in chunk.response_metadata:
                usage_data = chunk.response_metadata["token_usage"]
        response = AIMessage(content=full_content)

        # Extract usage information (from last chunk or build default)
        if usage_data:
            prompt_tokens = usage_data.get('prompt_tokens', 0)
            completion_tokens = usage_data.get('completion_tokens', 0)
            total_tokens = usage_data.get('total_tokens', 0)
            estimated_cost = calculate_cost(
                model=settings.OPENAI_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )
            usage_data = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(estimated_cost, 6)
            }
            logger.info(f"Writer usage: {total_tokens} tokens, ${estimated_cost:.6f}")

        return {
            "messages": [response],
            "next_step": "end",
            "usage": usage_data
        }
    except Exception as e:
        logger.error(f"Writer node failed to call LLM: {e}")
        # Fallback to simple synthesis if LLM fails
        final_text = "Beklager, jeg klarte ikke å generere et fullstendig svar akkurat nå."
        for m in reversed(messages):
            if hasattr(m, 'content') and "RELEVANT LANGTIDSHUKOMMELSE" in m.content:
                final_text = f"Basert på hukommelsen min: {m.content.split('RELEVANT LANGTIDSHUKOMMELSE:')[1].strip()}"
                break
        
        return {
            "messages": [AIMessage(content=final_text)],
            "next_step": "end"
        }
