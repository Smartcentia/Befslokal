from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# --- Enums ---

class ContractStatus(str, Enum):
    """Status enum for kontrakter."""
    active = "active"
    terminated = "terminated"

# --- Models ---

class PropertyBase(BaseModel):
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    @field_validator('postal_code', mode='before')
    @classmethod
    def validate_postal_code(cls, v: Any) -> Optional[str]:
        if v is None or v == '':
            return None
        return str(v)

class Property(PropertyBase):
    property_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    usage: Optional[str] = None
    total_area: Optional[float] = None
    construction_year: Optional[int] = None
    energy_label: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PropertyCreate(BaseModel):
    address: str
    postal_code: Optional[str] = None
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UnitBase(BaseModel):
    property_id: UUID
    purpose: str
    area_sqm: float
    floor: Optional[int] = None

class Unit(UnitBase):
    unit_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    property_id: Optional[UUID] = None
    purpose: Optional[str] = None
    area_sqm: Optional[float] = None
    floor: Optional[int] = None

class PartyBase(BaseModel):
    name: str
    orgnr: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class Party(PartyBase):
    party_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PartyCreate(PartyBase):
    pass

class PartyUpdate(BaseModel):
    name: Optional[str] = None
    orgnr: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class Contract(BaseModel):
    contract_id: UUID
    unit_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    status: str
    periods: Optional[Any] = None
    amount: Optional[Any] = None
    signed_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class ContractCreate(BaseModel):
    unit_id: UUID
    party_id: UUID
    status: str
    periods: Optional[Any] = None
    amount: Optional[Any] = None
    signed_at: Optional[datetime] = None

class RiskFactor(BaseModel):
    factor_name: str
    category: str
    severity: str
    probability: Optional[str] = None
    weight: Optional[float] = None
    calculated_score: float
    
    model_config = ConfigDict(from_attributes=True)

class RiskAssessment(BaseModel):
    assessment_id: UUID
    assessment_date: datetime
    methodology: str
    overall_risk_score: float
    risk_category: str
    assessed_by: Optional[str] = None
    notes: Optional[str] = None
    factors: List[RiskFactor] = []
    
    model_config = ConfigDict(from_attributes=True)

class WarningRisk(BaseModel):
    score: float
    nivaa: str
    faregrad: int
    treffende_varsler: List[Any] = []
    
    model_config = ConfigDict(from_attributes=True)

class PropertyDetailView(BaseModel):
    property: Property
    units: List[Unit] = []
    contracts: List[Contract] = []
    parties: List[Party] = []
    latest_risk_assessment: Optional[RiskAssessment] = None
    warning_risk: Optional[WarningRisk] = None
    external_risk: Optional[Dict[str, Any]] = None
    location_data: Optional[Dict[str, Any]] = None
    proximity_services: List[Dict[str, Any]] = []
    generated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)
