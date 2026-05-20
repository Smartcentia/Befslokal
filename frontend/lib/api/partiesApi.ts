import { fetchAPI } from './client';

export interface Party {
    party_id: string;
    name: string;
    role: 'landlord' | 'tenant' | 'contractor' | 'other';
    orgnr?: string;
    contact_person?: string;
    email?: string;
    phone?: string;
    address?: string;
    is_company: boolean;
    external_data?: Record<string, unknown>;
    created_at?: string;
    updated_at?: string;
}

export interface CreatePartyPayload {
    name: string;
    role: 'landlord' | 'tenant' | 'contractor' | 'other';
    orgnr?: string;
    contact_person?: string;
    email?: string;
    phone?: string;
    address?: string;
    is_company?: boolean;
}

export interface UpdatePartyPayload {
    name?: string;
    role?: 'landlord' | 'tenant' | 'contractor' | 'other';
    orgnr?: string;
    contact_person?: string;
    email?: string;
    phone?: string;
    address?: string;
    is_company?: boolean;
}

export interface DueDiligenceReport {
    risk_level: 'LAV' | 'MIDDELS' | 'HØY';
    summary: string;
    red_flags: string[];
    detailed_analysis: {
        okonomi?: string;
        juridisk?: string;
        omdømme?: string;
    };
    follow_up_questions: string[];
    sources: Array<{ url: string; title: string }>;
    generated_at: string;
}

export interface CompanySummary {
    summary: string;
    key_facts: string[];
    saved: boolean;
    generated_at: string;
}

export interface BrregEnrichment {
    enhet: Record<string, unknown>;
    roller: Array<Record<string, unknown>>;
    enriched_at: string;
}

export interface TenantWithProperty extends Party {
    health_score?: {
        score?: number;
        rationale?: string;
    };
    property?: {
        name?: string;
        address?: string;
        latitude?: number;
        longitude?: number;
    };
}

export async function getParties(params: {
    role?: string;
    search?: string;
    skip?: number;
    limit?: number;
} = {}): Promise<Party[]> {
    const searchParams = new URLSearchParams();
    if (params.role) searchParams.set('role', params.role);
    if (params.search) searchParams.set('search', params.search);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<Party[]>(`/parties${query ? `?${query}` : ''}`);
}

/** Hent leietakere med eiendomsinfo i én spørring (reduserer last). */
export async function getTenantsWithProperty(params: {
    skip?: number;
    limit?: number;
} = {}): Promise<TenantWithProperty[]> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<TenantWithProperty[]>(`/parties/tenants-with-property${query ? `?${query}` : ''}`);
}

export async function getParty(partyId: string): Promise<Party> {
    return fetchAPI<Party>(`/parties/${partyId}`);
}

export async function createParty(payload: CreatePartyPayload): Promise<Party> {
    return fetchAPI<Party>('/parties', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateParty(partyId: string, payload: UpdatePartyPayload): Promise<Party> {
    return fetchAPI<Party>(`/parties/${partyId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteParty(partyId: string): Promise<void> {
    await fetchAPI(`/parties/${partyId}`, { method: 'DELETE' });
}

export async function enrichPartyBrreg(partyId: string): Promise<BrregEnrichment> {
    return fetchAPI<BrregEnrichment>(`/parties/${partyId}/enrich-brreg`, { method: 'POST' });
}

export async function batchEnrichPartiesBrreg(): Promise<{
    status: string;
    enriched: number;
    failed: number;
}> {
    return fetchAPI('/parties/batch-enrich-brreg', { method: 'POST' });
}

export async function getCompanySummary(partyId: string): Promise<CompanySummary> {
    return fetchAPI<CompanySummary>(`/parties/${partyId}/company-summary-from-web`, {
        method: 'POST',
    });
}

export async function runDueDiligence(partyId: string): Promise<DueDiligenceReport> {
    return fetchAPI<DueDiligenceReport>(`/parties/${partyId}/due-diligence`, { method: 'POST' });
}

export const partiesApi = {
    getAll: getParties,
    getById: getParty,
    create: createParty,
    update: updateParty,
    delete: deleteParty,
    enrichBrreg: enrichPartyBrreg,
    batchEnrichBrreg: batchEnrichPartiesBrreg,
    getCompanySummary,
    runDueDiligence,
};
