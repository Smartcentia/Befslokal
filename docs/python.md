# Python Scripts – Utvidet dokumentasjon og sårbarhetsvurdering

Denne siden er auto-generert. Den beskriver hvert skript og inkluderer en heuristisk vurdering av sårbarheter/svakheter.
NB: Heuristikken er konservativ og kan gi falske positiver; bruk som sjekkliste ved kodegjennomgang.

---

## Høyrisiko skript (heuristisk)

- alter_property_table.py (backend/scripts/alter_property_table.py)
- check_hms_schema.py (backend/scripts/check_hms_schema.py)
- classify_data.py (backend/scripts/classify_data.py)
- clear_economic_data.py (backend/scripts/clear_economic_data.py)
- delete_synthetic_properties.py (backend/scripts/delete_synthetic_properties.py)
- find_all_bufetat.py (backend/scripts/find_all_bufetat.py)
- global_search.py (backend/scripts/global_search.py)
- show_database_schema.py (backend/scripts/show_database_schema.py)
- verify_ai_semantic.py (backend/scripts/verify_ai_semantic.py)

---

# Andre

## __init__.py
- Kategori: Andre
- Fil: backend/scripts/collectors/__init__.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Collectors package initialization.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## add_frank_user.py
- Kategori: Andre
- Fil: backend/scripts/add_frank_user.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Quick script to add Frank as admin user

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## add_metadata_column.py
- Kategori: Andre
- Fil: backend/scripts/add_metadata_column.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Add missing additional_metadata column.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## alter_property_table.py
- Kategori: Andre
- Fil: backend/scripts/alter_property_table.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Alter property table.

### Bruk
- ("usage", "VARCHAR"),

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## analyze_contract_fields_v2.py
- Kategori: Andre
- Fil: backend/scripts/analyze_contract_fields_v2.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASEFELTER
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze contract fields v2.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_elements_availability.py
- Kategori: Andre
- Fil: backend/scripts/analyze_elements_availability.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze elements availability.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## apply_schema_migration.py
- Kategori: Andre
- Fil: backend/scripts/apply_schema_migration.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Apply database schema changes for text_content table.
Adds full-text search support and vector search migration fields.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## approve_tool.py
- Kategori: Andre
- Fil: backend/scripts/approve_tool.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Approve tool.

### Bruk
- print("Usage: python scripts/approve_tool.py <tool_name|all>")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_address.py
- Kategori: Andre
- Fil: backend/scripts/check_address.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check address.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_auth_tables.py
- Kategori: Andre
- Fil: backend/scripts/check_auth_tables.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check auth tables.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_brreg_kunngjoringer.py
- Kategori: Andre
- Fil: backend/scripts/check_brreg_kunngjoringer.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Check brreg kunngjoringer.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_brreg_regnskap.py
- Kategori: Andre
- Fil: backend/scripts/check_brreg_regnskap.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Check brreg regnskap.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_db.py
- Kategori: Andre
- Fil: backend/scripts/check_db.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Direct SQL check on what was actually saved to database

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_losore.py
- Kategori: Andre
- Fil: backend/scripts/check_losore.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Maskinporten, BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Check losore.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_migration_safety.py
- Kategori: Andre
- Fil: scripts/check_migration_safety.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Pre-commit hook to check Alembic migrations for unsafe patterns.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## check_schema.py
- Kategori: Andre
- Fil: backend/scripts/check_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check schema.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_tools.py
- Kategori: Andre
- Fil: backend/scripts/check_tools.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check tools.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_users.py
- Kategori: Andre
- Fil: backend/scripts/check_users.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check users.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## cleanup_elements_verification.py
- Kategori: Andre
- Fil: backend/scripts/cleanup_elements_verification.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Cleanup elements verification.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## count_contracts.py
- Kategori: Andre
- Fil: backend/scripts/count_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Count contracts.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## count_unknown_parties.py
- Kategori: Andre
- Fil: backend/scripts/count_unknown_parties.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Count unknown parties.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## deep_scan_data.py
- Kategori: Andre
- Fil: backend/scripts/deep_scan_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Deep scan data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## diagnose_contract.py
- Kategori: Andre
- Fil: backend/scripts/diagnose_contract.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Diagnose contract.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## diagnose_jernbaneveien.py
- Kategori: Andre
- Fil: backend/scripts/diagnose_jernbaneveien.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Diagnose jernbaneveien.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fix_db_schema.py
- Kategori: Andre
- Fil: backend/scripts/fix_db_schema.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix db schema.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_embeddings.py
- Kategori: Andre
- Fil: backend/scripts/fix_embeddings.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix embeddings.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_empty_status.py
- Kategori: Andre
- Fil: backend/scripts/fix_empty_status.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix Invalid Contract Status Values

Some contracts have status="" (empty string) which violates the contractstatus enum.
This script fixes them to 'active' before we can update their metadata.

Usage:
    python3 scripts/fix_empty_status.py

### Bruk
- Usage:

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_trigger.py
- Kategori: Andre
- Fil: backend/scripts/fix_trigger.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix trigger creation with separate statements.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## generate_mcp_tool.py
- Kategori: Andre
- Fil: backend/scripts/generate_mcp_tool.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: GATEWAY_URL
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Generate mcp tool.

### Bruk
- print("Usage: python generate_tool_code.py <tool_name>")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## global_search.py
- Kategori: Andre
- Fil: backend/scripts/global_search.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Global search.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).

---

## init_db.py
- Kategori: Andre
- Fil: backend/scripts/init_db.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Init db.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_contracts.py
- Kategori: Andre
- Fil: backend/scripts/inspect_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect contracts.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_property_data.py
- Kategori: Andre
- Fil: backend/scripts/inspect_property_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect property data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_schema.py
- Kategori: Andre
- Fil: backend/scripts/inspect_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect schema.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_specific_property.py
- Kategori: Andre
- Fil: backend/scripts/inspect_specific_property.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect specific property.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_vectordb.py
- Kategori: Andre
- Fil: backend/scripts/inspect_vectordb.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CHROMA_DB_PATH
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect vectordb.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## list_properties.py
- Kategori: Andre
- Fil: backend/scripts/list_properties.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
List properties.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## populate_property_metadata.py
- Kategori: Andre
- Fil: backend/scripts/populate_property_metadata.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Populate property metadata.

### Bruk
- p_target.usage = "Næringseiendom"
- p_jern.usage = "Næringseiendom"
- if not p.usage:
- p.usage = "Næringseiendom"

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## regenerate_embeddings.py
- Kategori: Andre
- Fil: backend/scripts/regenerate_embeddings.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_EMBEDDING_MODEL
- Eksterne tjenester: OpenAI, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Regenerate embeddings.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## register_tools.py
- Kategori: Andre
- Fil: backend/scripts/register_tools.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Register tools.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## reset_db.py
- Kategori: Andre
- Fil: backend/scripts/reset_db.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Reset db.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## run_openai_query.py
- Kategori: Andre
- Fil: backend/scripts/run_openai_query.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
- Eksterne tjenester: OpenAI
- Risiko (heuristisk): Lav

### Beskrivelse
Kjør én enkel OpenAI-spørring for å verifisere at OPENAI_API_KEY og oppsett fungerer.
Bruker samme config som appen (app.core.config.settings).

Kjør fra prosjektrot:
  cd backend && python scripts/run_openai_query.py
eller fra backend:
  python scripts/run_openai_query.py

Alternativt med egen prompt:
  python scripts/run_openai_query.py "Din spørring her"

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## search_pattern.py
- Kategori: Andre
- Fil: backend/scripts/search_pattern.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Search pattern.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_elements_verification.py
- Kategori: Andre
- Fil: backend/scripts/seed_elements_verification.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed elements verification.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_query_library_storste_lav_husleie.py
- Kategori: Andre
- Fil: backend/scripts/seed_query_library_storste_lav_husleie.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed query_library med «største eiendommer med lav husleie».
Kjør: python backend/scripts/seed_query_library_storste_lav_husleie.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## sync_upgraded_tools.py
- Kategori: Andre
- Fil: backend/scripts/sync_upgraded_tools.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: FORCE_API_KEY
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Sync upgraded tools.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_brreg_connectivity.py
- Kategori: Andre
- Fil: backend/scripts/test_brreg_connectivity.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Test BRREG (Brønnøysundregistrene) connectivity.
Kjør fra prosjektrot: ./scripts/kjor_test_brreg.sh
eller fra backend:  python3 scripts/test_brreg_connectivity.py [orgnr]
Uten orgnr: tester med 984851006 (DNB).

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_chat_memory.py
- Kategori: Andre
- Fil: backend/scripts/test_chat_memory.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test chat memory.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_cost_query.py
- Kategori: Andre
- Fil: backend/scripts/test_cost_query.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test cost query.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_db_connect.py
- Kategori: Andre
- Fil: backend/scripts/test_db_connect.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test db connect.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_deviations_api.py
- Kategori: Andre
- Fil: backend/scripts/test_deviations_api.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: BASE_URL
- Eksterne tjenester: HTTP/requests
- Risiko (heuristisk): Middels

### Beskrivelse
Test deviations api.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- HTTP-kall uten timeout.

### Foreslåtte tiltak
- Legg til timeout=30 (eller passende).

---

## test_landslide_version.py
- Kategori: Andre
- Fil: backend/scripts/test_landslide_version.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: NVE
- Risiko (heuristisk): Lav

### Beskrivelse
Test landslide version.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_nve_endpoints.py
- Kategori: Andre
- Fil: backend/scripts/test_nve_endpoints.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: NVE
- Risiko (heuristisk): Lav

### Beskrivelse
Test nve endpoints.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_openai.py
- Kategori: Andre
- Fil: backend/scripts/test_openai.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: OPENAI_API_KEY, OPENAI_MODEL
- Eksterne tjenester: OpenAI
- Risiko (heuristisk): Lav

### Beskrivelse
Test openai.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_proactive_bench.py
- Kategori: Andre
- Fil: backend/scripts/test_proactive_bench.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test proactive bench.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_search.py
- Kategori: Andre
- Fil: backend/scripts/test_search.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Test search.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_sql_bench.py
- Kategori: Andre
- Fil: backend/scripts/test_sql_bench.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Test sql bench.

### Bruk
- # Check for SQL usage in sources

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## test_sql_generator_quick.py
- Kategori: Andre
- Fil: backend/scripts/dspy/test_sql_generator_quick.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: OPENAI_API_KEY
- Eksterne tjenester: OpenAI
- Risiko (heuristisk): Middels

### Beskrivelse
Test sql generator quick.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## test_toolbox.py
- Kategori: Andre
- Fil: backend/scripts/test_toolbox.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Test toolbox.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## trigger_evolution.py
- Kategori: Andre
- Fil: backend/scripts/trigger_evolution.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Trigger evolution.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## trigger_metrics_refresh.py
- Kategori: Andre
- Fil: backend/scripts/trigger_metrics_refresh.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Trigger metrics refresh.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_approval_table.py
- Kategori: Andre
- Fil: backend/scripts/verify_approval_table.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify approval table.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_brreg_persistence.py
- Kategori: Andre
- Fil: backend/scripts/verify_brreg_persistence.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify brreg persistence.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_contract_schema.py
- Kategori: Andre
- Fil: backend/scripts/verify_contract_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify contract schema.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_data_integrity.py
- Kategori: Andre
- Fil: backend/scripts/verify_data_integrity.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify data integrity.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_empty.py
- Kategori: Andre
- Fil: backend/scripts/verify_empty.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify empty.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_headers.py
- Kategori: Andre
- Fil: backend/scripts/verify_headers.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify headers.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_imports.py
- Kategori: Andre
- Fil: backend/scripts/verify_imports.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify imports.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_mcp_integration.py
- Kategori: Andre
- Fil: backend/scripts/verify_mcp_integration.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DOCKER_MCP_GATEWAY_URL
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify mcp integration.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_memory.py
- Kategori: Andre
- Fil: backend/scripts/verify_memory.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify memory.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_rrh_creds_v2.py
- Kategori: Andre
- Fil: backend/scripts/verify_rrh_creds_v2.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Verify rrh creds v2.

### Bruk
- print("Usage: python verify_rrh_creds_v2.py <username> <password>")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_tool_creation.py
- Kategori: Andre
- Fil: backend/scripts/verify_tool_creation.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify tool creation.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_upgrade.py
- Kategori: Andre
- Fil: backend/scripts/verify_upgrade.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify upgrade.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_vector_search.py
- Kategori: Andre
- Fil: backend/scripts/verify_vector_search.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: OpenAI, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Verify vector search.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

# Bufdir

## analyze_address_quality.py
- Kategori: Bufdir
- Fil: backend/scripts/analyze_address_quality.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Detaljert analyse av adressedata og koordinater

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_missing_addresses.py
- Kategori: Bufdir
- Fil: backend/scripts/check_missing_addresses.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Kartverket/Geonorge, Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Sjekk eiendommer med manglende adressedata

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fix_regions.py
- Kategori: Bufdir
- Fil: backend/scripts/fix_regions.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fix regions.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_bufdir_ids.py
- Kategori: Bufdir
- Fil: backend/scripts/inspect_bufdir_ids.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect bufdir ids.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## match_bufdir_to_properties.py
- Kategori: Bufdir
- Fil: backend/scripts/match_bufdir_to_properties.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Match bufdir to properties.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## test_bufdir_pagination.py
- Kategori: Bufdir
- Fil: backend/scripts/test_bufdir_pagination.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Test bufdir pagination.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_brreg_enhet.py
- Kategori: Bufdir
- Fil: backend/scripts/verify_brreg_enhet.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Verify brreg enhet.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_multi_agent.py
- Kategori: Bufdir
- Fil: backend/scripts/verify_multi_agent.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify multi agent.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_rrh_creds.py
- Kategori: Bufdir
- Fil: backend/scripts/verify_rrh_creds.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: BRREG
- Risiko (heuristisk): Lav

### Beskrivelse
Verify rrh creds.

### Bruk
- print("Usage: python verify_rrh_creds.py <username> <password>")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_web_tools.py
- Kategori: Bufdir
- Fil: backend/scripts/verify_web_tools.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify web tools.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

# Finans

## add_contract_category.py
- Kategori: Finans
- Fil: backend/scripts/add_contract_category.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Add contract category.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## add_region_column.py
- Kategori: Finans
- Fil: backend/scripts/add_region_column.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Add region column.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## advanced_financial_analysis.py
- Kategori: Finans
- Fil: backend/scripts/advanced_financial_analysis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Advanced financial data analysis with pattern recognition and intelligent auto-fix suggestions
This script takes more risks and provides actionable recommendations

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## aggregate_suppliers.py
- Kategori: Finans
- Fil: scripts/aggregate_suppliers.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Aggregate suppliers.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## analyze_contract_types.py
- Kategori: Finans
- Fil: backend/scripts/analyze_contract_types.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze contract types.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_contracts.py
- Kategori: Finans
- Fil: backend/scripts/analyze_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze contracts.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_einovember.py
- Kategori: Finans
- Fil: backend/scripts/analyze_einovember.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Script to analyze Einovember.xls and compare with database data

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_negative_amounts.py
- Kategori: Finans
- Fil: backend/scripts/analyze_negative_amounts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze negative amounts in financial transactions to identify:
1. Legitimate credit notes/corrections
2. Import errors
3. Patterns in negative amounts

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_price_per_sqm.py
- Kategori: Finans
- Fil: backend/scripts/analyze_price_per_sqm.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze contract data to calculate average price per square meter for rent estimation.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_regional_integrity.py
- Kategori: Finans
- Fil: backend/scripts/analyze_regional_integrity.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Deep analysis of regional integrity issues to understand:
1. Which properties have wrong regional data
2. Which source files are being incorrectly mapped
3. Scale of the problem per region
4. Whether this can be fixed or needs re-import

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## analyze_rent_discrepancy.py
- Kategori: Finans
- Fil: backend/scripts/analyze_rent_discrepancy.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Analyze rent discrepancy.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## analyze_usage_types.py
- Kategori: Finans
- Fil: backend/scripts/analyze_usage_types.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Analyze property usage types and prepare for update.

### Bruk
- Analyze property usage types and prepare for update.
- print("🏢 Analyzing Property Usage Types")
- # Get current property usage in database
- print(f"\n🗄️  Current database property usage:")
- usage = p.usage or "NULL"
- usage_counts[usage] = usage_counts.get(usage, 0) + 1
- for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
- print(f"  {usage}: {count}")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## apply_schema_migration_v2.py
- Kategori: Finans
- Fil: backend/scripts/apply_schema_migration_v2.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Apply database schema changes with explicit commit verification.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## audit_contracts.py
- Kategori: Finans
- Fil: backend/scripts/audit_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Comprehensive contract data audit

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## audit_data_quality.py
- Kategori: Finans
- Fil: backend/scripts/audit_data_quality.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Audit data quality.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## audit_expense_details.py
- Kategori: Finans
- Fil: backend/scripts/audit_expense_details.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Deep-dive audit to analyze expense patterns and detect duplicates

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## audit_financial_outliers.py
- Kategori: Finans
- Fil: backend/scripts/audit_financial_outliers.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Comprehensive audit to find financial data outliers and suspicious values

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## audit_incomplete_properties.py
- Kategori: Finans
- Fil: backend/scripts/audit_incomplete_properties.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Audit script to identify properties with missing or incomplete data

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## audit_missing_financial_data.py
- Kategori: Finans
- Fil: backend/scripts/audit_missing_financial_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Comprehensive audit to find properties missing financial data

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## calculate_total_rent.py
- Kategori: Finans
- Fil: backend/scripts/calculate_total_rent.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Calculate total rent.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## check_all_duplicates.py
- Kategori: Finans
- Fil: backend/scripts/check_all_duplicates.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Check all duplicates.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_contract_count.py
- Kategori: Finans
- Fil: backend/scripts/check_contract_count.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Quick database contract count check

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_data_quality.py
- Kategori: Finans
- Fil: backend/scripts/check_data_quality.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check data quality.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_db_permissions.py
- Kategori: Finans
- Fil: backend/scripts/check_db_permissions.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Check database write permissions and test insertion.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## check_db_rent.py
- Kategori: Finans
- Fil: backend/scripts/check_db_rent.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check db rent.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_gl_table_structure.py
- Kategori: Finans
- Fil: backend/scripts/check_gl_table_structure.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check the actual structure of gl_transactions table in the database.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_hms_schema.py
- Kategori: Finans
- Fil: backend/scripts/check_hms_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
!/usr/bin/env python3

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).

---

## check_internal_control_cases.py
- Kategori: Finans
- Fil: backend/scripts/check_internal_control_cases.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check internal control cases in the database using raw SQL to avoid ORM issues.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_properties_without_costs.py
- Kategori: Finans
- Fil: backend/scripts/check_properties_without_costs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check properties without cost data (contracts).

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_property_details.py
- Kategori: Finans
- Fil: backend/scripts/check_property_details.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check specific property details to answer user query.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_property_names.py
- Kategori: Finans
- Fil: backend/scripts/check_property_names.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check property names in database.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_regions.py
- Kategori: Finans
- Fil: backend/scripts/check_regions.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check regions.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## check_synthetic_data_coverage.py
- Kategori: Finans
- Fil: backend/scripts/check_synthetic_data_coverage.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Check which properties have synthetic monthly financial data.

This script verifies that all properties have generated time-series data
and reports which ones are missing data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## classify_data.py
- Kategori: Finans
- Fil: backend/scripts/classify_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL, POSTGRES_DB
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Classify data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## cleanup_bad_amounts.py
- Kategori: Finans
- Fil: backend/scripts/cleanup_bad_amounts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Clean up contracts with corrupted amounts (> 50M NOK threshold).
Sets erroneous amounts to NULL for manual correction.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## cleanup_duplicates.py
- Kategori: Finans
- Fil: backend/scripts/cleanup_duplicates.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Cleanup duplicates.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## clear_economic_data.py
- Kategori: Finans
- Fil: backend/scripts/clear_economic_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Clear economic data.

### Bruk
- Args: parser.add_argument("--force", action="store_true", help="Actually execute the deletion.")

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## compare_csv_portfolio.py
- Kategori: Finans
- Fil: backend/scripts/compare_csv_portfolio.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
CSV Portfolio Data Comparison Script

Compares CSV master table data with existing database records.
Generates detailed comparison report showing:
- New records (in CSV but not in DB)
- Updated records (differences between CSV and DB)
- Unchanged records (exact match)
- Orphaned records (in DB but not in CSV)

Usage:
    python3 scripts/compare_csv_portfolio.py [--validate-only]

### Bruk
- Usage:

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## compare_einovember.py
- Kategori: Finans
- Fil: backend/scripts/compare_einovember.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Compare Einovember.xls with database data to find discrepancies

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## compare_totalny.py
- Kategori: Finans
- Fil: backend/scripts/compare_totalny.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Compare totalny.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## comprehensive_rent_fix.py
- Kategori: Finans
- Fil: backend/scripts/comprehensive_rent_fix.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Comprehensive script to fix ALL rent data issues:
1. Find contracts with missing rent
2. Find contracts with corrupted rent (> 100M)
3. Import missing properties from total.txt
4. Fix mismatches

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## cost_analyzer.py
- Kategori: Finans
- Fil: backend/scripts/cost_analyzer.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
EXPERT PROPERTY COST ANALYZER
==============================
Intelligent script for finding, comparing, and analyzing property costs.

Usage examples:
  python cost_analyzer.py search "Alta"
  python cost_analyzer.py compare "Bodø" "Alta" "Tromsø"
  python cost_analyzer.py details "Bufetathus Kristiansand"
  python cost_analyzer.py region "01 - Nord"
  python cost_analyzer.py anomalies
  python cost_analyzer.py patterns    - Utvidede kostnadsmønstre (regional, leverandør, cluster, etc.)
  python cost_analyzer.py top 10 costs
  python cost_analyzer.py top 10 rent

