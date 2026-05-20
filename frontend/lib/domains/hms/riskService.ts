import { fetchAPI } from '../../api/client';

export interface RiskStats {
    avg_score: number;
    count_high: number;
    count_medium: number;
    count_low: number;
    count_critical: number;
    total_assessments: number;
    top10: any[];
}

export interface CreateRiskParams {
    property_id: string;
    risk_category: string;
    risk_type: string;
    severity: string;
    description?: string;
}

export const riskService = {
    getStats: async (): Promise<RiskStats | null> => {
        try {
            return await fetchAPI('/risk/portfolio');
        } catch (error) {
            console.warn("Failed to fetch risk stats", error);
            return null;
        }
    },

    create: async (data: CreateRiskParams) => {
        return fetchAPI('/risk/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    analyzeProperty: async (property_id: string) => {
        return fetchAPI(`/risk/analyze/${property_id}`);
    }
};
