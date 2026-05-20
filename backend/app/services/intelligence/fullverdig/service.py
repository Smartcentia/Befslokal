"""
Fullverdig KI Kollega Service – AI-first med domeneagenter.

Fase 1: Orchestrator + Internkontroll-agent.
Ved «avansert» delegeres til eksisterende ki_kollega (LangGraph).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intelligence.fullverdig.graph import fullverdig_graph
from app.domains.core.models.user import User
from app.services.intelligence.ki_kollega.service import ki_kollega_service

logger = logging.getLogger(__name__)

CHAT_TIMEOUT_SECONDS = 45.0


class FullverdigService:
    """Fullverdig KI Kollega – intensjon-først, domeneagenter."""

    async def chat(
        self,
        message: str,
        context: Optional[Any] = None,
        history: Optional[List[Dict[str, str]]] = None,
        db: Optional[AsyncSession] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Fullverdig chat: Orchestrator velger agent, kjører graf, returnerer svar.
        Ved orchestrator_choice=avansert delegeres til ki_kollega_service.
        """
        # Bygg meldinger
        chat_messages = []
        
        # Brukerinfo
        if user and user.name:
            chat_messages.append(SystemMessage(content=f"DU SNAKKER MED: {user.name}. Bruk navnet aktivt og naturlig i samtalen."))
            
        if history:
            for m in history:
                role = m.get("role", "user")
                content = m.get("content", "")
                if role == "assistant":
                    from langchain_core.messages import AIMessage
                    chat_messages.append(AIMessage(content=content))
                else:
                    chat_messages.append(HumanMessage(content=content))
        chat_messages.append(HumanMessage(content=message))

        # Kontekst som dict
        ctx = {}
        if context:
            ctx = {
                "page": getattr(context, "page", None),
                "entity_type": getattr(context, "entity_type", None),
                "entity_id": getattr(context, "entity_id", None),
                "region": getattr(context, "region", None),
            }

        initial_state = {
            "messages": chat_messages,
            "orchestrator_choice": "",
            "context": ctx,
            "next_step": "",
            "agent_result": None,
            "usage": None,
            "error": None,
        }

        config = {}
        if db:
            config = {"configurable": {"db": db}}

        try:
            final_state = await asyncio.wait_for(
                fullverdig_graph.ainvoke(initial_state, config=config),
                timeout=CHAT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error("Fullverdig chat timeout")
            return {
                "answer": "Forespørselen tok for lang tid. Prøv igjen.",
                "sources": [],
                "follow_up_questions": [],
                "error": "Timeout",
            }

        choice = final_state.get("orchestrator_choice", "avansert")

        # Kun internkontroll har egen agent. Alt annet (avansert, analyst, kontrakter, eiendommer) → ki_kollega
        if choice != "internkontroll":
            logger.info("Fullverdig: Delegating to ki_kollega (avansert)")
            return await ki_kollega_service.chat(
                message=message,
                context=context,
                history=history,
                db=db,
                user=user
            )

        # Hent svar fra writer
        messages = final_state.get("messages", [])
        answer = "Beklager, jeg kunne ikke generere et svar."
        for m in reversed(messages):
            if hasattr(m, "content") and m.content:
                from langchain_core.messages import AIMessage
                if isinstance(m, AIMessage):
                    answer = m.content
                    break

        usage_info = final_state.get("usage")

        return {
            "answer": answer,
            "sources": [],
            "follow_up_questions": [],
            "usage": usage_info,
            "error": final_state.get("error"),
        }