### Bruk
- Usage examples:
- print("Usage: python cost_analyzer.py search <query>")
- print("Usage: python cost_analyzer.py details <property_name>")
- print("Usage: python cost_analyzer.py compare <prop1> <prop2> [prop3...]")
- print("Usage: python cost_analyzer.py region <region_name>")

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## cost_monitor.py
- Kategori: Finans
- Fil: backend/scripts/cost_monitor.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Cost Monitor - Main Orchestration Script

Collects cost data from all infrastructure services and stores in database.

### Bruk
- Args: parser.add_argument(; parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## count_core_data.py
- Kategori: Finans
- Fil: backend/scripts/count_core_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Viser antall eiendommer, enheter, kontrakter og partier (leietakere/utleiere) i databasen.

Kjør fra backend: python3 scripts/count_core_data.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## create_admin_users.py
- Kategori: Finans
- Fil: backend/scripts/create_admin_users.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Script to create 5 admin users with secure passwords.
Users are created with ADMIN role and email_verified=True (no email confirmation needed).

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## debug_prod_user.py
- Kategori: Finans
- Fil: backend/scripts/debug_prod_user.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Debug prod user.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## debug_rent_issue.py
- Kategori: Finans
- Fil: backend/scripts/debug_rent_issue.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Debug rent issue.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## debug_variance.py
- Kategori: Finans
- Fil: backend/scripts/debug_variance.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Debug variance.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## deep_cost_analysis.py
- Kategori: Finans
- Fil: backend/scripts/deep_cost_analysis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Deep cost analysis to identify additional data quality issues

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## delete_synthetic_properties.py
- Kategori: Finans
- Fil: backend/scripts/delete_synthetic_properties.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Delete synthetic properties and all related data.

This script:
1. Identifies all synthetic properties (external_data.is_synthetic = true)
2. Deletes all related data in correct order (CASCADE)
3. Deletes the properties themselves
4. Provides detailed logging and statistics
5. Supports dry-run mode for testing

WARNING: This operation is IRREVERSIBLE. Always run with --dry-run first!

### Bruk
- Args: parser.add_argument(; parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## dry_run_eiendom.py
- Kategori: Finans
- Fil: backend/scripts/dry_run_eiendom.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Dry run eiendom.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## dry_run_import_elements.py
- Kategori: Finans
- Fil: backend/scripts/dry_run_import_elements.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Dry run import elements.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## enrich_properties_bufdir.py
- Kategori: Finans
- Fil: backend/scripts/enrich_properties_bufdir.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Enrich properties with Bufdir data from bufdir_matches_robust.json.
Writes to external_data["bufdir"] with standard structure; downloads images to frontend/public/bufdir_images/.
Krever DATABASE_URL (lastes fra .env). Kjør fra prosjektrot: python backend/scripts/enrich_properties_bufdir.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## ensure_synthetic_contract_and_tenant.py
- Kategori: Finans
- Fil: backend/scripts/ensure_synthetic_contract_and_tenant.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Sikrer at alle syntetiske eiendommer har minst én syntetisk kontrakt og tilknyttet leietaker.
- Finner eiendommer der external_data.synthetic er True (eller data_source er 'synthetic').
- For hver slik eiendom uten aktiv kontrakt: oppretter én Unit, én Party (syntetisk leietaker)
  og én Contract (Leiekontrakt, aktiv) med external_data.synthetic = True.

Krever DATABASE_URL. For å merke alle eiendommer som syntetiske, kjør først
scripts/mark_all_properties_synthetic.py. Kan kjøres etter establish_bufdir_unmatched.py
eller uavhengig for å fylle inn manglende syntetisk kontrakt/leietaker.

### Bruk
- Args: parser.add_argument("--dry-run", action="store_true", help="Vis bare hva som ville blitt gjort")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## establish_bufdir_unmatched.py
- Kategori: Finans
- Fil: backend/scripts/establish_bufdir_unmatched.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Etabler eiendommer for bufdir-institusjoner som ikke matchet noen eiendom i datasettet.
Oppretter nye Property med samme bufdir-data (navn, beskrivelse, bilde, lovgrunnlag osv.)
og merker dem med syntetiske data (external_data.synthetic = true).
Krever DATABASE_URL (lastes fra .env). Kjør etter match_bufdir_robust.py.

### Bruk
- usage="Barnevernsinstitusjon",

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## export_financial_table.py
- Kategori: Finans
- Fil: backend/scripts/export_financial_table.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Export complete financial data table for all properties

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## export_properties_contracts.py
- Kategori: Finans
- Fil: backend/scripts/export_properties_contracts.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Export all properties and contracts to CSV for easy viewing.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## familievern_details.py
- Kategori: Finans
- Fil: backend/scripts/familievern_details.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Get detailed information about familievern contracts

### Bruk
- p.usage,
- address, municipality, region, area, places, usage, party_id,
- print(f"   Bruk: {usage}" if usage else "   Bruk: Ikke oppgitt")

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## fetch_bufdir_data.py
- Kategori: Finans
- Fil: backend/scripts/fetch_bufdir_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Hent barnevernsinstitusjoner fra bufdir.no/barnevern/finn-institusjon/.
Støtter automatisk henting med paginering (httpx) eller lesing fra lokal HTML (plan B).
Kjør fra prosjektrot: python backend/scripts/fetch_bufdir_data.py [--local]

### Bruk
- Args: parser.add_argument(

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## fetch_images_for_barnevern.py
- Kategori: Finans
- Fil: backend/scripts/fetch_images_for_barnevern.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
- Eksterne tjenester: OpenAI, Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Søker på nettet etter bilder for barnevernsinstitusjoner som mangler bilde.
Bruker LLM (OpenAI) til å foreslå effektive søkeord, deretter DuckDuckGo bildesøk.
Laster ned til frontend/public/bufdir_images/ og oppdaterer external_data.bufdir.

Krever: DATABASE_URL, nettverkstilgang. For LLM: OPENAI_API_KEY.
Kjør: python backend/scripts/fetch_images_for_barnevern.py [--dry-run] [--limit N] [--no-llm]

### Bruk
- # Finn barnevern-eiendommer (usage inneholder barnevern)
- Property.usage.ilike("%barnevern%"),
- Property.usage.ilike("%BARNEVERN%"),
- Args: parser.add_argument(; parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fill_budget_from_consumption.py
- Kategori: Finans
- Fil: backend/scripts/fill_budget_from_consumption.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Fyll budsjett-tabellen fra forbruk (manual_expenses) for 2024–2026 med ±variance per kategori.

Bruker cost_analysis_service for kategorisering og BudgetGenerationService.populate_budget_from_consumption.
Kjør fra backend-mappen:
  python3 scripts/fill_budget_from_consumption.py
  python3 scripts/fill_budget_from_consumption.py --years 2024,2025,2026
  python3 scripts/fill_budget_from_consumption.py --variance 0.15
  python3 scripts/fill_budget_from_consumption.py --property-ids <uuid1>,<uuid2>
  (Bruk ekte UUID-er; utelat --property-ids for alle eiendommer.)

### Bruk
- Args: p.add_argument(; p.add_argument("--variance", type=float, default=0.2, help="Variance per category, default 0.2 (±20%%)"); p.add_argument(

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fill_missing_rents.py
- Kategori: Finans
- Fil: backend/scripts/fill_missing_rents.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fill missing rent values using median price per square meter.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fill_remaining_zero_rents.py
- Kategori: Finans
- Fil: backend/scripts/fill_remaining_zero_rents.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Investigate and fill the 24 remaining properties with 0 rent.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## find_all_bufetat.py
- Kategori: Finans
- Fil: backend/scripts/find_all_bufetat.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Search for all types of Bufetat facilities

### Bruk
- p.usage,
- OR LOWER(CAST(p.usage AS TEXT)) LIKE :pattern
- GROUP BY p.property_id, p.name, p.address, p.municipality, p.region, p.usage
- prop_id, name, address, municipality, region, usage, contracts, active = facility
- if usage:
- print(f"    Bruk: {usage}")

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).

---

## find_elements_key.py
- Kategori: Finans
- Fil: backend/scripts/find_elements_key.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Find elements key.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## find_familievern.py
- Kategori: Finans
- Fil: backend/scripts/find_familievern.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Find all familievern (family counseling) contracts

### Bruk
- OR LOWER(CAST(p.usage AS TEXT)) LIKE '%familievern%'
- OR LOWER(CAST(p.usage AS TEXT)) LIKE '%familievern%'

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## find_good_example.py
- Kategori: Finans
- Fil: backend/scripts/find_good_example.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Check property details finding a good example.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## find_zero_rent.py
- Kategori: Finans
- Fil: backend/scripts/find_zero_rent.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Find zero rent.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## finn_og_fyll_leie_vedlikehold.py
- Kategori: Finans
- Fil: backend/scripts/finn_og_fyll_leie_vedlikehold.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Finn eiendommer som mangler Leie (YTD) eller Vedlikehold, og fyll med syntetisk data.
Med --all: berik ALLE eiendommer (sikrer at hver har financials; fyll manglende).

- Leie (YTD) = sum av aktive kontrakters amount_per_year.
- Vedlikehold = total_manual_expenses + total_spend_csv (eller total_maintenance).

Syntetisk logikk:
- Vedlikehold: utgifter med norske typer som cost_analysis forstår (Strøm og oppvarming, Renhold, etc.).
- Leie: Estimat fra areal (NOK/kvm) eller vedlikehold * multiplikator.

Kjør fra backend:
  python3 scripts/finn_og_fyll_leie_vedlikehold.py --dry-run
  python3 scripts/finn_og_fyll_leie_vedlikehold.py
  python3 scripts/finn_og_fyll_leie_vedlikehold.py --all    # berik alle eiendommer

### Bruk
- Args: parser.add_argument("--dry-run", action="store_true", help="Kun rapporter, ikke skriv til DB"); parser.add_argument("--all", dest="all_properties", action="store_true",

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_familievern_duplicate.py
- Kategori: Finans
- Fil: backend/scripts/fix_familievern_duplicate.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix duplicate familievern contracts

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_financial_discrepancies.py
- Kategori: Finans
- Fil: backend/scripts/fix_financial_discrepancies.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fix financial data discrepancies with multiple repair strategies

### Bruk
- Args: parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry-run)'); parser.add_argument('--dry-run', action='store_true', help='Dry run mode (default)')

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fix_financial_mixup.py
- Kategori: Finans
- Fil: backend/scripts/fix_financial_mixup.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fix financial mixup.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fix_negative_amounts.py
- Kategori: Finans
- Fil: backend/scripts/fix_negative_amounts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fix negative amounts that are clearly import errors while preserving legitimate credits.

Strategy:
1. Remove negatives in "Leie lokaler" categories (likely import errors - should never be negative)
2. Keep small negatives in utility categories (likely legitimate credits/adjustments)
3. Flag suspicious large negatives for manual review

### Bruk
- 'Strøm og oppvarming',  # Credit from usage estimates
- 'Renovasjon, vann, avløp o.l.',  # Usage adjustments

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## fix_regional_integrity.py
- Kategori: Finans
- Fil: backend/scripts/fix_regional_integrity.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Conservative fix for regional integrity issues.

Strategy:
1. Skip properties with "Unknown" region (can't determine what's wrong)
2. Skip properties where >50% of data is from wrong region (would lose too much)
3. Only remove wrong-region data from properties with <50% wrong data
4. Log all removals for review

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## fix_rent_data.py
- Kategori: Finans
- Fil: backend/scripts/fix_rent_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Fix rent data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## fix_thoroya_final.py
- Kategori: Finans
- Fil: backend/scripts/fix_thoroya_final.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Fix the final Thorøyaveien 1 property usage.

### Bruk
- Fix the final Thorøyaveien 1 property usage.
- print("🔧 Fixing Thorøyaveien 1 Property Usage")
- print(f"  Current Usage: {prop.usage}")
- if prop.usage is None:
- prop.usage = 'Barnevernsinstitusjon'
- print("\n📊 Final Status Check (All Properties with NULL usage):")
- select(Property).where(Property.usage == None)
- print("  🎉 ZERO properties have NULL usage! 100% Complete.")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## generate_historical_financials.py
- Kategori: Finans
- Fil: backend/scripts/generate_historical_financials.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Generate historical financials.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## generate_monthly_financial_timeseries.py
- Kategori: Finans
- Fil: backend/scripts/generate_monthly_financial_timeseries.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Generate synthetic monthly financial time-series dataset for real estate.

This script generates monthly financial data covering the last 3 years,
with realistic seasonality for electricity and inflation-adjusted rent.

Can work with mock data OR fetch all properties from database.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## generate_python_docs.py
- Kategori: Finans
- Fil: scripts/generate_python_docs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
- Eksterne tjenester: OpenAI, Maskinporten, BRREG, LangExtract, Docling/PDF
- Risiko (heuristisk): Middels

### Beskrivelse
Generate expanded Python script documentation into docs/python.md.

Features:
- Scans backend/scripts and scripts/ for .py files
- Extracts top-level docstrings for concise explanations
- Heuristically describes scripts without docstrings
- Detects "used" scripts referenced in *.md and *.sh files
- Appends new sections to docs/python.md without overwriting existing content

Run:
  python3 scripts/generate_python_docs.py

### Bruk
- usage: List[str] = []
- # Usage lines in docstring
- if re.search(r"(Kjør|Usage|Bruk|Run)\b", line, re.IGNORECASE) and ("python" in line or "docker" in line):
- usage.append(line.strip())
- # Fallback: code comments mentioning usage
- usage.append(line.strip())
- # Trim overly long usage list
- usage = usage[:4]
- return usage, envs
- usage, envs = extract_usage_and_env(p, doc, file_text)
- grouped.setdefault(domain, []).append((str(p.relative_to(ROOT)), desc, usage, envs))
- usage, envs = extract_usage_and_env(p, doc, file_text)
- grouped.setdefault(domain, []).append((str(p.relative_to(ROOT)), desc, usage, envs))
- for rel, desc, usage, envs in items:
- dedup.append((rel, desc, usage, envs))
- for rel, desc, usage, envs in sorted(items, key=lambda t: t[0]):
- if usage:
- for u in usage:
- out.append(f"  - Usage: {u}")

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## generate_timeseries_for_all_properties.py
- Kategori: Finans
- Fil: backend/scripts/generate_timeseries_for_all_properties.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Generate monthly financial time-series for ALL properties in database.

This script:
1. Connects to database
2. Loads all properties with their rent and electricity costs
3. Generates 3 years of monthly financial data
4. Exports to CSV files

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## geocode_all_properties.py
- Kategori: Finans
- Fil: backend/scripts/geocode_all_properties.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_NAME
- Eksterne tjenester: HTTP/requests
- Risiko (heuristisk): Middels

### Beskrivelse
Complete geocoding solution for all properties.
Fetches properties from database, geocodes them, and generates SQL updates.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- HTTP-kall uten timeout.
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Legg til timeout=30 (eller passende).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## grandfather_existing_users.py
- Kategori: Finans
- Fil: backend/scripts/grandfather_existing_users.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Script to grandfather existing users: set email_verified=True and mfa_verified_at.
This should be run once after the migration.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## import_and_synthesize.py
- Kategori: Finans
- Fil: backend/scripts/import_and_synthesize.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Import and synthesize.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## import_bufetat_contracts.py
- Kategori: Finans
- Fil: backend/scripts/import_bufetat_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Import Bufetat rental contracts and enrich property data from CSV files.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## import_elements_from_csv.py
- Kategori: Finans
- Fil: backend/scripts/import_elements_from_csv.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Import elements from csv.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## import_elements_from_eiendom.py
- Kategori: Finans
- Fil: backend/scripts/import_elements_from_eiendom.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Import elements from eiendom.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## import_gl_data.py
- Kategori: Finans
- Fil: backend/scripts/import_gl_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Import General Ledger data from ok1.csv into gl_transactions table.
Processes 35,818 accounting transactions.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## import_landlords.py
- Kategori: Finans
- Fil: backend/scripts/import_landlords.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Import landlords.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## import_totalny_selective.py
- Kategori: Finans
- Fil: backend/scripts/import_totalny_selective.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Import totalny selective.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## ingest_data.py
- Kategori: Finans
- Fil: backend/scripts/ingest_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: OPENAI_API_KEY
- Eksterne tjenester: OpenAI, Docling/PDF, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Ingest data.

### Bruk
- usage=data.get('usage'),

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## inspect_filenames.py
- Kategori: Finans
- Fil: backend/scripts/inspect_filenames.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect filenames.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_financial_data.py
- Kategori: Finans
- Fil: backend/scripts/inspect_financial_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect financial data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_full_schema.py
- Kategori: Finans
- Fil: backend/scripts/inspect_full_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect full schema.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_gl_columns.py
- Kategori: Finans
- Fil: backend/scripts/inspect_gl_columns.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect gl columns.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## inspect_outliers.py
- Kategori: Finans
- Fil: backend/scripts/inspect_outliers.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Inspect outliers.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## intelligent_auto_fix.py
- Kategori: Finans
- Fil: backend/scripts/intelligent_auto_fix.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Intelligent auto-fix script for financial data
Implements all fixes identified by advanced analysis

### Bruk
- Args: parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry-run)'); parser.add_argument('--all', action='store_true', help='Enable all fixes'); parser.add_argument('--pairs', action='store_true', help='Fix correction pairs'); parser.add_argument('--scale', action='store_true', help='Fix scale errors'); parser.add_argument('--duplicates', action='store_true', help='Fix duplicates'); parser.add_argument('--outliers', action='store_true', help='Fix outliers')

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## investigate_null_properties.py
- Kategori: Finans
- Fil: backend/scripts/investigate_null_properties.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Find the 3 properties with NULL usage and investigate.

### Bruk
- Find the 3 properties with NULL usage and investigate.
- print("🔍 Investigating Properties with NULL Usage")
- # Find properties with NULL usage
- select(Property).where(Property.usage == None)
- print(f"\nFound {len(null_props)} properties with NULL usage:\n")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## langextract_poc.py
- Kategori: Finans
- Fil: backend/scripts/langextract_poc.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: GOOGLE_GENAI_API_KEY
- Eksterne tjenester: LangExtract, Docling/PDF
- Risiko (heuristisk): Middels

### Beskrivelse
LangExtract + Docling POC
==========================

Demonstrates integration of Docling (PDF text extraction) with LangExtract
(LLM-based structured extraction with source grounding).

This script:
1. Uses Docling to extract text from a PDF
2. Defines extraction schema for lease contracts
3. Uses LangExtract to extract structured entities with source citations
4. Outputs JSON with precise source references
5. Generates interactive HTML visualization

Cost: ~3-5 øre per 30-page document (Gemini Flash)

### Bruk
- Args: parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## mark_all_properties_synthetic.py
- Kategori: Finans
- Fil: backend/scripts/mark_all_properties_synthetic.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Merker alle eiendommer som syntetiske ved å sette external_data.synthetic = True
(og synthetic_note) på hver eiendom. Eksisterende external_data beholdes og slås sammen.

Krever DATABASE_URL. Kjør før ensure_synthetic_contract_and_tenant.py hvis du vil
at alle eiendommer skal få syntetisk kontrakt og leietaker.

### Bruk
- Args: parser.add_argument("--dry-run", action="store_true", help="Vis bare hva som ville blitt gjort")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## match_bufdir_robust.py
- Kategori: Finans
- Fil: backend/scripts/match_bufdir_robust.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Robust matching of Bufdir institutions to properties.
Krever DATABASE_URL (lastes fra .env hvis tilgjengelig). Kjør fra prosjektrot.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## ml_financial_analysis.py
- Kategori: Finans
- Fil: backend/scripts/ml_financial_analysis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
!/usr/bin/env python3

### Bruk
- Args: parser.add_argument("target", nargs="?", help="Navn eller ID på eiendommen (valgfri for mønstre)"); parser.add_argument("--type", choices=["forecast", "anomalies", "patterns", "both"], default="both"); parser.add_argument("--years", type=int, default=3, help="Antall år frem i tid for prognose")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## openai_costs.py
- Kategori: Finans
- Fil: backend/scripts/collectors/openai_costs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: OpenAI, HTTP/requests, Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
OpenAI Cost Collector

Collects usage metrics from database logs (ApiCallLog).

### Bruk
- Collects usage metrics from database logs (ApiCallLog).
- For simplicity, we just aggregate the last 30 days to check total usage trend,
- We should calculate the total usage within the last 24 hours to represent 'daily cost'
- Database collector returns projected monthly cost based on usage.

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## parse_pdf_folder.py
- Kategori: Finans
- Fil: backend/scripts/parse_pdf_folder.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Docling/PDF
- Risiko (heuristisk): Lav

### Beskrivelse
Parser alle PDF-filer i pdf_docs-mappen og lagrer ekstrahert tekst i pdf_docs/extracted/.

Kjør fra backend: python3 scripts/parse_pdf_folder.py
  --ocr          Bruk OCR (Tesseract) på alle PDF-er (for skannede dokumenter).
  --ocr-fallback Bruk OCR bare når PyPDF ikke finner tekst (anbefalt for blandet mappe).

Krever for OCR: tesseract + poppler (macOS: brew install tesseract poppler), og pip: pdf2image pytesseract.

### Bruk
- Args: parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## pattern_analyzer.py
- Kategori: Finans
- Fil: backend/scripts/pattern_analyzer.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Pattern Analysis Extension for Cost Analyzer

Commands:
  python pattern_analyzer.py similar <property_name>  - Find most similar properties
  python pattern_analyzer.py patterns                 - Find common cost patterns
  python pattern_analyzer.py patterns extended        - Extended patterns (regional, supplier, time, etc.)
  python pattern_analyzer.py validate                 - Find outliers and potential errors

### Bruk
- print(f"  {x['usage'][:40]}: {x['property_count']} eiendommer, snitt {x['avg_costs']:,.0f} kr")
- print("Usage: python pattern_analyzer.py similar <property_name>")

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## populate_bup_data.py
- Kategori: Finans
- Fil: backend/scripts/populate_bup_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: BUP_JSON_PATH
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Populate bup data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## populate_hms_data.py
- Kategori: Finans
- Fil: backend/scripts/populate_hms_data.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Populate HMS tables with realistic internal control data
Based on: Leietakers internkontroll veileder

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## quick_stats.py
- Kategori: Finans
- Fil: backend/scripts/quick_stats.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Quick statistics about properties and synthetic data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## refresh_dashboard_metrics.py
- Kategori: Finans
- Fil: backend/scripts/refresh_dashboard_metrics.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Refresh DashboardMetrics table.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## reimport_all_financials.py
- Kategori: Finans
- Fil: backend/scripts/reimport_all_financials.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Reimport all financials.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## reimport_all_financials_v2.py
- Kategori: Finans
- Fil: backend/scripts/reimport_all_financials_v2.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Reimport all financials v2.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## remove_financial_duplicates.py
- Kategori: Finans
- Fil: backend/scripts/remove_financial_duplicates.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Script to find and remove duplicate financial transactions (manual_expenses)
from property external_data

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## remove_synthetic.py
- Kategori: Finans
- Fil: backend/scripts/remove_synthetic.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Remove synthetic.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## reproduce_supplier_data.py
- Kategori: Finans
- Fil: backend/scripts/reproduce_supplier_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_USER
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Reproduce supplier data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## run_seed_users.py
- Kategori: Finans
- Fil: backend/scripts/run_seed_users.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Quick script to seed test users in production database
Reads from .env and executes seed_simple_users.sql

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## scan_terms.py
- Kategori: Finans
- Fil: scripts/scan_terms.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Scan terms.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## search_pdf_extracts.py
- Kategori: Finans
- Fil: backend/scripts/search_pdf_extracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Søk i ekstrahert tekst fra pdf_docs/extracted/ (etter at parse_pdf_folder.py er kjørt).

Kjør fra backend: python scripts/search_pdf_extracts.py "søkeord"

### Bruk
- print("Bruk: python scripts/search_pdf_extracts.py \"søkeord\"")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_db.py
- Kategori: Finans
- Fil: backend/scripts/seed_db.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Seed db.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## seed_evolution_test.py
- Kategori: Finans
- Fil: backend/scripts/seed_evolution_test.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Seed evolution test.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## seed_ns3451.py
- Kategori: Finans
- Fil: backend/scripts/seed_ns3451.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed ns3451.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_property_users.py
- Kategori: Finans
- Fil: backend/scripts/seed_property_users.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed property users.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_users_orm.py
- Kategori: Finans
- Fil: backend/scripts/seed_users_orm.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Seed test users directly via SQLAlchemy ORM

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## set_user_passwords.py
- Kategori: Finans
- Fil: backend/scripts/set_user_passwords.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Set passwords for all users in the database
Default password: test123

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## setup_memory.py
- Kategori: Finans
- Fil: backend/scripts/setup_memory.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: OpenAI, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Setup memory.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## show_all_properties_contracts.py
- Kategori: Finans
- Fil: backend/scripts/show_all_properties_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Show all properties and their associated contracts.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## show_database_schema.py
- Kategori: Finans
- Fil: backend/scripts/show_database_schema.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Show complete database schema with all tables and fields

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## sjekk_utgifter_eiendommer.py
- Kategori: Finans
- Fil: backend/scripts/sjekk_utgifter_eiendommer.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Sjekk løpende utgifter per eiendom
=================================
Finner eiendommer som mangler utgifter (0 poster) og eiendommer med uvanlig mange poster.
Kjør fra backend: python scripts/sjekk_utgifter_eiendommer.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## sjekk_utgiftsduplikater.py
- Kategori: Finans
- Fil: backend/scripts/sjekk_utgiftsduplikater.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Sjekk duplikater i løpende utgifter (manual_expenses) per eiendom
=================================================================
Rapport-only: finner mulige duplikater (samme type, beløp, leverandør, dato).
Endrer ikke databasen. For å fjerne duplikater, kjør: remove_financial_duplicates.py

Kjør fra backend: python3 scripts/sjekk_utgiftsduplikater.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## start_local_sandbox.py
- Kategori: Finans
- Fil: backend/scripts/start_local_sandbox.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Start local sandbox.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_db_connection.py
- Kategori: Finans
- Fil: backend/scripts/test_db_connection.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test database connection

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_financial_analysis.py
- Kategori: Finans
- Fil: backend/scripts/test_financial_analysis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_SERVER, POSTGRES_USER
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test financial analysis.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_gl_insert.py
- Kategori: Finans
- Fil: backend/scripts/test_gl_insert.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test script to verify GL transaction insertion works.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_memory_persona.py
- Kategori: Finans
- Fil: backend/scripts/test_memory_persona.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Test memory persona.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_rbac.py
- Kategori: Finans
- Fil: backend/scripts/test_rbac.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Quick RBAC test script.

Kjører grunnleggende tester for å verifisere at RBAC implementeringen fungerer.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_timeseries.py
- Kategori: Finans
- Fil: backend/scripts/test_timeseries.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Quick test of the timeseries generator

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## update_bufdir_enrichment.py
- Kategori: Finans
- Fil: backend/scripts/update_bufdir_enrichment.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Update bufdir enrichment.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## update_expired_contracts.py
- Kategori: Finans
- Fil: backend/scripts/update_expired_contracts.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Update expired contracts to 'terminated' status.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## update_from_csv.py
- Kategori: Finans
- Fil: backend/scripts/update_from_csv.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Database Update Script - Enrich Matched Contracts with CSV Metadata

Updates the 9 matched contracts found by compare_csv_portfolio.py with enriching
metadata from the CSV master table.

Updates include:
- external_data fields: region, filename, category, parking, facilities
- property gnr/bnr (cadastral numbers)
- contract status (only if CSV is more recent/accurate)

Usage:
    python3 scripts/update_from_csv.py [--dry-run]

### Bruk
- Usage:

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## update_from_csv_sql.py
- Kategori: Finans
- Fil: backend/scripts/update_from_csv_sql.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Database Update Script (Raw SQL) - Enrich Matched Contracts with CSV Metadata

Uses raw SQL to bypass ORM validation issues with contract status enum.
Directly updates external_data JSONB fields and property cadastral numbers.

Usage:
    python3 scripts/update_from_csv_sql.py [--dry-run]

### Bruk
- Usage:

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## update_property_names.py
- Kategori: Finans
- Fil: backend/scripts/update_property_names.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Update property names from CSV Avtalenavn field.

### Bruk
- # Avoid overwriting if usage suggests it might not be relevant, but user wants everything cleaned

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## update_property_usage.py
- Kategori: Finans
- Fil: backend/scripts/update_property_usage.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: CSV_PATH
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Update property usage types from CSV Type lokasjon field.

### Bruk
- Update property usage types from CSV Type lokasjon field.
- # Mapping from CSV Type lokasjon to database usage
- print("🏢 Updating Property Usage Types")
- # Update usage
- old_usage = matched_prop.usage
- matched_prop.usage = new_usage
- print(f"\n📊 Final usage distribution:")
- usage = p.usage or "NULL"
- usage_counts[usage] = usage_counts.get(usage, 0) + 1
- for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
- print(f"  {usage}: {count}")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## update_regions_from_excel.py
- Kategori: Finans
- Fil: backend/scripts/update_regions_from_excel.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Update 4 property regions from Einovember.xls

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## update_remaining_nulls.py
- Kategori: Finans
- Fil: backend/scripts/update_remaining_nulls.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Manually update the 3 remaining NULL properties based on CSV findings.

### Bruk
- old_usage = prop.usage
- prop.usage = usage_type
- print(f"\n📊 Final usage distribution:")
- usage = p.usage or "NULL"
- usage_counts[usage] = usage_counts.get(usage, 0) + 1
- for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
- print(f"  {usage}: {count}")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_accounting.py
- Kategori: Finans
- Fil: backend/scripts/verify_accounting.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify accounting.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_admin.py
- Kategori: Finans
- Fil: backend/scripts/verify_admin.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL, RAW_DB_URL
- Eksterne tjenester: Kartverket/Geonorge, Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
!/usr/bin/env python3

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_ai_semantic.py
- Kategori: Finans
- Fil: backend/scripts/verify_ai_semantic.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Høy

### Beskrivelse
Verify ai semantic.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Potensiell SQL-injection (f-string/format i execute/text).
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Bruk parameterisering (psycopg2 %s/params eller SQLAlchemy bindparam).
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## verify_cleanup.py
- Kategori: Finans
- Fil: backend/scripts/verify_cleanup.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Quick verification script to count transactions after cleanup

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_enrichment.py
- Kategori: Finans
- Fil: backend/scripts/verify_enrichment.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify property enrichment with Bufdir data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_gl_transactions.py
- Kategori: Finans
- Fil: backend/scripts/verify_gl_transactions.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify that GL transactions have been generated correctly for all properties.

This script checks:
1. All properties have GL transactions
2. Correct number of transactions per property
3. Data covers multiple calendar years
4. Transaction structure is correct
5. Date ranges are correct

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_historical_data.py
- Kategori: Finans
- Fil: backend/scripts/verify_historical_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify historical data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_import_details.py
- Kategori: Finans
- Fil: backend/scripts/verify_import_details.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify import details.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_maskinporten.py
- Kategori: Finans
- Fil: backend/scripts/verify_maskinporten.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: RRH_MASKINPORTEN_KEY_PATH
- Eksterne tjenester: Maskinporten
- Risiko (heuristisk): Lav

### Beskrivelse
Verify maskinporten.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_property_financials.py
- Kategori: Finans
- Fil: backend/scripts/verify_property_financials.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify property financials.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_script_executor.py
- Kategori: Finans
- Fil: backend/scripts/verify_script_executor.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify the run_analysis_script MCP tool works correctly.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_semantic_data.py
- Kategori: Finans
- Fil: backend/scripts/verify_semantic_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify semantic data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_stored_data.py
- Kategori: Finans
- Fil: backend/scripts/verify_stored_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify stored data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_years_coverage.py
- Kategori: Finans
- Fil: backend/scripts/verify_years_coverage.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify that synthetic data covers multiple calendar years.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

# HMS

## add_risk_status_column.py
- Kategori: HMS
- Fil: backend/scripts/add_risk_status_column.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Add missing status column to risk_assessments.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## ai_demo_runner.py
- Kategori: HMS
- Fil: backend/scripts/ai_demo_runner.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: API_URL
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Ai demo runner.

### Bruk
- if result.get("usage"):
- print(f"\n(Usage: {result['usage'].get('total_tokens')} tokens)")

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

## check_risk_api.py
- Kategori: HMS
- Fil: backend/scripts/check_risk_api.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Check risk api.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## create_checklist_tables.py
- Kategori: HMS
- Fil: backend/scripts/create_checklist_tables.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Create checklist tables.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## export_overview_md.py
- Kategori: HMS
- Fil: backend/scripts/export_overview_md.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Export overview md.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## geocode_missing_properties.py
- Kategori: HMS
- Fil: backend/scripts/geocode_missing_properties.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: HTTP/requests, Kartverket/Geonorge, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Geocode properties missing coordinates using Kartverket/Geonorge API.

This script:
1. Fetches all properties without coordinates
2. Geocodes each address using KartverketClient
3. Updates latitude, longitude, and PostGIS geometry
4. Extracts postal codes from addresses
5. Handles rate limiting and errors gracefully

### Bruk
- Args: parser.add_argument(; parser.add_argument(; parser.add_argument(; parser.add_argument(

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## import_oslo.py
- Kategori: HMS
- Fil: backend/scripts/import_oslo.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Kartverket/Geonorge, NVE, Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Import oslo.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## index_docs.py
- Kategori: HMS
- Fil: backend/scripts/index_docs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Index docs.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## regenerate_natural_deviations.py
- Kategori: HMS
- Fil: backend/scripts/regenerate_natural_deviations.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Regenerate natural deviations (internal control cases) after synthetic data cleanup.

This script:
1) Verifies that synthetic properties/cases are gone (or reports how many remain)
2) Generates actionable, "natural" deviations that can be followed:
   - Missing coordinates on properties
   - Overdue scheduled activities
   - Missing risk assessments

Features:
- Dry-run mode (default) to preview changes
- De-duplication: avoids creating duplicate open cases with same title per property

Usage:
  python3 backend/scripts/regenerate_natural_deviations.py --dry-run
  python3 backend/scripts/regenerate_natural_deviations.py --apply

### Bruk
- Usage:
- Args: parser.add_argument("--dry-run", action="store_true", help="Preview without committing changes"); parser.add_argument("--apply", action="store_true", help="Apply changes (commit to DB)")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## run_cron_jobs.py
- Kategori: HMS
- Fil: backend/scripts/run_cron_jobs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Run cron jobs for internkontroll.
Process due activities and overdue case follow-up.
Kjør f.eks. daglig via cron: cd backend && python scripts/run_cron_jobs.py

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_activity_templates.py
- Kategori: HMS
- Fil: backend/scripts/seed_activity_templates.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed activity_templates from ActivityGenerator.DEFAULT_TEMPLATES.
Kjør for å fylle hub med system-maler.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_checklists.py
- Kategori: HMS
- Fil: backend/scripts/seed_checklists.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Seed checklists.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## seed_data.py
- Kategori: HMS
- Fil: backend/scripts/seed_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_deviations_variation.py
- Kategori: HMS
- Fil: backend/scripts/seed_deviations_variation.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed deviations variation.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_internal_control.py
- Kategori: HMS
- Fil: backend/scripts/seed_internal_control.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Seed internal control cases for all properties.
Uses InternalControlService.create_initial_cases_for_property.
Skips properties that already have cases (from templates).

### Bruk
- Args: parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## seed_persona.py
- Kategori: HMS
- Fil: backend/scripts/seed_persona.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Seed persona.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_hybrid_search.py
- Kategori: HMS
- Fil: backend/scripts/test_hybrid_search.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Test hybrid search.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## test_qa_bench.py
- Kategori: HMS
- Fil: backend/scripts/test_qa_bench.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Test qa bench.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_checklists.py
- Kategori: HMS
- Fil: backend/scripts/verify_checklists.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify checklists.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_data.py
- Kategori: HMS
- Fil: backend/scripts/verify_data.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: POSTGRES_DB, POSTGRES_SERVER
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Lav

### Beskrivelse
Verify data.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_templates.py
- Kategori: HMS
- Fil: backend/scripts/verify_templates.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify templates.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

# PDF

## test_insert.py
- Kategori: PDF
- Fil: backend/scripts/test_insert.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Docling/PDF, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
Test single document migration to see full error.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## vercel_costs.py
- Kategori: PDF
- Fil: backend/scripts/collectors/vercel_costs.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Ingen
- Risiko (heuristisk): Middels

### Beskrivelse
Vercel Cost Collector

Collects usage metrics from Vercel using vercel CLI.

### Bruk
- Collects usage metrics from Vercel using vercel CLI.
- # Additional usage costs (Pro tier)
- usage metrics via CLI, we'll assume hobby tier with $0 cost.
- "note": "CLI provides limited metrics. Consider using Vercel API for detailed usage data."

### Sårbarheter og svakheter
- Bred unntaksfanging (except/except Exception).

### Foreslåtte tiltak
- Fang spesifikke unntak; logg og håndter eksplisitt.

---

# Proximity

## check_external_apis.py
- Kategori: Proximity
- Fil: backend/scripts/check_external_apis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Kartverket/Geonorge, NVE
- Risiko (heuristisk): Lav

### Beskrivelse
Check external apis.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## geocode_batch.py
- Kategori: Proximity
- Fil: backend/scripts/geocode_batch.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: HTTP/requests
- Risiko (heuristisk): Middels

### Beskrivelse
Batch geocode properties using Nominatim and generate SQL UPDATE statements.
Processes properties in chunks to allow for progress monitoring.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- HTTP-kall uten timeout.
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Legg til timeout=30 (eller passende).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## geocode_direct.py
- Kategori: Proximity
- Fil: backend/scripts/geocode_direct.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: HTTP/requests, Postgres/SQL
- Risiko (heuristisk): Middels

### Beskrivelse
!/usr/bin/env python3

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- HTTP-kall uten timeout.
- Bred unntaksfanging (except/except Exception).
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Legg til timeout=30 (eller passende).
- Fang spesifikke unntak; logg og håndter eksplisitt.
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## geocode_sample.py
- Kategori: Proximity
- Fil: backend/scripts/geocode_sample.py
- Sikkerhet: Endrer data (skriv/sideeffekter)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: HTTP/requests
- Risiko (heuristisk): Middels

### Beskrivelse
Simple geocoding script - outputs SQL UPDATE statements.
Run this script, wait for completion, then execute the SQL via MCP.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- HTTP-kall uten timeout.
- Skript utfører skrivende operasjoner (DB/fil).

### Foreslåtte tiltak
- Legg til timeout=30 (eller passende).
- Kjør med --dry-run og transaksjoner; audit-logger endringer.

---

## refresh_proximity_batch.py
- Kategori: Proximity
- Fil: scripts/refresh_proximity_batch.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: DATABASE_URL
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Refresh proximity batch.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## verify_postgis.py
- Kategori: Proximity
- Fil: backend/scripts/verify_postgis.py
- Sikkerhet: Safe (lese/analyse)
- Miljøvariabler: Ingen spesifikke
- Eksterne tjenester: Postgres/SQL
- Risiko (heuristisk): Lav

### Beskrivelse
Verify postgis.

### Bruk
- (ingen eksplisitt usage funnet)

### Sårbarheter og svakheter
- Ingen evidente risikofunn (heuristisk).

### Foreslåtte tiltak
- Ingen.

---

## Miljøvariabler (referanse)


## Domenegjennomgang (Finans, HMS, PDF, Bufdir, Proximity)


## Brukte Skript (Oppdaget via dokumentasjon)

- [backend/scripts/approve_tool.py](backend/scripts/approve_tool.py): Script: approve tool
- [backend/scripts/audit_financial_outliers.py](backend/scripts/audit_financial_outliers.py): Comprehensive audit to find financial data outliers and suspicious values
- [backend/scripts/berik_navn_familievernkontor.py](backend/scripts/berik_navn_familievernkontor.py): Berik eiendommer med navn fra familievernkontor-mapping (Bufdir.no).
- [backend/scripts/berik_navn_fra_oversikt_bygg.py](backend/scripts/berik_navn_fra_oversikt_bygg.py): Berik eiendommer som kun har adresse som navn, med navn fra «Oversikt bygg og eiendom» CSV.
- [backend/scripts/budget_2026_kategori.py](backend/scripts/budget_2026_kategori.py): Budsjett 2026 – kategori-basert estimering fra GL 2025.
- [backend/scripts/compare_csv_portfolio.py](backend/scripts/compare_csv_portfolio.py): CSV Portfolio Data Comparison Script
- [backend/scripts/count_core_data.py](backend/scripts/count_core_data.py): Viser antall eiendommer, enheter, kontrakter og partier (leietakere/utleiere) i databasen.
- [backend/scripts/create_admin_users.py](backend/scripts/create_admin_users.py): Script to create 5 admin users with secure passwords.
- [backend/scripts/deep_cost_analysis.py](backend/scripts/deep_cost_analysis.py): Deep cost analysis to identify additional data quality issues
- [backend/scripts/fetch_images_for_barnevern.py](backend/scripts/fetch_images_for_barnevern.py): Søker på nettet etter bilder for barnevernsinstitusjoner som mangler bilde.
- [backend/scripts/fill_budget_from_consumption.py](backend/scripts/fill_budget_from_consumption.py): Fyll budsjett-tabellen fra forbruk (manual_expenses) for 2024–2026 med ±variance per kategori.
- [backend/scripts/finn_og_fyll_leie_vedlikehold.py](backend/scripts/finn_og_fyll_leie_vedlikehold.py): Finn eiendommer som mangler Leie (YTD) eller Vedlikehold, og fyll med syntetisk data.
- [backend/scripts/fix_empty_status.py](backend/scripts/fix_empty_status.py): Fix Invalid Contract Status Values
- [backend/scripts/fix_fellesbyg_property_mismatch.py](backend/scripts/fix_fellesbyg_property_mismatch.py): Nullstill property_id på gl_transactions som ble feilaktig matchet til fellesbyg via adresse (Dim2).
- [backend/scripts/fix_negative_amounts.py](backend/scripts/fix_negative_amounts.py): Fix negative amounts that are clearly import errors while preserving legitimate credits.
- [scripts/generate_python_docs.py](scripts/generate_python_docs.py): Generate expanded Python script documentation into docs/python.md.
- [backend/scripts/grandfather_existing_users.py](backend/scripts/grandfather_existing_users.py): Script to grandfather existing users: set email_verified=True and mfa_verified_at.
- [backend/scripts/import_oversikt_bygg_eiendom_csv.py](backend/scripts/import_oversikt_bygg_eiendom_csv.py): Import fra «Oversikt bygg og eiendom - GK og Budsjetterte» eller «Eiendomsportefølje- Bufdir» CSV til BEFS.
- [backend/scripts/langextract_poc.py](backend/scripts/langextract_poc.py): LangExtract + Docling POC
- [backend/scripts/legg_til_eiendomsbilde.py](backend/scripts/legg_til_eiendomsbilde.py): Legg til eiendomsbilde for eiendommer som mangler.
- [backend/scripts/migrer_og_import_edon2_avdeling.py](backend/scripts/migrer_og_import_edon2_avdeling.py): Kjør migrering for unit_short_type/unit_type_derived, deretter e-don2-import
- [backend/scripts/oppdater_parent_erp_fra_birk_csv.py](backend/scripts/oppdater_parent_erp_fra_birk_csv.py): Oppdater properties.parent_unit_id_erp (og evt. unit_short_type, region) fra
- [backend/scripts/parse_pdf_folder.py](backend/scripts/parse_pdf_folder.py): Parser alle PDF-filer i pdf_docs-mappen og lagrer ekstrahert tekst i pdf_docs/extracted/.
- [backend/scripts/rapport_innkjøpsanalyse_husleie.py](backend/scripts/rapport_innkjøpsanalyse_husleie.py): Rapport: Eiendommer og avdelinger med husleie fra Innkjøpsanalyse.
- [scripts/refresh_proximity_batch.py](scripts/refresh_proximity_batch.py): Script for å batch-oppdatere nærliggende tjenester for alle eiendommer
- [backend/scripts/reimport_all_financials_v2.py](backend/scripts/reimport_all_financials_v2.py): Normalize property name for better matching.
- [backend/scripts/remove_financial_duplicates.py](backend/scripts/remove_financial_duplicates.py): Script to find and remove duplicate financial transactions (manual_expenses)
- [backend/scripts/run_cron_jobs.py](backend/scripts/run_cron_jobs.py): Run cron jobs for internkontroll.
- [backend/scripts/run_openai_query.py](backend/scripts/run_openai_query.py): Kjør én enkel OpenAI-spørring for å verifisere at OPENAI_API_KEY og oppsett fungerer.
- [backend/scripts/search_pdf_extracts.py](backend/scripts/search_pdf_extracts.py): Søk i ekstrahert tekst fra pdf_docs/extracted/ (etter at parse_pdf_folder.py er kjørt).
- [backend/scripts/seed_query_library_storste_lav_husleie.py](backend/scripts/seed_query_library_storste_lav_husleie.py): Seed query_library med «største eiendommer med lav husleie».
- [backend/scripts/sjekk_naeringseiendom_matching.py](backend/scripts/sjekk_naeringseiendom_matching.py): Sjekk om eiendommer med type næringseiendom (eller som vises som det) er matchet
- [backend/scripts/sjekk_utgifter_eiendommer.py](backend/scripts/sjekk_utgifter_eiendommer.py): Sjekk løpende utgifter per eiendom
- [backend/scripts/sjekk_utgiftsduplikater.py](backend/scripts/sjekk_utgiftsduplikater.py): Sjekk duplikater i løpende utgifter (manual_expenses) per eiendom
- [backend/scripts/slaa_opp_manglende_parent_brreg.py](backend/scripts/slaa_opp_manglende_parent_brreg.py): Slår opp manglende forelder (parent) for eiendommer via Brønnøysund Enhetsregisteret.
- [backend/scripts/test_brreg_connectivity.py](backend/scripts/test_brreg_connectivity.py): Test BRREG (Brønnøysundregistrene) connectivity.
- [backend/scripts/test_rbac.py](backend/scripts/test_rbac.py): Quick RBAC test script.
- [backend/scripts/update_from_csv.py](backend/scripts/update_from_csv.py): Database Update Script - Enrich Matched Contracts with CSV Metadata
- [backend/scripts/update_from_csv_sql.py](backend/scripts/update_from_csv_sql.py): Database Update Script (Raw SQL) - Enrich Matched Contracts with CSV Metadata

### Finans

- [backend/scripts/add_contract_category.py](backend/scripts/add_contract_category.py): Script: add contract category
- [backend/scripts/advanced_financial_analysis.py](backend/scripts/advanced_financial_analysis.py): Advanced financial data analysis with pattern recognition and intelligent auto-fix suggestions
  - Env: DATABASE_URL
- [backend/scripts/analyze_contract_fields_v2.py](backend/scripts/analyze_contract_fields_v2.py): Script: analyze contract fields v2
  - Env: DATABASE_URL
- [backend/scripts/analyze_contract_types.py](backend/scripts/analyze_contract_types.py): Script: analyze contract types
  - Env: DATABASE_URL
- [backend/scripts/analyze_contracts.py](backend/scripts/analyze_contracts.py): Script: analyze contracts
  - Env: DATABASE_URL
- [backend/scripts/analyze_negative_amounts.py](backend/scripts/analyze_negative_amounts.py): Analyze negative amounts in financial transactions to identify:
  - Env: DATABASE_URL
- [backend/scripts/analyze_price_per_sqm.py](backend/scripts/analyze_price_per_sqm.py): Analyze contract data to calculate average price per square meter for rent estimation.
  - Env: DATABASE_URL
- [backend/scripts/analyze_rent_discrepancy.py](backend/scripts/analyze_rent_discrepancy.py): Script: analyze rent discrepancy
  - Env: DATABASE_URL
- [backend/scripts/audit_contracts.py](backend/scripts/audit_contracts.py): Comprehensive contract data audit
  - Env: DATABASE_URL
- [backend/scripts/audit_data_quality.py](backend/scripts/audit_data_quality.py): Revisjon/avdekking: audit data quality
  - Env: DATABASE_URL
- [backend/scripts/audit_expense_details.py](backend/scripts/audit_expense_details.py): Deep-dive audit to analyze expense patterns and detect duplicates
  - Env: DATABASE_URL
- [backend/scripts/audit_financial_outliers.py](backend/scripts/audit_financial_outliers.py): Comprehensive audit to find financial data outliers and suspicious values
  - Env: DATABASE_URL
- [backend/scripts/audit_gl_properties_2020_2025.py](backend/scripts/audit_gl_properties_2020_2025.py): Revisjon av gl_transactions 2020–2025:
  - Env: DATABASE_URL
- [backend/scripts/audit_incomplete_properties.py](backend/scripts/audit_incomplete_properties.py): Audit script to identify properties with missing or incomplete data
  - Env: DATABASE_URL
- [backend/scripts/audit_missing_financial_data.py](backend/scripts/audit_missing_financial_data.py): Comprehensive audit to find properties missing financial data
  - Env: DATABASE_URL
- [backend/scripts/avstem_husleie_mot_csv_2025.py](backend/scripts/avstem_husleie_mot_csv_2025.py): Avstemning: BEFS faktisk husleie (GL) mot Innkjøpsanalyse-CSV 2025.
  - Env: DATABASE_URL
- [backend/scripts/backfill_gl_name_match.py](backend/scripts/backfill_gl_name_match.py): Find and backfill GL rows for properties that match unmapped cost centers by name.
  - Usage: Run: railway run --service striking-insight python3 scripts/backfill_gl_name_match.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/berik_navn_fra_oversikt_bygg.py](backend/scripts/berik_navn_fra_oversikt_bygg.py): Berik eiendommer som kun har adresse som navn, med navn fra «Oversikt bygg og eiendom» CSV.
  - Usage: Kjør: cd backend && railway run python3 scripts/berik_navn_fra_oversikt_bygg.py [--csv PATH] [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/budget_2026_kategori.py](backend/scripts/budget_2026_kategori.py): Budsjett 2026 – kategori-basert estimering fra GL 2025.
  - Usage: python3 scripts/budget_2026_kategori.py --dry-run
  - Usage: python3 scripts/budget_2026_kategori.py
  - Env: DATABASE_URL
- [backend/scripts/calculate_total_rent.py](backend/scripts/calculate_total_rent.py): Script: calculate total rent
  - Env: DATABASE_URL
- [backend/scripts/check_contract_count.py](backend/scripts/check_contract_count.py): Quick database contract count check
  - Env: DATABASE_URL
- [backend/scripts/check_db_rent.py](backend/scripts/check_db_rent.py): Sjekk/kontroll: check db rent
  - Env: DATABASE_URL
- [backend/scripts/check_properties_without_costs.py](backend/scripts/check_properties_without_costs.py): Check properties without cost data (contracts).
  - Env: DATABASE_URL
- [backend/scripts/check_synthetic_data_coverage.py](backend/scripts/check_synthetic_data_coverage.py): Check which properties have synthetic monthly financial data.
  - Env: DATABASE_URL
- [backend/scripts/cleanup_bad_amounts.py](backend/scripts/cleanup_bad_amounts.py): Clean up contracts with corrupted amounts (> 50M NOK threshold).
  - Env: DATABASE_URL
- [backend/scripts/compare_csv_portfolio.py](backend/scripts/compare_csv_portfolio.py): CSV Portfolio Data Comparison Script
  - Usage: python3 scripts/compare_csv_portfolio.py [--validate-only]
  - Env: DATABASE_URL
- [backend/scripts/comprehensive_rent_fix.py](backend/scripts/comprehensive_rent_fix.py): Comprehensive script to fix ALL rent data issues:
  - Env: DATABASE_URL
- [backend/scripts/cost_analyzer.py](backend/scripts/cost_analyzer.py): EXPERT PROPERTY COST ANALYZER
  - Env: DATABASE_URL
- [backend/scripts/cost_monitor.py](backend/scripts/cost_monitor.py): Cost Monitor - Main Orchestration Script
  - Env: DATABASE_URL, OPENAI_API_KEY
- [backend/scripts/count_contracts.py](backend/scripts/count_contracts.py): Script: count contracts
  - Env: DATABASE_URL
- [backend/scripts/create_missing_properties.py](backend/scripts/create_missing_properties.py): Create stub property records for GL cost centers that exist in Agresso
  - Usage: Run: railway run --service striking-insight python3 scripts/create_missing_properties.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/debug_rent_issue.py](backend/scripts/debug_rent_issue.py): Script: debug rent issue
  - Env: DATABASE_URL
- [backend/scripts/deep_cost_analysis.py](backend/scripts/deep_cost_analysis.py): Deep cost analysis to identify additional data quality issues
  - Env: DATABASE_URL
- [backend/scripts/diagnose_contract.py](backend/scripts/diagnose_contract.py): Script: diagnose contract
  - Env: DATABASE_URL
- [backend/scripts/ensure_synthetic_contract_and_tenant.py](backend/scripts/ensure_synthetic_contract_and_tenant.py): Sikrer at alle syntetiske eiendommer har minst én syntetisk kontrakt og tilknyttet leietaker.
  - Env: DATABASE_URL
- [backend/scripts/estimate_budget_2026.py](backend/scripts/estimate_budget_2026.py): Estimer budsjett for 2026 basert på Innkjøpsanalyse (property_husleie_csv).
  - Usage: python3 scripts/estimate_budget_2026.py
  - Usage: python3 scripts/estimate_budget_2026.py --dry-run
  - Usage: python3 scripts/estimate_budget_2026.py --source gl   # Bruk GL i stedet
  - Usage: railway run python3 scripts/estimate_budget_2026.py --dry-run
  - Env: DATABASE_URL
- [backend/scripts/export_financial_table.py](backend/scripts/export_financial_table.py): Export complete financial data table for all properties
  - Env: DATABASE_URL
- [backend/scripts/export_properties_contracts.py](backend/scripts/export_properties_contracts.py): Export all properties and contracts to CSV for easy viewing.
  - Env: DATABASE_URL
- [backend/scripts/familievern_details.py](backend/scripts/familievern_details.py): Get detailed information about familievern contracts
  - Env: DATABASE_URL
- [backend/scripts/fill_budget_from_consumption.py](backend/scripts/fill_budget_from_consumption.py): Fyll budsjett-tabellen fra forbruk (manual_expenses) for 2024–2026 med ±variance per kategori.
  - Usage: python3 scripts/fill_budget_from_consumption.py
  - Usage: python3 scripts/fill_budget_from_consumption.py --years 2024,2025,2026
  - Usage: python3 scripts/fill_budget_from_consumption.py --variance 0.15
  - Usage: python3 scripts/fill_budget_from_consumption.py --property-ids <uuid1>,<uuid2>
  - Env: DATABASE_URL
- [backend/scripts/fill_missing_rents.py](backend/scripts/fill_missing_rents.py): Fill missing rent values using median price per square meter.
  - Env: DATABASE_URL
- [backend/scripts/fill_remaining_zero_rents.py](backend/scripts/fill_remaining_zero_rents.py): Investigate and fill the 24 remaining properties with 0 rent.
  - Env: DATABASE_URL
- [backend/scripts/find_familievern.py](backend/scripts/find_familievern.py): Find all familievern (family counseling) contracts
  - Env: DATABASE_URL
- [backend/scripts/find_zero_rent.py](backend/scripts/find_zero_rent.py): Script: find zero rent
- [backend/scripts/fix_empty_status.py](backend/scripts/fix_empty_status.py): Fix Invalid Contract Status Values
  - Usage: python3 scripts/fix_empty_status.py
  - Usage: print("  python3 scripts/update_from_csv_sql.py")
  - Env: DATABASE_URL
- [backend/scripts/fix_familievern_duplicate.py](backend/scripts/fix_familievern_duplicate.py): Fix duplicate familievern contracts
  - Env: DATABASE_URL
- [backend/scripts/fix_financial_discrepancies.py](backend/scripts/fix_financial_discrepancies.py): Fix financial data discrepancies with multiple repair strategies
  - Env: DATABASE_URL
- [backend/scripts/fix_financial_mixup.py](backend/scripts/fix_financial_mixup.py): Script: fix financial mixup
  - Env: DATABASE_URL
- [backend/scripts/fix_parent_erp_from_budget_csv.py](backend/scripts/fix_parent_erp_from_budget_csv.py): fix_parent_erp_from_budget_csv.py
- [backend/scripts/fix_rent_data.py](backend/scripts/fix_rent_data.py): Script: fix rent data
  - Env: DATABASE_URL
- [backend/scripts/generate_historical_financials.py](backend/scripts/generate_historical_financials.py): Script: generate historical financials
  - Env: DATABASE_URL
- [backend/scripts/generate_master_audit.py](backend/scripts/generate_master_audit.py): Generates address_match_audit.csv (BIRK vs Address Catalog)
- [backend/scripts/generate_monthly_financial_timeseries.py](backend/scripts/generate_monthly_financial_timeseries.py): Generate synthetic monthly financial time-series dataset for real estate.
  - Env: DATABASE_URL
- [backend/scripts/generate_timeseries_for_all_properties.py](backend/scripts/generate_timeseries_for_all_properties.py): Generate monthly financial time-series for ALL properties in database.
  - Env: DATABASE_URL
- [backend/scripts/import_bufetat_contracts.py](backend/scripts/import_bufetat_contracts.py): Import Bufetat rental contracts and enrich property data from CSV files.
  - Env: DATABASE_URL
- [backend/scripts/import_costs_birk_477.py](backend/scripts/import_costs_birk_477.py): Kobler de 477 birk-enhetene (Barnevernsinstitusjon + Avdeling) til kostnadsdata
- [backend/scripts/import_edon2_csv.py](backend/scripts/import_edon2_csv.py): Import fra e-don2/BIRK CSV til BEFS.
  - Env: DATABASE_URL
- [backend/scripts/import_elements_from_csv.py](backend/scripts/import_elements_from_csv.py): Importer/berik: import elements from csv
  - Env: DATABASE_URL
- [backend/scripts/import_financial_data.py](backend/scripts/import_financial_data.py): Fetch all properties to map names to IDs.
  - Env: DATABASE_URL
- [backend/scripts/import_financials_2025.py](backend/scripts/import_financials_2025.py): Importer/berik: import financials 2025
  - Env: DATABASE_URL
- [backend/scripts/import_financials_2025_rest.py](backend/scripts/import_financials_2025_rest.py): Import 2025 annual cost data via Supabase REST API (no direct DB connection needed).
- [backend/scripts/import_gl_agresso.py](backend/scripts/import_gl_agresso.py): Import Agresso GL-data (Eiendomfebruar.csv) → gl_transactions-tabell.
  - Usage: python scripts/import_gl_agresso.py [--dry-run] [--limit 1000]
  - Env: DATABASE_URL
- [backend/scripts/import_gl_data.py](backend/scripts/import_gl_data.py): Import General Ledger data from ok1.csv into gl_transactions table.
  - Env: DATABASE_URL
- [backend/scripts/import_innkjøpsanalyse_husleie.py](backend/scripts/import_innkjøpsanalyse_husleie.py): Import Innkjøpsanalyse-CSV Total kost til property_husleie_csv.
  - Env: DATABASE_URL
- [backend/scripts/import_institusjoner_csv.py](backend/scripts/import_institusjoner_csv.py): Import fra Institusjons-CSV (barnevernsinstitusjoner med plasser) til BEFS.
  - Env: DATABASE_URL
- [backend/scripts/import_koststed_mapping.py](backend/scripts/import_koststed_mapping.py): Import koststed_eiendom_mapping.csv → koststed_mapping-tabell i Supabase.
  - Usage: python scripts/import_koststed_mapping.py
  - Env: DATABASE_URL
- [backend/scripts/import_oversikt_bygg_eiendom_csv.py](backend/scripts/import_oversikt_bygg_eiendom_csv.py): Import fra «Oversikt bygg og eiendom - GK og Budsjetterte» eller «Eiendomsportefølje- Bufdir» CSV til BEFS.
  - Usage: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/import_oversikt_bygg_eiendom_csv.py [--csv PATH] [--dry-run]
  - Usage: DATABASE_URL=... python3 scripts/import_oversikt_bygg_eiendom_csv.py --use-db [--csv PATH] [--dry-run] [--report]
  - Env: DATABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_SERVICE_ROLE_KEY
- [backend/scripts/inspect_contracts.py](backend/scripts/inspect_contracts.py): Inspiserer/viser detaljer: inspect contracts
  - Env: DATABASE_URL
- [backend/scripts/inspect_financial_data.py](backend/scripts/inspect_financial_data.py): Inspiserer/viser detaljer: inspect financial data
  - Env: DATABASE_URL
- [backend/scripts/intelligent_auto_fix.py](backend/scripts/intelligent_auto_fix.py): Intelligent auto-fix script for financial data
  - Env: DATABASE_URL
- [backend/scripts/ml_financial_analysis.py](backend/scripts/ml_financial_analysis.py): Script: ml financial analysis
  - Env: DATABASE_URL
- [backend/scripts/oppdater_parent_erp_fra_birk_csv.py](backend/scripts/oppdater_parent_erp_fra_birk_csv.py): Oppdater properties.parent_unit_id_erp (og evt. unit_short_type, region) fra
  - Usage: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py [--csv PATH] [--dry-run] [--oppdater-felter]
  - Env: SUPABASE_SERVICE_KEY, SUPABASE_SERVICE_ROLE_KEY
- [backend/scripts/pattern_analyzer.py](backend/scripts/pattern_analyzer.py): Pattern Analysis Extension for Cost Analyzer
  - Env: DATABASE_URL
- [backend/scripts/reimport_all_financials.py](backend/scripts/reimport_all_financials.py): Script: reimport all financials
  - Env: DATABASE_URL
- [backend/scripts/reimport_all_financials_v2.py](backend/scripts/reimport_all_financials_v2.py): Normalize property name for better matching.
  - Env: DATABASE_URL
- [backend/scripts/remove_financial_duplicates.py](backend/scripts/remove_financial_duplicates.py): Script to find and remove duplicate financial transactions (manual_expenses)
  - Env: DATABASE_URL
- [backend/scripts/show_all_properties_contracts.py](backend/scripts/show_all_properties_contracts.py): Show all properties and their associated contracts.
  - Env: DATABASE_URL
- [backend/scripts/sjekk_lokalisering_for_import.py](backend/scripts/sjekk_lokalisering_for_import.py): Sjekk hva som finnes i databasen for CSV-import «Oversikt bygg og eiendom».
  - Usage: Kjør: cd backend && railway run python3 scripts/sjekk_lokalisering_for_import.py
  - Usage: eller: DATABASE_URL=... python3 scripts/sjekk_lokalisering_for_import.py
  - Env: DATABASE_URL
- [backend/scripts/sjekk_utgiftsduplikater.py](backend/scripts/sjekk_utgiftsduplikater.py): Sjekk duplikater i løpende utgifter (manual_expenses) per eiendom
  - Usage: Kjør fra backend: python3 scripts/sjekk_utgiftsduplikater.py
  - Env: DATABASE_URL
- [backend/scripts/slaa_opp_manglende_parent_brreg.py](backend/scripts/slaa_opp_manglende_parent_brreg.py): Slår opp manglende forelder (parent) for eiendommer via Brønnøysund Enhetsregisteret.
  - Usage: Kjør: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/slaa_opp_manglende_parent_brreg.py [--csv UTFIL]
  - Env: BRREG_UNDERENHET, SUPABASE_SERVICE_KEY, SUPABASE_SERVICE_ROLE_KEY
- [backend/scripts/test_cost_query.py](backend/scripts/test_cost_query.py): Script: test cost query
  - Env: DATABASE_URL
- [backend/scripts/test_financial_analysis.py](backend/scripts/test_financial_analysis.py): Script: test financial analysis
  - Env: DATABASE_URL
- [backend/scripts/update_expired_contracts.py](backend/scripts/update_expired_contracts.py): Update expired contracts to 'terminated' status.
  - Env: DATABASE_URL
- [backend/scripts/update_from_csv.py](backend/scripts/update_from_csv.py): Database Update Script - Enrich Matched Contracts with CSV Metadata
  - Usage: python3 scripts/update_from_csv.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/update_from_csv_sql.py](backend/scripts/update_from_csv_sql.py): Database Update Script (Raw SQL) - Enrich Matched Contracts with CSV Metadata
  - Usage: python3 scripts/update_from_csv_sql.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/update_property_names.py](backend/scripts/update_property_names.py): Update property names from CSV Avtalenavn field.
  - Env: DATABASE_URL
- [backend/scripts/update_property_usage.py](backend/scripts/update_property_usage.py): Update property usage types from CSV Type lokasjon field.
  - Env: DATABASE_URL
- [backend/scripts/update_remaining_nulls.py](backend/scripts/update_remaining_nulls.py): Manually update the 3 remaining NULL properties based on CSV findings.
  - Env: DATABASE_URL
- [backend/scripts/verify_annual_costs.py](backend/scripts/verify_annual_costs.py): Verifiserer dataintegritet: verify annual costs
  - Env: DATABASE_URL
- [backend/scripts/verify_contract_schema.py](backend/scripts/verify_contract_schema.py): Verifiserer dataintegritet: verify contract schema
  - Env: DATABASE_URL
- [backend/scripts/verify_property_financials.py](backend/scripts/verify_property_financials.py): Verifiserer dataintegritet: verify property financials
  - Env: DATABASE_URL

### HMS

- [backend/scripts/add_risk_status_column.py](backend/scripts/add_risk_status_column.py): Add missing status column to risk_assessments.
- [backend/scripts/check_hms_schema.py](backend/scripts/check_hms_schema.py): Sjekk/kontroll: check hms schema
  - Env: DATABASE_URL
- [backend/scripts/check_internal_control_cases.py](backend/scripts/check_internal_control_cases.py): Check internal control cases in the database using raw SQL to avoid ORM issues.
  - Env: DATABASE_URL
- [backend/scripts/check_risk_api.py](backend/scripts/check_risk_api.py): Sjekk/kontroll: check risk api
- [backend/scripts/create_checklist_tables.py](backend/scripts/create_checklist_tables.py): Script: create checklist tables
- [backend/scripts/populate_hms_data.py](backend/scripts/populate_hms_data.py): Populate HMS tables with realistic internal control data
  - Env: DATABASE_URL
- [backend/scripts/regenerate_natural_deviations.py](backend/scripts/regenerate_natural_deviations.py): Regenerate natural deviations (internal control cases) after synthetic data cleanup.
  - Env: DATABASE_URL
- [backend/scripts/seed_checklists.py](backend/scripts/seed_checklists.py): Seeder/testdata: seed checklists
- [backend/scripts/seed_deviations_variation.py](backend/scripts/seed_deviations_variation.py): Seeder/testdata: seed deviations variation
  - Env: DATABASE_URL
- [backend/scripts/seed_internal_control.py](backend/scripts/seed_internal_control.py): Seed internal control cases for all properties.
  - Env: DATABASE_URL
- [backend/scripts/test_deviations_api.py](backend/scripts/test_deviations_api.py): Script: test deviations api
- [backend/scripts/test_hms_generate.py](backend/scripts/test_hms_generate.py): Script: test hms generate
  - Env: DATABASE_URL
- [backend/scripts/verify_checklists.py](backend/scripts/verify_checklists.py): Verifiserer dataintegritet: verify checklists
- [backend/scripts/verify_years_coverage.py](backend/scripts/verify_years_coverage.py): Verify that synthetic data covers multiple calendar years.
  - Env: DATABASE_URL

### PDF

- [backend/scripts/langextract_poc.py](backend/scripts/langextract_poc.py): LangExtract + Docling POC
- [backend/scripts/parse_pdf_folder.py](backend/scripts/parse_pdf_folder.py): Parser alle PDF-filer i pdf_docs-mappen og lagrer ekstrahert tekst i pdf_docs/extracted/.
  - Usage: Kjør fra backend: python3 scripts/parse_pdf_folder.py
  - Env: PDF_DOCS
- [backend/scripts/search_pdf_extracts.py](backend/scripts/search_pdf_extracts.py): Søk i ekstrahert tekst fra pdf_docs/extracted/ (etter at parse_pdf_folder.py er kjørt).
  - Usage: Kjør fra backend: python scripts/search_pdf_extracts.py "søkeord"
  - Usage: print("Bruk: python scripts/search_pdf_extracts.py \"søkeord\"")
  - Usage: print("   Kjør først: python scripts/parse_pdf_folder.py")
  - Env: PDF_DOCS

### Bufdir

- [backend/scripts/berik_navn_familievernkontor.py](backend/scripts/berik_navn_familievernkontor.py): Berik eiendommer med navn fra familievernkontor-mapping (Bufdir.no).
  - Usage: Kjør: cd backend && railway run python3 scripts/berik_navn_familievernkontor.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/enrich_properties_bufdir.py](backend/scripts/enrich_properties_bufdir.py): Enrich properties with Bufdir data from bufdir_matches_robust.json.
  - Env: DATABASE_URL
- [backend/scripts/establish_bufdir_unmatched.py](backend/scripts/establish_bufdir_unmatched.py): Etabler eiendommer for bufdir-institusjoner som ikke matchet noen eiendom i datasettet.
  - Env: DATABASE_URL
- [backend/scripts/fetch_bufdir_data.py](backend/scripts/fetch_bufdir_data.py): Hent barnevernsinstitusjoner fra bufdir.no/barnevern/finn-institusjon/.
- [backend/scripts/fetch_images_for_barnevern.py](backend/scripts/fetch_images_for_barnevern.py): Søker på nettet etter bilder for barnevernsinstitusjoner som mangler bilde.
  - Env: DATABASE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
- [backend/scripts/inspect_bufdir_ids.py](backend/scripts/inspect_bufdir_ids.py): Inspiserer/viser detaljer: inspect bufdir ids
- [backend/scripts/match_bufdir_robust.py](backend/scripts/match_bufdir_robust.py): Robust matching of Bufdir institutions to properties.
  - Env: DATABASE_URL
- [backend/scripts/match_bufdir_to_properties.py](backend/scripts/match_bufdir_to_properties.py): Calculate similarity ratio between two strings
  - Env: DATABASE_URL
- [backend/scripts/populate_bup_data.py](backend/scripts/populate_bup_data.py): Script: populate bup data
- [backend/scripts/test_bufdir_pagination.py](backend/scripts/test_bufdir_pagination.py): Script: test bufdir pagination
- [backend/scripts/update_bufdir_enrichment.py](backend/scripts/update_bufdir_enrichment.py): Download image and save to output directory
  - Env: DATABASE_URL
- [backend/scripts/verify_enrichment.py](backend/scripts/verify_enrichment.py): Verify property enrichment with Bufdir data.
  - Env: DATABASE_URL

### Proximity

- [backend/scripts/geocode_all_properties.py](backend/scripts/geocode_all_properties.py): Complete geocoding solution for all properties.
- [backend/scripts/geocode_batch.py](backend/scripts/geocode_batch.py): Batch geocode properties using Nominatim and generate SQL UPDATE statements.
- [backend/scripts/geocode_direct.py](backend/scripts/geocode_direct.py): Geokoder adresser/koordinater: geocode direct
  - Env: DATABASE_URL
- [backend/scripts/geocode_missing_properties.py](backend/scripts/geocode_missing_properties.py): Geocode properties missing coordinates using Kartverket/Geonorge API.
  - Env: DATABASE_URL
- [backend/scripts/geocode_sample.py](backend/scripts/geocode_sample.py): Simple geocoding script - outputs SQL UPDATE statements.
- [scripts/refresh_proximity_batch.py](scripts/refresh_proximity_batch.py): Script for å batch-oppdatere nærliggende tjenester for alle eiendommer
  - Env: DATABASE_URL

### Andre

- [backend/scripts/add_frank_user.py](backend/scripts/add_frank_user.py): Quick script to add Frank as admin user
  - Env: DATABASE_URL
- [backend/scripts/add_metadata_column.py](backend/scripts/add_metadata_column.py): Add missing additional_metadata column.
- [backend/scripts/add_region_column.py](backend/scripts/add_region_column.py): Script: add region column
- [backend/scripts/ai_demo_runner.py](backend/scripts/ai_demo_runner.py): KI/LLM-relatert verktøy: ai demo runner
- [backend/scripts/alter_property_table.py](backend/scripts/alter_property_table.py): Script: alter property table
  - Env: DATABASE_URL
- [backend/scripts/analyse_orphan_address_matches.py](backend/scripts/analyse_orphan_address_matches.py): Analyser GL-transaksjoner for koststeder uten eiendom.
  - Usage: railway run python scripts/analyse_orphan_address_matches.py --dept 204416 --year 2025 [--csv output.csv]
  - Usage: railway run python scripts/analyse_orphan_address_matches.py --all --year 2025 [--csv output.csv]
  - Usage: railway run python scripts/analyse_orphan_address_matches.py --all --year 2025 --apply   # Oppdater gl_transactions.property_id
  - Env: DATABASE_URL
- [backend/scripts/analyze_address_quality.py](backend/scripts/analyze_address_quality.py): Detaljert analyse av adressedata og koordinater
  - Env: DATABASE_URL
- [backend/scripts/analyze_einovember.py](backend/scripts/analyze_einovember.py): Script to analyze Einovember.xls and compare with database data
  - Env: DATABASE_URL
- [backend/scripts/analyze_elements_availability.py](backend/scripts/analyze_elements_availability.py): KI/LLM-relatert verktøy: analyze elements availability
  - Env: DATABASE_URL
- [backend/scripts/analyze_missing_properties.py](backend/scripts/analyze_missing_properties.py): Analyze which properties can still be linked to GL data.
  - Env: DATABASE_URL
- [backend/scripts/analyze_regional_integrity.py](backend/scripts/analyze_regional_integrity.py): Deep analysis of regional integrity issues to understand:
  - Env: DATABASE_URL
- [backend/scripts/analyze_usage_types.py](backend/scripts/analyze_usage_types.py): Analyze property usage types and prepare for update.
  - Env: DATABASE_URL
- [backend/scripts/apply_schema_migration.py](backend/scripts/apply_schema_migration.py): Apply database schema changes for text_content table.
- [backend/scripts/apply_schema_migration_v2.py](backend/scripts/apply_schema_migration_v2.py): Apply database schema changes with explicit commit verification.
- [backend/scripts/approve_tool.py](backend/scripts/approve_tool.py): Script: approve tool
  - Usage: print("Usage: python scripts/approve_tool.py <tool_name|all>")
  - Env: DATABASE_URL
- [backend/scripts/backfill_gl_unique_unit_id.py](backend/scripts/backfill_gl_unique_unit_id.py): Backfill gl_transactions.property_id for properties where unit_id_erp
  - Usage: Run: railway run --service striking-insight python3 scripts/backfill_gl_unique_unit_id.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/check_address.py](backend/scripts/check_address.py): Sjekk/kontroll: check address
  - Env: DATABASE_URL
