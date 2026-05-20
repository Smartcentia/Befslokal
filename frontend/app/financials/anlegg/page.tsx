"use client";

import { useState, useEffect, useCallback } from "react";
import { API_BASE_URL } from "@/lib/api/client";
import {
    Building2,
    RefreshCw,
    TrendingDown,
    BarChart3,
    AlertCircle,
    CheckCircle2,
    Clock,
    Download,
    Loader2,
} from "lucide-react";

interface FixedAsset {
    id: string;
    asset_name: string;
    koststed_kode: string;
    agresso_dim6_id: string | null;
    original_account: string;
    purchase_date: string | null;
    acquisition_cost: number;
    opening_balance_value: number;
    monthly_depreciation_amount: number;
    remaining_months_at_start: number | null;
    lease_end_date: string | null;
    srs_status: string;
    is_grouped: boolean;
}

interface AvskrivningAr {
    ar: number;
    avskrivning: number;
    restverdi_inngaende: number;
}

interface AnleggData {
    totalt_antall: number;
    aktive: number;
    total_bokfort_verdi: number;
    total_arlig_avskrivning: number;
    assets: FixedAsset[];
    avskrivningsplan: AvskrivningAr[];
}

function fmt(n: number) {
    return new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);
}

function fmtDate(s: string | null) {
    if (!s) return "–";
    return new Date(s).toLocaleDateString("no-NO", { day: "2-digit", month: "short", year: "numeric" });
}

