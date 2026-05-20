from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum
from app.schemas.user import UserMinimal

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
    description: Optional[str] = None
    area: Optional[str] = None
    usage: Optional[str] = None
    total_area: Optional[float] = None
    land_area: Optional[float] = None
    construction_year: Optional[int] = None
    energy_label: Optional[str] = None
    municipality: Optional[str] = None
    municipality_code: Optional[str] = None
    gnr: Optional[Any] = None # Can be int "14" or str "14/15"
    bnr: Optional[Any] = None # Can be int "2" or str "2, 4"
    risk_level: Optional[str] = None
    region: Optional[str] = None
    
    # e-don2 fields
    affiliation: Optional[str] = None
    center_id: Optional[str] = None
    center_name: Optional[str] = None
    approved_places: Optional[int] = None
    budgeted_places: Optional[int] = None
    legal_basis: Optional[str] = None
    regulation_type: Optional[str] = None
    owner_name: Optional[str] = None
    org_number: Optional[str] = None
    closed_at: Optional[datetime] = None
    ownership_type: Optional[str] = None
    unit_id_erp: Optional[str] = None
    unit_short_type: Optional[str] = None   # Enhetskorttype: Avdeling | Barnevernsinstitusjon
    unit_type_derived: Optional[str] = None  # Enhetstype (Utledet)
    parent_unit_id_erp: Optional[str] = None  # TilhørighetEnhetID fra e-don2 (organisatorisk forelder)
    parent_property_id: Optional[UUID] = None # Matched UUID for the parent property
    department_code: Optional[str] = None  # Avdelingens koststed (1:1 med institusjon)
    department_name: Optional[str] = None  # Navn på avdeling (1:1 med institusjon)
    koststed_kode: Optional[str] = None  # Agresso Dim1 (SRS)
    leiekontrakt_utlop: Optional[date] = None
    project_phase: Optional[str] = None
    project_comments: Optional[str] = None

    # ── Kontraktsøkonomi ──────────────────────────────────────────────────────
    malgruppe: Optional[str] = None              # Akutt / Omsorg / BFS / FVK / Kontor
    contract_rent_nok: Optional[float] = None    # Avtalefestet husleie kr/år (fra leieavtale)
    contract_maint_nok: Optional[float] = None   # Indre vedlikehold kr/år
    contract_common_nok: Optional[float] = None  # Felleskostnader kr/år
    contract_user_ops_nok: Optional[float] = None  # Brukeravhengige driftskostnader kr/år
    extension_terms: Optional[str] = None        # Adgang til forlengelse og vilkår
    price_adj_clause: Optional[str] = None       # Leieregulering / prisjusteringsfaktor

    # ── GL-regnskap ───────────────────────────────────────────────────────────
    gl_rent_2025: Optional[float] = None         # Faktisk husleie 2025 fra GL (srs_kategori='Lokaler')

    # ── KPI-justert husleie 2026 ──────────────────────────────────────────────
    husleie_2026: Optional[float] = None             # KPI-justert husleie 2026 (Alternativ A)
    husleie_2026_kpi_note: Optional[str] = None      # KPI-notat f.eks. "+24.2% (KPI*100%)"

    # ── Geografisk hierarki ───────────────────────────────────────────────────
    lok_omrade: Optional[str] = None             # Lok: Område  (f.eks. "03 - Trøndelag")
    lok_distrikt: Optional[str] = None           # Lok: Distrikt (f.eks. "01 - Nord")
    fylke: Optional[str] = None                  # Fylke (f.eks. "Trøndelag")

    # ── Areal fra leiekontrakt ────────────────────────────────────────────────
    leased_area_kvm: Optional[float] = None      # Areal inkl fellesareal i leiekontrakt (kvm)

    # ── Eiendomsegnethet og utviklingsplan ────────────────────────────────────
    egnethet_lokalisering: Optional[str] = None
    egnethet_bygg: Optional[str] = None
    prioritert_videroforing: Optional[str] = None
    ar_videreutvikling: Optional[int] = None
    kostnader_videreutvikling: Optional[float] = None

    # ── Systemreferanser ──────────────────────────────────────────────────────
    elements_id: Optional[str] = None            # Elements saksnummer
    utleier_kategori: Optional[int] = None       # 1 = privat, 2 = offentlig

    # ── Nye felt fra Eiendomsportefølje-CSV (mai 2025) ────────────────────────
    tilstandsgrad: Optional[str] = None                    # Tilstandsgrad (TG0–TG3)
    antall_ansatte: Optional[int] = None                   # Antall ansatte
    p_plasser: Optional[int] = None                        # Parkeringsplasser
    eksklusivt_areal_kvm: Optional[float] = None           # Eksklusivt areal (kvm)
    tilleggsareal_kvm: Optional[float] = None              # Tilleggsareal (kvm)
    reduksjon_addendum_kvm: Optional[float] = None         # Reduksjon/addendum (kvm)
    energi_kr_per_ar: Optional[float] = None               # Energikostnader kr/år
    oppvarming_kr_per_ar: Optional[float] = None           # Oppvarmingskostnader kr/år
    mva_kompensasjon_kr_per_ar: Optional[float] = None     # MVA-kompensasjon kr/år
    kontantinnskudd_kr: Optional[float] = None             # Kontantinnskudd kr
    kpi_oppstartsdato: Optional[date] = None               # KPI-oppstartsdato
    kontraktsleie_ved_oppstart_kr: Optional[float] = None  # Kontraktsleie ved oppstart kr
    kommunale_gebyrer_kr: Optional[float] = None           # Kommunale gebyrer kr/år
    kommentar: Optional[str] = None                        # Kommentar

    managers: Optional[List[UserMinimal]] = None

    # Avledet i API (ikke DB-kolonner): Bufdir-miniatyrbilde, primær kontraktsmotpart
    bufdir_image_path: Optional[str] = None
    primary_lease_party_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PropertyCreate(BaseModel):
    address: str
    postal_code: Optional[str] = None
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None

