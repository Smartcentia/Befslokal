
// Types
export interface Tool {
    id: string;
    name: string;
    type?: string;
    description: string;
    status: 'verified' | 'experimental' | 'deprecated';
    qa_status?: 'pending' | 'pass' | 'fail';
    created_at: string;
    is_pinned?: boolean;
    usage_count?: number;
    is_public?: boolean;
}

export interface LabResponse {
    status: string; // 'created' | 'found' | 'error' or other
    strategy?: string;
    code?: string;
    sandbox_stdout?: string;
    logs?: string[];
    message?: string;
    tool_id?: string;
    error?: string;
}

export interface FinancialQueryRequest {
    query: string;
    property_ids?: string[];
}

export interface FinancialQueryResponse {
    results?: any[];
    summary?: string;
    status?: string;
    tool_id?: string;
    intent?: string;
    confidence?: number;
    code?: string;
    error?: string;
    data?: any; // Structured data for visualization
}

import { fetchAPI } from './client';

interface ChatResponse {
    answer: string;
    sources: any[];
    data?: any;
    error?: string;
}

export async function runFinancialQuery(req: FinancialQueryRequest): Promise<FinancialQueryResponse> {
    // Route to Unified Agent for advanced financial analysis
    try {
        const response = await fetchAPI<ChatResponse>('/v1/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message: req.query })
        });

        return {
            summary: response.answer,
            status: response.error ? 'error' : 'success',
            data: response.data,
            error: response.error
        };
    } catch (e: unknown) {
        return {
            summary: "Kunne ikke utføre finansiell spørring.",
            status: "error",
            error: e instanceof Error ? e.message : String(e)
        };
    }
}

export async function compareProperties(propertyIds: string[]): Promise<{ comparison: any[] }> {
    console.warn("compareProperties stub called");
    return { comparison: [] };
}

// Lab Management Functions
export async function labChat(query: string | Array<{ role: string; content: string }>, sessionId?: string): Promise<LabResponse> {
    const normalizedQuery = Array.isArray(query) ? (query[query.length - 1]?.content ?? '') : query;
    return fetchAPI('/lab/chat', {
        method: 'POST',
        body: JSON.stringify({ query: normalizedQuery, session_id: sessionId }),
    });
}

export async function getTools(status?: string, pinned?: boolean): Promise<Tool[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (pinned) params.append('pinned', 'true');
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return fetchAPI(`/lab/tools${queryString}`);
}

export async function publishTool(toolId: string): Promise<{ status: string, message: string }> {
    return fetchAPI(`/lab/tools/${toolId}/publish`, {
        method: 'POST'
    });
}

export async function pinTool(toolId: string, is_pinned: boolean): Promise<{ status: string, message: string }> {
    return fetchAPI(`/lab/tools/${toolId}/pin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_pinned })
    });
}

export async function executeTool(toolId: string, inputText: string): Promise<any> {
    return fetchAPI(`/lab/tools/${toolId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_text: inputText })
    });
}

export async function searchTools(query: string): Promise<Tool[]> {
    return fetchAPI(`/lab/tools/search?query=${encodeURIComponent(query)}`);
}
