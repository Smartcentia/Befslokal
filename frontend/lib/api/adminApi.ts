import { fetchAPI } from './client';

export interface SystemStats {
    total_properties: number;
    total_contracts: number;
    total_parties: number;
    total_users: number;
    total_deviations: number;
    active_internal_control_cases: number;
    database_size_mb: number;
    last_sync: string;
}

export interface FullHealthCheck {
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: Array<{
        name: string;
        status: 'ok' | 'warning' | 'error';
        message?: string;
        duration_ms: number;
    }>;
    database: {
        connected: boolean;
        latency_ms: number;
        pool_size: number;
        active_connections: number;
    };
    external_services: Array<{
        name: string;
        status: 'ok' | 'unreachable';
        last_checked: string;
    }>;
}

export interface AuditLog {
    log_id: string;
    user_email: string;
    action: string;
    entity_type: string;
    entity_id?: string;
    details?: Record<string, unknown>;
    ip_address?: string;
    timestamp: string;
}

export interface ApiCostSummary {
    period: string;
    total_cost_usd: number;
    total_tokens: number;
    by_model: Record<string, { cost: number; tokens: number; requests: number }>;
    by_endpoint: Record<string, { cost: number; requests: number }>;
}

export interface DailyApiCost {
    date: string;
    cost_usd: number;
    tokens: number;
    requests: number;
}

export interface MapboxUsage {
    period: string;
    total_requests: number;
    geocoding_requests: number;
    static_map_requests: number;
    estimated_cost_usd: number;
}

export interface ApiUsageSummary {
    period: string;
    total_requests: number;
    total_tokens: number;
    estimated_cost_usd: number;
    by_model: Record<string, { requests: number; tokens: number; cost: number }>;
}

export interface ApiUsageByModel {
    model_name: string;
    total_requests: number;
    total_tokens: number;
    average_latency_ms: number;
    error_rate: number;
    daily_stats: Array<{ date: string; requests: number; tokens: number }>;
}

export interface RecentApiUsage {
    request_id: string;
    endpoint: string;
    model: string;
    tokens: number;
    latency_ms: number;
    status: 'success' | 'error';
    timestamp: string;
}

export interface EconomicStatus {
    last_import: string;
    total_gl_transactions: number;
    years_available: number[];
    data_freshness: 'current' | 'stale' | 'outdated';
    missing_mappings: number;
}

export interface PropertyEnrichmentRequest {
    apply?: boolean;
    confirm_apply?: boolean;
    min_score?: number;
    force_description?: boolean;
    download_images?: boolean;
    limit?: number;
    report_file?: string;
}

export interface PropertyEnrichmentRunResponse {
    message: string;
    mode: 'dry-run' | 'apply';
    report_file: string;
    summary: {
        baseline_before: Record<string, number>;
        baseline_after: Record<string, number>;
        updated: Record<string, number>;
        skipped_no_match: number;
        skipped_low_score: number;
    };
    samples: Array<{
        property_id: string;
        before: Record<string, unknown>;
        after: Record<string, unknown>;
    }>;
}

export interface PropertyEnrichmentReportItem {
    filename: string;
    size_bytes: number;
    modified_at: string;
}

export interface PropertyEnrichmentReportResponse {
    filename: string;
    report: {
        baseline_before?: Record<string, number>;
        baseline_after?: Record<string, number>;
        updated?: Record<string, number>;
        samples?: Array<{ property_id: string }>;
        [key: string]: unknown;
    };
}

export async function getSystemStats(): Promise<SystemStats> {
    return fetchAPI<SystemStats>('/admin/stats/system');
}

export async function getFullHealthCheck(): Promise<FullHealthCheck> {
    return fetchAPI<FullHealthCheck>('/admin/health/full');
}

export async function getAdminHandbook(): Promise<{ content: string; last_updated: string }> {
    return fetchAPI('/admin/handbook');
}

export async function getAuditLogs(params: {
    skip?: number;
    limit?: number;
    user_email?: string;
    action?: string;
    from_date?: string;
    to_date?: string;
} = {}): Promise<AuditLog[]> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params.user_email) searchParams.set('user_email', params.user_email);
    if (params.action) searchParams.set('action', params.action);
    if (params.from_date) searchParams.set('from_date', params.from_date);
    if (params.to_date) searchParams.set('to_date', params.to_date);

    const query = searchParams.toString();
    return fetchAPI<AuditLog[]>(`/admin/logs${query ? `?${query}` : ''}`);
}