- [backend/scripts/check_addresses.py](backend/scripts/check_addresses.py): Sjekk om alle eiendommer og enheter/avdelinger har adresser.
  - Env: DATABASE_URL
- [backend/scripts/check_all_duplicates.py](backend/scripts/check_all_duplicates.py): Sjekk/kontroll: check all duplicates
- [backend/scripts/check_auth_tables.py](backend/scripts/check_auth_tables.py): Sjekk/kontroll: check auth tables
  - Env: DATABASE_URL
- [backend/scripts/check_brreg_kunngjoringer.py](backend/scripts/check_brreg_kunngjoringer.py): Sjekk/kontroll: check brreg kunngjoringer
- [backend/scripts/check_brreg_regnskap.py](backend/scripts/check_brreg_regnskap.py): Sjekk/kontroll: check brreg regnskap
- [backend/scripts/check_data_quality.py](backend/scripts/check_data_quality.py): Sjekk/kontroll: check data quality
  - Env: DATABASE_URL
- [backend/scripts/check_db.py](backend/scripts/check_db.py): Direct SQL check on what was actually saved to database
  - Env: DATABASE_URL
- [backend/scripts/check_db_permissions.py](backend/scripts/check_db_permissions.py): Check database write permissions and test insertion.
  - Env: DATABASE_URL