class PropertyUpdate(BaseModel):
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None
    name: Optional[str] = None
    municipality: Optional[str] = None
    municipality_code: Optional[str] = None
    gnr: Optional[Any] = None
    bnr: Optional[Any] = None
    center_id: Optional[str] = None
    center_name: Optional[str] = None
    owner_name: Optional[str] = None
    usage: Optional[str] = None
    affiliation: Optional[str] = None
    malgruppe: Optional[str] = None
    approved_places: Optional[int] = None
    budgeted_places: Optional[int] = None
    contract_rent_nok: Optional[float] = None
    contract_maint_nok: Optional[float] = None
    contract_common_nok: Optional[float] = None
    contract_user_ops_nok: Optional[float] = None
    extension_terms: Optional[str] = None
    price_adj_clause: Optional[str] = None
    lok_omrade: Optional[str] = None
    lok_distrikt: Optional[str] = None
    egnethet_lokalisering: Optional[str] = None
    egnethet_bygg: Optional[str] = None
    legal_basis: Optional[str] = None
    regulation_type: Optional[str] = None
    leased_area_kvm: Optional[float] = None
    tilstandsgrad: Optional[str] = None
    antall_ansatte: Optional[int] = None
    p_plasser: Optional[int] = None
    eksklusivt_areal_kvm: Optional[float] = None
    tilleggsareal_kvm: Optional[float] = None
    reduksjon_addendum_kvm: Optional[float] = None
    energi_kr_per_ar: Optional[float] = None
    oppvarming_kr_per_ar: Optional[float] = None
    mva_kompensasjon_kr_per_ar: Optional[float] = None
    kontantinnskudd_kr: Optional[float] = None
    kpi_oppstartsdato: Optional[date] = None
    kontraktsleie_ved_oppstart_kr: Optional[float] = None
    kommunale_gebyrer_kr: Optional[float] = None
    kommentar: Optional[str] = None

class UnitBase(BaseModel):
    property_id: UUID
    address: Optional[str] = None
    purpose: Optional[str] = None
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
    address: Optional[str] = None
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
    reference_code: Optional[str] = None  # BUF-P-NNNNNN
    created_at: datetime
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    active_contract_count: Optional[int] = None  # Fylles av API ved GET /parties/{id}
    health_score: Optional[Dict[str, Any]] = None  # Beregnet av party_health_service

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
    contract_name: Optional[str] = None
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