export async function getApiCostSummary(): Promise<ApiCostSummary> {
    return fetchAPI<ApiCostSummary>('/admin/api-costs/summary');
}

export async function getDailyApiCosts(days: number = 30): Promise<DailyApiCost[]> {
    return fetchAPI<DailyApiCost[]>(`/admin/api-costs/daily?days=${days}`);
}

export async function getMapboxUsage(): Promise<MapboxUsage> {
    return fetchAPI<MapboxUsage>('/admin/api-costs/mapbox');
}

export async function getApiUsageSummary(): Promise<ApiUsageSummary> {
    return fetchAPI<ApiUsageSummary>('/admin/api-usage/summary');
}

export async function getApiUsageByModel(modelName: string): Promise<ApiUsageByModel> {
    return fetchAPI<ApiUsageByModel>(`/admin/api-usage/by-model/${encodeURIComponent(modelName)}`);
}

export async function getRecentApiUsage(limit: number = 50): Promise<RecentApiUsage[]> {
    return fetchAPI<RecentApiUsage[]>(`/admin/api-usage/recent?limit=${limit}`);
}

export async function getDailyApiStats(days: number = 30): Promise<Array<{
    date: string;
    requests: number;
    tokens: number;
    errors: number;
}>> {
    return fetchAPI(`/admin/api-usage/daily-stats?days=${days}`);
}

export async function getEconomicStatus(): Promise<EconomicStatus> {
    return fetchAPI<EconomicStatus>('/admin/economic-status');
}

export async function runPropertyEnrichmentBatch(
    payload: PropertyEnrichmentRequest
): Promise<PropertyEnrichmentRunResponse> {
    return fetchAPI<PropertyEnrichmentRunResponse>('/admin/property-enrichment/batch', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function listPropertyEnrichmentReports(limit: number = 20): Promise<{ reports: PropertyEnrichmentReportItem[] }> {
    return fetchAPI<{ reports: PropertyEnrichmentReportItem[] }>(`/admin/property-enrichment/reports?limit=${limit}`);
}

export async function getPropertyEnrichmentReport(filename: string): Promise<PropertyEnrichmentReportResponse> {
    return fetchAPI<PropertyEnrichmentReportResponse>(`/admin/property-enrichment/reports/${encodeURIComponent(filename)}`);
}

export async function batchGeocode(propertyIds: string[]): Promise<{
    status: string;
    processed: number;
    failed: number;
}> {
    return fetchAPI('/admin/geocoding/batch', {
        method: 'POST',
        body: JSON.stringify({ property_ids: propertyIds }),
    });
}

export async function batchRiskCalculation(propertyIds: string[]): Promise<{
    status: string;
    processed: number;
}> {
    return fetchAPI('/admin/risk/batch', {
        method: 'POST',
        body: JSON.stringify({ property_ids: propertyIds }),
    });
}

export interface GeneratedTool {
    tool_id: string;
    name: string;
    description: string;
    code: string;
    status: 'pending' | 'approved' | 'rejected';
    created_at: string;
    approved_by?: string;
    approved_at?: string;
}

export async function getEvolutionTools(): Promise<GeneratedTool[]> {
    return fetchAPI<GeneratedTool[]>('/admin/evolution/tools');
}

export async function approveEvolutionTool(
    toolId: string,
    approve: boolean
): Promise<{ status: string }> {
    return fetchAPI(`/admin/evolution/tools/${toolId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ approve }),
    });
}

export const adminApi = {
    system: {
        stats: getSystemStats,
        healthCheck: getFullHealthCheck,
        handbook: getAdminHandbook,
        economicStatus: getEconomicStatus,
    },
    logs: {
        audit: getAuditLogs,
    },
    costs: {
        summary: getApiCostSummary,
        daily: getDailyApiCosts,
        mapbox: getMapboxUsage,
    },
    apiUsage: {
        summary: getApiUsageSummary,
        byModel: getApiUsageByModel,
        recent: getRecentApiUsage,
        dailyStats: getDailyApiStats,
    },
    batch: {
        geocode: batchGeocode,
        riskCalculation: batchRiskCalculation,
        propertyEnrichment: runPropertyEnrichmentBatch,
    },
    propertyEnrichment: {
        listReports: listPropertyEnrichmentReports,
        getReport: getPropertyEnrichmentReport,
    },
    evolution: {
        getTools: getEvolutionTools,
        approveTool: approveEvolutionTool,
    },
};
