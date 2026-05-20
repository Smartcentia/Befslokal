import { fetchAPI } from './client';

export interface ProcurementRow {
  institution: string;
  property_id: string | null;
  property_name: string | null;
  by_region: Record<string, number>;
  total: number;
}

export interface ProcurementCategory {
  key: string;
  label: string;
  rows: ProcurementRow[];
  totals_by_region: Record<string, number>;
  grand_total: number;
}

export interface ProcurementGroup {
  group: string;
  categories: ProcurementCategory[];
}

export interface ProcurementPivot {
  year: number | null;
  region_filter: string | null;
  regions: string[];
  groups: ProcurementGroup[];
  total_transactions: number;
}

export async function getProcurementPivot(params?: {
  year?: number;
  region?: string;
  category?: string;
}): Promise<ProcurementPivot> {
  const query = new URLSearchParams();
  if (params?.year) query.set('year', String(params.year));
  if (params?.region) query.set('region', params.region);
  if (params?.category) query.set('category', params.category);
  const qs = query.toString();
  return fetchAPI<ProcurementPivot>(`/procurement/pivot${qs ? `?${qs}` : ''}`);
}

export interface DynamicPivotGroup {
  group: string;
  categories: ProcurementCategory[];
  totals_by_region: Record<string, number>;
  grand_total: number;
}

export interface DynamicPivot {
  year: number | null;
  region_filter: string | null;
  regions: string[];
  groups: DynamicPivotGroup[];
  total_transactions: number;
}

export async function getDynamicPivot(params?: {
  year?: number;
  region?: string;
}): Promise<DynamicPivot> {
  const query = new URLSearchParams();
  if (params?.year) query.set('year', String(params.year));
  if (params?.region) query.set('region', params.region);
  const qs = query.toString();
  return fetchAPI<DynamicPivot>(`/procurement/dynamic${qs ? `?${qs}` : ''}`);
}

// Per-region pivot (Kategori → Region → Institusjon, én totalkolonne)
export interface PerRegionRow {
  institution: string;
  property_id: string | null;
  property_name: string | null;
  total: number;
}

export interface PerRegionSection {
  region: string;
  rows: PerRegionRow[];
  region_total: number;
}

export interface PerRegionAccount {
  key: string;
  label: string;
  regions: PerRegionSection[];
  grand_total: number;
}

export interface PerRegionGroup {
  group: string;
  accounts: PerRegionAccount[];
  grand_total: number;
}

export interface PerRegionPivot {
  year: number | null;
  groups: PerRegionGroup[];
  total_transactions: number;
}

export async function getPerRegionPivot(params?: {
  year?: number;
}): Promise<PerRegionPivot> {
  const query = new URLSearchParams();
  if (params?.year) query.set('year', String(params.year));
  const qs = query.toString();
  return fetchAPI<PerRegionPivot>(`/procurement/per-region${qs ? `?${qs}` : ''}`);
}

// Institution drill-down
export interface InstitutionCostCategory {
  label: string;
  account_code: string;
  amount: number;
  pct: number;
}

export interface InstitutionSupplier {
  name: string;
  invoice_count: number;
  amount: number;
  pct: number;
}

export interface InstitutionMonthly {
  period: string;
  amount: number;
}

export interface InstitutionDetail {
  institution: string;
  year: number | null;
  property_id: string | null;
  region: string | null;
  grand_total: number;
  cost_by_category: InstitutionCostCategory[];
  top_suppliers: InstitutionSupplier[];
  monthly_trend: InstitutionMonthly[];
}

export async function getInstitutionDetail(name: string, year?: number): Promise<InstitutionDetail> {
  const query = new URLSearchParams({ name });
  if (year) query.set('year', String(year));
  return fetchAPI<InstitutionDetail>(`/procurement/institution?${query.toString()}`);
}

// Property profiles
export interface PropertyProfile {
  property_id: string;
  name: string;
  region: string;
  total_area: number | null;
  construction_year: number | null;
  energy_label: string | null;
  owner_name: string | null;
  total_cost: number;
  husleie_gl: number;
  strom: number;
  renhold: number;
  vedlikehold: number;
  cost_per_sqm: number | null;
  contract_rent: number | null;
  rent_delta: number | null;
  tx_count: number;
}

export interface PropertyProfiles {
  year: number | null;
  profiles: PropertyProfile[];
  total_properties: number;
}

export async function getPropertyProfiles(params?: { year?: number }): Promise<PropertyProfiles> {
  const query = new URLSearchParams();
  if (params?.year) query.set('year', String(params.year));
  const qs = query.toString();
  return fetchAPI<PropertyProfiles>(`/procurement/property-profiles${qs ? `?${qs}` : ''}`);
}
