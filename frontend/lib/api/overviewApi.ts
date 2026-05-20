import { fetchAPI } from './client';

export interface DataOverview {
    summary: {
        total_properties: number;
        total_contracts: number;
        total_parties: number;
        total_deviations: number;
        total_internal_control_cases: number;
        total_files: number;
    };
    by_region: Array<{
        region: string;
        properties: number;
        contracts: number;
        total_rent: number;
        total_area: number;
    }>;
    data_quality: {
        properties_with_coordinates: number;
        properties_with_costs: number;
        contracts_with_end_date: number;
        parties_with_orgnr: number;
    };
    recent_changes: {
        properties_added_30d: number;
        contracts_added_30d: number;
        deviations_closed_30d: number;
    };
}

export async function getDataOverview(): Promise<DataOverview> {
    return fetchAPI<DataOverview>('/overview');
}

export const overviewApi = {
    get: getDataOverview,
};
