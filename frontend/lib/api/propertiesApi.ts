import { fetchAPI } from './client';
import { RiskLevel, Region, Property, RecentActivityItem } from '../types';
export type { Property };

// Using global Property type from ../types

export async function healthCheck(): Promise<{ status: string }> {
    console.warn("healthCheck stub called");
    return { status: 'ok' };
}

export interface AccessibilitySummary {
    id: string;
    property_id: string;
    service_counts: Record<string, number>;
    nearest_by_type: Record<string, any>;
}

export async function analyzeRisk(propertyId: string): Promise<{ status: string }> {
    console.warn("analyzeRisk stub called for:", propertyId);
    return { status: 'success' };
}

export interface GetPropertiesParams {
    usage?: string;
    search?: string;
    unit_short_type?: string;
    order_by?: string;
    order_dir?: "asc" | "desc";
    include_discontinued?: boolean;
    source_coverage?: "complete" | "missing" | "all";
    /** Filtrer på region (kort format: Nord, Midt-Norge, Vest, Sør, Øst, Bufdir) */
    region?: string;
    include_risk?: boolean;
}

export interface PropertySuggestion {
    property_id: string;
    name: string;
    address: string;
}

/**
 * Fetch list of properties
 */
export async function getProperties(
    skip: number = 0,
    limit: number = 50,
    params?: GetPropertiesParams
): Promise<Property[]> {
    try {
        const searchParams = new URLSearchParams();
        searchParams.set("skip", String(skip));
        searchParams.set("limit", String(limit));
        if (params?.usage) searchParams.set("usage", params.usage);
        if (params?.search) searchParams.set("search", params.search);
        if (params?.unit_short_type) searchParams.set("unit_short_type", params.unit_short_type);
        if (params?.order_by) searchParams.set("order_by", params.order_by);
        if (params?.order_dir) searchParams.set("order_dir", params.order_dir);
        if (typeof params?.include_discontinued === "boolean") {
            searchParams.set("include_discontinued", String(params.include_discontinued));
        }
        if (params?.source_coverage) {
            searchParams.set("source_coverage", params.source_coverage);
        }
        if (params?.region) {
            searchParams.set("region", params.region);
        }
        if (typeof params?.include_risk === "boolean") {
            searchParams.set("include_risk", String(params.include_risk));
        }

        // Use fetchAPI to call Python backend (/properties), which has proper access control and manager data
        return await fetchAPI<Property[]>(`/properties?${searchParams.toString()}`);
    } catch (error) {
        console.error("Failed to fetch properties:", error);
        return [];
    }
}

/** Hent lette eiendomsmarkører for kart (reduserer last vs. getProperties). */
export async function getPropertyMapMarkers(
    limit: number = 500,
    includeDiscontinued: boolean = false,
    sourceCoverage: "complete" | "missing" | "all" = "complete"
): Promise<Property[]> {
    try {
        return await fetchAPI<Property[]>(`/properties/map-markers?limit=${limit}&include_discontinued=${includeDiscontinued}&source_coverage=${sourceCoverage}`);
    } catch (error) {
        console.error("Failed to fetch map markers:", error);
        return [];
    }
}

export interface PropertyAnnualCost {
    property_annual_cost_id: string;
    year: number;
    kpi_adjusted_rent: number | null;
    internal_maintenance: number | null;
    common_costs: number | null;
    energy_costs: number | null;
    heating_costs: number | null;
    cleaning_costs: number | null;
    parking_rent: number | null;
    caretaker_cost: number | null;
    card_reader_cost: number | null;
    other_costs: Record<string, number> | null;
}

/** Henter kostnadsdata (PropertyAnnualCost) for en eiendom og et gitt år. */
export async function getPropertyAnnualCosts(propertyId: string, year: number): Promise<PropertyAnnualCost[]> {
    try {
        return await fetchAPI<PropertyAnnualCost[]>(`/properties/${propertyId}/annual-costs?year=${year}`);
    } catch {
        return [];
    }
}

export interface FinancialSummary {
    year: number;
    faktisk_husleie: number;
    andre_kostnader: number;
    totalt: number;
    kategorier: Record<string, number>;
    har_data: boolean;
    lonn?: {
        har_data: boolean;
        is_partial_year: boolean;
        faste_stillinger: number;
        vikarer: number;
        arbeidsgiveravgift: number;
        totalt: number;
    };
}

