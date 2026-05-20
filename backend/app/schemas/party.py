from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# Party modeller
class PartyBase(BaseModel):
    name: str
    orgnr: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class PartyCreate(PartyBase):
    pass


class PartyUpdate(BaseModel):
    name: Optional[str] = None
    orgnr: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class Party(PartyBase):
    party_id: UUID
    reference_code: Optional[str] = None  # BUF-P-NNNNNN
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    external_data: Optional[dict] = None
