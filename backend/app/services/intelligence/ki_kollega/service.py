"""
KI Kollega Service - Main orchestrator for the AI assistant.

Builds on existing infrastructure:
- RagService for document retrieval
- PostgreSQL for structured data
"""

from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import os
from pathlib import Path
from uuid import uuid4
from typing import Any, AsyncGenerator, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.infrastructure.logger import get_logger
from app.services.mcp_service import mcp_service
from app.models.api_call_logs import ApiCallLog
from app.domains.core.models.user import User, UserRole
from app.services.agent_memory_service import AgentMemoryService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.tool_discovery_service import ToolDiscoveryService

logger = get_logger(__name__)

# BEFS-instruksjoner (terminologi + regler) – samme kilde som enkel modus, brukes i full flyt
_BEFS_INSTRUKSJONER_PATH = Path(__file__).resolve().parent / "befs_instruksjoner.txt"


def get_befs_instruksjoner() -> str:
    """Last BEFS-terminologi og regler – brukes i både enkel modus og full flyt."""
    try:
        if _BEFS_INSTRUKSJONER_PATH.exists():
            return _BEFS_INSTRUKSJONER_PATH.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning("Kunne ikke laste befs_instruksjoner.txt: %s", e)
    return ""


# Constants (use settings for timeouts to allow easy configuration)
SEARCH_LIMIT = 5
LOOKUP_PROPERTIES_LIMIT = 500  # «Alle X» (f.eks. alle familievernkontor) – returner mange treff
MAX_DOC_CONTENT_LENGTH = 500


class QueryType(str, Enum):
    """Types of queries the assistant can handle."""
    LOOKUP = "lookup"           # "Hvor er Vestlund?"
    COMPARISON = "comparison"   # "Sammenlign Region Øst og Vest"
    ANALYSIS = "analysis"       # "Hvilke eiendommer har høyest risiko?"
    SQL_ANALYSIS = "sql_analysis" # "Hvor mange m2 leier vi totalt?"
    EXPLANATION = "explanation" # "Forklar HMS-kravet"
    ACTION = "action"           # "Vis alle kontrakter som utløper"
    GENERAL = "general"         # General questions


@dataclass
class ChatContext:
    """Context information for the current chat."""
    page: Optional[str] = None
    entity_type: Optional[str] = None  # property, contract, party, etc.
    entity_id: Optional[str] = None
    region: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content
        }

