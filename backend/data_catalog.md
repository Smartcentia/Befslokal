# Data Classification Catalog

| Table | Column | Type | Classification | JSON Content |
|---|---|---|---|---|
| **infrastructure_costs** | id | INTEGER | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | service_name | VARCHAR(50) | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | collection_date | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | raw_metrics | JSONB | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | estimated_cost_usd | NUMERIC(10, 2) | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | active_time_seconds | INTEGER | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | cpu_used_seconds | INTEGER | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | storage_gb | NUMERIC(10, 2) | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | bandwidth_gb | NUMERIC(10, 2) | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | notes | TEXT | Level 3: Restricted (Financial) |  |
| **infrastructure_costs** | created_at | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **sessions** | session_id | UUID | Level 2: Internal |  |
| **sessions** | user_email | VARCHAR | Level 3: Restricted (PII) |  |
| **sessions** | access_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **sessions** | id_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **sessions** | refresh_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **sessions** | expires_at | TIMESTAMP | Level 2: Internal |  |
| **sessions** | created_at | TIMESTAMP | Level 2: Internal |  |
| **sessions** | updated_at | TIMESTAMP | Level 2: Internal |  |
| **audit_logs** | log_id | UUID | Level 2: Internal |  |
| **audit_logs** | timestamp | TIMESTAMP | Level 2: Internal |  |
| **audit_logs** | action | VARCHAR | Level 2: Internal |  |
| **audit_logs** | actor | VARCHAR | Level 2: Internal |  |
| **audit_logs** | entity_type | VARCHAR | Level 2: Internal |  |
| **audit_logs** | entity_id | VARCHAR | Level 2: Internal |  |
| **audit_logs** | details | JSON | Level 2: Internal |  |
| **audit_logs** | severity | VARCHAR | Level 2: Internal |  |
| **expenses** | expense_id | UUID | Level 3: Restricted (Financial) |  |
| **expenses** | property_id | UUID | Level 3: Restricted (Financial) |  |
| **expenses** | supplier_id | UUID | Level 3: Restricted (Financial) |  |
| **expenses** | amount | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **expenses** | date | DATE | Level 3: Restricted (Financial) |  |
| **expenses** | category | TEXT | Level 3: Restricted (Financial) |  |
| **expenses** | description | TEXT | Level 3: Restricted (Financial) |  |
| **expenses** | year | INTEGER | Level 3: Restricted (Financial) |  |
| **expenses** | created_at | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **expenses** | updated_at | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **suppliers** | supplier_id | UUID | Level 1: Public/Internal |  |
| **suppliers** | name | TEXT | Level 3: Restricted (PII) |  |
| **suppliers** | orgnr | VARCHAR(9) | Level 1: Public/Internal |  |
| **suppliers** | category | TEXT | Level 1: Public/Internal |  |
| **suppliers** | contact_info | TEXT | Level 1: Public/Internal |  |
| **suppliers** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **suppliers** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **alembic_version** | version_num | VARCHAR(32) | Level 1: Public/Internal |  |
| **crisis_centers** | center_id | UUID | Level 1: Public/Internal |  |
| **crisis_centers** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **crisis_centers** | location | VARCHAR | Level 1: Public/Internal |  |
| **crisis_centers** | url | VARCHAR | Level 1: Public/Internal |  |
| **crisis_centers** | latitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **crisis_centers** | longitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **crisis_centers** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **crisis_centers** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **nextauth_users** | id | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_users** | name | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_users** | email | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_users** | emailVerified | TIMESTAMP | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_users** | image | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | id | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | userId | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | type | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | provider | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | providerAccountId | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | refresh_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | access_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | expires_at | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | token_type | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | scope | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | id_token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | session_state | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | expires_in | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_accounts** | ext_expires_in | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_sessions** | id | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_sessions** | sessionToken | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_sessions** | userId | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_sessions** | expires | TIMESTAMP | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_verification_tokens** | identifier | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_verification_tokens** | token | TEXT | Level 3: Restricted (High Sensitivity) |  |
| **nextauth_verification_tokens** | expires | TIMESTAMP | Level 3: Restricted (High Sensitivity) |  |
| **socioeconomic_data** | socio_data_id | UUID | Level 1: Public/Internal |  |
| **socioeconomic_data** | property_id | UUID | Level 1: Public/Internal |  |
| **socioeconomic_data** | municipality_code | VARCHAR(10) | Level 1: Public/Internal |  |
| **socioeconomic_data** | crime_rate_per_1000 | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **socioeconomic_data** | unemployment_rate | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **socioeconomic_data** | median_income | NUMERIC(15, 2) | Level 1: Public/Internal |  |
| **socioeconomic_data** | population_density | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **socioeconomic_data** | demographic_profile | JSONB | Level 1: Public/Internal |  |
| **socioeconomic_data** | data_source | VARCHAR(50) | Level 1: Public/Internal |  |
| **socioeconomic_data** | year | INTEGER | Level 1: Public/Internal |  |
| **socioeconomic_data** | fetched_at | TIMESTAMP | Level 1: Public/Internal |  |
| **socioeconomic_data** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **pending_script_executions** | execution_id | VARCHAR | Level 1: Public/Internal |  |
| **pending_script_executions** | script_key | VARCHAR | Level 1: Public/Internal |  |
| **pending_script_executions** | params | JSON | Level 1: Public/Internal |  |
| **pending_script_executions** | requested_by | VARCHAR | Level 1: Public/Internal |  |
| **pending_script_executions** | requested_at | TIMESTAMP | Level 1: Public/Internal |  |
| **pending_script_executions** | status | VARCHAR | Level 1: Public/Internal |  |
| **pending_script_executions** | approved_by | VARCHAR | Level 1: Public/Internal |  |
| **pending_script_executions** | approved_at | TIMESTAMP | Level 1: Public/Internal |  |
| **pending_script_executions** | execution_result | TEXT | Level 1: Public/Internal |  |
| **pending_script_executions** | executed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **pending_script_executions** | reason | TEXT | Level 1: Public/Internal |  |
| **user_preferences** | preference_id | UUID | Level 3: Restricted (PII) |  |
| **user_preferences** | user_id | VARCHAR | Level 3: Restricted (PII) |  |
| **user_preferences** | language | VARCHAR(10) | Level 3: Restricted (PII) |  |
| **user_preferences** | notifications | JSON | Level 3: Restricted (PII) |  |
| **user_preferences** | ui_settings | JSON | Level 3: Restricted (PII) |  |
| **user_preferences** | created_at | TIMESTAMP | Level 3: Restricted (PII) |  |
| **user_preferences** | updated_at | TIMESTAMP | Level 3: Restricted (PII) |  |
| **context_history** | context_id | UUID | Level 1: Public/Internal |  |
| **context_history** | session_id | VARCHAR | Level 1: Public/Internal |  |
| **context_history** | user_id | VARCHAR | Level 3: Restricted (PII) |  |
| **context_history** | interaction_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **context_history** | content | JSON | Level 1: Public/Internal |  |
| **context_history** | embedding | JSON | Level 1: Public/Internal |  |
| **context_history** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **text_content** | text_id | UUID | Level 1: Public/Internal |  |
| **text_content** | source_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **text_content** | content | TEXT | Level 1: Public/Internal |  |
| **text_content** | additional_metadata | JSON | Level 1: Public/Internal |  |
| **text_content** | contract_id | UUID | Level 1: Public/Internal |  |
| **text_content** | unit_id | UUID | Level 1: Public/Internal |  |
| **text_content** | property_id | UUID | Level 1: Public/Internal |  |
| **text_content** | source_index_id | VARCHAR(255) | Level 1: Public/Internal |  |
| **text_content** | source_file | VARCHAR(500) | Level 1: Public/Internal |  |
| **text_content** | chunk_index | INTEGER | Level 1: Public/Internal |  |
| **text_content** | category | VARCHAR(100) | Level 1: Public/Internal |  |
| **text_content** | search_vector | TSVECTOR | Level 1: Public/Internal |  |
| **text_content** | embedding | NULL | Level 1: Public/Internal |  |
| **text_content** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **text_content** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **external_api_data** | api_data_id | UUID | Level 1: Public/Internal |  |
| **external_api_data** | source_api | VARCHAR(50) | Level 1: Public/Internal |  |
| **external_api_data** | entity_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **external_api_data** | entity_id | VARCHAR(100) | Level 1: Public/Internal |  |
| **external_api_data** | data | JSON | Level 1: Public/Internal | `geo_info, nve_stations, flood_forecast` |
| **external_api_data** | fetched_at | TIMESTAMP | Level 1: Public/Internal |  |
| **external_api_data** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **api_call_logs** | call_id | UUID | Level 1: Public/Internal |  |
| **api_call_logs** | service_name | VARCHAR(50) | Level 3: Restricted (PII) |  |
| **api_call_logs** | endpoint | VARCHAR(200) | Level 1: Public/Internal |  |
| **api_call_logs** | request_count | INTEGER | Level 1: Public/Internal |  |
| **api_call_logs** | cost_estimate | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **api_call_logs** | timestamp | TIMESTAMP | Level 1: Public/Internal |  |
| **api_call_logs** | response_time_ms | INTEGER | Level 1: Public/Internal |  |
| **api_call_logs** | status_code | INTEGER | Level 1: Public/Internal |  |
| **api_call_logs** | error_message | VARCHAR(500) | Level 1: Public/Internal |  |
| **natural_hazard_events** | event_id | UUID | Level 1: Public/Internal |  |
| **natural_hazard_events** | latitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **natural_hazard_events** | longitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **natural_hazard_events** | event_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **natural_hazard_events** | event_date | TIMESTAMP | Level 1: Public/Internal |  |
| **natural_hazard_events** | severity | VARCHAR(20) | Level 1: Public/Internal |  |
| **natural_hazard_events** | description | VARCHAR | Level 1: Public/Internal |  |
| **natural_hazard_events** | casualties | INTEGER | Level 1: Public/Internal |  |
| **natural_hazard_events** | property_damage | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **natural_hazard_events** | radius_affected_meters | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **natural_hazard_events** | data_source | VARCHAR(50) | Level 1: Public/Internal |  |
| **natural_hazard_events** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **gdpr_requests** | request_id | UUID | Level 1: Public/Internal |  |
| **gdpr_requests** | user_id | VARCHAR | Level 3: Restricted (PII) |  |
| **gdpr_requests** | request_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **gdpr_requests** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **gdpr_requests** | details | JSON | Level 1: Public/Internal |  |
| **gdpr_requests** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **gdpr_requests** | completed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | log_id | UUID | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | entity_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | entity_id | VARCHAR | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | original_pii_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | action | VARCHAR(20) | Level 1: Public/Internal |  |
| **gdpr_anonymization_logs** | timestamp | TIMESTAMP | Level 1: Public/Internal |  |
| **ai_tools** | id | UUID | Level 1: Public/Internal |  |
| **ai_tools** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **ai_tools** | description | TEXT | Level 1: Public/Internal |  |
| **ai_tools** | code | TEXT | Level 1: Public/Internal |  |
| **ai_tools** | dependencies | TEXT | Level 1: Public/Internal |  |
| **ai_tools** | requires_real_sk | BOOLEAN | Level 1: Public/Internal |  |
| **ai_tools** | qa_status | VARCHAR(7) | Level 1: Public/Internal |  |
| **ai_tools** | qa_report | TEXT | Level 1: Public/Internal |  |
| **ai_tools** | status | VARCHAR(12) | Level 1: Public/Internal |  |
| **ai_tools** | is_public | BOOLEAN | Level 1: Public/Internal |  |
| **ai_tools** | is_pinned | BOOLEAN | Level 1: Public/Internal |  |
| **ai_tools** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **ai_tools** | usage_count | INTEGER | Level 1: Public/Internal |  |
| **ai_tools** | last_used_at | TIMESTAMP | Level 1: Public/Internal |  |
| **ai_tools** | vector_id | VARCHAR | Level 1: Public/Internal |  |
| **centers** | center_id | VARCHAR | Level 1: Public/Internal |  |
| **centers** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **centers** | description | TEXT | Level 1: Public/Internal |  |
| **centers** | region | VARCHAR | Level 1: Public/Internal |  |
| **centers** | emergency_contacts | JSONB | Level 1: Public/Internal |  |
| **centers** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **centers** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **properties** | property_id | UUID | Level 1: Public/Internal |  |
| **properties** | address | VARCHAR | Level 3: Restricted (PII) |  |
| **properties** | postal_code | VARCHAR(4) | Level 1: Public/Internal |  |
| **properties** | city | VARCHAR | Level 1: Public/Internal |  |
| **properties** | latitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **properties** | longitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **properties** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **properties** | usage | VARCHAR | Level 1: Public/Internal |  |
| **properties** | total_area | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **properties** | land_area | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **properties** | construction_year | INTEGER | Level 1: Public/Internal |  |
| **properties** | energy_label | VARCHAR | Level 1: Public/Internal |  |
| **properties** | municipality | VARCHAR | Level 1: Public/Internal |  |
| **properties** | municipality_code | VARCHAR | Level 1: Public/Internal |  |
| **properties** | gnr | INTEGER | Level 1: Public/Internal |  |
| **properties** | bnr | INTEGER | Level 1: Public/Internal |  |
| **properties** | approved_places | INTEGER | Level 1: Public/Internal |  |
| **properties** | region | VARCHAR | Level 1: Public/Internal |  |
| **properties** | owner_name | VARCHAR | Level 3: Restricted (PII) |  |
| **properties** | org_number | VARCHAR | Level 1: Public/Internal |  |
| **properties** | regulation_type | VARCHAR | Level 1: Public/Internal |  |
| **properties** | project_phase | VARCHAR | Level 1: Public/Internal |  |
| **properties** | project_comments | VARCHAR | Level 1: Public/Internal |  |
| **properties** | full_address | JSONB | Level 3: Restricted (PII) |  |
| **properties** | center_id | VARCHAR | Level 1: Public/Internal |  |
| **properties** | crisis_contacts | JSONB | Level 1: Public/Internal |  |
| **properties** | external_data | JSONB | Level 1: Public/Internal | `financials, data_source, area_estimated, financial_history, bufdir`... |
| **properties** | malgruppe | VARCHAR | Level 1: Public/Internal |  |
| **properties** | contract_rent_nok | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | contract_maint_nok | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | contract_common_nok | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | contract_user_ops_nok | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | extension_terms | VARCHAR | Level 1: Public/Internal |  |
| **properties** | price_adj_clause | VARCHAR | Level 1: Public/Internal |  |
| **properties** | gl_rent_2025 | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | lok_omrade | VARCHAR(50) | Level 1: Public/Internal |  |
| **properties** | lok_distrikt | VARCHAR(50) | Level 1: Public/Internal |  |
| **properties** | fylke | VARCHAR(50) | Level 1: Public/Internal |  |
| **properties** | leased_area_kvm | NUMERIC(10,1) | Level 1: Public/Internal |  |
| **properties** | elements_id | VARCHAR(200) | Level 1: Public/Internal |  |
| **properties** | utleier_kategori | SMALLINT | Level 1: Public/Internal |  |
| **properties** | egnethet_lokalisering | VARCHAR(100) | Level 1: Public/Internal |  |
| **properties** | egnethet_bygg | VARCHAR(100) | Level 1: Public/Internal |  |
| **properties** | prioritert_videroforing | VARCHAR(50) | Level 1: Public/Internal |  |
| **properties** | ar_videreutvikling | INTEGER | Level 1: Public/Internal |  |
| **properties** | kostnader_videreutvikling | NUMERIC(14,2) | Level 3: Restricted (Financial) |  |
| **properties** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **properties** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **notifications** | notification_id | UUID | Level 1: Public/Internal |  |
| **notifications** | user_id | UUID | Level 3: Restricted (PII) |  |
| **notifications** | title | VARCHAR | Level 1: Public/Internal |  |
| **notifications** | message | VARCHAR | Level 1: Public/Internal |  |
| **notifications** | notification_type | VARCHAR | Level 1: Public/Internal |  |
| **notifications** | related_entity_type | VARCHAR | Level 1: Public/Internal |  |
| **notifications** | related_entity_id | UUID | Level 1: Public/Internal |  |
| **notifications** | is_read | BOOLEAN | Level 1: Public/Internal |  |
| **notifications** | read_at | TIMESTAMP | Level 1: Public/Internal |  |
| **notifications** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **user_property_association** | user_id | UUID | Level 3: Restricted (PII) |  |
| **user_property_association** | property_id | UUID | Level 3: Restricted (PII) |  |
| **units** | unit_id | UUID | Level 1: Public/Internal |  |
| **units** | property_id | UUID | Level 1: Public/Internal |  |
| **units** | purpose | VARCHAR | Level 1: Public/Internal |  |
| **units** | area_sqm | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **units** | floor | INTEGER | Level 1: Public/Internal |  |
| **units** | zone_type | VARCHAR | Level 1: Public/Internal |  |
| **units** | uu_compliant | BOOLEAN | Level 1: Public/Internal |  |
| **units** | uu_notes | VARCHAR | Level 1: Public/Internal |  |
| **units** | external_data | JSON | Level 1: Public/Internal |  |
| **units** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **units** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **external_risk_errors** | error_id | UUID | Level 1: Public/Internal |  |
| **external_risk_errors** | property_id | UUID | Level 1: Public/Internal |  |
| **external_risk_errors** | source | VARCHAR(50) | Level 1: Public/Internal |  |
| **external_risk_errors** | error_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **external_risk_errors** | error_message | VARCHAR(1000) | Level 1: Public/Internal |  |
| **external_risk_errors** | error_details | JSONB | Level 1: Public/Internal |  |
| **external_risk_errors** | http_status_code | INTEGER | Level 1: Public/Internal |  |
| **external_risk_errors** | url | VARCHAR(500) | Level 1: Public/Internal |  |
| **external_risk_errors** | latitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **external_risk_errors** | longitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **external_risk_errors** | retry_count | INTEGER | Level 1: Public/Internal |  |
| **external_risk_errors** | resolved | VARCHAR(10) | Level 1: Public/Internal |  |
| **external_risk_errors** | resolved_at | TIMESTAMP | Level 1: Public/Internal |  |
| **external_risk_errors** | resolved_by | VARCHAR(100) | Level 1: Public/Internal |  |
| **external_risk_errors** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **users** | user_id | UUID | Level 3: Restricted (PII) |  |
| **users** | email | VARCHAR | Level 3: Restricted (PII) |  |
| **users** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **users** | role | VARCHAR(16) | Level 3: Restricted (PII) |  |
| **users** | region | VARCHAR | Level 3: Restricted (PII) |  |
| **users** | email_verified | BOOLEAN | Level 3: Restricted (PII) |  |
| **users** | mfa_enabled | BOOLEAN | Level 3: Restricted (PII) |  |
| **users** | mfa_verified_at | TIMESTAMP | Level 3: Restricted (PII) |  |
| **users** | is_active | BOOLEAN | Level 3: Restricted (PII) |  |
| **users** | hashed_password | VARCHAR | Level 3: Restricted (High Sensitivity) |  |
| **risk_assessments** | assessment_id | UUID | Level 1: Public/Internal |  |
| **risk_assessments** | property_id | UUID | Level 1: Public/Internal |  |
| **risk_assessments** | assessment_date | TIMESTAMP | Level 1: Public/Internal |  |
| **risk_assessments** | methodology | VARCHAR(50) | Level 1: Public/Internal |  |
| **risk_assessments** | overall_risk_score | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **risk_assessments** | risk_category | VARCHAR(20) | Level 1: Public/Internal |  |
| **risk_assessments** | assessed_by | VARCHAR | Level 1: Public/Internal |  |
| **risk_assessments** | notes | VARCHAR | Level 1: Public/Internal |  |
| **risk_assessments** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **risk_assessments** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **checklist_executions** | execution_id | UUID | Level 1: Public/Internal |  |
| **checklist_executions** | template_id | UUID | Level 1: Public/Internal |  |
| **checklist_executions** | property_id | UUID | Level 1: Public/Internal |  |
| **checklist_executions** | user_id | UUID | Level 3: Restricted (PII) |  |
| **checklist_executions** | status | VARCHAR | Level 1: Public/Internal |  |
| **checklist_executions** | responses | JSON | Level 1: Public/Internal |  |
| **checklist_executions** | completed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **checklist_executions** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **scheduled_activities** | activity_id | UUID | Level 1: Public/Internal |  |
| **scheduled_activities** | property_id | UUID | Level 1: Public/Internal |  |
| **scheduled_activities** | title | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | description | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | activity_type | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | category | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | priority | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | responsible_role | VARCHAR | Level 1: Public/Internal |  |
| **scheduled_activities** | assigned_user_id | UUID | Level 3: Restricted (PII) |  |
| **scheduled_activities** | recurrence_rule | JSONB | Level 1: Public/Internal |  |
| **scheduled_activities** | next_due_date | TIMESTAMP | Level 1: Public/Internal |  |
| **scheduled_activities** | last_generated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **scheduled_activities** | enabled | BOOLEAN | Level 1: Public/Internal |  |
| **scheduled_activities** | property_tags_required | JSONB | Level 1: Public/Internal |  |
| **scheduled_activities** | property_tags_excluded | JSONB | Level 1: Public/Internal |  |
| **scheduled_activities** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **scheduled_activities** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **scheduled_activities** | created_by | VARCHAR | Level 1: Public/Internal |  |
| **generated_tools** | tool_id | UUID | Level 1: Public/Internal |  |
| **generated_tools** | name | VARCHAR(255) | Level 3: Restricted (PII) |  |
| **generated_tools** | description | TEXT | Level 1: Public/Internal |  |
| **generated_tools** | python_code | TEXT | Level 1: Public/Internal |  |
| **generated_tools** | sql_pattern | TEXT | Level 1: Public/Internal |  |
| **generated_tools** | status | VARCHAR(50) | Level 1: Public/Internal |  |
| **generated_tools** | source_log_ids | JSONB | Level 1: Public/Internal |  |
| **generated_tools** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **generated_tools** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **generated_tools** | version | INTEGER | Level 1: Public/Internal |  |
| **work_orders** | order_id | UUID | Level 1: Public/Internal |  |
| **work_orders** | property_id | UUID | Level 1: Public/Internal |  |
| **work_orders** | description | VARCHAR | Level 1: Public/Internal |  |
| **work_orders** | status | VARCHAR(50) | Level 1: Public/Internal |  |
| **work_orders** | priority | VARCHAR(20) | Level 1: Public/Internal |  |
| **work_orders** | assigned_to | VARCHAR | Level 1: Public/Internal |  |
| **work_orders** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **work_orders** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **building_components** | component_id | UUID | Level 1: Public/Internal |  |
| **building_components** | property_id | UUID | Level 1: Public/Internal |  |
| **building_components** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **building_components** | type | VARCHAR(50) | Level 1: Public/Internal |  |
| **building_components** | location | VARCHAR | Level 1: Public/Internal |  |
| **building_components** | install_date | TIMESTAMP | Level 1: Public/Internal |  |
| **building_components** | lifecycle_years | INTEGER | Level 1: Public/Internal |  |
| **building_components** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **building_components** | technical_data | JSON | Level 1: Public/Internal |  |
| **building_components** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **building_components** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **sensors** | sensor_id | UUID | Level 1: Public/Internal |  |
| **sensors** | property_id | UUID | Level 1: Public/Internal |  |
| **sensors** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **sensors** | type | VARCHAR(50) | Level 1: Public/Internal |  |
| **sensors** | location | VARCHAR | Level 1: Public/Internal |  |
| **sensors** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **sensors** | config | JSON | Level 1: Public/Internal |  |
| **sensors** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **budget** | budget_id | UUID | Level 3: Restricted (Financial) |  |
| **budget** | property_id | UUID | Level 3: Restricted (Financial) |  |
| **budget** | year | INTEGER | Level 3: Restricted (Financial) |  |
| **budget** | month | INTEGER | Level 3: Restricted (Financial) |  |
| **budget** | category | VARCHAR(100) | Level 3: Restricted (Financial) |  |
| **budget** | amount | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **budget** | created_at | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **budget** | updated_at | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **bim_models** | model_id | UUID | Level 1: Public/Internal |  |
| **bim_models** | property_id | UUID | Level 1: Public/Internal |  |
| **bim_models** | filename | VARCHAR | Level 3: Restricted (PII) |  |
| **bim_models** | format | VARCHAR(10) | Level 1: Public/Internal |  |
| **bim_models** | upload_date | TIMESTAMP | Level 1: Public/Internal |  |
| **bim_models** | file_path | VARCHAR | Level 1: Public/Internal |  |
| **bim_models** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **proximity_services** | service_id | UUID | Level 1: Public/Internal |  |
| **proximity_services** | property_id | UUID | Level 1: Public/Internal |  |
| **proximity_services** | service_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **proximity_services** | service_name | VARCHAR(255) | Level 3: Restricted (PII) |  |
| **proximity_services** | distance_meters | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **proximity_services** | travel_time_minutes | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **proximity_services** | latitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **proximity_services** | longitude | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **proximity_services** | rating | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **proximity_services** | address | VARCHAR(500) | Level 3: Restricted (PII) |  |
| **proximity_services** | phone | VARCHAR(50) | Level 3: Restricted (PII) |  |
| **proximity_services** | data_source | VARCHAR(50) | Level 1: Public/Internal |  |
| **proximity_services** | fetched_at | TIMESTAMP | Level 1: Public/Internal |  |
| **proximity_services** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **geological_data** | geo_data_id | UUID | Level 1: Public/Internal |  |
| **geological_data** | property_id | UUID | Level 1: Public/Internal |  |
| **geological_data** | bedrock_type | VARCHAR(100) | Level 1: Public/Internal |  |
| **geological_data** | soil_type | VARCHAR(100) | Level 1: Public/Internal |  |
| **geological_data** | groundwater_depth | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **geological_data** | landslide_risk | VARCHAR(20) | Level 1: Public/Internal |  |
| **geological_data** | quickclay_risk | INTEGER | Level 1: Public/Internal |  |
| **geological_data** | seismic_zone | INTEGER | Level 1: Public/Internal |  |
| **geological_data** | data_source | VARCHAR(50) | Level 1: Public/Internal |  |
| **geological_data** | raw_data | JSON | Level 1: Public/Internal |  |
| **geological_data** | fetched_at | TIMESTAMP | Level 1: Public/Internal |  |
| **geological_data** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **environmental_data** | env_data_id | UUID | Level 1: Public/Internal |  |
| **environmental_data** | property_id | UUID | Level 1: Public/Internal |  |
| **environmental_data** | air_quality_index | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **environmental_data** | noise_level_db | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **environmental_data** | pollution_sources | JSON | Level 1: Public/Internal |  |
| **environmental_data** | contaminated_sites_nearby | JSON | Level 1: Public/Internal |  |
| **environmental_data** | data_source | VARCHAR(50) | Level 1: Public/Internal |  |
| **environmental_data** | fetched_at | TIMESTAMP | Level 1: Public/Internal |  |
| **environmental_data** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **agent_memory** | id | UUID | Level 1: Public/Internal |  |
| **agent_memory** | content | TEXT | Level 1: Public/Internal |  |
| **agent_memory** | additional_metadata | JSONB | Level 3: Mixed Content (user (Level 3: Restricted (PII)), user_id (Level 3: Restricted (PII)), tool_name (Level 3: Restricted (PII)), name (Level 3: Restricted (PII)), user_query (Level 3: Restricted (PII))) | `type, property, user, user_id, timestamp`... |
| **agent_memory** | embedding | NULL | Level 1: Public/Internal |  |
| **agent_memory** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **parties** | party_id | UUID | Level 1: Public/Internal |  |
| **parties** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **parties** | orgnr | VARCHAR(9) | Level 1: Public/Internal |  |
| **parties** | contact_email | VARCHAR | Level 3: Restricted (PII) |  |
| **parties** | contact_phone | VARCHAR | Level 3: Restricted (PII) |  |
| **parties** | external_data | JSON | Level 1: Public/Internal | `party_type, brreg_enhet, brreg_roller, roles, openai_company_summary`... |
| **parties** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **parties** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **risk_factors** | factor_id | UUID | Level 1: Public/Internal |  |
| **risk_factors** | assessment_id | UUID | Level 1: Public/Internal |  |
| **risk_factors** | category | VARCHAR(50) | Level 1: Public/Internal |  |
| **risk_factors** | factor_name | VARCHAR(100) | Level 3: Restricted (PII) |  |
| **risk_factors** | severity | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **risk_factors** | probability | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **risk_factors** | weight | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **risk_factors** | data_source | VARCHAR(100) | Level 1: Public/Internal |  |
| **risk_factors** | raw_data | JSON | Level 1: Public/Internal |  |
| **risk_factors** | calculated_score | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **risk_factors** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **gl_transactions** | transaction_id | UUID | Level 3: Restricted (Financial) |  |
| **gl_transactions** | property_id | UUID | Level 3: Restricted (Financial) |  |
| **gl_transactions** | transaction_date | TIMESTAMP | Level 3: Restricted (Financial) |  |
| **gl_transactions** | year | INTEGER | Level 3: Restricted (Financial) |  |
| **gl_transactions** | month | INTEGER | Level 3: Restricted (Financial) |  |
| **gl_transactions** | amount | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **gl_transactions** | category | VARCHAR(100) | Level 3: Restricted (Financial) |  |
| **gl_transactions** | description | VARCHAR(500) | Level 3: Restricted (Financial) |  |
| **gl_transactions** | account_code | VARCHAR(50) | Level 3: Restricted (Financial) |  |
| **gl_transactions** | vendor | VARCHAR(200) | Level 3: Restricted (Financial) |  |
| **gl_transactions** | source_system | VARCHAR(50) | Level 3: Restricted (Financial) |  |
| **batch_jobs** | job_id | UUID | Level 1: Public/Internal |  |
| **batch_jobs** | job_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **batch_jobs** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **batch_jobs** | progress | INTEGER | Level 1: Public/Internal |  |
| **batch_jobs** | total_items | INTEGER | Level 1: Public/Internal |  |
| **batch_jobs** | processed_items | INTEGER | Level 1: Public/Internal |  |
| **batch_jobs** | success_count | INTEGER | Level 1: Public/Internal |  |
| **batch_jobs** | failed_count | INTEGER | Level 1: Public/Internal |  |
| **batch_jobs** | config | JSONB | Level 1: Public/Internal |  |
| **batch_jobs** | property_ids | JSONB | Level 1: Public/Internal |  |
| **batch_jobs** | results | JSONB | Level 1: Public/Internal |  |
| **batch_jobs** | errors | JSONB | Level 1: Public/Internal |  |
| **batch_jobs** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **batch_jobs** | started_at | TIMESTAMP | Level 1: Public/Internal |  |
| **batch_jobs** | completed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **batch_jobs** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **batch_jobs** | error_message | VARCHAR(1000) | Level 1: Public/Internal |  |
| **batch_jobs** | error_details | JSONB | Level 1: Public/Internal |  |
| **batch_jobs** | worker_id | VARCHAR(100) | Level 1: Public/Internal |  |
| **tasks** | task_id | UUID | Level 1: Public/Internal |  |
| **tasks** | order_id | UUID | Level 1: Public/Internal |  |
| **tasks** | title | VARCHAR | Level 1: Public/Internal |  |
| **tasks** | action_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **tasks** | payload | JSON | Level 1: Public/Internal |  |
| **tasks** | status | VARCHAR(50) | Level 1: Public/Internal |  |
| **tasks** | result | JSON | Level 1: Public/Internal |  |
| **tasks** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **tasks** | completed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **maintenance_records** | record_id | UUID | Level 1: Public/Internal |  |
| **maintenance_records** | component_id | UUID | Level 1: Public/Internal |  |
| **maintenance_records** | date_performed | TIMESTAMP | Level 1: Public/Internal |  |
| **maintenance_records** | performed_by | VARCHAR | Level 1: Public/Internal |  |
| **maintenance_records** | description | VARCHAR | Level 1: Public/Internal |  |
| **maintenance_records** | cost | INTEGER | Level 3: Restricted (Financial) |  |
| **maintenance_records** | linked_work_order_id | UUID | Level 1: Public/Internal |  |
| **maintenance_records** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **sensor_readings** | reading_id | UUID | Level 1: Public/Internal |  |
| **sensor_readings** | sensor_id | UUID | Level 1: Public/Internal |  |
| **sensor_readings** | timestamp | TIMESTAMP | Level 1: Public/Internal |  |
| **sensor_readings** | value | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **sensor_readings** | unit | VARCHAR(20) | Level 1: Public/Internal |  |
| **sensor_readings** | raw_data | JSON | Level 1: Public/Internal |  |
| **api_usage** | id | UUID | Level 1: Public/Internal |  |
| **api_usage** | endpoint | VARCHAR(100) | Level 1: Public/Internal |  |
| **api_usage** | model | VARCHAR(50) | Level 1: Public/Internal |  |
| **api_usage** | user_id | VARCHAR(255) | Level 3: Restricted (PII) |  |
| **api_usage** | prompt_tokens | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **api_usage** | completion_tokens | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **api_usage** | total_tokens | INTEGER | Level 3: Restricted (High Sensitivity) |  |
| **api_usage** | estimated_cost | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **api_usage** | request_path | VARCHAR(255) | Level 1: Public/Internal |  |
| **api_usage** | conversation_id | VARCHAR(100) | Level 1: Public/Internal |  |
| **api_usage** | error_message | TEXT | Level 1: Public/Internal |  |
| **api_usage** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **sensor_anomalies** | anomaly_id | UUID | Level 1: Public/Internal |  |
| **sensor_anomalies** | sensor_id | UUID | Level 1: Public/Internal |  |
| **sensor_anomalies** | detected_at | TIMESTAMP | Level 1: Public/Internal |  |
| **sensor_anomalies** | description | VARCHAR | Level 1: Public/Internal |  |
| **sensor_anomalies** | severity | VARCHAR(20) | Level 1: Public/Internal |  |
| **sensor_anomalies** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **sensor_anomalies** | resolution | VARCHAR | Level 1: Public/Internal |  |
| **bim_objects** | object_id | UUID | Level 1: Public/Internal |  |
| **bim_objects** | model_id | UUID | Level 1: Public/Internal |  |
| **bim_objects** | ifc_guid | VARCHAR(50) | Level 1: Public/Internal |  |
| **bim_objects** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **bim_objects** | type | VARCHAR(50) | Level 1: Public/Internal |  |
| **bim_objects** | pos_x | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **bim_objects** | pos_y | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **bim_objects** | pos_z | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **bim_objects** | properties | JSON | Level 1: Public/Internal |  |
| **bim_objects** | linked_component_id | UUID | Level 1: Public/Internal |  |
| **file_meta** | file_id | UUID | Level 1: Public/Internal |  |
| **file_meta** | contract_id | UUID | Level 1: Public/Internal |  |
| **file_meta** | path | VARCHAR | Level 1: Public/Internal |  |
| **file_meta** | sha256 | VARCHAR(64) | Level 1: Public/Internal |  |
| **file_meta** | file_type | VARCHAR(20) | Level 1: Public/Internal |  |
| **file_meta** | content_type | VARCHAR(100) | Level 1: Public/Internal |  |
| **file_meta** | tags | ARRAY | Level 1: Public/Internal |  |
| **file_meta** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **contracts** | contract_id | UUID | Level 1: Public/Internal |  |
| **contracts** | unit_id | UUID | Level 1: Public/Internal |  |
| **contracts** | party_id | UUID | Level 1: Public/Internal |  |
| **contracts** | status | VARCHAR(10) | Level 1: Public/Internal |  |
| **contracts** | category | VARCHAR | Level 1: Public/Internal |  |
| **contracts** | start_date | DATE | Level 1: Public/Internal |  |
| **contracts** | end_date | DATE | Level 1: Public/Internal |  |
| **contracts** | periods | JSONB | Level 1: Public/Internal |  |
| **contracts** | amount | JSONB | Level 3: Mixed Content (currency (Level 3: Restricted (Financial)), amount_per_year (Level 3: Restricted (Financial)), estimated (Level 3: Restricted (Financial)), used_default_area (Level 3: Restricted (Financial)), rent (Level 3: Restricted (Financial)), admin (Level 3: Restricted (Financial)), total (Level 3: Restricted (Financial)), energy (Level 3: Restricted (Financial)), heating (Level 3: Restricted (Financial)), maintenance (Level 3: Restricted (Financial)), common_costs (Level 3: Restricted (Financial))) | `currency, amount_per_year, estimated, used_default_area, rent`... |
| **contracts** | has_option | BOOLEAN | Level 1: Public/Internal |  |
| **contracts** | option_deadline | DATE | Level 1: Public/Internal |  |
| **contracts** | option_count_total | INTEGER | Level 1: Public/Internal |  |
| **contracts** | option_count_used | INTEGER | Level 1: Public/Internal |  |
| **contracts** | external_data | JSONB | Level 3: Mixed Content (energy_cost (Level 3: Restricted (Financial)), common_costs (Level 3: Restricted (Financial)), heating_cost (Level 3: Restricted (Financial)), contract_name (Level 3: Restricted (PII)), user_dependent_costs (Level 3: Restricted (Financial)), internal_maintenance_cost (Level 3: Restricted (Financial)), tenant_name (Level 3: Restricted (PII))) | `deposit, energy_cost, common_costs, heating_cost, contract_name`... |
| **contracts** | caretaker_cost | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **contracts** | cleaning_cost | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **contracts** | parking_cost | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **contracts** | card_reader_cost | DOUBLE PRECISION | Level 3: Restricted (High Sensitivity) |  |
| **contracts** | signed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **contracts** | terminated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **contracts** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **contracts** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **contracts** | filename_region | VARCHAR(10) | Level 3: Restricted (PII) |  |
| **contracts** | filename_type | VARCHAR(10) | Level 3: Restricted (PII) |  |
| **contracts** | filename_number | INTEGER | Level 3: Restricted (PII) |  |
| **contracts** | elements | VARCHAR | Level 1: Public/Internal |  |
| **query_library** | query_id | UUID | Level 1: Public/Internal |  |
| **query_library** | query_name | VARCHAR(255) | Level 3: Restricted (PII) |  |
| **query_library** | user_question_pattern | TEXT | Level 3: Restricted (PII) |  |
| **query_library** | sql_template | TEXT | Level 1: Public/Internal |  |
| **query_library** | description | TEXT | Level 1: Public/Internal |  |
| **query_library** | usage_count | INTEGER | Level 1: Public/Internal |  |
| **query_library** | success_rate | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **query_library** | avg_execution_time_ms | INTEGER | Level 1: Public/Internal |  |
| **query_library** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **query_library** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **query_library** | created_by | VARCHAR(50) | Level 1: Public/Internal |  |
| **dashboard_metrics** | metric_id | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | properties_count | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | contracts_count | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | risks_count | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | total_annual_rent | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **dashboard_metrics** | total_maintenance_cost | DOUBLE PRECISION | Level 3: Restricted (Financial) |  |
| **dashboard_metrics** | last_updated | TIMESTAMP | Level 1: Public/Internal |  |
| **dashboard_metrics** | critical_deviations | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | expiring_contracts | INTEGER | Level 1: Public/Internal |  |
| **dashboard_metrics** | overdue_tasks | INTEGER | Level 1: Public/Internal |  |
| **query_logs** | log_id | UUID | Level 1: Public/Internal |  |
| **query_logs** | user_question | TEXT | Level 3: Restricted (PII) |  |
| **query_logs** | generated_sql | TEXT | Level 1: Public/Internal |  |
| **query_logs** | query_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **query_logs** | execution_success | BOOLEAN | Level 1: Public/Internal |  |
| **query_logs** | result_count | INTEGER | Level 1: Public/Internal |  |
| **query_logs** | execution_time_ms | INTEGER | Level 1: Public/Internal |  |
| **query_logs** | error_message | TEXT | Level 1: Public/Internal |  |
| **query_logs** | context_data | JSONB | Level 3: Mixed Content (query_name (Level 3: Restricted (PII))) | `source, query_name, query_type, is_complex, error_type` |
| **query_logs** | timestamp | TIMESTAMP | Level 1: Public/Internal |  |
| **query_logs** | user_id | VARCHAR(255) | Level 3: Restricted (PII) |  |
| **query_logs** | conversation_id | VARCHAR(255) | Level 1: Public/Internal |  |
| **query_logs** | confidence_score | DOUBLE PRECISION | Level 1: Public/Internal |  |
| **query_logs** | model_used | VARCHAR(50) | Level 1: Public/Internal |  |
| **query_logs** | cache_hit | BOOLEAN | Level 1: Public/Internal |  |
| **query_logs** | retry_count | INTEGER | Level 1: Public/Internal |  |
| **query_logs** | parent_log_id | UUID | Level 3: Restricted (Financial) |  |
| **mfa_tokens** | token | VARCHAR | Level 3: Restricted (High Sensitivity) |  |
| **mfa_tokens** | user_email | VARCHAR | Level 3: Restricted (High Sensitivity) |  |
| **mfa_tokens** | expires_at | TIMESTAMP | Level 3: Restricted (High Sensitivity) |  |
| **mfa_tokens** | used | BOOLEAN | Level 3: Restricted (High Sensitivity) |  |
| **mfa_tokens** | created_at | TIMESTAMP | Level 3: Restricted (High Sensitivity) |  |
| **email_verification_codes** | id | VARCHAR | Level 3: Restricted (PII) |  |
| **email_verification_codes** | email | VARCHAR | Level 3: Restricted (PII) |  |
| **email_verification_codes** | code_hash | VARCHAR | Level 3: Restricted (PII) |  |
| **email_verification_codes** | expires_at | TIMESTAMP | Level 3: Restricted (PII) |  |
| **email_verification_codes** | used | BOOLEAN | Level 3: Restricted (PII) |  |
| **email_verification_codes** | created_at | TIMESTAMP | Level 3: Restricted (PII) |  |
| **forecast_cache** | forecast_id | UUID | Level 1: Public/Internal |  |
| **forecast_cache** | property_id | UUID | Level 1: Public/Internal |  |
| **forecast_cache** | forecast_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **forecast_cache** | parameters | JSONB | Level 1: Public/Internal |  |
| **forecast_cache** | result | JSONB | Level 1: Public/Internal |  |
| **forecast_cache** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **forecast_cache** | expires_at | TIMESTAMP | Level 1: Public/Internal |  |
| **scenarios** | scenario_id | UUID | Level 1: Public/Internal |  |
| **scenarios** | name | VARCHAR(200) | Level 3: Restricted (PII) |  |
| **scenarios** | description | TEXT | Level 1: Public/Internal |  |
| **scenarios** | base_forecast_id | UUID | Level 1: Public/Internal |  |
| **scenarios** | modifications | JSONB | Level 1: Public/Internal |  |
| **scenarios** | result_forecast | JSONB | Level 1: Public/Internal |  |
| **scenarios** | created_by | VARCHAR(100) | Level 1: Public/Internal |  |
| **scenarios** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **action_recommendations** | recommendation_id | UUID | Level 1: Public/Internal |  |
| **action_recommendations** | recommendation_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **action_recommendations** | target_entity_type | VARCHAR(50) | Level 1: Public/Internal |  |
| **action_recommendations** | target_entity_id | UUID | Level 1: Public/Internal |  |
| **action_recommendations** | priority | INTEGER | Level 1: Public/Internal |  |
| **action_recommendations** | estimated_impact_nok | NUMERIC(15, 2) | Level 1: Public/Internal |  |
| **action_recommendations** | description | TEXT | Level 1: Public/Internal |  |
| **action_recommendations** | ai_rationale | TEXT | Level 1: Public/Internal |  |
| **action_recommendations** | status | VARCHAR(20) | Level 1: Public/Internal |  |
| **action_recommendations** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **action_recommendations** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | case_id | UUID | Level 1: Public/Internal |  |
| **internal_control_cases** | property_id | UUID | Level 1: Public/Internal |  |
| **internal_control_cases** | risk_assessment_id | UUID | Level 1: Public/Internal |  |
| **internal_control_cases** | assigned_user_id | UUID | Level 3: Restricted (PII) |  |
| **internal_control_cases** | title | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | description | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | case_type | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | status | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | priority | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | due_date | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | completed_at | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | notes | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | process_state | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | process_data | JSON | Level 1: Public/Internal | `checklist, template_id, risk_class, legal_references, checklist_responses`... |
| **internal_control_cases** | process_history | JSON | Level 1: Public/Internal |  |
| **internal_control_cases** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | follow_up_status | VARCHAR | Level 1: Public/Internal |  |
| **internal_control_cases** | last_reminder_at | TIMESTAMP | Level 1: Public/Internal |  |
| **internal_control_cases** | escalated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **activity_templates** | template_id | UUID | Level 1: Public/Internal |  |
| **activity_templates** | title | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | description | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | category | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | priority | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | activity_type | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | recurrence_pattern | JSONB | Level 1: Public/Internal |  |
| **activity_templates** | responsible_role | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | property_tags_required | JSONB | Level 1: Public/Internal |  |
| **activity_templates** | property_tags_excluded | JSONB | Level 1: Public/Internal |  |
| **activity_templates** | enabled | BOOLEAN | Level 1: Public/Internal |  |
| **activity_templates** | version | INTEGER | Level 1: Public/Internal |  |
| **activity_templates** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **activity_templates** | updated_at | TIMESTAMP | Level 1: Public/Internal |  |
| **activity_templates** | created_by_user_id | UUID | Level 3: Restricted (PII) |  |
| **activity_templates** | scope | VARCHAR | Level 1: Public/Internal |  |
| **activity_templates** | adoption_count | INTEGER | Level 1: Public/Internal |  |
| **checklist_templates** | template_id | UUID | Level 1: Public/Internal |  |
| **checklist_templates** | title | VARCHAR | Level 1: Public/Internal |  |
| **checklist_templates** | description | VARCHAR | Level 1: Public/Internal |  |
| **checklist_templates** | items | JSON | Level 1: Public/Internal |  |
| **checklist_templates** | category | VARCHAR | Level 1: Public/Internal |  |
| **checklist_templates** | frequency | VARCHAR | Level 1: Public/Internal |  |
| **checklist_templates** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **checklist_templates** | created_by_user_id | UUID | Level 3: Restricted (PII) |  |
| **checklist_templates** | scope | VARCHAR | Level 1: Public/Internal |  |
| **graph_entities** | id | UUID | Level 1: Public/Internal |  |
| **graph_entities** | name | VARCHAR | Level 3: Restricted (PII) |  |
| **graph_entities** | label | VARCHAR | Level 1: Public/Internal |  |
| **graph_entities** | description | TEXT | Level 1: Public/Internal |  |
| **graph_entities** | metadata | JSONB | Level 1: Public/Internal |  |
| **graph_entities** | embedding | NULL | Level 1: Public/Internal |  |
| **graph_entities** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
| **graph_relationships** | id | UUID | Level 1: Public/Internal |  |
| **graph_relationships** | source_id | UUID | Level 1: Public/Internal |  |
| **graph_relationships** | target_id | UUID | Level 1: Public/Internal |  |
| **graph_relationships** | relation_type | VARCHAR | Level 1: Public/Internal |  |
| **graph_relationships** | description | TEXT | Level 1: Public/Internal |  |
| **graph_relationships** | metadata | JSONB | Level 1: Public/Internal |  |
| **graph_relationships** | created_at | TIMESTAMP | Level 1: Public/Internal |  |
