from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, ForeignKey, Date, Numeric, SmallInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import validates
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.core.models.center import Center
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.user import User
class Property(Base):
    __tablename__ = "properties"

    property_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lokalisering_id = Column(String, nullable=True, index=True) # e.g., '6125'
    address = Column(String, nullable=True, index=True)
    postal_code = Column(String(4), nullable=True, index=True)
    city = Column(String, nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    # geom (PostGIS) omitted - not available on this host
    
    @validates("latitude")
    def validate_latitude(self, key, value):
        if value is not None and (value < -90 or value > 90):
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @validates("longitude")
    def validate_longitude(self, key, value):
        if value is not None and (value < -180 or value > 180):
            raise ValueError("Longitude must be between -180 and 180")
        return value
    
    # New Fields for Enhanced Information
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)  # Aggregert fra avtalenavn
    area = Column(String, nullable=True)  # Lok: Område (f.eks. "Øst / Oslo")
    usage = Column(String, nullable=True) # e.g., Næringseiendom
    total_area = Column(Float, nullable=True) # m2
    land_area = Column(Float, nullable=True) # Tomteareal m2
    construction_year = Column(Integer, nullable=True)
    energy_label = Column(String, nullable=True) # e.g., B
    municipality = Column(String, nullable=True)
    municipality_code = Column(String, nullable=True)
    gnr = Column(Integer, nullable=True)
    bnr = Column(Integer, nullable=True)
    approved_places = Column(Integer, nullable=True) # Antall godkjente plasser
    region = Column(String, nullable=True)  # Standard: Nord, Midt-Norge, Vest, Sør, Øst, Bufdir (docs/REGION_STANDARD.md)
    
    # e-don2 Enhanced Fields
    affiliation = Column(String, nullable=True) # Tilhørighet
    budgeted_places = Column(Integer, nullable=True) # Antall budsjetterte plasser
    legal_basis = Column(String, nullable=True) # Hjemler
    closed_at = Column(DateTime, nullable=True) # Nedlagt Dato
    ownership_type = Column(String, nullable=True) # Eierskapenhet
    unit_id_erp = Column(String, nullable=True, index=True) # EnhetID (from ERP/e-don2)
    unit_short_type = Column(String, nullable=True)  # Enhetskorttype: Avdeling | Barnevernsinstitusjon
    unit_type_derived = Column(String, nullable=True)  # Enhetstype (Utledet): Barnevernsinstitusjon | Institusjonsavdeling | Omsorgssenter
    parent_unit_id_erp = Column(String, nullable=True, index=True)  # TilhørighetEnhetID fra e-don2 (organisatorisk forelder)
    department_code = Column(String, nullable=True)  # Avdelingens koststed (1:1 med institusjon)
    department_name = Column(String, nullable=True)  # Navn på avdeling (1:1 med institusjon)

    # SRS-felt — regnskapskobling
    koststed_kode      = Column(String(20), nullable=True, index=True)  # Agresso Dim1-kode, f.eks. "635703"
    leiekontrakt_utlop = Column(Date, nullable=True)                    # Påkrevd for SRS 17 avskrivning
    
    # Ownership and Regulation
    owner_name = Column(String, nullable=True) # Hjemmelshaver
    org_number = Column(String, nullable=True) # Org.nr utleier/hjemmelshaver
    regulation_type = Column(String, nullable=True) # 100% KPI, etc.
    
    # Project / Refurbishment
    project_phase = Column(String, nullable=True) # B2-B4
    project_comments = Column(String, nullable=True)
    
    # Extended Address
    full_address = Column(JSONB, nullable=True) # Structured address layout
    
    # Phase 2: Center & Crisis
    center_id = Column(String, ForeignKey("centers.center_id"), nullable=True)
    crisis_contacts = Column(JSONB, nullable=True) # Property-specific emergency contacts

    # ── Kontraktsøkonomi (CSV: eiendomsoversikt / portefølje) ─────────────────
    malgruppe              = Column(String(100), nullable=True)  # Akutt / Omsorg / BFS / FVK / Kontor
    contract_rent_nok      = Column(Numeric(14, 2), nullable=True)  # Avtalefestet husleie kr/år (fra leieavtale)
    contract_maint_nok     = Column(Numeric(14, 2), nullable=True)  # Indre vedlikehold kr/år
    contract_common_nok    = Column(Numeric(14, 2), nullable=True)  # Felleskostnader kr/år
    contract_user_ops_nok  = Column(Numeric(14, 2), nullable=True)  # Brukeravhengige driftskostnader kr/år
    extension_terms        = Column(String(500), nullable=True)   # Adgang til forlengelse og vilkår
    price_adj_clause       = Column(String(300), nullable=True)   # Leieregulering / prisjusteringsfaktor

    # ── GL-regnskap (faktisk husleie 2025) ────────────────────────────────────
    gl_rent_2025           = Column(Numeric(14, 2), nullable=True)  # Faktisk husleie 2025 (srs_kategori='Lokaler')

    # ── KPI-justert husleie 2026 (beregnet fra SSB KPI, oppdatert per script) ──
    husleie_2026           = Column(Numeric(14, 2), nullable=True)  # KPI-justert husleie 2026 (beregnet alternativ A)
    husleie_2026_kpi_note  = Column(String(100), nullable=True)     # KPI-justeringsnotat (f.eks. "+24.2% (KPI*100%)")

    # ── Geografisk hierarki (CSV: eiendomsoversikt / portefølje) ──────────────
    lok_omrade             = Column(String(50), nullable=True)   # Lok: Område  (f.eks. "03 - Trøndelag")
    lok_distrikt           = Column(String(50), nullable=True)   # Lok: Distrikt (f.eks. "01 - Nord")
    fylke                  = Column(String(50), nullable=True)   # Fylke (f.eks. "Trøndelag")

    # ── Areal fra leiekontrakt ────────────────────────────────────────────────
    leased_area_kvm        = Column(Numeric(10, 1), nullable=True)  # Areal inkl fellesareal i leiekontrakt (kvm)

    # ── Eiendomsegnethet og utviklingsplan (fremtidige CSV-eksporter) ─────────
    egnethet_lokalisering  = Column(String(100), nullable=True)
    egnethet_bygg          = Column(String(100), nullable=True)
    prioritert_videroforing = Column(String(50), nullable=True)
    ar_videreutvikling     = Column(Integer, nullable=True)
    kostnader_videreutvikling = Column(Numeric(14, 2), nullable=True)

    # ── Systemreferanser ──────────────────────────────────────────────────────
    elements_id            = Column(String(200), nullable=True)  # Elements saksnummer
    utleier_kategori       = Column(SmallInteger, nullable=True)  # 1 = privat, 2 = offentlig

    # ── Nye felt fra Eiendomsportefølje-CSV (mai 2025) ───────────────────────
    tilstandsgrad                  = Column(String, nullable=True)          # Tilstandsgrad (TG0–TG3)
    antall_ansatte                 = Column(Integer, nullable=True)         # Antall ansatte
    p_plasser                      = Column(Integer, nullable=True)         # Parkerings-plasser
    eksklusivt_areal_kvm           = Column(Numeric(10, 1), nullable=True)  # Eksklusivt areal (kvm)
    tilleggsareal_kvm              = Column(Numeric(10, 1), nullable=True)  # Tilleggsareal (kvm)
    reduksjon_addendum_kvm         = Column(Numeric(10, 1), nullable=True)  # Reduksjon/addendum (kvm)
    energi_kr_per_ar               = Column(Numeric(14, 2), nullable=True)  # Energikostnader kr/år
    oppvarming_kr_per_ar           = Column(Numeric(14, 2), nullable=True)  # Oppvarmingskostnader kr/år
    mva_kompensasjon_kr_per_ar     = Column(Numeric(14, 2), nullable=True)  # MVA-kompensasjon kr/år
    kontantinnskudd_kr             = Column(Numeric(14, 2), nullable=True)  # Kontantinnskudd kr
    kpi_oppstartsdato              = Column(Date, nullable=True)            # KPI-oppstartsdato
    kontraktsleie_ved_oppstart_kr  = Column(Numeric(14, 2), nullable=True)  # Kontraktsleie ved oppstart kr
    kommunale_gebyrer_kr           = Column(Numeric(14, 2), nullable=True)  # Kommunale gebyrer kr/år
    kommentar                      = Column(Text, nullable=True)            # Kommentar

    external_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    center = relationship("Center", back_populates="properties")
    # contracts = relationship("Contract", back_populates="property")
    risk_assessments = relationship("RiskAssessment", back_populates="property", lazy="selectin")
    cases = relationship("InternalControlCase", back_populates="property", lazy="selectin")
