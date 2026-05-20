import { fetchAPI } from './client';

export interface Contract {
    contract_id: string;
    contractNumber?: string;
    property_id: string;
    party_id?: string;
    unit_id?: string;
    contract_number?: string;
    contract_type?: string;
    start_date?: string;
    end_date?: string;
    amount_per_year?: number;
    amount_per_month?: number;
    index_regulation?: string;
    notice_period_months?: number;
    renewal_options?: string;
    special_terms?: string;
    status?: string;
    landlord_party_id?: string;
    tenant_party_id?: string;
    created_at?: string;
    updated_at?: string;
    external_data?: {
        elements?: string;
        [key: string]: any;
    };
    periods?: Array<{ start_date?: string; end_date?: string }>;
    amount?: { amount_per_year?: number; amount_per_month?: number; currency?: string };
    party?: {
        party_id?: string;
        name?: string;
    };
    unit?: {
        unit_id?: string;
        property?: {
            property_id?: string;
            name?: string;
            address?: string;
        };
    };
    property?: {
        property_id?: string;
        name?: string;
        address?: string;
        latitude?: number;
        longitude?: number;
        external_data?: any;
    };
}

export interface CreateContractPayload {
    property_id: string;
    unit_id?: string;
    contract_number?: string;
    contract_type?: string;
    start_date?: string;
    end_date?: string;
    amount_per_year?: number;
    amount_per_month?: number;
    index_regulation?: string;
    notice_period_months?: number;
    renewal_options?: string;
    special_terms?: string;
    status?: string;
    landlord_party_id?: string;
    tenant_party_id?: string;
}

export interface UpdateContractPayload {
    contract_number?: string;
    contract_type?: string;
    start_date?: string;
    end_date?: string;
    amount_per_year?: number;
    amount_per_month?: number;
    index_regulation?: string;
    notice_period_months?: number;
    renewal_options?: string;
    special_terms?: string;
    status?: string;
    landlord_party_id?: string;
    tenant_party_id?: string;
}

export interface GetContractsParams {
    property_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
}

export async function getContracts(params: GetContractsParams = {}): Promise<Contract[]> {
    const searchParams = new URLSearchParams();
    if (params.property_id) searchParams.set('property_id', params.property_id);
    if (params.status) searchParams.set('status', params.status);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<Contract[]>(`/contracts${query ? `?${query}` : ''}`);
}

export async function getContract(contractId: string): Promise<Contract> {
    return fetchAPI<Contract>(`/contracts/${contractId}`);
}

export async function createContract(payload: CreateContractPayload): Promise<Contract> {
    return fetchAPI<Contract>('/contracts', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateContract(contractId: string, payload: UpdateContractPayload): Promise<Contract> {
    return fetchAPI<Contract>(`/contracts/${contractId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
    });
}

export async function deleteContract(contractId: string): Promise<void> {
    await fetchAPI(`/contracts/${contractId}`, { method: 'DELETE' });
}

export interface ContractCostSummary {
    total_annual_rent: number;
    average_per_sqm: number;
    total_contracts: number;
    by_type: Record<string, number>;
}

export interface RegionalBreakdown {
    region: string;
    total_contracts: number;
    total_annual_rent: number;
    average_rent_per_sqm: number;
}

export interface LandlordComparison {
    landlord_id: string;
    landlord_name: string;
    total_contracts: number;
    total_annual_rent: number;
    properties: number;
}

export interface ExpiringContract {
    contract_id: string;
    property_id: string;
    property_name: string;
    end_date: string;
    days_until_expiry: number;
    amount_per_year: number;
    landlord_name?: string;
}

export interface CostPerSqm {
    property_id: string;
    property_name: string;
    cost_per_sqm: number;
    total_area: number;
    annual_rent: number;
}

export async function getContractCostSummary(): Promise<ContractCostSummary> {
    return fetchAPI<ContractCostSummary>('/contracts/analytics/cost-summary');
}

export async function getContractRegionalBreakdown(): Promise<RegionalBreakdown[]> {
    return fetchAPI<RegionalBreakdown[]>('/contracts/analytics/regional-breakdown');
}

export async function getContractLandlordComparison(): Promise<LandlordComparison[]> {
    return fetchAPI<LandlordComparison[]>('/contracts/analytics/landlord-comparison');
}

export async function getExpiringContracts(days: number = 90): Promise<ExpiringContract[]> {
    return fetchAPI<ExpiringContract[]>(`/contracts/analytics/expiring?days=${days}`);
}

export async function getContractCostPerSqm(): Promise<CostPerSqm[]> {
    return fetchAPI<CostPerSqm[]>('/contracts/analytics/cost-per-sqm');
}

export const contractsApi = {
    getAll: getContracts,
    getById: getContract,
    create: createContract,
    update: updateContract,
    delete: deleteContract,
    getByProperty: (propertyId: string) => getContracts({ property_id: propertyId }),
    analytics: {
        costSummary: getContractCostSummary,
        regionalBreakdown: getContractRegionalBreakdown,
        landlordComparison: getContractLandlordComparison,
        expiring: getExpiringContracts,
        costPerSqm: getContractCostPerSqm,
    },
};
