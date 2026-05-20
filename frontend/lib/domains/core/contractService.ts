import { fetchAPI } from '../../api/client';

// Basic types
export interface Period {
    start_date: string;
    end_date?: string;
}

export interface Amount {
    currency: string;
    amount_per_year?: number;
}

// Support types for nested structures
export interface File {
    file_id: string;
    path: string;
    file_type?: string;
    content_type?: string;
    created_at?: string;
}

export interface Property {
    property_id: string;
    address?: string;
    postal_code?: string;
    city?: string;
    name?: string;
    gnr?: string | number;
    bnr?: string | number;
    external_data?: any;
    // ... add accessible fields from backend as needed 
}

export interface Unit {
    unit_id: string;
    purpose?: string;
    area_sqm?: number;
    floor?: number;
    property?: Property;
    zone_type?: string;
    uu_compliant?: boolean;
}

export interface Party {
    party_id: string;
    name: string;
    orgnr?: string;
    contact_email?: string;
    contact_phone?: string;
    external_data?: any;
}

// Main Contract Interface
export interface Contract {
    id: string; // Keep for safety if anything uses it, though backend uses contract_id. Mapped or alias?
    contract_id: string;
    unit_id: string;
    party_id: string;
    status: string;
    periods: Period[];
    amount: Amount;
    signed_at?: string;
    terminated_at?: string;
    contractNumber?: string; // Legacy?
    tenantId?: string; // Legacy?
    annualRent?: number; // Legacy?
    external_data?: any;

    // Cost breakdowns (Annual)
    caretaker_cost?: number;
    cleaning_cost?: number;
    parking_cost?: number;
    card_reader_cost?: number;
    category?: string;
    elements?: string;

    unit?: Unit;
    party?: Party;
    files: File[];
    property?: Property; // New direct accessor if backend provides it or we derive it

    // Legacy / Flat Fields (Deprecated - verify if populated)
    // party_name?: string; // favor contract.party?.name
    // property_address?: string; // favor contract.property?.address
    // property_id?: string; // favor contract.property?.property_id or unit?.property_id
}

export const contractService = {
    getAll: async (params?: { limit?: number; skip?: number }): Promise<Contract[]> => {
        try {
            const queryParams = new URLSearchParams();
            if (params?.limit) queryParams.append('limit', params.limit.toString());
            if (params?.skip) queryParams.append('skip', params.skip.toString());

            const queryString = queryParams.toString();
            return await fetchAPI(queryString ? `/contracts?${queryString}` : '/contracts');
        } catch (error) {
            console.warn("Failed to fetch contracts", error);
            return [];
        }
    },

    getById: async (id: string): Promise<Contract> => {
        return fetchAPI(`/contracts/${id}`);
    }
};
