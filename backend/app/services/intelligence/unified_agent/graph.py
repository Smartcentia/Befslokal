"""
Unified Agent graph - ReAct loop with Guardian.

Flow: Entry -> guardian -> (blocked?) END | (approved) -> agent <-> tools -> END
"""

import logging
from typing import Any, Dict, List, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.services.intelligence.ki_kollega.service import get_befs_instruksjoner
from app.services.intelligence.unified_agent.state import UnifiedAgentState
from app.services.intelligence.unified_agent.tools import create_befs_tools

logger = logging.getLogger(__name__)

# Max iterations to prevent infinite loops (allow complex multi-tool queries)
MAX_ITERATIONS = 8

# Guardian forbidden terms
FORBIDDEN_TERMS = ["fødselsnummer", "ssn", "kontonummer", "passord"]


def _guardian_node(state: UnifiedAgentState) -> dict:
    """
    Security check - block requests containing sensitive terms.
    When blocked: adds AIMessage and sets blocked=True so we route to END.
    """
    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    if not last_msg or not isinstance(last_msg, HumanMessage):
        return {"messages": [], "blocked": False}

    content = (last_msg.content or "").lower()
    for term in FORBIDDEN_TERMS:
        if term in content:
            logger.warning(f"Guardian BLOCKED request containing: {term}")
            return {
                "messages": [
                    AIMessage(
                        content=f"Beklager, jeg kan ikke søke etter sensitiv informasjon som {term}. Er det noe annet jeg kan hjelpe deg med?"
                    )
                ],
                "blocked": True,
            }

    logger.info("Guardian APPROVED request.")
    return {"messages": [], "blocked": False}


def _create_agent_node(tools: list):
    """Create the agent (LLM) node with tools bound."""

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )
    model_with_tools = llm.bind_tools(tools)

    befs = get_befs_instruksjoner()
    system_content = f"""Du er KI Kollega, en hjelpsom assistent for BEFS Eiendom.
{befs}

Bruk verktøyene når du trenger data. Svar på norsk, kort og konkret.
Ved telling: oppgi eksakt tall. Ved «alle X»: list alle treff.
Gi aldri rå SQL eller tekniske detaljer til brukeren.

RETRY VED SQL-FEIL:
- Når run_sql_query returnerer "FEIL:" eller feilmelding (f.eks. "column X does not exist"), reformuler spørsmålet og kall run_sql_query igjen med korrigert formulering.
- Eksempel: FEIL: column end_date does not exist → bruk c.end_date eller start_date i stedet, prøv igjen.

DATAKILDER:
- Regnskap/kostnader/husleie (faktiske tall 2025): bruk run_sql_query → tabellen gl_transactions, kolonne account_name
- Husleie-filtrering: account_name IN ('Leie lokaler fra Statsbygg', 'Leie lokaler andre utleiere', 'Leie parkeringsplass')
- Kontrakter og budsjettert leie: bruk run_sql_query → tabellen contracts, felt amount->>'amount_per_year'
- Eiendomsinfo (navn, adresse, region): bruk lookup_properties ELLER run_sql_query → tabellen properties
- Geografi (lengst nord/sør, nordligst, sørligst, koordinater): bruk **run_sql_query** mot `properties` med kolonnene `latitude` og `longitude` (se SCHEMA). **Ikke** bruk lookup_properties for slike spørsmål – det søker bare i tekstfelt og gir ofte ingen treff.

INGEN TREFF VS. TOM DATABASE:
- Teksten «Ingen eiendommer funnet» fra lookup_properties betyr at **søkeordet** ikke matchet navn/adresse/bruk – det betyr **ikke** at databasen mangler eiendommer. Bruk run_sql_query (f.eks. liste eller COUNT fra `properties`) eller et annet verktøy før du sier at ingen eiendommer er registrert.
- Tilsvarende: «Ingen resultater fra databasen» fra SQL kan bety feil spørring – reformuler og prøv igjen (se RETRY VED SQL-FEIL).

DATAKILDER (fortsettelse):
- Familievernkontor nasjonalt (Bufdir, offisielt navn, telefon utover BEFS-registeret): bruk lookup_familievernkontor_bufdir
- SSB (nasjonal statistikk): bruk fetch_ssb_statistics for KPI, inflasjon, boligpriser. Bruk combine_ssb_befs_data for å sammenligne våre data med SSB.
- Barnevern / Bufdir / Storting (overordnet kontekst): bruk get_barnevern_reference_context for St.prp./Prop-lenker, Bufdir årsrapport-lenker og SSB tabell-kortliste (tittel, referanse, URL – ikke fulltekst).
- Prediksjon Excel (finans/): bruk get_finans_prediksjon_excel_summary for antagelser og tall fra Prediksjon_*_Økonomi.xlsx eller Lønn (ark-visning). For faktiske poster i databasen (GL, budsjett): bruk run_sql_query.

RAPPORTER:
- Når brukeren ber om rapport (f.eks. "lag rapport for region Vest", "rapport for eiendom X", "generer rapport 2025"):
  1. Kall flere verktøy i sekvens: run_sql_query, get_leie_gap_analyse, get_yoy_cost_analysis, get_budget_variance_report, get_monthly_budget_actual
  2. Strukturer svaret med tydelige overskrifter: ## Eiendommer, ## Kontrakter, ## Kostnader, ## Budsjett vs faktisk, ## Avvik
  3. Oppsummer kort på slutten

DIAGRAM: Når du henter SSB-data (fetch_ssb_statistics / combine_ssb_befs_data), kan appen vise et interaktivt diagram under svaret – oppsummer og forklar tallene i tekst uansett.

LENKER I SVAR:
- Når du nevner eiendom, kontrakt eller part med kjent ID fra dataene, bruk Markdown-lenker:
  - Eiendom: [Navn](property:UUID)
  - Kontrakt: [Navn](contract:UUID)
  - Part: [Navn](party:UUID)
- Eksempel: "Den største eiendommen er [Bufdir Helsfyr](property:abc-123-uuid) med 2500 m²."
"""

    async def agent_node(state: UnifiedAgentState):
        messages = [SystemMessage(content=system_content)] + list(state["messages"])
        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return agent_node


