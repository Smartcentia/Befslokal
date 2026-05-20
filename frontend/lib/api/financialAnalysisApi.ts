import { fetchAPI } from './client';

export interface YearSummary {
    year: number;
    gl_totalt: number;
    gl_husleie: number;
    gl_andre: number;
    salary_totalt: number;
    property_count: number;
}

export interface SupplierStats {
    total_portfolio_cost: number;
    supplier_count: number;
    suppliers: Array<{
        name: string;
        total_amount: number;
        property_count: number;
        category: string;
        details: Array<{
            property_id: string;
            name: string;
            amount: number;
            category: string;
            date?: string;
        }>;
    }>;
}

/** GL uten property_id — sentraløkonomi / ikke-eiendom */
export interface GlUtenEiendomRad {
    dim1_kode: string;
    dim1_navn: string;
    region: string;
    antall: number;
    sum_belop: number;
}

export interface GlUtenEiendomResponse {
    ar: number;
    oppsummering: {
        antall_transaksjoner: number;
        sum_belop: number;
        antall_koststed_grupper: number;
    };
    rader: GlUtenEiendomRad[];
}

export interface CommonPatterns {
    total_properties: number;
    common_categories: Array<{
        category: string;
        property_count: number;
        percentage: number;
        avg_amount: number;
    }>;
    common_providers: Array<{
        provider: string;
        transaction_count: number;
    }>;
    /** Geografiske mønstre: kostnader per region */
    regional_patterns?: {
        by_region: Array<{
            region: string;
            property_count: number;
            total_costs: number;
            avg_costs: number;
            avg_rent: number;
            cost_to_rent_ratio: number;
            cost_per_sqm?: number;
        }>;
        above_below_regional_avg: Array<{
            property: string;
            region: string;
            costs: number;
            regional_avg: number;
            deviation_pct: number;
        }>;
    };
    /** Leverandørkoncentration: få vs mange leverandører */
    supplier_concentration?: {
        few_suppliers: Array<{ property: string; supplier_count: number; total_costs: number }>;
        many_suppliers: Array<{ property: string; supplier_count: number; total_costs: number }>;
        high_concentration: Array<{ property: string; top_provider: string; share_pct: number; amount: number }>;
    };
    /** Leverandørprisvariasjon */
    supplier_price_variation?: {
        by_provider: Array<{
            provider: string;
            property_count: number;
            mean_amount: number;
            coefficient_of_variation_pct: number;
        }>;
    };
    /** Tidsmønstre (når date er fylt) */
    time_patterns?: {
        date_coverage_pct: number;
        by_year: Array<{ year: number; total: number }>;
        by_month: Array<{ month: number; total: number }>;
        seasonal?: { winter_total: number; summer_total: number };
    };
    /** Kategori-kombinasjoner (bundles) */
    category_bundles?: {
        common_bundles: Array<{ categories: string[]; property_count: number }>;
    };
    /** Skaleringsmønstre (kostnad per kvm) */
    scaling_patterns?: {
        cost_per_sqm: Array<{ property: string; cost_per_sqm: number; total_costs: number; total_area: number }>;
        outliers: Array<{ property: string; cost_per_sqm: number; deviation: number }>;
        message?: string;
    };
    /** Provider-kategori-mønstre */
    provider_category_patterns?: {
        provider_category_matrix: Array<{
            provider: string;
            total_amount: number;
            dominant_category: string;
            specialization_pct: number;
        }>;
    };
    /** Cluster-analyse */
    cluster_patterns?: {
        clusters: Array<{
            cluster_id: number;
            label: string;
            property_count: number;
            properties: string[];
        }>;
        message?: string;
    };
    /** 9. Bygningsalder vs kostnad */
    building_age_patterns?: { by_age_bucket: Array<{ age_bucket: string; property_count: number; avg_costs: number }> };
    /** 10. Energimerking vs kostnad */
    energy_label_patterns?: { by_energy_label: Array<{ label: string; property_count: number; avg_costs: number }> };
    /** 11. Brukstype vs kostnad */
    usage_type_patterns?: { by_usage: Array<{ usage: string; property_count: number; avg_costs: number }> };
    /** 12. Kostnad per kvm per kategori */
    cost_per_sqm_by_category?: { by_category: Array<{ category: string; property_count: number; avg_per_sqm: number }>; message?: string };
    /** 13. Budsjett vs faktisk */
    budget_variance_patterns?: { year: number; variances: Array<{ property: string; budget: number; actual: number; variance_pct: number }>; message?: string };
    /** 14. Risiko-kostnad */
    risk_cost_patterns?: { priority_list: Array<{ property: string; risk_score: number; priority_index: number }>; message?: string };
    /** 15. Leverandørportefølje-overlap */
    supplier_overlap_patterns?: { overlap_pairs: Array<{ property_a: string; property_b: string; jaccard: number }>; message?: string };
    /** 16. Manglende data */
    missing_data_patterns?: {
        high_rent_no_costs: string[];
        high_costs_no_rent: string[];
        expenses_without_date: number;
        total_expenses: number;
        costs_without_area: string[];
    };
    /** 17. Kommune */
    municipality_patterns?: { by_municipality: Array<{ municipality: string; property_count: number; total_costs: number }> };
    /** 18. Senter */
    center_patterns?: { by_center: Array<{ center_id: string; property_count: number; total_costs: number }> };
    /** 19. Transaksjonstetthet */
    transaction_density_patterns?: {
        low_density_few_transactions: string[];
        high_density_many_transactions: string[];
        highest_avg_per_expense: Array<{ property: string; avg: number }>;
    };
    /** 20. Kategori-diversifikasjon */
    category_diversification_patterns?: {
        single_category_high_costs: Array<{ property: string; category: string }>;
        many_categories: Array<{ property: string; category_count: number }>;
    };
}

