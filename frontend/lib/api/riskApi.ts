
import { fetchAPI } from './client';

export interface RiskStats {
    total_risks: number;
    high_risks: number;
    medium_risks: number;
    low_risks: number;
    avg_score?: number;
    count_critical?: number;
    count_critical_deviations?: number;
    total_assessments?: number;
    count_high?: number;
}

export interface Deviation {
    id: string;
    title: string;
    description?: string;
    status: string;
    severity: string;
    property_name?: string;
    property_id?: string;
    created_at?: string;
}

export async function getRiskStats(): Promise<RiskStats> {
    try {
        const data = await fetchAPI('/risk/portfolio');
        return {
            total_risks: data.total_assessments || 0,
            high_risks: data.count_high || 0,
            medium_risks: data.count_medium || 0,
            low_risks: data.count_low || 0,
            avg_score: data.avg_score || 0,
            count_critical: data.count_critical || 0,
            count_critical_deviations: data.count_critical_deviations || 0,
            total_assessments: data.total_assessments || 0
        };
    } catch (error) {
        console.error("Failed to fetch risk stats:", error);
        return {
            total_risks: 0,
            high_risks: 0,
            medium_risks: 0,
            low_risks: 0
        };
    }
}

export async function getDeviations(page: number = 1, limit: number = 50): Promise<Deviation[]> {
    try {
        const offset = (page - 1) * limit;
        return await fetchAPI(`/deviations?limit=${limit}&offset=${offset}`);
    } catch (error) {
        console.error("Failed to fetch deviations:", error);
        return [];
    }
}

export async function createRiskAssessment(data: any): Promise<any> {
    try {
        return await fetchAPI('/risk/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    } catch (error) {
        console.error("Failed to create risk assessment:", error);
        throw error;
    }
}

export const deviationService = {
    get: async (id: string) => await fetchAPI(`/deviations/${id}`),
    getById: async (id: string) => await fetchAPI(`/deviations/${id}`),
    update: async (id: string, data: any) => await fetchAPI(`/deviations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    })
};

