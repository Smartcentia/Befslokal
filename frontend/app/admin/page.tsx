"use client";

import React, { useState } from 'react';
import { fetchAPI } from '@/lib/api';
import Link from 'next/link';
import { glossaryApi } from '@/lib/api/glossaryApi';
import { useFeatureFlags } from '@/contexts/FeatureFlagsContext';

interface PropertyReportItem {
    property_id: string;
    property_name: string;
    old_score: number | null;
    new_score: number;
    old_status: string;
    new_status: string;
    factors: string[];
}

interface BatchReport {
    processed: number;
    total_attempted: number;
    status: string;
    timestamp: string;
    details: PropertyReportItem[];
}

interface GeocodeReportItem {
    property_id: string;
    property_name: string;
    address: string;
    status: "success" | "warning" | "error";
    message: string;
    latitude: number | null;
    longitude: number | null;
}

interface GeocodeBatchReport {
    message: string;
    processed: number;
    total_attempted: number;
    details: GeocodeReportItem[];
}

interface GlossaryScanReport {
    status: string;
    terms_count: number;
    matches_count: number;
    matches: {
        term: string;
        file: string;
        line: number;
        context: string;
    }[];
}

interface PropertyEnrichmentRunResponse {
    message: string;
    mode: "dry-run" | "apply";
    report_file: string;
    summary: {
        baseline_before: Record<string, number>;
        baseline_after: Record<string, number>;
        updated: Record<string, number>;
        skipped_no_match: number;
        skipped_low_score: number;
    };
}

interface PropertyEnrichmentReportItem {
    filename: string;
    size_bytes: number;
    modified_at: string;
}

interface PropertyEnrichmentReportDetail {
    filename: string;
    report: {
        baseline_before?: Record<string, number>;
        baseline_after?: Record<string, number>;
        updated?: Record<string, number>;
        [key: string]: unknown;
    };
}

/** Viser hva som skjer ved klikk (rute eller API-kall) */
function CardActionHint({ children }: { children: React.ReactNode }) {
    return (
        <p className="text-xs text-muted-foreground/80 font-mono mt-2 pt-2 border-t border-border/50 break-all" title="Teknisk: hva som kjøres ved klikk">
            Ved klikk: {children}
        </p>
    );
}