/** Henter aggregert GL-oversikt (faktisk husleie + bokførte kostnader) for et gitt år. */
export async function getFinancialSummary(propertyId: string, year: number): Promise<FinancialSummary | null> {
    try {
        return await fetchAPI<FinancialSummary>(`/properties/${propertyId}/financial-summary?year=${year}`);
    } catch {
        return null;
    }
}

export interface GLFinancialBulk {
    year: number;
    by_property: Record<string, { faktisk_husleie: number; andre_kostnader: number; totalt: number }>;
    /** Transaksjoner uten property_id (kostnader uten eiendom) – inkluderes i total Bokført husleie */
    orphan_faktisk_husleie?: number;
    orphan_andre_kostnader?: number;
}

/** Henter GL-finansdata for alle eiendommer i ett bulk-kall. */
export async function getGLFinancialBulk(year: number): Promise<GLFinancialBulk | null> {
    try {
        return await fetchAPI<GLFinancialBulk>(`/properties/gl-financial-bulk?year=${year}`);
    } catch {
        return null;
    }
}

/** Returnerer total GL-beløp per år (alle år i databasen). */
export async function getGLTotalsByYear(): Promise<{ by_year: Record<string, number> } | null> {
    try {
        return await fetchAPI<{ by_year: Record<string, number> }>(`/properties/gl-totals-by-year`);
    } catch {
        return null;
    }
}

/** Global GL per kontonavn (kostnadskilde-analyse). */
export interface GLAccountTotals {
    year: number;
    total_amount: number;
    total_faktisk_husleie: number;
    total_andre_kostnader: number;
    account_count: number;
    top_accounts: Array<{ account_name: string; amount: number; is_lease: boolean }>;
}

export async function getGLAccountTotals(year: number, limit = 30): Promise<GLAccountTotals | null> {
    try {
        return await fetchAPI<GLAccountTotals>(`/properties/gl-account-totals?year=${year}&limit=${limit}`);
    } catch {
        return null;
    }
}

export interface PropertyWithoutCosts {
    property_id: string;
    name: string;
    address: string;
    region: string;
    unit_id_erp: string | null;
    unit_short_type: string | null;
}

/** Henter eiendommer som mangler kostnadsdata (GL) for valgt år. */
export async function getPropertiesWithoutCosts(year: number): Promise<{ year: number; properties: PropertyWithoutCosts[]; count: number } | null> {
    try {
        return await fetchAPI<{ year: number; properties: PropertyWithoutCosts[]; count: number }>(`/properties/without-costs?year=${year}`);
    } catch {
        return null;
    }
}

export interface DiscontinuedProperty {
    property_id: string;
    name: string;
    address: string;
    region: string;
    unit_id_erp: string | null;
    unit_short_type: string | null;
    has_costs_in_year: boolean;
    total_cost_in_year: number;
}

/** Henter avviklede eiendommer: ikke i budsjett for valgt år og uten GL-kostnader i valgt kostnadsår. */
export async function getDiscontinuedProperties(
    budgetYear: number,
    costYear?: number
): Promise<{
    budget_year: number;
    cost_year: number;
    budget_available: boolean;
    properties: DiscontinuedProperty[];
    count: number;
} | null> {
    try {
        const params = new URLSearchParams({ budget_year: String(budgetYear) });
        if (typeof costYear === "number") {
            params.set("cost_year", String(costYear));
        }
        return await fetchAPI(`/properties/discontinued-properties?${params.toString()}`);
    } catch {
        return null;
    }
}

export interface CostCenterWithoutProperty {
    department_code: string;
    department_name: string;
    total: number;
    transaction_count: number;
}

/** Henter koststeder fra GL som har kostnader men ingen tilknyttet eiendom. */
export async function getCostsWithoutProperty(year: number): Promise<{
    year: number;
    cost_centers: CostCenterWithoutProperty[];
    count: number;
    total_amount: number;
} | null> {
    try {
        return await fetchAPI(`/properties/costs-without-property?year=${year}`);
    } catch {
        return null;
    }
}

/** Pivot-struktur for kostnader uten eiendom (kompatibel med procurement pivot) */
export interface CostsWithoutPropertyPivot {
    year: number;
    regions: string[];
    groups: Array<{
        group: string;
        categories: Array<{
            key: string;
            label: string;
            rows: Array<{
                department_code: string;
                department_name: string;
                institution: string;
                by_region: Record<string, number>;
                total: number;
            }>;
            totals_by_region: Record<string, number>;
            grand_total: number;
        }>;
    }>;
}

