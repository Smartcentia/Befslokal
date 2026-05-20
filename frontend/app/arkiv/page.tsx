"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

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

function formatDate(d: string | null): string {
    if (!d) return "–";
    try {
        return new Date(d).toLocaleDateString("nb-NO");
    } catch {
        return d;
    }
}

interface InaktivPart {
    party_id: string;
    name: string;
    orgnr: string | null;
    contact_email: string | null;
    created_at: string | null;
    antall_kontrakter: number;
    siste_sluttdato: string | null;
    statuser: string;
    eiendommer: string;
    total_husleie: number;
    brreg_navn: string | null;
    konkurs_flagg: boolean;
}

interface InaktivKontrakt {
    contract_id: string;
    contract_name: string | null;
    status: string;
    category: string | null;
    start_date: string | null;
    end_date: string | null;
    party_name: string | null;
    party_id: string | null;
    property_name: string | null;
    property_id: string | null;
    amount: Record<string, unknown> | null;
}

type Tab = "parter" | "kontrakter";

export default function ArkivPage() {
    const [tab, setTab] = useState<Tab>("parter");

    // --- Parter state ---
    const [parter, setParter] = useState<InaktivPart[]>([]);
    const [parterLoading, setParterLoading] = useState(false);
    const [parterError, setParterError] = useState<string | null>(null);
    const [selectedParter, setSelectedParter] = useState<Set<string>>(new Set());
    const [reaktiverLoading, setReaktiverLoading] = useState(false);
    const [reaktiverMsg, setReaktiverMsg] = useState<string | null>(null);

    // --- Kontrakter state ---
    const [kontrakter, setKontrakter] = useState<InaktivKontrakt[]>([]);
    const [kontraktLoading, setKontraktLoading] = useState(false);
    const [kontraktError, setKontraktError] = useState<string | null>(null);
    const [kontraktSok, setKontraktSok] = useState("");

    useEffect(() => {
        if (tab === "parter" && parter.length === 0) fetchParter();
        if (tab === "kontrakter" && kontrakter.length === 0) fetchKontrakter();
    }, [tab]);

    async function fetchParter() {
        setParterLoading(true);
        setParterError(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/parties/arkiv/inaktive`, {
                headers: getHeaders(),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setParter(json.parter ?? []);
        } catch (e: any) {
            setParterError(e.message);
        } finally {
            setParterLoading(false);
        }
    }

    async function fetchKontrakter() {
        setKontraktLoading(true);
        setKontraktError(null);
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/contracts?status=terminated&limit=500`,
                { headers: getHeaders() }
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            // Enrich with party/property names from nested fields
            const list: InaktivKontrakt[] = (Array.isArray(json) ? json : []).map((c: any) => ({
                contract_id: c.contract_id,
                contract_name: c.contract_name ?? c.name ?? null,
                status: c.status,
                category: c.category ?? null,
                start_date: c.start_date ?? c.periods?.[0]?.start_date ?? null,
                end_date: c.end_date ?? c.periods?.[0]?.end_date ?? null,
                party_name: c.party?.name ?? c.party_name ?? null,
                party_id: c.party_id ?? null,
                property_name: c.unit?.property?.name ?? c.property_name ?? null,
                property_id: c.unit?.property_id ?? c.property_id ?? null,
                amount: c.amount ?? null,
            }));
            setKontrakter(list);
        } catch (e: any) {
            setKontraktError(e.message);
        } finally {
            setKontraktLoading(false);
        }
    }

    function togglePart(id: string) {
        setSelectedParter((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    }
    function toggleAllParter() {
        setSelectedParter(
            selectedParter.size === parter.length
                ? new Set()
                : new Set(parter.map((p) => p.party_id))
        );
    }

    async function handleReaktiver() {
        if (selectedParter.size === 0) return;
        const ok = window.confirm(
            `Reaktiver alle kontrakter for ${selectedParter.size} part(er)?`
        );
        if (!ok) return;
        setReaktiverLoading(true);
        setReaktiverMsg(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/parties/arkiv/reaktiver`, {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ party_ids: Array.from(selectedParter) }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setReaktiverMsg(
                `✅ ${json.reaktivert} kontrakt(er) reaktivert for ${json.parter} part(er).`
            );
            setSelectedParter(new Set());
            setParter([]);
            await fetchParter();
        } catch (e: any) {
            setReaktiverMsg(`❌ Feil: ${e.message}`);
        } finally {
            setReaktiverLoading(false);
        }
    }

    const filteredKontrakter = kontrakter.filter((k) => {
        if (!kontraktSok) return true;
        const q = kontraktSok.toLowerCase();
        return (
            k.contract_name?.toLowerCase().includes(q) ||
            k.party_name?.toLowerCase().includes(q) ||
            k.property_name?.toLowerCase().includes(q) ||
            k.category?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto space-y-6">

                {/* Header */}
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Arkiv</h1>
                    <p className="text-muted text-sm mt-1">
                        Inaktive kontrakter og parter uten aktive avtaler. Data beholdes for historikk og revisjon.
                    </p>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 border-b border-border">
                    {(["parter", "kontrakter"] as Tab[]).map((t) => (
                        <button
                            key={t}
                            onClick={() => setTab(t)}
                            className={`px-5 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
                                tab === t
                                    ? "border-primary text-primary"
                                    : "border-transparent text-muted hover:text-foreground"
                            }`}
                        >
                            {t === "parter" ? "Parter / Leietakere" : "Kontrakter"}
                        </button>
                    ))}
                </div>

                {/* ── PARTER TAB ── */}
                {tab === "parter" && (
                    <div className="space-y-4">
                        {selectedParter.size > 0 && (
                            <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4 flex-wrap gap-3">
                                <span className="text-sm text-foreground font-medium">
                                    {selectedParter.size} part(er) valgt
                                </span>
                                <button
                                    onClick={handleReaktiver}
                                    disabled={reaktiverLoading}
                                    className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                                >
                                    {reaktiverLoading ? "Reaktiverer…" : "Reaktiver kontrakter"}
                                </button>
                            </div>
                        )}

                        {reaktiverMsg && (
                            <div className={`rounded-lg border p-3 text-sm ${reaktiverMsg.startsWith("✅") ? "border-success/40 bg-success/10 text-success" : "border-destructive/40 bg-destructive/10 text-destructive"}`}>
                                {reaktiverMsg}
                            </div>
                        )}

                        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
                            {parterLoading ? (
                                <div className="p-12 text-center text-muted">Laster arkiv…</div>
                            ) : parterError ? (
                                <div className="p-12 text-center text-destructive">Feil: {parterError}</div>
                            ) : parter.length === 0 ? (
                                <div className="p-12 text-center">
                                    <svg className="h-10 w-10 text-muted mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8" />
                                    </svg>
                                    <p className="text-muted text-sm">Ingen inaktive parter i arkivet.</p>
                                </div>
                            ) : (
                                <table className="min-w-full divide-y divide-border">
                                    <thead className="bg-surface/80">
                                        <tr>
                                            <th className="px-4 py-3 text-left">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedParter.size === parter.length}
                                                    onChange={toggleAllParter}
                                                    className="rounded border-border"
                                                />
                                            </th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Part</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Orgnr</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Eiendommer</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">Kontrakter</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">Husleie</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Siste slutt</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border bg-card">
                                        {parter.map((p) => (
                                            <tr
                                                key={p.party_id}
                                                className={selectedParter.has(p.party_id) ? "bg-primary/5" : "hover:bg-surface/40"}
                                            >
                                                <td className="px-4 py-3">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedParter.has(p.party_id)}
                                                        onChange={() => togglePart(p.party_id)}
                                                        className="rounded border-border"
                                                    />
                                                </td>
                                                <td className="px-4 py-3">
                                                    <Link href={`/parties/${p.party_id}`} className="font-medium text-sm text-foreground hover:text-primary flex items-center gap-1.5">
                                                        {p.name}
                                                        {p.konkurs_flagg && (
                                                            <span className="inline-flex rounded-full bg-red-100 dark:bg-red-500/15 border border-red-200 dark:border-red-500/30 px-1.5 text-[10px] font-semibold text-red-700 dark:text-red-300">KONKURS</span>
                                                        )}
                                                    </Link>
                                                    {p.brreg_navn && p.brreg_navn !== p.name && (
                                                        <div className="text-xs text-muted mt-0.5">BRREG: {p.brreg_navn}</div>
                                                    )}
                                                    {p.contact_email && (
                                                        <div className="text-xs text-muted">{p.contact_email}</div>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-sm font-mono text-muted">
                                                    {p.orgnr ? (
                                                        <a href={`https://www.brreg.no/bedrift/?orgnr=${p.orgnr}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{p.orgnr}</a>
                                                    ) : "–"}
                                                </td>
                                                <td className="px-4 py-3 text-sm text-muted max-w-[160px] truncate" title={p.eiendommer}>
                                                    {p.eiendommer || "–"}
                                                </td>
                                                <td className="px-4 py-3 text-sm text-right text-foreground">{p.antall_kontrakter}</td>
                                                <td className="px-4 py-3 text-sm text-right font-medium text-foreground">{formatNOK(p.total_husleie)}</td>
                                                <td className="px-4 py-3 text-sm text-muted">{formatDate(p.siste_sluttdato)}</td>
                                                <td className="px-4 py-3">
                                                    <span className="inline-flex rounded-full bg-surface border border-border px-2 py-0.5 text-xs text-muted">
                                                        {p.statuser || "Ingen kontrakter"}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        <p className="text-xs text-muted">
                            {parter.length} inaktive parter i arkivet.
                            Velg parter og klikk «Reaktiver kontrakter» for å gjenopprette aktiv status.
                        </p>
                    </div>
                )}

                {/* ── KONTRAKTER TAB ── */}
                {tab === "kontrakter" && (
                    <div className="space-y-4">
                        <div className="flex gap-3 items-center">
                            <input
                                type="search"
                                placeholder="Søk på navn, leietaker, eiendom…"
                                value={kontraktSok}
                                onChange={(e) => setKontraktSok(e.target.value)}
                                className="enterprise-input flex-1 max-w-sm"
                            />
                            <span className="text-sm text-muted">{filteredKontrakter.length} kontrakter</span>
                        </div>

                        <div className="rounded-lg border border-border bg-card shadow-sm overflow-hidden">
                            {kontraktLoading ? (
                                <div className="p-12 text-center text-muted">Laster kontrakter…</div>
                            ) : kontraktError ? (
                                <div className="p-12 text-center text-destructive">Feil: {kontraktError}</div>
                            ) : filteredKontrakter.length === 0 ? (
                                <div className="p-12 text-center">
                                    <p className="text-muted text-sm">
                                        {kontraktSok ? "Ingen treff på søket." : "Ingen avsluttede kontrakter i arkivet."}
                                    </p>
                                </div>
                            ) : (
                                <table className="min-w-full divide-y divide-border">
                                    <thead className="bg-surface/80">
                                        <tr>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Kontrakt</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Leietaker</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Eiendom</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Kategori</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Periode</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted">Husleie/år</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border bg-card">
                                        {filteredKontrakter.map((k) => {
                                            const annualRent = k.amount && typeof k.amount === "object"
                                                ? Number((k.amount as any).annual_rent ?? 0)
                                                : 0;
                                            return (
                                                <tr key={k.contract_id} className="hover:bg-surface/40">
                                                    <td className="px-4 py-3">
                                                        <Link href={`/contracts/${k.contract_id}`} className="text-sm font-medium text-foreground hover:text-primary">
                                                            {k.contract_name || <span className="text-muted italic">Uten navn</span>}
                                                        </Link>
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-muted">
                                                        {k.party_id ? (
                                                            <Link href={`/parties/${k.party_id}`} className="hover:text-primary">
                                                                {k.party_name || "–"}
                                                            </Link>
                                                        ) : k.party_name || "–"}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-muted">
                                                        {k.property_id ? (
                                                            <Link href={`/properties/${k.property_id}`} className="hover:text-primary">
                                                                {k.property_name || "–"}
                                                            </Link>
                                                        ) : k.property_name || "–"}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-muted">{k.category || "–"}</td>
                                                    <td className="px-4 py-3 text-sm text-muted whitespace-nowrap">
                                                        {formatDate(k.start_date)} → {formatDate(k.end_date)}
                                                    </td>
                                                    <td className="px-4 py-3 text-sm text-right font-medium text-foreground">
                                                        {formatNOK(annualRent)}
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <span className="inline-flex rounded-full bg-surface border border-border px-2 py-0.5 text-xs text-muted">
                                                            {k.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