function BatchReportModal({ report, onClose }: { report: BatchReport; onClose: () => void }) {
    if (!report) return null;

    const improved = report.details.filter(d => d.old_score !== null && d.new_score < d.old_score).length;
    const worsened = report.details.filter(d => d.old_score !== null && d.new_score > d.old_score).length;
    const unchanged = report.details.filter(d => d.old_score === null || d.new_score === d.old_score).length;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-card w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-border/50">
                {/* Header */}
                <div className="p-6 border-b border-border/50 bg-muted/30 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-foreground">Risikooppdatering Ferdig</h2>
                        <p className="text-sm text-muted-foreground mt-1">Behandlet {report.processed} av {report.total_attempted} eiendommer</p>
                    </div>
                    <button aria-label="Lukk" onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4 p-6 bg-background">
                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
                        <div className="text-3xl font-bold text-green-500">{improved}</div>
                        <div className="text-sm font-medium text-green-400/80 uppercase tracking-wider mt-1">Forbedret</div>
                    </div>
                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                        <div className="text-3xl font-bold text-red-500">{worsened}</div>
                        <div className="text-sm font-medium text-red-400/80 uppercase tracking-wider mt-1">Forverret</div>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-500/20 text-center">
                        <div className="text-3xl font-bold text-slate-500">{unchanged}</div>
                        <div className="text-sm font-medium text-slate-400/80 uppercase tracking-wider mt-1">Uendret / Nye</div>
                    </div>
                </div>

                {/* Details List */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    <h3 className="text-lg font-semibold mb-4 text-foreground">Detaljer pr. Eiendom</h3>
                    {report.details.map((item, idx) => {
                        const isImproved = item.old_score !== null && item.new_score < item.old_score;
                        const isWorsened = item.old_score !== null && item.new_score > item.old_score;

                        return (
                            <div key={item.property_id || idx} className="p-4 rounded-lg bg-muted/20 border border-border/50 flex flex-col gap-3">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="font-semibold text-foreground">{item.property_name}</div>
                                        <div className="text-xs text-muted-foreground font-mono mt-1">{item.property_id}</div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {item.old_score !== null && (
                                            <div className="flex flex-col items-center">
                                                <span className="text-xs text-muted-foreground uppercase">Før</span>
                                                <span className="font-mono bg-background px-2 py-1 rounded text-sm">{item.old_score} ({item.old_status})</span>
                                            </div>
                                        )}
                                        {item.old_score !== null && (
                                            <svg className={`w-5 h-5 ${isImproved ? 'text-green-500' : isWorsened ? 'text-red-500' : 'text-slate-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                            </svg>
                                        )}
                                        <div className="flex flex-col items-center">
                                            <span className="text-xs text-muted-foreground uppercase">Nå</span>
                                            <span className={`font-mono px-2 py-1 rounded text-sm font-bold ${item.new_status === 'critical' ? 'bg-red-500/20 text-red-500' :
                                                item.new_status === 'high' ? 'bg-orange-500/20 text-orange-500' :
                                                    item.new_status === 'moderate' ? 'bg-yellow-500/20 text-yellow-500' :
                                                        'bg-green-500/20 text-green-500'
                                                }`}>{item.new_score} ({item.new_status})</span>
                                        </div>
                                    </div>
                                </div>
                                {item.factors && item.factors.length > 0 && (
                                    <div className="text-sm bg-background/50 p-3 rounded text-muted-foreground">
                                        <div className="font-semibold text-xs uppercase mb-1">Identifiserte Faktorer:</div>
                                        <ul className="list-disc pl-5 space-y-1">
                                            {item.factors.map((f, i) => <li key={i}>{f}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border/50 bg-muted/30 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg transition-colors">
                        Lukk
                    </button>
                </div>
            </div>
        </div>
    );
}

function BatchGeocodeModal({ report, onClose }: { report: GeocodeBatchReport; onClose: () => void }) {
    if (!report) return null;

    const successes = report.details.filter(d => d.status === 'success').length;
    const warnings = report.details.filter(d => d.status === 'warning').length;
    const errors = report.details.filter(d => d.status === 'error').length;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-card w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-border/50">
                {/* Header */}
                <div className="p-6 border-b border-border/50 bg-muted/30 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-foreground">Geokoding Ferdig</h2>
                        <p className="text-sm text-muted-foreground mt-1">{report.message}</p>
                    </div>
                    <button aria-label="Lukk" onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-3 gap-4 p-6 bg-background">
                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
                        <div className="text-3xl font-bold text-green-500">{successes}</div>
                        <div className="text-sm font-medium text-green-400/80 uppercase tracking-wider mt-1">Suksess</div>
                    </div>
                    <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20 text-center">
                        <div className="text-3xl font-bold text-orange-500">{warnings}</div>
                        <div className="text-sm font-medium text-orange-400/80 uppercase tracking-wider mt-1">Ingen Treff</div>
                    </div>
                    <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center">
                        <div className="text-3xl font-bold text-red-500">{errors}</div>
                        <div className="text-sm font-medium text-red-400/80 uppercase tracking-wider mt-1">Mangler Adresse</div>
                    </div>
                </div>

                {/* Details List */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    <h3 className="text-lg font-semibold mb-4 text-foreground">Detaljer pr. Eiendom</h3>
                    {report.details.map((item, idx) => {
                        return (
                            <div key={item.property_id || idx} className="p-4 rounded-lg bg-muted/20 border border-border/50 flex flex-col gap-3">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="font-semibold text-foreground flex items-center gap-2">
                                            {item.status === 'success' && <span className="w-2 h-2 rounded-full bg-green-500"></span>}
                                            {item.status === 'warning' && <span className="w-2 h-2 rounded-full bg-orange-500"></span>}
                                            {item.status === 'error' && <span className="w-2 h-2 rounded-full bg-red-500"></span>}
                                            {item.property_name}
                                        </div>
                                        <div className="text-sm text-muted-foreground mt-1 whitespace-pre-line">{item.address}</div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="flex flex-col items-end">
                                            <span className="text-xs text-muted-foreground uppercase">{item.status}</span>
                                            <span className="font-mono text-sm opacity-80 mt-1">{item.message}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                    {report.details.length === 0 && (
                        <div className="text-center p-8 text-muted-foreground">
                            Ingen eiendommer manglet koordinater.
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border/50 bg-muted/30 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-lg transition-colors">
                        Lukk
                    </button>
                </div>
            </div>
        </div>
    );
}

function GlossaryScanModal({ report, onClose }: { report: GlossaryScanReport; onClose: () => void }) {
    if (!report) return null;

    // Group matches by file for cleaner display
    const matchesByFile = report.matches.reduce((acc, match) => {
        if (!acc[match.file]) acc[match.file] = [];
        acc[match.file].push(match);
        return acc;
    }, {} as Record<string, typeof report.matches>);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-card w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-border/50">
                {/* Header */}
                <div className="p-6 border-b border-border/50 bg-muted/30 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-foreground">Begreps-Scan Ferdig</h2>
                        <p className="text-sm text-muted-foreground mt-1">Skannet kodebasen etter kjente begreper.</p>
                    </div>
                    <button aria-label="Lukk" onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-4 p-6 bg-background">
                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center">
                        <div className="text-3xl font-bold text-blue-500">{report.terms_count}</div>
                        <div className="text-sm font-medium text-blue-400/80 uppercase tracking-wider mt-1">Begreper Letet Etter</div>
                    </div>
                    <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 text-center">
                        <div className="text-3xl font-bold text-purple-500">{report.matches_count}</div>
                        <div className="text-sm font-medium text-purple-400/80 uppercase tracking-wider mt-1">Totale Funn i Koden</div>
                    </div>
                </div>

                {/* Details List */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {Object.entries(matchesByFile).map(([file, matches]) => (
                        <div key={file} className="overflow-hidden rounded-lg bg-muted/10 border border-border/50">
                            <div className="bg-muted/30 px-4 py-2 border-b border-border/50 font-mono text-sm text-foreground flex items-center gap-2">
                                <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                {file} <span className="ml-auto text-xs opacity-60 bg-black/20 px-2 py-0.5 rounded-full">{matches.length} funn</span>
                            </div>
                            <div className="divide-y divide-border/30">
                                {matches.map((m, i) => (
                                    <div key={i} className="p-4 flex gap-4">
                                        <div className="text-right w-12 pt-0.5 font-mono text-xs text-muted-foreground opacity-70">
                                            {m.line}
                                        </div>
                                        <div className="flex-1">
                                            <div className="inline-block px-2 py-1 bg-primary/20 text-primary-foreground text-xs font-semibold rounded mb-2">
                                                {m.term}
                                            </div>
                                            <div className="font-mono text-sm text-foreground bg-black/40 p-3 rounded overflow-x-auto whitespace-pre">
                                                {m.context}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                    {report.matches.length === 0 && (
                        <div className="text-center p-8 text-muted-foreground">
                            Ingen bruk av begrepene ble funnet i koden.
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border/50 bg-muted/30 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg transition-colors">
                        Lukk
                    </button>
                </div>
            </div>
        </div>
    );
}

function PropertyEnrichmentModal({
    report,
    recentReports,
    selectedReport,
    loadingReport,
    onSelectReport,
    onClose,
}: {
    report: PropertyEnrichmentRunResponse;
    recentReports: PropertyEnrichmentReportItem[];
    selectedReport: PropertyEnrichmentReportDetail | null;
    loadingReport: boolean;
    onSelectReport: (filename: string) => void;
    onClose: () => void;
}) {
    const before = selectedReport?.report?.baseline_before || {};
    const after = selectedReport?.report?.baseline_after || {};
    const deltaNameEqAddr = (after.name_equals_address ?? 0) - (before.name_equals_address ?? 0);
    const deltaMissingImage = (after.missing_image ?? 0) - (before.missing_image ?? 0);
    const deltaMissingDesc = (after.missing_description ?? 0) - (before.missing_description ?? 0);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-card w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-border/50">
                <div className="p-6 border-b border-border/50 bg-muted/30 flex justify-between items-center">
                    <div>
                        <h2 className="text-2xl font-bold text-foreground">Property Enrichment Ferdig</h2>
                        <p className="text-sm text-muted-foreground mt-1">{report.message}</p>
                        <p className="text-xs text-muted-foreground mt-1">Modus: {report.mode} | Rapport: {report.report_file}</p>
                    </div>
                    <button aria-label="Lukk" onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>

                <div className="grid grid-cols-3 gap-4 p-6 bg-background">
                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center">
                        <div className="text-2xl font-bold text-blue-500">{report.summary.updated?.properties_touched ?? 0}</div>
                        <div className="text-xs font-medium text-blue-400/80 uppercase tracking-wider mt-1">Berørte Eiendommer</div>
                    </div>
                    <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-center">
                        <div className="text-2xl font-bold text-green-500">{report.summary.updated?.names ?? 0}</div>
                        <div className="text-xs font-medium text-green-400/80 uppercase tracking-wider mt-1">Navn Oppdatert</div>
                    </div>
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center">
                        <div className="text-2xl font-bold text-amber-500">{report.summary.updated?.images ?? 0}</div>
                        <div className="text-xs font-medium text-amber-400/80 uppercase tracking-wider mt-1">Bilder Oppdatert</div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    <div className="rounded-lg border border-border/50 bg-muted/20 p-4">
                        <div className="font-semibold text-foreground mb-2">Siste rapportfiler (klikk for detaljer)</div>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            {recentReports.slice(0, 5).map((r) => (
                                <li key={r.filename}>
                                    <button
                                        onClick={() => onSelectReport(r.filename)}
                                        className="w-full text-left font-mono px-2 py-1 rounded hover:bg-background/60 transition-colors"
                                    >
                                        {r.filename}
                                    </button>
                                </li>
                            ))}
                            {recentReports.length === 0 && <li>Ingen rapportfiler funnet.</li>}
                        </ul>
                    </div>

                    <div className="rounded-lg border border-border/50 bg-muted/20 p-4">
                        <div className="font-semibold text-foreground mb-2">Valgt rapportdetalj</div>
                        {loadingReport && <p className="text-sm text-muted-foreground">Laster rapport...</p>}
                        {!loadingReport && !selectedReport && (
                            <p className="text-sm text-muted-foreground">Ingen rapport valgt ennå.</p>
                        )}
                        {!loadingReport && selectedReport && (
                            <div className="space-y-2 text-sm">
                                <p className="font-mono text-muted-foreground">{selectedReport.filename}</p>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                                    <div className="p-2 rounded bg-background/60 border border-border/50">
                                        <div className="text-xs text-muted-foreground">name==address delta</div>
                                        <div className="font-semibold">{deltaNameEqAddr}</div>
                                    </div>
                                    <div className="p-2 rounded bg-background/60 border border-border/50">
                                        <div className="text-xs text-muted-foreground">missing_image delta</div>
                                        <div className="font-semibold">{deltaMissingImage}</div>
                                    </div>
                                    <div className="p-2 rounded bg-background/60 border border-border/50">
                                        <div className="text-xs text-muted-foreground">missing_description delta</div>
                                        <div className="font-semibold">{deltaMissingDesc}</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="p-4 border-t border-border/50 bg-muted/30 flex justify-end">
                    <button onClick={onClose} className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg transition-colors">
                        Lukk
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function AdminPage() {
    const { hide_financials, refresh: refreshFlags } = useFeatureFlags();
    const [togglingFinancials, setTogglingFinancials] = useState(false);

    const handleToggleFinancials = async () => {
        setTogglingFinancials(true);
        try {
            await fetchAPI('/feature-flags/hide_financials', { method: 'POST' });
            await refreshFlags();
        } catch (e) {
            console.error('Kunne ikke toggle feature-flagg', e);
        } finally {
            setTogglingFinancials(false);
        }
    };

    const [updating, setUpdating] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<string | null>(null);
    const [geocoding, setGeocoding] = useState(false);
    const [lastGeocode, setLastGeocode] = useState<string | null>(null);

    // modal states
    const [batchReport, setBatchReport] = useState<BatchReport | null>(null);
    const [isReportOpen, setIsReportOpen] = useState(false);

    // geocode modal state
    const [geocodeReport, setGeocodeReport] = useState<GeocodeBatchReport | null>(null);
    const [isGeocodeReportOpen, setIsGeocodeReportOpen] = useState(false);

    // glossary scan modal state
    const [glossaryReport, setGlossaryReport] = useState<GlossaryScanReport | null>(null);
    const [isGlossaryReportOpen, setIsGlossaryReportOpen] = useState(false);
    const [enriching, setEnriching] = useState(false);
    const [lastEnrichment, setLastEnrichment] = useState<string | null>(null);
    const [enrichmentReport, setEnrichmentReport] = useState<PropertyEnrichmentRunResponse | null>(null);
    const [recentEnrichmentReports, setRecentEnrichmentReports] = useState<PropertyEnrichmentReportItem[]>([]);
    const [selectedEnrichmentReport, setSelectedEnrichmentReport] = useState<PropertyEnrichmentReportDetail | null>(null);
    const [loadingEnrichmentReport, setLoadingEnrichmentReport] = useState(false);
    const [isEnrichmentModalOpen, setIsEnrichmentModalOpen] = useState(false);

    const runBatchUpdate = async () => {
        setUpdating(true);
        try {
            const data = await fetchAPI<BatchReport>('/agent/admin/batch-risk-update', { method: 'POST' });
            setLastUpdate(new Date().toLocaleTimeString());
            setBatchReport(data);
            setIsReportOpen(true);
        } catch (e) {
            console.error(e);
            alert("Feilet å kjøre batch oppdatering. Sjekk at backend kjører.");
        }
        setUpdating(false);
    };

    const runGeocodeAll = async () => {
        setGeocoding(true);
        try {
            const data = await fetchAPI<GeocodeBatchReport>('/admin/geocoding/batch', { method: 'POST' });
            setLastGeocode(new Date().toLocaleTimeString());
            setGeocodeReport(data);
            setIsGeocodeReportOpen(true);
        } catch (e) {
            console.error(e);
            alert('Geokoding feilet. Sjekk at backend kjører og at du er logget inn som admin.');
        }
        setGeocoding(false);
    };

    const runGlossaryScan = async () => {
        try {
            const data = await glossaryApi.scanTerms();
            setGlossaryReport(data);
            setIsGlossaryReportOpen(true);
        } catch (e) {
            console.error(e);
            alert("Klarte ikke kjøre glossary scan.");
        }
    };

    const runPropertyEnrichment = async (apply: boolean) => {
        if (apply) {
            const ok = window.confirm('Dette vil skrive endringer i databasen. Fortsette?');
            if (!ok) return;
        }
        setEnriching(true);
        try {
            const data = await fetchAPI<PropertyEnrichmentRunResponse>('/admin/property-enrichment/batch', {
                method: 'POST',
                body: JSON.stringify({
                    apply,
                    confirm_apply: apply,
                    min_score: 0.65,
                    force_description: false,
                    download_images: true,
                    limit: apply ? null : 50,
                }),
            });

            const list = await fetchAPI<{ reports: PropertyEnrichmentReportItem[] }>('/admin/property-enrichment/reports?limit=10');
            setRecentEnrichmentReports(list.reports || []);

            const first = (list.reports || [])[0];
            if (first) {
                setLoadingEnrichmentReport(true);
                try {
                    const detail = await fetchAPI<PropertyEnrichmentReportDetail>(`/admin/property-enrichment/reports/${encodeURIComponent(first.filename)}`);
                    setSelectedEnrichmentReport(detail);
                } finally {
                    setLoadingEnrichmentReport(false);
                }
            } else {
                setSelectedEnrichmentReport(null);
            }

            setEnrichmentReport(data);
            setIsEnrichmentModalOpen(true);
            setLastEnrichment(new Date().toLocaleTimeString());
        } catch (e) {
            console.error(e);
            alert('Property enrichment feilet. Sjekk backend-logg og auth.');
        }
        setEnriching(false);
    };

    const selectEnrichmentReport = async (filename: string) => {
        setLoadingEnrichmentReport(true);
        try {
            const detail = await fetchAPI<PropertyEnrichmentReportDetail>(`/admin/property-enrichment/reports/${encodeURIComponent(filename)}`);
            setSelectedEnrichmentReport(detail);
        } catch (e) {
            console.error(e);
            alert('Klarte ikke hente rapportdetalj.');
        }
        setLoadingEnrichmentReport(false);
    };

    return (
        <div className="min-h-screen bg-background p-8">
            {isReportOpen && batchReport && (
                <BatchReportModal report={batchReport} onClose={() => setIsReportOpen(false)} />
            )}
            {isGeocodeReportOpen && geocodeReport && (
                <BatchGeocodeModal report={geocodeReport} onClose={() => setIsGeocodeReportOpen(false)} />
            )}
            {isGlossaryReportOpen && glossaryReport && (
                <GlossaryScanModal report={glossaryReport} onClose={() => setIsGlossaryReportOpen(false)} />
            )}
            {isEnrichmentModalOpen && enrichmentReport && (
                <PropertyEnrichmentModal
                    report={enrichmentReport}
                    recentReports={recentEnrichmentReports}
                    selectedReport={selectedEnrichmentReport}
                    loadingReport={loadingEnrichmentReport}
                    onSelectReport={selectEnrichmentReport}
                    onClose={() => setIsEnrichmentModalOpen(false)}
                />
            )}

            <div className="max-w-7xl mx-auto">
                <div className="mb-8 text-center md:text-left">
                    <h1 className="text-3xl font-bold bg-linear-to-r from-primary to-accent bg-clip-text text-transparent">Admin Dashboard</h1>
                    <p className="text-muted mt-2">Administrer plattformens kjernefunksjoner og data</p>
                </div>

                {/* ── Kill-switch: skjul økonomidata for testbrukere ── */}
                <div className={`mb-8 flex items-center justify-between rounded-2xl border px-5 py-4 ${
                    hide_financials
                        ? 'bg-amber-50 border-amber-200 dark:bg-amber-950/30 dark:border-amber-800/40'
                        : 'bg-surface border-border'
                }`}>
                    <div className="flex items-center gap-3">
                        <div className={`w-2.5 h-2.5 rounded-full ${hide_financials ? 'bg-amber-400' : 'bg-green-500'}`} />
                        <div>
                            <p className="font-semibold text-sm text-foreground">
                                {hide_financials ? 'Økonomidata er skjult for testbrukere' : 'Økonomidata er synlig for alle'}
                            </p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {hide_financials
                                    ? 'Testbrukere ser ikke husleie, budsjett eller GL-tall. Du og andre administratorer ser fortsatt alt.'
                                    : 'Alle innloggede brukere kan se alle finansielle tall.'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleToggleFinancials}
                        disabled={togglingFinancials}
                        className={`ml-4 shrink-0 px-4 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 ${
                            hide_financials
                                ? 'bg-green-600 hover:bg-green-700 text-white'
                                : 'bg-amber-500 hover:bg-amber-600 text-white'
                        }`}
                    >
                        {togglingFinancials ? '…' : hide_financials ? 'Vis økonomidata igjen' : 'Skjul økonomidata for testbrukere'}
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Data Management Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-blue-500/50 transition-colors">
                        <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Ekstern Risiko
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Kjør batch-oppdatering av ekstern risiko (NVE, Kartverket) for hele porteføljen.</p>
                        <CardActionHint>POST /api/v1/agent/admin/batch-risk-update</CardActionHint>
                        <div className="w-full space-y-4 mt-4">
                            <button
                                onClick={runBatchUpdate}
                                disabled={updating}
                                className={`w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex justify-center items-center gap-3
                                    ${updating ? 'bg-slate-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 shadow-lg hover:shadow-blue-500/20'}`}
                            >
                                {updating ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        <span className="text-sm">Kjører...</span>
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                                        <span className="text-sm">Kjør Oppdatering</span>
                                    </>
                                )}
                            </button>
                            {lastUpdate && (
                                <div className="p-2 bg-green-500/10 border border-green-500/20 rounded text-center">
                                    <p className="text-xs text-green-400 font-medium">✅ Sist: {lastUpdate}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Geocoding Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-amber-500/50 transition-colors">
                        <div className="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Geokoding av adresser
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Hent koordinater (lat/lon) for alle eiendommer som mangler. Bruker Kartverket/Geonorge.</p>
                        <CardActionHint>POST /api/v1/admin/geocoding/batch</CardActionHint>
                        <div className="w-full space-y-4 mt-4">
                            <button
                                onClick={runGeocodeAll}
                                disabled={geocoding}
                                className={`w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex justify-center items-center gap-3
                                    ${geocoding ? 'bg-slate-600 cursor-not-allowed' : 'bg-amber-600 hover:bg-amber-500 shadow-lg hover:shadow-amber-500/20'}`}
                            >
                                {geocoding ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        <span className="text-sm">Geokoder...</span>
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /></svg>
                                        <span className="text-sm">Geokoder alle adresser</span>
                                    </>
                                )}
                            </button>
                            {lastGeocode && (
                                <div className="p-2 bg-green-500/10 border border-green-500/20 rounded text-center">
                                    <p className="text-xs text-green-400 font-medium">✅ Sist: {lastGeocode}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Property Enrichment Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-indigo-500/50 transition-colors">
                        <div className="w-12 h-12 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Property Enrichment
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Auto-berik navn, beskrivelser, bilder og leverandørkontekst fra Bufdir + eksisterende kontraktsdata.</p>
                        <CardActionHint>POST /api/v1/admin/property-enrichment/batch + GET /api/v1/admin/property-enrichment/reports</CardActionHint>
                        <div className="w-full space-y-3 mt-4">
                            <button
                                onClick={() => runPropertyEnrichment(false)}
                                disabled={enriching}
                                className={`w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex justify-center items-center gap-3
                                    ${enriching ? 'bg-slate-600 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg hover:shadow-indigo-500/20'}`}
                            >
                                <span className="text-sm">{enriching ? 'Kjører...' : 'Kjør Dry-Run (pilot 50)'}</span>
                            </button>
                            <button
                                onClick={() => runPropertyEnrichment(true)}
                                disabled={enriching}
                                className={`w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex justify-center items-center gap-3
                                    ${enriching ? 'bg-slate-600 cursor-not-allowed' : 'bg-fuchsia-600 hover:bg-fuchsia-500 shadow-lg hover:shadow-fuchsia-500/20'}`}
                            >
                                <span className="text-sm">Kjør Apply (full)</span>
                            </button>
                            {lastEnrichment && (
                                <div className="p-2 bg-green-500/10 border border-green-500/20 rounded text-center">
                                    <p className="text-xs text-green-400 font-medium">✅ Sist: {lastEnrichment}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Risk Analysis Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-red-500/50 transition-colors">
                        <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Risikobildet
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Se detaljert risikoanalyse for hele eiendomsporteføljen.</p>
                        <CardActionHint>Går til /risk (henter GET /api/v1/risk/prioritized)</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/risk"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-red-600 hover:bg-red-500 shadow-lg hover:shadow-red-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" /></svg>
                                    <span className="text-sm">Se Risikooversikt</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Financial Analysis Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-green-500/50 transition-colors">
                        <div className="w-12 h-12 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Finansiell Analyse
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Søk, sammenlign og analyser kostnader på tvers av eiendommer.</p>
                        <CardActionHint>Går til /admin/financial-analysis (GET .../financial-analysis/search, .../property/&#123;id&#125;)</CardActionHint>
                        <div className="w-full mt-4">
                            <a
                                href="/admin/financial-analysis"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-green-600 hover:bg-green-500 shadow-lg hover:shadow-green-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                                    <span className="text-sm">Åpne Verktøy</span>
                                </div>
                            </a>
                        </div>
                    </div>

                    {/* User Impersonation Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-purple-500/50 transition-colors">
                        <div className="w-12 h-12 bg-purple-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Bruker Impersonering
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Test systemet med forskjellige brukerroller og rettigheter.</p>
                        <CardActionHint>Går til /admin/impersonate (bruker X-Impersonate-Email i API-kall)</CardActionHint>
                        <div className="w-full mt-4">
                            <a
                                href="/admin/impersonate"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-purple-600 hover:bg-purple-500 shadow-lg hover:shadow-purple-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                                    <span className="text-sm">Simulér Bruker</span>
                                </div>
                            </a>
                        </div>
                    </div>

                    {/* HMS Calendar Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-orange-500/50 transition-colors">
                        <div className="w-12 h-12 bg-orange-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            HMS Kalender
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Oversikt over alle planlagte HMS-aktiviteter på tvers av porteføljen.</p>
                        <CardActionHint>Går til /admin/hms-calendar (GET /api/v1/hms/activities/scheduled, POST .../generate)</CardActionHint>
                        <div className="w-full mt-4">
                            <a
                                href="/admin/hms-calendar"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-orange-600 hover:bg-orange-500 shadow-lg hover:shadow-orange-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                                    <span className="text-sm">Åpne Kalender</span>
                                </div>
                            </a>
                        </div>
                    </div>

                    {/* User Management Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-yellow-500/50 transition-colors">
                        <div className="w-12 h-12 bg-yellow-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Brukeradministrasjon
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Administrer brukerroller og tilganger for alle brukere.</p>
                        <CardActionHint>Går til /admin/users</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/users"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-yellow-600 hover:bg-yellow-500 shadow-lg hover:shadow-yellow-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                    <span className="text-sm">Administrér Brukere</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Parter ikke i økonomi rapport */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-red-500/50 transition-colors">
                        <div className="w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Parter ikke i økonomi
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Leietakere/parter med aktive kontrakter som ikke finnes i økonomiregnskapet 2025. Bør deaktiveres.</p>
                        <CardActionHint>Går til /admin/parties-rapport</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/parties-rapport"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-red-600 hover:bg-red-500 shadow-lg hover:shadow-red-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span className="text-sm">Se rapport</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Procurement Analysis Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-teal-500/50 transition-colors">
                        <div className="w-12 h-12 bg-teal-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18M10 3v18M14 3v18" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Innkjøpsanalyse
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Pivotanalyse av lokalkostnader – leie, strøm, renhold og vedlikehold per institusjon og region.</p>
                        <CardActionHint>Går til /admin/procurement</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/procurement"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-teal-600 hover:bg-teal-500 shadow-lg hover:shadow-teal-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" /></svg>
                                    <span className="text-sm">Åpne innkjøpsanalyse</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Economic Data Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-emerald-500/50 transition-colors">
                        <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Økonomidata
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Oversikt over regnskapstabeller og import av Xledger/Visma CSV.</p>
                        <CardActionHint>Går til /admin/economic-data</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/economic-data"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-emerald-600 hover:bg-emerald-500 shadow-lg hover:shadow-emerald-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                    <span className="text-sm">Økonomidata & Import</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Data Import Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-indigo-500/50 transition-colors">
                        <div className="w-12 h-12 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Data Import
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Importer eiendommer, parter og kontrakter via CSV.</p>
                        <CardActionHint>Går til /admin/import</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/import"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-indigo-600 hover:bg-indigo-500 shadow-lg hover:shadow-indigo-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                                    <span className="text-sm">Importer Data</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Document Archive Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-cyan-500/50 transition-colors">
                        <div className="w-12 h-12 bg-cyan-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Dokumentarkiv
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Last opp filer, skann storage og koble dokumenter til kontrakter.</p>
                        <CardActionHint>Går til /admin/documents</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/documents"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-cyan-600 hover:bg-cyan-500 shadow-lg hover:shadow-cyan-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span className="text-sm">Gå til Arkiv</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Admin Docs / Handbook Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-slate-500/50 transition-colors">
                        <div className="w-12 h-12 bg-slate-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Admin Håndbok
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Teknisk dokumentasjon, kommandoer og arkiv.</p>
                        <CardActionHint>Går til /admin/docs</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/docs"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-slate-600 hover:bg-slate-500 shadow-lg hover:shadow-slate-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                                    <span className="text-sm">Åpne Håndbok</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* System Logs Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-pink-500/50 transition-colors">
                        <div className="w-12 h-12 bg-pink-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-pink-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Systemlogger
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Se systemlogger, feilmeldinger og brukeraktivitet.</p>
                        <CardActionHint>Går til /admin/logs</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/logs"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-pink-600 hover:bg-pink-500 shadow-lg hover:shadow-pink-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                                    <span className="text-sm">Se Logger</span>
                                </div>
                            </Link>
                        </div>
                    </div>

                    {/* Glossary Scan Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-blue-500/50 transition-colors">
                        <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Begrepskatalog Scan
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Skann kodebasen for å oppdatere bruken av begreper i katalogen.</p>
                        <CardActionHint>POST /api/v1/glossary/scan</CardActionHint>
                        <div className="w-full mt-4">
                            <GlossaryScanButton onScan={runGlossaryScan} />
                        </div>
                    </div>

                    {/* Contract Costs Card */}
                    <div className="glass-card p-6 flex flex-col items-center text-center hover:border-violet-500/50 transition-colors">
                        <div className="w-12 h-12 bg-violet-500/10 rounded-full flex items-center justify-center mb-4">
                            <svg className="w-6 h-6 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                        </div>
                        <h2 className="text-xl font-semibold mb-2 text-foreground">
                            Kontraktskostnader
                        </h2>
                        <p className="text-muted mb-4 text-sm flex-1">Aggregert oversikt over alle aktive husleiekontrakter og tilleggskostnader.</p>
                        <CardActionHint>Går til /admin/contract-costs (GET /api/v1/admin/contracts/costs)</CardActionHint>
                        <div className="w-full mt-4">
                            <Link
                                href="/admin/contract-costs"
                                className="block w-full py-3 px-6 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] text-center
                                    bg-violet-600 hover:bg-violet-500 shadow-lg hover:shadow-violet-500/20"
                            >
                                <div className="flex justify-center items-center gap-3">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    <span className="text-sm">Se Kostnader</span>
                                </div>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Glossary scan knappen
function GlossaryScanButton({ onScan }: { onScan: () => Promise<void> }) {
    const [scanning, setScanning] = useState(false);

    return (
        <button
            onClick={async () => {
                setScanning(true);
                await onScan();
                setScanning(false);
            }}
            disabled={scanning}
            className="w-full relative group overflow-hidden rounded-lg bg-surface hover:bg-surface-hover border border-border transition-all duration-300"
        >
            <div className="absolute inset-0 bg-linear-to-r from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="px-5 py-3 flex items-center justify-center gap-3">
                {scanning ? (
                    <div className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                ) : (
                    <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                )}
                <span className="font-medium text-foreground relative z-10">
                    {scanning ? 'Skanner...' : 'Kjør Scan'}
                </span>
            </div>
        </button>
    );
}
