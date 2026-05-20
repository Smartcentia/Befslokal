
import React from 'react';

interface ConflictDiff {
    db: any;
    csv: any;
}

interface ConflictRow {
    row_key: string;
    diffs: Record<string, ConflictDiff>;
    row_data: any;
}

interface ImportAnalysis {
    total_rows: number;
    new_records: any[];
    conflicts: ConflictRow[];
    identical: number;
    new_columns: string[];
}

interface ImportAnalysisResultProps {
    analysis: ImportAnalysis;
}

export default function ImportAnalysisResult({ analysis }: ImportAnalysisResultProps) {
    if (!analysis) return null;

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-surface p-4 rounded-lg border border-border">
                    <div className="text-sm text-muted">Totalt antall rader</div>
                    <div className="text-2xl font-bold text-foreground">{analysis.total_rows}</div>
                </div>
                <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-lg border border-green-200 dark:border-green-800/50">
                    <div className="text-sm text-green-700 dark:text-green-400">Nye poster</div>
                    <div className="text-2xl font-bold text-green-800 dark:text-green-300">{analysis.new_records.length}</div>
                </div>
                <div className="bg-yellow-100 dark:bg-yellow-900/30 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800/50">
                    <div className="text-sm text-yellow-700 dark:text-yellow-400">Konflikter / Oppdateringer</div>
                    <div className="text-2xl font-bold text-yellow-800 dark:text-yellow-300">{analysis.conflicts.length}</div>
                </div>
                <div className="bg-surface p-4 rounded-lg border border-border">
                    <div className="text-sm text-muted">Identiske (ignoreres)</div>
                    <div className="text-2xl font-bold text-muted">{analysis.identical}</div>
                </div>
            </div>

            {analysis.new_columns.length > 0 && (
                <div className="bg-blue-100 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50 p-4 rounded-lg">
                    <h3 className="font-semibold text-blue-700 dark:text-blue-300 mb-2 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        Nye kolonner oppdaget
                    </h3>
                    <p className="text-sm text-blue-600 dark:text-blue-200 mb-2">Disse feltene finnes ikke i standardskjemaet og vil bli lagret som utvidet data:</p>
                    <div className="flex flex-wrap gap-2">
                        {analysis.new_columns.map(col => (
                            <span key={col} className="px-2 py-1 bg-blue-200 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 rounded text-xs font-mono border border-blue-300 dark:border-blue-800">
                                {col}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {analysis.conflicts.length > 0 && (
                <div className="bg-surface rounded-lg border border-border overflow-hidden">
                    <div className="p-4 bg-muted/10 border-b border-border">
                        <h3 className="font-semibold text-foreground">Konflikter ({analysis.conflicts.length})</h3>
                        <p className="text-sm text-muted">Disse postene finnes fra før, men har endringer i CSV-filen.</p>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left text-muted">
                            <thead className="text-xs text-muted uppercase bg-muted/10">
                                <tr>
                                    <th className="px-4 py-3">Nøkkel</th>
                                    <th className="px-4 py-3">Felt</th>
                                    <th className="px-4 py-3 text-red-500">Nåværende (DB)</th>
                                    <th className="px-4 py-3 text-green-500">Ny verdi (CSV)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {analysis.conflicts.map((conflict, idx) => (
                                    <React.Fragment key={idx}>
                                        {Object.entries(conflict.diffs).map(([field, diff], diffIdx) => (
                                            <tr key={`${idx}-${field}`} className="border-b border-border bg-background">
                                                {diffIdx === 0 && (
                                                    <td className="px-4 py-3 font-mono text-foreground" rowSpan={Object.keys(conflict.diffs).length}>
                                                        {conflict.row_key}
                                                    </td>
                                                )}
                                                <td className="px-4 py-3 font-medium">{field}</td>
                                                <td className="px-4 py-3 text-red-400 line-through decoration-red-500/50">
                                                    {String(diff.db)}
                                                </td>
                                                <td className="px-4 py-3 text-green-600 dark:text-green-300">
                                                    {String(diff.csv)}
                                                </td>
                                            </tr>
                                        ))}
                                    </React.Fragment>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {analysis.new_records.length > 0 && (
                <div className="bg-surface rounded-lg border border-border overflow-hidden">
                    <div className="p-4 bg-muted/10 border-b border-border" onClick={(e) => (e.currentTarget.nextElementSibling as HTMLElement).classList.toggle('hidden')}>
                        <div className="flex justify-between items-center cursor-pointer">
                            <div>
                                <h3 className="font-semibold text-foreground">Nye poster ({analysis.new_records.length})</h3>
                                <p className="text-sm text-muted">Disse postene vil bli opprettet.</p>
                            </div>
                            <svg className="w-5 h-5 text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                        </div>
                    </div>
                    <div className="hidden overflow-x-auto max-h-60">
                        <table className="w-full text-sm text-left text-muted">
                            <thead className="text-xs text-muted uppercase bg-muted/10 sticky top-0">
                                <tr>
                                    {Object.keys(analysis.new_records[0] || {}).slice(0, 5).map(header => (
                                        <th key={header} className="px-4 py-3">{header}</th>
                                    ))}
                                    {Object.keys(analysis.new_records[0] || {}).length > 5 && <th className="px-4 py-3">...</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {analysis.new_records.slice(0, 20).map((record, idx) => (
                                    <tr key={idx} className="border-b border-border hover:bg-muted/5">
                                        {Object.values(record).slice(0, 5).map((val: any, vIdx) => (
                                            <td key={vIdx} className="px-4 py-2 truncate max-w-[150px]">{String(val)}</td>
                                        ))}
                                        {Object.values(record).length > 5 && <td className="px-4 py-2 text-muted">...</td>}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {analysis.new_records.length > 20 && (
                            <div className="p-2 text-center text-xs text-muted bg-background">
                                Visere de første 20 av {analysis.new_records.length} poster
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
