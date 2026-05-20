"""
Lab API Router

Experimental AI/ML features and financial intelligence.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.financial_intelligence import (
    FinancialQueryRequest,
    FinancialQueryResponse
)
from app.services.financial_intelligence import financial_intelligence_service
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/financial-query", response_model=FinancialQueryResponse)
async def run_financial_query(
    request: FinancialQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> FinancialQueryResponse:
    """
    Process a natural language financial analysis query.
    
    This endpoint uses LLM to:
    1. Classify the intent of the query
    2. Generate Python/SQL code for the analysis
    3. (Optional) Create a reusable tool
    
    **Example Queries:**
    - "Finn eiendommer med unormalt høye vedlikeholdskostnader"
    - "Sammenlign totale kostnader for valgte eiendommer"
    - "Analyser korrelasjon mellom leie og vedlikehold"
    
    **Returns:**
    - Generated code
    - Intent classification
    - Confidence score
    - Tool ID (if created)
    """
    try:
        logger.info(f"Processing financial query: {request.query[:50]}...")
        
        # Process query using Financial Intelligence service
        result = await financial_intelligence_service.process_query(
            query=request.query,
            property_ids=request.property_ids
        )
        
        # Return as Pydantic model
        return FinancialQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing financial query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/financial-query/health")
async def health_check():
    """
    Health check for Financial Intelligence service.
    
    Returns service status and availability.
    """
    service_available = financial_intelligence_service.client is not None
    
    return {
        "status": "healthy" if service_available else "degraded",
        "service": "financial_intelligence",
        "openai_configured": service_available,
        "supported_intents": financial_intelligence_service.SUPPORTED_INTENTS
    }
