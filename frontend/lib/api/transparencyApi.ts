import { fetchAPI } from './client';

export interface AIVitals {
    status: string;
    timestamp: string;
    models: {
        primary_llm: {
            name: string;
            provider: string;
            role: string;
        };
        tools: Array<{
            name: string;
            description: string;
            type: string;
        }>;
        data_retrieval: {
            vector_db: string;
            search_type: string;
            status: string;
        };
    };
    metrics: {
        last_24h: {
            total_requests: number;
            avg_response_time_ms: number;
            error_rate_percent: number;
            system_health: string;
        };
    };
}

export interface Scenario {
    id: string;
    title: string;
    description: string;
    llm_role: string;
    ml_role: string;
}

export async function getAiVitals(): Promise<AIVitals> {
    return fetchAPI<AIVitals>('/v1/ai/transparency/vitals');
}

export async function getScenarios(): Promise<{ scenarios: Scenario[] }> {
    return fetchAPI<{ scenarios: Scenario[] }>('/v1/ai/transparency/scenarios');
}
