import { fetchAPI } from '../../api/client';

export interface DashboardStatsData {
    properties: number;
    contracts: number;
    risks: number;
    total_annual_rent?: number;
    total_maintenance_cost?: number;
    critical_deviations?: number;
    expiring_contracts?: number;
}

export const agentService = {
    chat: async (messages: any[]) => {
        // Use the powerful AI Assistant with MCP Tools (Context Aware)
        // Endpoint: /api/v1/agent/chat

        const context = {
            url: typeof window !== 'undefined' ? window.location.href : '',
            path: typeof window !== 'undefined' ? window.location.pathname : '',
            user_agent: typeof window !== 'undefined' ? window.navigator.userAgent : '',
            timestamp: new Date().toISOString()
        };

        return fetchAPI('/agent/chat', {
            method: 'POST',
            body: JSON.stringify({
                messages: messages,
                context: context
            }),
        });
    },

    getStats: async (): Promise<DashboardStatsData> => {
        // Updated to use the correct domain-aware endpoint
        return await fetchAPI('/dashboard/stats');
    },

    getRegionalFinancials: async (): Promise<any[]> => {
        try {
            return await fetchAPI('/dashboard/regional-financials');
        } catch (e) {
            console.warn("Failed regional stats", e);
            return [];
        }
    }
};
