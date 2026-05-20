from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class GLTransactionResponse(BaseModel):
    """
    Detailed response model for General Ledger transactions.
    """
    transaction_id: UUID
    property_id: Optional[UUID] = None
    
    # Location/Dimensions
    region_code: Optional[str] = None
    region_name: Optional[str] = None
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    
    # Accounting Details
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    purpose_code: Optional[str] = None
    purpose_name: Optional[str] = None
    
    # Vendor Info
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    description: Optional[str] = None
    
    # Financials
    amount: float
    period: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    transaction_date: Optional[datetime] = None
    category: Optional[str] = None
    
    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[GLTransactionResponse]
    total: int
    page: int
    size: int
    total_pages: int
