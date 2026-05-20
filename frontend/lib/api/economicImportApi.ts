import { fetchAPI } from './client';

export interface EconomicStatus {
  gl_transactions: {
    count: number;
    min_period: string | null;
    max_period: string | null;
  };
  budget: {
    count: number;
    years_covered: number[];
  };
  text_content: { count: number };
  socioeconomic_data: { count: number };
  property_coverage: {
    total_properties: number;
    properties_with_gl_data: number;
    properties_without_gl_data: number;
  };
  top_properties_by_transactions: Array<{
    property_name: string;
    transaction_count: number;
  }>;
}

export interface CsvPreviewResult {
  total_rows: number;
  matched_rows: number;
  unmatched_rows: number;
  match_rate_pct: number;
  matched_properties: string[];
  sample_unmatched: string[];
  columns_found: string[];
}

export interface ImportResult {
  status: string;
  imported: number;
  errors: number;
  total_rows: number;
}

export interface MasterImportResult {
  status: string;
  imported: number;
  updated: number;
}

export async function getEconomicStatus(): Promise<EconomicStatus> {
  return fetchAPI<EconomicStatus>('/admin/economic-status');
}

export async function previewFinancialCsv(file: File): Promise<CsvPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  return fetchAPI<CsvPreviewResult>('/admin/economic-import/preview', {
    method: 'POST',
    body: formData,
  });
}

export async function importFinancialCsv(file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  return fetchAPI<ImportResult>('/admin/economic-import/financial-csv', {
    method: 'POST',
    body: formData,
  });
}

export async function importMasterCsv(file: File): Promise<MasterImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  return fetchAPI<MasterImportResult>('/admin/economic-import/master-csv', {
    method: 'POST',
    body: formData,
  });
}

export async function clearEconomicData(): Promise<{ status: string; message: string }> {
  return fetchAPI('/admin/economic-import/clear', { method: 'POST' });
}
