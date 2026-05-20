"""
Financial Intelligence Service

LLM-powered financial analysis code generation service.
Uses OpenAI to:
1. Classify user intent
2. Generate Python/SQL analysis code
3. (Optional) Create reusable MCP tools
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI

from app.core.config import settings
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)


class FinancialIntelligenceService:
    """
    Service for converting natural language queries into financial analysis code.
    
    Capabilities:
    - Intent classification (outlier_detection, comparison, correlation, etc.)
    - Python/SQL code generation
    - Context-aware analysis based on property data model
    """
    
    SUPPORTED_INTENTS = [
        "outlier_detection",  # Find anomalies
        "comparison",         # Compare properties
        "correlation",        # Find correlations
        "trend_analysis",     # Analyze trends
        "aggregation",        # Sum/average calculations
        "ranking",            # Rank properties
        "forecasting",        # Predict future values
        "breakdown",          # Breakdown costs by category
    ]
    
    def __init__(self):
        """Initialize service with OpenAI client."""
        self.client = self._initialize_client()
        
    def _initialize_client(self) -> Optional[OpenAI]:
        """Initialize OpenAI client."""
        try:
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI credentials not configured")
                return None
                
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY
            )
            logger.info("OpenAI client initialized successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    async def process_query(
        self,
        query: str,
        property_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Process financial query and generate code.
        
        Args:
            query: Natural language financial analysis query
            property_ids: Optional list of property UUIDs to filter
            
        Returns:
            Dict with status, code, intent, confidence, etc.
        """
        start_time = time.time()
        
        try:
            # Step 1: Classify intent
            intent, confidence = await self.classify_intent(query)
            logger.info(f"Classified intent: {intent} (confidence: {confidence:.2f})")
            
            # Step 2: Generate analysis code
            code = await self.generate_code(
                query=query,
                intent=intent,
                property_ids=property_ids
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "status": "tool_created",
                "code": code,
                "intent": intent,
                "confidence": confidence,
                "execution_time_ms": execution_time_ms,
                "tool_id": None,  # TODO: Implement tool creation
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "status": "error",
                "code": None,
                "intent": "unknown",
                "confidence": 0.0,
                "execution_time_ms": execution_time_ms,
                "tool_id": None,
                "error": str(e)
            }
    
    async def classify_intent(self, query: str) -> Tuple[str, float]:
        """
        Classify the intent of a financial query using LLM.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (intent, confidence)
        """
        if not self.client:
            return "unknown", 0.0
        
        system_prompt = f"""You are a financial analyst query classifier.

Classify the user's financial analysis query into ONE of these intents:
{chr(10).join(f'- {intent}' for intent in self.SUPPORTED_INTENTS)}

Return ONLY a JSON object with this structure:
{{{{
    "intent": "intent_name",
    "confidence": 0.85,
    "reasoning": "brief explanation"
}}}}

Be specific and confident in your classification."""

        user_prompt = f"""Classify this financial query:

Query: "{query}"

Return JSON with intent, confidence, and reasoning."""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
                
            result = json.loads(result_text)
            
            intent = result.get("intent", "unknown")
            confidence = float(result.get("confidence", 0.5))
            
            # Validate intent
            if intent not in self.SUPPORTED_INTENTS:
                logger.warning(f"Unknown intent: {intent}, defaulting to aggregation")
                intent = "aggregation"
                confidence = 0.5
            
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "unknown", 0.0
    
    async def generate_code(
        self,
        query: str,
        intent: str,
        property_ids: Optional[List[str]] = None
    ) -> str:
        """
        Generate Python analysis code based on query and intent.
        
        Args:
            query: Original natural language query
            intent: Classified intent
            property_ids: Optional property filter
            
        Returns:
            Generated Python code as string
        """
        if not self.client:
            return "# Error: OpenAI client not initialized"
        
        property_filter = ""
        if property_ids:
            property_filter = f"""
# Filter to specific properties
property_uuids = {property_ids}
properties_query = properties_query.filter(PropertyModel.property_id.in_(property_uuids))
"""
        
        system_prompt = """You are an expert Python developer specializing in financial data analysis.

Generate clean, production-ready Python code for financial analysis using SQLAlchemy async patterns.

Database Schema:
```python
# Properties table
class PropertyModel:
    property_id: UUID
    address: str
    municipality: str
    external_data: JSONB  # Contains financials

# Units table  
class UnitModel:
    unit_id: UUID
    property_id: UUID  # FK
    area_sqm: float

# Contracts table
class ContractModel:
    contract_id: UUID
    unit_id: UUID  # FK
    status: Enum("active", "terminated")
    amount: JSONB  # {"currency": "NOK", "amount_per_year": 756299}
```

Financial Data Structure (property.external_data):
```python
{
    "financials": {
        "total_maintenance": 17710757,
        "manual_expenses": [...],
        "total_manual_expenses": 500000
    }
}
```

Requirements:
- Use async/await patterns
- Use SQLAlchemy select() queries
- Include error handling
- Add clear comments
- Return structured dictionary results
- Use statistics/pandas if needed for calculations

Return ONLY executable Python code, no explanations.

IMPORTANT: If the analysis suggests that a follow-up action is needed (e.g. creating a task, work order, or alert), 
you can request it by including a specific dictionary key `action_request` in the returned results.

Action Request Format:
```python
return {
    "summary": "High power usage detected...",
    "results": [...],
    "action_request": {
        "type": "create_task",  # Supported: "create_task", "create_work_order"
        "payload": {
            "title": "Investigate High Power Usage",
            "description": "Property X is 50% above baseline...",
            "priority": "high",
            "metadata": {"source": "ai_lab_analysis"}
        }
    }
}
```"""

        user_prompt = f"""Generate Python code for this financial analysis:

**Query:** "{query}"
**Intent:** {intent}
**Properties:** {"Specific properties provided" if property_ids else "All properties"}

{property_filter if property_filter else "# Analyze all properties"}

The code should:
1. Query database using async SQLAlchemy
2. Perform the requested analysis
3. Return results as a dictionary

Example structure:
```python
async def analyze_financials(db: AsyncSession) -> Dict[str, Any]:
    # Your analysis code here
    return {{
        "summary": "...",
        "results": [...],
        "insights": "..."
    }}
```"""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            code = response.choices[0].message.content.strip()
            
            # Clean up code fences
            if code.startswith("```python"):
                code = code[9:-3].strip()
            elif code.startswith("```"):
                code = code[3:-3].strip()
            
            return code
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"# Error generating code: {str(e)}"


# Singleton instance
financial_intelligence_service = FinancialIntelligenceService()