/** Henter pivot over koststeder uten eiendom (koststed × region). */
export async function getCostsWithoutPropertyPivot(
    year: number
): Promise<CostsWithoutPropertyPivot | null> {
    try {
        return await fetchAPI(`/properties/costs-without-property-pivot?year=${year}`);
    } catch {
        return null;
    }
}

export interface OrphanTransaction {
    transaction_id: string | null;
    period: string;
    account_name: string;
    supplier_name: string;
    dim2_name: string;
    amount: number;
    invoice_number: string;
}

/** Pivot-struktur for kontraktsdata: region × utleier med kontraktsleie. */
export interface ContractsPivot {
    regions: string[];
    utleiere: string[];
    rows: Array<{ region: string; by_utleier: Record<string, number>; total: number }>;
    totals_by_utleier: Record<string, number>;
    grand_total: number;
}

/** Innkjøpsanalyse husleie per eiendom (Kontraktsfestet fra CSV). */
export interface InnkjoepsanalyseHusleie {
    year: number;
    by_property: Record<string, { by_region: Record<string, number>; aggregert: number }>;
    total: number;
}

/** Henter Kontraktsfestet husleie fra Innkjøpsanalyse-CSV. */
export async function getInnkjøpsanalyseHusleie(year: number): Promise<InnkjoepsanalyseHusleie | null> {
    try {
        return await fetchAPI<InnkjoepsanalyseHusleie>(`/properties/innkjoepsanalyse-husleie?year=${year}`);
    } catch {
        return null;
    }
}

/** Total kost per region og kategori fra Innkjøpsanalyse-import. */
export interface TotalKostPerRegion {
    year: number;
    by_category: Record<string, {
        by_region_totals: Record<string, number>;
        by_region_radetikett: Record<string, { radetikett: string; amount: number }[]>;
    }>;
}

/** Henter godkjente eiendommer og avdelinger (for UTGÅTT-badge). */
export async function getGodkjenteEiendommer(): Promise<string[]> {
    try {
        return await fetchAPI<string[]>(`/properties/godkjente-eiendommer`);
    } catch {
        return [];
    }
}

/** Henter Total kost per region (regionnivå + enhetsfordeling). */
export async function getTotalKostPerRegion(year: number): Promise<TotalKostPerRegion | null> {
    try {
        return await fetchAPI<TotalKostPerRegion>(`/properties/total-kost-per-region?year=${year}`);
    } catch {
        return null;
    }
}

/** Henter pivot over kontrakter (region × utleier). */
export async function getContractsPivot(): Promise<ContractsPivot | null> {
    try {
        return await fetchAPI<ContractsPivot>("/properties/contracts-pivot");
    } catch {
        return null;
    }
}

/** Rå kontraktsrecord for client-side pivot. */
export interface ContractsPivotRawRecord {
    region: string;
    utleier: string;
    eiendom: string;
    amount_per_year: number;
}

/** Henter rå kontraktsdata for dynamisk pivot. */
export async function getContractsPivotRaw(): Promise<{ records: ContractsPivotRawRecord[] } | null> {
    try {
        return await fetchAPI<{ records: ContractsPivotRawRecord[] }>("/properties/contracts-pivot-raw");
    } catch {
        return null;
    }
}

/** Henter enkelttransaksjoner for et koststed uten eiendom. */
export async function getOrphanTransactions(
    departmentCode: string,
    year: number,
    skip = 0,
    limit = 100
): Promise<{
    department_code: string;
    year: number;
    transactions: OrphanTransaction[];
    total_count: number;
    total_amount: number;
    skip: number;
    limit: number;
} | null> {
    try {
        return await fetchAPI(
            `/properties/orphan-transactions?department_code=${encodeURIComponent(departmentCode)}&year=${year}&skip=${skip}&limit=${limit}`
        );
    } catch {
        return null;
    }
}

/** Henter autofullføring-forslag basert på søkestreng. */
export async function getPropertySuggestions(q: string): Promise<PropertySuggestion[]> {
    if (!q || q.length < 2) return [];
    try {
        return await fetchAPI<PropertySuggestion[]>(`/properties/suggestions?q=${encodeURIComponent(q)}`);
    } catch {
        return [];
    }
}

/** Henter alle distinkte eiendomstyper (usage) fra API. */
export async function getPropertyTypes(): Promise<string[]> {
    try {
        return await fetchAPI<string[]>("/properties/usage-types") || [];
    } catch (error) {
        console.error("Failed to fetch property types:", error);
        return [];
    }
}