- [backend/scripts/check_external_apis.py](backend/scripts/check_external_apis.py): Sjekk/kontroll: check external apis
  - Env: FROST_CLIENT_ID, KARTVERKET_API_KEY, NVE_API_KEY
- [backend/scripts/check_gl_table_structure.py](backend/scripts/check_gl_table_structure.py): Check the actual structure of gl_transactions table in the database.
  - Env: DATABASE_URL
- [backend/scripts/check_losore.py](backend/scripts/check_losore.py): Sjekk/kontroll: check losore
- [backend/scripts/check_missing_addresses.py](backend/scripts/check_missing_addresses.py): Sjekk eiendommer med manglende adressedata
  - Env: DATABASE_URL
- [backend/scripts/check_property_details.py](backend/scripts/check_property_details.py): Check specific property details to answer user query.
  - Env: DATABASE_URL
- [backend/scripts/check_property_names.py](backend/scripts/check_property_names.py): Check property names in database.
  - Env: DATABASE_URL
- [backend/scripts/check_regions.py](backend/scripts/check_regions.py): Sjekk/kontroll: check regions
  - Env: DATABASE_URL
- [backend/scripts/check_schema.py](backend/scripts/check_schema.py): Sjekk/kontroll: check schema
  - Env: DATABASE_URL