class KIKollegaService:
    """
    Main KI Kollega service that orchestrates:
    1. Query understanding and classification
    2. Context evaluation
    3. Hybrid retrieval
    4. Response generation
    """

    def __init__(self):
        self.client = None
        self.model = settings.OPENAI_MODEL
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        try:
            from app.core.ai_utils import get_ai_client
            self.client, self.model = get_ai_client()
            
            if settings.USE_LOCAL_AI:
                logger.info(f"Initialized KI Kollega with Local AI Station at {settings.LOCAL_AI_STATION_URL} (Model: {self.model})")
            else:
                logger.info(f"Initialized KI Kollega with OpenAI Direct API (Model: {self.model})")

        except Exception as e:
            logger.error(f"Client initialization failed: {e}")

    # Tool definitions
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": "Søk etter dokumenter om rutiner, krav, instrukser, eller generell informasjon. Bruk dette for 'hvordan'-spørsmål.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Søketekst"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_sql_query",
                "description": "Kjør en database-analyse for å svare på spørsmål om eiendommer, kontrakter, kostnader eller statistikk.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "Spørsmålet som skal besvares med SQL"}
                    },
                    "required": ["question"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lookup_properties",
                "description": "Søk etter spesifikke eiendommer ved navn eller adresse.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Navn eller adresse"}
                    },
                    "required": ["search_term"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lookup_parties",
                "description": "Søk etter parter (leietakere/leverandører) ved navn eller orgnr. Returnerer part med tilknyttede kontrakter og eiendommer. Bruk for spørsmål som 'har vi kontrakt med X', 'leietaker Y', 'part Z'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Navn eller orgnr (f.eks. 'Pir', 'Acme')"}
                    },
                    "required": ["search_term"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lookup_familievernkontor_bufdir",
                "description": "Nasjonal oversikt over familievernkontor fra Bufdir (offisielt navn, telefon, e-post, region, kontakttekst). Bruk for spørsmål om familievernkontor/familievern/fvk som ikke bare handler om BEFS-eiendommer i databasen, eller når brukeren vil ha Bufdir-info.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Sted, region, kommune eller navn (f.eks. Arendal, Tromsø, familievern)"}
                    },
                    "required": ["search_term"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_lovdata",
                "description": "Søk i lover, forskrifter og juridiske dokumenter fra Lovdata. Bruk dette for spørsmål om husleieloven, HMS-krav, kontraktsrett, universell utforming og andre juridiske spørsmål.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Søketekst på norsk (f.eks. 'husleieloven indeksregulering')"},
                        "limit": {"type": "integer", "description": "Antall resultater (standard 5)", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "assess_property_risk",
                "description": "Vurder risiko for eiendom basert på eksterne data fra NVE, Kartverket og Miljødirektoratet. Bruk dette for spørsmål om flomfare, grunnforhold, miljørisiko og samlet risikoscore.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_id": {"type": "string", "description": "Eiendoms-ID eller navn/adresse"},
                        "risk_types": {"type": "array", "description": "Spesifikke risikotyper å vurdere", "items": {"type": "string", "enum": ["flood", "geotechnical", "environmental", "all"]}, "default": ["all"]}
                    },
                    "required": ["property_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_jira_issue",
                "description": "Opprett en ny sak/to-do i Jira. Bruk dette NÅR brukeren ber om å lage en oppgave, registrere en feil, lage en to-do eller lignende.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Kort tittel på saken"},
                        "description": {"type": "string", "description": "Detaljert beskrivelse"},
                        "project_key": {"type": "string", "description": "Prosjekt (standard 'KAN' for BEFS)", "default": "KAN"},
                        "issue_type": {"type": "string", "description": "Type sak (Task, Epic, Bug)", "default": "Task"}
                    },
                    "required": ["summary", "description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "lookup_building_components",
                "description": "Søk etter utstyr og bygningskomponenter. Returnerer navn, type, systemkode og hierarki (hva som hører til hva). Bruk dette for spørsmål om ventilasjon, varme, dører, heiser osv.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Søketekst (navn, systemkode eller type)"},
                        "property_id": {"type": "string", "description": "Filtrer på eiendoms-ID (valgfritt)"}
                    },
                    "required": ["search_term"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_ssb_statistics",
                "description": "Hent offisiell statistikk fra SSB (Statistisk sentralbyrå). Bruk for KPI, konsumprisindeks, boligpriser, befolkning, lønn, næringsstruktur osv. Returnerer tabell med tall. Bruk dette når brukeren spør om nasjonal/offisiell statistikk, inflasjon, KPI-utvikling, eller for å sammenligne våre tall mot markedet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Søk i SSB Statbank (f.eks. 'KPI', 'konsumprisindeks', 'boligpriser', 'befolkning')"},
                        "table_id": {"type": "string", "description": "Spesifikk tabell-ID (f.eks. 14707 for KPI årstall). Valgfritt – bruk query for å finne tabell."},
                        "value_codes": {"type": "object", "description": "Filtre som Tid=2024*, top(5) for siste 5 perioder. Valgfritt."}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "combine_ssb_befs_data",
                "description": "Kombiner SSB-statistikk med BEFS interne data. Bruk for spørsmål som 'sammenlign våre kostnader med KPI', 'hvor ligger vi an mot nasjonal statistikk', 'kostnadsvekst vs inflasjon'. Velg befs_dataset: region_costs (kostnader per region), properties (eiendommer per region), contracts (kontrakter per region). join_key: region, kommune eller year.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_id": {"type": "string", "description": "SSB tabell-ID (f.eks. 14707 for KPI)"},
                        "befs_dataset": {"type": "string", "description": "BEFS-datasett: region_costs, properties eller contracts", "enum": ["region_costs", "properties", "contracts"]},
                        "join_key": {"type": "string", "description": "Slå sammen på: region, kommune eller year", "enum": ["region", "kommune", "year"]},
                        "year": {"type": "integer", "description": "År for BEFS-data (standard 2025)"}
                    },
                    "required": ["table_id", "befs_dataset", "join_key"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_barnevern_reference_context",
                "description": "Hent Bufdir/Storting/SSB referanselister (St.prp./Prop, årsrapport-lenker, SSB tabell-kortliste) som BEFS lagrer lokalt. Bruk for proposisjoner, årsrapport, overordnet ramme, eller relevante SSB-tabeller for barnevern.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "all | stprp | annual | ssb",
                            "enum": ["all", "stprp", "annual", "ssb"],
                            "default": "all",
                        },
                        "max_items": {
                            "type": "integer",
                            "description": "Maks antall linjer per del (1–40)",
                            "default": 12,
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_finans_prediksjon_excel_summary",
                "description": "Les tekstlig sammendrag av prediksjon-Excel (finans/Prediksjon_*_Økonomi eller Lønn): antagelser og nøkkeltall per ark. For DB-tall bruk SQL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Valgfritt eksakt filnavn; tom = nyeste fil av valgt type",
                            "default": "",
                        },
                        "file_type": {
                            "type": "string",
                            "description": "okonomi eller lonn",
                            "enum": ["okonomi", "lonn"],
                            "default": "okonomi",
                        },
                        "max_rows_per_sheet": {
                            "type": "integer",
                            "description": "Rader per ark (8–60)",
                            "default": 28,
                        },
                    },
                    "required": [],
                },
            },
        },
    ]

    async def _tool_search_documents(self, db: AsyncSession, query: str) -> str:
        """Tool: Search documents."""
        try:
            # Generate embedding
            embedding = await self._generate_embedding(query)
            
            if embedding:
                from app.services.search.search_service import search_hybrid
                docs = await search_hybrid(db, query, embedding, limit=SEARCH_LIMIT)
            else:
                from app.services.search.search_service import search_fulltext
                docs = await search_fulltext(db, query, limit=SEARCH_LIMIT)
            
            if not docs:
                return "Ingen dokumenter funnet."
                
            # Format docs for context
            formatted = []
            for doc in docs:
                source = doc.get("source_file", "Ukjent")
                content = doc.get("content", "")[:MAX_DOC_CONTENT_LENGTH].replace("\n", " ")
                formatted.append(f"KILDE: {source}\nINNHOLD: {content}")
                
            return "\n\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Tool search_documents failed: {e}")
            return f"Feil ved dokumentsøk: {str(e)}"

    async def _tool_run_sql(self, db: AsyncSession, question: str) -> Any:
        """Tool: Run SQL analysis. Dict med formatted + valgfri tabular for diagram."""
        try:
            results = await self._handle_sql_analysis(db, question)
            if not results or not results[0].get("content"):
                return {
                    "formatted": "Ingen resultater fra databasen.",
                    "structured_sources": [],
                }
            block = results[0]
            out: Dict[str, Any] = {
                "formatted": block["content"],
                "structured_sources": [],
            }
            if block.get("tabular"):
                out["tabular"] = block["tabular"]
            return out
        except Exception as e:
            return {
                "formatted": f"Feil ved SQL-analyse: {str(e)}",
                "structured_sources": [],
            }

    async def _tool_lookup_properties(self, db: AsyncSession, search_term: str) -> Dict[str, Any]:
        """Tool: Lookup properties. Returns formatted string and structured_sources for links.
        Søker i name, address og usage (f.eks. familievern i usage-feltet)."""
        try:
            # Input validation
            if not search_term or len(search_term.strip()) < 2:
                return {"formatted": "Angi minst to tegn for å søke etter eiendom.", "structured_sources": []}

            # Escape LIKE special characters to avoid unintended wildcard behavior
            search_term_clean = search_term.strip().replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{search_term_clean}%"
            limit = LOOKUP_PROPERTIES_LIMIT
            result = await db.execute(text("""
                SELECT
                    p.property_id, p.name, p.address, p.city, p.region,
                    p.department_code,
                    p.approved_places, p.budgeted_places,
                    p.unit_type_derived, p.affiliation,
                    -- Aktiv kontrakt: husleie + tilleggskostnader
                    c.amount->>'amount_per_year'                        AS husleie_per_ar,
                    c.external_data->>'internal_maintenance_cost'       AS indre_vedlikehold,
                    c.external_data->>'user_dependent_costs'            AS brukeravhengige,
                    c.external_data->>'common_costs'                    AS felleskostnader,
                    -- total_annual_cost = sum av ALLE kontrakter i komplekset (ikke kun én eiendom)
                    c.external_data->>'total_annual_cost'               AS total_kostnad_kompleks,
                    c.external_data->>'contract_name'                   AS kontraktsnavn,
                    jsonb_array_length(
                        CASE WHEN jsonb_typeof(c.external_data->'additional_costs') = 'array'
                             THEN c.external_data->'additional_costs' ELSE '[]'::jsonb END
                    )                                                   AS antall_tilknyttede_kontrakter
                FROM properties p
                LEFT JOIN units u ON u.property_id = p.property_id
                LEFT JOIN contracts c ON c.unit_id = u.unit_id AND c.status = 'active'
                WHERE p.name ILIKE :q OR p.address ILIKE :q OR COALESCE(p.usage, '') ILIKE :q
                ORDER BY p.name
                LIMIT :limit
            """), {"q": pattern, "limit": limit})

            rows = result.fetchall()
            if not rows:
                return {"formatted": "Ingen eiendommer funnet.", "structured_sources": []}

            def _fmt_nok(v) -> str:
                if v is None:
                    return ""
                try:
                    return f"{float(v):,.0f} kr".replace(",", " ")
                except (ValueError, TypeError):
                    return str(v)

            formatted = []
            structured_sources = []
            seen_props: set = set()
            for row in rows:
                pid = str(row.property_id)
                if pid in seen_props:
                    continue
                seen_props.add(pid)
                parts = [
                    f"Eiendom: {row.name or row.address}",
                    f"Adresse: {row.address}, {row.city or ''}".rstrip(", "),
                ]
                if row.region:
                    parts.append(f"Region: {row.region}")
                if row.unit_type_derived:
                    parts.append(f"Type: {row.unit_type_derived}")
                if row.affiliation:
                    parts.append(f"Tilhørighet: {row.affiliation}")
                if row.approved_places is not None and row.approved_places > 0:
                    parts.append(f"GK-plasser (godkjente): {row.approved_places}")
                if row.budgeted_places is not None and row.budgeted_places > 0:
                    parts.append(f"Budsjetterte plasser: {row.budgeted_places}")
                if row.department_code:
                    parts.append(f"Koststed: {row.department_code}")
                if row.kontraktsnavn:
                    parts.append(f"Kontrakt: {row.kontraktsnavn}")
                if row.husleie_per_ar:
                    parts.append(f"Husleie/år: {_fmt_nok(row.husleie_per_ar)}")
                if row.indre_vedlikehold:
                    parts.append(f"Indre vedlikehold: {_fmt_nok(row.indre_vedlikehold)}")
                if row.brukeravhengige:
                    parts.append(f"Brukeravhengige kostnader: {_fmt_nok(row.brukeravhengige)}")
                if row.felleskostnader:
                    parts.append(f"Felleskostnader: {_fmt_nok(row.felleskostnader)}")
                if row.total_kostnad_kompleks:
                    n_extra = (row.antall_tilknyttede_kontrakter or 0)
                    note = f" (sum for hele komplekset, inkl. {n_extra} tilknyttede kontrakter)" if n_extra > 0 else " (sum for komplekset)"
                    parts.append(f"Total kostnad kompleks{note}: {_fmt_nok(row.total_kostnad_kompleks)}")
                parts.append(f"ID: {pid}")
                formatted.append(" | ".join(parts))
                structured_sources.append({
                    "type": "property",
                    "id": pid,
                    "name": (row.name or row.address or "Eiendom")[:80],
                })
            return {"formatted": "\n".join(formatted), "structured_sources": structured_sources}
        except Exception as e:
            return {"formatted": f"Feil ved eiendomssøk: {str(e)}", "structured_sources": []}

    async def _tool_lookup_parties(self, db: AsyncSession, search_term: str) -> Dict[str, Any]:
        """Tool: Lookup parties (leietakere/leverandører) by name or orgnr. Returns formatted string and structured_sources."""
        try:
            # Input validation (already exists, but let's enhance it)
            if not search_term or len(search_term.strip()) < 2:
                return {"formatted": "Angi minst to tegn for å søke etter part.", "structured_sources": []}

            # Escape LIKE special characters
            search_term_clean = search_term.strip().replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{search_term_clean}%"
            limit = 50
            result = await db.execute(text("""
                SELECT p.party_id, p.name AS party_name, p.orgnr, c.contract_id, c.category,
                       prop.name AS property_name
                FROM parties p
                LEFT JOIN contracts c ON c.party_id = p.party_id
                LEFT JOIN units u ON c.unit_id = u.unit_id
                LEFT JOIN properties prop ON u.property_id = prop.property_id
                WHERE p.name ILIKE :q OR p.orgnr::text LIKE :q
                ORDER BY p.name, c.contract_id
                LIMIT :limit
            """), {"q": pattern, "limit": limit})
            rows = result.fetchall()
            if not rows:
                return {"formatted": f"Ingen parter funnet som matcher «{search_term.strip()}».", "structured_sources": []}
            by_party: Dict[tuple, List[Any]] = {}
            for r in rows:
                key = (r.party_id, r.party_name or "-", r.orgnr)
                if key not in by_party:
                    by_party[key] = []
                by_party[key].append(r)
            lines = []
            structured_sources = []
            for (pid, pname, orgnr), party_rows in by_party.items():
                lines.append(f"Part: {pname} (ID: {pid})" + (f", orgnr: {orgnr}" if orgnr else ""))
                structured_sources.append({"type": "party", "id": str(pid), "name": (pname or "Part")[:80]})
                for r in party_rows:
                    if r.contract_id:
                        lines.append(f"  – Kontrakt: {r.category or '-'}, Eiendom: {r.property_name or '-'}")
                        structured_sources.append({
                            "type": "contract",
                            "id": str(r.contract_id),
                            "name": (r.category or "Kontrakt")[:80],
                        })
                        break
                if not any(r.contract_id for r in party_rows):
                    lines.append("  – Ingen kontrakter registrert")
            return {"formatted": "\n".join(lines), "structured_sources": structured_sources}
        except Exception as e:
            logger.warning(f"lookup_parties failed: {e}")
            return {"formatted": f"Feil ved partsøk: {str(e)}", "structured_sources": []}

    def _tool_lookup_familievernkontor_bufdir(self, search_term: str) -> Dict[str, Any]:
        """Bufdir familievernkontor (JSON i backend/data, følger med deploy)."""
        try:
            from app.services.familievernkontor_bufdir_knowledge import search_bufdir_familievernkontor

            text = search_bufdir_familievernkontor((search_term or "").strip(), limit=8)
            src = {
                "type": "web",
                "name": "Bufdir – familievernkontorer",
                "url": "https://www.bufdir.no/familie/familievernkontorer/",
            }
            if not text:
                return {
                    "formatted": "Ingen treff i Bufdir-familievernkontor for dette søket (eller datafil mangler på server).",
                    "structured_sources": [src],
                }
            return {"formatted": text, "structured_sources": [src]}
        except Exception as e:
            logger.warning("lookup_familievernkontor_bufdir failed: %s", e)
            return {
                "formatted": f"Feil ved Bufdir oppslag: {str(e)}",
                "structured_sources": [],
            }

    async def _tool_search_lovdata(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Tool: Search laws and regulations in Lovdata. Returns formatted string and structured_sources."""
        try:
            from app.services.external.api_clients.lovdata_client import LovdataClient
            
            client = LovdataClient()
            results = await client.search(query, limit=limit)
            
            items = results.get("results") or results.get("items") or []
            
            if not items:
                return {"formatted": f"Ingen lovdata-treff funnet for '{query}'.", "structured_sources": []}
            
            formatted = []
            structured_sources = []
            for idx, item in enumerate(items[:limit], 1):
                title = item.get("title") or item.get("name") or "Uten tittel"
                summary = item.get("summary") or item.get("snippet") or "Ingen beskrivelse."
                doc_id = item.get("id", "ukjent")
                url = item.get("url") or f"https://lovdata.no/dokument/{doc_id}"
                formatted.append(f"**[{idx}] {title}**\n{summary}\nLenke: {url}")
                structured_sources.append({"type": "lovdata", "name": title[:80], "url": url})
            
            header = f"Fant {len(items)} treff i Lovdata for '{query}':\n\n"
            return {"formatted": header + "\n\n".join(formatted), "structured_sources": structured_sources}
            
        except Exception as e:
            logger.error(f"Lovdata search failed: {e}")
            return {"formatted": f"Feil ved søk i Lovdata: {str(e)}", "structured_sources": []}

    async def _tool_assess_property_risk(self, property_id: str, risk_types: List[str] = None, db: AsyncSession = None) -> str:
        """Tool: Assess property risk using available risk services."""
        try:
            session = db or getattr(self, "db", None)
            if not session:
                return "Database-tilkobling mangler for risikovurdering."
            # Get property info first
            property_info = None
            if property_id:
                # Try to find property by ID or name/address
                from sqlalchemy import text
                result = await session.execute(text("""
                    SELECT property_id, name, address, city, latitude, longitude
                    FROM properties
                    WHERE property_id = :pid OR name ILIKE :name OR address ILIKE :addr
                    LIMIT 1
                """), {"pid": property_id, "name": f"%{property_id}%", "addr": f"%{property_id}%"})
                property_info = result.fetchone()
            
            if not property_info:
                return f"Fant ikke eiendom med ID/navn: {property_id}"
            
            # Try to use ExternalRiskService if available
            try:
                from app.services.risk.external_risk_service import ExternalRiskService
                risk_service = ExternalRiskService()
                
                # Determine which risk types to assess
                risk_types_to_assess = risk_types or ["all"]
                
                # Perform risk assessment
                risk_result = await risk_service.assess_property_risk(
                    property_id=property_info.property_id,
                    latitude=property_info.latitude,
                    longitude=property_info.longitude,
                    risk_types=risk_types_to_assess
                )
                
                # Format result for LLM
                formatted = []
                overall_score = risk_result.get("overall_score", 0)
                
                formatted.append(f"**Samlet risikoscore: {overall_score}/100**")
                
                if overall_score < 30:
                    formatted.append("🟢 **Lav risiko** - Eiendommen har minimal risiko")
                elif overall_score < 70:
                    formatted.append("🟡 **Moderat risiko** - Noen risikofaktorer identifisert")
                else:
                    formatted.append("🔴 **Høy risiko** - Signifikante risikofaktorer funnet")
                
                # Add specific risk details
                if "flood_risk" in risk_result:
                    formatted.append(f"\n🌊 **Flomfare:** {risk_result['flood_risk']['score']}/100")
                    formatted.append(f"   Kilde: {risk_result['flood_risk']['source']}")
                    # Add link to NVE Flood map if score is high
                    if risk_result['flood_risk']['score'] > 0:
                        formatted.append("   [Se flomkart på NVE](https://www.nve.no/flom-og-skred/varsling/flomvarsling/)")
                
                if "geotechnical_risk" in risk_result:
                    formatted.append(f"\n🏔️ **Grunnforhold:** {risk_result['geotechnical_risk']['score']}/100")
                    formatted.append(f"   Kilde: {risk_result['geotechnical_risk']['source']}")
                    if risk_result['geotechnical_risk']['score'] > 0:
                        formatted.append("   [Se skredkart på NVE](https://www.nve.no/flom-og-skred/varsling/jordskredvarsling/)")
                
                if "environmental_risk" in risk_result:
                    formatted.append(f"\n🌱 **Miljørisiko:** {risk_result['environmental_risk']['score']}/100")
                    formatted.append(f"   Kilde: {risk_result['environmental_risk']['source']}")
                    if risk_result['environmental_risk']['score'] > 0:
                        formatted.append("   [Se grunnforurensning](https://grunnforurensning.miljodirektoratet.no/)")
                
                # Add recommendations if available
                if "recommendations" in risk_result and risk_result["recommendations"]:
                    formatted.append("\n💡 **Anbefalinger:**")
                    for rec in risk_result["recommendations"]:
                        formatted.append(f"   - {rec}")
                
                return "\n".join(formatted)
                
            except ImportError:
                # Fallback: Use basic accessibility risk assessment if ExternalRiskService not available
                from app.services.risk_assessment_service import RiskAssessmentService
                
                risk_service = RiskAssessmentService(session)
                accessibility_risk = await risk_service.calculate_accessibility_risk(property_info.property_id)
                
                # Format basic risk result
                formatted = []
                formatted.append(f"**Tilgjengelighetsrisiko: {accessibility_risk['risk_score']}/100")
                formatted.append(f"🟡 **Kategori:** {accessibility_risk['risk_category']}")
                formatted.append(f"\n📍 **Basert på:** Proximity til nødvendige tjenester")
                
                if accessibility_risk['factors']:
                    formatted.append("\n📋 **Faktorer:**")
                    for factor in accessibility_risk['factors']:
                        formatted.append(f"   - {factor}")
                
                if accessibility_risk['message']:
                    formatted.append(f"\n💡 **Melding:** {accessibility_risk['message']}")
                
                return "\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return f"Feil ved risikovurdering: {str(e)}"

    async def _tool_create_jira_issue(self, summary: str, description: str, project_key: str = "KAN", issue_type: str = "Task") -> str:
        """Tool: Create a Jira issue."""
        try:
            from app.services.jira_service import jira_service
            
            if not jira_service.is_configured():
                return "Jira integration is not configured. I cannot create issues at the moment."
            
            # Create the issue
            issue = await asyncio.to_thread(
                jira_service.create_issue,
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            
            if issue:
                key = issue.get("key")
                url = issue.get("url") or f"{settings.JIRA_URL}/browse/{key}"
                return f"✅ Opprettet Jira-sak: **[{key}] {summary}**\nLenke: {url}"
            else:
                return "Kunne ikke opprette Jira-sak (ingen respons fra Jira)."
                
        except Exception as e:
            logger.error(f"Failed to create Jira issue: {e}")
            return f"Feil ved opprettelse av Jira-sak: {str(e)}"

    async def _tool_lookup_building_components(self, db: AsyncSession, search_term: str, property_id: str = None) -> Dict[str, Any]:
        """Tool: Lookup building components (FDV / Semantic Data)."""
        try:
            if not search_term or len(search_term.strip()) < 2:
                return {"formatted": "Angi minst to tegn for å søke etter komponenter.", "structured_sources": []}

            search_clean = search_term.strip().replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{search_clean}%"
            
            # Base query
            query_str = """
                SELECT 
                    c.component_id, c.name, c.system_code, c.brick_class, 
                    p.name as property_name, parent.name as parent_name
                FROM building_components c
                JOIN properties p ON c.property_id = p.property_id
                LEFT JOIN building_components parent ON c.parent_id = parent.component_id
                WHERE (c.name ILIKE :q OR c.system_code ILIKE :q OR c.brick_class ILIKE :q)
            """
            
            params = {"q": pattern, "limit": 20}
            
            if property_id:
                query_str += " AND c.property_id = CAST(:pid AS uuid)"
                params["pid"] = property_id
                
            query_str += " ORDER BY c.system_code, c.name LIMIT :limit"
            
            result = await db.execute(text(query_str), params)
            rows = result.fetchall()
            
            if not rows:
                return {"formatted": f"Ingen komponenter funnet for '{search_term}'.", "structured_sources": []}
                
            lines = []
            structured_sources = []
            
            for r in rows:
                c_name = r.name or "Ukjent"
                sys_code = r.system_code or ""
                brick = r.brick_class or ""
                prop = r.property_name or "Ukjent eiendom"
                parent = r.parent_name
                
                info = f"**{c_name}** ({prop})"
                if sys_code: info += f" [System: {sys_code}]"
                if brick: info += f" [Type: {brick}]"
                if parent: info += f" -> Tilhører: {parent}"
                
                lines.append(info)
                
                structured_sources.append({
                    "type": "component",
                    "id": str(r.component_id),
                    "name": c_name,
                    "relevance": 1.0
                })
                
            return {"formatted": "\n".join(lines), "structured_sources": structured_sources}

        except Exception as e:
            logger.error(f"Failed to lookup components: {e}")
            return {"formatted": f"Feil ved komponentsøk: {str(e)}", "structured_sources": []}

    async def _tool_fetch_ssb_statistics(
        self,
        query: str,
        table_id: Optional[str] = None,
        value_codes: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Tool: Fetch statistics from SSB Statbank Norway. Returnerer dict med formatted + tabular for diagram."""
        try:
            from app.services.external.api_clients.ssb_pxweb_client import SSBPxWebClient
            from app.services.external.ssb_json_stat_flatten import flatten_json_stat2_for_chart

            client = SSBPxWebClient()
            tid = table_id
            table_label = ""
            if not tid:
                search = await client.search_tables(query=query, page=1, page_size=5)
                tables = search.get("tables") or []
                if not tables:
                    return {
                        "formatted": f"Ingen SSB-tabeller funnet for søket «{query}».",
                        "structured_sources": [],
                    }
                tid = tables[0].get("id")
                table_label = (tables[0].get("label", "") or "")[:80]
                if not tid:
                    return {"formatted": "Kunne ikke hente SSB-tabell-ID.", "structured_sources": []}

            data = await client.get_data(
                table_id=tid,
                value_codes=value_codes or {"Tid": "top(5)"},
                output_format="json-stat2",
            )
            if not data or not isinstance(data, dict):
                return {"formatted": "Ingen data returnert fra SSB.", "structured_sources": []}

            # Parse json-stat2 to readable text (simplified)
            value = data.get("value") or []
            dimension = data.get("dimension") or {}
            id_dims = data.get("id") or []
            if not value or not id_dims:
                return {"formatted": "SSB-data har uventet format.", "structured_sources": []}

            dims = []
            for key in id_dims:
                d = dimension.get(key, {})
                cat = d.get("category", {})
                idx = cat.get("index") or {}
                lbl = cat.get("label") or {}
                codes = sorted(idx.keys(), key=lambda c: idx.get(c, 0))
                dims.append({"key": key, "label": lbl, "codes": codes})

            lines = ["SSB STATISTIKK (Statistisk sentralbyrå):"]
            if table_label:
                lines.append(f"Tabell: {table_label} ({tid})")
            header = [d["key"] for d in id_dims] + ["verdi"]
            lines.append(" | ".join(header))

            # Simple row-major iteration (json-stat2 order)
            idx = 0

            def iter_rows(di: int, acc: List[str]) -> None:
                nonlocal idx
                if idx >= len(value) or len(lines) >= 25:
                    return
                if di >= len(dims):
                    v = value[idx]
                    val_str = str(round(float(v), 2)) if isinstance(v, (int, float)) else str(v)
                    lines.append(" | ".join(acc + [val_str]))
                    idx += 1
                    return
                dim = dims[di]
                for code in dim["codes"][:12]:
                    if idx >= len(value) or len(lines) >= 25:
                        return
                    lbl = (dim["label"].get(code, code) or code)[:25]
                    iter_rows(di + 1, acc + [lbl])

            iter_rows(0, [])
            ssb_url = f"https://www.ssb.no/statbank/table/{tid}/"
            structured_sources = [
                {
                    "type": "web",
                    "name": f"SSB tabell {tid}" + (f" – {table_label}" if table_label else ""),
                    "url": ssb_url,
                    "relevance": 1.0,
                }
            ]
            tabular = flatten_json_stat2_for_chart(data, max_rows=2500)
            out: Dict[str, Any] = {
                "formatted": "\n".join(lines),
                "structured_sources": structured_sources,
            }
            if tabular:
                out["tabular"] = tabular
            return out
        except Exception as e:
            logger.error("fetch_ssb_statistics failed: %s", e)
            return {
                "formatted": f"Feil ved henting av SSB-statistikk: {str(e)}",
                "structured_sources": [],
            }

    async def _tool_combine_ssb_befs_data(
        self,
        db: AsyncSession,
        table_id: str,
        befs_dataset: str,
        join_key: str,
        year: int = 2025,
        user: Optional["User"] = None,
    ) -> Any:
        """Tool: Combine SSB data with BEFS internal data. user is injected by create_befs_tools."""
        try:
            from app.services.external.api_clients.ssb_pxweb_client import SSBPxWebClient
            from app.services.external.ssb_json_stat_flatten import flatten_json_stat2_for_chart
            from app.api.v1.ssb_api import _load_befs_region_costs
            from app.core.property_access import filter_properties_by_access
            from sqlalchemy import select
            from app.domains.core.models.property import Property
            from app.domains.core.models.contract import Contract
            from app.domains.core.models.unit import Unit
            from sqlalchemy.orm import selectinload

            client = SSBPxWebClient()
            ssb_raw = await client.get_data(
                table_id=table_id,
                value_codes={"Tid": "top(5)"},
                output_format="json-stat2",
            )

            if befs_dataset == "region_costs":
                befs_data = _load_befs_region_costs(year)
                befs_by_key = befs_data.get("by_region", {})
            elif befs_dataset == "properties":
                result = await db.execute(select(Property))
                all_props = result.scalars().all()
                if user:
                    filtered = await filter_properties_by_access(db=db, user=user, properties=list(all_props))
                else:
                    filtered = all_props
                by_region = {}
                for p in filtered:
                    r = p.region or "Ukjent"
                    by_region[r] = by_region.get(r, 0) + 1
                befs_by_key = by_region
            elif befs_dataset == "contracts":
                stmt = select(Contract).options(selectinload(Contract.unit).selectinload(Unit.property))
                result = await db.execute(stmt)
                contracts = result.scalars().all()
                all_props = [c.unit.property for c in contracts if c.unit and c.unit.property]
                unique = list({p.property_id: p for p in all_props}.values())
                if user:
                    filtered = await filter_properties_by_access(db=db, user=user, properties=unique)
                    allowed = {p.property_id for p in filtered}
                else:
                    allowed = {p.property_id for p in unique}
                by_region = {}
                for c in contracts:
                    if c.unit and c.unit.property and c.unit.property.property_id in allowed:
                        r = c.unit.property.region or "Ukjent"
                        by_region[r] = by_region.get(r, 0) + 1
                befs_by_key = by_region
            else:
                return {
                    "formatted": f"Ukjent befs_dataset: {befs_dataset}",
                    "structured_sources": [],
                }

            lines = [
                f"KOMBINERT SSB + BEFS (år {year}, join på {join_key}):",
                "",
                "BEFS-data:",
            ]
            for k, v in sorted(befs_by_key.items(), key=lambda x: -x[1])[:15]:
                lines.append(f"  {k}: {v:,.0f}".replace(",", " ") if isinstance(v, (int, float)) else f"  {k}: {v}")
            lines.append("")

            # Parse SSB json-stat2 (same logic as _tool_fetch_ssb_statistics)
            ssb_lines: List[str] = ["SSB-data (Statistisk sentralbyrå):"]
            if ssb_raw and isinstance(ssb_raw, dict):
                s_value = ssb_raw.get("value") or []
                s_dimension = ssb_raw.get("dimension") or {}
                s_id_dims = ssb_raw.get("id") or []
                ssb_dims = []
                for key in s_id_dims:
                    d = s_dimension.get(key, {})
                    cat = d.get("category", {})
                    idx_map = cat.get("index") or {}
                    lbl_map = cat.get("label") or {}
                    codes = sorted(idx_map.keys(), key=lambda c: idx_map.get(c, 0))
                    ssb_dims.append({"key": key, "label": lbl_map, "codes": codes})
                if ssb_dims and s_value:
                    ssb_lines.append("  " + " | ".join(d["key"] for d in ssb_dims) + " | verdi")
                val_idx_s = 0

                def _iter_ssb(di: int, acc: List[str]) -> None:
                    nonlocal val_idx_s
                    if val_idx_s >= len(s_value) or len(ssb_lines) >= 20:
                        return
                    if di >= len(ssb_dims):
                        v = s_value[val_idx_s]
                        vs = str(round(float(v), 2)) if isinstance(v, (int, float)) else str(v)
                        ssb_lines.append("  " + " | ".join(acc + [vs]))
                        val_idx_s += 1
                        return
                    dim = ssb_dims[di]
                    for code in dim["codes"][:10]:
                        if val_idx_s >= len(s_value) or len(ssb_lines) >= 20:
                            return
                        lbl_str = (dim["label"].get(code, code) or code)[:25]
                        _iter_ssb(di + 1, acc + [lbl_str])

                _iter_ssb(0, [])
            else:
                ssb_lines.append("  (ingen data fra SSB)")
            lines.extend(ssb_lines)
            ssb_url = f"https://www.ssb.no/statbank/table/{table_id}/"
            structured_sources = [
                {
                    "type": "web",
                    "name": f"SSB tabell {table_id}",
                    "url": ssb_url,
                    "relevance": 1.0,
                }
            ]
            out: Dict[str, Any] = {
                "formatted": "\n".join(lines),
                "structured_sources": structured_sources,
            }
            if ssb_raw and isinstance(ssb_raw, dict):
                tabular = flatten_json_stat2_for_chart(ssb_raw, max_rows=2500)
                if tabular:
                    out["tabular"] = tabular
            return out
        except Exception as e:
            logger.error("combine_ssb_befs_data failed: %s", e)
            return {
                "formatted": f"Feil ved kombinasjon av SSB og BEFS: {str(e)}",
                "structured_sources": [],
            }

    async def get_proactive_insights(
        self,
        db: AsyncSession,
        context: ChatContext
    ) -> List[Dict[str, Any]]:
        """
        Level 4: Generate proactive insights based on user context.
        """
        insights = []
        try:
            tasks = []
            
            # 1. Property Context Task
            if context.entity_type == "property" and context.entity_id:
                tasks.append(self._check_expiring_contracts(db, context.entity_id))
            else:
                tasks.append(asyncio.sleep(0)) # No-op placeholder

            # 2. Dashboard Context Task
            if context.page == "dashboard":
                tasks.append(self._get_portfolio_stats(db))
            else:
                tasks.append(asyncio.sleep(0)) # No-op placeholder
                
            # Execute in parallel
            results = await asyncio.gather(*tasks)
            
            # Unpack results
            contract_insight = results[0] if isinstance(results[0], dict) else None
            portfolio_insight = results[1] if isinstance(results[1], dict) else None
            
            if contract_insight:
                insights.append(contract_insight)
            if portfolio_insight:
                insights.append(portfolio_insight)

        except Exception as e:
            logger.error(f"Proactive insights failed: {e}")
        
        return insights

    async def _check_expiring_contracts(self, db: AsyncSession, property_id: str) -> Optional[Dict]:
        """Helper to check expiring contracts."""
        try:
            result = await db.execute(text("""
                SELECT c.contract_id, p.name as party_name, c.periods->>'end' as end_date
                FROM contracts c
                JOIN units u ON c.unit_id = u.unit_id
                JOIN parties p ON c.party_id = p.party_id
                WHERE u.property_id = :pid
                AND (c.periods->>'end')::date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '6 months')
            """), {"pid": property_id})
            
            rows = result.fetchall()
            if rows:
                items = "\n".join([f"- {r.party_name} (Utløper: {r.end_date})" for r in rows])
                return {
                    "type": "warning",
                    "content": f"⚠️ **Utløpende kontrakter:**\n{items}\n\nVil du se detaljer eller starte reforhandling?"
                }
        except Exception:
            return None
        return None

    async def _get_portfolio_stats(self, db: AsyncSession) -> Optional[Dict]:
        """Helper to check portfolio stats."""
        try:
            stats = await db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN total_area > 5000 THEN 1 END) as large_props
                FROM properties
            """))
            s = stats.fetchone()
            if s:
                return {
                    "type": "info",
                    "content": f"📊 **Portefølje Status:**\nDu har {s.total} eiendommer, hvorav {s.large_props} er større enn 5000 m². \n\nSkal jeg analysere ledighet for deg?"
                }
        except Exception:
            return None
        return None

    async def _get_page_context_summary(self, db: AsyncSession, context: "ChatContext") -> Optional[str]:
        """Hent kort sammendrag for siden brukeren ser på (kontrakt/part/eiendom). Brukes for å gi Writer sidekontekst."""
        if not context or not context.entity_type or not context.entity_id:
            return None
        try:
            eid = context.entity_id.strip()
            if context.entity_type == "contract":
                result = await db.execute(text("""
                    SELECT c.category,
                           c.external_data->>'contract_name' AS contract_name,
                           p.name AS party_name,
                           prop.name AS property_name
                    FROM contracts c
                    LEFT JOIN parties p ON c.party_id = p.party_id
                    LEFT JOIN units u ON c.unit_id = u.unit_id
                    LEFT JOIN properties prop ON u.property_id = prop.property_id
                    WHERE c.contract_id = CAST(:eid AS uuid)
                    LIMIT 1
                """), {"eid": eid})
                row = result.fetchone()
                if row:
                    name = (row.contract_name or row.category or "Kontrakt")[:80]
                    party = (row.party_name or "Ukjent part")[:50]
                    prop = (row.property_name or "Ukjent eiendom")[:50]
                    return f"Kontrakt: {name}. Part: {party}. Eiendom: {prop}."
            elif context.entity_type == "party":
                result = await db.execute(text("""
                    SELECT p.name AS party_name,
                           (SELECT COUNT(*) FROM contracts c WHERE c.party_id = p.party_id) AS contract_count
                    FROM parties p
                    WHERE p.party_id = CAST(:eid AS uuid)
                    LIMIT 1
                """), {"eid": eid})
                row = result.fetchone()
                if row:
                    name = (row.party_name or "Part")[:80]
                    cnt = row.contract_count or 0
                    return f"Part: {name}. Antall kontrakter: {cnt}."
            elif context.entity_type == "property":
                result = await db.execute(text("""
                    SELECT name, address
                    FROM properties
                    WHERE property_id = CAST(:eid AS uuid)
                    LIMIT 1
                """), {"eid": eid})
                row = result.fetchone()
                if row:
                    name = (row.name or row.address or "Eiendom")[:80]
                    addr = (row.address or "")[:60]
                    return f"Eiendom: {name}. Adresse: {addr}." if addr else f"Eiendom: {name}."
            elif context.entity_type == "case":
                result = await db.execute(text("""
                    SELECT title, status, priority, 
                           (SELECT name FROM properties WHERE property_id = c.property_id) AS property_name
                    FROM internal_control_cases c
                    WHERE c.case_id = CAST(:eid AS uuid)
                    LIMIT 1
                """), {"eid": eid})
                row = result.fetchone()
                if row:
                    return f"Sak/Tiltak: {row.title}. Status: {row.status}. Prioritet: {row.priority}. Eiendom: {row.property_name or 'Ukjent'}."
            elif context.entity_type == "deviation":
                # Vi antar deviations kan ligge i en tabell som heter 'deviations' 
                # eller er knyttet til sjekklister. Sjekker her 'internal_control_cases' som fallback.
                result = await db.execute(text("""
                    SELECT title, status FROM internal_control_cases 
                    WHERE case_id = CAST(:eid AS uuid) LIMIT 1
                """), {"eid": eid})
                row = result.fetchone()
                if row:
                    return f"Avvik: {row.title}. Status: {row.status}."
        except Exception as e:
            logger.debug("Page context summary failed: %s", e)
        return None

    def _get_role_label(self, role: str) -> str:
        """Oversetter systemroller til norske brukernavn for persona-tilpasning."""
        if not role:
            return "bruker"
        mapping = {
            "ADMIN": "Bufdir (Administrator)",
            "REGIONAL_MANAGER": "Regionleder",
            "PROPERTY_MANAGER": "Eiendomsforvalter",
            "JANITOR": "Vaktmester"
        }
        return mapping.get(role.upper(), role)

    async def _get_user_workload_summary(self, db: AsyncSession, user: User) -> Optional[str]:
        """Hent sammendrag av brukerens aktive avvik og kommende aktiviteter."""
        if not user or not user.user_id:
            return None
        try:
            # 1. Aktive avvik/saker (internal_control_cases)
            res_cases = await db.execute(text("""
                SELECT COUNT(*) as cnt, 
                       (SELECT string_agg(title, ', ') FROM (SELECT title FROM internal_control_cases WHERE assigned_user_id = :uid AND status != 'closed' LIMIT 3) t) as titles
                FROM internal_control_cases
                WHERE assigned_user_id = :uid AND status != 'closed'
            """), {"uid": user.user_id})
            row_cases = res_cases.fetchone()
            
            # 2. Kommende aktiviteter (scheduled_activities) neste 30 dager
            res_acts = await db.execute(text("""
                SELECT COUNT(*) as cnt,
                       (SELECT string_agg(title, ', ') FROM (SELECT title FROM scheduled_activities WHERE assigned_user_id = :uid AND next_due_date > now() AND next_due_date < now() + interval '30 days' AND enabled = true LIMIT 3) t) as titles
                FROM scheduled_activities
                WHERE assigned_user_id = :uid 
                AND next_due_date > now() 
                AND next_due_date < now() + interval '30 days'
                AND enabled = true
            """), {"uid": user.user_id})
            row_acts = res_acts.fetchone()
            
            parts = []
            if row_cases and row_cases.cnt > 0:
                titles = row_cases.titles or "Ukjente saker"
                if row_cases.cnt > 3:
                     titles += f" og {row_cases.cnt - 3} til"
                parts.append(f"Du har {row_cases.cnt} aktive saker/avvik tildelt deg ({titles}).")
            
            if row_acts and row_acts.cnt > 0:
                titles = row_acts.titles or "Ukjente aktiviteter"
                if row_acts.cnt > 3:
                     titles += f" og {row_acts.cnt - 3} til"
                parts.append(f"Du har {row_acts.cnt} HMS-aktiviteter som forfaller snart ({titles}).")
            
            # 3. Portefølje-oversikt (hvis Admin/Manager)
            portfolio_status = ""
            user_role = user.role.value if hasattr(user.role, "value") else str(user.role)
            if user_role in [UserRole.ADMIN, UserRole.REGIONAL_MANAGER]:
                res_total = await db.execute(text("""
                    SELECT 
                        SUM(CASE WHEN status != 'closed' THEN 1 ELSE 0 END) as open_cases,
                        COUNT(*) as total_cases
                    FROM internal_control_cases
                """))
                row_total = res_total.fetchone()
                if row_total and row_total.total_cases > 0:
                    portfolio_status = f"\n\nPORTEFØLJE-STATUS:\nDet er totalt {row_total.open_cases} åpne avvik/saker i systemet."
            
            if parts:
                return "DITT ARBEID:\n" + "\n".join(parts) + portfolio_status
        except Exception as e:
            logger.debug("Workload summary failed: %s", e)
        return None

    def _extract_sources_from_state(self, final_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract sources from research_data and script_results.
        Supports structured_sources (preferred) and legacy results format.
        """
        sources: List[Dict[str, Any]] = []
        seen = set()  # Deduplicate by (type, id or url)

        def add_source(s: Dict[str, Any]) -> None:
            key = (s.get("type"), s.get("id") or s.get("url") or s.get("name", ""))
            if key in seen:
                return
            seen.add(key)
            out = {
                "type": s.get("type", "unknown"),
                "id": s.get("id"),
                "name": s.get("name", "Ukjent"),
                "relevance": s.get("relevance", 0.0),
            }
            if s.get("url"):
                out["url"] = s["url"]
            sources.append(out)

        # 1. structured_sources (from researcher or analyst)
        research_data = final_state.get("research_data", {})
        script_results = final_state.get("script_results", {})
        for src in research_data.get("structured_sources") or []:
            add_source(src)
        for key, val in script_results.items():
            if isinstance(val, dict) and "structured_sources" in val:
                for src in val.get("structured_sources", []):
                    add_source(src)

        # 2. Legacy: raw results
        if not sources:
            raw_results = research_data.get("results")
            if raw_results is not None:
                items = [raw_results] if isinstance(raw_results, str) else raw_results
                for r in items:
                    if isinstance(r, dict):
                        if "text_id" in r:
                            url = None
                            if r.get("contract_id"):
                                url = f"/contracts/{r['contract_id']}"
                            elif r.get("property_id"):
                                url = f"/properties/{r['property_id']}"
                            add_source({
                                "type": "document",
                                "id": str(r.get("text_id", "")),
                                "name": (r.get("source_file") or "Dokument")[:80],
                                "url": url,
                            })
                        else:
                            href = r.get("href") or r.get("url", "")
                            add_source({
                                "type": r.get("type", "web"),
                                "name": r.get("title", r.get("name", "Web")),
                                "url": href if href else None,
                            })
                    elif isinstance(r, str):
                        add_source({"type": "document", "name": r[:100]})

        return sources

    async def chat(
        self,
        message: str,
        context: Optional[ChatContext] = None,
        history: Optional[List[Dict[str, str]]] = None,
        db: Optional[AsyncSession] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Main chat endpoint using Native Function Calling (Tools).
        """
        if not self.client:
            return {
                "answer": "Beklager, jeg er ikke tilkoblet akkurat nå. Prøv igjen senere.",
                "sources": [],
                "error": "Client not initialized"
            }

        history = history or []
        context = context or ChatContext()
        collected_sources = []

        try:
            # 1. Prepare system prompt for Supervisor (Optional, or handled inside Supervisor)
            # For now, we just pass the user message.
            # Ideally, context is passed to the state.
            
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            from app.services.intelligence.agents.graph import app
            
            # 1. Retrieve relevant memories & Persona (kun når db er tilgjengelig)
            memories = []
            persona_text = None
            past_convos = []
            graph_context = ""
            if db:
                memories = await AgentMemoryService.search_memory(db, message, limit=3)
                
                # Hybrid RAG: Knowledge Graph Search
                try:
                    graph_entities = await KnowledgeGraphService.search_entities(db, message, limit=2)
                    if graph_entities:
                        graph_info = []
                        for entity in graph_entities:
                            rels = await KnowledgeGraphService.get_relationships(db, entity["id"])
                            formatted_rels = []
                            for r in rels[:5]:
                                if r['source_name'] == entity['name']:
                                    formatted_rels.append(f"{r['source_name']} ({r['source_label']}) --[{r['relation_type']}]--> {r['target_name']} ({r['target_label']})")
                                else:
                                    formatted_rels.append(f"{r['target_name']} ({r['target_label']}) <--[{r['relation_type']}]-- {r['source_name']} ({r['source_label']})")
                            
                            graph_info.append(f"ENTITET: {entity['name']} ({entity['label']})\nRELASJONER:\n" + "\n".join(formatted_rels))
                        
                        if graph_info:
                            graph_context = "\n\nRELEVANT KUNNSKAPSGRAF (HybridRAG):\n" + "\n\n".join(graph_info)
                            logger.info(f"HybridRAG: Found {len(graph_entities)} entities in knowledge graph")
                except Exception as e:
                    logger.debug(f"Knowledge Graph retrieval failed: {e}")

                personas = await AgentMemoryService.search_memory(db, "persona", limit=1, filters={"type": "persona_definition"})
                persona_text = personas[0]["content"] if personas else None
                past_convos = await AgentMemoryService.search_memory(db, message, limit=2, filters={"type": "conversation"})
            # BEFS-instruksjoner (læring fra enkel modus) – legg til persona slik at full flyt bruker samme terminologi
            befs_instruksjoner = get_befs_instruksjoner()
            if befs_instruksjoner:
                base_persona = persona_text or "Du er KI Kollega, en hjelpsom assistent for BEFS Eiendom."
                persona_text = f"{base_persona}\n\n{befs_instruksjoner}"
            
            convo_context = ""
            if past_convos:
                convo_context = "\n\nRELATERTE TIDLIGERE SAMTALER:\n" + "\n".join([f"- {c['content']}" for c in past_convos])

            memory_context = ""
            if memories:
                memory_context = "\n\nRELEVANT LANGTIDSHUKOMMELSE (Vektorsøk):\n" + "\n".join([f"- {m['content']}" for m in memories])
                if graph_context:
                    memory_context += graph_context
                if convo_context:
                    memory_context += convo_context
                logger.info(f"Injected {len(memories)} memories and {len(past_convos)} past convos into context")
            elif graph_context:
                memory_context = graph_context
                if convo_context:
                    memory_context += convo_context

            # 2. Discover relevant tools (kun når db er tilgjengelig)
            discovered_tools = await ToolDiscoveryService.find_relevant_tools(db, message, limit=2) if db else []
            if discovered_tools:
                logger.info(f"Discovered {len(discovered_tools)} relevant tools in toolbox")

            # 3. Build messages list (include conversation history, cap 10 messages)
            chat_messages = []
            
            # Legg til brukerinformasjon i konteksten
            if user and user.name:
                role_label = self._get_role_label(user.role.value if hasattr(user.role, "value") else str(user.role))
                chat_messages.append(SystemMessage(content=f"DU SNAKKER MED: {user.name} ({role_label}). Bruk navnet aktivt og naturlig i samtalen for å bygge relasjon."))
                
                # Legg til arbeidsmengde (avvik og aktiviteter)
                if db:
                    try:
                        workload = await self._get_user_workload_summary(db, user)
                        if workload:
                            chat_messages.append(SystemMessage(content=workload))
                    except Exception as e:
                        logger.debug("Failed to inject workload context in chat: %s", e)
            
            if memory_context:
                chat_messages.append(SystemMessage(content=f"Du har tilgang til følgende relevant langtidsinformasjon om eiendommene, brukerne og tidligere hendelser: {memory_context}"))
            history_capped = history[-10:]  # last 10 messages (5 turns)
            for m in history_capped:
                role = (m.get("role") or "user").lower()
                content = m.get("content") or ""
                if role == "assistant":
                    chat_messages.append(AIMessage(content=content))
                else:
                    chat_messages.append(HumanMessage(content=content))
            chat_messages.append(HumanMessage(content=message))

            # Sidekontekst: hent sammendrag for nåværende side (kontrakt/part/eiendom) og gi til Writer
            if db and context.entity_type and context.entity_id:
                try:
                    page_summary = await self._get_page_context_summary(db, context)
                    if page_summary:
                        chat_messages.insert(0, SystemMessage(content="BRUKEREN SER PÅ:\n" + page_summary))
                        logger.info("Injected page context for %s %s", context.entity_type, context.entity_id[:8])
                except Exception as e:
                    logger.debug("Could not inject page context: %s", e)

            inputs = {
                "messages": chat_messages,
                "discovered_tools": discovered_tools,
                "persona": persona_text,
                "context": {
                    "entity_type": context.entity_type,
                    "entity_id": context.entity_id,
                    "page": context.page,
                    "region": context.region
                }
            }
            
            # 4. Invoke Graph with Timeout
            # We use ainvoke to run the graph with a 45s timeout to prevent hanging
            try:
                final_state = await asyncio.wait_for(
                    app.ainvoke(inputs),
                    timeout=settings.CHAT_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.error("Chat request timed out")
                return {
                    "answer": "Forespørselen tok for lang tid. Prøv å forenkle spørsmålet eller prøv igjen senere.",
                    "sources": [],
                    "error": "Timeout"
                }

            # 3. Extract output
            messages = final_state["messages"]
            last_msg = messages[-1]
            
            # Check for errors
            if final_state.get("error"):
                logger.error(f"Agent flow returned error: {final_state['error']}")
                return {
                    "answer": "Jeg møtte på problemer under behandlingen av forespørselen.",
                    "sources": [],
                    "error": "Internal processing error"
                }

            # Extract sources if available
            sources = self._extract_sources_from_state(final_state)

            # Extract usage information from final state
            usage_info = final_state.get("usage")

            # Log usage to database if available
            if usage_info and db:
                try:
                    from app.services.api_usage_tracker import track_usage
                    await track_usage(
                        db=db,
                        endpoint="ki_kollega_chat",
                        model=self.model,
                        prompt_tokens=usage_info.get("prompt_tokens", 0),
                        completion_tokens=usage_info.get("completion_tokens", 0),
                        user_id=context.user_id if context else None
                    )
                except Exception as track_err:
                    logger.error(f"Failed to track usage: {track_err}")

            # 4. Save this interaction to long-term memory
            if db:
                try:
                    chat_interaction = f"Bruker: {message}\nKI Kollega: {last_msg.content}"
                    await AgentMemoryService.add_memory(
                        db,
                        chat_interaction,
                        metadata={"type": "conversation", "user_query": message}
                    )
                except Exception as mem_err:
                    logger.error(f"Failed to save convo to memory: {mem_err}")

            return {
                "answer": last_msg.content,
                "sources": sources,
                "usage": usage_info
            }
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            # Log failure if db is available
            if db:
                try:
                    log_entry = ApiCallLog(
                        service_name="openai",
                        endpoint="chat",
                        request_count=1,
                        status_code=500,
                        error_message=str(e)[:500]
                    )
                    db.add(log_entry)
                    await db.commit()
                except Exception as log_err:
                    logger.error(f"Failed to log error: {log_err}")

            return {
                "answer": "Beklager, det oppstod en uventet feil. Systemadministrator er varslet.",
                "sources": [],
                "error": "Internal Server Error"
            }

    async def chat_stream(
        self,
        message: str,
        context: Optional[ChatContext] = None,
        history: Optional[List[Dict[str, str]]] = None,
        db: Optional[AsyncSession] = None,
        user: Optional[User] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat via Unified Agent (ReAct). Tekst-token fra modellen; done inkluderer kilder og valgfri diagramdata (SSB).
        """
        if not self.client:
            yield {"type": "error", "error": "Client not initialized"}
            return

        if not db:
            yield {"type": "error", "error": "Database-tilkobling mangler"}
            return

        history = history or []
        context = context or ChatContext()

        try:
            from langgraph.checkpoint.memory import MemorySaver
            from app.services.intelligence.unified_agent.graph import create_unified_graph

            chat_messages = await self._build_unified_chat_messages(
                message, context, history, db, user, history_limit=20
            )
            thread_id = str(uuid4())
            checkpointer = MemorySaver()
            agent_graph = create_unified_graph(db, user=user, checkpointer=checkpointer)
            config: Dict[str, Any] = {
                "recursion_limit": 20,
                "configurable": {"thread_id": thread_id},
            }
            inputs = {"messages": chat_messages}

            async def run_stream():
                full_answer = ""
                async for event in agent_graph.astream_events(
                    inputs, config=config, version="v2"
                ):
                    ev = event.get("event")
                    if ev == "on_chain_start":
                        name = (event.get("name") or "").lower()
                        if "tools" in name:
                            yield {
                                "type": "status",
                                "content": "Henter data med verktøy...",
                            }
                        elif "guardian" in name:
                            yield {
                                "type": "status",
                                "content": "KI Kollega sjekker forespørselen...",
                            }
                    elif ev == "on_chat_model_stream":
                        meta = event.get("metadata") or {}
                        if meta.get("langgraph_node") != "agent":
                            continue
                        chunk = (event.get("data") or {}).get("chunk")
                        if not chunk:
                            continue
                        content = chunk.content
                        pieces: List[str] = []
                        if isinstance(content, str) and content:
                            pieces.append(content)
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                                    pieces.append(str(part["text"]))
                                elif hasattr(part, "text") and getattr(part, "text", None):
                                    pieces.append(str(part.text))
                        for p in pieces:
                            full_answer += p
                            yield {"type": "content", "content": p}

                try:
                    snap = await agent_graph.aget_state(config)
                    final_state = (
                        dict(snap.values)
                        if snap and getattr(snap, "values", None) is not None
                        else {}
                    )
                except Exception as e:
                    logger.debug("chat_stream aget_state: %s", e)
                    final_state = {}

                if not full_answer:
                    msgs = final_state.get("messages", [])
                    lm = msgs[-1] if msgs else None
                    if lm and hasattr(lm, "content"):
                        c = lm.content
                        if isinstance(c, str):
                            full_answer = c
                        elif isinstance(c, list):
                            for part in c:
                                if isinstance(part, dict) and part.get("text"):
                                    full_answer += str(part["text"])

                if db and full_answer:
                    try:
                        await AgentMemoryService.add_memory(
                            db,
                            f"Bruker: {message}\nKI Kollega: {full_answer}",
                            metadata={
                                "type": "conversation",
                                "user_query": message[:100],
                                "mode": "unified_stream",
                            },
                        )
                    except Exception as mem_err:
                        logger.error("Failed to save stream memory: %s", mem_err)

                sources = self._extract_sources_from_unified_state(final_state)
                chart_data = self._extract_chart_from_script_results(
                    final_state.get("script_results") or {}
                )
                yield {
                    "type": "done",
                    "sources": sources,
                    "follow_up_questions": [],
                    "error": None,
                    "data": chart_data,
                }

            timeout_time = time.time() + settings.CHAT_TIMEOUT_SECONDS
            async for chunk in run_stream():
                if time.time() > timeout_time:
                    raise asyncio.TimeoutError()
                yield chunk

        except asyncio.TimeoutError:
            logger.error("Chat stream timed out")
            yield {
                "type": "error",
                "error": "Forespørselen tok for lang tid. Prøv å forenkle spørsmålet.",
            }
        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)[:200]}

    async def _handle_sql_analysis(self, db: AsyncSession, message: str) -> List[Dict[str, Any]]:
        """Handle SQL analysis queries using direct OpenAI + SCHEMA.md + befs_instruksjoner."""
        try:
            schema = self._load_schema_config()
            instruksjoner = get_befs_instruksjoner()
            combined_context = f"{instruksjoner}\n\n{schema}" if instruksjoner else schema

            sql = await self._generate_sql_query(message, combined_context)
            if not sql:
                logger.error("SQL generation returned None")
                return []

            logger.info(f"Generated SQL: {sql[:300]}")
            exec_res = await self._execute_safe_sql_structured(db, sql)
            if exec_res is None:
                return []
            if not exec_res.get("success"):
                logger.error("SQL execution failed: %s", exec_res.get("message"))
                return []
            result_str = exec_res.get("formatted") or ""
            if result_str == "Ingen resultater funnet.":
                return []
            tabular = None
            cols = exec_res.get("columns") or []
            rds = exec_res.get("row_dicts") or []
            if cols and rds:
                from app.services.intelligence.ki_kollega.sql_chart_tabular import (
                    sql_rows_to_chart_tabular,
                )
                tabular = sql_rows_to_chart_tabular(cols, rds)
            item: Dict[str, Any] = {
                "type": "sql_data",
                "content": f"DATABASE RAPPORT:\n{result_str}\n\n(Basert på: `{sql}`)",
            }
            if tabular:
                item["tabular"] = tabular
            return [item]

        except Exception as e:
            logger.error(f"SQL Analysis failed: {e}", exc_info=True)
            return []

    def _load_schema_config(self) -> str:
        """Load schema configuration."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../config/SCHEMA.md")
            with open(config_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load SCHEMA.md: {e}")
            return ""

    async def _generate_sql_query(self, message: str, schema: str) -> Optional[str]:
        """Generate SQL query from natural language."""
        if not self.client:
            return None
            
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""Du er en ekspert på PostgreSQL SQL for BEFS (Bufetat eiendomsforvaltning).
Din jobb er å oversette et spørsmål til ENKEL, GYLDIG SQL basert på konteksten under.

KONTEKST (terminologi, regler og schema):
{schema}

KRITISKE REGLER:
1. Returner KUN SQL-koden. Ingen forklaring.
2. IKKE bruk Markdown-formatering (```sql...).
3. Sørg for at spørringen er READ-ONLY (SELECT).
4. Bruk ILIKE for tekstsøk.
5. For gl_transactions: bruk `ar` (ikke `year`), `belop` (ikke `amount`), `konto_navn`, `srs_kategori`, `dim1_kode`, `region`, `leverandor_navn`.
6. Returner maks 20 rader hvis ikke annet er spesifisert.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]

            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                    max_tokens=200
                ),
                timeout=settings.SQL_GEN_TIMEOUT_SECONDS
            )

            sql = response.choices[0].message.content.strip()
            # Clean potential markdown
            sql = sql.replace("```sql", "").replace("```", "").strip()
            try:
                # Log usage
                if self.client and hasattr(response.usage, 'total_tokens'):
                     # Simple cost calculation for 4o mini/sql gen
                     usage = response.usage
                     # Input $0.15/1M, Output $0.60/1M (gpt-4o-mini approx)
                     cost = ((usage.prompt_tokens * 0.15) + (usage.completion_tokens * 0.60)) / 1_000_000
                     
                     # Since we don't have DB session easily here (it's passed but deeper down), 
                     # ideally we should pass db to _generate_sql_query.
                     # For now, we skip SQL gen logging or need to refactor to pass DB.
                     pass

            except Exception:
                pass

            return sql
            
        except Exception as e:
            logger.error(f"SQL Generation failed: {e}")
            return None

    _SQL_MAX_ROWS = 200  # Hard øvre grense for AI-generert SQL

    async def _execute_safe_sql_structured(
        self, db: AsyncSession, sql: str
    ) -> Optional[Dict[str, Any]]:
        forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "GRANT", "EXECUTE"]
        upper_sql = sql.upper()
        if not upper_sql.startswith("SELECT") and not upper_sql.startswith("WITH"):
            logger.warning("Blocked unsafe SQL (must start with SELECT/WITH): %s", sql)
            return None
        for word in forbidden:
            if f" {word} " in f" {upper_sql} " or f"\n{word}" in upper_sql:
                logger.debug("Blocked unsafe SQL (contains %s): %s", word, sql)
                return None
        try:
            # Inject LIMIT at DB level so we never load more than _SQL_MAX_ROWS+1 rows
            # into memory regardless of what the AI-generated SQL contains.
            fetch_limit = self._SQL_MAX_ROWS + 1
            stripped = sql.rstrip().rstrip(";")
            limited_sql = f"SELECT * FROM ({stripped}) AS _q LIMIT {fetch_limit}"
            result = await db.execute(text(limited_sql))
            rows = result.fetchall()
            columns = list(result.keys())
            str_cols = [str(c) for c in columns]
            truncated = len(rows) > self._SQL_MAX_ROWS
            if truncated:
                rows = rows[: self._SQL_MAX_ROWS]
                logger.warning(
                    "SQL avkuttet til %d rader (LIMIT %d injisert): %s",
                    self._SQL_MAX_ROWS, fetch_limit, sql[:200],
                )
            if not rows:
                return {
                    "success": True,
                    "formatted": "Ingen resultater funnet.",
                    "columns": str_cols,
                    "row_dicts": [],
                    "truncated": False,
                }
            row_dicts = [{str(k): row._mapping[k] for k in columns} for row in rows]
            lines = [" | ".join(str_cols), "-" * 30]
            for row in rows:
                lines.append(" | ".join(str(val) for val in row))
            if truncated:
                lines.append(f"[Merk: resultatet er avkuttet til {self._SQL_MAX_ROWS} rader]")
            return {
                "success": True,
                "formatted": "\n".join(lines),
                "columns": str_cols,
                "row_dicts": row_dicts,
                "truncated": truncated,
                "total_rows": len(rows),
            }
        except Exception as e:
            logger.error("SQL execution error: %s", e)
            return {"success": False, "message": f"Feil ved kjøring av database-søk: {str(e)}"}

    async def _execute_safe_sql(self, db: AsyncSession, sql: str) -> Optional[str]:
        res = await self._execute_safe_sql_structured(db, sql)
        if res is None:
            return None
        if not res.get("success"):
            return res.get("message")
        return res.get("formatted")

    def _load_agent_config(self) -> str:
        """Load agent configuration from Markdown file."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../config/AGENT.md")
            with open(config_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load AGENT.md: {e}")
            # Fallback prompt
            return """Du er en hjelpsom assistent. SPØRSMÅLSTYPE: {query_type}. KONTEKST: {context_text}"""



    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for query using the configured client.
        
        Args:
            text: The input text to embed.
            
        Returns:
            List of floats representing the embedding vector, or None if failed.
        """
        if not self.client:
            return None
            
        try:
            # Clean text
            text = text.replace("\n", " ").strip()
            
            # Using same model as ingest_data.py
            # Note: client.embeddings.create works for OpenAI compatible clients
            response = await self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small" 
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

    def _calculate_usage(self, usage: Any) -> Dict[str, Any]:
        """
        Calculate usage and estimated cost for OpenAI call.
        
        Args:
            usage: OpenAI usage object (prompt_tokens, completion_tokens).
            
        Returns:
            Dictionary with token counts and estimated cost in USD.
        """
        usage_dict = usage.model_dump()
        
        # GPT-4o pricing (as of Jan 2025)
        # Input: $2.50 / 1M tokens
        # Output: $10.00 / 1M tokens
        input_cost_per_m = 2.50
        output_cost_per_m = 10.00
        
        cost = (
            (usage.prompt_tokens * input_cost_per_m) + 
            (usage.completion_tokens * output_cost_per_m)
        ) / 1_000_000
        
        usage_dict["estimated_cost"] = round(cost, 6)
        return usage_dict

    async def _log_usage(self, db: AsyncSession, usage_dict: Dict[str, Any], endpoint: str = "chat"):
        """Log usage to database."""
        try:
            if not db:
                return

            log = ApiCallLog(
                service_name="openai",
                endpoint=endpoint,
                request_count=1,
                cost_estimate=usage_dict.get("estimated_cost", 0.0),
                response_time_ms=0, # Not easily available here
                status_code=200
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")

    def _extract_chart_from_script_results(
        self, sr: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Plukk ut siste diagram-payload fra script_results (delegert til ren funksjon)."""
        from app.services.intelligence.ki_kollega.sql_chart_tabular import (
            pick_last_chart_from_script_results,
        )

        return pick_last_chart_from_script_results(sr)

    async def _build_unified_chat_messages(
        self,
        message: str,
        context: ChatContext,
        history: List[Dict[str, str]],
        db: AsyncSession,
        user: Optional[User],
        history_limit: int = 20,
    ) -> List[Any]:
        """Bygg meldingsliste for Unified Agent (samme kontekst som chat_unified)."""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        chat_messages: List[Any] = []

        if user and user.name:
            role_label = self._get_role_label(
                user.role.value if hasattr(user.role, "value") else str(user.role)
            )
            chat_messages.append(
                SystemMessage(
                    content=f"DU SNAKKER MED: {user.name} ({role_label}). Bruk navnet aktivt og naturlig i samtalen."
                )
            )
            try:
                workload = await self._get_user_workload_summary(db, user)
                if workload:
                    chat_messages.append(SystemMessage(content=workload))
            except Exception as e:
                logger.debug("Failed to inject workload context in unified messages: %s", e)

        if context.entity_type and context.entity_id:
            try:
                page_summary = await self._get_page_context_summary(db, context)
                if page_summary:
                    chat_messages.append(
                        SystemMessage(content="BRUKEREN SER PÅ:\n" + page_summary)
                    )
            except Exception as e:
                logger.debug("Unified: Could not inject page context: %s", e)

        graph_context = ""
        memories = await AgentMemoryService.search_memory(db, message, limit=3)
        try:
            graph_entities = await KnowledgeGraphService.search_entities(db, message, limit=2)
            if graph_entities:
                graph_info = []
                for entity in graph_entities:
                    rels = await KnowledgeGraphService.get_relationships(db, entity["id"])
                    formatted_rels = []
                    for r in rels[:5]:
                        if r["source_name"] == entity["name"]:
                            formatted_rels.append(
                                f"{r['source_name']} ({r['source_label']}) --[{r['relation_type']}]--> {r['target_name']} ({r['target_label']})"
                            )
                        else:
                            formatted_rels.append(
                                f"{r['target_name']} ({r['target_label']}) <--[{r['relation_type']}]-- {r['source_name']} ({r['source_label']})"
                            )
                    graph_info.append(
                        f"ENTITET: {entity['name']} ({entity['label']})\nRELASJONER:\n"
                        + "\n".join(formatted_rels)
                    )
                if graph_info:
                    graph_context = "\n\nRELEVANT KUNNSKAPSGRAF (HybridRAG):\n" + "\n\n".join(
                        graph_info
                    )
                    logger.info(
                        "HybridRAG Unified: Found %s entities in knowledge graph",
                        len(graph_entities),
                    )
        except Exception as e:
            logger.debug("Knowledge Graph retrieval failed: %s", e)

        past_convos = await AgentMemoryService.search_memory(
            db, message, limit=2, filters={"type": "conversation"}
        )

        convo_context = ""
        if past_convos:
            convo_context = "\n\nRELATERTE TIDLIGERE SAMTALER:\n" + "\n".join(
                [f"- {c['content']}" for c in past_convos]
            )

        memory_context = ""
        if memories:
            memory_context = "\n\nRELEVANT LANGTIDSHUKOMMELSE (Vektorsøk):\n" + "\n".join(
                [f"- {m['content']}" for m in memories]
            )
            if graph_context:
                memory_context += graph_context
            if convo_context:
                memory_context += convo_context
            chat_messages.append(
                SystemMessage(
                    content=f"Du har tilgang til følgende relevant langtidsinformasjon: {memory_context}"
                )
            )
        elif graph_context:
            memory_context = graph_context
            if convo_context:
                memory_context += convo_context
            chat_messages.append(
                SystemMessage(
                    content=f"Du har tilgang til følgende relevant langtidsinformasjon fra kunnskapsgrafen: {memory_context}"
                )
            )

        for m in history[-history_limit:]:
            role = (m.get("role") or "user").lower()
            content = m.get("content") or ""
            if role == "assistant":
                chat_messages.append(AIMessage(content=content))
            else:
                chat_messages.append(HumanMessage(content=content))
        chat_messages.append(HumanMessage(content=message))
        return chat_messages

    async def chat_unified(
        self,
        message: str,
        context: Optional[ChatContext] = None,
        history: Optional[List[Dict[str, str]]] = None,
        db: Optional[AsyncSession] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Unified Agent (ReAct) - LLM chooses tools dynamically.
        Simpler than Avansert pipeline; better semantic understanding.
        """
        if not self.client:
            return {
                "answer": "Beklager, AI-tjenesten er ikke konfigurert. Kontakt administrator.",
                "sources": [],
                "error": "Client not initialized",
            }

        if not db:
            return {
                "answer": "Database-tilkobling mangler. Prøv igjen senere.",
                "sources": [],
                "error": "No database",
            }

        from app.services.intelligence.unified_agent.graph import create_unified_graph

        history = history or []
        context = context or ChatContext()

        chat_messages = await self._build_unified_chat_messages(
            message, context, history, db, user, history_limit=20
        )
        agent_graph = create_unified_graph(db, user=user)

        try:
            config = {"recursion_limit": 20}
            
            final_state = await asyncio.wait_for(
                agent_graph.ainvoke(
                    {"messages": chat_messages},
                    config=config,
                ),
                timeout=settings.CHAT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error("Unified chat timeout")
            return {
                "answer": "Forespørselen tok for lang tid. Prøv å forenkle spørsmålet eller prøv igjen senere.",
                "sources": [],
                "error": "Timeout",
            }
        except Exception as e:
            logger.error(f"Unified chat error: {e}", exc_info=True)
            return {
                "answer": "Beklager, det oppstod en uventet feil.",
                "sources": [],
                "error": str(e)[:200],
            }

        messages = final_state.get("messages", [])
        last_msg = messages[-1] if messages else None
        raw_answer = (
            last_msg.content
            if last_msg and hasattr(last_msg, "content")
            else "Ingen respons."
        )
        if isinstance(raw_answer, list):
            parts: List[str] = []
            for block in raw_answer:
                if isinstance(block, dict) and block.get("text"):
                    parts.append(str(block["text"]))
                elif hasattr(block, "text") and getattr(block, "text", None):
                    parts.append(str(block.text))
            answer = "".join(parts) if parts else "Ingen respons."
        else:
            answer = raw_answer

        # Extract sources from ToolMessages (lookup_properties/lookup_parties may have structured_sources in content)
        sources = self._extract_sources_from_unified_state(final_state)

        if db:
            try:
                chat_interaction = f"Bruker: {message}\nKI Kollega: {answer}"
                await AgentMemoryService.add_memory(
                    db,
                    chat_interaction,
                    metadata={"type": "conversation", "user_query": message, "mode": "unified"},
                )
            except Exception as mem_err:
                logger.error(f"Failed to save convo to memory: {mem_err}")

        chart_data = self._extract_chart_from_script_results(
            final_state.get("script_results") or {}
        )

        return {
            "answer": answer,
            "sources": sources,
            "data": chart_data,
            "error": None,
        }

    def _extract_sources_from_unified_state(self, final_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from Agent state (supports research_data, script_results and collected_sources)."""
        sources: List[Dict[str, Any]] = []
        seen = set()

        def add_source(s: Dict[str, Any]) -> None:
            if not isinstance(s, dict): return
            key = (s.get("type"), s.get("id") or s.get("url") or s.get("name", ""))
            if key in seen:
                return
            seen.add(key)
            sources.append({
                "type": s.get("type", "unknown"),
                "id": s.get("id"),
                "name": s.get("name", "Ukjent"),
                "relevance": s.get("relevance", 0.0),
                **({"url": s["url"]} if s.get("url") else {}),
            })

        # Sjekk collected_sources (fallback)
        for src in (final_state.get("collected_sources") or []):
            add_source(src)
            
        # Sjekk research_data (fra Researcher)
        rd = final_state.get("research_data") or {}
        for src in rd.get("structured_sources", []):
            add_source(src)
            
        # Sjekk script_results (fra Analyst)
        sr = final_state.get("script_results") or {}
        for script_id, data in sr.items():
            if isinstance(data, dict):
                for src in data.get("structured_sources", []):
                    add_source(src)
                    
        return sources


# Singleton instance
ki_kollega_service = KIKollegaService()
