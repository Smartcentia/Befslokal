import { fetchAPI } from "./client";

const BASE = "/finance-budget";

export interface FinanceBudgetByProperty {
  property_id: string;
  property_name: string;
  region: string;
  total: number;
  by_category: Record<string, number>;
}

export interface FinanceBudgetSummary {
  year: number;
  data_source: string;
  through_month?: number | null;
  total_nok: number;
  total_eiendommer_nok: number;
  total_direktorat_nok: number;
  antall_eiendommer: number;
  by_property: FinanceBudgetByProperty[];
  by_category: Record<string, number>;
  direktorat: {
    total: number;
    by_category: Record<string, number>;
  };
}

export interface FinanceBudgetPropertyDetail {
  property_id: string;
  year: number;
  total: number;
  by_category: Record<string, number>;
  monthly: { month: number; konto: string; konto_navn: string; category: string; amount: number }[];
}

export interface FinanceBudgetImportReport {
  total_rows: number;
  inserted: number;
  matched_properties: number;
  direktorat_rows: number;
  total_2025_nok: number;
  total_2026_nok: number;
  skipped: { no_periode: number; wrong_year: number; zero_amount: number; unknown_konto: number };
  unmatched_koststeder_count: number;
  unmatched_koststeder: string[];
}

export async function getFinanceBudgetSummary(
  year: number,
  dataSource?: string,
  throughMonth?: number,
): Promise<FinanceBudgetSummary> {
  const params = new URLSearchParams({ year: String(year) });
  if (dataSource) params.set("data_source", dataSource);
  if (throughMonth != null) params.set("through_month", String(throughMonth));
  const resolvedDs = dataSource ?? `finance_dept_${year}`;
  try {
    return await fetchAPI<FinanceBudgetSummary>(`${BASE}/summary?${params}`);
  } catch {
    return {
      year,
      data_source: resolvedDs,
      through_month: throughMonth ?? null,
      total_nok: 0,
      total_eiendommer_nok: 0,
      total_direktorat_nok: 0,
      antall_eiendommer: 0,
      by_property: [],
      by_category: {},
      direktorat: { total: 0, by_category: {} },
    };
  }
}

export async function getFinanceBudgetByProperty(
  propertyId: string,
  year: number,
  dataSource?: string,
): Promise<FinanceBudgetPropertyDetail | null> {
  try {
    const params = new URLSearchParams({ year: String(year) });
    if (dataSource) params.set("data_source", dataSource);
    return await fetchAPI<FinanceBudgetPropertyDetail>(`${BASE}/by-property/${propertyId}?${params}`);
  } catch {
    return null;
  }
}

export async function importFinanceBudget(file: File): Promise<{ status: string; report: FinanceBudgetImportReport }> {
  const formData = new FormData();
  formData.append("file", file);
  return fetchAPI(`${BASE}/import`, { method: "POST", body: formData });
}

export interface Kontant2026ImportReport {
  status: string;
  inserted: number;
  skipped_zero_amount: number;
  unmatched_koststeder: number;
  total_2026_nok: number;
}

export async function importKontant2026(file: File): Promise<Kontant2026ImportReport> {
  const formData = new FormData();
  formData.append("file", file);
  return fetchAPI("/agresso/import-kontant-2026", { method: "POST", body: formData });
}
