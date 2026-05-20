import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from fastapi import HTTPException
from sqlalchemy import text # Import text for raw SQL
from app.core.config import settings
from app.services.infrastructure.logger import get_logger

# Import existing services (Sync)
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.search.search_service import search_fulltext

from app.services.infrastructure.logger import get_logger
from app.services.dspy.sql_generator import dspy_generator  # [NEW] DSPy Integration

logger = get_logger(__name__)

class RagService:
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AsyncOpenAI Client"""
        if not self.api_key:
            logger.error("OpenAI API Key missing.")
            return

        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("RagService: Initialized with Standard OpenAI.")
        except Exception as e:
            logger.error(f"RagService: Initialization failed: {e}")

    async def _condense_query(self, question: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Transforms history + question into a standalone search query and list of potential entities."""
        if not self.client:
             return {"search_query": question, "entities": []}

        history_json = json.dumps(history[-3:]) if history else "[]"
            
        messages = [
            {"role": "system", "content": """Gitt historikk og et spørsmål, lag et JSON-objekt:
{
  "search_query": "Et frittstående søkeargument (norsk) som fanger opp emnet.",
  "entities": ["Liste over navngitte enheter (parter, bedrifter, adresser) funnet i teksten."]
}
Svar KUN med gyldig JSON."""},
            {"role": "user", "content": f"Historikk: {history_json}\nSpørsmål: {question}"}
        ]
        
        try:
             res = await self.client.chat.completions.create(
                 model=self.model,
                 response_format={"type": "json_object"},
                 messages=messages,
                 temperature=0
             )
             data = json.loads(res.choices[0].message.content)
             logger.info(f"Condensed query data: {data}")
             return data
        except Exception as e:
             logger.warning(f"Query condensation failed: {e}")
             return {"search_query": question, "entities": []}

    async def answer(self, question: str, history: List[Dict[str, str]] = None, db: AsyncSession = None) -> str:
        """
        Pure RAG Pipeline v4 (Entity Linking):
        1. Retrieval: Postgres (Text) + Structured (Entities)
        2. Fusion: Deduplicate and format context.
        3. Generation: Strict entity linking protocol.
        """
        if not self.client:
             return "Beklager, jeg er ikke koblet til AI-hjernen min (Konfigurasjonsfeil)."

        # --- 1. RETRIEVAL ---
        pg_results = []
        struct_results = []
        
        try:
            # Task 0: Condense query for better retrieval
            condensed = await self._condense_query(question, history)
            condensed_q = condensed.get("search_query", question)
            search_entities = condensed.get("entities", [])
            
            logger.info(f"RAG Retrieval v4 for: {condensed_q} (Entities: {search_entities})")
            
            # DB Tasks
            if db:
                try:
                    # [NEW] DSPy Retrieval Strategy (Opt-in)
                    if settings.ENABLE_DSPY_SQL: # Check env var
                        try:
                            dspy_res = await dspy_generator.execute_query(db, condensed_q)
                            if not dspy_res.get("error") and dspy_res.get("results"):
                                content = f"DSPy SQL Result ({dspy_res['count']} rows):\n{str(dspy_res['results'])}"
                                logger.info(f"DSPy SQL Success: {dspy_res['sql']}")
                                struct_results.append({
                                    "content": content, 
                                    "source": "DSPy SQL Generator", 
                                    "id": "dspy-auto", 
                                    "type": "sql_data"
                                })
                        except Exception as e:
                            logger.error(f"DSPy retrieval failed (fallback to legacy): {e}")

                    # Balanced limit to avoid 429
                    pg_results = await search_fulltext(db, condensed_q, limit=12)
                except Exception as e:
                    logger.error(f"Postgres Search failed: {e}")
                
                # Expand to include Parties and corrected Contract search
                try:
                    # Intent-Based SQL Search
                    intent_q = condensed_q.lower()
                    is_expiring = any(kw in intent_q for kw in ["utløper", "utløpt", "expired", "expiring", "snart"])
                    
                    # 1. Structured Search (Properties)
                    prop_query = text("""
                        SELECT property_id, name, address, external_data
                        FROM properties
                        WHERE name ILIKE :q OR address ILIKE :q
                        LIMIT 5
                    """)
                    p_res = await db.execute(prop_query, {"q": f"%{condensed_q}%"})
                    props = p_res.fetchall()
                    
                    for p in props:
                        content = (
                            f"EIENDOM (ID: property:{p.property_id}):\n"
                            f"Navn: {p.name}\n"
                            f"Adresse: {p.address}\n"
                            f"Info: {str(p.external_data) if p.external_data else 'Ingen tilleggsdata'}"
                        )
                        struct_results.append({"content": content, "source": "Eiendomsregisteret", "id": str(p.property_id), "type": "property"})

                    # 2. Structured Search (Contracts) - Enhanced with Date Intent
                    if is_expiring:
                        # Search for contracts expiring soon or already expired
                        # Periods is a list of objects, we check the first one (usually only one)
                        contract_query = text("""
                            SELECT c.contract_id, c.filename_number, c.status, c.amount, c.periods, p.address as property_address
                            FROM contracts c
                            LEFT JOIN units u ON c.unit_id = u.unit_id
                            LEFT JOIN properties p ON u.property_id = p.property_id
                            WHERE (c.periods->0->>'end_date' IS NOT NULL AND (c.periods->0->>'end_date')::date <= (CURRENT_DATE + INTERVAL '90 days'))
                               OR c.status = 'terminated'
                            ORDER BY (c.periods->0->>'end_date')::date ASC NULLS LAST
                            LIMIT 15
                        """)
                        c_res = await db.execute(contract_query)
                    else:
                        contract_query = text("""
                            SELECT c.contract_id, c.filename_number, c.status, c.amount, c.periods, c.external_data, p.address as property_address
                            FROM contracts c
                            LEFT JOIN units u ON c.unit_id = u.unit_id
                            LEFT JOIN properties p ON u.property_id = p.property_id
                            WHERE CAST(c.filename_number AS TEXT) ILIKE :q 
                               OR CAST(c.external_data AS TEXT) ILIKE :q
                            LIMIT 10
                        """)
                        c_res = await db.execute(contract_query, {"q": f"%{condensed_q}%"})
                    
                    contracts = c_res.fetchall()
                    for c in contracts:
                         # Safely extract end date from periods list
                         end_date = "Ikke oppgitt"
                         if c.periods and isinstance(c.periods, list) and len(c.periods) > 0:
                             end_date = c.periods[0].get("end_date") or "Ikke oppgitt"
                         elif isinstance(c.periods, dict):
                             end_date = c.periods.get("end_date") or c.periods.get("end") or "Ikke oppgitt"

                         content = (
                             f"KONTRAKT (ID: contract:{c.contract_id}):\n"
                             f"Nummer: {c.filename_number}\n"
                             f"Adresse: {getattr(c, 'property_address', 'Ukjent')}\n"
                             f"Status: {c.status}\n"
                             f"Beløp: {str(c.amount) if c.amount else 'N/A'}\n"
                             f"Utløpsdato: {end_date}\n"
                             f"Data: {str(getattr(c, 'external_data', ''))}"
                         )
                         struct_results.append({"content": content, "source": "Kontraktsregisteret", "id": str(c.contract_id), "type": "contract"})

                    # 3. Structured Search (Parties) + ALL Linked Contracts
                    party_keywords = search_entities if search_entities else [condensed_q]
                    seen_party_ids = set()

                    for p_name in party_keywords:
                        if len(p_name) < 3: continue
                        party_query = text("""
                            SELECT party_id, name, orgnr, contact_email
                            FROM parties
                            WHERE name ILIKE :q OR orgnr ILIKE :q
                            LIMIT 3
                        """)
                        party_res = await db.execute(party_query, {"q": f"%{p_name}%"})
                        parties = party_res.fetchall()
                        
                        for p in parties:
                            if p.party_id in seen_party_ids: continue
                            seen_party_ids.add(p.party_id)

                            content = (
                                f"PART (ID: party:{p.party_id}):\n"
                                f"Navn: {p.name}\n"
                                f"OrgNr: {p.orgnr}\n"
                                f"Email: {p.contact_email}"
                            )
                            struct_results.append({"content": content, "source": "Partsregisteret", "id": str(p.party_id), "type": "party"})

                            # RELATIONAL STEP: Fetch all contracts for this party
                            # Increased limit to 50 for "all info" request
                            party_contracts_query = text("""
                                SELECT c.contract_id, c.filename_number, c.status, c.amount, c.periods, p.address as property_address
                                FROM contracts c
                                LEFT JOIN units u ON c.unit_id = u.unit_id
                                LEFT JOIN properties p ON u.property_id = p.property_id
                                WHERE c.party_id = :pid
                                LIMIT 50
                            """)
                            pc_res = await db.execute(party_contracts_query, {"pid": p.party_id})
                            for pc in pc_res.fetchall():
                                 end_date = pc.periods[0].get("end_date") if pc.periods and isinstance(pc.periods, list) else "N/A"
                                 pc_content = (
                                     f"KONTRAKT FOR PART {p.name} (ID: contract:{pc.contract_id}):\n"
                                     f"Nummer: {pc.filename_number}\n"
                                     f"Adresse: {getattr(pc, 'property_address', 'Ukjent')}\n"
                                     f"Status: {pc.status}\n"
                                     f"Beløp: {str(pc.amount) if pc.amount else 'N/A'}\n"
                                     f"Utløp: {end_date}"
                                 )
                                 struct_results.append({"content": pc_content, "source": f"Kontrakter for {p.name}", "id": str(pc.contract_id), "type": "contract"})

                except Exception as e:
                    logger.error(f"Structured Search failed: {e}")
            else:
                logger.warning("RagService called without DB session.")
            
            # Special handling for "is that all?" follow-ups
            is_followup_for_more = any(kw in condensed_q.lower() for kw in ["alt", "mer", "fler", "more", "everything"])
            if is_followup_for_more and not struct_results and not pg_results:
                 struct_results.append({
                     "content": "INFO: Brukeren spør om det finnes mer informasjon. Det ble ikke funnet flere treff.",
                     "source": "System"
                 })

            logger.info(f"Retrieval Stats: PG={len(pg_results)}, Struct={len(struct_results)}")
                
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return f"Jeg klarte ikke å søke i dokumentene. Feil: {str(e)}"

        # --- 2. FUSION & AUGMENTATION ---
        final_docs = []
        seen_ids = set() 
        
        # 1. Process Structured Results (GOLD STANDARD)
        for row in struct_results:
             content = row.get("content", "")
             source = row.get("source", "System")
             final_docs.append({
                "content": content,
                "source": source,
                "metadata": {},
                "origin": "DATABASE RECORD"
             })
        
        # 2. Process Postgres Results
        for row in pg_results:
            content = row.get("content", "")
            source = row.get("source_file", "Database")
            
            # Inject IDs if present in row but missing in content
            c_id = row.get("contract_id")
            p_id = row.get("property_id")
            if c_id and f"contract:{c_id}" not in content:
                content = f"(ID: contract:{c_id})\n" + content
            if p_id and f"property:{p_id}" not in content:
                content = f"(ID: property:{p_id})\n" + content
                
            sig = f"{source}_{content[:50]}"
            if sig not in seen_ids:
                final_docs.append({"content": content, "source": source, "origin": "PostgreSQL"})
                seen_ids.add(sig)
        


        final_docs = final_docs[:15] # Balanced context window
        
        context_text = ""
        if not final_docs:
            context_text = "Ingen relevante dokumenter funnet."
        else:
            for i, doc in enumerate(final_docs):
                source_name = doc["source"]
                if "/" in source_name: source_name = source_name.split("/")[-1]
                context_text += f"\n--- DOKUMENT {i+1} ({source_name}) [{doc['origin']}] ---\n{doc['content']}\n"

        # Construct System Prompt with LINKING RULES
        system_prompt = """Du er "KI Kollega", en hjelpsom assistent for BEFS.
Din oppgave er å svare på brukerens spørsmål basert KUN på informasjonen gitt i "KONTEKST".

STRENG REGEL OM INTERNETT OG EKSTERN INFO (INGEN UNNTAK):
- Du har IKKE tilgang til internett eller eksterne registre.
- Det er STRENGT FORBUDT å foreslå at brukeren sjekker eksterne nettsider, Google, Statsbyggs hjemmesider, ringer kundeservice eller sjekker offentlige registre.
- Hvis informasjonen ikke finnes i KONTEKST, skal du svare: "Jeg finner dessverre ingen informasjon om dette i BEFS-systemene."
- Ikke gi "hjelpsomme" råd om hvor man kan finne informasjonen andre steder. Hold deg 100% til de interne dataene i KONTEKST.

VIKTIG REGEL FOR LENKING:
Når du nevner en Eiendom, Kontrakt eller Part som er funnet i konteksten (spesielt fra "DATABASE RECORD"), MÅ du lage en klikkbar lenke.
Bruk formatet: [Navn på objekt](type:id)

Eksempler:
- [Storgata 12](property:123-abc)
- [Kontrakt 45001](contract:456-def)
- [Utleier AS](party:789-ghi)

ID-en ("property:...") står tydelig i konteksten som "(ID: type:id)". Kopiér denne nøyaktig.

GENERELLE REGLER:
1. Bruk KUN informasjonen fra konteksten.
2. Hvis svaret ikke finnes, si det kort og slutt der.
3. Svar på norsk.
4. Bruk Markdown (fet tekst, lister) for lesbarhet.

KONTEKST:
{context}
"""
        formatted_system_prompt = system_prompt.format(context=context_text)

        # --- 3. GENERATION ---
        messages = [{"role": "system", "content": formatted_system_prompt}]
        if history:
            messages.extend(history[-4:]) 
        messages.append({"role": "user", "content": question})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3, 
                timeout=45.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return "Jeg fikk problemer med å formulere svaret. Vennligst prøv igjen."

    # Kept for backward compat / testing if needed, but logic is moved inside answer
    async def _search_structured_data(self, db: AsyncSession, query: str) -> List[Dict[str, Any]]:
        return [] 

rag_service = RagService()
