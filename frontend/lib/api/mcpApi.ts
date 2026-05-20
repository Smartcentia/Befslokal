import { fetchAPI } from './client';

export interface McpTool {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
    category: string;
}

export interface McpToolCallResult {
    success: boolean;
    result?: unknown;
    error?: string;
    execution_time_ms: number;
}

export interface McpServiceStatus {
    service: string;
    status: 'ready' | 'unavailable' | 'degraded';
    last_checked: string;
}

export interface FdvComponent {
    component_id: string;
    property_id: string;
    name: string;
    type: string;
    location?: string;
    condition?: string;
    installation_date?: string;
    last_maintenance?: string;
    next_maintenance?: string;
}

export interface MaintenanceLog {
    log_id: string;
    component_id: string;
    type: string;
    description: string;
    performed_by: string;
    performed_at: string;
    cost?: number;
}

export interface IoTSensor {
    sensor_id: string;
    property_id: string;
    type: string;
    location: string;
    status: 'active' | 'inactive' | 'error';
    last_reading?: {
        value: number;
        unit: string;
        timestamp: string;
    };
}

export interface IoTAnomaly {
    anomaly_id: string;
    sensor_id: string;
    type: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
    detected_at: string;
    resolved?: boolean;
}

export async function getMcpTools(): Promise<McpTool[]> {
    return fetchAPI<McpTool[]>('/mcp/tools');
}

export async function callMcpTool(
    toolName: string,
    parameters: Record<string, unknown>
): Promise<McpToolCallResult> {
    return fetchAPI<McpToolCallResult>(`/mcp/tools/${toolName}/call`, {
        method: 'POST',
        body: JSON.stringify(parameters),
    });
}

export async function getMcpDocumentStatus(): Promise<McpServiceStatus> {
    return fetchAPI<McpServiceStatus>('/mcp/document/');
}

export async function searchMcpDocuments(
    query: string,
    options?: { limit?: number; filters?: Record<string, unknown> }
): Promise<{ results: Array<{ id: string; content: string; score: number }> }> {
    return fetchAPI('/mcp/document/search', {
        method: 'POST',
        body: JSON.stringify({ query, ...options }),
    });
}

export async function ingestMcpDocument(
    content: string,
    metadata: Record<string, unknown>
): Promise<{ document_id: string; status: string }> {
    return fetchAPI('/mcp/document/ingest', {
        method: 'POST',
        body: JSON.stringify({ content, metadata }),
    });
}

export async function getMcpFdvStatus(): Promise<McpServiceStatus> {
    return fetchAPI<McpServiceStatus>('/mcp/fdv/');
}

export async function getFdvComponents(propertyId: string): Promise<FdvComponent[]> {
    return fetchAPI<FdvComponent[]>(`/mcp/fdv/components/${propertyId}`);
}

export async function addFdvComponent(
    component: Omit<FdvComponent, 'component_id'>
): Promise<FdvComponent> {
    return fetchAPI<FdvComponent>('/mcp/fdv/components', {
        method: 'POST',
        body: JSON.stringify(component),
    });
}

export async function logMcpMaintenance(log: Omit<MaintenanceLog, 'log_id'>): Promise<MaintenanceLog> {
    return fetchAPI<MaintenanceLog>('/mcp/fdv/maintenance', {
        method: 'POST',
        body: JSON.stringify(log),
    });
}

export async function getMcpIotStatus(): Promise<McpServiceStatus> {
    return fetchAPI<McpServiceStatus>('/mcp/iot/');
}

export async function registerIotSensor(
    sensor: Omit<IoTSensor, 'sensor_id' | 'status' | 'last_reading'>
): Promise<IoTSensor> {
    return fetchAPI<IoTSensor>('/mcp/iot/sensors', {
        method: 'POST',
        body: JSON.stringify(sensor),
    });
}

export async function ingestIotReading(
    sensorId: string,
    value: number,
    unit: string
): Promise<{ status: string }> {
    return fetchAPI('/mcp/iot/readings', {
        method: 'POST',
        body: JSON.stringify({ sensor_id: sensorId, value, unit }),
    });
}

export async function checkIotAnomalies(propertyId: string): Promise<IoTAnomaly[]> {
    return fetchAPI<IoTAnomaly[]>(`/mcp/iot/anomalies/${propertyId}`);
}

export async function getMcpFinansStatus(): Promise<McpServiceStatus> {
    return fetchAPI<McpServiceStatus>('/mcp/finans/');
}

export async function getMcpPropertyCosts(
    propertyId: string,
    year?: number
): Promise<{ costs: Array<{ category: string; amount: number }> }> {
    const params = year ? `?year=${year}` : '';
    return fetchAPI(`/mcp/finans/property/${propertyId}/costs${params}`);
}

export async function getMcpRegionalCosts(): Promise<{
    regions: Array<{ region: string; total: number; categories: Record<string, number> }>;
}> {
    return fetchAPI('/mcp/finans/regional-costs');
}

export async function getMcpPortfolioSummary(): Promise<{
    total_properties: number;
    total_value: number;
    total_costs: number;
    key_metrics: Record<string, number>;
}> {
    return fetchAPI('/mcp/finans/portfolio-summary');
}

export async function getMcpKpis(): Promise<Array<{
    name: string;
    value: number;
    unit: string;
    trend: 'up' | 'down' | 'stable';
}>> {
    return fetchAPI('/mcp/finans/kpis');
}

export async function getMcpExpiringContracts(days: number = 90): Promise<Array<{
    contract_id: string;
    property_name: string;
    end_date: string;
    days_remaining: number;
    annual_value: number;
}>> {
    return fetchAPI(`/mcp/finans/expiring-contracts?days=${days}`);
}

export const mcpApi = {
    tools: {
        list: getMcpTools,
        call: callMcpTool,
    },
    document: {
        status: getMcpDocumentStatus,
        search: searchMcpDocuments,
        ingest: ingestMcpDocument,
    },
    fdv: {
        status: getMcpFdvStatus,
        components: getFdvComponents,
        addComponent: addFdvComponent,
        logMaintenance: logMcpMaintenance,
    },
    iot: {
        status: getMcpIotStatus,
        registerSensor: registerIotSensor,
        ingestReading: ingestIotReading,
        anomalies: checkIotAnomalies,
    },
    finans: {
        status: getMcpFinansStatus,
        propertyCosts: getMcpPropertyCosts,
        regionalCosts: getMcpRegionalCosts,
        portfolioSummary: getMcpPortfolioSummary,
        kpis: getMcpKpis,
        expiringContracts: getMcpExpiringContracts,
    },
};