- [backend/scripts/check_tools.py](backend/scripts/check_tools.py): Sjekk/kontroll: check tools
  - Env: DATABASE_URL
- [backend/scripts/check_users.py](backend/scripts/check_users.py): Sjekk/kontroll: check users
- [backend/scripts/classify_data.py](backend/scripts/classify_data.py): Classifies a field based on its name and context.
  - Env: DATABASE_URL, POSTGRES_DB
- [backend/scripts/cleanup_duplicates.py](backend/scripts/cleanup_duplicates.py): Script: cleanup duplicates
  - Env: DATABASE_URL
- [backend/scripts/cleanup_elements_verification.py](backend/scripts/cleanup_elements_verification.py): Script: cleanup elements verification
  - Env: DATABASE_URL
- [backend/scripts/clear_economic_data.py](backend/scripts/clear_economic_data.py): Script: clear economic data
  - Env: DATABASE_URL
- [backend/scripts/clear_regnskap_2026.py](backend/scripts/clear_regnskap_2026.py): Tøm regnskapsdata for 2026.
  - Usage: Kjør: cd backend && railway run env PYTHONPATH=. python3 scripts/clear_regnskap_2026.py [--force]
  - Env: DATABASE_URL
- [backend/scripts/compare_einovember.py](backend/scripts/compare_einovember.py): Compare Einovember.xls with database data to find discrepancies
  - Env: DATABASE_URL
- [backend/scripts/compare_totalny.py](backend/scripts/compare_totalny.py): Script: compare totalny
  - Env: DATABASE_URL
- [backend/scripts/count_core_data.py](backend/scripts/count_core_data.py): Viser antall eiendommer, enheter, kontrakter og partier (leietakere/utleiere) i databasen.
  - Usage: Kjør fra backend: python3 scripts/count_core_data.py
  - Env: DATABASE_URL
- [backend/scripts/count_unknown_parties.py](backend/scripts/count_unknown_parties.py): Script: count unknown parties
  - Env: DATABASE_URL
- [backend/scripts/create_admin_users.py](backend/scripts/create_admin_users.py): Script to create 5 admin users with secure passwords.
  - Env: DATABASE_URL
- [backend/scripts/debug_headers.py](backend/scripts/debug_headers.py): Script: debug headers
- [backend/scripts/debug_prod_user.py](backend/scripts/debug_prod_user.py): Script: debug prod user
  - Env: DATABASE_URL
- [backend/scripts/debug_variance.py](backend/scripts/debug_variance.py): Script: debug variance
  - Env: DATABASE_URL
- [backend/scripts/deep_scan_data.py](backend/scripts/deep_scan_data.py): Script: deep scan data
  - Env: DATABASE_URL
- [backend/scripts/delete_synthetic_properties.py](backend/scripts/delete_synthetic_properties.py): Delete synthetic properties and all related data.
  - Env: DATABASE_URL
- [backend/scripts/diagnose_eiendom_kostnader.py](backend/scripts/diagnose_eiendom_kostnader.py): Diagnostiser hvorfor en eiendom mangler kostnader.
  - Usage: Bruk: cd backend && railway run python3 scripts/diagnose_eiendom_kostnader.py "Familievernkontoret Innlandet Øst - Tynset"
  - Env: DATABASE_URL
- [backend/scripts/diagnose_jernbaneveien.py](backend/scripts/diagnose_jernbaneveien.py): Script: diagnose jernbaneveien
  - Env: DATABASE_URL
- [backend/scripts/dry_run_eiendom.py](backend/scripts/dry_run_eiendom.py): Script: dry run eiendom
  - Env: DATABASE_URL
- [backend/scripts/dry_run_import_elements.py](backend/scripts/dry_run_import_elements.py): Script: dry run import elements
  - Env: DATABASE_URL
- [backend/scripts/export_all_relationships.py](backend/scripts/export_all_relationships.py): Eksporterer data/rapport: export all relationships
  - Env: DATABASE_URL
- [backend/scripts/export_eiendommer_json.py](backend/scripts/export_eiendommer_json.py): Eksporter eiendommer, avdelinger (units), kontrakter og leietakere til én JSON-fil
  - Usage: cd backend && python scripts/export_eiendommer_json.py
  - Usage: cd backend && python scripts/export_eiendommer_json.py --also-flat
  - Env: DATABASE_URL, EXPORT_JSON_PATH
- [backend/scripts/export_overview_md.py](backend/scripts/export_overview_md.py): Eksporterer data/rapport: export overview md
  - Env: DATABASE_URL
- [backend/scripts/export_prediction_data.py](backend/scripts/export_prediction_data.py): Export prediction data for Excel generation.
  - Env: DATABASE_URL
- [backend/scripts/fetch_images_for_all_properties.py](backend/scripts/fetch_images_for_all_properties.py): Søker på nettet etter bilder og ekstra opplysninger for ALLE eiendommer som mangler bilde.
  - Usage: Kjør: cd backend && python scripts/fetch_images_for_all_properties.py [--dry-run] [--limit N] [--skip-existing]
  - Env: DATABASE_URL
- [backend/scripts/find_all_bufetat.py](backend/scripts/find_all_bufetat.py): Search for all types of Bufetat facilities
  - Env: DATABASE_URL
- [backend/scripts/find_elements_key.py](backend/scripts/find_elements_key.py): Script: find elements key
  - Env: DATABASE_URL
- [backend/scripts/find_good_example.py](backend/scripts/find_good_example.py): Check property details finding a good example.
  - Env: DATABASE_URL
- [backend/scripts/finn_og_fyll_leie_vedlikehold.py](backend/scripts/finn_og_fyll_leie_vedlikehold.py): Finn eiendommer som mangler Leie (YTD) eller Vedlikehold, og fyll med syntetisk data.
  - Usage: python3 scripts/finn_og_fyll_leie_vedlikehold.py --dry-run
  - Usage: python3 scripts/finn_og_fyll_leie_vedlikehold.py
  - Usage: python3 scripts/finn_og_fyll_leie_vedlikehold.py --all    # berik alle eiendommer
  - Env: DATABASE_URL
- [backend/scripts/fix_address_equals_name.py](backend/scripts/fix_address_equals_name.py): Script for å rette eiendommer der address ble feilaktig satt til navn. Ved BIRK-import
  - Env: DATABASE_URL
- [backend/scripts/fix_db_schema.py](backend/scripts/fix_db_schema.py): Script: fix db schema
- [backend/scripts/fix_embeddings.py](backend/scripts/fix_embeddings.py): Script: fix embeddings
  - Env: DATABASE_URL
- [backend/scripts/fix_fellesbyg_property_mismatch.py](backend/scripts/fix_fellesbyg_property_mismatch.py): Nullstill property_id på gl_transactions som ble feilaktig matchet til fellesbyg via adresse (Dim2).
  - Usage: railway run python scripts/fix_fellesbyg_property_mismatch.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/fix_negative_amounts.py](backend/scripts/fix_negative_amounts.py): Fix negative amounts that are clearly import errors while preserving legitimate credits.
  - Env: DATABASE_URL
- [backend/scripts/fix_regional_integrity.py](backend/scripts/fix_regional_integrity.py): Conservative fix for regional integrity issues.
  - Env: DATABASE_URL
- [backend/scripts/fix_regions.py](backend/scripts/fix_regions.py): Script: fix regions
  - Env: DATABASE_URL
- [backend/scripts/fix_thoroya_final.py](backend/scripts/fix_thoroya_final.py): Fix the final Thorøyaveien 1 property usage.
  - Env: DATABASE_URL
- [backend/scripts/fix_trigger.py](backend/scripts/fix_trigger.py): Fix trigger creation with separate statements.
- [backend/scripts/generate_json_from_txt.py](backend/scripts/generate_json_from_txt.py): Script: generate json from txt
- [backend/scripts/generate_mcp_tool.py](backend/scripts/generate_mcp_tool.py): Script: generate mcp tool
- [backend/scripts/global_search.py](backend/scripts/global_search.py): Script: global search
  - Env: DATABASE_URL
- [backend/scripts/grandfather_existing_users.py](backend/scripts/grandfather_existing_users.py): Script to grandfather existing users: set email_verified=True and mfa_verified_at.
  - Env: DATABASE_URL
- [backend/scripts/import_and_synthesize.py](backend/scripts/import_and_synthesize.py): Parses totalny.txt to get the Source of Truth for properties.
  - Env: DATABASE_URL
- [backend/scripts/import_elements_from_eiendom.py](backend/scripts/import_elements_from_eiendom.py): Importer/berik: import elements from eiendom
  - Env: DATABASE_URL
- [backend/scripts/import_landlords.py](backend/scripts/import_landlords.py): Importer/berik: import landlords
  - Env: DATABASE_URL
- [backend/scripts/import_manual_institusjoner.py](backend/scripts/import_manual_institusjoner.py): Importer det manuale institusjonssettet fra `data/manual_institusjoner.json`.
- [backend/scripts/import_oslo.py](backend/scripts/import_oslo.py): Importer/berik: import oslo
  - Env: DATABASE_URL, NVE_API_KEY
- [backend/scripts/import_totalny_selective.py](backend/scripts/import_totalny_selective.py): Importer/berik: import totalny selective
  - Env: DATABASE_URL
- [backend/scripts/index_docs.py](backend/scripts/index_docs.py): Script: index docs
  - Env: DATABASE_URL
- [backend/scripts/ingest_data.py](backend/scripts/ingest_data.py): Generates embedding using OpenAI directly.
  - Env: OPENAI_API_KEY
- [backend/scripts/ingest_master_data.py](backend/scripts/ingest_master_data.py): Script: ingest master data
- [backend/scripts/init_db.py](backend/scripts/init_db.py): Script: init db
- [backend/scripts/inspect_filenames.py](backend/scripts/inspect_filenames.py): Inspiserer/viser detaljer: inspect filenames
  - Env: DATABASE_URL
- [backend/scripts/inspect_full_schema.py](backend/scripts/inspect_full_schema.py): Inspiserer/viser detaljer: inspect full schema
  - Env: DATABASE_URL
- [backend/scripts/inspect_gl_columns.py](backend/scripts/inspect_gl_columns.py): Inspiserer/viser detaljer: inspect gl columns
  - Env: DATABASE_URL
- [backend/scripts/inspect_outliers.py](backend/scripts/inspect_outliers.py): Inspiserer/viser detaljer: inspect outliers
  - Env: DATABASE_URL
- [backend/scripts/inspect_property_data.py](backend/scripts/inspect_property_data.py): Inspiserer/viser detaljer: inspect property data
  - Env: DATABASE_URL
- [backend/scripts/inspect_schema.py](backend/scripts/inspect_schema.py): Inspiserer/viser detaljer: inspect schema
  - Env: DATABASE_URL
