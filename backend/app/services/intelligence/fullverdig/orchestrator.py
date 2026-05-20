"""
Orchestrator – tolker brukerens intensjon og velger domeneagent.

Bruker gpt-4o-mini for rask routing.
"""

import logging
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.intelligence.fullverdig.state import FullverdigState

logger = logging.getLogger(__name__)

ORCHESTRATOR_PROMPT = """Du er en router. Brukerens melding og kontekst er gitt.
Velg ÉN agent basert på intensjonen:

- internkontroll: Spørsmål om avvik, sjekklister, internkontroll, HMS, brannvern, forfallte saker, "sjekk internkontroll for X"
- kontrakter: Spørsmål om kontrakter, utløp, leietakere, husleie, avtaleutløp, "kontrakter for X", "utløper snart"
- eiendommer: Spørsmål om eiendommer, portefølje, areal, region, kostnad per kvm, "eiendommer i region X"
- oekonomi: Kostnader, GL-data, budsjett, kostnad per kvm, regionvis økonomi, trend, «hva koster», «dyreste»
- avansert: Alt annet – hilsninger, generell samtale, juridiske spørsmål, komplekse spørsmål

Kontekst: {context}
Brukerens melding: {message}

Svar KUN med ett ord: internkontroll | kontrakter | eiendommer | oekonomi | avansert"""


async def orchestrator_node(state: FullverdigState) -> dict:
    """
    Orchestrator: LLM tolker intensjon → velger agent.
    """
    logger.info("🎯 Orchestrator: Tolker intensjon...")
    messages = state.get("messages", [])
    context = state.get("context") or {}

    last_msg = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break
    message = last_msg or ""

    context_str = ""
    if context.get("entity_type"):
        context_str = f"entity_type={context.get('entity_type')}, entity_id={context.get('entity_id')}"
    if context.get("page"):
        context_str += f", page={context.get('page')}"

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
            max_tokens=20,
        )
        response = await llm.ainvoke([
            SystemMessage(content=ORCHESTRATOR_PROMPT.format(
                context=context_str or "ingen",
                message=message[:500],
            )),
        ])
        choice = (response.content or "").strip().lower()
        # Normaliser til gyldig valg
        valid = {"internkontroll", "kontrakter", "eiendommer", "oekonomi", "analyst", "avansert"}
        if choice in valid:
            orchestrator_choice = choice
        else:
            # Prøv å finne ord i svaret
            for v in valid:
                if v in choice:
                    orchestrator_choice = v
                    break
            else:
                orchestrator_choice = "avansert"

        logger.info(f"🎯 Orchestrator: Valgte '{orchestrator_choice}'")
        return {
            "orchestrator_choice": orchestrator_choice,
            "next_step": orchestrator_choice if orchestrator_choice != "avansert" else "avansert",
        }
    except Exception as e:
        logger.warning(f"Orchestrator LLM feilet: {e}, fallback til avansert")
        return {
            "orchestrator_choice": "avansert",
            "next_step": "avansert",
        }
