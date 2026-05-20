import { fetchAPI } from './client';

export interface BupLocation {
    location_id: string;
    name: string;
    address?: string;
    municipality?: string;
    county?: string;
    lat?: number;
    lon?: number;
    type?: string;
    contact_info?: {
        phone?: string;
        email?: string;
        website?: string;
    };
    services?: string[];
    created_at?: string;
    updated_at?: string;
}

export interface NearbyProperty {
    property_id: string;
    name: string;
    address: string;
    distance_km: number;
    travel_time_minutes?: number;
}

export interface NearbyMapResult {
    center: { lat: number; lon: number };
    radius_km: number;
    bup_locations: Array<BupLocation & { distance_km: number }>;
    properties: Array<NearbyProperty>;
}

export interface BupWithNearestInstitution {
    bup: BupLocation;
    nearest_institution?: {
        property_id: string;
        name: string;
        distance_km: number;
    };
}

export async function getBupLocations(params: {
    municipality?: string;
    county?: string;
    skip?: number;
    limit?: number;
} = {}): Promise<BupLocation[]> {
    const searchParams = new URLSearchParams();
    if (params.municipality) searchParams.set('municipality', params.municipality);
    if (params.county) searchParams.set('county', params.county);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<BupLocation[]>(`/bup-locations/bup-locations${query ? `?${query}` : ''}`);
}

export async function getNearbyMap(
    lat: number,
    lon: number,
    radiusKm: number = 50
): Promise<NearbyMapResult> {
    const params = new URLSearchParams({
        lat: String(lat),
        lon: String(lon),
        radius_km: String(radiusKm),
    });
    return fetchAPI<NearbyMapResult>(`/bup-locations/nearby-map?${params}`);
}

export async function getNearbyProperties(
    locationId: string,
    radiusKm: number = 50
): Promise<NearbyProperty[]> {
    return fetchAPI<NearbyProperty[]>(
        `/bup-locations/bup-locations/${locationId}/nearby-properties?radius_km=${radiusKm}`
    );
}

export async function getBupWithNearestInstitution(): Promise<BupWithNearestInstitution[]> {
    return fetchAPI<BupWithNearestInstitution[]>('/bup-locations/with-nearest-institution');
}

export async function geocodeBupLocations(forceRefresh: boolean = false): Promise<{
    status: string;
    geocoded: number;
    failed: number;
}> {
    return fetchAPI(`/bup-locations/bup-locations/geocode?force_refresh=${forceRefresh}`, {
        method: 'POST',
    });
}

export const bupLocationsApi = {
    getAll: getBupLocations,
    nearbyMap: getNearbyMap,
    nearbyProperties: getNearbyProperties,
    withNearestInstitution: getBupWithNearestInstitution,
    geocode: geocodeBupLocations,
};
