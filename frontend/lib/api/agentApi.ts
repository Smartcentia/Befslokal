import { fetchAPI } from './client';

export interface AgentChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export interface AgentChatResponse {
    response: string;
    actions_taken?: Array<{
        tool: string;
        input: Record<string, unknown>;
        result: unknown;
    }>;
    sources?: Array<{
        type: string;
        id?: string;
        title?: string;
    }>;
    follow_up_questions?: string[];
}

export interface AgentDashboardStats {
    total_properties: number;
    total_contracts: number;
    total_parties: number;
    total_value: number;
    key_metrics: Record<string, number>;
}

export interface AgentPropertyDetails {
    property_id: string;
    name: string;
    address: string;
    summary: string;
    key_facts: Array<{ label: string; value: string }>;
    risk_indicators: Array<{ name: string; level: string; description: string }>;
}

export interface AgentContractDetails {
    contract_id: string;
    summary: string;
    key_terms: Array<{ label: string; value: string }>;
    important_dates: Array<{ label: string; date: string; days_away: number }>;
}

export interface AgentPartyDetails {
    party_id: string;
    name: string;
    orgnr?: string;
    summary: string;
    brreg_data?: Record<string, unknown>;
    risk_assessment?: {
        level: string;
        flags: string[];
    };
}

export interface ProcessStep {
    step_id: string;
    title: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'skipped';
    actions?: Array<{ label: string; action: string }>;
}

export interface DeviationProcess {
    deviation_id: string;
    current_step: number;
    total_steps: number;
    steps: ProcessStep[];
    can_proceed: boolean;
}

export interface AIHelpResponse {
    explanation: string;
    suggestions: string[];
    relevant_regulations?: string[];
    examples?: string[];
}

export async function agentChat(
    messages: AgentChatMessage[],
    context?: {
        property_id?: string;
        contract_id?: string;
        deviation_id?: string;
    }
): Promise<AgentChatResponse> {
    return fetchAPI<AgentChatResponse>('/agent/chat', {
        method: 'POST',
        body: JSON.stringify({ messages, context }),
    });
}

export async function getAgentDashboardStats(): Promise<AgentDashboardStats> {
    return fetchAPI<AgentDashboardStats>('/agent/dashboard-stats');
}

export async function getAgentPropertyDetails(propertyId: string): Promise<AgentPropertyDetails> {
    return fetchAPI<AgentPropertyDetails>(`/agent/properties/${propertyId}`);
}

export async function getAgentContractDetails(contractId: string): Promise<AgentContractDetails> {
    return fetchAPI<AgentContractDetails>(`/agent/contracts/${contractId}`);
}

export async function getAgentPartyDetails(partyId: string): Promise<AgentPartyDetails> {
    return fetchAPI<AgentPartyDetails>(`/agent/parties/${partyId}`);
}

export async function getAgentProximityServices(
    propertyId: string
): Promise<Array<{ type: string; name: string; distance_m: number }>> {
    return fetchAPI(`/agent/properties/${propertyId}/proximity-services`);
}

export async function calculatePropertyRisk(propertyId: string): Promise<{
    risk_score: number;
    risk_level: string;
    factors: Array<{ name: string; impact: number; description: string }>;
}> {
    return fetchAPI(`/agent/properties/${propertyId}/risk-assessment`, { method: 'POST' });
}

export async function batchRiskUpdate(propertyIds: string[]): Promise<{
    status: string;
    processed: number;
}> {
    return fetchAPI('/agent/admin/batch-risk-update', {
        method: 'POST',
        body: JSON.stringify({ property_ids: propertyIds }),
    });
}

export async function getDeviationProcess(deviationId: string): Promise<DeviationProcess> {
    return fetchAPI<DeviationProcess>(`/agent/processes/${deviationId}`);
}

export async function advanceDeviationProcess(
    deviationId: string,
    action?: string
): Promise<DeviationProcess> {
    return fetchAPI<DeviationProcess>(`/agent/processes/${deviationId}/next`, {
        method: 'POST',
        body: JSON.stringify({ action }),
    });
}

export async function getAIHelp(
    context: string,
    question: string
): Promise<AIHelpResponse> {
    return fetchAPI<AIHelpResponse>('/agent/processes/ai-help', {
        method: 'POST',
        body: JSON.stringify({ context, question }),
    });
}

export const agentApi = {
    chat: agentChat,
    dashboardStats: getAgentDashboardStats,
    property: {
        details: getAgentPropertyDetails,
        proximityServices: getAgentProximityServices,
        calculateRisk: calculatePropertyRisk,
    },
    contract: {
        details: getAgentContractDetails,
    },
    party: {
        details: getAgentPartyDetails,
    },
    batch: {
        riskUpdate: batchRiskUpdate,
    },
    process: {
        get: getDeviationProcess,
        advance: advanceDeviationProcess,
        aiHelp: getAIHelp,
    },
};