export default function AnleggPage() {
    const [data, setData] = useState<AnleggData | null>(null);
    const [loading, setLoading] = useState(true);
    const [populating, setPopulating] = useState(false);
    const [populateResult, setPopulateResult] = useState<{ inserted: number; skipped_terskel: number; message: string } | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState("");

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE_URL}/financials/srs17/anlegg`, {
                headers: {
                    Authorization: `Bearer ${process.env.NEXT_PUBLIC_API_SECRET || "befs-super-secret-key-12345"}`,
                },
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setData(await res.json());
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Ukjent feil");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchData(); }, [fetchData]);

    const handlePopulate = async () => {
        setPopulating(true);
        setPopulateResult(null);
        try {
            const res = await fetch(`${API_BASE_URL}/financials/srs17/populate`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${process.env.NEXT_PUBLIC_API_SECRET || "befs-super-secret-key-12345"}`,
                },
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            const result = await res.json();
            setPopulateResult(result);
            await fetchData();
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Ukjent feil ved import");
        } finally {
            setPopulating(false);
        }
    };

    const filtered = data?.assets.filter(a =>
        !search ||
        a.asset_name.toLowerCase().includes(search.toLowerCase()) ||
        a.koststed_kode.includes(search) ||
        (a.agresso_dim6_id || "").includes(search)
    ) ?? [];

    const isEmpty = !loading && data?.totalt_antall === 0;

    return (
        <div className="p-8 max-w-7xl mx-auto print:p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-8 print:mb-4">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow">
                            <Building2 size={20} />
                        </div>
                        <h1 className="text-2xl font-bold text-foreground">Anleggsregister – SRS 17</h1>
                    </div>
                    <p className="text-sm text-muted-foreground ml-13">
                        Balanseførte anleggsmidler med lineær avskrivning over gjenværende leieperiode
                    </p>
                </div>
                <div className="flex gap-2 print:hidden">
                    <button
                        onClick={() => window.print()}
                        className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
                    >
                        <Download size={15} />
                        Skriv ut
                    </button>
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
                    >
                        <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
                        Oppdater
                    </button>
                </div>
            </div>

            {/* Populate-knapp for tomt register */}
            {isEmpty && (
                <div className="mb-8 p-6 border border-dashed border-amber-300 bg-amber-50 dark:bg-amber-950/20 rounded-xl">
                    <div className="flex items-start gap-4">
                        <AlertCircle size={22} className="text-amber-500 mt-0.5 shrink-0" />
                        <div className="flex-1">
                            <h3 className="font-semibold text-foreground mb-1">Anleggsregisteret er tomt</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Importer anleggsmidler fra GL-transaksjoner (konto 1268/4960).
                                Terskel: ≥ 50 000 NOK per anlegg. Avskrivning beregnes
                                lineært over gjenværende leieperiode fra 01.01.2025.
                            </p>
                            <button
                                onClick={handlePopulate}
                                disabled={populating}
                                className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm disabled:opacity-60"
                            >
                                {populating ? <Loader2 size={16} className="animate-spin" /> : <Building2 size={16} />}
                                {populating ? "Importerer fra GL…" : "Importer anleggsmidler fra GL"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Populate-resultat */}
            {populateResult && (
                <div className="mb-6 p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-xl flex items-center gap-3">
                    <CheckCircle2 size={18} className="text-green-600 shrink-0" />
                    <p className="text-sm text-green-800 dark:text-green-200">{populateResult.message}. Hoppet over {populateResult.skipped_terskel} under terskel.</p>
                </div>
            )}

            {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3">
                    <AlertCircle size={18} className="text-red-600 shrink-0" />
                    <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
            )}

            {loading && (
                <div className="flex justify-center py-16">
                    <Loader2 size={32} className="animate-spin text-muted-foreground" />
                </div>
            )}

            {data && data.totalt_antall > 0 && (
                <>
                    {/* KPI-kort */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        <div className="bg-card border border-border rounded-xl p-5">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Anleggsmidler</p>
                            <p className="text-2xl font-bold text-foreground">{data.aktive}</p>
                            <p className="text-xs text-muted-foreground mt-1">aktive poster</p>
                        </div>
                        <div className="bg-card border border-border rounded-xl p-5">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Bokført verdi</p>
                            <p className="text-xl font-bold text-foreground">{fmt(data.total_bokfort_verdi)}</p>
                            <p className="text-xs text-muted-foreground mt-1">per 01.01.2025</p>
                        </div>
                        <div className="bg-card border border-border rounded-xl p-5">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Årlig avskrivning</p>
                            <p className="text-xl font-bold text-amber-600">{fmt(data.total_arlig_avskrivning)}</p>
                            <p className="text-xs text-muted-foreground mt-1">konto 6010 (SRS 17)</p>
                        </div>
                        <div className="bg-card border border-border rounded-xl p-5">
                            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Avskr. 2025</p>
                            <p className="text-xl font-bold text-blue-600">
                                {fmt(data.avskrivningsplan.find(p => p.ar === 2025)?.avskrivning ?? 0)}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">dette år</p>
                        </div>
                    </div>

                    {/* Avskrivningsplan */}
                    <div className="bg-card border border-border rounded-xl p-6 mb-8">
                        <div className="flex items-center gap-2 mb-4">
                            <BarChart3 size={18} className="text-blue-600" />
                            <h2 className="font-semibold text-foreground">Avskrivningsplan 2025–2033 (SRS 17)</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-2 px-3 text-muted-foreground font-medium">År</th>
                                        <th className="text-right py-2 px-3 text-muted-foreground font-medium">Restverdi inng.</th>
                                        <th className="text-right py-2 px-3 text-muted-foreground font-medium">Avskrivning</th>
                                        <th className="text-right py-2 px-3 text-muted-foreground font-medium">Restverdi utg.</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.avskrivningsplan.map((row, i) => {
                                        const next = data.avskrivningsplan[i + 1];
                                        const restverdi_utg = next ? next.restverdi_inngaende : 0;
                                        return (
                                            <tr key={row.ar} className={`border-b border-border/50 ${row.ar === 2025 ? "bg-blue-50 dark:bg-blue-950/20 font-medium" : ""}`}>
                                                <td className="py-2 px-3">{row.ar}</td>
                                                <td className="py-2 px-3 text-right">{fmt(row.restverdi_inngaende)}</td>
                                                <td className="py-2 px-3 text-right text-amber-600">–{fmt(row.avskrivning)}</td>
                                                <td className="py-2 px-3 text-right">{fmt(restverdi_utg)}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Anleggsliste */}
                    <div className="bg-card border border-border rounded-xl p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <TrendingDown size={18} className="text-blue-600" />
                                <h2 className="font-semibold text-foreground">Anleggsmidler ({data.totalt_antall})</h2>
                            </div>
                            <input
                                type="search"
                                placeholder="Søk navn, koststed, dim6…"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="px-3 py-1.5 text-sm border border-border rounded-lg bg-background w-64 print:hidden"
                            />
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border text-left">
                                        <th className="py-2 px-3 text-muted-foreground font-medium">Navn</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium">Koststed</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium">Konto</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium text-right">Anskaffelse</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium text-right">Bokført</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium text-right">Mnd. avskr.</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium">Leieslutt</th>
                                        <th className="py-2 px-3 text-muted-foreground font-medium">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.slice(0, 200).map(a => (
                                        <tr key={a.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                                            <td className="py-2 px-3 max-w-64">
                                                <p className="truncate font-medium text-foreground" title={a.asset_name}>{a.asset_name}</p>
                                                {a.agresso_dim6_id && <p className="text-xs text-muted-foreground">Dim6: {a.agresso_dim6_id}</p>}
                                                {a.is_grouped && <span className="text-xs text-amber-600 italic">gruppert</span>}
                                            </td>
                                            <td className="py-2 px-3 text-muted-foreground font-mono text-xs">{a.koststed_kode}</td>
                                            <td className="py-2 px-3">
                                                <span className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-xs rounded font-mono">{a.original_account}</span>
                                            </td>
                                            <td className="py-2 px-3 text-right text-muted-foreground">{fmt(a.acquisition_cost)}</td>
                                            <td className="py-2 px-3 text-right font-medium">{fmt(a.opening_balance_value)}</td>
                                            <td className="py-2 px-3 text-right text-amber-600">
                                                {a.monthly_depreciation_amount > 0 ? fmt(a.monthly_depreciation_amount) : "–"}
                                            </td>
                                            <td className="py-2 px-3 text-muted-foreground">
                                                {a.lease_end_date ? (
                                                    <span className="flex items-center gap-1">
                                                        <Clock size={12} />
                                                        {fmtDate(a.lease_end_date)}
                                                    </span>
                                                ) : <span className="text-red-400 text-xs">ikke koblet</span>}
                                            </td>
                                            <td className="py-2 px-3">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                    a.srs_status === "Aktiv"
                                                        ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                                        : "bg-slate-100 text-slate-600 dark:bg-slate-800"
                                                }`}>
                                                    {a.srs_status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {filtered.length > 200 && (
                                <p className="text-xs text-muted-foreground text-center mt-3">Viser 200 av {filtered.length} rader</p>
                            )}
                        </div>
                    </div>

                    {/* Import-knapp når data finnes */}
                    <div className="mt-6 flex justify-end print:hidden">
                        <button
                            onClick={handlePopulate}
                            disabled={populating}
                            className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors text-muted-foreground"
                        >
                            {populating ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                            {populating ? "Importerer…" : "Kjør GL-import på nytt (legger til nye)"}
                        </button>
                    </div>
                </>
            )}
        </div>
    );
}