- [backend/scripts/inspect_specific_property.py](backend/scripts/inspect_specific_property.py): Inspiserer/viser detaljer: inspect specific property
  - Env: DATABASE_URL
- [backend/scripts/inspect_vectordb.py](backend/scripts/inspect_vectordb.py): Inspiserer/viser detaljer: inspect vectordb
  - Env: CHROMA_DB_PATH
- [backend/scripts/investigate_null_properties.py](backend/scripts/investigate_null_properties.py): Find the 3 properties with NULL usage and investigate.
  - Env: DATABASE_URL
- [backend/scripts/legg_til_eiendomsbilde.py](backend/scripts/legg_til_eiendomsbilde.py): Legg til eiendomsbilde for eiendommer som mangler.
  - Usage: Kjør: cd backend && railway run python3 scripts/legg_til_eiendomsbilde.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/list_properties.py](backend/scripts/list_properties.py): Script: list properties
  - Env: DATABASE_URL
- [backend/scripts/mark_all_properties_synthetic.py](backend/scripts/mark_all_properties_synthetic.py): Merker alle eiendommer som syntetiske ved å sette external_data.synthetic = True
  - Env: DATABASE_URL
- [backend/scripts/migrer_og_import_edon2_avdeling.py](backend/scripts/migrer_og_import_edon2_avdeling.py): Kjør migrering for unit_short_type/unit_type_derived, deretter e-don2-import
  - Usage: cd backend && python scripts/migrer_og_import_edon2_avdeling.py
  - Usage: # Med Railway: railway run -- python scripts/migrer_og_import_edon2_avdeling.py
  - Env: DATABASE_URL
- [backend/scripts/populate_property_metadata.py](backend/scripts/populate_property_metadata.py): Script: populate property metadata
  - Env: DATABASE_URL
- [backend/scripts/property_enrichment_batch.py](backend/scripts/property_enrichment_batch.py): Property enrichment pipeline (baseline + auto updates).
  - Usage: cd backend && PYTHONPATH=. .venv/bin/python scripts/property_enrichment_batch.py
  - Usage: cd backend && PYTHONPATH=. .venv/bin/python scripts/property_enrichment_batch.py --apply --min-score 0.65
  - Env: DATABASE_URL
- [backend/scripts/quick_stats.py](backend/scripts/quick_stats.py): Quick statistics about properties and synthetic data.
  - Env: DATABASE_URL
- [backend/scripts/rapport_innkjøpsanalyse_husleie.py](backend/scripts/rapport_innkjøpsanalyse_husleie.py): Rapport: Eiendommer og avdelinger med husleie fra Innkjøpsanalyse.
  - Usage: Kjør: railway run python scripts/rapport_innkjøpsanalyse_husleie.py [--year 2025]
  - Env: DATABASE_URL
- [backend/scripts/reconcile_master_data.py](backend/scripts/reconcile_master_data.py): Generates a stable deterministic hash ID from components.
- [backend/scripts/refresh_dashboard_metrics.py](backend/scripts/refresh_dashboard_metrics.py): Refresh DashboardMetrics table.
  - Env: DATABASE_URL
- [backend/scripts/regenerate_embeddings.py](backend/scripts/regenerate_embeddings.py): Generate embedding for text using OpenAI.
  - Env: DATABASE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_EMBEDDING_MODEL
- [backend/scripts/register_tools.py](backend/scripts/register_tools.py): Script: register tools
  - Env: DATABASE_URL
- [backend/scripts/remove_synthetic.py](backend/scripts/remove_synthetic.py): Script: remove synthetic
  - Env: DATABASE_URL
- [backend/scripts/remove_synthetic_marking.py](backend/scripts/remove_synthetic_marking.py): Fjern all syntetisk merking fra eiendommer, kontrakter og parter.
  - Usage: Kjør fra backend: cd backend && python scripts/remove_synthetic_marking.py
  - Env: DATABASE_URL
- [backend/scripts/reproduce_supplier_data.py](backend/scripts/reproduce_supplier_data.py): Script: reproduce supplier data
  - Env: DATABASE_URL
- [backend/scripts/reset_db.py](backend/scripts/reset_db.py): Script: reset db
- [backend/scripts/run_cron_jobs.py](backend/scripts/run_cron_jobs.py): Run cron jobs for internkontroll.
  - Usage: Kjør f.eks. daglig via cron: cd backend && python scripts/run_cron_jobs.py
  - Env: DATABASE_URL
- [backend/scripts/run_openai_query.py](backend/scripts/run_openai_query.py): Kjør én enkel OpenAI-spørring for å verifisere at OPENAI_API_KEY og oppsett fungerer.
  - Usage: cd backend && python scripts/run_openai_query.py
  - Usage: python scripts/run_openai_query.py
  - Usage: python scripts/run_openai_query.py "Din spørring her"
  - Env: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
- [backend/scripts/run_prediction.py](backend/scripts/run_prediction.py): Standalone prediction runner — kjøres direkte i Railway-miljøet via:
  - Usage: railway run --service striking-insight python scripts/run_prediction.py
  - Env: DATABASE_URL
- [backend/scripts/run_seed_users.py](backend/scripts/run_seed_users.py): Quick script to seed test users in production database
  - Env: DATABASE_URL
- [backend/scripts/search_pattern.py](backend/scripts/search_pattern.py): Script: search pattern
  - Env: DATABASE_URL
- [backend/scripts/seed_activity_templates.py](backend/scripts/seed_activity_templates.py): Seed activity_templates from ActivityGenerator.DEFAULT_TEMPLATES.
  - Env: DATABASE_URL
- [backend/scripts/seed_data.py](backend/scripts/seed_data.py): Seeder/testdata: seed data
  - Env: DATABASE_URL
- [backend/scripts/seed_db.py](backend/scripts/seed_db.py): Seeder/testdata: seed db
  - Env: DATABASE_URL
- [backend/scripts/seed_elements_verification.py](backend/scripts/seed_elements_verification.py): Seeder/testdata: seed elements verification
  - Env: DATABASE_URL
- [backend/scripts/seed_evolution_test.py](backend/scripts/seed_evolution_test.py): Seeder/testdata: seed evolution test
  - Env: DATABASE_URL
- [backend/scripts/seed_fictional_users.py](backend/scripts/seed_fictional_users.py): Seeder/testdata: seed fictional users
  - Env: DATABASE_URL
- [backend/scripts/seed_ns3451.py](backend/scripts/seed_ns3451.py): Seeder/testdata: seed ns3451
  - Env: DATABASE_URL
- [backend/scripts/seed_persona.py](backend/scripts/seed_persona.py): Seeder/testdata: seed persona
  - Env: DATABASE_URL
- [backend/scripts/seed_property_users.py](backend/scripts/seed_property_users.py): Seeder/testdata: seed property users
  - Env: DATABASE_URL
- [backend/scripts/seed_query_library_storste_lav_husleie.py](backend/scripts/seed_query_library_storste_lav_husleie.py): Seed query_library med «største eiendommer med lav husleie».
  - Env: DATABASE_URL
- [backend/scripts/seed_users_orm.py](backend/scripts/seed_users_orm.py): Seed test users directly via SQLAlchemy ORM
  - Env: DATABASE_URL
- [backend/scripts/set_user_passwords.py](backend/scripts/set_user_passwords.py): Set passwords for all users in the database
  - Env: DATABASE_URL
- [backend/scripts/sett_unit_id_erp_manglende_kostnader.py](backend/scripts/sett_unit_id_erp_manglende_kostnader.py): Sett unit_id_erp på eiendommer som mangler kostnadsdata, ved å matche mot GL department_code/department_name.
  - Usage: Kjør: cd backend && railway run python3 scripts/sett_unit_id_erp_manglende_kostnader.py [--dry-run]
  - Env: DATABASE_URL
- [backend/scripts/setup_memory.py](backend/scripts/setup_memory.py): )
  - Env: DATABASE_URL
- [backend/scripts/show_database_schema.py](backend/scripts/show_database_schema.py): Show complete database schema with all tables and fields
  - Env: DATABASE_URL
- [backend/scripts/simulate_linking.py](backend/scripts/simulate_linking.py): Script: simulate linking
- [backend/scripts/simulate_v2.py](backend/scripts/simulate_v2.py): Script: simulate v2
- [backend/scripts/sjekk_kostnader_vs_husleie.py](backend/scripts/sjekk_kostnader_vs_husleie.py): Sjekk om alle kostnader er slettet og kun husleie gjenstår.
  - Env: SUPABASE_SERVICE_KEY, SUPABASE_SERVICE_ROLE_KEY
- [backend/scripts/sjekk_naeringseiendom_matching.py](backend/scripts/sjekk_naeringseiendom_matching.py): Sjekk om eiendommer med type næringseiendom (eller som vises som det) er matchet
  - Usage: Kjør fra backend: cd backend && python scripts/sjekk_naeringseiendom_matching.py
  - Env: DATABASE_URL
- [backend/scripts/sjekk_navn_kun_adresse.py](backend/scripts/sjekk_navn_kun_adresse.py): Sjekk eiendommer som kun har adresse som navn (ingen egentlig eiendomsnavn).
  - Usage: Kjør: cd backend && railway run python3 scripts/sjekk_navn_kun_adresse.py
  - Usage: eller: DATABASE_URL=... python3 scripts/sjekk_navn_kun_adresse.py
  - Env: DATABASE_URL
- [backend/scripts/sjekk_regnskapsdata.py](backend/scripts/sjekk_regnskapsdata.py): Sjekk om regnskapsdata er tømt i Supabase.
  - Usage: Kjør: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/sjekk_regnskapsdata.py
  - Env: SUPABASE_SERVICE_KEY, SUPABASE_SERVICE_ROLE_KEY
- [backend/scripts/sjekk_utgifter_eiendommer.py](backend/scripts/sjekk_utgifter_eiendommer.py): Sjekk løpende utgifter per eiendom
  - Usage: Kjør fra backend: python scripts/sjekk_utgifter_eiendommer.py
  - Env: DATABASE_URL
- [backend/scripts/start_local_sandbox.py](backend/scripts/start_local_sandbox.py): Script: start local sandbox
- [backend/scripts/sync_upgraded_tools.py](backend/scripts/sync_upgraded_tools.py): Script: sync upgraded tools
- [backend/scripts/test_brreg_connectivity.py](backend/scripts/test_brreg_connectivity.py): Test BRREG (Brønnøysundregistrene) connectivity.
  - Usage: eller fra backend:  python3 scripts/test_brreg_connectivity.py [orgnr]
  - Env: BRREG
- [backend/scripts/test_chat_memory.py](backend/scripts/test_chat_memory.py): Script: test chat memory
  - Env: DATABASE_URL
- [backend/scripts/test_db_connect.py](backend/scripts/test_db_connect.py): Script: test db connect
  - Env: DATABASE_URL
- [backend/scripts/test_db_connection.py](backend/scripts/test_db_connection.py): Test database connection
  - Env: DATABASE_URL
- [backend/scripts/test_exec.py](backend/scripts/test_exec.py): Script: test exec
- [backend/scripts/test_gl_insert.py](backend/scripts/test_gl_insert.py): Test script to verify GL transaction insertion works.
  - Env: DATABASE_URL
- [backend/scripts/test_hybrid_search.py](backend/scripts/test_hybrid_search.py): Script: test hybrid search
  - Env: DATABASE_URL
- [backend/scripts/test_insert.py](backend/scripts/test_insert.py): Test single document migration to see full error.
- [backend/scripts/test_landslide_version.py](backend/scripts/test_landslide_version.py): Script: test landslide version
- [backend/scripts/test_memory_persona.py](backend/scripts/test_memory_persona.py): Script: test memory persona
  - Env: DATABASE_URL
- [backend/scripts/test_nve_endpoints.py](backend/scripts/test_nve_endpoints.py): Script: test nve endpoints
- [backend/scripts/test_openai.py](backend/scripts/test_openai.py): KI/LLM-relatert verktøy: test openai
  - Env: OPENAI_API_KEY
- [backend/scripts/test_proactive_bench.py](backend/scripts/test_proactive_bench.py): Script: test proactive bench
  - Env: DATABASE_URL
- [backend/scripts/test_qa_bench.py](backend/scripts/test_qa_bench.py): Script: test qa bench
  - Env: DATABASE_URL
- [backend/scripts/test_rbac.py](backend/scripts/test_rbac.py): Quick RBAC test script.
- [backend/scripts/test_search.py](backend/scripts/test_search.py): Script: test search
  - Env: DATABASE_URL
- [backend/scripts/test_sql_bench.py](backend/scripts/test_sql_bench.py): Script: test sql bench
  - Env: DATABASE_URL
- [backend/scripts/test_timeseries.py](backend/scripts/test_timeseries.py): Quick test of the timeseries generator
- [backend/scripts/test_toolbox.py](backend/scripts/test_toolbox.py): Script: test toolbox
  - Env: DATABASE_URL
- [backend/scripts/trigger_evolution.py](backend/scripts/trigger_evolution.py): Script: trigger evolution
- [backend/scripts/trigger_metrics_refresh.py](backend/scripts/trigger_metrics_refresh.py): Script: trigger metrics refresh
- [backend/scripts/update_regions_from_excel.py](backend/scripts/update_regions_from_excel.py): Update 4 property regions from Einovember.xls
  - Env: DATABASE_URL
- [backend/scripts/verify_accounting.py](backend/scripts/verify_accounting.py): Verifiserer dataintegritet: verify accounting
  - Env: DATABASE_URL
- [backend/scripts/verify_admin.py](backend/scripts/verify_admin.py): Verifiserer dataintegritet: verify admin
  - Env: DATABASE_URL
- [backend/scripts/verify_ai_semantic.py](backend/scripts/verify_ai_semantic.py): Verifiserer dataintegritet: verify ai semantic
  - Env: DATABASE_URL
- [backend/scripts/verify_approval_table.py](backend/scripts/verify_approval_table.py): Verifiserer dataintegritet: verify approval table
- [backend/scripts/verify_brreg_enhet.py](backend/scripts/verify_brreg_enhet.py): Verifiserer dataintegritet: verify brreg enhet
  - Env: BRREG
- [backend/scripts/verify_brreg_persistence.py](backend/scripts/verify_brreg_persistence.py): Verifiserer dataintegritet: verify brreg persistence
  - Env: DATABASE_URL
- [backend/scripts/verify_cleanup.py](backend/scripts/verify_cleanup.py): Quick verification script to count transactions after cleanup
  - Env: DATABASE_URL
- [backend/scripts/verify_data.py](backend/scripts/verify_data.py): Verifiserer dataintegritet: verify data
  - Env: DATABASE_URL, POSTGRES_DB, POSTGRES_SERVER
- [backend/scripts/verify_data_integrity.py](backend/scripts/verify_data_integrity.py): Verifiserer dataintegritet: verify data integrity
  - Env: DATABASE_URL
- [backend/scripts/verify_empty.py](backend/scripts/verify_empty.py): Verifiserer dataintegritet: verify empty
  - Env: DATABASE_URL
- [backend/scripts/verify_gl_transactions.py](backend/scripts/verify_gl_transactions.py): Verify that GL transactions have been generated correctly for all properties.
  - Env: DATABASE_URL
- [backend/scripts/verify_headers.py](backend/scripts/verify_headers.py): Verifiserer dataintegritet: verify headers
- [backend/scripts/verify_historical_data.py](backend/scripts/verify_historical_data.py): Verifiserer dataintegritet: verify historical data
  - Env: DATABASE_URL
- [backend/scripts/verify_import_details.py](backend/scripts/verify_import_details.py): Verifiserer dataintegritet: verify import details
  - Env: DATABASE_URL
- [backend/scripts/verify_imports.py](backend/scripts/verify_imports.py): Verifiserer dataintegritet: verify imports
- [backend/scripts/verify_maskinporten.py](backend/scripts/verify_maskinporten.py): Verifiserer dataintegritet: verify maskinporten
  - Env: RRH_MASKINPORTEN_CLIENT_ID, RRH_MASKINPORTEN_KEY_PATH
- [backend/scripts/verify_mcp_integration.py](backend/scripts/verify_mcp_integration.py): Verifiserer dataintegritet: verify mcp integration
  - Env: DOCKER_MCP_GATEWAY_URL, LOCAL_MODEL_NAME, USE_LOCAL_AI
- [backend/scripts/verify_memory.py](backend/scripts/verify_memory.py): Verifiserer dataintegritet: verify memory
  - Env: DATABASE_URL
- [backend/scripts/verify_multi_agent.py](backend/scripts/verify_multi_agent.py): Verifiserer dataintegritet: verify multi agent
- [backend/scripts/verify_postgis.py](backend/scripts/verify_postgis.py): Verifiserer dataintegritet: verify postgis
  - Env: DATABASE_URL
- [backend/scripts/verify_rrh_creds.py](backend/scripts/verify_rrh_creds.py): Verifiserer dataintegritet: verify rrh creds
- [backend/scripts/verify_rrh_creds_v2.py](backend/scripts/verify_rrh_creds_v2.py): Verifiserer dataintegritet: verify rrh creds v2
- [backend/scripts/verify_script_executor.py](backend/scripts/verify_script_executor.py): Verify the run_analysis_script MCP tool works correctly.
- [backend/scripts/verify_semantic_data.py](backend/scripts/verify_semantic_data.py): Verifiserer dataintegritet: verify semantic data
- [backend/scripts/verify_stored_data.py](backend/scripts/verify_stored_data.py): Verifiserer dataintegritet: verify stored data
  - Env: DATABASE_URL
- [backend/scripts/verify_templates.py](backend/scripts/verify_templates.py): Verifiserer dataintegritet: verify templates
  - Env: DATABASE_URL
- [backend/scripts/verify_tool_creation.py](backend/scripts/verify_tool_creation.py): Verifiserer dataintegritet: verify tool creation
- [backend/scripts/verify_upgrade.py](backend/scripts/verify_upgrade.py): Verifiserer dataintegritet: verify upgrade
- [backend/scripts/verify_vector_search.py](backend/scripts/verify_vector_search.py): Verifiserer dataintegritet: verify vector search
  - Env: DATABASE_URL, ENABLE_VECTOR_SEARCH
- [backend/scripts/verify_web_tools.py](backend/scripts/verify_web_tools.py): Verifiserer dataintegritet: verify web tools
- [scripts/aggregate_suppliers.py](scripts/aggregate_suppliers.py): Script: aggregate suppliers
  - Env: DATABASE_URL
- [scripts/check_migration_safety.py](scripts/check_migration_safety.py): Pre-commit hook to check Alembic migrations for unsafe patterns.
- [scripts/generate_python_docs.py](scripts/generate_python_docs.py): Generate expanded Python script documentation into docs/python.md.
  - Usage: python3 scripts/generate_python_docs.py
  - Usage: """Scan markdown and shell files for 'python scripts/<name>.py' references."""
  - Env: BRREG, BRREG_, DATABASE_URL, ENV_NAME, MASKINPORTEN, MASKINPORTEN_, OPENAI_API_KEY, OPENAI_BASE_URL, PDF_DOCS
- [scripts/generate_python_docs_v2.py](scripts/generate_python_docs_v2.py): Script: generate python docs v2
  - Env: BRREG, OPENAI_API_KEY
- [scripts/scan_terms.py](scripts/scan_terms.py): Script: scan terms

- `BRREG`: (se settings)
- `BRREG_`: (se settings)
- `BRREG_UNDERENHET`: (se settings)
- `CHROMA_DB_PATH`: (se settings)
- `DATABASE_URL`: Postgres connection string used by backend scripts.
- `DOCKER_MCP_GATEWAY_URL`: (se settings)
- `ENABLE_VECTOR_SEARCH`: (se settings)
- `ENV_NAME`: (se settings)
- `EXPORT_JSON_PATH`: (se settings)
- `FROST_CLIENT_ID`: (se settings)
- `KARTVERKET_API_KEY`: (se settings)
- `LOCAL_MODEL_NAME`: (se settings)
- `MASKINPORTEN`: (se settings)
- `MASKINPORTEN_`: (se settings)
- `NVE_API_KEY`: (se settings)
- `OPENAI_API_KEY`: API key for OpenAI LLM integrations.
- `OPENAI_BASE_URL`: Optional override for OpenAI HTTP endpoint.
- `OPENAI_EMBEDDING_MODEL`: (se settings)
- `OPENAI_MODEL`: Model name used when calling OpenAI (e.g., gpt-4o-mini).
- `PDF_DOCS`: Path to folder containing PDF documents to process.
- `POSTGRES_DB`: (se settings)
- `POSTGRES_SERVER`: (se settings)
- `RRH_MASKINPORTEN_CLIENT_ID`: (se settings)
- `RRH_MASKINPORTEN_KEY_PATH`: (se settings)
- `SUPABASE_SERVICE_KEY`: (se settings)
- `SUPABASE_SERVICE_ROLE_KEY`: (se settings)
- `USE_LOCAL_AI`: (se settings)
- `MASKINPORTEN_*`: Credentials/config for Maskinporten integrations.
- `BRREG_*`: Configuration for BRREG service access.

## Alle Skript – Auto-genererte forklaringer

