import { fetchAPI } from '../api/client';
import { BUPLocationsResponse, BUPLocation, BUPLocationForMap } from '../types';

export async function getBUPLocations(region?: string): Promise<BUPLocationsResponse> {
    const query = region ? `?region=${region}` : '';
    return fetchAPI(`/bup-locations${query}`);
}

export async function getBUPLocationsNearbyMap(
    propertyIds: string[],
    maxDistanceKm: number = 30
): Promise<{ locations: BUPLocationForMap[]; total: number }> {
    if (propertyIds.length === 0) {
        return { locations: [], total: 0 };
    }
    const params = new URLSearchParams();
    params.set('property_ids', propertyIds.join(','));
    params.set('max_distance_km', String(maxDistanceKm));
    return fetchAPI(`/bup-locations/nearby-map?${params.toString()}`);
}

export async function getBUPLocationsWithNearestInstitution(region?: string): Promise<BUPLocationsResponse> {
    const query = region ? `?region=${region}` : '';
    return fetchAPI(`/bup-locations/with-nearest-institution${query}`);
}

export async function getNearbyPropertiesForBUPLocation(locationId: string, maxDistanceKm: number = 5.0): Promise<{ properties: any[] }> {
    return fetchAPI(`/bup-locations/${locationId}/nearby-properties?max_distance_km=${maxDistanceKm}`);
}


export async function geocodeBUPLocations(forceRefresh: boolean = false): Promise<{ geocoded: number, failed: number, skipped: number, message: string }> {
    return fetchAPI(`/bup-locations/geocode?force_refresh=${forceRefresh}`, { method: 'POST' });
}
