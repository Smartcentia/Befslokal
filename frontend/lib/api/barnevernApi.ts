import { fetchAPI } from "./client";

export interface BarnevernInstitution {
    property_id: string;
    name: string;
    region: string;
    approved_places: number;
    budgeted_places: number;
    annual_cost_2025: number;
}

export interface BarnevernRegionAgg {
    approved_places: number;
    budgeted_places: number;
    annual_cost: number;
    count: number;
}

export interface BarnevernPlacesResponse {
    institutions: BarnevernInstitution[];
    by_region: Record<string, BarnevernRegionAgg>;
    total_approved_places: number;
    total_count: number;
    ssb_reference?: unknown;
}

export interface RegionSimulation {
    region: string;
    approved_places: number;
    brukte_plasser: number;
    ubrukte_plasser: number;
    kost_brukte: number;
    kost_ubrukte: number;
    total_kostnad: number;
    annual_cost_region: number;
}

export interface SimulationResult {
    year: number;
    usage_pct: number;
    egenandel_maaned: number;
    egenandel_aar: number;
    by_region: RegionSimulation[];
    total_approved_places: number;
    total_brukte: number;
    total_ubrukte: number;
    total_kost_brukte: number;
    total_kost_ubrukte: number;
    total_kostnad: number;
    ssb_data?: unknown;
}

export async function getBarnevernPlaces(): Promise<BarnevernPlacesResponse> {
    return fetchAPI<BarnevernPlacesResponse>("/barnevern/places");
}

export async function simulateBarnevernCost(
    params?: { year?: number; usage_pct?: number; include_ssb?: boolean }
): Promise<SimulationResult> {
    const search = new URLSearchParams();
    if (params?.year != null) search.set("year", String(params.year));
    if (params?.usage_pct != null) search.set("usage_pct", String(params.usage_pct));
    if (params?.include_ssb != null) search.set("include_ssb", String(params.include_ssb));
    const qs = search.toString();
    return fetchAPI<SimulationResult>(`/barnevern/simulate${qs ? `?${qs}` : ""}`);
}
