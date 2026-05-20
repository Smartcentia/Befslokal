import { fetchAPI } from './client';

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

export interface Organisation {
    org_id: string;
    name: string;
    region_code: string | null;
    org_nr: string | null;
    contact_email: string | null;
    budget_target_nok: number | null;
    is_active: boolean;
}

export interface OrganisationCreate {
    name: string;
    region_code?: string | null;
    org_nr?: string | null;
    contact_email?: string | null;
    budget_target_nok?: number | null;
    is_active?: boolean;
}

export interface OrganisationUpdate {
    name?: string;
    region_code?: string | null;
    org_nr?: string | null;
    contact_email?: string | null;
    budget_target_nok?: number | null;
    is_active?: boolean;
}

export interface OrganisationProperty {
    property_id: string;
    name: string | null;
    address: string | null;
    city: string | null;
    region: string | null;
}

export interface OrganisationUser {
    user_id: string;
    email: string;
    name: string | null;
    role: string;
    region: string | null;
}

export interface OrganisationKPI {
    property_count: number;
    user_count: number;
    active_contracts: number;
    total_monthly_rent_nok: number;
    budget_target_nok: number | null;
    compliance_rate: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function listOrganisations(): Promise<Organisation[]> {
    return fetchAPI<Organisation[]>('/organisations');
}

export async function getOrganisation(orgId: string): Promise<Organisation> {
    return fetchAPI<Organisation>(`/organisations/${orgId}`);
}

export async function createOrganisation(payload: OrganisationCreate): Promise<Organisation> {
    return fetchAPI<Organisation>('/organisations', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateOrganisation(
    orgId: string,
    payload: OrganisationUpdate
): Promise<Organisation> {
    return fetchAPI<Organisation>(`/organisations/${orgId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function getOrganisationProperties(orgId: string): Promise<OrganisationProperty[]> {
    return fetchAPI<OrganisationProperty[]>(`/organisations/${orgId}/properties`);
}

export async function getOrganisationUsers(orgId: string): Promise<OrganisationUser[]> {
    return fetchAPI<OrganisationUser[]>(`/organisations/${orgId}/users`);
}

export async function getOrganisationKPI(orgId: string): Promise<OrganisationKPI> {
    return fetchAPI<OrganisationKPI>(`/organisations/${orgId}/kpi`);
}
