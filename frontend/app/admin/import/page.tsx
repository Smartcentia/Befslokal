
"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { analyzeImport, executeImport, ImportAnalysisResponse } from '@/lib/api';
import { previewFinancialCsv, importFinancialCsv, importMasterCsv, type CsvPreviewResult } from '@/lib/api/economicImportApi';
import ImportAnalysisResult from '@/app/components/features/ImportAnalysisResult';

export default function AdminImportPage() {
    const [file, setFile] = useState<File | null>(null);
    const [type, setType] = useState<string>('party');
    const [analysis, setAnalysis] = useState<ImportAnalysisResponse | null>(null);
    const [financialPreview, setFinancialPreview] = useState<CsvPreviewResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [updateConflicts, setUpdateConflicts] = useState(false);

    const isFinancial = type === 'financial';
    const isMaster = type === 'master';

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setAnalysis(null);
            setFinancialPreview(null);
            setError(null);
            setSuccess(null);
        }
    };

    const runAnalysis = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        try {
            if (isFinancial) {
                const result = await previewFinancialCsv(file);
                setFinancialPreview(result);
            } else if (isMaster) {
                // Master CSV import has no preview step – go straight to import
                await runMasterImport();
            } else {
                const result = await analyzeImport(file, type);
                setAnalysis(result);
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const runMasterImport = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        try {
            const result = await importMasterCsv(file);
            setSuccess(`Masterdata importert! ${result.imported} nye eiendommer, ${result.updated} oppdatert.`);
            setFile(null);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const runImport = async () => {
        if (!file) return;
        if (!confirm("Er du sikker på at du vil gjennomføre importen? Dette kan endre data i systemet.")) return;

        setLoading(true);
        setError(null);
        try {
            if (isFinancial) {
                const result = await importFinancialCsv(file);
                setSuccess(`Import fullført! ${result.imported} transaksjoner importert, ${result.errors} feil av ${result.total_rows} rader.`);
                setFinancialPreview(null);
            } else {
                const result = await executeImport(file, type, updateConflicts);
                setSuccess(`Import fullført! ${result.imported} nye poster opprettet, ${result.updated} oppdatert.`);
                setAnalysis(null);
            }
            setFile(null);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/admin" className="p-2 bg-white rounded-lg shadow-sm text-slate-600 hover:bg-slate-50 transition-colors">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                    </Link>
                    <h1 className="text-3xl font-bold text-slate-800">Import av Data (CSV)</h1>
                </div>

                <div className="bg-white p-6 rounded-lg shadow-md border border-slate-200 mb-8">
                    <h2 className="text-xl font-semibold mb-6">Last opp fil</h2>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Velg datatype</label>
                            <select
                                value={type}
                                onChange={(e) => { setType(e.target.value); setAnalysis(null); }}
                                className="w-full p-2 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                            >
                                <option value="party">Parter / Aktører</option>
                                <option value="property">Eiendommer</option>
                                <option value="contract">Kontrakter</option>
                                <option value="financial">Finansielle data (GL / Xledger)</option>
                                <option value="master">Masterdata eiendommer (totalny.txt / Eie1212)</option>
                            </select>
                            <p className="text-xs text-slate-500 mt-1">Velg hvilken type data filen inneholder.</p>
                        </div>

                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-slate-700 mb-2">Velg CSV-fil</label>
                            <input
                                type="file"
                                accept=".csv,.txt"
                                onChange={handleFileChange}
                                className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition-colors"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end gap-4">
                        <button
                            onClick={runAnalysis}
                            disabled={!file || loading}
                            className={`px-6 py-2 rounded-lg font-medium text-white transition-colors flex items-center gap-2
                                ${!file || loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 shadow-lg'}`}
                        >
                            {loading ? (isMaster ? 'Importerer...' : 'Analyserer...') : (isMaster ? '1. Importer Masterdata' : '1. Analyser Fil')}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-8 flex items-center gap-3">
                        <svg className="w-6 h-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <div>
                            <div className="font-bold">Feil oppstod</div>
                            <div>{error}</div>
                        </div>
                    </div>
                )}

                {success && (
                    <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-lg mb-8 flex items-center gap-3">
                        <svg className="w-6 h-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        <div>
                            <div className="font-bold">Suksess</div>
                            <div>{success}</div>
                        </div>
                    </div>
                )}

                {financialPreview && (
                    <div className="bg-slate-900 p-6 rounded-lg shadow-xl border border-slate-700 text-slate-100 mb-8">
                        <h2 className="text-xl font-bold text-white mb-4">Forhåndsvisning – Finansielle data</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-slate-800 p-4 rounded-lg">
                                <p className="text-slate-400 text-xs mb-1">Totalt rader</p>
                                <p className="text-2xl font-bold text-white">{financialPreview.total_rows.toLocaleString('no-NO')}</p>
                            </div>
                            <div className="bg-green-900/40 p-4 rounded-lg border border-green-700/30">
                                <p className="text-slate-400 text-xs mb-1">Matchet eiendommer</p>
                                <p className="text-2xl font-bold text-green-400">{financialPreview.matched_rows.toLocaleString('no-NO')}</p>
                            </div>
                            <div className="bg-red-900/40 p-4 rounded-lg border border-red-700/30">
                                <p className="text-slate-400 text-xs mb-1">Ikke matchet</p>
                                <p className="text-2xl font-bold text-red-400">{financialPreview.unmatched_rows.toLocaleString('no-NO')}</p>
                            </div>
                            <div className="bg-blue-900/40 p-4 rounded-lg border border-blue-700/30">
                                <p className="text-slate-400 text-xs mb-1">Match-rate</p>
                                <p className="text-2xl font-bold text-blue-400">{financialPreview.match_rate_pct}%</p>
                            </div>
                        </div>
                        {financialPreview.sample_unmatched.length > 0 && (
                            <div className="mb-6">
                                <p className="text-slate-400 text-sm mb-2">Eksempel på ikke-matchede verdier (hoppes over):</p>
                                <div className="flex flex-wrap gap-2">
                                    {financialPreview.sample_unmatched.map((v, i) => (
                                        <span key={i} className="bg-red-900/30 border border-red-700/30 text-red-300 text-xs px-2 py-1 rounded font-mono">{v}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div className="flex justify-end">
                            <button
                                onClick={runImport}
                                disabled={loading}
                                className={`px-8 py-3 rounded-lg font-bold text-white transition-all flex items-center gap-2
                                    ${loading ? 'bg-slate-600 cursor-not-allowed' : 'bg-green-600 hover:bg-green-500 shadow-lg'}`}
                            >
                                {loading ? 'Importerer...' : `2. Importer ${financialPreview.matched_rows.toLocaleString('no-NO')} transaksjoner`}
                            </button>
                        </div>
                    </div>
                )}

                {analysis && (
                    <div className="bg-slate-900 p-6 rounded-lg shadow-xl border border-slate-700 text-slate-100">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                Analyseresultat
                            </h2>
                            <div className="text-sm text-slate-400">
                                Fil: <span className="text-white font-mono">{file?.name}</span>
                            </div>
                        </div>

                        <ImportAnalysisResult analysis={analysis} />

                        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
                            <label className="flex items-center gap-3 bg-slate-800 px-4 py-2 rounded-lg border border-slate-700 cursor-pointer hover:bg-slate-750 transition-colors">
                                <input
                                    type="checkbox"
                                    checked={updateConflicts}
                                    onChange={(e) => setUpdateConflicts(e.target.checked)}
                                    className="w-5 h-5 text-green-600 rounded bg-slate-700 border-slate-600 focus:ring-offset-slate-800"
                                />
                                <span className="text-slate-300">Oppdater eksisterende poster (overskriv ved konflikt)</span>
                            </label>

                            <button
                                onClick={runImport}
                                disabled={loading}
                                className={`px-8 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex items-center gap-2
                                    ${loading ? 'bg-slate-600 cursor-not-allowed' : 'bg-linear-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 shadow-lg shadow-green-900/50'}`}
                            >
                                {loading ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                        Importerer...
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                        2. Gjennomfør Import
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
