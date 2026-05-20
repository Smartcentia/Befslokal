import { fetchAPI } from "./client";

const BUDGET_BASE = "/cost-management/budgets";

export interface BudgetSummary {
  year: number;
  total_budget_nok: number;
  by_property: { property_id: string; total_annual_budget: number }[];
}

export interface BudgetByCategory {
  property: number;
  operations: number;
  investment: number;
  other: number;
}

export interface PropertyBudget {
  property_id: string;
  year: number;
  total_annual_budget: number;
  by_category?: BudgetByCategory;
  monthly_budgets: { year: number; month: number; category: string; amount: number }[];
}

export interface BudgetSummaryFilter {
  /** Eksakt match på budget.data_source (f.eks. "finance_dept_2026"). */
  dataSource?: string;
  /** NOT-match — alle rader unntatt eksakt verdi (NULL telles som ikke-match). */
  excludeDataSource?: string;
}

export async function getBudgetSummary(
  year: number = 2026,
  filter: BudgetSummaryFilter = {},
): Promise<BudgetSummary> {
  const params = new URLSearchParams({ year: String(year) });
  if (filter.dataSource) params.set("data_source", filter.dataSource);
  if (filter.excludeDataSource) params.set("exclude_data_source", filter.excludeDataSource);
  try {
    return await fetchAPI<BudgetSummary>(`${BUDGET_BASE}/summary?${params.toString()}`);
  } catch {
    return { year, total_budget_nok: 0, by_property: [] };
  }
}

/** Konstant for økonomi-avdelingens 2026-budsjett — brukes både ved import og ved henting. */
export const FINANCE_BUDGET_2026_SOURCE = "finance_dept_2026";

export async function getPropertyBudget(propertyId: string, year: number = 2026): Promise<PropertyBudget | null> {
  try {
    return await fetchAPI(`${BUDGET_BASE}/${propertyId}?year=${year}`);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Lønnskostnader
// ---------------------------------------------------------------------------

export interface SalaryCostEntry {
  property_id: string;
  property_name: string;
  faste_stillinger: number;
  vikarer: number;
  arbeidsgiveravgift: number;
  total: number;
}

export interface SalaryCostSummary {
  year: number;
  total: number;
  by_property: SalaryCostEntry[];
}

export async function getSalaryCosts(year: number): Promise<SalaryCostSummary | null> {
  try {
    return await fetchAPI<SalaryCostSummary>(`/financials/salary-costs?year=${year}`);
  } catch {
    return null;
  }
}

export async function getSalaryCostYears(): Promise<number[]> {
  try {
    const data = await fetchAPI<{ available_years: number[] }>('/financials/salary-costs/years');
    return data.available_years ?? [];
  } catch {
    return [];
  }
}