/** Henter alle distinkte enhetstyper (unit_short_type) fra API. */
export async function getPropertyUnitShortTypes(): Promise<string[]> {
    try {
        return await fetchAPI<string[]>("/properties/unit-short-types") || [];
    } catch (error) {
        console.error("Failed to fetch unit short types:", error);
        return [];
    }
}

/** Henter alle avdelinger (underenheter med unit_short_type=Avdeling). */
export async function getAvdelinger(includeDiscontinued: boolean = false): Promise<Property[]> {
    try {
        return await getProperties(0, 500, {
            unit_short_type: "Avdeling",
            include_discontinued: includeDiscontinued,
            source_coverage: "all", // Hent alle avdelinger uavhengig av datadekning
        });
    } catch {
        return [];
    }
}

export const propertyService = {
    fetch: async (id: string) => {
        return await fetchAPI(`/properties/${id}`);
    },
    getDetailView: async (id: string, includeRelations: boolean = true) => {
        try {
            // Use the dedicated backend endpoint which exists
            console.log(`[getDetailView] Fetching /properties/${id}/detail-view`);
            return await fetchAPI(`/properties/${id}/detail-view?include_risk=${includeRelations}`);
        } catch (error) {
            console.error("Failed to fetch property details:", error);
            // Fallback to basic fetch if detail view fails
            try {
                const property = await fetchAPI(`/properties/${id}`);
                return {
                    property,
                    units: [],
                    contracts: [],
                    parties: [],
                    latest_risk_assessment: null
                };
            } catch (fallbackError) {
                return null;
            }
        }
    },
    getAll: async (skip: number = 0, limit: number = 100) => {
        return await getProperties(skip, limit);
    },
    getProximityServices: async (id: string) => {
        try {
            return await fetchAPI(`/properties/${id}/proximity-services`);
        } catch (error) {
            console.error("Failed to fetch proximity services:", error);
            return [];
        }
    },
    refreshProximityServices: async (id: string, force: boolean = false) => {
        return fetchAPI(`/properties/${id}/proximity-services/refresh?force_refresh=${force}`, {
            method: 'POST'
        });
    }
};


// Using global RecentActivityItem type from ../types

export async function getPropertyRecentActivity(limit: number = 10): Promise<RecentActivityItem[]> {
    try {
        return await fetchAPI<RecentActivityItem[]>(`/dashboard/recent-activity?limit=${limit}`);
    } catch (error) {
        console.error("Failed to fetch recent activity:", error);
        return [];
    }
}

export async function getBUPLocations(): Promise<{ locations: any[] }> {
    try {
        return await fetchAPI('/bup-locations/bup-locations');
    } catch (error) {
        console.error("Failed to fetch BUP locations:", error);
        return { locations: [] };
    }
}

// --- GL-kostnader (løpende kostnader fra regnskapssystem) ---

export interface GLCostsVendor {
    name: string;
    total: number;
}

export interface GLCostsAccount {
    code: string;
    name: string;
    total: number;
    vendors: GLCostsVendor[];
}

export interface GLCostsSubcategory {
    name: string;
    total: number;
    accounts: GLCostsAccount[];
}

export interface GLCostsYear {
    total: number;
    subcategories: GLCostsSubcategory[];
}

export interface GLCosts {
    available_years: number[];
    by_year: Record<string, GLCostsYear>;
}

/** Henter GL-kostnader per eiendom gruppert per år → underkategori → konto → leverandør. */
export async function getGLCosts(propertyId: string, year?: number): Promise<GLCosts | null> {
    try {
        const url = year
            ? `/properties/${propertyId}/gl-costs?year=${year}`
            : `/properties/${propertyId}/gl-costs`;
        return await fetchAPI<GLCosts>(url);
    } catch {
        return null;
    }
}

export interface GLCostsDim4Row {
    dim4_kode: string | null;
    dim4_navn: string;
    total: number;
}

export interface GLCostsByDim4 {
    property_id: string;
    year: number;
    total: number;
    rows: GLCostsDim4Row[];
}

/** GL aggregert per Dim4 (kapittelpost / tildelingsbrev) for ett år. */
export async function getGLCostsByDim4(propertyId: string, year: number): Promise<GLCostsByDim4 | null> {
    try {
        return await fetchAPI<GLCostsByDim4>(
            `/properties/${propertyId}/gl-costs-by-dim4?year=${year}`
        );
    } catch {
        return null;
    }
}

