-- Befslokal: legg til kolonner som mangler etter delvis schema-import
ALTER TABLE properties
  ADD COLUMN IF NOT EXISTS malgruppe VARCHAR(100),
  ADD COLUMN IF NOT EXISTS contract_rent_nok NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS contract_maint_nok NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS contract_common_nok NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS contract_user_ops_nok NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS extension_terms VARCHAR(500),
  ADD COLUMN IF NOT EXISTS price_adj_clause VARCHAR(300),
  ADD COLUMN IF NOT EXISTS gl_rent_2025 NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS husleie_2026 NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS husleie_2026_kpi_note VARCHAR(100),
  ADD COLUMN IF NOT EXISTS lok_omrade VARCHAR(50),
  ADD COLUMN IF NOT EXISTS lok_distrikt VARCHAR(50),
  ADD COLUMN IF NOT EXISTS fylke VARCHAR(50),
  ADD COLUMN IF NOT EXISTS leased_area_kvm NUMERIC(10,1),
  ADD COLUMN IF NOT EXISTS egnethet_lokalisering VARCHAR(100),
  ADD COLUMN IF NOT EXISTS egnethet_bygg VARCHAR(100),
  ADD COLUMN IF NOT EXISTS prioritert_videroforing VARCHAR(50),
  ADD COLUMN IF NOT EXISTS ar_videreutvikling INTEGER,
  ADD COLUMN IF NOT EXISTS kostnader_videreutvikling NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS elements_id VARCHAR(200),
  ADD COLUMN IF NOT EXISTS utleier_kategori SMALLINT,
  ADD COLUMN IF NOT EXISTS tilstandsgrad VARCHAR(255),
  ADD COLUMN IF NOT EXISTS antall_ansatte INTEGER,
  ADD COLUMN IF NOT EXISTS p_plasser INTEGER,
  ADD COLUMN IF NOT EXISTS eksklusivt_areal_kvm NUMERIC(10,1),
  ADD COLUMN IF NOT EXISTS tilleggsareal_kvm NUMERIC(10,1),
  ADD COLUMN IF NOT EXISTS reduksjon_addendum_kvm NUMERIC(10,1),
  ADD COLUMN IF NOT EXISTS energi_kr_per_ar NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS oppvarming_kr_per_ar NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS mva_kompensasjon_kr_per_ar NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS kontantinnskudd_kr NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS kpi_oppstartsdato DATE,
  ADD COLUMN IF NOT EXISTS kontraktsleie_ved_oppstart_kr NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS kommunale_gebyrer_kr NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS kommentar TEXT;

CREATE TABLE IF NOT EXISTS system_settings (
  key VARCHAR(100) PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Lønnstabell (kreves for eiendomsliste med source_coverage=complete)
CREATE TABLE IF NOT EXISTS salary_costs (
  salary_cost_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id UUID REFERENCES properties(property_id),
  year INTEGER NOT NULL,
  faste_stillinger NUMERIC(19,4) NOT NULL DEFAULT 0,
  vikarer NUMERIC(19,4) NOT NULL DEFAULT 0,
  arbeidsgiveravgift NUMERIC(19,4) NOT NULL DEFAULT 0,
  institution_name_raw VARCHAR(500),
  import_batch_id VARCHAR(100),
  imported_at TIMESTAMPTZ DEFAULT now(),
  data_source VARCHAR(100),
  is_partial_year BOOLEAN NOT NULL DEFAULT false,
  turnustillegg NUMERIC(19,4),
  pensjonspremie NUMERIC(19,4),
  midlertidige NUMERIC(19,4),
  turnustillegg_vik NUMERIC(19,4),
  overtid_faste NUMERIC(19,4),
  overtid_midl NUMERIC(19,4),
  aga_spk NUMERIC(19,4),
  CONSTRAINT uq_salary_costs_property_year UNIQUE (property_id, year)
);
CREATE INDEX IF NOT EXISTS ix_salary_costs_property ON salary_costs(property_id);
CREATE INDEX IF NOT EXISTS ix_salary_costs_year ON salary_costs(year);