def _create_tools_node(tools: list):
    """Custom tools node that extracts structured_sources for API response."""

    tools_by_name = {t.name: t for t in tools}

    async def tools_node(state: UnifiedAgentState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_msg = messages[-1] if messages else None
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {"messages": [], "collected_sources": []}

        collected_sources: List[Dict[str, Any]] = list(state.get("collected_sources") or [])
        tool_messages = []
        script_results: Dict[str, Any] = {}

        for tc in last_msg.tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args") or {}
            tool_call_id = tc.get("id", "") or "call"

            tool = tools_by_name.get(tool_name)
            if not tool:
                content = f"Verktøy '{tool_name}' ikke funnet."
            else:
                try:
                    result = await tool.ainvoke(tool_args)
                    if isinstance(result, dict) and "formatted" in result and "structured_sources" in result:
                        content = result.get("formatted", str(result))
                        for src in result.get("structured_sources") or []:
                            collected_sources.append(src)
                        tab = result.get("tabular")
                        if (
                            isinstance(tab, dict)
                            and isinstance(tab.get("rows"), list)
                            and len(tab["rows"]) > 0
                            and tab.get("dimensionKeys")
                            and tab.get("valueKey")
                        ):
                            key = f"{tool_name}_{str(tool_call_id)[:12]}"
                            script_results[key] = {
                                "chart": {
                                    "rows": tab["rows"],
                                    "dimensionKeys": tab["dimensionKeys"],
                                    "valueKey": tab["valueKey"],
                                    "role": tab.get("role"),
                                }
                            }
                    else:
                        content = str(result) if result is not None else ""
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    content = f"Feil ved kjøring av verktøy: {str(e)}"

            tool_messages.append(
                ToolMessage(content=content, tool_call_id=tool_call_id)
            )

        out: Dict[str, Any] = {"messages": tool_messages, "collected_sources": collected_sources}
        if script_results:
            out["script_results"] = script_results
        return out

    return tools_node


def _should_continue(state: UnifiedAgentState) -> Literal["tools", "end"]:
    """If last message has tool_calls, go to tools; else end."""
    messages = state["messages"]
    last_msg = messages[-1] if messages else None
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return "end"


def create_unified_graph(db, user=None, checkpointer=None):
    """
    Create and compile the Unified Agent graph.

    Args:
        db: AsyncSession for database access (passed to tools via closure)
        user: Optional User for RBAC in tools that filter by access (e.g. combine_ssb_befs)
        checkpointer: Optional checkpointer (f.eks. MemorySaver) for aget_state etter streaming

    Returns:
        Compiled LangGraph
    """
    from app.services.intelligence.ki_kollega.service import ki_kollega_service

    tools = create_befs_tools(db, ki_kollega_service, user=user)
    tools_node_fn = _create_tools_node(tools)

    workflow = StateGraph(UnifiedAgentState)

    workflow.add_node("guardian", _guardian_node)
    workflow.add_node("agent", _create_agent_node(tools))
    workflow.add_node("tools", tools_node_fn)

    workflow.set_entry_point("guardian")

    def route_after_guardian(state: UnifiedAgentState) -> Literal["agent", "end"]:
        if state.get("blocked"):
            return "end"
        return "agent"

    workflow.add_conditional_edges("guardian", route_after_guardian, {"agent": "agent", "end": END})

    workflow.add_conditional_edges("agent", _should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)
