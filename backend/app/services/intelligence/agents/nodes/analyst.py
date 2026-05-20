from langchain_core.messages import SystemMessage, HumanMessage
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.agents.utils import TraceLogger
from app.services.mcp.script_executor import execute_analysis_script, SAFE_ANALYSIS_SCRIPTS
import logging
import json

logger = logging.getLogger(__name__)

async def analyst_node(state: AgentState):
    """
    The Data Analyst.
    Executes analysis scripts based on user request.
    """
    TraceLogger.log_node("analyst", "Utfører data-analyse og SQL-spørringer...")
    messages = state["messages"]
    # Use last HumanMessage (current user question) for script matching; fallback to last message
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break
        elif isinstance(msg, tuple) and msg[0] == "user":
            last_user_msg = HumanMessage(content=msg[1])
            break
            
    last_message = last_user_msg or (messages[-1] if messages else None)
    
    if isinstance(last_message, tuple):
        content = last_message[1]
    else:
        content = getattr(last_message, "content", "") if last_message else ""

    # 1. Sjekk for feedback fra Reflector
    reflector_feedback = next((msg.content for msg in reversed(messages) if isinstance(msg, SystemMessage) and "REFLECTOR_FEEDBACK" in msg.content), None)
    if reflector_feedback:
        logger.info(f"📊 Analyst: Mottok feedback fra Reflector: {reflector_feedback}")
        content = f"{content}\n[Refleksjon over forrige forsøk: {reflector_feedback}]"

    # ... (identifisering av skript fortsetter)
    # "Hvilket firma har størst kostnad" trenger dynamisk SQL, ikke ferdigskript
    dspy_first_keywords = [
        "firma", "firmaer", "part", "parter", "leverandør", "leverandører",
        "leietaker", "leietakere", "hvilket", "hvilke", "hvem",
        "budsjett", "budget", "økonomi", "regnskap", "avvik", "oversikt", "statistikk",
        "saker", "hms", "risiko", "mangler", "feil"
    ]
    use_dspy_first = any(kw in content.lower() for kw in dspy_first_keywords)

    # 1. Identify which script to run (skip hvis DSPy-first)
    selected_script = None
    params = {}
    
    if not use_dspy_first:
        sorted_scripts = sorted(SAFE_ANALYSIS_SCRIPTS.keys(), key=len, reverse=True)
        for script_key in sorted_scripts:
            script_config = SAFE_ANALYSIS_SCRIPTS[script_key]
            keywords = script_key.replace("_", " ").split()
            if all(k in content for k in keywords):
                selected_script = script_key
                break
                
        if not selected_script:
            if "status" in content or "risk" in content:
                selected_script = "audit_contracts"
            elif ("cost" in content or "kostnad" in content) and not any(
                kw in content for kw in ["kvm", "kvadratmeter", "kvadrat", "per kvm"]
            ):
                # cost_analyzer_top sorterer kun på rent/costs/total – ikke kostnad per kvm.
                # Spørsmål om kostnad per kvadratmeter må bruke DSPy (SQL med total_manual_expenses+total_spend_csv/total_area).
                selected_script = "cost_analyzer_top"
                params = {"n": "5", "by": "total"}
            elif any(kw in content.lower() for kw in ["prognose", "forecast", "fremtid", "neste år"]):
                selected_script = "ml_financial_forecasting"
                # Prøv å hente navn eller ID fra kontekst
                prop_name = context.get("entity_name") or context.get("name")
                prop_id = context.get("entity_id") if context.get("entity_type") == "property" else None
                params = {"target": prop_id or prop_name or ""}
                     
            elif any(kw in content.lower() for kw in ["avvik", "anomali", "merkelig", "unormal"]):
                selected_script = "ml_financial_anomalies"
                prop_name = context.get("entity_name") or context.get("name")
                prop_id = context.get("entity_id") if context.get("entity_type") == "property" else None
                params = {"target": prop_id or prop_name or ""}
            elif any(kw in content.lower() for kw in ["mønster", "pattern", "struktur", "gjenganger", "gjenkjenning", "gjennkjenning"]):
                selected_script = "ml_financial_patterns"
                params = {}
    else:
        logger.info("📊 Analyst: Ad-hoc firma/part-spørsmål → DSPy (LLM genererer SQL)")
            
    if selected_script:
        logger.info(f"📊 Analyst: Selected script '{selected_script}'")
        
        # Extract params from content if needed (very basic extraction)
        if "params" not in params and "{" in str(SAFE_ANALYSIS_SCRIPTS[selected_script]["args"]):
             # TODO: Implement better param extraction
             pass

        # Execute
        result = await execute_analysis_script(selected_script, params)
        
        # Format result
        return {
            "messages": [SystemMessage(content=f"ANALYST_RESULT ({selected_script}):\n{result[:1000]}...")],
            "script_results": {selected_script: result},
            "next_step": "reflector", "sender": "analyst"
        }
    else:
        # Fallback: Use DSPy SQL Generator for dynamic SQL queries
        # Self-correction: ved SQL-feil, retry med feilmelding som kontekst (maks 2 forsøk)
        logger.info("📊 Analyst: No script match, using DSPy SQL Generator")
        try:
            from app.services.dspy.sql_generator import dspy_generator
            from app.db.session import SessionLocal

            original_question = last_message.content if last_message else None
            if not original_question:
                logger.warning("📊 Analyst: Could not find HumanMessage, using last message content")
                original_question = messages[-1].content if messages else ""

            # Hent sidekontekst fra state
            context = state.get("context", {})
            page_context_str = ""
            if context and context.get("entity_id"):
                etype = context.get("entity_type", "entity")
                eid = context.get("entity_id")
                page_context_str = f"User is currently viewing {etype} with ID '{eid}'."
                logger.info(f"📊 Analyst: Using page context: {page_context_str}")

            def _is_retryable_error(err: str) -> bool:
                """Syntaks/DB-feil kan retries; validering/sikkerhet ikke."""
                err_lower = err.lower()
                if "read-only" in err_lower or "forbudt" in err_lower or "validering" in err_lower:
                    return False
                return any(k in err_lower for k in [
                    "syntax", "syntaks", "does not exist", "operator does not exist",
                    "invalid", "column", "kolonne", "tabell", "table"
                ])

            max_retries = 2
            question = original_question
            result = None

            async with SessionLocal() as db:
                for attempt in range(max_retries):
                    result = await dspy_generator.execute_query(
                        db, 
                        question, 
                        page_context=page_context_str
                    )
                    if not result.get("error"):
                        break
                    error_msg = result["error"]
                    if not _is_retryable_error(error_msg) or attempt >= max_retries - 1:
                        logger.error(f"DSPy SQL error (no retry): {error_msg}")
                        return {
                            "messages": [SystemMessage(content=f"ANALYST_FEIL: Kunne ikke hente data for spørsmålet. Feil: {error_msg}")],
                            "next_step": "reflector", "sender": "analyst"
                        }
                    logger.info(f"📊 Analyst: SQL feilet, retry {attempt + 2}/{max_retries} med feilkontekst")
                    question = f"{original_question}\n\n[Forrige SQL feilet: {error_msg}. Korriger og prøv igjen.]"

                if result.get("error"):
                    return {
                        "messages": [SystemMessage(content=f"ANALYST_FEIL: Kunne ikke hente data. Feil: {result['error']}")],
                        "next_step": "reflector", "sender": "analyst"
                    }
                
                formatted_data = result.get("results", [])
                sql_used = result.get("sql", "")
                
                TraceLogger.log_node("analyst", f"SQL brukt: {sql_used}")

                if not formatted_data:
                    return {
                        "messages": [SystemMessage(content="ANALYST: Ingen resultater funnet i databasen for spørsmålet ditt.")],
                        "next_step": "reflector", "sender": "analyst"
                    }
                
                # Format results as table (KUN resultatdata – IKKE SQL. Writer skal gi naturlige svar.)
                if len(formatted_data) > 0:
                    keys = formatted_data[0].keys()
                    header = " | ".join(str(k) for k in keys)
                    rows = []
                    for row in formatted_data[:10]:  # Limit to 10 rows
                        rows.append(" | ".join(str(row[k]) for k in keys))
                    
                    table_str = f"{header}\n{'-'*len(header)}\n" + "\n".join(rows)
                    if len(formatted_data) > 10:
                        table_str += f"\n(... og {len(formatted_data) - 10} flere rader)"
                    
                    # Build structured_sources from entity columns for links
                    structured_sources = []
                    entity_cols = {
                        "property_id": "property", 
                        "contract_id": "contract", 
                        "party_id": "party",
                        "case_id": "case",
                        "deviation_id": "deviation",
                        "activity_id": "activity",
                        "assessment_id": "risk",
                        "risk_id": "risk",
                        "unit_id": "unit"
                    }
                    seen = set()
                    for row in formatted_data[:20]:
                        for col, stype in entity_cols.items():
                            if col in keys and row.get(col):
                                eid = str(row[col])
                                key = (stype, eid)
                                if key in seen:
                                    continue
                                seen.add(key)
                                name = None
                                for nc in ["title", "name", "property_name", "party_name", "contract_category", "category"]:
                                    if nc in keys and row.get(nc):
                                        name = str(row[nc])[:80]
                                        break
                                structured_sources.append({
                                    "type": stype,
                                    "id": eid,
                                    "name": name or stype.capitalize(),
                                })
                    
                    return {
                        "messages": [SystemMessage(content=f"ANALYST_RESULT:\n{table_str}")],
                        "script_results": {
                            "dspy_sql": {**result, "structured_sources": structured_sources},
                        },
                        "research_data": {"structured_sources": structured_sources},
                        "next_step": "reflector", "sender": "analyst"
                    }
                else:
                    return {
                        "messages": [SystemMessage(content="ANALYST: Ingen resultater funnet.")],
                        "next_step": "reflector", "sender": "analyst"
                    }
                    
        except Exception as e:
            logger.error(f"DSPy SQL execution failed: {e}", exc_info=True)
            return {
                "messages": [SystemMessage(content=f"ANALYST: Kunne ikke utføre database-analyse. Teknisk feil: {str(e)}")],
                "next_step": "reflector", "sender": "analyst"
            }
