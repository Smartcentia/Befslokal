-- SRS Regnskap Fase 1: koststed på Property, ny GLTransaction, KoststedMapping, FixedAsset
-- 2026-03-21

-- 1. Property: nye SRS-felt
ALTER TABLE properties ADD COLUMN IF NOT EXISTS koststed_kode VARCHAR(20);
ALTER TABLE properties ADD COLUMN IF NOT EXISTS leiekontrakt_utlop DATE;
CREATE INDEX IF NOT EXISTS ix_properties_koststed_kode ON properties(koststed_kode);

-- 2. Dropp gamle tomme tabeller
DROP TABLE IF EXISTS gl_transactions CASCADE;
DROP TABLE IF EXISTS budget CASCADE;
DROP TABLE IF EXISTS koststed_mapping CASCADE;
DROP TABLE IF EXISTS fixed_assets CASCADE;

-- 3. Ny gl_transactions med full SRS-struktur
CREATE TABLE gl_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id VARCHAR(100),
    imported_by VARCHAR(100),
    source_file_ref VARCHAR(500),
    ba_kode VARCHAR(10),
    bilagsnr VARCHAR(50),
    bilagsdato DATE,
    periode VARCHAR(6),
    ar INTEGER,
    maaned INTEGER,
    konto VARCHAR(20),
    konto_navn VARCHAR(200),
    av_konto VARCHAR(20),
    region VARCHAR(50),
    dim1_kode VARCHAR(20),
    dim1_navn VARCHAR(200),
    dim2_kode VARCHAR(20),
    dim2_navn VARCHAR(200),
    dim3_kode VARCHAR(20),
    dim4_kode VARCHAR(20),
    dim5_kode VARCHAR(20),
    dim6_anlegg_id VARCHAR(20),
    dim6_ansatt_id VARCHAR(20),
    dim7_kode VARCHAR(20),
    tekst VARCHAR(500),
    belop NUMERIC(19,4) NOT NULL,
    leverandor_id VARCHAR(20),
    leverandor_navn VARCHAR(200),
    property_id UUID REFERENCES properties(property_id),
    srs_kategori VARCHAR(20),
    is_statsbygg BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ
);

CREATE INDEX ix_gl_bilagsnr  ON gl_transactions(bilagsnr);
CREATE INDEX ix_gl_konto     ON gl_transactions(konto);
CREATE INDEX ix_gl_dim1_kode ON gl_transactions(dim1_kode);
CREATE INDEX ix_gl_periode   ON gl_transactions(periode);
CREATE INDEX ix_gl_ar        ON gl_transactions(ar);
CREATE INDEX ix_gl_property  ON gl_transactions(property_id);

-- 4. Ny budget med NUMERIC
CREATE TABLE budget (
    budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID NOT NULL REFERENCES properties(property_id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount NUMERIC(19,4) NOT NULL,
    is_synthetic BOOLEAN NOT NULL DEFAULT false,
    data_source VARCHAR(100),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- 5. koststed_mapping
CREATE TABLE koststed_mapping (
    koststed_kode VARCHAR(20) PRIMARY KEY,
    koststed_navn VARCHAR(200),
    region VARCHAR(50),
    eksempel_adresse VARCHAR(500),
    property_id UUID REFERENCES properties(property_id)
);

-- 6. fixed_assets
CREATE TABLE fixed_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_name VARCHAR(500) NOT NULL,
    property_id UUID REFERENCES properties(property_id),
    koststed_kode VARCHAR(20) NOT NULL,
    agresso_dim6_id VARCHAR(20),
    original_account VARCHAR(20),
    purchase_date DATE,
    acquisition_cost NUMERIC(19,4) NOT NULL,
    opening_balance_value NUMERIC(19,4),
    monthly_depreciation_amount NUMERIC(19,4),
    remaining_months_at_start INTEGER,
    lease_end_date DATE,
    depreciation_account VARCHAR(20) DEFAULT '6010',
    accum_depr_account VARCHAR(20) DEFAULT '1269',
    neutralization_account VARCHAR(20) DEFAULT '3390',
    financing_account VARCHAR(20) DEFAULT '3390',
    is_grouped BOOLEAN NOT NULL DEFAULT false,
    is_fully_depreciated BOOLEAN NOT NULL DEFAULT false,
    srs_status VARCHAR(20) NOT NULL DEFAULT 'Aktiv',
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

CREATE INDEX ix_asset_property ON fixed_assets(property_id);
CREATE INDEX ix_asset_koststed ON fixed_assets(koststed_kode);
CREATE INDEX ix_asset_dim6     ON fixed_assets(agresso_dim6_id);
