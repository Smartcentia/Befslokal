from langchain_core.messages import SystemMessage, HumanMessage
import logging
import re
from app.services.intelligence.agents.state import AgentState
from app.services.intelligence.agents.utils import TraceLogger
from app.services.intelligence.ki_kollega.query_normalizer import (
    normalize_query,
    expand_query_terms,
    get_search_terms_for_property_lookup,
)
from app.services.mcp.handler import mcp_handler, search_web_tool
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _bufdir_national_context(search_term: str) -> str:
    """Nasjonal familievernkontor-data (Bufdir JSON på Railway)."""
    try:
        from app.services.familievernkontor_bufdir_knowledge import search_bufdir_familievernkontor

        return search_bufdir_familievernkontor(search_term, limit=8)
    except Exception as e:
        logger.debug("Bufdir knowledge search failed: %s", e)
        return ""

async def web_research_node(state: AgentState):
    """
    The Researcher / Tool Executor.
    Først: Søker i dokumenter og strukturert data
    Hvis ingenting funnet: Ruter til analyst for SQL-analyse
    """
    TraceLogger.log_node("researcher", "Søker etter informasjon i dokumenter og database...")
    messages = state["messages"]
    # Use last HumanMessage (current user question); fallback to last message when researcher runs after SystemMessages added
    last_user_input = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_input = msg.content
            break
    if last_user_input is None:
        last_user_input = messages[-1].content if messages else ""
    # Normaliser og utvid for robust matching
    text_normalized = expand_query_terms(normalize_query(last_user_input))
    text_lower = text_normalized.lower()

    # Sjekk for feedback fra Reflector
    reflector_feedback = next((msg.content for msg in reversed(messages) if isinstance(msg, SystemMessage) and "REFLECTOR_FEEDBACK" in msg.content), None)
    if reflector_feedback:
        logger.info(f"🔎 Researcher: Mottok feedback fra Reflector: {reflector_feedback}")
        last_user_input = f"{last_user_input}\n[Korreksjon: {reflector_feedback}]"

    discovered_tools = state.get("discovered_tools", [])
    use_lovdata = state.get("use_lovdata", False)
    
    found_results = False
    
    # 0. Check for legal/juridical questions - prioritize Lovdata search
    legal_keywords = ["lov", "loven", "lovdata", "forskrift", "paragraf", "§", 
                     "husleie", "husleieloven", "hms", "hms-krav", "oppsigelse",
                     "kontraktsrett", "juridisk", "rettigheter", "plikter", 
                     "universell utforming", "arbeidsmiljø", "arbeidsmiljøloven", 
                     "brannvern", "byggteknisk"]
    
    is_legal_query = use_lovdata or any(k in text_lower for k in legal_keywords)
    
    if is_legal_query:
        logger.info("🔎 Researcher: Legal query detected, trying Lovdata search...")
        try:
            from app.services.intelligence.ki_kollega.service import ki_kollega_service
            out = await ki_kollega_service._tool_search_lovdata(last_user_input, limit=5)
            result = out.get("formatted", "") if isinstance(out, dict) else str(out)
            if result and "ingen" not in result.lower() and "feil" not in result.lower():
                found_results = True
                return {
                    "messages": [SystemMessage(content=f"LOVDATA_RESULTATER:\n{result}")],
                    "research_data": {
                        "results": result,
                        "tool": "search_lovdata",
                        "type": "legal",
                        "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                    },
                    "next_step": "reflector",
                    "sender": "researcher"
                }
            else:
                logger.info("🔎 Researcher: Lovdata search returned no results, continuing with other tools...")
        except Exception as e:
            logger.error(f"🔎 Researcher: Lovdata search failed: {e}")
    
    # 0.5 «Alle X» / navn-søk (f.eks. alle familievernkontor, familievern, fvk, hvilke eiendommer er X) – alltid prøv lookup_properties først
    # Slik at vi returnerer alle treff uavhengig av discovered_tools (ToolDiscoveryService kan gi andre verktøy)
    alle_navn_keywords = ["alle ", "finn alle", "liste over alle", "familievernkontor", "familievern", "list alle",
                          "hvilke eiendommer", "fvk", "hvilke er", "eiendommer som", "barnevern", "bup"]
    if any(k in text_lower for k in alle_navn_keywords):
        # Ikke analyse-spørsmål (største/minst kvm) – da skal analyst håndtere
        analysis_keywords = ["største", "størst", "minste", "minst", "høyest", "lavest", "lav", "billig", "sorter", "kvm", "kvadratmeter", "areal"]
        if not any(a in text_lower for a in analysis_keywords):
            try:
                async with SessionLocal() as db:
                    from app.services.intelligence.ki_kollega.service import ki_kollega_service
                    # Uttrekk søkeord: "alle familievernkontor" -> "familievernkontor", "hvilke eiendommer er familievern" -> "familievern"
                    search_term = last_user_input.strip()
                    for prefix in ["alle ", "finn alle ", "liste over alle ", "list alle "]:
                        if search_term.lower().startswith(prefix):
                            search_term = search_term[len(prefix):].strip()
                            break
                    # Mønster: "hvilke eiendommer er X" / "hvilke er X" / "eiendommer som er X"
                    for pattern in [
                        r"hvilke eiendommer (?:er|har|inneholder)\s+(.+)",
                        r"hvilke (?:er )?(.+)",
                        r"eiendommer (?:som er|med)\s+(.+)",
                        r"hvilke (?:eiendommer )?(?:er|har)\s+(.+)",
                    ]:
                        m = re.search(pattern, last_user_input, re.IGNORECASE)
                        if m:
                            search_term = m.group(1).strip().rstrip("?.")
                            break
                    if not search_term or len(search_term) < 2:
                        search_term = "familievernkontor" if "familievernkontor" in text_lower else ("familievern" if "familievern" in text_lower else ("fvk" if "fvk" in text_lower else "eiendom"))
                    # Utvid søkeord (fvk -> familievernkontor) og prøv termer inntil vi får treff
                    search_terms = get_search_terms_for_property_lookup(search_term)
                    if not search_terms:
                        search_terms = [search_term]
                    out = None
                    result = None
                    used_term = search_terms[0]
                    for term in search_terms:
                        out = await ki_kollega_service._tool_lookup_properties(db, term)
                        result = out.get("formatted", "") if isinstance(out, dict) else str(out)
                        no_result_phrases = ("ikke funnet", "ingen eiendommer funnet")
                        if result and not any(p in result.lower() for p in no_result_phrases):
                            used_term = term
                            break
                    if result and not any(p in (result or "").lower() for p in ("ikke funnet", "ingen eiendommer funnet")):
                        logger.info("🔎 Researcher: 'Alle X' lookup returned results, routing to writer")
                        bufdir_extra = _bufdir_national_context(used_term or last_user_input)
                        msg = f"EIENDOMER_FUNNET (alle treff):\n{result}"
                        if bufdir_extra:
                            msg += (
                                "\n\n---\nBUFDIR.NO (nasjonal oversikt familievernkontor – offisielt navn, telefon, kontakt):\n"
                                + bufdir_extra
                            )
                        return {
                            "messages": [SystemMessage(content=msg)],
                            "research_data": {
                                "results": result,
                                "tool": "lookup_properties",
                                "type": "properties",
                                "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                            },
                            "next_step": "reflector", "sender": "researcher"
                        }
                    else:
                        # Returner tydelig «ingen treff» til Writer – ikke fall gjennom til search_documents
                        logger.info("🔎 Researcher: 'Alle X' lookup returned no results, routing to writer with clear message")
                        bufdir_extra = _bufdir_national_context(used_term or last_user_input)
                        msg = f"EIENDOMER_SØK_INGEN_TREFF: Søkte i eiendomsregisteret etter «{used_term}». {result}"
                        if bufdir_extra:
                            msg += (
                                "\n\n---\nBUFDIR.NO (nasjonal oversikt – kan ha offisielt navn/telefon utenfor BEFS-registeret):\n"
                                + bufdir_extra
                            )
                        return {
                            "messages": [SystemMessage(content=msg)],
                            "research_data": {"results": result, "tool": "lookup_properties", "type": "properties"},
                            "next_step": "reflector", "sender": "researcher"
                        }
            except Exception as e:
                logger.error(f"🔎 Researcher: lookup_properties for 'alle X' failed: {e}")
    
    # 0.6 «Har vi kontrakt med X» / «leietaker Y» – lookup_parties
    contract_party_keywords = ["har vi kontrakt", "kontrakt med ", "leietaker", "har vi leietaker", "part ", "leverandør "]
    if any(k in text_lower for k in contract_party_keywords):
        try:
            search_term = last_user_input.strip()
            # Uttrekk navn: "har vi en kontrakt med Pir" -> "Pir", "kontrakt med Acme" -> "Acme"
            for pattern in [
                r"(?:har vi (?:en )?kontrakt med|kontrakt med)\s+(\w+(?:\s+\w+)?)",
                r"(?:leietaker|har vi leietaker|part|leverandør)\s+(\w+(?:\s+\w+)?)",
            ]:
                m = re.search(pattern, last_user_input, re.IGNORECASE)
                if m:
                    search_term = m.group(1).strip()
                    break
            if len(search_term) >= 2:
                async with SessionLocal() as db:
                    from app.services.intelligence.ki_kollega.service import ki_kollega_service
                    out = await ki_kollega_service._tool_lookup_parties(db, search_term)
                    result = out.get("formatted", "") if isinstance(out, dict) else str(out)
                    if result and "ingen parter funnet" not in result.lower() and "feil ved" not in result.lower():
                        logger.info("🔎 Researcher: lookup_parties returned results, routing to writer")
                        return {
                            "messages": [SystemMessage(content=f"PARTER_OG_KONTRAKTER:\n{result}")],
                            "research_data": {
                                "results": result,
                                "tool": "lookup_parties",
                                "type": "parties",
                                "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                            },
                            "next_step": "reflector", "sender": "researcher"
                        }
        except Exception as e:
            logger.error(f"🔎 Researcher: lookup_parties failed: {e}")
    
    # 1. Try to use Discovered Tools from Toolbox first (dokumenter, properties, etc.)
    if discovered_tools:
        for tool in discovered_tools:
            tool_name = tool["name"]
            
            # Special handling for known tools
            if tool_name in ["search_documents", "lookup_properties", "list_properties", "run_sql_query", "lookup_parties"]:
                logger.info(f"🔎 Researcher: Executing discovered tool '{tool_name}'")
                try:
                    async with SessionLocal() as db:
                        from app.services.intelligence.ki_kollega.service import ki_kollega_service
                        # Arguments and execution depend on the tool
                        if tool_name == "search_documents":
                            args = {"query": last_user_input}
                            result = await mcp_handler.execute_tool(tool_name, args, db=db)
                        elif tool_name == "lookup_parties":
                            out = await ki_kollega_service._tool_lookup_parties(db, last_user_input)
                            result = out.get("formatted", "") if isinstance(out, dict) else str(out)
                            if result and "ingen parter funnet" not in result.lower():
                                return {
                                    "messages": [SystemMessage(content=f"TOOL_RESULT (lookup_parties):\n{str(result)[:2000]}")],
                                    "research_data": {
                                        "results": result,
                                        "tool": "lookup_parties",
                                        "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                                    },
                                    "next_step": "reflector", "sender": "researcher"
                                }
                            continue
                        elif tool_name == "lookup_properties":
                            # Kun for konkrete søk (navn/adresse), ikke for analyse/region – la analyst/run_sql håndtere
                            analysis_keywords = ["største", "størst", "minste", "minst", "høyest", "lavest", "lav", "billig", "sorter", "kvm", "kvadratmeter", "areal", "region", "regioner"]
                            if any(k in text_lower for k in analysis_keywords):
                                continue  # La analyst/run_sql håndtere med SQL
                            search_terms = get_search_terms_for_property_lookup(last_user_input.strip())
                            lookup_term = search_terms[0] if search_terms else last_user_input.strip()
                            out = await ki_kollega_service._tool_lookup_properties(db, lookup_term)
                            result = out.get("formatted", "") if isinstance(out, dict) else str(out)
                            no_result_phrases = ("ikke funnet", "ingen eiendommer funnet", "ingen dokumenter funnet")
                            if result and not any(p in result.lower() for p in no_result_phrases):
                                return {
                                    "messages": [SystemMessage(content=f"TOOL_RESULT (lookup_properties):\n{str(result)[:1000]}")],
                                    "research_data": {
                                        "results": result,
                                        "tool": "lookup_properties",
                                        "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                                    },
                                    "next_step": "reflector", "sender": "researcher"
                                }
                            continue  # Try next tool if no results
                        elif tool_name == "run_sql_query":
                            result = await ki_kollega_service._tool_run_sql(db, last_user_input)
                            if result and result.strip() and "ingen resultater" not in result.lower():
                                return {
                                    "messages": [SystemMessage(content=f"TOOL_RESULT (run_sql_query):\n{str(result)[:2000]}")],
                                    "research_data": {"results": result, "tool": "run_sql_query"},
                                    "next_step": "reflector", "sender": "researcher"
                                }
                            continue
                        else:
                            args = {"city": None}
                            result = await mcp_handler.execute_tool(tool_name, args, db=db)
                        
                        # Check if we got meaningful results
                        no_result_phrases = ("ikke funnet", "ingen eiendommer funnet", "ingen dokumenter funnet")
                        if result and (isinstance(result, list) and len(result) > 0) or (isinstance(result, str) and result.strip() and not any(p in (result or "").lower() for p in no_result_phrases)):
                            found_results = True
                            return {
                                "messages": [SystemMessage(content=f"TOOL_RESULT ({tool_name}):\n{str(result)[:1000]}")],
                                "research_data": {"results": result, "tool": tool_name},
                                "next_step": "reflector", "sender": "researcher"
                            }
                        else:
                            logger.info(f"🔎 Researcher: Tool '{tool_name}' returned no results")
                except Exception as e:
                    logger.error(f"🔎 Researcher: Tool execution failed: {e}")
    
    # 2. Try structured database search (RAG, fulltext search)
    if not found_results:
        logger.info("🔎 Researcher: Trying structured database search...")
        try:
            from app.services.search.search_service import search_fulltext
            from app.services.intelligence.ki_kollega.service import ki_kollega_service
            
            async with SessionLocal() as db:
                # Try fulltext search
                docs = await search_fulltext(db, last_user_input, limit=5)
                if docs and len(docs) > 0:
                    found_results = True
                    formatted = "\n".join([f"- {d.get('source_file', 'Ukjent')}: {d.get('content', '')[:200]}" for d in docs[:3]])
                    structured_sources = []
                    for d in docs:
                        url = None
                        if d.get("contract_id"):
                            url = f"/contracts/{d['contract_id']}"
                        elif d.get("property_id"):
                            url = f"/properties/{d['property_id']}"
                        structured_sources.append({
                            "type": "document",
                            "id": str(d.get("text_id", "")),
                            "name": (d.get("source_file") or "Dokument")[:80],
                            "url": url,
                        })
                    return {
                        "messages": [SystemMessage(content=f"DOKUMENTER_FUNNET:\n{formatted}")],
                        "research_data": {
                            "results": docs,
                            "type": "documents",
                            "structured_sources": structured_sources,
                        },
                        "next_step": "reflector", "sender": "researcher"
                    }
                
                # Try property lookup (for specific property searches, not analysis queries)
                # Only if it's a lookup query, not an analysis query like "største eiendom"
                lookup_keywords = ["eiendom", "property", "adresse", "address", "hvor er", "finn", "alle ", "liste",
                                  "familievernkontor", "familievern", "hvilke eiendommer", "fvk", "barnevern", "bup"]
                analysis_keywords = ["største", "størst", "minste", "minst", "høyest", "lavest", "lav", "billig", "sorter", "topp", "antall", "kostnad", "region"]
                
                is_lookup_query = any(k in text_lower for k in lookup_keywords)
                is_analysis_query = any(k in text_lower for k in analysis_keywords)
                
                if is_lookup_query and not is_analysis_query:
                    # Bruk utvidet søkeord for robusthet (fvk -> familievernkontor)
                    search_terms = get_search_terms_for_property_lookup(last_user_input.strip())
                    search_term = search_terms[0] if search_terms else last_user_input.strip()
                    out = await ki_kollega_service._tool_lookup_properties(db, search_term)
                    prop_result = out.get("formatted", "") if isinstance(out, dict) else str(out)
                    if prop_result and "ingen eiendommer funnet" not in prop_result.lower() and "ikke funnet" not in prop_result.lower():
                        found_results = True
                        msg = f"EIENDOMER_FUNNET:\n{prop_result}"
                        if any(
                            k in text_lower
                            for k in ("familievernkontor", "familievern", "fvk", "bufdir")
                        ):
                            buf = _bufdir_national_context(search_term)
                            if buf:
                                msg += (
                                    "\n\n---\nBUFDIR.NO (nasjonal oversikt familievernkontor):\n" + buf
                                )
                        return {
                            "messages": [SystemMessage(content=msg)],
                            "research_data": {
                                "results": prop_result,
                                "type": "properties",
                                "structured_sources": out.get("structured_sources", []) if isinstance(out, dict) else [],
                            },
                            "next_step": "reflector", "sender": "researcher"
                        }
        except Exception as e:
            logger.error(f"🔎 Researcher: Database search failed: {e}")
    
    # 3. Check if this is a database query (not a document/web query)
    # If user asks about data (properties, contracts, regions, statistics), skip web search and go to SQL
    database_query_keywords = [
        "største", "størst", "minste", "minst", "høyest", "lavest", 
        "sorter", "sortert", "topp", "flest", "mest", "sammenlign",
        "antall", "kostnad", "region", "regioner", "eiendom", "eiendommer",
        "kontrakt", "kontrakter", "statistikk", "analyse", "rapport",
        "hvor mange", "hvilke", "vis meg alle", "gi meg"
    ]
    
    is_database_query = any(k in text_lower for k in database_query_keywords)
    
    # 4. Fallback to Web Search (only if NOT a database query)
    if not found_results and not is_database_query:
        try:
            logger.info("🔎 Researcher: No results in documents/structured data, trying web search...")
            results = await search_web_tool(last_user_input, max_results=3)
            
            if isinstance(results, list) and len(results) > 0:
                summary = "\n".join([f"- {r['title']}: {r['href']}" for r in results])
                structured_sources = [
                    {"type": "web", "name": (r.get("title") or "Web")[:80], "url": r.get("href", "")}
                    for r in results
                ]
                return {
                    "messages": [SystemMessage(content=f"WEB_RESULTATER:\n{summary}")],
                    "research_data": {
                        "results": results,
                        "type": "web",
                        "structured_sources": structured_sources,
                    },
                    "next_step": "reflector", "sender": "researcher"
                }
        except Exception as e:
            logger.error(f"🔎 Researcher: Web search failed: {e}")
    
    # 4b. Bufdir familievernkontor (statisk JSON på backend) – når annet ikke ga treff
    if not found_results and any(
        k in text_lower for k in ("familievernkontor", "familievern", "fvk", "bufdir")
    ):
        buf = _bufdir_national_context(last_user_input)
        if buf:
            logger.info("🔎 Researcher: Bufdir familievernkontor fallback")
            return {
                "messages": [SystemMessage(content=f"BUFDIR_FAMILIEVERNKONTOR (Bufdir.no):\n{buf}")],
                "research_data": {
                    "results": buf,
                    "tool": "bufdir_familievernkontor",
                    "type": "bufdir",
                },
                "next_step": "reflector",
                "sender": "researcher",
            }

    # 5. Last resort: Route to analyst for SQL analysis
    # This happens if:
    # - No results in documents/structured data AND
    # - It's a database query OR web search didn't find anything
    if not found_results:
        if is_database_query:
            logger.info("🔎 Researcher: Database query detected, routing to ANALYST for SQL analysis")
            return {
                "messages": [SystemMessage(content="DATABASE_SPØRSMÅL: Dette ser ut som et spørsmål om data i databasen (eiendommer, kontrakter, regioner, statistikk). Prøver SQL-analyse.")],
                "next_step": "analyst"
            }
        else:
            logger.info("🔎 Researcher: No results found anywhere, routing to ANALYST for SQL analysis")
            return {
                "messages": [SystemMessage(content="INGEN_RESULTATER_I_DOKUMENTER: Fant ingen informasjon i dokumenter eller strukturert data. Prøver SQL-analyse som siste utvei.")],
                "next_step": "analyst"
            }
    
    # Should not reach here, but just in case
    return {
        "messages": [SystemMessage(content="Researcher: Kunne ikke finne informasjon.")],
        "next_step": "reflector", "sender": "researcher"
    }
