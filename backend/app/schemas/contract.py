from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, ValidationInfo
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.schemas.unit import Unit
from app.schemas.party import Party
from app.schemas.file import File
from app.schemas.property import Property

class ContractStatus(str, Enum):
    """Status enum for kontrakter."""
    active = "active"
    terminated = "terminated"


class Period(BaseModel):
    start_date: Any = None
    end_date: Any = None
    index_name: Optional[str] = "KPI"
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, v: Any) -> Any:
        """Parse dato-string til datetime."""
        if isinstance(v, str):
            try:
                if len(v) == 10:  # "YYYY-MM-DD"
                    return datetime.fromisoformat(v + "T00:00:00")
                elif "T" in v or " " in v:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                else:
                    return datetime.fromisoformat(v)
            except (ValueError, AttributeError):
                # Fallback: prøv date først
                try:
                    from datetime import date as date_type
                    if len(v) == 10:
                        parsed_date = date_type.fromisoformat(v)
                        return datetime.combine(parsed_date, datetime.min.time())
                except:
                    pass
        return v
    
    @model_validator(mode='before')
    @classmethod
    def parse_legacy_format(cls, data: Any) -> Any:
        """Konverter gammel struktur til ny."""
        if isinstance(data, dict):
            # Håndter gammel struktur: {"start": "...", "end": "...", "rent": ...}
            if "start" in data and "end" in data:
                start_date = data["start"]
                end_date = data["end"]
                
                if isinstance(start_date, str):
                    try:
                        if "T" in start_date or " " in start_date:
                            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                        else:
                            start_date = datetime.fromisoformat(start_date + "T00:00:00")
                    except (ValueError, AttributeError):
                         pass
                
                if isinstance(end_date, str):
                    try:
                        if "T" in end_date or " " in end_date:
                            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        else:
                            end_date = datetime.fromisoformat(end_date + "T00:00:00")
                    except (ValueError, AttributeError):
                        pass

                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "index_name": data.get("index_name", "KPI")
                }
        return data


class Amount(BaseModel):
    currency: str = "NOK"
    amount_per_year: Optional[float] = None
    
    @model_validator(mode='before')
    @classmethod
    def parse_legacy_format(cls, data: Any) -> Any:
        """Konverter gammel struktur til ny."""
        if isinstance(data, dict):
            if "total" in data and "currency" not in data:
                monthly_rent = data.get("monthly_rent", data.get("total", 0) / 12)
                return {
                    "currency": "NOK",
                    "amount_per_year": monthly_rent * 12 if monthly_rent else data.get("total", 0)
                }
            if "currency" not in data:
                data["currency"] = "NOK"
            if "amount_per_year" not in data:
                if "total" in data:
                    data["amount_per_year"] = data["total"]
                else:
                    data["amount_per_year"] = None
            elif data.get("amount_per_year") is None:
                pass
        elif data is None or (isinstance(data, dict) and not data):
            return {"currency": "NOK", "amount_per_year": None}
        return data


class ContractBase(BaseModel):
    unit_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    status: Optional[ContractStatus] = None
    category: Optional[str] = None
    start_date: Optional[Any] = None
    end_date: Optional[Any] = None
    periods: Optional[List[Period]] = None
    amount: Optional[Amount] = None
    signed_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    # Opsjoner/varsling
    has_option: Optional[bool] = None
    option_deadline: Optional[datetime] = None
    option_count_total: Optional[int] = None
    option_count_used: Optional[int] = None
    # Kostnadsfordeling (fra CSV/import)
    caretaker_cost: Optional[float] = None
    cleaning_cost: Optional[float] = None
    parking_cost: Optional[float] = None
    card_reader_cost: Optional[float] = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    unit_id: Optional[UUID] = None
    party_id: Optional[UUID] = None
    status: Optional[ContractStatus] = None
    periods: Optional[List[Period]] = None
    amount: Optional[Amount] = None
    signed_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None


class Contract(ContractBase):
    contract_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    filename_region: Optional[str] = None
    filename_type: Optional[str] = None
    filename_number: Optional[int] = None

    # Enhanced Fields (Joined)
    # Enhanced Fields (Joined) - Keeping shallow fields for backward compatibility if needed, 
    # but ideally frontend switches to nested objects.
    party_name: Optional[str] = None
    property_address: Optional[str] = None
    # property_id is already likely available via unit.property_id or we can map it.
    
    # Nested Objects
    unit: Optional[Unit] = None
    party: Optional[Party] = None
    property: Optional[Property] = None # Explicit property field as requested
    files: List[File] = []
    
    @model_validator(mode='before')
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        """Konverter JSON-felter fra dict/list/string til Pydantic-modeller."""
        import json
        
        # Pydantic v2 calls model validator for validation too, check if we deal with dict
        if isinstance(data, dict):
            if 'periods' in data:
                periods = data['periods']
                if isinstance(periods, str):
                    try:
                        periods = json.loads(periods)
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if periods and isinstance(periods, list):
                    parsed_periods = []
                    for p in periods:
                        if isinstance(p, dict):
                             # Let Pydantic validation handle casting to Period later if we just pass dicts
                             parsed_periods.append(p)
                        else:
                            parsed_periods.append(p)
                    data['periods'] = parsed_periods
                elif periods:
                    data['periods'] = periods
            
            if 'amount' in data:
                amount = data['amount']
                if isinstance(amount, str):
                    try:
                        amount = json.loads(amount)
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                if isinstance(amount, dict):
                   data['amount'] = amount
                elif amount:
                   data['amount'] = amount
                elif not amount:
                   data['amount'] = {"currency": "NOK", "amount_per_year": None}
        
        return data
    
    model_config = ConfigDict(from_attributes=True)
