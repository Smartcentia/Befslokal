"use client";

import { useState, useEffect } from "react";

interface PartyRapport {
    party_id: string;
    name: string;
    orgnr: string | null;
    contact_email: string | null;
    antall_kontrakter: number;
    total_husleie: number;
    eiendommer: string;
    kontrakt_statuser: string;
    siste_sluttdato: string | null;
    er_i_okonomi_2025: boolean;
    konkurs_flagg: boolean;
    brreg_navn: string | null;
}

interface RapportResponse {
    antall: number;
    parter: PartyRapport[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const AUTH_TOKEN = "d0f5592d6bdcfb03601c6bbea7686dfa";

function getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${AUTH_TOKEN}`,
    };
    const email =
        typeof window !== "undefined"
            ? localStorage.getItem("impersonate_email")
            : null;
    if (email) headers["X-User-Email"] = email;
    return headers;
}

function formatNOK(val: number): string {
    if (!val) return "–";
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)} MNOK`;
    return `${Math.round(val).toLocaleString("nb-NO")} kr`;
}

export default function PartiesRapportPage() {
    const [data, setData] = useState<RapportResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selected, setSelected] = useState<Set<string>>(new Set());
    const [deaktiverLoading, setDeaktiverLoading] = useState(false);
    const [deaktiverResult, setDeaktiverResult] = useState<string | null>(null);

    useEffect(() => {
        fetchRapport();
    }, []);

