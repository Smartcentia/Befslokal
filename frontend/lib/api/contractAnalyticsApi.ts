import { fetchAPI } from './client';
import { DashboardStatsData } from '../types';

const EMPTY_STATS: DashboardStatsData = {
    properties_count: 0,
    contracts_count: 0,
    total_area: 0,
    occupancy_rate: 0,
    properties: 0,
    contracts: 0,
    risks: 0,
    total_annual_rent: 0,
    total_maintenance_cost: 0,
    gl_andre_kostnader_2026: 0,
    total_vedlikehold_2025: 0,
    critical_deviations: 0,
    expiring_contracts: 0,
};

function mapStats(data: Record<string, unknown> | null): DashboardStatsData {
    if (!data || typeof data !== 'object') return EMPTY_STATS;
    return {
        properties_count: Number(data.properties) ?? 0,
        contracts_count: Number(data.contracts) ?? 0,
        total_area: Number(data.total_area) ?? 0,
        occupancy_rate: Number(data.occupancy_rate) ?? 0,
        properties: Number(data.properties) ?? 0,
        contracts: Number(data.contracts) ?? 0,
        risks: Number(data.risks) ?? 0,
        total_annual_rent: Number(data.total_annual_rent) ?? 0,
        total_maintenance_cost: Number(data.total_maintenance_cost) ?? 0,
        gl_andre_kostnader_2026: Number(data.gl_andre_kostnader_2026) ?? 0,
        total_vedlikehold_2025: Number(data.total_vedlikehold_2025) ?? 0,
        critical_deviations: Number(data.critical_deviations) ?? 0,
        expiring_contracts: Number(data.expiring_contracts) ?? 0,
    };
}

/**
 * Henter dashboard-tall: først direkte fra backend; ved feil fallback til Next.js-proxy.
 */
export async function getDashboardStats(): Promise<DashboardStatsData> {
    try {
        const data = await fetchAPI<Record<string, unknown>>('/dashboard/stats');
        return mapStats(data);
    } catch (err) {
        console.error("Failed to fetch dashboard stats:", err);
        return EMPTY_STATS;
    }
}

export interface CostSummary {
    total_cost: number;
    active_contracts: number;
    annual_rent: number;
    other_costs: number;
    caretaker_cost: number;
    cleaning_cost: number;
}

export interface RegionalBreakdown {
    region: string;
    total_cost: number;
    contract_count: number;
    property_count: number;
}

export interface ExpiringContractAnalytics {
    contract_id: string;
    property_name: string | null;
    property_address: string;
    landlord: string;
    end_date: string;
    days_until_expiry: number;
    annual_cost: number;
    monthly_rent?: number;
    status?: string;
}

export interface Contract {
    contract_id: string;
    contractNumber?: string;
    external_data?: any;
    unit_id?: string;
    unit?: any;
    start_date?: string;
    end_date?: string;
    monthly_rent?: number;
    amount?: {
        amount_per_year: number;
        currency: string;
    };
    party_id?: string;
    party?: any;
    property_id?: string;
    property?: any;
    status?: string;
    periods?: any[];
    amount_per_year?: number;
    currency?: string;
}

/**
 * Fetch cost summary for dashboard cards
 */
export async function getCostSummary(): Promise<CostSummary> {
    try {
        return await fetchAPI('/analytics/costs/summary');
    } catch (error) {
        console.error("Failed to fetch cost summary:", error);
        return {
            total_cost: 0,
            active_contracts: 0,
            annual_rent: 0,
            other_costs: 0,
            caretaker_cost: 0,
            cleaning_cost: 0
        };
    }
}

import { SystemStatus } from '../types';

export async function getSystemStatus(): Promise<SystemStatus> {
    try {
        return await fetchAPI('/dashboard/status');
    } catch (error) {
        console.error("Failed to fetch system status:", error);
        return { database: 'offline', api_gateway: 'online', nve_integration: 'unknown' } as any;
    }
}

/**
 * Fetch regional cost breakdown for charts
 */
export async function getRegionalCostBreakdown(groupBy: 'county' | 'region' = 'region'): Promise<RegionalBreakdown[]> {
    try {
        return await fetchAPI(`/analytics/costs/regional?group_by=${groupBy}`);
    } catch (error) {
        console.error("Failed to fetch regional breakdown:", error);
        return [];
    }
}

/**
 * Fetch expiring contracts
 */
export interface ProactiveInsight {
    id: string;
    type: string;
    content: string;
    severity: 'low' | 'medium' | 'high';
}

export async function getExpiringContractAnalyticss(days: number = 90): Promise<ExpiringContractAnalytics[]> {
    try {
        return await fetchAPI(`/contracts/expiring?days=${days}`);
    } catch (error) {
        console.error("Failed to fetch expiring contracts:", error);
        return [];
    }
}

export async function getContract(id: string): Promise<Contract | null> {
    try {
        return await fetchAPI(`/contracts/${id}`);
    } catch (error) {
        console.error(`Failed to fetch contract ${id}:`, error);
        return null;
    }
}

export async function getContracts(options: { skip?: number, limit?: number } = {}): Promise<Contract[]> {
    try {
        const params = new URLSearchParams();
        if (options.skip !== undefined) params.append('skip', options.skip.toString());
        if (options.limit !== undefined) params.append('limit', options.limit.toString());

        const queryString = params.toString();
        const endpoint = `/contracts${queryString ? `?${queryString}` : ''}`;

        return await fetchAPI(endpoint);
    } catch (error) {
        console.error("Failed to fetch contracts:", error);
        return [];
    }
}

// Financial Overview
export interface FinancialOverview {
    total_revenue: number;
    total_expenses: number;
    net_income: number;
    properties_count: number;
    contracts_count: number;
    by_region?: Record<string, { revenue: number; expenses: number }>;
    regions?: Array<{
        region: string;
        maintenance: number;
        rent: number;
        properties: Array<{
            property_id: string;
            name: string;
            address: string;
            contractedRent: number;
            actualAccountingSpend: number;
        }>;
    }>;
}

export async function getFinancialOverview(): Promise<FinancialOverview> {
    try {
        return await fetchAPI('/dashboard/financial-overview');
    } catch (error) {
        console.error("Failed to fetch financial overview:", error);
        return {
            total_revenue: 0,
            total_expenses: 0,
            net_income: 0,
            properties_count: 0,
            contracts_count: 0
        };
    }
}

export async function getRegionalStats(): Promise<any[]> {
    try {
        return await fetchAPI('/dashboard/regional-financials');
    } catch (error) {
        console.error("Failed to fetch regional stats:", error);
        return [];
    }
}

export interface Tenant {
    tenant_id: string;
    name: string;
    revenue: number;
    contracts: number;
}

export async function getTopTenants(): Promise<Tenant[]> {
    try {
        return await fetchAPI('/dashboard/top-tenants');
    } catch (error) {
        console.error("Failed to fetch top tenants:", error);
        return [];
    }
}
