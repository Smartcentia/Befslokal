"""
Finansmodeller for BEFS — SRS-kompatibel regnskapsmodul.

Arkitekturregler:
- Aldri Float for beløp — bruk Numeric(19,4)
- Aldri named PG Enums — bruk Column(String)
- Aldri UPDATE/DELETE på gl_transactions — immutabel audit-trail
- Filtrer alltid på `periode` (YYYYMM), IKKE på bilagsdato
- Alle koder er VARCHAR — "0012" ≠ "12"
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Numeric
import uuid
from app.db.base_class import Base


class Budget(Base):
    """Budsjettdata per eiendom / år / kategori."""
    __tablename__ = "budget"

    budget_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    year        = Column(Integer, nullable=False)
    month       = Column(Integer, nullable=False)
    category    = Column(String(100), nullable=False)
    amount      = Column(Numeric(19, 4), nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    data_source  = Column(String(100), nullable=True)
    created_at   = Column(DateTime(timezone=True), nullable=True)
    updated_at   = Column(DateTime(timezone=True), nullable=True)


class KoststedMapping(Base):
    """
    Mapping av Agresso Dim1-kode (koststed) til region og eiendom.
    Populeres fra finans/koststed_eiendom_mapping.csv (572 rader).
    """
    __tablename__ = "koststed_mapping"

    koststed_kode    = Column(String(20), primary_key=True)          # Dim1-kode, f.eks. "635703"
    koststed_navn    = Column(String(200), nullable=True)            # Dim1(T), f.eks. "Enhet for spesialiserte fosterhjem"
    region           = Column(String(50), nullable=True)             # Nord / Sør / Vest / Midt / Øst / Bufdir
    eksempel_adresse = Column(String(500), nullable=True)            # Adresse-hint fra Agresso Tekst-felt
    property_id      = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True)


class GLTransaction(Base):
    """
    General Ledger — Agresso transaksjoner (immutabel).

    Datagrunnlag: Agresso CSV-eksport (Eiendomfebruar.csv og etterfølgere).
    Kolonner: BA, region/Bilagsnr, Bilagsdato, År, Periode,
              Innkjøpskategorier, Innkjøpskategorier(T), Underkategorier, Underkategorier(T),
              Konto, Konto(T), Region, Dim1–Dim7, AV, Tekst, Beløp, Resk.nr, Resk.nr(T).
    Merk: Fra 2025 heter bilagsnr-kolonnen "region" (liten r) i eksporten.

    IMMUTABILITET: Aldri UPDATE/DELETE. Feil rettes med RE/H1-bilag.
    """
    __tablename__ = "gl_transactions"

    # --- Primærnøkkel og sporing ---
    transaction_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id        = Column(String(100), nullable=True)   # importbunt-ID (timestamp + filnavn)
    imported_by     = Column(String(100), nullable=True)   # bruker-e-post
    source_file_ref = Column(String(500), nullable=True)   # filnavn / blob-URL

    # --- Agresso-felt (direkte fra CSV) ---
    ba_kode         = Column(String(10),  nullable=True)   # BA – Bilagsart (IV, IW, LE, MT, H1, RE ...)
    bilagsnr        = Column(String(50),  nullable=True)   # Bilagsnr — indeksert
    bilagsdato      = Column(Date,        nullable=True)   # Bilagsdato
    periode         = Column(String(6),   nullable=True)   # YYYYMM — bruk dette til filtrering
    ar              = Column(Integer,     nullable=True)   # År (avledet fra periode)
    maaned          = Column(Integer,     nullable=True)   # Måned (avledet fra periode)

    konto           = Column(String(20),  nullable=True)   # Konto-kode, f.eks. "6300"
    konto_navn      = Column(String(200), nullable=True)   # Konto(T)
    av_konto        = Column(String(20),  nullable=True)   # AV (statskontoplan)

    innkjopskategori_kode = Column(String(20),  nullable=True)   # Innkjøpskategorier-kode
    innkjopskategori_navn = Column(String(200), nullable=True)   # Innkjøpskategorier(T)
    underkategori_kode    = Column(String(20),  nullable=True)   # Underkategorier-kode
    underkategori_navn    = Column(String(200), nullable=True)   # Underkategorier(T)

    region          = Column(String(50),  nullable=True)   # Nord / Sør / Vest / Midt / Øst / Bufdir
    dim1_kode       = Column(String(20),  nullable=True)   # Koststed-kode — indeksert
    dim1_navn       = Column(String(200), nullable=True)   # Koststed-navn
    dim2_kode       = Column(String(20),  nullable=True)
    dim2_navn       = Column(String(200), nullable=True)
    dim3_kode       = Column(String(20),  nullable=True)   # Formål
    dim4_kode       = Column(String(20),  nullable=True)   # Finansiering (tildelingsbrev)
    dim5_kode       = Column(String(20),  nullable=True)
    dim6_anlegg_id  = Column(String(20),  nullable=True)   # Anleggsnummer (påkrevd for konto 1268/4960)
    dim6_ansatt_id  = Column(String(20),  nullable=True)   # Ansattnummer (andre kontoer)
    dim7_kode       = Column(String(20),  nullable=True)

    tekst           = Column(String(500), nullable=True)   # Beskrivelsestekst
    belop           = Column(Numeric(19, 4), nullable=False)  # ALDRI Float
    leverandor_id   = Column(String(20),  nullable=True)   # Resk.nr
    leverandor_navn = Column(String(200), nullable=True)   # Resk.nr(T)

    # --- Berikede felt (beregnet ved import) ---
    property_id     = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True)
    srs_kategori    = Column(String(20),  nullable=True)   # 'Drift' | 'Investering' | 'Gjennomstrømning'
    is_statsbygg    = Column(Boolean, default=False, nullable=False)  # leverandor_navn ILIKE '%statsbygg%'

    # --- Ompostering / korreksjon ---
    # Peker på original transaction_id som denne linjen korrigerer.
    # H1/H2/HB/RE-bilag setter denne. Originalbilag røres aldri (immutabilitet).
    original_bilag_id = Column(UUID(as_uuid=True), ForeignKey("gl_transactions.transaction_id"), nullable=True)
    ompostert_av      = Column(String(100), nullable=True)   # e-post til den som opprettet omposteringen
    ompostert_at      = Column(DateTime(timezone=True), nullable=True)
    omposterings_kommentar = Column(String(500), nullable=True)

    created_at      = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_gl_bilagsnr",   "bilagsnr"),
        Index("ix_gl_konto",      "konto"),
        Index("ix_gl_dim1_kode",  "dim1_kode"),
        Index("ix_gl_periode",    "periode"),
        Index("ix_gl_ar",         "ar"),
        Index("ix_gl_property",   "property_id"),
    )


class FixedAsset(Base):
    """
    Anleggsregister — SRS 17 (Anleggsmidler) + SRS 10 (Nøytralisering).

    Populeres fra GLTransaction der konto IN ('1268', '4960') og beløp >= 50 000 kr,
    eller via gruppering av IT-utstyr (PC/Skjerm/IKT) under terskelverdi.

    Avskrivning: lineær over MIN(levetid, gjenværende leieperiode) — SRS 17 pkt 39.
    Nøytralisering: For hver avskrivning genereres motpost mot statens finansiering (SRS 10).
    """
    __tablename__ = "fixed_assets"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_name      = Column(String(500), nullable=False)   # Fra Tekst / Dim1(T) / gruppenavn

    # --- Kobling ---
    property_id     = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True)
    koststed_kode   = Column(String(20), nullable=False)    # Dim1
    agresso_dim6_id = Column(String(20), nullable=True)     # Dim6 anleggsnummer fra Agresso

    # --- Inngangsverdier (fra Fase 2 import) ---
    original_account    = Column(String(20), nullable=True)     # '1268' eller '4960'
    purchase_date       = Column(Date, nullable=True)           # Bilagsdato
    acquisition_cost    = Column(Numeric(19, 4), nullable=False) # Opprinnelig beløp (bruttosum)

    # --- SRS-beregningsfelter (Fase 3) ---
    opening_balance_value       = Column(Numeric(19, 4), nullable=True)   # Bokført verdi 01.01.2025
    monthly_depreciation_amount = Column(Numeric(19, 4), nullable=True)   # Månedlig avskrivning
    remaining_months_at_start   = Column(Integer, nullable=True)          # Måneder igjen fra 01.01.2025
    lease_end_date              = Column(Date, nullable=True)             # Fra Property.leiekontrakt_utlop

    # --- Regnskapsstyring (SRS 10) ---
    depreciation_account    = Column(String(20), default="6010", nullable=True)  # Debet kostnad
    accum_depr_account      = Column(String(20), default="1269", nullable=True)  # Kredit akk. avskr.
    neutralization_account  = Column(String(20), default="3390", nullable=True)  # Kredit inntektsf.
    financing_account       = Column(String(20), default="3390", nullable=True)  # Statens finansiering

    # --- Status ---
    is_grouped          = Column(Boolean, default=False, nullable=False)  # True = IT-gruppering
    is_fully_depreciated = Column(Boolean, default=False, nullable=False)
    srs_status          = Column(String(20), default="Aktiv", nullable=False)  # Aktiv / Fullt_avskrevet / Solgt

    created_at  = Column(DateTime(timezone=True), nullable=True)
    updated_at  = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_asset_property",  "property_id"),
        Index("ix_asset_koststed",  "koststed_kode"),
        Index("ix_asset_dim6",      "agresso_dim6_id"),
    )


class SalaryCost(Base):
    """
    Lønnskostnader per eiendom og år.

    Populeres via admin CSV-import (salary_import_service.py).
    Kildedata: Innkjøpsanalyse 2026 lønnsutgifter (pivot-CSV).
    UNIQUE(property_id, year) — idempotent upsert.
    """
    __tablename__ = "salary_costs"

    salary_cost_id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id         = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True)
    year                = Column(Integer, nullable=False)
    faste_stillinger    = Column(Numeric(19, 4), nullable=False, default=0)
    vikarer             = Column(Numeric(19, 4), nullable=False, default=0)
    arbeidsgiveravgift  = Column(Numeric(19, 4), nullable=False, default=0)
    institution_name_raw = Column(String(500), nullable=True)   # kildenavn fra CSV (audit)
    import_batch_id     = Column(String(100), nullable=True)
    imported_at         = Column(DateTime(timezone=True), nullable=True)
    data_source         = Column(String(100), nullable=True)    # f.eks. 'innkjopsanalyse_2026_excel'
    is_partial_year     = Column(Boolean, nullable=False, default=False)  # True for delår (f.eks. 2026)

    __table_args__ = (
        UniqueConstraint("property_id", "year", name="uq_salary_costs_property_year"),
        Index("ix_salary_costs_property", "property_id"),
        Index("ix_salary_costs_year",     "year"),
    )

    @property
    def total(self) -> float:
        return float(self.faste_stillinger or 0) + float(self.vikarer or 0) + float(self.arbeidsgiveravgift or 0)


class FinanceBudget(Base):
    """
    Vedtatt budsjett fra økonomi-avdelingen (Bufdir-økonomi).

    Holdes i egen tabell — ALDRI i budget-tabellen — for å forhindre
    sammenblanding med BEFS-prediksjoner (is_synthetic=True) og estimater.

    Idempotent import: re-import sletter og re-inseter alle rader med samme
    (year, data_source) uten å røre andre rader.
    """
    __tablename__ = "finance_budget"

    finance_budget_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id         = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True)
    koststed_kode       = Column(String(20),  nullable=True)    # Dim1-kode fra kildefila (revisjon)
    koststed_navn       = Column(String(200), nullable=True)    # Dim1(T) fra kildefila
    year                = Column(Integer,     nullable=False)
    month               = Column(Integer,     nullable=False)   # 1-12, fra Periode YYYYMM
    konto               = Column(String(20),  nullable=False)   # f.eks. "6300"
    konto_navn          = Column(String(200), nullable=True)
    category            = Column(String(50),  nullable=False)   # 'Lokaler' | 'Drift' | 'Vedlikehold'
    amount              = Column(Numeric(19, 4), nullable=False)  # Kontantbeløp — ALDRI Float
    finansiering_kode   = Column(String(20),  nullable=True)
    prosjekt_kode       = Column(String(20),  nullable=True)
    is_direktorat_level = Column(Boolean, default=False, nullable=False)  # True = koststed uten eiendom-match
    import_batch_id     = Column(String(100), nullable=True)
    imported_at         = Column(DateTime(timezone=True), nullable=True)
    data_source         = Column(String(100), nullable=False)   # 'finance_dept_2025' | 'finance_dept_2026'

    __table_args__ = (
        Index("ix_finance_budget_year",      "year"),
        Index("ix_finance_budget_property",  "property_id"),
        Index("ix_finance_budget_konto",     "konto"),
        Index("ix_finance_budget_koststed",  "koststed_kode"),
        Index("ix_finance_budget_source",    "data_source"),
    )


# Konto → kategori-mapping for økonomi-avdelingens uttrekk
FINANCE_KONTO_CATEGORY: dict[str | int, str] = {
    "6300": "Lokaler",  "6310": "Lokaler",  "6391": "Lokaler",
    "6395": "Lokaler",  "6396": "Lokaler",
    "6320": "Drift",    "6340": "Drift",    "6360": "Drift",
    "6364": "Drift",    "6365": "Drift",    "6390": "Drift",   "6398": "Drift",
    "6630": "Vedlikehold", "6632": "Vedlikehold", "6662": "Vedlikehold",
    "1268": "Vedlikehold", "4960": "Vedlikehold",
}


class InnkjopNasjonalSummary(Base):
    """
    Aggregerte nasjonale innkjøpskostnader per kategori, underkategori og region.

    Populeres fra Excel-eksport (Innkjøpsanalyse 2026 lønnsutgifter.xlsx).
    Dekker: Kjøp av barnevernstjenester, Lokaler, Varer og tjenester,
            Investeringer, Andre kostnader, Tilskudd, Klientkostnader.

    UNIQUE(ar, kategori, underkategori, region) — idempotent upsert.
    """
    __tablename__ = "innkjop_nasjonal_summary"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ar              = Column(Integer, nullable=False)
    kategori        = Column(String(200), nullable=False)
    underkategori   = Column(String(200), nullable=True)
    region          = Column(String(100), nullable=True)   # NULL = nasjonal sum
    belop           = Column(Numeric(19, 4), nullable=False)
    kilde_fane      = Column(String(100), nullable=True)
    import_batch_id = Column(String(100), nullable=True)
    imported_at     = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("ar", "kategori", "underkategori", "region",
                         name="uq_innkjop_ar_kat_underkat_region"),
        Index("ix_innkjop_ar",       "ar"),
        Index("ix_innkjop_kategori", "kategori"),
        Index("ix_innkjop_region",   "region"),
    )