    async function fetchRapport() {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/parties/ikke-i-okonomi/rapport`,
                { headers: getHeaders() }
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setData(json);
        } catch (e: any) {
            setError(e.message ?? "Ukjent feil");
        } finally {
            setLoading(false);
        }
    }

    function toggleAll() {
        if (!data) return;
        if (selected.size === data.parter.length) {
            setSelected(new Set());
        } else {
            setSelected(new Set(data.parter.map((p) => p.party_id)));
        }
    }

    function toggleOne(id: string) {
        setSelected((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    }

    async function handleDeaktiver() {
        if (selected.size === 0) return;
        const confirmed = window.confirm(
            `Vil du sette ${selected.size} parts aktive kontrakter til «avsluttet»?\n\nDette kan ikke angres direkte.`
        );
        if (!confirmed) return;

        setDeaktiverLoading(true);
        setDeaktiverResult(null);
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/parties/ikke-i-okonomi/deaktiver-bulk`,
                {
                    method: "POST",
                    headers: getHeaders(),
                    body: JSON.stringify({ party_ids: Array.from(selected) }),
                }
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setDeaktiverResult(
                `✅ ${json.deaktivert} kontrakt${json.deaktivert !== 1 ? "er" : ""} satt til avsluttet for ${json.parter} part${json.parter !== 1 ? "er" : ""}.`
            );
            setSelected(new Set());
            // Refresh rapport
            await fetchRapport();
        } catch (e: any) {
            setDeaktiverResult(`❌ Feil: ${e.message}`);
        } finally {
            setDeaktiverLoading(false);
        }
    }

    const totalHusleie = data?.parter.reduce((s, p) => s + p.total_husleie, 0) ?? 0;
    const konkursCount = data?.parter.filter((p) => p.konkurs_flagg).length ?? 0;

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto space-y-6">

                {/* Header */}
                <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">
                                Parter ikke i økonomi 2025
                            </h1>
                            <p className="text-muted text-sm mt-1">
                                Aktive leietakere/parter som <strong>ikke</strong> finnes i
                                økonomiavdelingens regnskap (kontant_2025). Bør vurderes for
                                deaktivering.
                            </p>
                        </div>
                        <button
                            onClick={fetchRapport}
                            className="rounded-md border border-border bg-surface px-4 py-2 text-sm text-foreground hover:bg-surface/70 transition-colors"
                        >
                            Oppdater rapport
                        </button>
                    </div>

                    {/* Summary cards */}
                    <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-500/25 dark:bg-red-500/10 p-4">
                            <div className="text-2xl font-bold text-red-800 dark:text-red-200">
                                {loading ? "…" : data?.antall ?? 0}
                            </div>
                            <div className="text-xs text-red-700 dark:text-red-300 mt-0.5">
                                Parter ikke i økonomi
                            </div>
                        </div>
                        <div className="rounded-lg border border-orange-200 bg-orange-50 dark:border-orange-500/25 dark:bg-orange-500/10 p-4">
                            <div className="text-2xl font-bold text-orange-800 dark:text-orange-200">
                                {loading ? "…" : formatNOK(totalHusleie)}
                            </div>
                            <div className="text-xs text-orange-700 dark:text-orange-300 mt-0.5">
                                Avtalefestet husleie (ikke betalt?)
                            </div>
                        </div>
                        <div className="rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-500/25 dark:bg-yellow-500/10 p-4">
                            <div className="text-2xl font-bold text-yellow-800 dark:text-yellow-200">
                                {loading ? "…" : konkursCount}
                            </div>
                            <div className="text-xs text-yellow-700 dark:text-yellow-300 mt-0.5">
                                Med konkurs-flagg (BRREG)
                            </div>
                        </div>
                        <div className="rounded-lg border border-blue-200 bg-blue-50 dark:border-blue-500/25 dark:bg-blue-500/10 p-4">
                            <div className="text-2xl font-bold text-blue-800 dark:text-blue-200">
                                {loading ? "…" : selected.size}
                            </div>
                            <div className="text-xs text-blue-700 dark:text-blue-300 mt-0.5">
                                Valgt for deaktivering
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action bar */}
                {selected.size > 0 && (
                    <div className="rounded-lg border border-warning bg-warning/10 p-4 flex items-center justify-between gap-4 flex-wrap">
                        <span className="text-sm font-medium text-foreground">
                            {selected.size} part{selected.size !== 1 ? "er" : ""} valgt
                        </span>
                        <button
                            onClick={handleDeaktiver}
                            disabled={deaktiverLoading}
                            className="rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 transition-colors"
                        >
                            {deaktiverLoading
                                ? "Deaktiverer…"
                                : `Avslutt kontrakter (${selected.size})`}
                        </button>
                    </div>
                )}

                {deaktiverResult && (
                    <div className={`rounded-lg border p-4 text-sm ${deaktiverResult.startsWith("✅") ? "border-success bg-success/10 text-success" : "border-destructive bg-destructive/10 text-destructive"}`}>
                        {deaktiverResult}
                    </div>
                )}

                {/* Table */}
                <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
                    {loading ? (
                        <div className="flex items-center justify-center p-16 text-muted">
                            Laster rapport…
                        </div>
                    ) : error ? (
                        <div className="flex items-center justify-center p-16 text-destructive">
                            Feil: {error}
                        </div>
                    ) : !data || data.antall === 0 ? (
                        <div className="flex flex-col items-center justify-center p-16 gap-3 text-center">
                            <svg className="h-10 w-10 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p className="text-foreground font-medium">Alle aktive parter er i økonomiregnskapet</p>
                            <p className="text-muted text-sm">Ingen parter mangler i kontant_2025.</p>
                        </div>
                    ) : (
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-surface/80">
                                <tr>
                                    <th className="px-4 py-3 text-left">
                                        <input
                                            type="checkbox"
                                            checked={selected.size === data.parter.length}
                                            onChange={toggleAll}
                                            className="rounded border-border"
                                        />
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Part / Leietaker
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Orgnr
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Eiendommer
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">
                                        Kontrakter
                                    </th>
                                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">
                                        Husleie (avt.)
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Sluttdato
                                    </th>
                                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">
                                        Status
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-card">
                                {data.parter.map((party) => (
                                    <tr
                                        key={party.party_id}
                                        className={selected.has(party.party_id) ? "bg-warning/10" : "hover:bg-surface/40"}
                                    >
                                        <td className="px-4 py-3">
                                            <input
                                                type="checkbox"
                                                checked={selected.has(party.party_id)}
                                                onChange={() => toggleOne(party.party_id)}
                                                className="rounded border-border"
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="font-medium text-sm text-foreground flex items-center gap-2">
                                                {party.name}
                                                {party.konkurs_flagg && (
                                                    <span className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-500/15 border border-red-200 dark:border-red-500/30 px-1.5 py-0.5 text-[10px] font-semibold text-red-700 dark:text-red-300">
                                                        KONKURS
                                                    </span>
                                                )}
                                            </div>
                                            {party.brreg_navn && party.brreg_navn !== party.name && (
                                                <div className="text-xs text-muted mt-0.5">
                                                    BRREG: {party.brreg_navn}
                                                </div>
                                            )}
                                            {party.contact_email && (
                                                <div className="text-xs text-muted">{party.contact_email}</div>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-muted font-mono">
                                            {party.orgnr ? (
                                                <a
                                                    href={`https://www.brreg.no/bedrift/?orgnr=${party.orgnr}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-primary hover:underline"
                                                >
                                                    {party.orgnr}
                                                </a>
                                            ) : (
                                                <span className="text-muted italic">–</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-muted max-w-[180px] truncate" title={party.eiendommer}>
                                            {party.eiendommer || "–"}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-right text-foreground">
                                            {party.antall_kontrakter}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-right font-medium text-foreground">
                                            {formatNOK(party.total_husleie)}
                                        </td>
                                        <td className="px-4 py-3 text-sm text-muted">
                                            {party.siste_sluttdato
                                                ? new Date(party.siste_sluttdato).toLocaleDateString("nb-NO")
                                                : "–"}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="inline-flex rounded-full bg-red-100 dark:bg-red-500/15 border border-red-200 dark:border-red-500/30 px-2 py-0.5 text-xs font-semibold text-red-700 dark:text-red-300">
                                                Ikke i økonomi
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                {/* Info box */}
                <div className="rounded border-l-4 border-primary bg-primary/5 p-4">
                    <div className="flex gap-3">
                        <svg className="h-5 w-5 shrink-0 text-primary mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <div className="text-sm text-muted">
                            <strong className="text-foreground">Metodikk:</strong> En part er «ikke i økonomi» dersom ingen av dens tilknyttede eiendommer (via aktive kontrakter) finnes i{" "}
                            <code className="bg-surface px-1 rounded text-xs">finance_budget WHERE data_source = &apos;kontant_2025&apos;</code>.
                            Deaktivering setter kontrakt-status til <em>terminated</em> — partens data beholdes for historikk.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
