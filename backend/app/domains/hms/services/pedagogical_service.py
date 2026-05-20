from typing import Dict, Any, Optional
import logging
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class PedagogicalService:
    """
    AI Agent that acts as a 'Pedagog', explaining Internal Control concepts
    in simple Norwegian using OpenAI.
    """
    
    _client: Optional[AsyncOpenAI] = None

    @classmethod
    def get_client(cls) -> Optional[AsyncOpenAI]:
        if cls._client:
            return cls._client
            
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API Key missing. Pedagogue disabled.")
            return None
            
        try:
            cls._client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
            return cls._client
        except Exception as e:  
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None

    @staticmethod
    async def get_guidance(context: str, step: str) -> str:
        """
        Returns context-aware guidance in Norwegian via OpenAI.
        """
        client = PedagogicalService.get_client()
        if not client:
            return "AI-tjenesten er ikke tilgjengelig (mangler konfigurasjon)."

        system_prompt = (
            "Du er en pedagogisk veileder for internkontroll i eiendomsforvaltning. "
            "Din oppgave er å forklare HVA brukeren skal gjøre i dette steget og HVORFOR, på en enkel og motiverende måte. "
            "Svar kort og konsist på norsk.\n"
            "Viktig lovgrunnlag du skal kjenne til:\n"
            "- Forskrift om brannforebygging § 8 (Eiers og brukers plikter ved særskilte brannobjekter)\n"
            "- Internkontrollforskriften § 5 (Krav til innhold i internkontroll)\n"
            "- Barnevernloven § 10-1 (Krav til forsvarlighet)"
        )
        
        user_prompt = f"Kontekst: {context}. Jeg står i dette steget av prosessen: '{step}'. Hva bør jeg fokusere på?"

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL, # e.g. gpt-4o
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Guidance Error: {e}")
            return "Kunne ikke hente veiledning akkurat nå. Vennligst prøv igjen senere."

    @staticmethod
    async def chat_with_pedagogue(user_message: str, context_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Context-aware chat with the pedagogue.
        """
        client = PedagogicalService.get_client()
        if not client:
             return "AI-tjenesten er ikke tilgjengelig."

        # Build context string
        context_str = ""
        if context_data:
            if "case" in context_data:
                c = context_data["case"]
                context_str += f"\nSAKSINFORMASJON:\nTittel: {c.get('title')}\nBeskrivelse: {c.get('description')}\nStatus: {c.get('status')}\nPrioritet: {c.get('priority')}\n"
            if "step" in context_data:
                context_str += f"\nNÅVÆRENDE STEG I PROSESSEN: {context_data['step']}\n"
        
        system_prompt = (
            "Du er 'Pedagogen', en erfaren HMS-rådgiver og læremester i internkontroll for BEFS (Bufetat Eiendomsforvaltning). "
            "Din rolle er å hjelpe brukeren med å forstå og løse oppgaver, ikke bare gi fasiten. "
            "\n\n"
            "RETNINGSLINJER FOR SVAR:\n"
            "1. **Struktur**: Bruk Markdown for å strukturere svaret (overskrifter, punkter).\n"
            "2. **Pedagogisk**: Forklar *hvorfor* noe er viktig, gjerne med henvisning til lovverk eller 'god praksis'.\n"
            "3. **Kontekst**: Bruk informasjonen om saken aktivt. Hvis brukeren spør om 'dette', referer til den aktuelle saken.\n"
            "4. **Format**: \n"
            "   - Start gjerne med en kort **Vurdering**.\n"
            "   - Gi deretter **Konkrete Råd**.\n"
            "   - Avslutt med **Refleksjonsspørsmål** hvis relevant.\n"
            "\n"
            "Språk: Norsk bokmål. Tone: Profesjonell, hjelpsom, men myndig på sikkerhet."
        )

        user_content = f"{user_message}\n\n[System Context]:\n{context_str}"

        try:
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Chat Error: {e}")
            return f"Beklager, jeg fikk problemer med å tenke meg om: {str(e)}"
