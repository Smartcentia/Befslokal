"use client";

import React, { useEffect, useState } from 'react';
import { fetchAPI, healthCheck } from '@/lib/api';

interface DataHealthReport {
    status: string;
    database: {
        connected: boolean;
        host: string;
    };
    volume: {
        users: number;
        properties: number;
        contracts: number;
        risks: number;
        deviations: number;
    };
    integrity_issues: string[];
}

export default function DataVerificationWidget() {
    const [report, setReport] = useState<DataHealthReport | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const checkDataHealth = async () => {
        setLoading(true);
        setError(null);
        try {
            // We use the full health endpoint we created earlier
            const data = await fetchAPI('/admin/health/full');
            setReport(data);
        } catch (err) {
            setError("Kunne ikke koble til databasen verification service.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-surface p-6 rounded-lg shadow-md border border-border mt-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-foreground">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Dataintegritet & Verifikasjon
            </h2>
            <p className="text-muted-foreground mb-6">
                Her kan du etterprøve at systemet har tilgang til og kontrollerer alle datadomener.
            </p>

            {!report && !loading && (
                <button
                    onClick={checkDataHealth}
                    className="bg-primary text-primary-foreground px-4 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors"
                >
                    Kjør Full Dataskann
                </button>
            )}

            {loading && (
                <div className="flex items-center gap-2 text-muted">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Analyserer databasetabeller...
                </div>
            )}

            {error && (
                <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-100">
                    {error}
                </div>
            )}

            {report && (
                <div className="space-y-6">
                    {/* Database Status */}
                    <div className="flex items-center justify-between p-3 bg-muted/10 rounded-lg border border-border">
                        <span className="font-medium text-foreground">Databasekobling</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${report.database.connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                            {report.database.connected ? 'OK' : 'OFFLINE'}
                        </span>
                    </div>

                    {/* Volume Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <MetricCard label="Eiendommer" value={report.volume.properties || 0} />
                        <MetricCard label="Kontrakter" value={report.volume.contracts || 0} />
                        <MetricCard label="Risikovurd." value={report.volume.risks || 0} />
                        <MetricCard label="Avvik" value={report.volume.deviations || 0} />
                        <MetricCard label="Brukere" value={report.volume.users || 0} />
                    </div>

                    {/* Integrity Issues */}
                    {report.integrity_issues && report.integrity_issues.length > 0 ? (
                        <div className="p-4 bg-amber-50 rounded-lg border border-amber-100">
                            <h3 className="font-bold text-amber-800 mb-2">Integritetsvarsler</h3>
                            <ul className="list-disc list-inside text-sm text-amber-700">
                                {report.integrity_issues.map((issue, idx) => (
                                    <li key={idx}>{issue}</li>
                                ))}
                            </ul>
                        </div>
                    ) : (
                        <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                            Ingen integritetsfeil funnet. Alle relasjoner er intakte.
                        </div>
                    )}

                    <button
                        onClick={checkDataHealth}
                        className="text-sm text-muted hover:text-primary underline"
                    >
                        Oppdater skann
                    </button>
                </div>
            )}
        </div>
    );
}

function MetricCard({ label, value }: { label: string, value: number }) {
    return (
        <div className="bg-surface p-3 rounded border border-border text-center shadow-sm">
            <div className="text-2xl font-bold text-foreground">{value}</div>
            <div className="text-xs text-muted uppercase tracking-wide">{label}</div>
        </div>
    );
}
