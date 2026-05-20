"""
Financial Intelligence Schemas

Request/response models for natural language financial analysis.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class FinancialQueryRequest(BaseModel):
    """Request for financial analysis query."""
    
    query: str = Field(
        ..., 
        description="Natural language financial analysis query",
        min_length=3,
        max_length=500,
        example="Finn eiendommer med unormalt høye vedlikeholdskostnader"
    )
    
    property_ids: Optional[List[str]] = Field(
        None,
        description="Optional list of property UUIDs to filter analysis",
        example=["uuid-1", "uuid-2"]
    )


class FinancialQueryResponse(BaseModel):
    """Response from financial intelligence service."""
    
    status: Literal["tool_created", "error", "processing"] = Field(
        ...,
        description="Processing status"
    )
    
    tool_id: Optional[str] = Field(
        None,
        description="ID of created MCP tool (if tool_created)"
    )
    
    code: Optional[str] = Field(
        None,
        description="Generated Python/SQL code for analysis"
    )
    
    intent: str = Field(
        ...,
        description="Classified intent of the query",
        example="outlier_detection"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for intent classification"
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if status is error"
    )
    
    execution_time_ms: Optional[int] = Field(
        None,
        description="Time taken to process request in milliseconds"
    )
