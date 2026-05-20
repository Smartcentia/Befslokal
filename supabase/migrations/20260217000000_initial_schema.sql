-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

--
-- PostgreSQL database dump
--


-- Dumped from database version 17.7 (bdd1736)
-- Dumped by pg_dump version 17.8 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;



--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--



--
-- Name: contractstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.contractstatus AS ENUM (
    'active',
    'terminated'
);


--
-- Name: qastatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.qastatus AS ENUM (
    'PENDING',
    'PASS',
    'FAIL'
);


--
-- Name: toolstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.toolstatus AS ENUM (
    'EXPERIMENTAL',
    'VERIFIED',
    'DEPRECATED'
);


--
-- Name: show_db_tree(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.show_db_tree() RETURNS TABLE(tree_structure text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- First show all databases
    RETURN QUERY
    SELECT ':file_folder: ' || datname || ' (DATABASE)'
    FROM pg_database 
    WHERE datistemplate = false;

    -- Then show current database structure
    RETURN QUERY
    WITH RECURSIVE 
    -- Get schemas
    schemas AS (
        SELECT 
            n.nspname AS object_name,
            1 AS level,
            n.nspname AS path,
            'SCHEMA' AS object_type
        FROM pg_namespace n
        WHERE n.nspname NOT LIKE 'pg_%' 
        AND n.nspname != 'information_schema'
    ),

    -- Get all objects (tables, views, functions, etc.)
    objects AS (
        SELECT 
            c.relname AS object_name,
            2 AS level,
            s.path || ' → ' || c.relname AS path,
            CASE c.relkind
                WHEN 'r' THEN 'TABLE'
                WHEN 'v' THEN 'VIEW'
                WHEN 'm' THEN 'MATERIALIZED VIEW'
                WHEN 'i' THEN 'INDEX'
                WHEN 'S' THEN 'SEQUENCE'
                WHEN 'f' THEN 'FOREIGN TABLE'
            END AS object_type
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN schemas s ON n.nspname = s.object_name
        WHERE c.relkind IN ('r','v','m','i','S','f')

        UNION ALL

        SELECT 
            p.proname AS object_name,
            2 AS level,
            s.path || ' → ' || p.proname AS path,
            'FUNCTION' AS object_type
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        JOIN schemas s ON n.nspname = s.object_name
    ),

    -- Combine schemas and objects
    combined AS (
        SELECT * FROM schemas
        UNION ALL
        SELECT * FROM objects
    )

    -- Final output with tree-like formatting
    SELECT 
        REPEAT('    ', level) || 
        CASE 
            WHEN level = 1 THEN '└── :open_file_folder: '
            ELSE '    └── ' || 
                CASE object_type
                    WHEN 'TABLE' THEN ':bar_chart: '
                    WHEN 'VIEW' THEN ':eye: '
                    WHEN 'MATERIALIZED VIEW' THEN ':newspaper: '
                    WHEN 'FUNCTION' THEN ':zap: '
                    WHEN 'INDEX' THEN ':mag: '
                    WHEN 'SEQUENCE' THEN ':1234: '
                    WHEN 'FOREIGN TABLE' THEN ':globe_with_meridians: '
                    ELSE ''
                END
        END || object_name || ' (' || object_type || ')'
    FROM combined
    ORDER BY path;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: action_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.action_recommendations (
    recommendation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    recommendation_type character varying(50) NOT NULL,
    target_entity_type character varying(50) NOT NULL,
    target_entity_id uuid NOT NULL,
    priority integer NOT NULL,
    estimated_impact_nok numeric(15,2) NOT NULL,
    description text NOT NULL,
    ai_rationale text,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: COLUMN action_recommendations.recommendation_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.recommendation_type IS 'Type: kpi_adjustment, renegotiation, consolidation, etc';


--
-- Name: COLUMN action_recommendations.target_entity_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.target_entity_type IS 'Entity type: contract, property';


--
-- Name: COLUMN action_recommendations.target_entity_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.target_entity_id IS 'ID of target contract/property';


--
-- Name: COLUMN action_recommendations.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.priority IS 'Priority 1-5 (1=highest cost savings)';


--
-- Name: COLUMN action_recommendations.estimated_impact_nok; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.estimated_impact_nok IS 'Estimated annual cost savings in NOK';


--
-- Name: COLUMN action_recommendations.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.description IS 'Human-readable action description';


--
-- Name: COLUMN action_recommendations.ai_rationale; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.ai_rationale IS 'GPT-4 explanation of why this recommendation was made';


--
-- Name: COLUMN action_recommendations.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.action_recommendations.status IS 'Status: pending, simulated, executed';


--
-- Name: activity_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_templates (
    template_id uuid NOT NULL,
    title character varying NOT NULL,
    description character varying,
    category character varying NOT NULL,
    priority character varying NOT NULL,
    activity_type character varying NOT NULL,
    recurrence_pattern jsonb NOT NULL,
    responsible_role character varying NOT NULL,
    property_tags_required jsonb,
    property_tags_excluded jsonb,
    enabled boolean NOT NULL,
    version integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by_user_id uuid,
    scope character varying DEFAULT 'system'::character varying,
    adoption_count integer DEFAULT 0
);


--
-- Name: ai_tools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_tools (
    id uuid NOT NULL,
    name character varying NOT NULL,
    description text NOT NULL,
    code text NOT NULL,
    dependencies text,
    requires_real_sk boolean,
    qa_status public.qastatus,
    qa_report text,
    status public.toolstatus,
    is_public boolean,
    is_pinned boolean,
    created_at timestamp without time zone,
    usage_count integer,
    last_used_at timestamp without time zone,
    vector_id character varying
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: api_call_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_call_logs (
    call_id uuid NOT NULL,
    service_name character varying(50),
    endpoint character varying(200),
    request_count integer,
    cost_estimate double precision,
    "timestamp" timestamp with time zone DEFAULT now(),
    response_time_ms integer,
    status_code integer,
    error_message character varying(500)
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    log_id uuid NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    action character varying NOT NULL,
    actor character varying,
    entity_type character varying,
    entity_id character varying,
    details json,
    severity character varying
);


--
-- Name: batch_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.batch_jobs (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_type character varying(50) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    progress integer DEFAULT 0 NOT NULL,
    total_items integer DEFAULT 0 NOT NULL,
    processed_items integer DEFAULT 0 NOT NULL,
    success_count integer DEFAULT 0 NOT NULL,
    failed_count integer DEFAULT 0 NOT NULL,
    config jsonb NOT NULL,
    property_ids jsonb,
    results jsonb,
    errors jsonb,
    created_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now(),
    error_message character varying(1000),
    error_details jsonb,
    worker_id character varying(100),
    CONSTRAINT check_batch_job_progress CHECK (((progress >= 0) AND (progress <= 100))),
    CONSTRAINT check_batch_job_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'running'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: bim_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bim_models (
    model_id uuid NOT NULL,
    property_id uuid NOT NULL,
    filename character varying NOT NULL,
    format character varying(10),
    upload_date timestamp with time zone DEFAULT now(),
    file_path character varying,
    status character varying(20)
);


--
-- Name: bim_objects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bim_objects (
    object_id uuid NOT NULL,
    model_id uuid NOT NULL,
    ifc_guid character varying(50),
    name character varying,
    type character varying(50),
    pos_x double precision,
    pos_y double precision,
    pos_z double precision,
    properties json,
    linked_component_id uuid
);


--
-- Name: building_components; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.building_components (
    component_id uuid NOT NULL,
    property_id uuid NOT NULL,
    name character varying NOT NULL,
    type character varying(50),
    location character varying,
    install_date timestamp with time zone,
    lifecycle_years integer,
    status character varying(20),
    technical_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    parent_id uuid,
    brick_class character varying,
    system_code character varying,
    ns3451_code character varying(20)
);


--
-- Name: centers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.centers (
    center_id character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    region character varying,
    emergency_contacts jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: checklist_executions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.checklist_executions (
    execution_id uuid NOT NULL,
    template_id uuid NOT NULL,
    property_id uuid NOT NULL,
    user_id uuid NOT NULL,
    status character varying,
    responses json,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: checklist_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.checklist_templates (
    template_id uuid NOT NULL,
    title character varying NOT NULL,
    description character varying,
    items json NOT NULL,
    category character varying NOT NULL,
    frequency character varying,
    created_at timestamp with time zone DEFAULT now(),
    created_by_user_id uuid,
    scope character varying DEFAULT 'system'::character varying
);


--
-- Name: context_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.context_history (
    context_id uuid NOT NULL,
    session_id character varying,
    user_id character varying,
    interaction_type character varying(50),
    content json,
    embedding json,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: contracts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contracts (
    contract_id uuid NOT NULL,
    unit_id uuid,
    party_id uuid,
    status public.contractstatus,
    category character varying,
    start_date date,
    end_date date,
    periods jsonb,
    amount jsonb,
    has_option boolean,
    option_deadline date,
    option_count_total integer,
    option_count_used integer,
    external_data jsonb,
    caretaker_cost double precision,
    cleaning_cost double precision,
    parking_cost double precision,
    card_reader_cost double precision,
    signed_at timestamp with time zone,
    terminated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    filename_region character varying(10),
    filename_type character varying(10),
    filename_number integer,
    elements text
);


--
-- Name: crisis_centers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.crisis_centers (
    center_id uuid NOT NULL,
    name character varying NOT NULL,
    location character varying,
    url character varying,
    latitude double precision,
    longitude double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: dashboard_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dashboard_metrics (
    metric_id integer NOT NULL,
    properties_count integer,
    contracts_count integer,
    risks_count integer,
    total_annual_rent double precision,
    total_maintenance_cost double precision,
    last_updated timestamp with time zone DEFAULT now(),
    critical_deviations integer DEFAULT 0,
    expiring_contracts integer DEFAULT 0,
    overdue_tasks integer DEFAULT 0
);


--
-- Name: dashboard_metrics_metric_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dashboard_metrics_metric_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dashboard_metrics_metric_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dashboard_metrics_metric_id_seq OWNED BY public.dashboard_metrics.metric_id;


--
-- Name: data_field_metadata; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_field_metadata (
    id integer NOT NULL,
    table_name character varying NOT NULL,
    column_name character varying NOT NULL,
    description text,
    classification_override character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: data_field_metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_field_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_field_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_field_metadata_id_seq OWNED BY public.data_field_metadata.id;


--
-- Name: email_verification_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_verification_codes (
    id character varying NOT NULL,
    email character varying NOT NULL,
    code_hash character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: environmental_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.environmental_data (
    env_data_id uuid NOT NULL,
    property_id uuid NOT NULL,
    air_quality_index double precision,
    noise_level_db double precision,
    pollution_sources json,
    contaminated_sites_nearby json,
    data_source character varying(50),
    fetched_at timestamp with time zone,
    expires_at timestamp with time zone
);


--
-- Name: external_api_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_api_data (
    api_data_id uuid NOT NULL,
    source_api character varying(50),
    entity_type character varying(50),
    entity_id character varying(100),
    data json,
    fetched_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone
);


--
-- Name: external_risk_errors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_risk_errors (
    error_id uuid DEFAULT gen_random_uuid() NOT NULL,
    property_id uuid NOT NULL,
    source character varying(50) NOT NULL,
    error_type character varying(50) NOT NULL,
    error_message character varying(1000) NOT NULL,
    error_details jsonb,
    http_status_code integer,
    url character varying(500),
    latitude double precision,
    longitude double precision,
    retry_count integer DEFAULT 0 NOT NULL,
    resolved character varying(10) DEFAULT 'false'::character varying NOT NULL,
    resolved_at timestamp with time zone,
    resolved_by character varying(100),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: file_meta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file_meta (
    file_id uuid NOT NULL,
    contract_id uuid,
    path character varying NOT NULL,
    sha256 character varying(64),
    file_type character varying(20),
    content_type character varying(100),
    tags character varying[],
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: forecast_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forecast_cache (
    forecast_id uuid DEFAULT gen_random_uuid() NOT NULL,
    property_id uuid,
    forecast_type character varying(50) NOT NULL,
    parameters jsonb NOT NULL,
    result jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: COLUMN forecast_cache.property_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.forecast_cache.property_id IS 'Property ID (nullable for portfolio-wide forecasts)';


--
-- Name: COLUMN forecast_cache.forecast_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.forecast_cache.forecast_type IS 'Type: cash_flow, cost_forecast, monte_carlo';


--
-- Name: COLUMN forecast_cache.parameters; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.forecast_cache.parameters IS 'Forecast parameters (months_ahead, kpi_adjustment, etc)';


--
-- Name: COLUMN forecast_cache.result; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.forecast_cache.result IS 'Full forecast data with P10/P50/P90';


--
-- Name: COLUMN forecast_cache.expires_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.forecast_cache.expires_at IS 'Auto-delete after this timestamp (24h TTL)';


--
-- Name: gdpr_anonymization_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gdpr_anonymization_logs (
    log_id uuid NOT NULL,
    entity_type character varying(50),
    entity_id character varying,
    original_pii_type character varying(50),
    action character varying(20),
    "timestamp" timestamp with time zone DEFAULT now()
);


--
-- Name: gdpr_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gdpr_requests (
    request_id uuid NOT NULL,
    user_id character varying NOT NULL,
    request_type character varying(50) NOT NULL,
    status character varying(20),
    details json,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- Name: generated_tools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generated_tools (
    tool_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    python_code text NOT NULL,
    sql_pattern text,
    status character varying(50),
    source_log_ids jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    version integer
);


--
-- Name: geological_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.geological_data (
    geo_data_id uuid NOT NULL,
    property_id uuid NOT NULL,
    bedrock_type character varying(100),
    soil_type character varying(100),
    groundwater_depth double precision,
    landslide_risk character varying(20),
    quickclay_risk integer,
    seismic_zone integer,
    data_source character varying(50),
    raw_data json,
    fetched_at timestamp with time zone,
    expires_at timestamp with time zone
);


--
-- Name: gl_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.gl_transactions (
    transaction_id uuid NOT NULL,
    property_id uuid,
    region_code character varying(10),
    region_name character varying(100),
    department_code character varying(20),
    department_name character varying(200),
    dim2_code character varying(20),
    dim2_name character varying(200),
    purpose_code character varying(20),
    purpose_name character varying(200),
    account_code character varying(20),
    account_name character varying(200),
    ba_code character varying(10),
    ba_name character varying(100),
    supplier_id character varying(20),
    supplier_name character varying(200),
    invoice_number character varying(50),
    amount numeric(15,2),
    period character varying(6),
    state_account character varying(20),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    is_synthetic boolean DEFAULT false NOT NULL,
    data_source character varying(100)
);


--
-- Name: graph_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.graph_entities (
    id uuid NOT NULL,
    name character varying NOT NULL,
    label character varying NOT NULL,
    description text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: infrastructure_costs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.infrastructure_costs (
    id integer NOT NULL,
    service_name character varying(50) NOT NULL,
    collection_date timestamp without time zone DEFAULT now() NOT NULL,
    raw_metrics jsonb,
    estimated_cost_usd numeric(10,2),
    active_time_seconds integer,
    cpu_used_seconds integer,
    storage_gb numeric(10,2),
    bandwidth_gb numeric(10,2),
    notes text,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: infrastructure_costs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.infrastructure_costs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: infrastructure_costs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.infrastructure_costs_id_seq OWNED BY public.infrastructure_costs.id;


--
-- Name: internal_control_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.internal_control_cases (
    case_id uuid NOT NULL,
    property_id uuid NOT NULL,
    risk_assessment_id uuid,
    assigned_user_id uuid,
    title character varying NOT NULL,
    description character varying,
    case_type character varying NOT NULL,
    status character varying,
    priority character varying,
    due_date timestamp with time zone,
    completed_at timestamp with time zone,
    notes character varying,
    process_state character varying,
    process_data json,
    process_history json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    follow_up_status character varying DEFAULT 'none'::character varying,
    last_reminder_at timestamp with time zone,
    escalated_at timestamp with time zone
);


--
-- Name: maintenance_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_records (
    record_id uuid NOT NULL,
    component_id uuid NOT NULL,
    date_performed timestamp with time zone DEFAULT now(),
    performed_by character varying,
    description character varying,
    cost integer,
    linked_work_order_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: mfa_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mfa_tokens (
    token character varying NOT NULL,
    user_email character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: natural_hazard_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.natural_hazard_events (
    event_id uuid NOT NULL,
    latitude double precision,
    longitude double precision,
    event_type character varying(50),
    event_date timestamp with time zone,
    severity character varying(20),
    description character varying,
    casualties integer,
    property_damage double precision,
    radius_affected_meters double precision,
    data_source character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: nextauth_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nextauth_accounts (
    id text NOT NULL,
    "userId" text NOT NULL,
    type text NOT NULL,
    provider text NOT NULL,
    "providerAccountId" text NOT NULL,
    refresh_token text,
    access_token text,
    expires_at integer,
    token_type text,
    scope text,
    id_token text,
    session_state text,
    expires_in integer,
    ext_expires_in integer
);


--
-- Name: nextauth_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nextauth_sessions (
    id text NOT NULL,
    "sessionToken" text NOT NULL,
    "userId" text NOT NULL,
    expires timestamp with time zone NOT NULL
);


--
-- Name: nextauth_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nextauth_users (
    id text NOT NULL,
    name text,
    email text,
    "emailVerified" timestamp with time zone,
    image text
);


--
-- Name: nextauth_verification_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nextauth_verification_tokens (
    identifier text NOT NULL,
    token text NOT NULL,
    expires timestamp with time zone NOT NULL
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    notification_id uuid NOT NULL,
    user_id uuid NOT NULL,
    title character varying NOT NULL,
    message character varying NOT NULL,
    notification_type character varying,
    related_entity_type character varying,
    related_entity_id uuid,
    is_read boolean,
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: ns3451_codes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ns3451_codes (
    code character varying(20) NOT NULL,
    name character varying(255) NOT NULL,
    level integer NOT NULL,
    parent_code character varying(20)
);


--
-- Name: parties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parties (
    party_id uuid NOT NULL,
    name character varying NOT NULL,
    orgnr character varying(9),
    contact_email character varying,
    contact_phone character varying,
    external_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: properties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties (
    property_id uuid NOT NULL,
    address character varying,
    postal_code character varying(4),
    city character varying,
    latitude double precision,
    longitude double precision,
    name character varying,
    usage character varying,
    total_area double precision,
    land_area double precision,
    construction_year integer,
    energy_label character varying,
    municipality character varying,
    municipality_code character varying,
    gnr integer,
    bnr integer,
    approved_places integer,
    region character varying,
    owner_name character varying,
    org_number character varying,
    regulation_type character varying,
    project_phase character varying,
    project_comments character varying,
    full_address jsonb,
    center_id character varying,
    crisis_contacts jsonb,
    external_data jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    geom public.geometry(Point,4326),
    id text DEFAULT ('befs_'::text || replace((gen_random_uuid())::text, '-'::text, ''::text)),
    organization_id text
);


--
-- Name: proximity_services; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.proximity_services (
    service_id uuid NOT NULL,
    property_id uuid NOT NULL,
    service_type character varying(50),
    service_name character varying(255),
    distance_meters double precision,
    travel_time_minutes double precision,
    latitude double precision,
    longitude double precision,
    rating double precision,
    address character varying(500),
    phone character varying(50),
    data_source character varying(50),
    fetched_at timestamp with time zone,
    expires_at timestamp with time zone
);


--
-- Name: query_library; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query_library (
    query_id uuid DEFAULT gen_random_uuid() NOT NULL,
    query_name character varying(255) NOT NULL,
    user_question_pattern text NOT NULL,
    sql_template text NOT NULL,
    description text,
    usage_count integer NOT NULL,
    success_rate double precision NOT NULL,
    avg_execution_time_ms integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by character varying(50) NOT NULL
);


--
-- Name: COLUMN query_library.query_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.query_name IS 'Descriptive name generated from SQL pattern';


--
-- Name: COLUMN query_library.user_question_pattern; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.user_question_pattern IS 'Example user question that this query answers';


--
-- Name: COLUMN query_library.sql_template; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.sql_template IS 'The SQL query template';


--
-- Name: COLUMN query_library.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.description IS 'Auto-generated description of what this query does';


--
-- Name: COLUMN query_library.usage_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.usage_count IS 'Number of times this query has been used';


--
-- Name: COLUMN query_library.success_rate; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.success_rate IS 'Success rate (0.0-1.0) of query executions';


--
-- Name: COLUMN query_library.avg_execution_time_ms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.avg_execution_time_ms IS 'Average execution time in milliseconds';


--
-- Name: COLUMN query_library.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.query_library.created_by IS 'auto (system-generated) or manual (human-created)';


--
-- Name: query_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query_logs (
    log_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_question text NOT NULL,
    generated_sql text,
    query_type character varying(50),
    execution_success boolean,
    result_count integer,
    execution_time_ms integer,
    error_message text,
    context_data jsonb,
    "timestamp" timestamp with time zone DEFAULT now(),
    user_id character varying(255),
    conversation_id character varying(255),
    confidence_score double precision,
    model_used character varying(50),
    cache_hit boolean DEFAULT false NOT NULL,
    retry_count integer DEFAULT 0 NOT NULL,
    parent_log_id uuid
);


--
-- Name: risk_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_assessments (
    assessment_id uuid NOT NULL,
    property_id uuid NOT NULL,
    assessment_date timestamp with time zone DEFAULT now(),
    methodology character varying(50),
    overall_risk_score double precision,
    risk_category character varying(20),
    assessed_by character varying,
    notes character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: risk_factors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.risk_factors (
    factor_id uuid NOT NULL,
    assessment_id uuid NOT NULL,
    category character varying(50),
    factor_name character varying(100),
    severity double precision,
    probability double precision,
    weight double precision,
    data_source character varying(100),
    raw_data json,
    calculated_score double precision,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: scenarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scenarios (
    scenario_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    base_forecast_id uuid,
    modifications jsonb NOT NULL,
    result_forecast jsonb NOT NULL,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: COLUMN scenarios.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.name IS 'User-friendly scenario name';


--
-- Name: COLUMN scenarios.description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.description IS 'Scenario description';


--
-- Name: COLUMN scenarios.base_forecast_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.base_forecast_id IS 'Reference to baseline forecast';


--
-- Name: COLUMN scenarios.modifications; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.modifications IS 'List of changes applied to baseline';


--
-- Name: COLUMN scenarios.result_forecast; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.result_forecast IS 'Resulting forecast after modifications';


--
-- Name: COLUMN scenarios.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.scenarios.created_by IS 'User ID or email';


--
-- Name: scheduled_activities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scheduled_activities (
    activity_id uuid NOT NULL,
    property_id uuid NOT NULL,
    title character varying NOT NULL,
    description character varying,
    activity_type character varying NOT NULL,
    category character varying NOT NULL,
    priority character varying NOT NULL,
    responsible_role character varying NOT NULL,
    assigned_user_id uuid,
    recurrence_rule jsonb NOT NULL,
    next_due_date timestamp with time zone NOT NULL,
    last_generated_at timestamp with time zone,
    enabled boolean NOT NULL,
    property_tags_required jsonb,
    property_tags_excluded jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by character varying
);


--
-- Name: sensor_anomalies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_anomalies (
    anomaly_id uuid NOT NULL,
    sensor_id uuid NOT NULL,
    detected_at timestamp with time zone DEFAULT now(),
    description character varying NOT NULL,
    severity character varying(20),
    status character varying(20),
    resolution character varying
);


--
-- Name: sensor_readings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings (
    reading_id uuid NOT NULL,
    sensor_id uuid NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    value double precision NOT NULL,
    unit character varying(20),
    raw_data json
);


--
-- Name: sensors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensors (
    sensor_id uuid NOT NULL,
    property_id uuid NOT NULL,
    name character varying NOT NULL,
    type character varying(50) NOT NULL,
    location character varying,
    status character varying(20),
    config json,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    session_id uuid NOT NULL,
    user_email character varying NOT NULL,
    access_token text NOT NULL,
    id_token text,
    refresh_token text,
    expires_at timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: socioeconomic_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socioeconomic_data (
    socio_data_id uuid DEFAULT gen_random_uuid() NOT NULL,
    property_id uuid NOT NULL,
    municipality_code character varying(10),
    crime_rate_per_1000 double precision,
    unemployment_rate double precision,
    median_income numeric(15,2),
    population_density double precision,
    demographic_profile jsonb,
    data_source character varying(50),
    year integer,
    fetched_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone
);


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    task_id uuid NOT NULL,
    order_id uuid,
    title character varying NOT NULL,
    action_type character varying(50),
    payload json,
    status character varying(50),
    result json,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone
);


--
-- Name: text_content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.text_content (
    text_id uuid NOT NULL,
    source_type character varying(50),
    content text,
    additional_metadata json,
    contract_id uuid,
    unit_id uuid,
    property_id uuid,
    source_index_id character varying(255),
    source_file character varying(500),
    chunk_index integer,
    category character varying(100),
    search_vector tsvector,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: units; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.units (
    unit_id uuid NOT NULL,
    property_id uuid NOT NULL,
    purpose character varying,
    area_sqm double precision,
    floor integer,
    zone_type character varying,
    uu_compliant boolean,
    uu_notes character varying,
    external_data json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_preferences (
    preference_id uuid NOT NULL,
    user_id character varying NOT NULL,
    language character varying(10),
    notifications json,
    ui_settings json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: user_property_association; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_property_association (
    user_id uuid,
    property_id uuid
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id uuid NOT NULL,
    email character varying NOT NULL,
    name character varying,
    role character varying(16),
    region character varying,
    email_verified boolean DEFAULT false NOT NULL,
    mfa_enabled boolean DEFAULT true NOT NULL,
    mfa_verified_at timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    id text DEFAULT ('befs_'::text || replace((gen_random_uuid())::text, '-'::text, ''::text)),
    organization_id text,
    updated_at timestamp with time zone DEFAULT now(),
    hashed_password character varying
);


--
-- Name: work_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.work_orders (
    order_id uuid NOT NULL,
    property_id uuid NOT NULL,
    description character varying NOT NULL,
    status character varying(50),
    priority character varying(20),
    assigned_to character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- Name: dashboard_metrics metric_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_metrics ALTER COLUMN metric_id SET DEFAULT nextval('public.dashboard_metrics_metric_id_seq'::regclass);


--
-- Name: data_field_metadata id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_metadata ALTER COLUMN id SET DEFAULT nextval('public.data_field_metadata_id_seq'::regclass);


--
-- Name: infrastructure_costs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.infrastructure_costs ALTER COLUMN id SET DEFAULT nextval('public.infrastructure_costs_id_seq'::regclass);


--
-- Name: action_recommendations action_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.action_recommendations
    ADD CONSTRAINT action_recommendations_pkey PRIMARY KEY (recommendation_id);


--
-- Name: activity_templates activity_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_templates
    ADD CONSTRAINT activity_templates_pkey PRIMARY KEY (template_id);


--
-- Name: ai_tools ai_tools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_tools
    ADD CONSTRAINT ai_tools_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_call_logs api_call_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_call_logs
    ADD CONSTRAINT api_call_logs_pkey PRIMARY KEY (call_id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (log_id);


--
-- Name: batch_jobs batch_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.batch_jobs
    ADD CONSTRAINT batch_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: bim_models bim_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bim_models
    ADD CONSTRAINT bim_models_pkey PRIMARY KEY (model_id);


--
-- Name: bim_objects bim_objects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bim_objects
    ADD CONSTRAINT bim_objects_pkey PRIMARY KEY (object_id);


--
-- Name: building_components building_components_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_components
    ADD CONSTRAINT building_components_pkey PRIMARY KEY (component_id);


--
-- Name: centers centers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.centers
    ADD CONSTRAINT centers_pkey PRIMARY KEY (center_id);


--
-- Name: checklist_executions checklist_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_executions
    ADD CONSTRAINT checklist_executions_pkey PRIMARY KEY (execution_id);


--
-- Name: checklist_templates checklist_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_templates
    ADD CONSTRAINT checklist_templates_pkey PRIMARY KEY (template_id);


--
-- Name: context_history context_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.context_history
    ADD CONSTRAINT context_history_pkey PRIMARY KEY (context_id);


--
-- Name: contracts contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_pkey PRIMARY KEY (contract_id);


--
-- Name: crisis_centers crisis_centers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.crisis_centers
    ADD CONSTRAINT crisis_centers_pkey PRIMARY KEY (center_id);


--
-- Name: dashboard_metrics dashboard_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_metrics
    ADD CONSTRAINT dashboard_metrics_pkey PRIMARY KEY (metric_id);


--
-- Name: data_field_metadata data_field_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_field_metadata
    ADD CONSTRAINT data_field_metadata_pkey PRIMARY KEY (id);


--
-- Name: email_verification_codes email_verification_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_verification_codes
    ADD CONSTRAINT email_verification_codes_pkey PRIMARY KEY (id);


--
-- Name: environmental_data environmental_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.environmental_data
    ADD CONSTRAINT environmental_data_pkey PRIMARY KEY (env_data_id);


--
-- Name: external_api_data external_api_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_api_data
    ADD CONSTRAINT external_api_data_pkey PRIMARY KEY (api_data_id);


--
-- Name: external_risk_errors external_risk_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_risk_errors
    ADD CONSTRAINT external_risk_errors_pkey PRIMARY KEY (error_id);


--
-- Name: file_meta file_meta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_meta
    ADD CONSTRAINT file_meta_pkey PRIMARY KEY (file_id);


--
-- Name: forecast_cache forecast_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_cache
    ADD CONSTRAINT forecast_cache_pkey PRIMARY KEY (forecast_id);


--
-- Name: gdpr_anonymization_logs gdpr_anonymization_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gdpr_anonymization_logs
    ADD CONSTRAINT gdpr_anonymization_logs_pkey PRIMARY KEY (log_id);


--
-- Name: gdpr_requests gdpr_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gdpr_requests
    ADD CONSTRAINT gdpr_requests_pkey PRIMARY KEY (request_id);


--
-- Name: generated_tools generated_tools_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_tools
    ADD CONSTRAINT generated_tools_name_key UNIQUE (name);


--
-- Name: generated_tools generated_tools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_tools
    ADD CONSTRAINT generated_tools_pkey PRIMARY KEY (tool_id);


--
-- Name: geological_data geological_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.geological_data
    ADD CONSTRAINT geological_data_pkey PRIMARY KEY (geo_data_id);


--
-- Name: gl_transactions gl_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gl_transactions
    ADD CONSTRAINT gl_transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: graph_entities graph_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.graph_entities
    ADD CONSTRAINT graph_entities_pkey PRIMARY KEY (id);


--
-- Name: infrastructure_costs infrastructure_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.infrastructure_costs
    ADD CONSTRAINT infrastructure_costs_pkey PRIMARY KEY (id);


--
-- Name: internal_control_cases internal_control_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.internal_control_cases
    ADD CONSTRAINT internal_control_cases_pkey PRIMARY KEY (case_id);


--
-- Name: maintenance_records maintenance_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_records
    ADD CONSTRAINT maintenance_records_pkey PRIMARY KEY (record_id);


--
-- Name: mfa_tokens mfa_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mfa_tokens
    ADD CONSTRAINT mfa_tokens_pkey PRIMARY KEY (token);


--
-- Name: natural_hazard_events natural_hazard_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.natural_hazard_events
    ADD CONSTRAINT natural_hazard_events_pkey PRIMARY KEY (event_id);


--
-- Name: nextauth_accounts nextauth_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_accounts
    ADD CONSTRAINT nextauth_accounts_pkey PRIMARY KEY (id);


--
-- Name: nextauth_accounts nextauth_accounts_provider_providerAccountId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_accounts
    ADD CONSTRAINT "nextauth_accounts_provider_providerAccountId_key" UNIQUE (provider, "providerAccountId");


--
-- Name: nextauth_sessions nextauth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_sessions
    ADD CONSTRAINT nextauth_sessions_pkey PRIMARY KEY (id);


--
-- Name: nextauth_sessions nextauth_sessions_sessionToken_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_sessions
    ADD CONSTRAINT "nextauth_sessions_sessionToken_key" UNIQUE ("sessionToken");


--
-- Name: nextauth_users nextauth_users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_users
    ADD CONSTRAINT nextauth_users_email_key UNIQUE (email);


--
-- Name: nextauth_users nextauth_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_users
    ADD CONSTRAINT nextauth_users_pkey PRIMARY KEY (id);


--
-- Name: nextauth_verification_tokens nextauth_verification_tokens_identifier_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_verification_tokens
    ADD CONSTRAINT nextauth_verification_tokens_identifier_token_key UNIQUE (identifier, token);


--
-- Name: nextauth_verification_tokens nextauth_verification_tokens_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_verification_tokens
    ADD CONSTRAINT nextauth_verification_tokens_token_key UNIQUE (token);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: ns3451_codes ns3451_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ns3451_codes
    ADD CONSTRAINT ns3451_codes_pkey PRIMARY KEY (code);


--
-- Name: parties parties_orgnr_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parties
    ADD CONSTRAINT parties_orgnr_key UNIQUE (orgnr);


--
-- Name: parties parties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parties
    ADD CONSTRAINT parties_pkey PRIMARY KEY (party_id);


--
-- Name: properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (property_id);


--
-- Name: proximity_services proximity_services_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proximity_services
    ADD CONSTRAINT proximity_services_pkey PRIMARY KEY (service_id);


--
-- Name: query_library query_library_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_library
    ADD CONSTRAINT query_library_pkey PRIMARY KEY (query_id);


--
-- Name: query_library query_library_query_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_library
    ADD CONSTRAINT query_library_query_name_key UNIQUE (query_name);


--
-- Name: query_logs query_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_logs
    ADD CONSTRAINT query_logs_pkey PRIMARY KEY (log_id);


--
-- Name: risk_assessments risk_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_assessments
    ADD CONSTRAINT risk_assessments_pkey PRIMARY KEY (assessment_id);


--
-- Name: risk_factors risk_factors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_factors
    ADD CONSTRAINT risk_factors_pkey PRIMARY KEY (factor_id);


--
-- Name: scenarios scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (scenario_id);


--
-- Name: scheduled_activities scheduled_activities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_activities
    ADD CONSTRAINT scheduled_activities_pkey PRIMARY KEY (activity_id);


--
-- Name: sensor_anomalies sensor_anomalies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomalies
    ADD CONSTRAINT sensor_anomalies_pkey PRIMARY KEY (anomaly_id);


--
-- Name: sensor_readings sensor_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings
    ADD CONSTRAINT sensor_readings_pkey PRIMARY KEY (reading_id);


--
-- Name: sensors sensors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_pkey PRIMARY KEY (sensor_id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (session_id);


--
-- Name: socioeconomic_data socioeconomic_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socioeconomic_data
    ADD CONSTRAINT socioeconomic_data_pkey PRIMARY KEY (socio_data_id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (task_id);


--
-- Name: text_content text_content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_content
    ADD CONSTRAINT text_content_pkey PRIMARY KEY (text_id);


--
-- Name: text_content text_content_source_index_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_content
    ADD CONSTRAINT text_content_source_index_id_key UNIQUE (source_index_id);


--
-- Name: units units_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_pkey PRIMARY KEY (unit_id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (preference_id);


--
-- Name: user_preferences user_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: work_orders work_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_pkey PRIMARY KEY (order_id);


--
-- Name: idx_contracts_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_contracts_end_date ON public.contracts USING btree (((external_data ->> 'end_date'::text)));


--
-- Name: idx_costs_collection_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_costs_collection_date ON public.infrastructure_costs USING btree (collection_date);


--
-- Name: idx_costs_service_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_costs_service_date ON public.infrastructure_costs USING btree (service_name, collection_date);


--
-- Name: idx_forecast_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_forecast_created ON public.forecast_cache USING btree (created_at);


--
-- Name: idx_forecast_expiry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_forecast_expiry ON public.forecast_cache USING btree (expires_at);


--
-- Name: idx_forecast_property; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_forecast_property ON public.forecast_cache USING btree (property_id);


--
-- Name: idx_forecast_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_forecast_type ON public.forecast_cache USING btree (forecast_type);


--
-- Name: idx_generated_tools_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_generated_tools_name ON public.generated_tools USING btree (name);


--
-- Name: idx_generated_tools_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_generated_tools_status ON public.generated_tools USING btree (status);


--
-- Name: idx_gl_account; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_account ON public.gl_transactions USING btree (account_code);


--
-- Name: idx_gl_amount; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_amount ON public.gl_transactions USING btree (amount);


--
-- Name: idx_gl_dept_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_dept_code ON public.gl_transactions USING btree (department_code);


--
-- Name: idx_gl_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_period ON public.gl_transactions USING btree (period);


--
-- Name: idx_gl_period_amount; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_period_amount ON public.gl_transactions USING btree (period, amount);


--
-- Name: idx_gl_period_v2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_period_v2 ON public.gl_transactions USING btree (period);


--
-- Name: idx_gl_property; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_property ON public.gl_transactions USING btree (property_id);


--
-- Name: idx_gl_property_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_property_period ON public.gl_transactions USING btree (property_id, period);


--
-- Name: idx_gl_supplier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_supplier ON public.gl_transactions USING btree (supplier_id);


--
-- Name: idx_gl_supplier_v2; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gl_supplier_v2 ON public.gl_transactions USING btree (supplier_id);


--
-- Name: idx_properties_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_properties_geom ON public.properties USING gist (geom);


--
-- Name: idx_properties_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_properties_name ON public.properties USING btree (name);


--
-- Name: idx_properties_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_properties_region ON public.properties USING btree (region);


--
-- Name: idx_query_library_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_library_created ON public.query_library USING btree (created_at);


--
-- Name: idx_query_library_question_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_library_question_search ON public.query_library USING gin (to_tsvector('norwegian'::regconfig, user_question_pattern));


--
-- Name: idx_query_library_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_library_success ON public.query_library USING btree (success_rate);


--
-- Name: idx_query_library_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_library_usage ON public.query_library USING btree (usage_count);


--
-- Name: idx_query_logs_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_logs_confidence ON public.query_logs USING btree (confidence_score);


--
-- Name: idx_query_logs_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_logs_model ON public.query_logs USING btree (model_used);


--
-- Name: idx_query_logs_query_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_logs_query_type ON public.query_logs USING btree (query_type);


--
-- Name: idx_query_logs_success; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_logs_success ON public.query_logs USING btree (execution_success);


--
-- Name: idx_query_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_query_logs_timestamp ON public.query_logs USING btree ("timestamp");


--
-- Name: idx_recommendations_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendations_created ON public.action_recommendations USING btree (created_at);


--
-- Name: idx_recommendations_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendations_entity ON public.action_recommendations USING btree (target_entity_type, target_entity_id);


--
-- Name: idx_recommendations_impact; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendations_impact ON public.action_recommendations USING btree (estimated_impact_nok);


--
-- Name: idx_recommendations_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendations_priority ON public.action_recommendations USING btree (priority);


--
-- Name: idx_recommendations_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recommendations_status ON public.action_recommendations USING btree (status);


--
-- Name: idx_scenarios_base_forecast; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scenarios_base_forecast ON public.scenarios USING btree (base_forecast_id);


--
-- Name: idx_scenarios_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scenarios_created_at ON public.scenarios USING btree (created_at);


--
-- Name: idx_scenarios_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scenarios_created_by ON public.scenarios USING btree (created_by);


--
-- Name: idx_text_content_contract_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_text_content_contract_id ON public.text_content USING btree (contract_id);


--
-- Name: idx_text_content_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_text_content_embedding ON public.text_content USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_text_content_search_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_text_content_search_vector ON public.text_content USING gin (search_vector);


--
-- Name: idx_text_content_source_index_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_text_content_source_index_id ON public.text_content USING btree (source_index_id);


--
-- Name: ix_ai_tools_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_tools_name ON public.ai_tools USING btree (name);


--
-- Name: ix_api_call_logs_service_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_call_logs_service_name ON public.api_call_logs USING btree (service_name);


--
-- Name: ix_api_call_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_call_logs_timestamp ON public.api_call_logs USING btree ("timestamp");


--
-- Name: ix_batch_jobs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_batch_jobs_created_at ON public.batch_jobs USING btree (created_at);


--
-- Name: ix_batch_jobs_job_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_batch_jobs_job_type ON public.batch_jobs USING btree (job_type);


--
-- Name: ix_batch_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_batch_jobs_status ON public.batch_jobs USING btree (status);


--
-- Name: ix_batch_jobs_worker_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_batch_jobs_worker_id ON public.batch_jobs USING btree (worker_id);


--
-- Name: ix_checklist_executions_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_checklist_executions_property_id ON public.checklist_executions USING btree (property_id);


--
-- Name: ix_checklist_executions_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_checklist_executions_template_id ON public.checklist_executions USING btree (template_id);


--
-- Name: ix_checklist_executions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_checklist_executions_user_id ON public.checklist_executions USING btree (user_id);


--
-- Name: ix_contracts_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_category ON public.contracts USING btree (category);


--
-- Name: ix_contracts_elements; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_elements ON public.contracts USING btree (elements);


--
-- Name: ix_contracts_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_end_date ON public.contracts USING btree (end_date);


--
-- Name: ix_contracts_filename_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_contracts_filename_unique ON public.contracts USING btree (filename_region, filename_type, filename_number) WHERE ((filename_region IS NOT NULL) AND (filename_type IS NOT NULL) AND (filename_number IS NOT NULL));


--
-- Name: ix_contracts_party_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_party_id ON public.contracts USING btree (party_id);


--
-- Name: ix_contracts_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_start_date ON public.contracts USING btree (start_date);


--
-- Name: ix_contracts_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_status ON public.contracts USING btree (status);


--
-- Name: ix_contracts_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_contracts_unit_id ON public.contracts USING btree (unit_id);


--
-- Name: ix_crisis_centers_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_crisis_centers_name ON public.crisis_centers USING btree (name);


--
-- Name: ix_dashboard_metrics_metric_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dashboard_metrics_metric_id ON public.dashboard_metrics USING btree (metric_id);


--
-- Name: ix_data_field_metadata_column_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_field_metadata_column_name ON public.data_field_metadata USING btree (column_name);


--
-- Name: ix_data_field_metadata_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_field_metadata_id ON public.data_field_metadata USING btree (id);


--
-- Name: ix_data_field_metadata_table_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_data_field_metadata_table_name ON public.data_field_metadata USING btree (table_name);


--
-- Name: ix_email_verification_codes_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_verification_codes_email ON public.email_verification_codes USING btree (email);


--
-- Name: ix_email_verification_codes_email_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_verification_codes_email_expires ON public.email_verification_codes USING btree (email, expires_at);


--
-- Name: ix_environmental_data_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_environmental_data_property_id ON public.environmental_data USING btree (property_id);


--
-- Name: ix_external_api_data_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_api_data_entity ON public.external_api_data USING btree (entity_type, entity_id);


--
-- Name: ix_external_api_data_fetched_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_api_data_fetched_at ON public.external_api_data USING btree (fetched_at);


--
-- Name: ix_external_api_data_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_api_data_source ON public.external_api_data USING btree (source_api);


--
-- Name: ix_external_risk_errors_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_risk_errors_created_at ON public.external_risk_errors USING btree (created_at);


--
-- Name: ix_external_risk_errors_error_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_risk_errors_error_type ON public.external_risk_errors USING btree (error_type);


--
-- Name: ix_external_risk_errors_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_risk_errors_property_id ON public.external_risk_errors USING btree (property_id);


--
-- Name: ix_external_risk_errors_resolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_risk_errors_resolved ON public.external_risk_errors USING btree (resolved);


--
-- Name: ix_external_risk_errors_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_external_risk_errors_source ON public.external_risk_errors USING btree (source);


--
-- Name: ix_file_meta_contract_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_file_meta_contract_id ON public.file_meta USING btree (contract_id);


--
-- Name: ix_file_meta_sha256; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_file_meta_sha256 ON public.file_meta USING btree (sha256);


--
-- Name: ix_gdpr_requests_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_gdpr_requests_user_id ON public.gdpr_requests USING btree (user_id);


--
-- Name: ix_geological_data_landslide_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_geological_data_landslide_risk ON public.geological_data USING btree (landslide_risk);


--
-- Name: ix_geological_data_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_geological_data_property_id ON public.geological_data USING btree (property_id);


--
-- Name: ix_graph_entities_label; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_graph_entities_label ON public.graph_entities USING btree (label);


--
-- Name: ix_graph_entities_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_graph_entities_name ON public.graph_entities USING btree (name);


--
-- Name: ix_internal_control_cases_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_internal_control_cases_property_id ON public.internal_control_cases USING btree (property_id);


--
-- Name: ix_mfa_tokens_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mfa_tokens_user_email ON public.mfa_tokens USING btree (user_email);


--
-- Name: ix_mfa_tokens_user_email_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mfa_tokens_user_email_expires ON public.mfa_tokens USING btree (user_email, expires_at);


--
-- Name: ix_natural_hazard_events_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_natural_hazard_events_date ON public.natural_hazard_events USING btree (event_date);


--
-- Name: ix_natural_hazard_events_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_natural_hazard_events_location ON public.natural_hazard_events USING btree (latitude, longitude);


--
-- Name: ix_natural_hazard_events_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_natural_hazard_events_severity ON public.natural_hazard_events USING btree (severity);


--
-- Name: ix_natural_hazard_events_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_natural_hazard_events_type ON public.natural_hazard_events USING btree (event_type);


--
-- Name: ix_ns3451_codes_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ns3451_codes_code ON public.ns3451_codes USING btree (code);


--
-- Name: ix_parties_orgnr; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_parties_orgnr ON public.parties USING btree (orgnr);


--
-- Name: ix_properties_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_properties_property_id ON public.properties USING btree (property_id);


--
-- Name: ix_proximity_services_distance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_proximity_services_distance ON public.proximity_services USING btree (distance_meters);


--
-- Name: ix_proximity_services_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_proximity_services_expires_at ON public.proximity_services USING btree (expires_at);


--
-- Name: ix_proximity_services_property_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_proximity_services_property_expires ON public.proximity_services USING btree (property_id, expires_at);


--
-- Name: ix_proximity_services_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_proximity_services_property_id ON public.proximity_services USING btree (property_id);


--
-- Name: ix_proximity_services_service_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_proximity_services_service_type ON public.proximity_services USING btree (service_type);


--
-- Name: ix_risk_assessments_assessment_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_assessments_assessment_date ON public.risk_assessments USING btree (assessment_date);


--
-- Name: ix_risk_assessments_property_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_assessments_property_date ON public.risk_assessments USING btree (property_id, assessment_date DESC);


--
-- Name: ix_risk_assessments_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_assessments_property_id ON public.risk_assessments USING btree (property_id);


--
-- Name: ix_risk_assessments_risk_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_assessments_risk_category ON public.risk_assessments USING btree (risk_category);


--
-- Name: ix_risk_factors_assessment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_factors_assessment_id ON public.risk_factors USING btree (assessment_id);


--
-- Name: ix_risk_factors_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_factors_category ON public.risk_factors USING btree (category);


--
-- Name: ix_risk_factors_factor_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_risk_factors_factor_name ON public.risk_factors USING btree (factor_name);


--
-- Name: ix_scheduled_activities_next_due_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scheduled_activities_next_due_date ON public.scheduled_activities USING btree (next_due_date);


--
-- Name: ix_scheduled_activities_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scheduled_activities_property_id ON public.scheduled_activities USING btree (property_id);


--
-- Name: ix_sessions_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_user_email ON public.sessions USING btree (user_email);


--
-- Name: ix_socioeconomic_data_municipality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_socioeconomic_data_municipality ON public.socioeconomic_data USING btree (municipality_code);


--
-- Name: ix_socioeconomic_data_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_socioeconomic_data_property_id ON public.socioeconomic_data USING btree (property_id);


--
-- Name: ix_socioeconomic_data_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_socioeconomic_data_year ON public.socioeconomic_data USING btree (year);


--
-- Name: ix_text_content_contract_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_text_content_contract_id ON public.text_content USING btree (contract_id);


--
-- Name: ix_text_content_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_text_content_created_at ON public.text_content USING btree (created_at);


--
-- Name: ix_text_content_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_text_content_property_id ON public.text_content USING btree (property_id);


--
-- Name: ix_text_content_source_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_text_content_source_type ON public.text_content USING btree (source_type);


--
-- Name: ix_text_content_unit_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_text_content_unit_id ON public.text_content USING btree (unit_id);


--
-- Name: ix_units_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_units_property_id ON public.units USING btree (property_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_user_id ON public.users USING btree (user_id);


--
-- Name: bim_models bim_models_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bim_models
    ADD CONSTRAINT bim_models_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: bim_objects bim_objects_linked_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bim_objects
    ADD CONSTRAINT bim_objects_linked_component_id_fkey FOREIGN KEY (linked_component_id) REFERENCES public.building_components(component_id);


--
-- Name: bim_objects bim_objects_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bim_objects
    ADD CONSTRAINT bim_objects_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.bim_models(model_id);


--
-- Name: building_components building_components_ns3451_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_components
    ADD CONSTRAINT building_components_ns3451_code_fkey FOREIGN KEY (ns3451_code) REFERENCES public.ns3451_codes(code);


--
-- Name: building_components building_components_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_components
    ADD CONSTRAINT building_components_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.building_components(component_id);


--
-- Name: building_components building_components_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_components
    ADD CONSTRAINT building_components_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: checklist_executions checklist_executions_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_executions
    ADD CONSTRAINT checklist_executions_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: checklist_executions checklist_executions_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_executions
    ADD CONSTRAINT checklist_executions_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.checklist_templates(template_id);


--
-- Name: checklist_executions checklist_executions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.checklist_executions
    ADD CONSTRAINT checklist_executions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: contracts contracts_party_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_party_id_fkey FOREIGN KEY (party_id) REFERENCES public.parties(party_id);


--
-- Name: contracts contracts_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.units(unit_id);


--
-- Name: environmental_data environmental_data_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.environmental_data
    ADD CONSTRAINT environmental_data_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: external_risk_errors external_risk_errors_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_risk_errors
    ADD CONSTRAINT external_risk_errors_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: file_meta file_meta_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_meta
    ADD CONSTRAINT file_meta_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(contract_id);


--
-- Name: properties fk_properties_center_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT fk_properties_center_id FOREIGN KEY (center_id) REFERENCES public.centers(center_id);


--
-- Name: query_logs fk_query_logs_parent; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_logs
    ADD CONSTRAINT fk_query_logs_parent FOREIGN KEY (parent_log_id) REFERENCES public.query_logs(log_id) ON DELETE SET NULL;


--
-- Name: forecast_cache forecast_cache_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecast_cache
    ADD CONSTRAINT forecast_cache_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id) ON DELETE CASCADE;


--
-- Name: geological_data geological_data_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.geological_data
    ADD CONSTRAINT geological_data_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: gl_transactions gl_transactions_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.gl_transactions
    ADD CONSTRAINT gl_transactions_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id) ON DELETE SET NULL;


--
-- Name: internal_control_cases internal_control_cases_assigned_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.internal_control_cases
    ADD CONSTRAINT internal_control_cases_assigned_user_id_fkey FOREIGN KEY (assigned_user_id) REFERENCES public.users(user_id);


--
-- Name: internal_control_cases internal_control_cases_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.internal_control_cases
    ADD CONSTRAINT internal_control_cases_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: internal_control_cases internal_control_cases_risk_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.internal_control_cases
    ADD CONSTRAINT internal_control_cases_risk_assessment_id_fkey FOREIGN KEY (risk_assessment_id) REFERENCES public.risk_assessments(assessment_id);


--
-- Name: maintenance_records maintenance_records_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_records
    ADD CONSTRAINT maintenance_records_component_id_fkey FOREIGN KEY (component_id) REFERENCES public.building_components(component_id);


--
-- Name: nextauth_accounts nextauth_accounts_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_accounts
    ADD CONSTRAINT nextauth_accounts_userid_fkey FOREIGN KEY ("userId") REFERENCES public.nextauth_users(id) ON DELETE CASCADE;


--
-- Name: nextauth_sessions nextauth_sessions_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nextauth_sessions
    ADD CONSTRAINT nextauth_sessions_userid_fkey FOREIGN KEY ("userId") REFERENCES public.nextauth_users(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: ns3451_codes ns3451_codes_parent_code_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ns3451_codes
    ADD CONSTRAINT ns3451_codes_parent_code_fkey FOREIGN KEY (parent_code) REFERENCES public.ns3451_codes(code);


--
-- Name: properties properties_center_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_center_id_fkey FOREIGN KEY (center_id) REFERENCES public.centers(center_id);


--
-- Name: proximity_services proximity_services_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.proximity_services
    ADD CONSTRAINT proximity_services_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: risk_assessments risk_assessments_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_assessments
    ADD CONSTRAINT risk_assessments_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: risk_factors risk_factors_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.risk_factors
    ADD CONSTRAINT risk_factors_assessment_id_fkey FOREIGN KEY (assessment_id) REFERENCES public.risk_assessments(assessment_id);


--
-- Name: scenarios scenarios_base_forecast_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scenarios
    ADD CONSTRAINT scenarios_base_forecast_id_fkey FOREIGN KEY (base_forecast_id) REFERENCES public.forecast_cache(forecast_id) ON DELETE SET NULL;


--
-- Name: scheduled_activities scheduled_activities_assigned_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_activities
    ADD CONSTRAINT scheduled_activities_assigned_user_id_fkey FOREIGN KEY (assigned_user_id) REFERENCES public.users(user_id);


--
-- Name: scheduled_activities scheduled_activities_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_activities
    ADD CONSTRAINT scheduled_activities_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: sensor_anomalies sensor_anomalies_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_anomalies
    ADD CONSTRAINT sensor_anomalies_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id);


--
-- Name: sensor_readings sensor_readings_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings
    ADD CONSTRAINT sensor_readings_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id);


--
-- Name: sensors sensors_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: socioeconomic_data socioeconomic_data_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socioeconomic_data
    ADD CONSTRAINT socioeconomic_data_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id) ON DELETE CASCADE;


--
-- Name: tasks tasks_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.work_orders(order_id);


--
-- Name: units units_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: user_property_association user_property_association_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_property_association
    ADD CONSTRAINT user_property_association_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- Name: user_property_association user_property_association_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_property_association
    ADD CONSTRAINT user_property_association_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: work_orders work_orders_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.work_orders
    ADD CONSTRAINT work_orders_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(property_id);


--
-- PostgreSQL database dump complete
--


