// Types for BUP Locations (and potential others if missing)

export interface BUPLocation {
    id: string;
    adresse: string;
    telefon?: string;
    region: string;
    region_key: string;
    latitude?: number;
    longitude?: number;
    nearest_institution?: {
        property_id: string;
        address: string;
        postal_code: string;
        city: string;
        property_name?: string;
        latitude: number;
        longitude: number;
        distance_km: number;
        distance_meters: number;
    };
    nearest_institution_distance_km?: number;
}

export interface BUPLocationsResponse {
    total: number;
    locations: BUPLocation[];
    metadata?: Record<string, any>;
}

export interface BUPLocationForMap {
    id: string;
    navn: string;
    adresse?: string;
    latitude: number;
    longitude: number;
    nearest_property_distance_km: number;
}

export interface Property {
    id?: string;
    property_id: string;
    name?: string;
    address: string;
    city: string;
    postal_code?: string;
    region?: string;
    usage?: string;
    type?: string;
    municipality?: string;
    municipality_code?: string;
    latitude?: number;
    longitude?: number;
    risk_level?: RiskLevel | string;
    managers?: Array<{ user_id: string; name: string; email: string }>;

    // Additional fields from propertyService
    external_data?: any;
    total_area?: number;
    area?: number;
    construction_year?: number;
    year_built?: number;
    energy_label?: string;
    gnr?: string | number;
    bnr?: string | number;

    // e-don2 / BIRK (avdeling, institusjon, kostnadsfordeling)
    unit_id_erp?: string;
    unit_short_type?: string;   // Enhetskorttype: Avdeling | Barnevernsinstitusjon
    unit_type_derived?: string;  // Enhetstype (Utledet): Barnevernsinstitusjon | Institusjonsavdeling | Omsorgssenter
    parent_unit_id_erp?: string; // TilhørighetEnhetID fra e-don2 (organisatorisk forelder)
    parent_property_id?: string; // Resolved UUID for the parent property
    affiliation?: string;        // Tilhørighet (tekst-navn på forelder/driftsoperatør)
    department_code?: string;   // Avdelingens koststed (1:1 med institusjon)
    department_name?: string;   // Navn på avdeling (1:1 med institusjon)
    approved_places?: number;    // Antall G/K - plasser
    budgeted_places?: number;   // Antall budsjetterte plasser
    legal_basis?: string;
    regulation_type?: string;    // Årlig prisjusteringsfaktaktor (KPI)
    ownership_type?: string;
    closed_at?: string | null;

    // KPI-justert husleie 2026
    husleie_2026?: number | null;          // KPI-justert husleie 2026 (Alternativ A, SSB)
    husleie_2026_kpi_note?: string | null; // f.eks. "+24.2% (KPI*100%)"
    gl_rent_2025?: number | null;          // Faktisk husleie 2025 fra GL
    contract_rent_nok?: number | null;     // Avtalefestet husleie kr/år (startpris)

    /** Avledet fra API: Bufdir-miniatyrbilde eller ekstern image_url */
    bufdir_image_path?: string | null;
    /** Avledet: primær kontraktsmotpart (leietaker/leverandør) */
    primary_lease_party_name?: string | null;
}

/** Bufdir-data i external_data.bufdir (fetch + scrape + enrich) */
export interface PropertyBufdirGalleryItem {
    url?: string;
    local_path?: string | null;
    caption?: string | null;
    credit?: string | null;
    alt?: string | null;
}

export interface PropertyBufdirSubsection {
    title?: string;
    body_html?: string;
}

export interface PropertyBufdirContentSection {
    title?: string;
    intro_html?: string;
    subsections?: PropertyBufdirSubsection[];
}

export interface PropertyBufdirData {
    bufdir_id?: number | string;
    institution_name?: string;
    bufdir_name?: string;
    name?: string;
    description?: string;
    legal_bases?: string[];
    owner_type?: string;
    bufdir_url?: string;
    email?: string;
    phone?: string;
    location?: string;
    placement_type?: string;
    capacity?: number;
    summary?: {
        raw_bullets?: string[];
        ownership?: string;
        placement_type?: string;
        capacity?: number;
        place?: string;
    };
    contact_postal_address?: string;
    contact_rich_html?: string;
    content_sections?: PropertyBufdirContentSection[];
    gallery?: PropertyBufdirGalleryItem[];
    image_url?: string;
    image_path?: string;
    source_detail_url?: string;
    scraped_at?: string;
    detail_parse_error?: string | null;
}

export interface RecentActivityItem {
    id: string;
    type: string;
    description?: string;
    text?: string;
    timestamp?: string;
    time?: string;
    icon?: string;
    color?: string;
    entity_id?: string;
    entity_type?: string;
}
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type Region = 'Sør' | 'Vest' | 'Øst' | 'Midt' | 'Nord';

export interface SystemStatus {
    database?: string;
    api_gateway?: string;
    nve_integration?: string;
    last_check?: string;
    status?: 'healthy' | 'degraded' | 'down';
    components?: Array<{
        name: string;
        status: 'ok' | 'warning' | 'error';
        message?: string;
    }>;
    last_updated?: string;
}

export interface DashboardStatsData {
    properties_count: number;
    contracts_count: number;
    total_area: number;
    occupancy_rate: number;
    properties?: number;
    contracts?: number;
    risks?: number;
    users?: number;
    total_annual_rent?: number;
    total_maintenance_cost?: number;
    /** Sum bokførte kostnader fra kontant_2026 (jan-apr), ekskl. husleie. */
    gl_andre_kostnader_2026?: number;
    /** Sum vedlikehold fra kontant_2025 (økonomi regnskap). */
    total_vedlikehold_2025?: number;
    critical_deviations?: number;
    expiring_contracts?: number;
}

export interface GLTransaction {
    transaction_id: string;
    property_id?: string;
    region_code?: string;
    region_name?: string;
    department_code?: string;
    department_name?: string;
    purpose_code?: string;
    purpose_name?: string;
    account_code?: string;
    account_name?: string;
    supplier_id?: string;
    supplier_name?: string;
    invoice_number?: string;
    description?: string;
    amount: number;
    period?: string;
    year?: number;
    month?: number;
    transaction_date?: string;
    category?: string;
}

export interface TransactionListResponse {
    items: GLTransaction[];
    total: number;
    page: number;
    size: number;
    total_pages: number;
}
