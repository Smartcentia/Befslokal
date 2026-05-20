"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { getKonkursFlaggedParties, runKonkursCheckAll, getKonkursRunStatus, type KonkursStatusEntry } from "@/lib/api";

export default function KonkursMonitorPage() {
    const [flagged, setFlagged] = useState<KonkursStatusEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [runStatus, setRunStatus] = useState<Record<string, unknown>>({});
    const [running, setRunning] = useState(false);
    const [runMsg, setRunMsg] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [parties, status] = await Promise.all([
                getKonkursFlaggedParties(),
                getKonkursRunStatus(),
            ]);
            setFlagged(parties);
            setRunStatus(status);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(msg || "Kunne ikke hente data.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const onRunAll = async () => {
        setRunning(true);
        setRunMsg(null);
        try {
            const res = await runKonkursCheckAll();
            setRunMsg(res.message || "Konkurssjekk startet i bakgrunnen.");
            // Poll for completion after a few seconds
            setTimeout(() => loadData(), 5000);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setRunMsg("Feil: " + (msg || "Ukjent feil"));
        } finally {
            setRunning(false);
        }
    };

    const critical = flagged.filter((p) => p.risk_level === "CRITICAL");
    const warnings = flagged.filter((p) => p.risk_level === "WARNING");

    const lastRun = runStatus as {
        status?: string;
        done?: number;
        flagged?: number;
        errors?: number;
        total?: number;
    };

    return (
        <div className="min-h-screen p-8 bg-background text-foreground">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-start justify-between flex-wrap gap-4">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            🚨 Konkursovervåkning
                        </h1>
                        <p className="text-muted-foreground text-sm mt-1">
                            Nattlig BRREG-sjekk av konkurs, avvikling og risikoflagg for alle parter.
                            Kjøres automatisk kl. 03:00.
                        </p>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                        <button
                            onClick={onRunAll}
                            disabled={running}
                            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 text-sm font-medium"
                        >
                            {running ? "Starter…" : "Kjør sjekk nå (alle parter)"}
                        </button>
                        <button
                            onClick={loadData}
                            disabled={loading}
                            className="px-4 py-2 rounded-lg bg-muted text-muted-foreground hover:bg-muted/70 disabled:opacity-50 text-sm font-medium"
                        >
                            Oppdater
                        </button>
                    </div>
                </div>

                {runMsg && (
                    <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-700 dark:text-blue-400 text-sm">
                        {runMsg}
                    </div>
                )}
                {error && (
                    <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {/* Last run status */}
                {lastRun.status && lastRun.status !== "not_run_yet" && (
                    <div className="mb-6 p-4 rounded-xl border border-border bg-muted/10">
                        <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                            Siste kjøring
                        </div>
                        <div className="flex flex-wrap gap-6 text-sm">
                            <span><span className="text-muted-foreground">Status:</span> {lastRun.status}</span>
                            {lastRun.total != null && (
                                <span><span className="text-muted-foreground">Totalt:</span> {lastRun.total}</span>
                            )}
                            {lastRun.done != null && (
                                <span><span className="text-muted-foreground">Sjekket:</span> {lastRun.done}</span>
                            )}
                            {lastRun.flagged != null && (
                                <span className={lastRun.flagged > 0 ? "text-orange-600 dark:text-orange-400 font-bold" : ""}>
                                    <span className="text-muted-foreground font-normal">Flagget:</span> {lastRun.flagged}
                                </span>
                            )}
                            {lastRun.errors != null && lastRun.errors > 0 && (
                                <span className="text-red-600 dark:text-red-400">
                                    <span className="text-muted-foreground font-normal">Feil:</span> {lastRun.errors}
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="text-muted-foreground py-12 text-center">Laster…</div>
                ) : flagged.length === 0 ? (
                    <div className="py-16 text-center">
                        <div className="text-4xl mb-3">✅</div>
                        <div className="text-lg font-semibold text-foreground mb-1">Ingen risikoflagg</div>
                        <div className="text-muted-foreground text-sm">
                            Alle sjektede parter ser OK ut per siste kjøring.
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Critical section */}
                        {critical.length > 0 && (
                            <section>
                                <h2 className="text-base font-bold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                                    🚨 KRITISK ({critical.length})
                                </h2>
                                <PartyRiskTable rows={critical} />
                            </section>
                        )}

                        {/* Warning section */}
                        {warnings.length > 0 && (
                            <section>
                                <h2 className="text-base font-bold text-orange-600 dark:text-orange-400 mb-3 flex items-center gap-2">
                                    ⚠️ ADVARSEL ({warnings.length})
                                </h2>
                                <PartyRiskTable rows={warnings} />
                            </section>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function PartyRiskTable({ rows }: { rows: KonkursStatusEntry[] }) {
    return (
        <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                    <tr>
                        <th className="text-left px-4 py-3 font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">Part</th>
                        <th className="text-left px-4 py-3 font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">Orgnr</th>
                        <th className="text-left px-4 py-3 font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">Risikoflagg</th>
                        <th className="text-right px-4 py-3 font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">Aktive kontrakter</th>
                        <th className="text-right px-4 py-3 font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">Sjekket</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border">
                    {rows.map((row) => (
                        <tr key={row.party_id} className="hover:bg-muted/10 transition-colors">
                            <td className="px-4 py-3">
                                <Link
                                    href={`/parties/${row.party_id}`}
                                    className="font-medium text-primary hover:underline"
                                >
                                    {row.name}
                                </Link>
                            </td>
                            <td className="px-4 py-3 font-mono text-muted-foreground text-xs">
                                {row.orgnr}
                            </td>
                            <td className="px-4 py-3">
                                <div className="flex flex-wrap gap-1">
                                    {row.risk_flags.map((flag, i) => (
                                        <span
                                            key={i}
                                            className={`px-2 py-0.5 rounded text-xs font-medium ${row.risk_level === "CRITICAL"
                                                    ? "bg-red-500/15 text-red-700 dark:text-red-400 border border-red-500/30"
                                                    : "bg-orange-500/15 text-orange-700 dark:text-orange-400 border border-orange-500/30"
                                                }`}
                                        >
                                            {flag}
                                        </span>
                                    ))}
                                </div>
                            </td>
                            <td className="px-4 py-3 text-right">
                                {row.active_contracts > 0 ? (
                                    <span className="font-bold text-orange-600 dark:text-orange-400">
                                        {row.active_contracts}
                                    </span>
                                ) : (
                                    <span className="text-muted-foreground">0</span>
                                )}
                            </td>
                            <td className="px-4 py-3 text-right text-muted-foreground text-xs">
                                {row.checked_at
                                    ? new Date(row.checked_at).toLocaleDateString("nb-NO")
                                    : "—"}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
