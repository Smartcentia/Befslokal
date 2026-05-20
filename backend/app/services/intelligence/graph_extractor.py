import json
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class GraphExtractor:
    """
    Utility for extracting entities and relationships from text for the Knowledge Graph.
    Uses LLM to perform triplet extraction.
    """
    
    EXTRACTION_PROMPT = """
    Du er en ekspert på kunnskapsgrafer og entitets-ekstraksjon for eiendomsbransjen.
    Din oppgave er å trekke ut entiteter og deres relasjoner fra den gitte teksten.
    
    ENTITETSTYPER:
    - Person (f.eks. ansatte, leietakere, kontaktpersoner)
    - Property (Eiendommer, bygg, adresser)
    - Organization (Selskaper, leverandører, det offentlige)
    - Role (Stillinger, ansvarsområder)
    - Contract (Leiekontrakter, rammeavtaler)
    - Location (Byer, regioner, bydeler)
    - Maintenance (Vedlikeholdsoppgaver, feilmeldinger)

    RELASJONSTYPER:
    - WORKS_AT (Person jobber hos Organisasjon)
    - MANAGES (Person/Rolle forvalter Eiendom)
    - LIVES_IN (Person bor i Eiendom/By)
    - IS_PART_OF (Bygg er del av Eiendom, Eiendom er i Region)
    - HAS_CONTRACT (Organisasjon/Person har Kontrakt)
    - RESPONSIBLE_FOR (Person har ansvar for Vedlikehold/Oppgave)
    - LOCATED_IN (Eiendom ligger i Lokasjon)
    - OWNS (Organisasjon eier Eiendom)

    FORMAT:
    Returner resultatet som en JSON-liste med objekter:
    [
      {
        "source": {"name": "Navn", "label": "Type"},
        "relation": "RELASJONSTYPE",
        "target": {"name": "Navn", "label": "Type"}
      }
    ]

    Viktig: Hvis ingen relasjoner finnes, returner en tom liste []. Ikke finn på informasjon.
    """

    @classmethod
    async def extract_triples(cls, text: str) -> List[Dict[str, Any]]:
        """Extracts triplets from text using LLM."""
        try:
            llm = ChatOpenAI(
                model=settings.CHAT_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0
            )
            
            messages = [
                SystemMessage(content=cls.EXTRACTION_PROMPT),
                HumanMessage(content=f"Ekstraher fra denne teksten:\n\n{text}")
            ]
            
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            # Remove markdown formatting if present
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            try:
                triples = json.loads(content)
                if not isinstance(triples, list):
                    return []
                return triples
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from GraphExtractor: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Graph extraction failed: {e}")
            return []
