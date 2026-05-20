import { fetchAPI } from './client';

export interface StprpItem {
  sak_id: number | string;
  sesjon?: string | null;
  title?: string | null;
  short_title?: string | null;
  reference?: string | null;
  updated_date?: string | null;
  date?: string | null;
  prop_url?: string | null;
  storting_sak_url?: string | null;
}

export interface AnnualReportItem {
  year: number;
  title: string;
  page_url?: string | null;
  pdf_url?: string | null;
  status?: string;
}

export interface SsbShortlistItem {
  id: string;
  label: string;
  updated?: string;
  firstPeriod?: string;
  lastPeriod?: string;
  variableNames?: string[];
  metadataUrl?: string | null;
  dataUrl?: string | null;
}

export interface BarnevernReportsAnalysis {
  generated_at: string;
  summary: {
    stprp_count: number;
    annual_report_total: number;
    annual_report_pdf_count: number;
    ssb_table_count: number;
  };
  highlights: string[];
  risks: string[];
  recommended_actions: string[];
}

export interface PredictionExcelFile {
  filename: string;
  size_bytes: number;
  updated_at: string;
  download_url: string;
}

export async function getStprpBufdir() {
  return fetchAPI<{ generated_at: string; count: number; items: StprpItem[] }>('/barnevern-docs/stprp');
}

export async function getBufdirAnnualReports() {
  return fetchAPI<{ generated_at: string; count: number; items: AnnualReportItem[] }>('/barnevern-docs/annual-reports');
}

export async function getSsbBufdirShortlist() {
  return fetchAPI<{ generated_at: string; count: number; items: SsbShortlistItem[] }>('/barnevern-docs/ssb-shortlist');
}

export async function getBarnevernReportsAnalysis() {
  return fetchAPI<BarnevernReportsAnalysis>('/barnevern-docs/analysis');
}

export async function regenerateBarnevernReportsAnalysis() {
  return fetchAPI<{ status: string; analysis: BarnevernReportsAnalysis }>('/barnevern-docs/analysis/regenerate', {
    method: 'POST',
  });
}

export async function listPredictionExcelFiles() {
  return fetchAPI<{ count: number; items: PredictionExcelFile[] }>('/barnevern-docs/prediction-excel');
}

// ── BFD Statsbudsjettet ──────────────────────────────────────────────────────

export interface BfdPost {
  post: string;
  navn: string;
  bevilget: number;
}

export interface BfdKapittel {
  kap: number;
  navn: string;
  poster: BfdPost[];
}

export interface StatsbudsjettetBfdYear {
  kilde: string;
  enhet: string;
  sist_oppdatert: string;
  year: number;
  kapitler: BfdKapittel[];
}

export async function getStatsbudsjettetBfdYear(year: number) {
  return fetchAPI<StatsbudsjettetBfdYear>(`/barnevern-docs/statsbudsjettet?year=${year}`);
}

export interface GlNasjonalTotal {
  year: number;
  // GL-baserte felt (eiendomsrelaterte kostnader fra BEFS)
  eiendom_total_nok: number;
  lonn_total_nok: number;
  familievern_eiendom_nok: number;
  // Innkjøpsanalyse-felt (nasjonale totaler fra Excel-import)
  kjoep_bv_tjenester_nok?: number;
  lokaler_nok?: number;
  varer_tjenester_nok?: number;
  investeringer_nok?: number;
  tilskudd_nok?: number;
  klientkostnader_nok?: number;
  innkjop_har_data?: boolean;
}

export async function getGlNasjonalTotal(year: number) {
  return fetchAPI<GlNasjonalTotal>(`/financials/gl-nasjonal-total?year=${year}`);
}
