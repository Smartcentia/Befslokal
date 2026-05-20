"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  getEconomicStatus,
  previewFinancialCsv,
  importFinancialCsv,
  clearEconomicData,
  type EconomicStatus,
  type CsvPreviewResult,
  type ImportResult,
} from '@/lib/api/economicImportApi';
import { triggerBudgetPrediction, type PredictionResult } from '@/lib/api/budgetPredictionApi';
import { fetchAPI } from '@/lib/api/client';

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className={`glass-card p-5 border-l-4 ${color}`}>
      <p className="text-muted text-xs uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-foreground">{value.toLocaleString('no-NO')}</p>
      {sub && <p className="text-muted text-xs mt-1">{sub}</p>}
    </div>
  );
}

function formatPeriod(period: string | null): string {
  if (!period || period.length < 6) return '—';
  return `${period.slice(0, 4)}-${period.slice(4, 6)}`;
}

function BudgetPredictionSection() {
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<PredictionResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await triggerBudgetPrediction({ year: 2027 });
      setResult(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mb-10">
      <h2 className="text-lg font-semibold text-foreground mb-4">Budsjett-prediksjon 2027</h2>
      <div className="glass-card p-6">
        <div className="flex items-start gap-4 mb-5">
          <div className="p-2 bg-blue-500/10 rounded-lg shrink-0">
            <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground mb-1">Holt-Winters eksponensiell glatting</p>
            <p className="text-xs text-muted">
              Predikerer budsjett for 2027 for alle eiendommer basert på GL-historikk 2021–2025.
              Nyere år (2024–2025) vektes tyngre enn eldre data (α=0.7, β=0.3).
              Resultater lagres i budget-tabellen.
            </p>
          </div>
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-colors
            ${loading
              ? 'bg-white/5 text-muted cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white'
            }`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Beregner...
            </span>
          ) : 'Generer 2027-budsjett (Holt-Winters)'}
        </button>

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-sm font-medium text-green-400 mb-2">Prediksjon fullført for {result.year}</p>
            <div className="flex gap-6 text-sm">
              <span className="text-foreground">
                <span className="font-bold">{result.processed}</span>
                <span className="text-muted ml-1">eiendommer behandlet</span>
              </span>
              <span className="text-foreground">
                <span className="font-bold">{result.skipped}</span>
                <span className="text-muted ml-1">hoppet over (ingen GL-data)</span>
              </span>
            </div>
            {result.errors.length > 0 && (
              <details className="mt-3">
                <summary className="text-xs text-yellow-400 cursor-pointer">
                  {result.errors.length} feil under kjøring
                </summary>
                <ul className="mt-2 space-y-1">
                  {result.errors.map((e, i) => (
                    <li key={i} className="text-xs text-muted font-mono">{e}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default function EconomicDataPage() {
  const [status, setStatus] = useState<EconomicStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvPreviewResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [clearing, setClearing] = useState(false);
  const [showDanger, setShowDanger] = useState(false);

  // Lønnskostnad CSV-import
  const [salaryFile, setSalaryFile] = useState<File | null>(null);
  const [salaryImporting, setSalaryImporting] = useState(false);
  const [salaryResult, setSalaryResult] = useState<{
    rows_parsed: number;
    rows_matched: number;
    rows_unmatched: number;
    match_rate_pct: number;
    unmatched_names: string[];
  } | null>(null);
  const [salaryError, setSalaryError] = useState<string | null>(null);

  const loadStatus = async () => {
    setStatusLoading(true);
    setStatusError(null);
    try {
      const data = await getEconomicStatus();
      setStatus(data);
    } catch (e: any) {
      setStatusError(e.message);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => { loadStatus(); }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setPreview(null);
    setImportResult(null);
    setActionError(null);
  };

  const handlePreview = async () => {
    if (!file) return;
    setPreviewLoading(true);
    setActionError(null);
    setPreview(null);
    try {
      const result = await previewFinancialCsv(file);
      setPreview(result);
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    if (!confirm('Er du sikker på at du vil importere denne CSV-filen til gl_transactions?')) return;
    setImportLoading(true);
    setActionError(null);
    try {
      const result = await importFinancialCsv(file);
      setImportResult(result);
      await loadStatus();
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setImportLoading(false);
    }
  };

  const handleClear = async () => {
    if (!confirm('ADVARSEL: Dette sletter ALLE regnskapsdata (gl_transactions, budget, text_content, socioeconomic_data). Er du helt sikker?')) return;
    setClearing(true);
    setActionError(null);
    try {
      await clearEconomicData();
      await loadStatus();
      setPreview(null);
      setImportResult(null);
    } catch (e: any) {
      setActionError(e.message);
    } finally {
      setClearing(false);
    }
  };

  const handleSalaryImport = async () => {
    if (!salaryFile) return;
    setSalaryImporting(true);
    setSalaryError(null);
    setSalaryResult(null);
    try {
      const formData = new FormData();
      formData.append('file', salaryFile);
      const res = await fetchAPI<{
        rows_parsed: number;
        rows_matched: number;
        rows_unmatched: number;
        match_rate_pct: number;
        unmatched_names: string[];
      }>('/admin/economic-import/salary-costs', {
        method: 'POST',
        body: formData,
      });
      setSalaryResult(res);
    } catch (e: any) {
      setSalaryError(e.message || 'Import feilet');
    } finally {
      setSalaryImporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/admin" className="p-2 bg-white/5 border border-white/10 rounded-lg text-muted hover:text-foreground transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          </Link>
          <div>
            <h1 className="text-3xl font-bold bg-linear-to-r from-primary to-accent bg-clip-text text-transparent">
              Økonomidata Oversikt
            </h1>
            <p className="text-muted text-sm mt-1">Status, import og administrasjon av regnskapsdata</p>
          </div>
          <button
            onClick={loadStatus}
            disabled={statusLoading}
            className="ml-auto p-2 bg-white/5 border border-white/10 rounded-lg text-muted hover:text-foreground transition-colors"
            title="Oppdater status"
          >
            <svg className={`w-5 h-5 ${statusLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {/* ─── Seksjon A: DB Status ─── */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-foreground mb-4">Nåværende DB-tilstand</h2>

          {statusError && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm mb-4">
              Klarte ikke å laste status: {statusError}
            </div>
          )}

          {statusLoading && !status ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="glass-card p-5 h-24 animate-pulse bg-white/5" />
              ))}
            </div>
          ) : status ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <StatCard
                  label="GL Transaksjoner"
                  value={status.gl_transactions.count}
                  sub={status.gl_transactions.count > 0
                    ? `${formatPeriod(status.gl_transactions.min_period)} → ${formatPeriod(status.gl_transactions.max_period)}`
                    : 'Ingen data importert'}
                  color="border-blue-500"
                />
                <StatCard
                  label="Budsjett-poster"
                  value={status.budget.count}
                  sub={status.budget.years_covered.length > 0
                    ? `År: ${status.budget.years_covered.join(', ')}`
                    : 'Ingen budsjett'}
                  color="border-green-500"
                />
                <StatCard
                  label="Tekstinnhold"
                  value={status.text_content.count}
                  color="border-purple-500"
                />
                <StatCard
                  label="Sosioøkonomi"
                  value={status.socioeconomic_data.count}
                  color="border-orange-500"
                />
              </div>

              {/* Property coverage */}
              <div className="glass-card p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-foreground">Eiendomsdekning (GL-data)</p>
                  <p className="text-sm text-muted">
                    <span className="font-bold text-foreground">{status.property_coverage.properties_with_gl_data}</span>
                    {' '}/{' '}
                    {status.property_coverage.total_properties} eiendommer
                  </p>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 mb-3">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${status.property_coverage.total_properties > 0
                        ? (status.property_coverage.properties_with_gl_data / status.property_coverage.total_properties) * 100
                        : 0}%`
                    }}
                  />
                </div>
                {status.top_properties_by_transactions.length > 0 && (
                  <div>
                    <p className="text-xs text-muted mb-2">Topp eiendommer etter transaksjonsvolum:</p>
                    <div className="space-y-1">
                      {status.top_properties_by_transactions.map((p, i) => (
                        <div key={i} className="flex justify-between text-xs">
                          <span className="text-foreground truncate max-w-xs">{p.property_name}</span>
                          <span className="text-muted ml-2">{p.transaction_count.toLocaleString('no-NO')} transaksjoner</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </section>

        {/* ─── Seksjon B: Import ─── */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-foreground mb-4">Importer Xledger/Visma CSV</h2>

          <div className="glass-card p-6">
            <div className="mb-6">
              <label className="block text-sm font-medium text-foreground mb-2">Velg CSV-fil</label>
              <p className="text-xs text-muted mb-3">
                Forventet format: semikolon-separert CSV med kolonner som BA, Regioner, Avdeling, Dim 2(T), Konto, Kontantbeløp, Kont.periode, Resk.nr(T).
              </p>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-500/10 file:text-blue-400 hover:file:bg-blue-500/20 transition-colors"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handlePreview}
                disabled={!file || previewLoading}
                className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2
                  ${!file || previewLoading ? 'bg-white/5 text-muted cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white'}`}
              >
                {previewLoading ? (
                  <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Analyserer...</>
                ) : (
                  <><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg> 1. Analyser (dry-run)</>
                )}
              </button>

              {preview && (
                <button
                  onClick={handleImport}
                  disabled={importLoading}
                  className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2
                    ${importLoading ? 'bg-white/5 text-muted cursor-not-allowed' : 'bg-green-600 hover:bg-green-500 text-white'}`}
                >
                  {importLoading ? (
                    <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Importerer...</>
                  ) : (
                    <><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg> 2. Gjennomfør Import</>
                  )}
                </button>
              )}
            </div>

            {actionError && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                {actionError}
              </div>
            )}

            {/* Preview resultat */}
            {preview && !importResult && (
              <div className="mt-6 p-5 bg-slate-900/50 border border-white/10 rounded-lg">
                <h3 className="text-sm font-semibold text-foreground mb-4">Forhåndsvisning</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-foreground">{preview.total_rows.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Totale rader</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">{preview.matched_rows.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Matchet</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-400">{preview.unmatched_rows.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Umatchet (hoppes over)</p>
                  </div>
                  <div className="text-center">
                    <p className={`text-2xl font-bold ${preview.match_rate_pct >= 80 ? 'text-green-400' : preview.match_rate_pct >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {preview.match_rate_pct}%
                    </p>
                    <p className="text-xs text-muted">Match-rate</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  {preview.matched_properties.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-foreground mb-2">
                        Matchede eiendommer ({preview.matched_properties.length}):
                      </p>
                      <ul className="text-xs text-muted space-y-1 max-h-32 overflow-y-auto">
                        {preview.matched_properties.map((p, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <span className="text-green-400">✓</span> {p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {preview.sample_unmatched.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-foreground mb-2">
                        Eksempler på umatchede Dim 2-verdier:
                      </p>
                      <ul className="text-xs text-muted space-y-1 max-h-32 overflow-y-auto">
                        {preview.sample_unmatched.map((v, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <span className="text-red-400">✗</span> {v}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <p className="mt-4 text-xs text-muted">
                  Kolonner funnet: {preview.columns_found.join(', ')}
                </p>
              </div>
            )}

            {/* Import resultat */}
            {importResult && (
              <div className="mt-6 p-5 bg-green-500/10 border border-green-500/20 rounded-lg">
                <h3 className="text-sm font-semibold text-green-400 mb-3">Import fullført</h3>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <p className="text-xl font-bold text-foreground">{importResult.imported.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Importert</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-red-400">{importResult.errors.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Feil / umatchet</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-muted">{importResult.total_rows.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Totale rader</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ─── Seksjon C: Lønnskostnader CSV-import ─── */}
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-foreground mb-4">Lønnskostnader – CSV-import</h2>
          <div className="glass-card p-6">
            <p className="text-xs text-muted mb-4">
              Format: Innkjøpsanalyse lønnsutgifter pivot-CSV. Kolonneheader på rad 9.
              Seksjoner: <strong>Faste stillinger</strong>, <strong>Lønn vikarer</strong>, <strong>Arbeidsgiveravgift</strong>.
              Rader matches mot eiendommer på navn (eksakt, deretter fuzzy substring).
            </p>
            <div className="mb-5">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => {
                  setSalaryFile(e.target.files?.[0] || null);
                  setSalaryResult(null);
                  setSalaryError(null);
                }}
                className="block w-full text-sm text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-rose-500/10 file:text-rose-400 hover:file:bg-rose-500/20 transition-colors"
              />
            </div>
            <button
              onClick={handleSalaryImport}
              disabled={!salaryFile || salaryImporting}
              className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2
                ${!salaryFile || salaryImporting ? 'bg-white/5 text-muted cursor-not-allowed' : 'bg-rose-600 hover:bg-rose-500 text-white'}`}
            >
              {salaryImporting ? (
                <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Importerer...</>
              ) : 'Importer lønnskostnader'}
            </button>

            {salaryError && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                {salaryError}
              </div>
            )}

            {salaryResult && (
              <div className="mt-5 p-5 bg-rose-500/5 border border-rose-500/20 rounded-lg">
                <h3 className="text-sm font-semibold text-rose-400 mb-4">Import fullført</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-foreground">{salaryResult.rows_parsed.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Rader lest</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">{salaryResult.rows_matched.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Matchet</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-400">{salaryResult.rows_unmatched.toLocaleString('no-NO')}</p>
                    <p className="text-xs text-muted">Umatchet</p>
                  </div>
                  <div className="text-center">
                    <p className={`text-2xl font-bold ${salaryResult.match_rate_pct >= 80 ? 'text-green-400' : salaryResult.match_rate_pct >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {salaryResult.match_rate_pct}%
                    </p>
                    <p className="text-xs text-muted">Match-rate</p>
                  </div>
                </div>
                {salaryResult.unmatched_names.length > 0 && (
                  <details>
                    <summary className="text-xs text-yellow-400 cursor-pointer mb-2">
                      {salaryResult.unmatched_names.length} umatchede institusjonsnavn (lagret uten eiendom)
                    </summary>
                    <ul className="text-xs text-muted space-y-1 max-h-40 overflow-y-auto mt-2">
                      {salaryResult.unmatched_names.map((n, i) => (
                        <li key={i} className="flex items-center gap-1">
                          <span className="text-red-400">✗</span> {n}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            )}
          </div>
        </section>

        {/* ─── Seksjon D: Budsjett-prediksjon ─── */}
        <BudgetPredictionSection />

        {/* ─── Seksjon E: Farlige handlinger ─── */}
        <section>
          <button
            onClick={() => setShowDanger(!showDanger)}
            className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 transition-colors mb-3"
          >
            <svg className={`w-4 h-4 transition-transform ${showDanger ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Farlige handlinger
          </button>

          {showDanger && (
            <div className="glass-card p-6 border-red-500/30">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-red-500/10 rounded-lg shrink-0">
                  <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground mb-1">Nullstill alle økonomitabeller</h3>
                  <p className="text-sm text-muted mb-4">
                    Sletter ALL data fra gl_transactions, budget, text_content og socioeconomic_data. Tilbakestiller også finansfelt i eiendommer og kontrakter. Kan ikke angres.
                  </p>
                  <button
                    onClick={handleClear}
                    disabled={clearing}
                    className={`px-5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2
                      ${clearing ? 'bg-white/5 text-muted cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white'}`}
                  >
                    {clearing ? (
                      <><svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Nullstiller...</>
                    ) : (
                      <><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg> Nullstill Økonomidata</>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
