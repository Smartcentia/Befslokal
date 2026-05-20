import { fetchAPI } from './client';
import type { DashboardStatsData, RecentActivityItem, SystemStatus } from '../types';

export interface DashboardStats {
    total_properties: number;
    total_contracts: number;
    total_parties: number;
    active_deviations: number;
    pending_internal_control: number;
    contracts_expiring_soon: number;
    total_annual_rent: number;
    /** GL driftskostnader 2026 ekskl. husleie (dashboard/stats). */
    gl_andre_kostnader_2026?: number;
    total_area_sqm: number;
}

export interface RegionalFinancial {
    region: string;
    total_properties: number;
    total_contracts: number;
    total_annual_rent: number;
    total_area_sqm: number;
    average_rent_per_sqm: number;
    active_deviations: number;
}

export interface FinancialOverview {
    year: number;
    total_rent: number;
    total_costs: number;
    net_position: number;
    by_category: Record<string, number>;
    by_region: Record<string, { rent: number; costs: number }>;
    year_over_year_change: number;
}

export interface Tenant {
    party_id?: string;
    tenant_id?: string;
    name: string;
    orgnr?: string;
    total_annual_rent: number;
    contract_count: number;
    contracts?: number;
    property_count: number;
    revenue?: number;
    average_rent_per_sqm?: number;
}

export async function getSystemStatus(): Promise<SystemStatus> {
    return fetchAPI<SystemStatus>('/dashboard/status');
}

export async function getDashboardStats(): Promise<DashboardStatsData> {
    return fetchAPI<DashboardStatsData>('/dashboard/stats');
}

export async function getRecentActivity(limit: number = 10): Promise<RecentActivityItem[]> {
    return fetchAPI<RecentActivityItem[]>(`/dashboard/recent-activity?limit=${limit}`);
}

export async function getRegionalFinancials(year?: number): Promise<RegionalFinancial[]> {
    const params = year ? `?year=${year}` : '';
    return fetchAPI<RegionalFinancial[]>(`/dashboard/regional-financials${params}`);
}

export async function getFinancialOverview(year?: number): Promise<FinancialOverview> {
    const params = year ? `?year=${year}` : '';
    return fetchAPI<FinancialOverview>(`/dashboard/financial-overview${params}`);
}

export async function getTopTenants(limit: number = 10): Promise<Tenant[]> {
    return fetchAPI<Tenant[]>(`/dashboard/top-tenants?limit=${limit}`);
}

export async function refreshDashboardMetrics(): Promise<{ status: string; message: string }> {
    return fetchAPI('/dashboard/refresh-metrics', { method: 'POST' });
}

export interface AnalyticsCostSummary {
    total: number;
    by_category: Record<string, number>;
    by_region: Record<string, number>;
    year_over_year: {
        current: number;
        previous: number;
        change_percent: number;
    };
}

export interface RegionalCostBreakdown {
    region: string;
    total: number;
    categories: Record<string, number>;
    property_count: number;
    average_per_property: number;
}

export async function getAnalyticsCostSummary(): Promise<AnalyticsCostSummary> {
    return fetchAPI<AnalyticsCostSummary>('/analytics/costs/summary');
}

export async function getAnalyticsRegionalCosts(
    groupBy: 'category' | 'property' | 'month' = 'category'
): Promise<RegionalCostBreakdown[]> {
    return fetchAPI<RegionalCostBreakdown[]>(`/analytics/costs/regional?group_by=${groupBy}`);
}

export const dashboardApi = {
    status: getSystemStatus,
    stats: getDashboardStats,
    recentActivity: getRecentActivity,
    regionalFinancials: getRegionalFinancials,
    financialOverview: getFinancialOverview,
    topTenants: getTopTenants,
    refreshMetrics: refreshDashboardMetrics,
    analytics: {
        costSummary: getAnalyticsCostSummary,
        regionalCosts: getAnalyticsRegionalCosts,
    },
};
