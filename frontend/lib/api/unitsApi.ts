import { fetchAPI } from './client';

export interface Unit {
    unit_id: string;
    property_id: string;
    name: string;
    unit_id_erp?: string;
    unit_short_type?: string;
    floor?: number;
    area_sqm?: number;
    area_common_sqm?: number;
    area_total_sqm?: number;
    status?: string;
    created_at?: string;
    updated_at?: string;
}

export interface CreateUnitPayload {
    property_id: string;
    name: string;
    unit_id_erp?: string;
    unit_short_type?: string;
    floor?: number;
    area_sqm?: number;
    area_common_sqm?: number;
    area_total_sqm?: number;
    status?: string;
}

export interface UpdateUnitPayload {
    name?: string;
    unit_id_erp?: string;
    unit_short_type?: string;
    floor?: number;
    area_sqm?: number;
    area_common_sqm?: number;
    area_total_sqm?: number;
    status?: string;
}

export interface GetUnitsParams {
    property_id?: string;
    skip?: number;
    limit?: number;
}

export async function getUnits(params: GetUnitsParams = {}): Promise<Unit[]> {
    const searchParams = new URLSearchParams();
    if (params.property_id) searchParams.set('property_id', params.property_id);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<Unit[]>(`/units${query ? `?${query}` : ''}`);
}

export async function createUnit(payload: CreateUnitPayload): Promise<Unit> {
    return fetchAPI<Unit>('/units', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateUnit(unitId: string, payload: UpdateUnitPayload): Promise<Unit> {
    return fetchAPI<Unit>(`/units/${unitId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteUnit(unitId: string): Promise<void> {
    await fetchAPI(`/units/${unitId}`, { method: 'DELETE' });
}

export const unitsApi = {
    getAll: getUnits,
    create: createUnit,
    update: updateUnit,
    delete: deleteUnit,
    getByProperty: (propertyId: string) => getUnits({ property_id: propertyId }),
};
