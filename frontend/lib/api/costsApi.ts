import { fetchAPI } from './client';

export interface CostSummary {
    total: number;
    by_category: Record<string, number>;
    by_service: Record<string, number>;
    period: string;
}

export interface CostByService {
    service: string;
    total: number;
    count: number;
    average: number;
}

export interface CostTimelineEntry {
    period: string;
    total: number;
    by_category: Record<string, number>;
}

export interface LatestCost {
    cost_id: string;
    property_id: string;
    property_name: string;
    amount: number;
    category: string;
    date: string;
    description: string;
}

export interface CostExport {
    data: Array<Record<string, unknown>>;
    total_records: number;
    generated_at: string;
}

export async function getCostSummary(): Promise<CostSummary> {
    return fetchAPI<CostSummary>('/costs/summary');
}

export async function getCostsByService(): Promise<CostByService[]> {
    return fetchAPI<CostByService[]>('/costs/by-service');
}

export async function getCostTimeline(startDate?: string, endDate?: string): Promise<CostTimelineEntry[]> {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const query = params.toString();
    return fetchAPI<CostTimelineEntry[]>(`/costs/timeline${query ? `?${query}` : ''}`);
}

export async function getLatestCosts(limit: number = 10): Promise<LatestCost[]> {
    return fetchAPI<LatestCost[]>(`/costs/latest?limit=${limit}`);
}

export async function collectCosts(): Promise<{ status: string; message: string }> {
    return fetchAPI('/costs/collect', { method: 'POST' });
}

export async function exportCosts(format: 'json' | 'csv' = 'json'): Promise<CostExport> {
    return fetchAPI<CostExport>(`/costs/export?format=${format}`);
}

export interface BudgetSummary {
    year: number;
    total_budgeted: number;
    total_actual: number;
    variance: number;
    variance_percent: number;
    by_property: Array<{
        property_id: string;
        property_name: string;
        budgeted: number;
        actual: number;
        variance: number;
    }>;
}

export interface PropertyBudget {
    property_id: string;
    year: number;
    categories: Array<{
        category: string;
        budgeted: number;
        actual: number;
        variance: number;
    }>;
    total_budgeted: number;
    total_actual: number;
}

export interface BudgetVarianceAnalysis {
    property_id: string;
    property_name: string;
    year: number;
    variance_percent: number;
    over_budget_categories: string[];
    under_budget_categories: string[];
    recommendations: string[];
}

export interface ConsumptionByYear {
    year: number;
    total: number;
    by_category: Record<string, number>;
}

export async function getBudgetSummary(year: number): Promise<BudgetSummary> {
    return fetchAPI<BudgetSummary>(`/cost-management/budgets/summary?year=${year}`);
}

export async function getPropertyBudget(propertyId: string, year: number): Promise<PropertyBudget> {
    return fetchAPI<PropertyBudget>(`/cost-management/budgets/${propertyId}?year=${year}`);
}

export async function generateBudgets(): Promise<{ status: string; generated: number }> {
    return fetchAPI('/cost-management/budgets/generate', { method: 'POST' });
}

export async function generateBudgetFromConsumption(
    propertyId: string,
    year: number
): Promise<PropertyBudget> {
    return fetchAPI('/cost-management/budgets/generate-from-consumption', {
        method: 'POST',
        body: JSON.stringify({ property_id: propertyId, year }),
    });
}

export async function generateBudgetFromGL(
    propertyId: string,
    year: number
): Promise<PropertyBudget> {
    return fetchAPI('/cost-management/budgets/generate-from-gl', {
        method: 'POST',
        body: JSON.stringify({ property_id: propertyId, year }),
    });
}

export async function getConsumptionByYear(): Promise<ConsumptionByYear[]> {
    return fetchAPI<ConsumptionByYear[]>('/cost-management/costs/consumption-by-year');
}

export async function getMissingBudgets(year: number): Promise<string[]> {
    return fetchAPI<string[]>(`/cost-management/budgets/missing?year=${year}`);
}

export async function getCostForecast(propertyId: string): Promise<{
    property_id: string;
    months: Array<{ month: string; predicted: number; confidence: number }>;
}> {
    return fetchAPI(`/cost-management/costs/forecast/${propertyId}`);
}

export async function getBudgetVarianceAnalysis(): Promise<BudgetVarianceAnalysis[]> {
    return fetchAPI<BudgetVarianceAnalysis[]>('/cost-management/costs/analysis/budget-variance');
}

export async function getCostManagementHealth(): Promise<{
    status: string;
    last_sync: string;
    missing_budgets: number;
}> {
    return fetchAPI('/cost-management/health');
}

export const costsApi = {
    summary: getCostSummary,
    byService: getCostsByService,
    timeline: getCostTimeline,
    latest: getLatestCosts,
    collect: collectCosts,
    export: exportCosts,
    budget: {
        summary: getBudgetSummary,
        byProperty: getPropertyBudget,
        generate: generateBudgets,
        generateFromConsumption: generateBudgetFromConsumption,
        generateFromGL: generateBudgetFromGL,
        missing: getMissingBudgets,
        variance: getBudgetVarianceAnalysis,
    },
    costManagement: {
        consumptionByYear: getConsumptionByYear,
        forecast: getCostForecast,
        health: getCostManagementHealth,
    },
};