export interface Forecast {
    property_id: string;
    forecast: Array<{
        year: number;
        predicted_cost: number;
    }>;
    trend: 'Increasing' | 'Decreasing' | 'Stable';
    annual_change_estimate: number;
    error?: string;
}

export interface Anomalies {
    property_id: string;
    anomaly_count: number;
    anomalies: Array<{
        year: number;
        amount: number;
        reason: string;
    }>;
    status: 'Normal' | 'Anomalies Detected';
    error?: string;
}

export const financialAnalysisApi = {
    /**
     * Get global supplier statistics across all properties
     */
    getSupplierStats: async (year?: number): Promise<SupplierStats> => {
        const params = year ? `?year=${year}` : '';
        return fetchAPI<SupplierStats>(`/financials/suppliers${params}`);
    },

    /**
     * Get the comprehensive supplier catalog from the pre-aggregated CSV via backend
     */
    getSupplierCatalog: async (): Promise<Array<{ Leverandør: string; Tjenester: string }>> => {
        return fetchAPI<Array<{ Leverandør: string; Tjenester: string }>>('/financials/supplier-catalog');
    },

    /**
     * Get common cost patterns across all properties
     */
    getCommonPatterns: async (year?: number): Promise<CommonPatterns> => {
        const params = year ? `?year=${year}` : '';
        return fetchAPI<CommonPatterns>(`/financials/patterns${params}`);
    },

    getRentGap: async (year?: number): Promise<any[]> => {
        const params = year ? `?year=${year}` : '';
        return fetchAPI<any[]>(`/financials/rent-gap${params}`);
    },

    getRentReconciliation: async (year?: number): Promise<any> => {
        const params = year ? `?year=${year}` : '';
        return fetchAPI<any>(`/financials/rent-reconciliation${params}`);
    },

    getYoyComparison: async (): Promise<any[]> => {
        return fetchAPI<any[]>('/financials/yoy-comparison');
    },

    getMonthlyBudgetActual: async (year?: number): Promise<any[]> => {
        const params = year ? `?year=${year}` : '';
        return fetchAPI<any[]>(`/financials/monthly-budget-actual${params}`);
    },

    /** Aggregert GL der property_id er NULL (per koststed) */
    getGlUtenEiendom: async (ar: number): Promise<GlUtenEiendomResponse> => {
        return fetchAPI<GlUtenEiendomResponse>(`/financials/gl-uten-eiendom?ar=${ar}`);
    },

    /**
     * Get ML-based cost forecast for a property
     */
    getPropertyForecast: async (propertyId: string, yearsAhead: number = 3): Promise<Forecast> => {
        return fetchAPI<Forecast>(`/admin/financial-analysis/property/${propertyId}/forecast?years_ahead=${yearsAhead}`);
    },

    /**
     * Detect spending anomalies for a property
     */
    getPropertyAnomalies: async (propertyId: string): Promise<Anomalies> => {
        return fetchAPI<Anomalies>(`/admin/financial-analysis/property/${propertyId}/anomalies`);
    },
};
