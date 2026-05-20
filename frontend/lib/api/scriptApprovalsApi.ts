import { fetchAPI } from './client';

export interface PendingScript {
    execution_id: string;
    script_name: string;
    script_code: string;
    description: string;
    requested_by: string;
    requested_at: string;
    risk_level: 'low' | 'medium' | 'high';
    affected_entities?: string[];
}

export interface ScriptApprovalRequest {
    script_name: string;
    script_code: string;
    description: string;
    risk_level?: 'low' | 'medium' | 'high';
}

export interface ApprovalResult {
    execution_id: string;
    status: 'approved' | 'rejected';
    approved_by?: string;
    approved_at?: string;
    execution_result?: unknown;
}

export interface ApprovalHistoryEntry {
    execution_id: string;
    script_name: string;
    status: 'approved' | 'rejected' | 'pending';
    requested_by: string;
    requested_at: string;
    decided_by?: string;
    decided_at?: string;
}

export async function getPendingScripts(): Promise<PendingScript[]> {
    return fetchAPI<PendingScript[]>('/script-approvals/pending');
}

export async function requestScriptApproval(
    request: ScriptApprovalRequest
): Promise<{ execution_id: string; status: string }> {
    return fetchAPI('/script-approvals/request', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

export async function approveOrRejectScript(
    executionId: string,
    approve: boolean,
    reason?: string
): Promise<ApprovalResult> {
    return fetchAPI<ApprovalResult>(`/script-approvals/approve/${executionId}`, {
        method: 'POST',
        body: JSON.stringify({ approve, reason }),
    });
}

export async function getApprovalHistory(params: {
    skip?: number;
    limit?: number;
    status?: string;
} = {}): Promise<ApprovalHistoryEntry[]> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    return fetchAPI<ApprovalHistoryEntry[]>(
        `/script-approvals/history${query ? `?${query}` : ''}`
    );
}

export const scriptApprovalsApi = {
    pending: getPendingScripts,
    request: requestScriptApproval,
    approve: (executionId: string, reason?: string) =>
        approveOrRejectScript(executionId, true, reason),
    reject: (executionId: string, reason?: string) =>
        approveOrRejectScript(executionId, false, reason),
    history: getApprovalHistory,
};
