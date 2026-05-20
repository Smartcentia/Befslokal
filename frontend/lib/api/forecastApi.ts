import { fetchAPI } from './client';

export interface ForecastMonth {
    month: string;
    predicted: number;
    lower_bound: number;
    upper_bound: number;
    confidence: number;
}

export interface PropertyForecast {
    property_id: string;
    property_name: string;
    base_year: number;
    forecast_months: ForecastMonth[];
    total_predicted: number;
    growth_rate: number;
    model_accuracy: number;
}

export interface VarianceReport {
    property_id: string;
    property_name: string;
    period: string;
    budgeted: number;
    actual: number;
    variance: number;
    variance_percent: number;
    status: 'on_track' | 'warning' | 'over_budget' | 'under_budget';
}

export interface VarianceTrend {
    property_id: string;
    periods: Array<{
        period: string;
        budgeted: number;
        actual: number;
        variance_percent: number;
    }>;
    trend_direction: 'improving' | 'stable' | 'worsening';
    average_variance: number;
}

export async function getPropertyForecast(propertyId: string): Promise<PropertyForecast> {
    return fetchAPI<PropertyForecast>(`/forecast/${propertyId}`);
}

export async function getVarianceReport(propertyId: string): Promise<VarianceReport> {
    return fetchAPI<VarianceReport>(`/variance/${propertyId}`);
}

export async function getVarianceTrend(propertyId: string): Promise<VarianceTrend> {
    return fetchAPI<VarianceTrend>(`/variance/trend/${propertyId}`);
}

export const forecastApi = {
    getPropertyForecast,
    getVarianceReport,
    getVarianceTrend,
};
