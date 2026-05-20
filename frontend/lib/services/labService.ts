import { fetchAPI } from '../api/client';

export interface LabResponse {
    status: string;
    message?: string;
    tool_id?: string;
    code?: string;
    sandbox_stdout?: string;
    error?: string;
    logs: string[];
    strategy?: string;
}

export interface Tool {
    id: string;
    name: string;
    description: string;
    status: 'experimental' | 'verified' | 'deprecated';
    created_at: string;
    usage_count: number;
    is_public: boolean;
    is_pinned?: boolean;
    qa_status?: 'pending' | 'pass' | 'fail';
}

export async function labChat(query: string, sessionId?: string): Promise<LabResponse> {
    return fetchAPI('/lab/chat', {
        method: 'POST',
        body: JSON.stringify({ query, session_id: sessionId }),
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