- [backend/scripts/add_contract_category.py](backend/scripts/add_contract_category.py): Script: add contract category
- [backend/scripts/add_frank_user.py](backend/scripts/add_frank_user.py): Quick script to add Frank as admin user
- [backend/scripts/add_metadata_column.py](backend/scripts/add_metadata_column.py): Add missing additional_metadata column.
- [backend/scripts/add_region_column.py](backend/scripts/add_region_column.py): Script: add region column
- [backend/scripts/add_risk_status_column.py](backend/scripts/add_risk_status_column.py): Add missing status column to risk_assessments.
- [backend/scripts/advanced_financial_analysis.py](backend/scripts/advanced_financial_analysis.py): Advanced financial data analysis with pattern recognition and intelligent auto-fix suggestions
- [backend/scripts/ai_demo_runner.py](backend/scripts/ai_demo_runner.py): KI/LLM-relatert verktøy: ai demo runner
- [backend/scripts/alter_property_table.py](backend/scripts/alter_property_table.py): Script: alter property table
- [backend/scripts/analyse_orphan_address_matches.py](backend/scripts/analyse_orphan_address_matches.py): Analyser GL-transaksjoner for koststeder uten eiendom.
- [backend/scripts/analyze_address_quality.py](backend/scripts/analyze_address_quality.py): Detaljert analyse av adressedata og koordinater
- [backend/scripts/analyze_contract_fields_v2.py](backend/scripts/analyze_contract_fields_v2.py): Script: analyze contract fields v2
- [backend/scripts/analyze_contract_types.py](backend/scripts/analyze_contract_types.py): Script: analyze contract types
- [backend/scripts/analyze_contracts.py](backend/scripts/analyze_contracts.py): Script: analyze contracts
- [backend/scripts/analyze_einovember.py](backend/scripts/analyze_einovember.py): Script to analyze Einovember.xls and compare with database data
- [backend/scripts/analyze_elements_availability.py](backend/scripts/analyze_elements_availability.py): KI/LLM-relatert verktøy: analyze elements availability
- [backend/scripts/analyze_missing_properties.py](backend/scripts/analyze_missing_properties.py): Analyze which properties can still be linked to GL data.
- [backend/scripts/analyze_negative_amounts.py](backend/scripts/analyze_negative_amounts.py): Analyze negative amounts in financial transactions to identify:
- [backend/scripts/analyze_price_per_sqm.py](backend/scripts/analyze_price_per_sqm.py): Analyze contract data to calculate average price per square meter for rent estimation.
- [backend/scripts/analyze_regional_integrity.py](backend/scripts/analyze_regional_integrity.py): Deep analysis of regional integrity issues to understand:
- [backend/scripts/analyze_rent_discrepancy.py](backend/scripts/analyze_rent_discrepancy.py): Script: analyze rent discrepancy
- [backend/scripts/analyze_usage_types.py](backend/scripts/analyze_usage_types.py): Analyze property usage types and prepare for update.
- [backend/scripts/apply_schema_migration.py](backend/scripts/apply_schema_migration.py): Apply database schema changes for text_content table.
- [backend/scripts/apply_schema_migration_v2.py](backend/scripts/apply_schema_migration_v2.py): Apply database schema changes with explicit commit verification.
- [backend/scripts/approve_tool.py](backend/scripts/approve_tool.py): Script: approve tool
- [backend/scripts/audit_contracts.py](backend/scripts/audit_contracts.py): Comprehensive contract data audit
- [backend/scripts/audit_data_quality.py](backend/scripts/audit_data_quality.py): Revisjon/avdekking: audit data quality
- [backend/scripts/audit_expense_details.py](backend/scripts/audit_expense_details.py): Deep-dive audit to analyze expense patterns and detect duplicates
- [backend/scripts/audit_financial_outliers.py](backend/scripts/audit_financial_outliers.py): Comprehensive audit to find financial data outliers and suspicious values
- [backend/scripts/audit_gl_properties_2020_2025.py](backend/scripts/audit_gl_properties_2020_2025.py): Revisjon av gl_transactions 2020–2025:
- [backend/scripts/audit_incomplete_properties.py](backend/scripts/audit_incomplete_properties.py): Audit script to identify properties with missing or incomplete data
- [backend/scripts/audit_missing_financial_data.py](backend/scripts/audit_missing_financial_data.py): Comprehensive audit to find properties missing financial data
- [backend/scripts/avstem_husleie_mot_csv_2025.py](backend/scripts/avstem_husleie_mot_csv_2025.py): Avstemning: BEFS faktisk husleie (GL) mot Innkjøpsanalyse-CSV 2025.
- [backend/scripts/backfill_gl_name_match.py](backend/scripts/backfill_gl_name_match.py): Find and backfill GL rows for properties that match unmapped cost centers by name.
- [backend/scripts/backfill_gl_unique_unit_id.py](backend/scripts/backfill_gl_unique_unit_id.py): Backfill gl_transactions.property_id for properties where unit_id_erp
- [backend/scripts/berik_navn_familievernkontor.py](backend/scripts/berik_navn_familievernkontor.py): Berik eiendommer med navn fra familievernkontor-mapping (Bufdir.no).
- [backend/scripts/berik_navn_fra_oversikt_bygg.py](backend/scripts/berik_navn_fra_oversikt_bygg.py): Berik eiendommer som kun har adresse som navn, med navn fra «Oversikt bygg og eiendom» CSV.
- [backend/scripts/budget_2026_kategori.py](backend/scripts/budget_2026_kategori.py): Budsjett 2026 – kategori-basert estimering fra GL 2025.
- [backend/scripts/calculate_total_rent.py](backend/scripts/calculate_total_rent.py): Script: calculate total rent
- [backend/scripts/check_address.py](backend/scripts/check_address.py): Sjekk/kontroll: check address
- [backend/scripts/check_addresses.py](backend/scripts/check_addresses.py): Sjekk om alle eiendommer og enheter/avdelinger har adresser.
- [backend/scripts/check_all_duplicates.py](backend/scripts/check_all_duplicates.py): Sjekk/kontroll: check all duplicates
- [backend/scripts/check_auth_tables.py](backend/scripts/check_auth_tables.py): Sjekk/kontroll: check auth tables
- [backend/scripts/check_brreg_kunngjoringer.py](backend/scripts/check_brreg_kunngjoringer.py): Sjekk/kontroll: check brreg kunngjoringer
- [backend/scripts/check_brreg_regnskap.py](backend/scripts/check_brreg_regnskap.py): Sjekk/kontroll: check brreg regnskap
- [backend/scripts/check_contract_count.py](backend/scripts/check_contract_count.py): Quick database contract count check
- [backend/scripts/check_data_quality.py](backend/scripts/check_data_quality.py): Sjekk/kontroll: check data quality
- [backend/scripts/check_db.py](backend/scripts/check_db.py): Direct SQL check on what was actually saved to database
- [backend/scripts/check_db_permissions.py](backend/scripts/check_db_permissions.py): Check database write permissions and test insertion.
- [backend/scripts/check_db_rent.py](backend/scripts/check_db_rent.py): Sjekk/kontroll: check db rent
- [backend/scripts/check_external_apis.py](backend/scripts/check_external_apis.py): Sjekk/kontroll: check external apis
- [backend/scripts/check_gl_table_structure.py](backend/scripts/check_gl_table_structure.py): Check the actual structure of gl_transactions table in the database.
- [backend/scripts/check_hms_schema.py](backend/scripts/check_hms_schema.py): Sjekk/kontroll: check hms schema
- [backend/scripts/check_internal_control_cases.py](backend/scripts/check_internal_control_cases.py): Check internal control cases in the database using raw SQL to avoid ORM issues.
- [backend/scripts/check_losore.py](backend/scripts/check_losore.py): Sjekk/kontroll: check losore
- [backend/scripts/check_missing_addresses.py](backend/scripts/check_missing_addresses.py): Sjekk eiendommer med manglende adressedata
- [backend/scripts/check_properties_without_costs.py](backend/scripts/check_properties_without_costs.py): Check properties without cost data (contracts).
- [backend/scripts/check_property_details.py](backend/scripts/check_property_details.py): Check specific property details to answer user query.
- [backend/scripts/check_property_names.py](backend/scripts/check_property_names.py): Check property names in database.
- [backend/scripts/check_regions.py](backend/scripts/check_regions.py): Sjekk/kontroll: check regions
- [backend/scripts/check_risk_api.py](backend/scripts/check_risk_api.py): Sjekk/kontroll: check risk api
- [backend/scripts/check_schema.py](backend/scripts/check_schema.py): Sjekk/kontroll: check schema
- [backend/scripts/check_synthetic_data_coverage.py](backend/scripts/check_synthetic_data_coverage.py): Check which properties have synthetic monthly financial data.
- [backend/scripts/check_tools.py](backend/scripts/check_tools.py): Sjekk/kontroll: check tools
- [backend/scripts/check_users.py](backend/scripts/check_users.py): Sjekk/kontroll: check users
- [backend/scripts/classify_data.py](backend/scripts/classify_data.py): Classifies a field based on its name and context.
- [backend/scripts/cleanup_bad_amounts.py](backend/scripts/cleanup_bad_amounts.py): Clean up contracts with corrupted amounts (> 50M NOK threshold).
- [backend/scripts/cleanup_duplicates.py](backend/scripts/cleanup_duplicates.py): Script: cleanup duplicates
- [backend/scripts/cleanup_elements_verification.py](backend/scripts/cleanup_elements_verification.py): Script: cleanup elements verification
- [backend/scripts/clear_economic_data.py](backend/scripts/clear_economic_data.py): Script: clear economic data
- [backend/scripts/clear_regnskap_2026.py](backend/scripts/clear_regnskap_2026.py): Tøm regnskapsdata for 2026.
- [backend/scripts/compare_csv_portfolio.py](backend/scripts/compare_csv_portfolio.py): CSV Portfolio Data Comparison Script
- [backend/scripts/compare_einovember.py](backend/scripts/compare_einovember.py): Compare Einovember.xls with database data to find discrepancies
- [backend/scripts/compare_totalny.py](backend/scripts/compare_totalny.py): Script: compare totalny
- [backend/scripts/comprehensive_rent_fix.py](backend/scripts/comprehensive_rent_fix.py): Comprehensive script to fix ALL rent data issues:
- [backend/scripts/cost_analyzer.py](backend/scripts/cost_analyzer.py): EXPERT PROPERTY COST ANALYZER
- [backend/scripts/cost_monitor.py](backend/scripts/cost_monitor.py): Cost Monitor - Main Orchestration Script
- [backend/scripts/count_contracts.py](backend/scripts/count_contracts.py): Script: count contracts
- [backend/scripts/count_core_data.py](backend/scripts/count_core_data.py): Viser antall eiendommer, enheter, kontrakter og partier (leietakere/utleiere) i databasen.
- [backend/scripts/count_unknown_parties.py](backend/scripts/count_unknown_parties.py): Script: count unknown parties
- [backend/scripts/create_admin_users.py](backend/scripts/create_admin_users.py): Script to create 5 admin users with secure passwords.
- [backend/scripts/create_checklist_tables.py](backend/scripts/create_checklist_tables.py): Script: create checklist tables
- [backend/scripts/create_missing_properties.py](backend/scripts/create_missing_properties.py): Create stub property records for GL cost centers that exist in Agresso
- [backend/scripts/debug_headers.py](backend/scripts/debug_headers.py): Script: debug headers
- [backend/scripts/debug_prod_user.py](backend/scripts/debug_prod_user.py): Script: debug prod user
- [backend/scripts/debug_rent_issue.py](backend/scripts/debug_rent_issue.py): Script: debug rent issue
- [backend/scripts/debug_variance.py](backend/scripts/debug_variance.py): Script: debug variance
- [backend/scripts/deep_cost_analysis.py](backend/scripts/deep_cost_analysis.py): Deep cost analysis to identify additional data quality issues
- [backend/scripts/deep_scan_data.py](backend/scripts/deep_scan_data.py): Script: deep scan data
- [backend/scripts/delete_synthetic_properties.py](backend/scripts/delete_synthetic_properties.py): Delete synthetic properties and all related data.
- [backend/scripts/diagnose_contract.py](backend/scripts/diagnose_contract.py): Script: diagnose contract
- [backend/scripts/diagnose_eiendom_kostnader.py](backend/scripts/diagnose_eiendom_kostnader.py): Diagnostiser hvorfor en eiendom mangler kostnader.
- [backend/scripts/diagnose_jernbaneveien.py](backend/scripts/diagnose_jernbaneveien.py): Script: diagnose jernbaneveien
- [backend/scripts/dry_run_eiendom.py](backend/scripts/dry_run_eiendom.py): Script: dry run eiendom
- [backend/scripts/dry_run_import_elements.py](backend/scripts/dry_run_import_elements.py): Script: dry run import elements
- [backend/scripts/enrich_properties_bufdir.py](backend/scripts/enrich_properties_bufdir.py): Enrich properties with Bufdir data from bufdir_matches_robust.json.
- [backend/scripts/ensure_synthetic_contract_and_tenant.py](backend/scripts/ensure_synthetic_contract_and_tenant.py): Sikrer at alle syntetiske eiendommer har minst én syntetisk kontrakt og tilknyttet leietaker.
- [backend/scripts/establish_bufdir_unmatched.py](backend/scripts/establish_bufdir_unmatched.py): Etabler eiendommer for bufdir-institusjoner som ikke matchet noen eiendom i datasettet.
- [backend/scripts/estimate_budget_2026.py](backend/scripts/estimate_budget_2026.py): Estimer budsjett for 2026 basert på Innkjøpsanalyse (property_husleie_csv).
- [backend/scripts/export_all_relationships.py](backend/scripts/export_all_relationships.py): Eksporterer data/rapport: export all relationships
- [backend/scripts/export_eiendommer_json.py](backend/scripts/export_eiendommer_json.py): Eksporter eiendommer, avdelinger (units), kontrakter og leietakere til én JSON-fil
- [backend/scripts/export_financial_table.py](backend/scripts/export_financial_table.py): Export complete financial data table for all properties
- [backend/scripts/export_overview_md.py](backend/scripts/export_overview_md.py): Eksporterer data/rapport: export overview md
- [backend/scripts/export_prediction_data.py](backend/scripts/export_prediction_data.py): Export prediction data for Excel generation.
- [backend/scripts/export_properties_contracts.py](backend/scripts/export_properties_contracts.py): Export all properties and contracts to CSV for easy viewing.
- [backend/scripts/familievern_details.py](backend/scripts/familievern_details.py): Get detailed information about familievern contracts
- [backend/scripts/fetch_bufdir_data.py](backend/scripts/fetch_bufdir_data.py): Hent barnevernsinstitusjoner fra bufdir.no/barnevern/finn-institusjon/.
- [backend/scripts/fetch_images_for_all_properties.py](backend/scripts/fetch_images_for_all_properties.py): Søker på nettet etter bilder og ekstra opplysninger for ALLE eiendommer som mangler bilde.
- [backend/scripts/fetch_images_for_barnevern.py](backend/scripts/fetch_images_for_barnevern.py): Søker på nettet etter bilder for barnevernsinstitusjoner som mangler bilde.
- [backend/scripts/fill_budget_from_consumption.py](backend/scripts/fill_budget_from_consumption.py): Fyll budsjett-tabellen fra forbruk (manual_expenses) for 2024–2026 med ±variance per kategori.
- [backend/scripts/fill_missing_rents.py](backend/scripts/fill_missing_rents.py): Fill missing rent values using median price per square meter.
- [backend/scripts/fill_remaining_zero_rents.py](backend/scripts/fill_remaining_zero_rents.py): Investigate and fill the 24 remaining properties with 0 rent.
- [backend/scripts/find_all_bufetat.py](backend/scripts/find_all_bufetat.py): Search for all types of Bufetat facilities
- [backend/scripts/find_elements_key.py](backend/scripts/find_elements_key.py): Script: find elements key
- [backend/scripts/find_familievern.py](backend/scripts/find_familievern.py): Find all familievern (family counseling) contracts
- [backend/scripts/find_good_example.py](backend/scripts/find_good_example.py): Check property details finding a good example.
- [backend/scripts/find_zero_rent.py](backend/scripts/find_zero_rent.py): Script: find zero rent
- [backend/scripts/finn_og_fyll_leie_vedlikehold.py](backend/scripts/finn_og_fyll_leie_vedlikehold.py): Finn eiendommer som mangler Leie (YTD) eller Vedlikehold, og fyll med syntetisk data.
- [backend/scripts/fix_address_equals_name.py](backend/scripts/fix_address_equals_name.py): Script for å rette eiendommer der address ble feilaktig satt til navn. Ved BIRK-import
- [backend/scripts/fix_db_schema.py](backend/scripts/fix_db_schema.py): Script: fix db schema
- [backend/scripts/fix_embeddings.py](backend/scripts/fix_embeddings.py): Script: fix embeddings
- [backend/scripts/fix_empty_status.py](backend/scripts/fix_empty_status.py): Fix Invalid Contract Status Values
- [backend/scripts/fix_familievern_duplicate.py](backend/scripts/fix_familievern_duplicate.py): Fix duplicate familievern contracts
- [backend/scripts/fix_fellesbyg_property_mismatch.py](backend/scripts/fix_fellesbyg_property_mismatch.py): Nullstill property_id på gl_transactions som ble feilaktig matchet til fellesbyg via adresse (Dim2).
- [backend/scripts/fix_financial_discrepancies.py](backend/scripts/fix_financial_discrepancies.py): Fix financial data discrepancies with multiple repair strategies
- [backend/scripts/fix_financial_mixup.py](backend/scripts/fix_financial_mixup.py): Script: fix financial mixup
- [backend/scripts/fix_negative_amounts.py](backend/scripts/fix_negative_amounts.py): Fix negative amounts that are clearly import errors while preserving legitimate credits.
- [backend/scripts/fix_parent_erp_from_budget_csv.py](backend/scripts/fix_parent_erp_from_budget_csv.py): fix_parent_erp_from_budget_csv.py
- [backend/scripts/fix_regional_integrity.py](backend/scripts/fix_regional_integrity.py): Conservative fix for regional integrity issues.
- [backend/scripts/fix_regions.py](backend/scripts/fix_regions.py): Script: fix regions
- [backend/scripts/fix_rent_data.py](backend/scripts/fix_rent_data.py): Script: fix rent data
- [backend/scripts/fix_thoroya_final.py](backend/scripts/fix_thoroya_final.py): Fix the final Thorøyaveien 1 property usage.
- [backend/scripts/fix_trigger.py](backend/scripts/fix_trigger.py): Fix trigger creation with separate statements.
- [backend/scripts/generate_historical_financials.py](backend/scripts/generate_historical_financials.py): Script: generate historical financials
- [backend/scripts/generate_json_from_txt.py](backend/scripts/generate_json_from_txt.py): Script: generate json from txt
- [backend/scripts/generate_master_audit.py](backend/scripts/generate_master_audit.py): Generates address_match_audit.csv (BIRK vs Address Catalog)
- [backend/scripts/generate_mcp_tool.py](backend/scripts/generate_mcp_tool.py): Script: generate mcp tool
- [backend/scripts/generate_monthly_financial_timeseries.py](backend/scripts/generate_monthly_financial_timeseries.py): Generate synthetic monthly financial time-series dataset for real estate.
- [backend/scripts/generate_timeseries_for_all_properties.py](backend/scripts/generate_timeseries_for_all_properties.py): Generate monthly financial time-series for ALL properties in database.
- [backend/scripts/geocode_all_properties.py](backend/scripts/geocode_all_properties.py): Complete geocoding solution for all properties.
- [backend/scripts/geocode_batch.py](backend/scripts/geocode_batch.py): Batch geocode properties using Nominatim and generate SQL UPDATE statements.
- [backend/scripts/geocode_direct.py](backend/scripts/geocode_direct.py): Geokoder adresser/koordinater: geocode direct
- [backend/scripts/geocode_missing_properties.py](backend/scripts/geocode_missing_properties.py): Geocode properties missing coordinates using Kartverket/Geonorge API.
- [backend/scripts/geocode_sample.py](backend/scripts/geocode_sample.py): Simple geocoding script - outputs SQL UPDATE statements.
- [backend/scripts/global_search.py](backend/scripts/global_search.py): Script: global search
- [backend/scripts/grandfather_existing_users.py](backend/scripts/grandfather_existing_users.py): Script to grandfather existing users: set email_verified=True and mfa_verified_at.
- [backend/scripts/import_and_synthesize.py](backend/scripts/import_and_synthesize.py): Parses totalny.txt to get the Source of Truth for properties.
- [backend/scripts/import_bufetat_contracts.py](backend/scripts/import_bufetat_contracts.py): Import Bufetat rental contracts and enrich property data from CSV files.
- [backend/scripts/import_costs_birk_477.py](backend/scripts/import_costs_birk_477.py): Kobler de 477 birk-enhetene (Barnevernsinstitusjon + Avdeling) til kostnadsdata
- [backend/scripts/import_edon2_csv.py](backend/scripts/import_edon2_csv.py): Import fra e-don2/BIRK CSV til BEFS.
- [backend/scripts/import_elements_from_csv.py](backend/scripts/import_elements_from_csv.py): Importer/berik: import elements from csv
- [backend/scripts/import_elements_from_eiendom.py](backend/scripts/import_elements_from_eiendom.py): Importer/berik: import elements from eiendom
- [backend/scripts/import_financial_data.py](backend/scripts/import_financial_data.py): Fetch all properties to map names to IDs.
- [backend/scripts/import_financials_2025.py](backend/scripts/import_financials_2025.py): Importer/berik: import financials 2025
- [backend/scripts/import_financials_2025_rest.py](backend/scripts/import_financials_2025_rest.py): Import 2025 annual cost data via Supabase REST API (no direct DB connection needed).
- [backend/scripts/import_gl_agresso.py](backend/scripts/import_gl_agresso.py): Import Agresso GL-data (Eiendomfebruar.csv) → gl_transactions-tabell.
- [backend/scripts/import_gl_data.py](backend/scripts/import_gl_data.py): Import General Ledger data from ok1.csv into gl_transactions table.
- [backend/scripts/import_innkjøpsanalyse_husleie.py](backend/scripts/import_innkjøpsanalyse_husleie.py): Import Innkjøpsanalyse-CSV Total kost til property_husleie_csv.
- [backend/scripts/import_institusjoner_csv.py](backend/scripts/import_institusjoner_csv.py): Import fra Institusjons-CSV (barnevernsinstitusjoner med plasser) til BEFS.
- [backend/scripts/import_koststed_mapping.py](backend/scripts/import_koststed_mapping.py): Import koststed_eiendom_mapping.csv → koststed_mapping-tabell i Supabase.
- [backend/scripts/import_landlords.py](backend/scripts/import_landlords.py): Importer/berik: import landlords
- [backend/scripts/import_manual_institusjoner.py](backend/scripts/import_manual_institusjoner.py): Importer det manuale institusjonssettet fra `data/manual_institusjoner.json`.
- [backend/scripts/import_oslo.py](backend/scripts/import_oslo.py): Importer/berik: import oslo
- [backend/scripts/import_oversikt_bygg_eiendom_csv.py](backend/scripts/import_oversikt_bygg_eiendom_csv.py): Import fra «Oversikt bygg og eiendom - GK og Budsjetterte» eller «Eiendomsportefølje- Bufdir» CSV til BEFS.
- [backend/scripts/import_totalny_selective.py](backend/scripts/import_totalny_selective.py): Importer/berik: import totalny selective
- [backend/scripts/index_docs.py](backend/scripts/index_docs.py): Script: index docs
- [backend/scripts/ingest_data.py](backend/scripts/ingest_data.py): Generates embedding using OpenAI directly.
- [backend/scripts/ingest_master_data.py](backend/scripts/ingest_master_data.py): Script: ingest master data
- [backend/scripts/init_db.py](backend/scripts/init_db.py): Script: init db
- [backend/scripts/inspect_bufdir_ids.py](backend/scripts/inspect_bufdir_ids.py): Inspiserer/viser detaljer: inspect bufdir ids
- [backend/scripts/inspect_contracts.py](backend/scripts/inspect_contracts.py): Inspiserer/viser detaljer: inspect contracts
- [backend/scripts/inspect_filenames.py](backend/scripts/inspect_filenames.py): Inspiserer/viser detaljer: inspect filenames
- [backend/scripts/inspect_financial_data.py](backend/scripts/inspect_financial_data.py): Inspiserer/viser detaljer: inspect financial data
- [backend/scripts/inspect_full_schema.py](backend/scripts/inspect_full_schema.py): Inspiserer/viser detaljer: inspect full schema
- [backend/scripts/inspect_gl_columns.py](backend/scripts/inspect_gl_columns.py): Inspiserer/viser detaljer: inspect gl columns
- [backend/scripts/inspect_outliers.py](backend/scripts/inspect_outliers.py): Inspiserer/viser detaljer: inspect outliers
- [backend/scripts/inspect_property_data.py](backend/scripts/inspect_property_data.py): Inspiserer/viser detaljer: inspect property data
- [backend/scripts/inspect_schema.py](backend/scripts/inspect_schema.py): Inspiserer/viser detaljer: inspect schema
- [backend/scripts/inspect_specific_property.py](backend/scripts/inspect_specific_property.py): Inspiserer/viser detaljer: inspect specific property
- [backend/scripts/inspect_vectordb.py](backend/scripts/inspect_vectordb.py): Inspiserer/viser detaljer: inspect vectordb
- [backend/scripts/intelligent_auto_fix.py](backend/scripts/intelligent_auto_fix.py): Intelligent auto-fix script for financial data
- [backend/scripts/investigate_null_properties.py](backend/scripts/investigate_null_properties.py): Find the 3 properties with NULL usage and investigate.
- [backend/scripts/langextract_poc.py](backend/scripts/langextract_poc.py): LangExtract + Docling POC
- [backend/scripts/legg_til_eiendomsbilde.py](backend/scripts/legg_til_eiendomsbilde.py): Legg til eiendomsbilde for eiendommer som mangler.
- [backend/scripts/list_properties.py](backend/scripts/list_properties.py): Script: list properties
- [backend/scripts/mark_all_properties_synthetic.py](backend/scripts/mark_all_properties_synthetic.py): Merker alle eiendommer som syntetiske ved å sette external_data.synthetic = True
- [backend/scripts/match_bufdir_robust.py](backend/scripts/match_bufdir_robust.py): Robust matching of Bufdir institutions to properties.
- [backend/scripts/match_bufdir_to_properties.py](backend/scripts/match_bufdir_to_properties.py): Calculate similarity ratio between two strings
- [backend/scripts/migrer_og_import_edon2_avdeling.py](backend/scripts/migrer_og_import_edon2_avdeling.py): Kjør migrering for unit_short_type/unit_type_derived, deretter e-don2-import
- [backend/scripts/ml_financial_analysis.py](backend/scripts/ml_financial_analysis.py): Script: ml financial analysis
- [backend/scripts/oppdater_parent_erp_fra_birk_csv.py](backend/scripts/oppdater_parent_erp_fra_birk_csv.py): Oppdater properties.parent_unit_id_erp (og evt. unit_short_type, region) fra
- [backend/scripts/parse_pdf_folder.py](backend/scripts/parse_pdf_folder.py): Parser alle PDF-filer i pdf_docs-mappen og lagrer ekstrahert tekst i pdf_docs/extracted/.
- [backend/scripts/pattern_analyzer.py](backend/scripts/pattern_analyzer.py): Pattern Analysis Extension for Cost Analyzer
- [backend/scripts/populate_bup_data.py](backend/scripts/populate_bup_data.py): Script: populate bup data
- [backend/scripts/populate_hms_data.py](backend/scripts/populate_hms_data.py): Populate HMS tables with realistic internal control data
- [backend/scripts/populate_property_metadata.py](backend/scripts/populate_property_metadata.py): Script: populate property metadata
- [backend/scripts/property_enrichment_batch.py](backend/scripts/property_enrichment_batch.py): Property enrichment pipeline (baseline + auto updates).
- [backend/scripts/quick_stats.py](backend/scripts/quick_stats.py): Quick statistics about properties and synthetic data.
- [backend/scripts/rapport_innkjøpsanalyse_husleie.py](backend/scripts/rapport_innkjøpsanalyse_husleie.py): Rapport: Eiendommer og avdelinger med husleie fra Innkjøpsanalyse.
- [backend/scripts/reconcile_master_data.py](backend/scripts/reconcile_master_data.py): Generates a stable deterministic hash ID from components.
- [backend/scripts/refresh_dashboard_metrics.py](backend/scripts/refresh_dashboard_metrics.py): Refresh DashboardMetrics table.
- [backend/scripts/regenerate_embeddings.py](backend/scripts/regenerate_embeddings.py): Generate embedding for text using OpenAI.
- [backend/scripts/regenerate_natural_deviations.py](backend/scripts/regenerate_natural_deviations.py): Regenerate natural deviations (internal control cases) after synthetic data cleanup.
- [backend/scripts/register_tools.py](backend/scripts/register_tools.py): Script: register tools
- [backend/scripts/reimport_all_financials.py](backend/scripts/reimport_all_financials.py): Script: reimport all financials
- [backend/scripts/reimport_all_financials_v2.py](backend/scripts/reimport_all_financials_v2.py): Normalize property name for better matching.
- [backend/scripts/remove_financial_duplicates.py](backend/scripts/remove_financial_duplicates.py): Script to find and remove duplicate financial transactions (manual_expenses)
- [backend/scripts/remove_synthetic.py](backend/scripts/remove_synthetic.py): Script: remove synthetic
- [backend/scripts/remove_synthetic_marking.py](backend/scripts/remove_synthetic_marking.py): Fjern all syntetisk merking fra eiendommer, kontrakter og parter.
- [backend/scripts/reproduce_supplier_data.py](backend/scripts/reproduce_supplier_data.py): Script: reproduce supplier data
- [backend/scripts/reset_db.py](backend/scripts/reset_db.py): Script: reset db
- [backend/scripts/run_cron_jobs.py](backend/scripts/run_cron_jobs.py): Run cron jobs for internkontroll.
- [backend/scripts/run_openai_query.py](backend/scripts/run_openai_query.py): Kjør én enkel OpenAI-spørring for å verifisere at OPENAI_API_KEY og oppsett fungerer.
- [backend/scripts/run_prediction.py](backend/scripts/run_prediction.py): Standalone prediction runner — kjøres direkte i Railway-miljøet via:
- [backend/scripts/run_seed_users.py](backend/scripts/run_seed_users.py): Quick script to seed test users in production database
- [backend/scripts/search_pattern.py](backend/scripts/search_pattern.py): Script: search pattern
- [backend/scripts/search_pdf_extracts.py](backend/scripts/search_pdf_extracts.py): Søk i ekstrahert tekst fra pdf_docs/extracted/ (etter at parse_pdf_folder.py er kjørt).
- [backend/scripts/seed_activity_templates.py](backend/scripts/seed_activity_templates.py): Seed activity_templates from ActivityGenerator.DEFAULT_TEMPLATES.
- [backend/scripts/seed_checklists.py](backend/scripts/seed_checklists.py): Seeder/testdata: seed checklists
- [backend/scripts/seed_data.py](backend/scripts/seed_data.py): Seeder/testdata: seed data
- [backend/scripts/seed_db.py](backend/scripts/seed_db.py): Seeder/testdata: seed db
- [backend/scripts/seed_deviations_variation.py](backend/scripts/seed_deviations_variation.py): Seeder/testdata: seed deviations variation
- [backend/scripts/seed_elements_verification.py](backend/scripts/seed_elements_verification.py): Seeder/testdata: seed elements verification
- [backend/scripts/seed_evolution_test.py](backend/scripts/seed_evolution_test.py): Seeder/testdata: seed evolution test
- [backend/scripts/seed_fictional_users.py](backend/scripts/seed_fictional_users.py): Seeder/testdata: seed fictional users
- [backend/scripts/seed_internal_control.py](backend/scripts/seed_internal_control.py): Seed internal control cases for all properties.
- [backend/scripts/seed_ns3451.py](backend/scripts/seed_ns3451.py): Seeder/testdata: seed ns3451
- [backend/scripts/seed_persona.py](backend/scripts/seed_persona.py): Seeder/testdata: seed persona
- [backend/scripts/seed_property_users.py](backend/scripts/seed_property_users.py): Seeder/testdata: seed property users
- [backend/scripts/seed_query_library_storste_lav_husleie.py](backend/scripts/seed_query_library_storste_lav_husleie.py): Seed query_library med «største eiendommer med lav husleie».
- [backend/scripts/seed_users_orm.py](backend/scripts/seed_users_orm.py): Seed test users directly via SQLAlchemy ORM
- [backend/scripts/set_user_passwords.py](backend/scripts/set_user_passwords.py): Set passwords for all users in the database
- [backend/scripts/sett_unit_id_erp_manglende_kostnader.py](backend/scripts/sett_unit_id_erp_manglende_kostnader.py): Sett unit_id_erp på eiendommer som mangler kostnadsdata, ved å matche mot GL department_code/department_name.
- [backend/scripts/setup_memory.py](backend/scripts/setup_memory.py): )
- [backend/scripts/show_all_properties_contracts.py](backend/scripts/show_all_properties_contracts.py): Show all properties and their associated contracts.
- [backend/scripts/show_database_schema.py](backend/scripts/show_database_schema.py): Show complete database schema with all tables and fields
- [backend/scripts/simulate_linking.py](backend/scripts/simulate_linking.py): Script: simulate linking
- [backend/scripts/simulate_v2.py](backend/scripts/simulate_v2.py): Script: simulate v2
- [backend/scripts/sjekk_kostnader_vs_husleie.py](backend/scripts/sjekk_kostnader_vs_husleie.py): Sjekk om alle kostnader er slettet og kun husleie gjenstår.
- [backend/scripts/sjekk_lokalisering_for_import.py](backend/scripts/sjekk_lokalisering_for_import.py): Sjekk hva som finnes i databasen for CSV-import «Oversikt bygg og eiendom».
- [backend/scripts/sjekk_naeringseiendom_matching.py](backend/scripts/sjekk_naeringseiendom_matching.py): Sjekk om eiendommer med type næringseiendom (eller som vises som det) er matchet
- [backend/scripts/sjekk_navn_kun_adresse.py](backend/scripts/sjekk_navn_kun_adresse.py): Sjekk eiendommer som kun har adresse som navn (ingen egentlig eiendomsnavn).
- [backend/scripts/sjekk_regnskapsdata.py](backend/scripts/sjekk_regnskapsdata.py): Sjekk om regnskapsdata er tømt i Supabase.
- [backend/scripts/sjekk_utgifter_eiendommer.py](backend/scripts/sjekk_utgifter_eiendommer.py): Sjekk løpende utgifter per eiendom
- [backend/scripts/sjekk_utgiftsduplikater.py](backend/scripts/sjekk_utgiftsduplikater.py): Sjekk duplikater i løpende utgifter (manual_expenses) per eiendom
- [backend/scripts/slaa_opp_manglende_parent_brreg.py](backend/scripts/slaa_opp_manglende_parent_brreg.py): Slår opp manglende forelder (parent) for eiendommer via Brønnøysund Enhetsregisteret.
- [backend/scripts/start_local_sandbox.py](backend/scripts/start_local_sandbox.py): Script: start local sandbox
- [backend/scripts/sync_upgraded_tools.py](backend/scripts/sync_upgraded_tools.py): Script: sync upgraded tools
- [backend/scripts/test_brreg_connectivity.py](backend/scripts/test_brreg_connectivity.py): Test BRREG (Brønnøysundregistrene) connectivity.
- [backend/scripts/test_bufdir_pagination.py](backend/scripts/test_bufdir_pagination.py): Script: test bufdir pagination
- [backend/scripts/test_chat_memory.py](backend/scripts/test_chat_memory.py): Script: test chat memory
- [backend/scripts/test_cost_query.py](backend/scripts/test_cost_query.py): Script: test cost query
- [backend/scripts/test_db_connect.py](backend/scripts/test_db_connect.py): Script: test db connect
- [backend/scripts/test_db_connection.py](backend/scripts/test_db_connection.py): Test database connection
- [backend/scripts/test_deviations_api.py](backend/scripts/test_deviations_api.py): Script: test deviations api
- [backend/scripts/test_exec.py](backend/scripts/test_exec.py): Script: test exec
- [backend/scripts/test_financial_analysis.py](backend/scripts/test_financial_analysis.py): Script: test financial analysis
- [backend/scripts/test_gl_insert.py](backend/scripts/test_gl_insert.py): Test script to verify GL transaction insertion works.
- [backend/scripts/test_hms_generate.py](backend/scripts/test_hms_generate.py): Script: test hms generate
- [backend/scripts/test_hybrid_search.py](backend/scripts/test_hybrid_search.py): Script: test hybrid search
- [backend/scripts/test_insert.py](backend/scripts/test_insert.py): Test single document migration to see full error.
- [backend/scripts/test_landslide_version.py](backend/scripts/test_landslide_version.py): Script: test landslide version
- [backend/scripts/test_memory_persona.py](backend/scripts/test_memory_persona.py): Script: test memory persona
- [backend/scripts/test_nve_endpoints.py](backend/scripts/test_nve_endpoints.py): Script: test nve endpoints
- [backend/scripts/test_openai.py](backend/scripts/test_openai.py): KI/LLM-relatert verktøy: test openai
- [backend/scripts/test_proactive_bench.py](backend/scripts/test_proactive_bench.py): Script: test proactive bench
- [backend/scripts/test_qa_bench.py](backend/scripts/test_qa_bench.py): Script: test qa bench
- [backend/scripts/test_rbac.py](backend/scripts/test_rbac.py): Quick RBAC test script.
- [backend/scripts/test_search.py](backend/scripts/test_search.py): Script: test search
- [backend/scripts/test_sql_bench.py](backend/scripts/test_sql_bench.py): Script: test sql bench
- [backend/scripts/test_timeseries.py](backend/scripts/test_timeseries.py): Quick test of the timeseries generator
- [backend/scripts/test_toolbox.py](backend/scripts/test_toolbox.py): Script: test toolbox
- [backend/scripts/trigger_evolution.py](backend/scripts/trigger_evolution.py): Script: trigger evolution
- [backend/scripts/trigger_metrics_refresh.py](backend/scripts/trigger_metrics_refresh.py): Script: trigger metrics refresh
- [backend/scripts/update_bufdir_enrichment.py](backend/scripts/update_bufdir_enrichment.py): Download image and save to output directory
- [backend/scripts/update_expired_contracts.py](backend/scripts/update_expired_contracts.py): Update expired contracts to 'terminated' status.
- [backend/scripts/update_from_csv.py](backend/scripts/update_from_csv.py): Database Update Script - Enrich Matched Contracts with CSV Metadata
- [backend/scripts/update_from_csv_sql.py](backend/scripts/update_from_csv_sql.py): Database Update Script (Raw SQL) - Enrich Matched Contracts with CSV Metadata
- [backend/scripts/update_property_names.py](backend/scripts/update_property_names.py): Update property names from CSV Avtalenavn field.
- [backend/scripts/update_property_usage.py](backend/scripts/update_property_usage.py): Update property usage types from CSV Type lokasjon field.
- [backend/scripts/update_regions_from_excel.py](backend/scripts/update_regions_from_excel.py): Update 4 property regions from Einovember.xls
- [backend/scripts/update_remaining_nulls.py](backend/scripts/update_remaining_nulls.py): Manually update the 3 remaining NULL properties based on CSV findings.
- [backend/scripts/verify_accounting.py](backend/scripts/verify_accounting.py): Verifiserer dataintegritet: verify accounting
- [backend/scripts/verify_admin.py](backend/scripts/verify_admin.py): Verifiserer dataintegritet: verify admin
- [backend/scripts/verify_ai_semantic.py](backend/scripts/verify_ai_semantic.py): Verifiserer dataintegritet: verify ai semantic
- [backend/scripts/verify_annual_costs.py](backend/scripts/verify_annual_costs.py): Verifiserer dataintegritet: verify annual costs
- [backend/scripts/verify_approval_table.py](backend/scripts/verify_approval_table.py): Verifiserer dataintegritet: verify approval table
- [backend/scripts/verify_brreg_enhet.py](backend/scripts/verify_brreg_enhet.py): Verifiserer dataintegritet: verify brreg enhet
- [backend/scripts/verify_brreg_persistence.py](backend/scripts/verify_brreg_persistence.py): Verifiserer dataintegritet: verify brreg persistence
- [backend/scripts/verify_checklists.py](backend/scripts/verify_checklists.py): Verifiserer dataintegritet: verify checklists
- [backend/scripts/verify_cleanup.py](backend/scripts/verify_cleanup.py): Quick verification script to count transactions after cleanup
- [backend/scripts/verify_contract_schema.py](backend/scripts/verify_contract_schema.py): Verifiserer dataintegritet: verify contract schema
- [backend/scripts/verify_data.py](backend/scripts/verify_data.py): Verifiserer dataintegritet: verify data
- [backend/scripts/verify_data_integrity.py](backend/scripts/verify_data_integrity.py): Verifiserer dataintegritet: verify data integrity
- [backend/scripts/verify_empty.py](backend/scripts/verify_empty.py): Verifiserer dataintegritet: verify empty
- [backend/scripts/verify_enrichment.py](backend/scripts/verify_enrichment.py): Verify property enrichment with Bufdir data.
- [backend/scripts/verify_gl_transactions.py](backend/scripts/verify_gl_transactions.py): Verify that GL transactions have been generated correctly for all properties.
- [backend/scripts/verify_headers.py](backend/scripts/verify_headers.py): Verifiserer dataintegritet: verify headers
- [backend/scripts/verify_historical_data.py](backend/scripts/verify_historical_data.py): Verifiserer dataintegritet: verify historical data
- [backend/scripts/verify_import_details.py](backend/scripts/verify_import_details.py): Verifiserer dataintegritet: verify import details
- [backend/scripts/verify_imports.py](backend/scripts/verify_imports.py): Verifiserer dataintegritet: verify imports
- [backend/scripts/verify_maskinporten.py](backend/scripts/verify_maskinporten.py): Verifiserer dataintegritet: verify maskinporten
- [backend/scripts/verify_mcp_integration.py](backend/scripts/verify_mcp_integration.py): Verifiserer dataintegritet: verify mcp integration
- [backend/scripts/verify_memory.py](backend/scripts/verify_memory.py): Verifiserer dataintegritet: verify memory
- [backend/scripts/verify_multi_agent.py](backend/scripts/verify_multi_agent.py): Verifiserer dataintegritet: verify multi agent
- [backend/scripts/verify_postgis.py](backend/scripts/verify_postgis.py): Verifiserer dataintegritet: verify postgis
- [backend/scripts/verify_property_financials.py](backend/scripts/verify_property_financials.py): Verifiserer dataintegritet: verify property financials
- [backend/scripts/verify_rrh_creds.py](backend/scripts/verify_rrh_creds.py): Verifiserer dataintegritet: verify rrh creds
- [backend/scripts/verify_rrh_creds_v2.py](backend/scripts/verify_rrh_creds_v2.py): Verifiserer dataintegritet: verify rrh creds v2
- [backend/scripts/verify_script_executor.py](backend/scripts/verify_script_executor.py): Verify the run_analysis_script MCP tool works correctly.
- [backend/scripts/verify_semantic_data.py](backend/scripts/verify_semantic_data.py): Verifiserer dataintegritet: verify semantic data
- [backend/scripts/verify_stored_data.py](backend/scripts/verify_stored_data.py): Verifiserer dataintegritet: verify stored data
- [backend/scripts/verify_templates.py](backend/scripts/verify_templates.py): Verifiserer dataintegritet: verify templates
- [backend/scripts/verify_tool_creation.py](backend/scripts/verify_tool_creation.py): Verifiserer dataintegritet: verify tool creation
- [backend/scripts/verify_upgrade.py](backend/scripts/verify_upgrade.py): Verifiserer dataintegritet: verify upgrade
- [backend/scripts/verify_vector_search.py](backend/scripts/verify_vector_search.py): Verifiserer dataintegritet: verify vector search
- [backend/scripts/verify_web_tools.py](backend/scripts/verify_web_tools.py): Verifiserer dataintegritet: verify web tools
- [backend/scripts/verify_years_coverage.py](backend/scripts/verify_years_coverage.py): Verify that synthetic data covers multiple calendar years.
- [scripts/aggregate_suppliers.py](scripts/aggregate_suppliers.py): Script: aggregate suppliers
- [scripts/check_migration_safety.py](scripts/check_migration_safety.py): Pre-commit hook to check Alembic migrations for unsafe patterns.
- [scripts/generate_python_docs.py](scripts/generate_python_docs.py): Generate expanded Python script documentation into docs/python.md.
- [scripts/generate_python_docs_v2.py](scripts/generate_python_docs_v2.py): Script: generate python docs v2
- [scripts/refresh_proximity_batch.py](scripts/refresh_proximity_batch.py): Script for å batch-oppdatere nærliggende tjenester for alle eiendommer
- [scripts/scan_terms.py](scripts/scan_terms.py): Script: scan terms
