import { fetchAPI } from './client';

export interface Center {
    center_id: string;
    name: string;
    type: string;
    address?: string;
    municipality?: string;
    county?: string;
    lat?: number;
    lon?: number;
    phone?: string;
    email?: string;
    website?: string;
    capacity?: number;
    services?: string[];
    external_data?: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
}

export interface ImportCentersResult {
    status: string;
    imported: number;
    updated: number;
    failed: number;
    errors?: string[];
}

export async function getCenters(params: {
    type?: string;
    municipality?: string;
    county?: string;
    skip?: number;
    limit?: number;
} = {}): Promise<Center[]> {
    const searchParams = new URLSearchParams();
    if (params.type) searchParams.set('type', params.type);
    if (params.municipality) searchParams.set('municipality', params.municipality);
    if (params.county) searchParams.set('county', params.county);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<Center[]>(`/centers/centers${query ? `?${query}` : ''}`);
}

export async function getCenter(centerId: string): Promise<Center> {
    return fetchAPI<Center>(`/centers/centers/${centerId}`);
}

export async function importCenters(data: Array<Partial<Center>>): Promise<ImportCentersResult> {
    return fetchAPI<ImportCentersResult>('/centers/centers/import', {
        method: 'POST',
        body: JSON.stringify({ centers: data }),
    });
}

export const centersApi = {
    getAll: getCenters,
    getById: getCenter,
    import: importCenters,
};
