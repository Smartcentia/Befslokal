from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.models.api_call_logs import ApiCallLog
from app.core.config import settings

router = APIRouter()

@router.get("/vitals")
async def get_ai_vitals(db: AsyncSession = Depends(get_db)):
    """
    Returns transparency data about the AI systems, including models used,
    algorithms for ML, and performance metrics.
    """
    try:
        # 1. Model Info
        models = {
            "primary_llm": {
                "name": settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else "gpt-4o",
                "provider": "OpenAI",
                "role": "Reasoning, verktøyvalg og svargenerering (ReAct-løkke)"
            },
            "tools": [
                {
                    "name": "run_sql_query",
                    "description": "Kjører SQL mot databasen for statistikk, tellinger og kostnadsanalyse",
                    "type": "Dataanalyse"
                },
                {
                    "name": "lookup_properties",
                    "description": "Søker etter eiendommer på navn, adresse eller brukstype",
                    "type": "Oppslag"
                },
                {
                    "name": "lookup_parties",
                    "description": "Søker etter parter (leietakere/leverandører) på navn eller orgnr",
                    "type": "Oppslag"
                },
                {
                    "name": "search_documents",
                    "description": "RAG-søk i interne dokumenter om rutiner, HMS og prosedyrer",
                    "type": "Dokumentsøk"
                },
                {
                    "name": "search_lovdata",
                    "description": "Søker i norske lover og forskrifter (husleielov, HMS, kontraktsrett)",
                    "type": "Juridisk"
                },
                {
                    "name": "assess_property_risk",
                    "description": "Beregner risikonivå for en eiendom (flom, miljø, grunnforhold)",
                    "type": "Risikovurdering"
                },
                {
                    "name": "create_jira_issue",
                    "description": "Oppretter en Jira-oppgave direkte fra chatten",
                    "type": "Handling"
                }
            ],
            "data_retrieval": {
                "vector_db": "PostgreSQL (pgvector)",
                "search_type": "Vektorsimilaritet (cosine distance)",
                "status": "Operational"
            }
        }

        # 2. Performance Metrics (Last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        
        # Total calls
        stmt_total = select(func.count(ApiCallLog.call_id)).where(ApiCallLog.timestamp >= yesterday)
        total_calls = (await db.execute(stmt_total)).scalar() or 0

        # Avg response time
        stmt_avg_time = select(func.avg(ApiCallLog.response_time_ms)).where(ApiCallLog.timestamp >= yesterday)
        avg_response_time = (await db.execute(stmt_avg_time)).scalar() or 0

        # Error rate
        stmt_errors = select(func.count(ApiCallLog.call_id)).where(
            ApiCallLog.timestamp >= yesterday,
            ApiCallLog.status_code >= 400
        )
        error_count = (await db.execute(stmt_errors)).scalar() or 0
        error_rate = (error_count / total_calls * 100) if total_calls > 0 else 0

        metrics = {
            "last_24h": {
                "total_requests": total_calls,
                "avg_response_time_ms": round(avg_response_time, 2),
                "error_rate_percent": round(error_rate, 2),
                "system_health": "Healthy" if error_rate < 5 else "Degraded"
            }
        }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "metrics": metrics
        }
    except Exception as e:
        import logging
        logger = logging.getLogger("app.ai.transparency")
        logger.error(f"Error fetching AI vitals: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch AI transparency data")

@router.get("/scenarios")
async def get_benchmark_scenarios():
    """Returns static information about test scenarios used for benchmarking."""
    return {
        "scenarios": [
            {
                "id": "property_lookup",
                "title": "Eiendomssøk med kontekst",
                "description": "Brukeren spør om eiendommer i en region – agenten bruker lookup_properties og run_sql_query for å svare med lenker.",
                "llm_role": "Formulerer spørringen, tolker resultater og genererer lenker (property:UUID)",
                "ml_role": "Vektorsøk i pgvector for å hente relevante tidligere samtaler"
            },
            {
                "id": "contract_expiry",
                "title": "Kontraktsoversikt",
                "description": "Brukeren spør hvilke kontrakter utløper snart – agenten kjører SQL og presenterer resultater.",
                "llm_role": "Bestemmer hvilke verktøy som trengs og svarer med lenkede kontrakter",
                "ml_role": "Vektorsøk i AgentMemory for relevant historikk"
            },
            {
                "id": "hms_guidance",
                "title": "HMS-veiledning",
                "description": "Brukeren spør om en prosedyre – agenten søker i interne dokumenter og Lovdata.",
                "llm_role": "Kombinerer dokumentfunn med juridisk kontekst i et klart svar",
                "ml_role": "RAG-søk med cosine similarity mot dokumentindeksen"
            },
            {
                "id": "risk_assessment",
                "title": "Risikovurdering eiendom",
                "description": "Brukeren ber om risikovurdering for en spesifikk eiendom.",
                "llm_role": "Tolker risikodata og forklarer årsaker og anbefalinger",
                "ml_role": "assess_property_risk beregner score basert på nærhet og HMS-data"
            }
        ]
    }
