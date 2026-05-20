import { fetchAPI } from './client';

// ---------------------------------------------------------------------------
// TypeScript interfaces
// ---------------------------------------------------------------------------

export interface Building {
    building_id: string;
    property_id: string;
    name: string;
    building_code?: string | null;
    year_built?: number | null;
    building_type?: string | null;
    floors_above_ground?: number | null;
    floors_below_ground?: number | null;
    total_area_sqm?: number | null;
    description?: string | null;
    floors?: Floor[];
}

export interface Floor {
    floor_id: string;
    building_id: string;
    floor_number: number;
    name?: string | null;
    area_sqm?: number | null;
    spaces?: Space[];
    units?: UnitRef[];
}

export interface Space {
    space_id: string;
    floor_id?: string | null;
    property_id: string;
    unit_id?: string | null;
    name: string;
    space_type?: string | null;
    area_sqm?: number | null;
    description?: string | null;
}

export interface UnitRef {
    unit_id: string;
    address?: string | null;
    purpose?: string | null;
    area_sqm?: number | null;
    floor?: number | null;
    building_id?: string | null;
    floor_id?: string | null;
}

export interface PropertyStructure {
    property_id: string;
    buildings: Array<Building & { floors: Array<Floor & { spaces: Space[]; units: UnitRef[] }> }>;
    unassigned_units: UnitRef[];
}

// Create/update payloads
export interface CreateBuildingPayload {
    property_id: string;
    name: string;
    building_code?: string;
    year_built?: number;
    building_type?: string;
    floors_above_ground?: number;
    floors_below_ground?: number;
    total_area_sqm?: number;
    description?: string;
}

export interface UpdateBuildingPayload {
    name?: string;
    building_code?: string;
    year_built?: number;
    building_type?: string;
    floors_above_ground?: number;
    floors_below_ground?: number;
    total_area_sqm?: number;
    description?: string;
}

export interface CreateFloorPayload {
    floor_number: number;
    name?: string;
    area_sqm?: number;
}

export interface UpdateFloorPayload {
    floor_number?: number;
    name?: string;
    area_sqm?: number;
}

export interface CreateSpacePayload {
    property_id: string;
    name: string;
    space_type?: string;
    area_sqm?: number;
    description?: string;
    unit_id?: string;
}

export interface UpdateSpacePayload {
    name?: string;
    space_type?: string;
    area_sqm?: number;
    description?: string;
    unit_id?: string;
}

// ---------------------------------------------------------------------------
// Building endpoints
// ---------------------------------------------------------------------------

export async function getBuildings(propertyId: string): Promise<Building[]> {
    return fetchAPI<Building[]>(`/buildings?property_id=${propertyId}`);
}

export async function createBuilding(payload: CreateBuildingPayload): Promise<Building> {
    return fetchAPI<Building>('/buildings', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateBuilding(buildingId: string, payload: UpdateBuildingPayload): Promise<Building> {
    return fetchAPI<Building>(`/buildings/${buildingId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteBuilding(buildingId: string): Promise<void> {
    await fetchAPI(`/buildings/${buildingId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Floor endpoints
// ---------------------------------------------------------------------------

export async function getFloors(buildingId: string): Promise<Floor[]> {
    return fetchAPI<Floor[]>(`/buildings/${buildingId}/floors`);
}

export async function createFloor(buildingId: string, payload: CreateFloorPayload): Promise<Floor> {
    return fetchAPI<Floor>(`/buildings/${buildingId}/floors`, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateFloor(floorId: string, payload: UpdateFloorPayload): Promise<Floor> {
    return fetchAPI<Floor>(`/floors/${floorId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteFloor(floorId: string): Promise<void> {
    await fetchAPI(`/floors/${floorId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Space endpoints
// ---------------------------------------------------------------------------

export async function getSpaces(floorId: string): Promise<Space[]> {
    return fetchAPI<Space[]>(`/floors/${floorId}/spaces`);
}

export async function createSpace(floorId: string, payload: CreateSpacePayload): Promise<Space> {
    return fetchAPI<Space>(`/floors/${floorId}/spaces`, {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateSpace(spaceId: string, payload: UpdateSpacePayload): Promise<Space> {
    return fetchAPI<Space>(`/spaces/${spaceId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteSpace(spaceId: string): Promise<void> {
    await fetchAPI(`/spaces/${spaceId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Full property structure tree
// ---------------------------------------------------------------------------

export async function getPropertyStructure(propertyId: string): Promise<PropertyStructure> {
    return fetchAPI<PropertyStructure>(`/properties/${propertyId}/structure`);
}

// ---------------------------------------------------------------------------
// Convenience object
// ---------------------------------------------------------------------------

export const buildingApi = {
    // Buildings
    getBuildings,
    createBuilding,
    updateBuilding,
    deleteBuilding,
    // Floors
    getFloors,
    createFloor,
    updateFloor,
    deleteFloor,
    // Spaces
    getSpaces,
    createSpace,
    updateSpace,
    deleteSpace,
    // Structure
    getPropertyStructure,
};
