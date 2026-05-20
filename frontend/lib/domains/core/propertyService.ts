import { fetchAPI } from '../../api/client';
import { Property } from '../../types';

// Re-export Property to maintain backward compatibility
export type { Property };

export const propertyService = {
    getAll: async (skip: number = 0, limit: number = 50): Promise<Property[]> => {
        try {
            return await fetchAPI(`/properties?skip=${skip}&limit=${limit}`);
        } catch (error) {
            console.warn("Failed to fetch properties", error);
            return [];
        }
    },

    getById: async (id: string): Promise<Property> => {
        return fetchAPI(`/properties/${id}`);
    },

    getDetailView: async (id: string, includeRisk: boolean = false): Promise<any> => {
        return fetchAPI(`/properties/${id}/detail-view?include_risk=${includeRisk}`);
    },

    // Proximity Services
    getProximityServices: async (id: string, type?: string): Promise<ProximityServiceItem[]> => {
        const query = type ? `?service_type=${type}` : '';
        return fetchAPI(`/properties/${id}/proximity-services${query}`);
    },

    refreshProximityServices: async (id: string, force: boolean = false): Promise<{ count: number, services: ProximityServiceItem[] }> => {
        return fetchAPI(`/properties/${id}/proximity-services/refresh?force_refresh=${force}`, {
            method: 'POST'
        });
    },

    /** Oppdater proximity for alle eiendommer som har koordinater (admin/batch). */
    refreshAllProximity: async (): Promise<{ updated: number; total_with_coords: number; errors: { property_id: string; error: string }[] }> => {
        return fetchAPI('/properties/refresh-all-proximity', { method: 'POST' });
    },

    getAccessibilitySummary: async (id: string): Promise<AccessibilitySummary> => {
        return fetchAPI(`/properties/${id}/accessibility-summary`);
    }
};

export interface ProximityServiceItem {
    service_id: string;
    property_id: string;
    service_type: string;
    service_name: string;
    distance_meters: number;
    travel_time_minutes?: number;
    latitude: number;
    longitude: number;
    rating?: number;
    address?: string;
    phone?: string;
    data_source: string;
}

export interface AccessibilitySummary {
    total_services: number;
    service_counts: Record<string, number>;
    nearest_by_type: Record<string, {
        name: string;
        distance_meters: number;
        travel_time_minutes?: number;
    }>;
    average_distance: number;
    average_travel_time: number;
}
