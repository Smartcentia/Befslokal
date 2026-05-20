"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
    ArrowLeft,
    FileSpreadsheet,
    RefreshCw,
    AlertTriangle,
    Info,
    ChevronDown,
    ChevronUp,
    RotateCcw,
} from "lucide-react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function buildAuthHeaders(): Promise<Record<string, string>> {
    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    const {
        data: { session },
    } = await supabase.auth.getSession();
    if (typeof window !== "undefined") {
        const impersonateEmail = localStorage.getItem("impersonate_email");
        const simulateRole = localStorage.getItem("simulate_role");
        if (impersonateEmail) {
            headers["X-Impersonate-Email"] = impersonateEmail;
        } else if (simulateRole && session?.user?.email) {
            headers["X-Simulate-Role"] = simulateRole;
            headers["X-User-Email"] = session.user.email;
        } else if (session?.user?.email) {
            headers["X-User-Email"] = session.user.email;
        }
    }
    return headers;
}

async function downloadBlob(url: string, filename: string): Promise<void> {
    const headers = await buildAuthHeaders();
    const res = await fetch(url, { cache: "no-store", credentials: "include", headers });
    if (!res.ok) throw new Error(`Nedlasting feilet (HTTP ${res.status})`);
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(objectUrl);
}

// ─── Formatering ─────────────────────────────────────────────────────────────

function fmtNOK(n: number): string {
    if (Math.abs(n) >= 1_000_000_000)
        return (n / 1_000_000_000).toFixed(2).replace(".", ",") + " mrd";
    if (Math.abs(n) >= 1_000_000)
        return (n / 1_000_000).toFixed(1).replace(".", ",") + " M";
    return Math.round(n)
        .toString()
        .replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
}

function fmtPst(n: number): string {
    return (n > 0 ? "+" : "") + n.toFixed(1).replace(".", ",") + " %";
}

function pstColor(pst: number): string {
    if (pst > 25) return "text-red-600";
    if (pst > 12) return "text-yellow-600";
    return "text-green-600";
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface RegionRow {
    region: string;
    belop_2027: number;
    belop_2025: number;
    endring_pst: number | null;
}

interface EiendomRow {
    property_id: string;
    name: string;
    region: string;
    belop_2027: number;
    belop_2025: number;
    endring_pst: number | null;
}

interface KategoriRow {
    kategori: string;
    belop_2027: number;
    belop_2025: number;
    endring_pst: number | null;
}

interface Sanity {
    ok: boolean;
    advarsler: string[];
    eiendommer_uten_prediksjon: number;
}

interface OutlierRow {
    name: string;
    region: string;
    b2025: number;
    b2027: number;
    flags: string[];
    endring_pct?: number;
    cv?: number;
    ratio_vs_median?: number;
    historisk_median?: number;
}

interface PredData {
    ar: number;
    generert: boolean;
    antall_eiendommer: number;
    total_2027: number;
    total_2025_gl: number;
    endring_pst: number | null;
    per_region: RegionRow[];
    per_eiendom_topp20: EiendomRow[];
    per_kategori: KategoriRow[];
    sanity: Sanity;
    lonn_2027: number;
    lonn_2025: number;
    lonn_generert: boolean;
    lonn_endring_pst: number | null;
    outliers?: OutlierRow[];
}

interface BacktestYear {
    overall: {
        mape: number;
        predicted: number;
        actual: number;
        endring_pst: number | null;
        n_properties: number;
    };
    per_category: Record<string, {
        mape: number;
        mae: number;
        predicted: number;
        actual: number;
        endring_pst: number | null;
        n_properties: number;
    }>;
}

interface BacktestData {
    test_years: number[];
    parameters: Record<string, number>;
    results: Record<string, BacktestYear>;
    error?: string;
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_INFLATION = 7.5;
const DEFAULT_LONN_VEKST = 4.5;

// ─── Komponenter ──────────────────────────────────────────────────────────────

function EditableCell({
    value,
    onChange,
    suffix = "",
    min,
    max,
}: {
    value: number;
    onChange: (v: number) => void;
    suffix?: string;
    min?: number;
    max?: number;
}) {
    const [raw, setRaw] = useState(value.toString().replace(".", ","));
    const [focused, setFocused] = useState(false);

    useEffect(() => {
        if (!focused) setRaw(value.toString().replace(".", ","));
    }, [value, focused]);

    return (
        <span className="inline-flex items-center gap-0.5">
            <input
                className="w-16 text-right bg-amber-50 border border-amber-300 rounded px-1.5 py-0.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-amber-400 focus:bg-amber-100"
                value={raw}
                onFocus={() => setFocused(true)}
                onChange={(e) => setRaw(e.target.value)}
                onBlur={() => {
                    setFocused(false);
                    const parsed = parseFloat(raw.replace(",", "."));
                    if (!isNaN(parsed)) {
                        const clamped = min !== undefined ? Math.max(min, parsed) : parsed;
                        const clamped2 = max !== undefined ? Math.min(max, clamped) : clamped;
                        onChange(clamped2);
                        setRaw(clamped2.toString().replace(".", ","));
                    } else {
                        setRaw(value.toString().replace(".", ","));
                    }
                }}
                onKeyDown={(e) => {
                    if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                    if (e.key === "Escape") {
                        setRaw(value.toString().replace(".", ","));
                        (e.target as HTMLInputElement).blur();
                    }
                }}
            />
            {suffix && <span className="text-xs text-muted">{suffix}</span>}
        </span>
    );
}

function SectionHeader({
    title,
    open,
    onToggle,
}: {
    title: string;
    open: boolean;
    onToggle: () => void;
}) {
    return (
        <button
            onClick={onToggle}
            className="w-full flex items-center justify-between py-2 px-1 text-left hover:bg-muted/5 rounded transition-colors"
        >
            <span className="font-semibold text-sm uppercase tracking-wider text-muted/70">
                {title}
            </span>
            {open ? (
                <ChevronUp className="h-4 w-4 text-muted/50" />
            ) : (
                <ChevronDown className="h-4 w-4 text-muted/50" />
            )}
        </button>
    );
}

// ─── Hovedkomponent ───────────────────────────────────────────────────────────

export default function BudsjettPage() {
    const [data, setData] = useState<PredData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [downloading, setDownloading] = useState(false);
    const [backtest, setBacktest] = useState<BacktestData | null>(null);
    const [backtestLoading, setBacktestLoading] = useState(false);

    // Justeringsvariable
    const [inflasjon, setInflasjon] = useState(DEFAULT_INFLATION);
    const [lonnVekst, setLonnVekst] = useState(DEFAULT_LONN_VEKST);
    const [regionFaktorer, setRegionFaktorer] = useState<Record<string, number>>({});

    // UI state
    const [showAntagelser, setShowAntagelser] = useState(true);
    const [showRegioner, setShowRegioner] = useState(true);
    const [showKategorier, setShowKategorier] = useState(true);
    const [showTopp20, setShowTopp20] = useState(true);
    const [showSanity, setShowSanity] = useState(false);
    const [showMetodikk, setShowMetodikk] = useState(false);
    const [showBacktest, setShowBacktest] = useState(false);
    const [showOutliers, setShowOutliers] = useState(true);

    // ── Data-henting ──────────────────────────────────────────────────────────
    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(`${API_BASE}/api/v1/financials/prediksjon-2027`, {
                headers,
                cache: "no-store",
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json: PredData = await res.json();
            setData(json);
            // Initialiser region-faktorer
            const faktorer: Record<string, number> = {};
            for (const r of json.per_region) faktorer[r.region] = 1.0;
            setRegionFaktorer(faktorer);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Ukjent feil");
        } finally {
            setLoading(false);
        }
    }, []);

    const loadBacktest = useCallback(async () => {
        setBacktestLoading(true);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(`${API_BASE}/api/v1/financials/backtest`, {
                headers,
                cache: "no-store",
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json: BacktestData = await res.json();
            setBacktest(json);
        } catch {
            // Non-fatal — backtest is optional
        } finally {
            setBacktestLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        loadBacktest();
    }, [load, loadBacktest]);

    // ── Kalkulasjoner ─────────────────────────────────────────────────────────
    const justert = useMemo(() => {
        if (!data) return null;

        const inflFaktor = 1 + inflasjon / 100;

        // Per region
        const perRegion = data.per_region.map((r) => {
            const faktor = regionFaktorer[r.region] ?? 1.0;
            const justert_belop = r.belop_2027 * inflFaktor * faktor;
            return {
                ...r,
                justert_belop,
                endring_vs_2025: r.belop_2025 > 0 ? ((justert_belop - r.belop_2025) / r.belop_2025) * 100 : null,
            };
        });

        const totalJustert = perRegion.reduce((s, r) => s + r.justert_belop, 0);
        const totalEndring = data.total_2025_gl > 0
            ? ((totalJustert - data.total_2025_gl) / data.total_2025_gl) * 100
            : null;

        // Per kategori (kun inflasjon, ingen region-faktor tilgjengelig)
        const perKategori = data.per_kategori.map((k) => ({
            ...k,
            justert_belop: k.belop_2027 * inflFaktor,
        }));

        // Lønn
        const lonnFaktor = 1 + lonnVekst / 100;
        const lonnJustert = data.lonn_2027 * lonnFaktor;

        // Topp 20
        const topp20 = data.per_eiendom_topp20.map((e) => {
            const faktor = regionFaktorer[e.region] ?? 1.0;
            return {
                ...e,
                justert_belop: e.belop_2027 * inflFaktor * faktor,
            };
        });

        // Totalbudsjett (eiendom + lønn)
        const budsjettTotal = totalJustert + lonnJustert;

        return {
            perRegion,
            perKategori,
            topp20,
            totalJustert,
            totalEndring,
            lonnJustert,
            budsjettTotal,
        };
    }, [data, inflasjon, lonnVekst, regionFaktorer]);

    const resetAll = () => {
        setInflasjon(DEFAULT_INFLATION);
        setLonnVekst(DEFAULT_LONN_VEKST);
        if (data) {
            const faktorer: Record<string, number> = {};
            for (const r of data.per_region) faktorer[r.region] = 1.0;
            setRegionFaktorer(faktorer);
        }
    };

    const handleDownload = async () => {
        setDownloading(true);
        try {
            await downloadBlob(
                `${API_BASE}/api/v1/financials/prediksjon-2027/export.xlsx`,
                "prediksjon_2027.xlsx"
            );
        } catch (e: unknown) {
            alert(e instanceof Error ? e.message : "Nedlasting feilet");
        } finally {
            setDownloading(false);
        }
    };

    // ── Render ─────────────────────────────────────────────────────────────────

    if (loading)
        return (
            <div className="flex items-center justify-center h-64">
                <RefreshCw className="h-6 w-6 animate-spin text-muted/50" />
            </div>
        );

    if (error)
        return (
            <div className="p-8 text-center">
                <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                <p className="text-sm text-muted">{error}</p>
                <button
                    onClick={load}
                    className="mt-4 text-xs underline text-primary"
                >
                    Prøv igjen
                </button>
            </div>
        );

    if (!data || !justert)
        return (
            <div className="p-8 text-center text-muted text-sm">
                Ingen prediksjon tilgjengelig. Kjør prediksjon fra oversiktssiden.
            </div>
        );

    return (
        <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
            {/* Topplinje */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3">
                    <Link
                        href="/financials/prediksjon"
                        className="flex items-center gap-1.5 text-sm text-muted hover:text-foreground transition-colors"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Tilbake til prediksjon
                    </Link>
                    <span className="text-muted/30">|</span>
                    <h1 className="text-lg font-semibold">Budsjettjustering 2027</h1>
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-medium">
                        Interaktiv
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={resetAll}
                        className="flex items-center gap-1.5 text-xs border border-border rounded px-2.5 py-1.5 hover:bg-muted/10 transition-colors"
                    >
                        <RotateCcw className="h-3 w-3" />
                        Nullstill
                    </button>
                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="flex items-center gap-1.5 text-xs border border-border rounded px-2.5 py-1.5 hover:bg-muted/10 transition-colors disabled:opacity-50"
                    >
                        {downloading ? (
                            <RefreshCw className="h-3 w-3 animate-spin" />
                        ) : (
                            <FileSpreadsheet className="h-3 w-3" />
                        )}
                        Last ned Excel
                    </button>
                </div>
            </div>

            {/* Sammendragskort */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="border border-border rounded-lg p-4 bg-card">
                    <p className="text-xs text-muted uppercase tracking-wider mb-1">
                        Eiendomsdrift 2027
                    </p>
                    <p className="text-xl font-bold tabular-nums">
                        {fmtNOK(justert.totalJustert)}
                    </p>
                    {justert.totalEndring !== null && (
                        <p className={`text-xs mt-0.5 ${pstColor(justert.totalEndring)}`}>
                            {fmtPst(justert.totalEndring)} vs 2025
                        </p>
                    )}
                </div>
                <div className="border border-border rounded-lg p-4 bg-card">
                    <p className="text-xs text-muted uppercase tracking-wider mb-1">
                        Lønnskostnader 2027
                    </p>
                    <p className="text-xl font-bold tabular-nums">
                        {fmtNOK(justert.lonnJustert)}
                    </p>
                    {data.lonn_endring_pst !== null && (
                        <p className={`text-xs mt-0.5 ${pstColor(data.lonn_endring_pst)}`}>
                            Holt-Winters: {fmtPst(data.lonn_endring_pst)}
                        </p>
                    )}
                </div>
                <div className="border border-border rounded-lg p-4 bg-card md:col-span-2">
                    <p className="text-xs text-muted uppercase tracking-wider mb-1">
                        Totalt budsjettbehov 2027
                    </p>
                    <p className="text-2xl font-bold tabular-nums">
                        {fmtNOK(justert.budsjettTotal)}
                    </p>
                    <p className="text-xs text-muted mt-0.5">
                        Eiendom + lønn etter justeringer
                    </p>
                </div>
            </div>

            {/* Antagelser */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Antagelser og justeringsfaktorer"
                        open={showAntagelser}
                        onToggle={() => setShowAntagelser((v) => !v)}
                    />
                </div>
                {showAntagelser && (
                    <div className="px-4 pb-4 space-y-5">
                        <p className="text-xs text-muted flex items-center gap-1.5">
                            <Info className="h-3.5 w-3.5 shrink-0" />
                            Gule felt kan redigeres. Endre et tall og se alle avhengige celler
                            oppdateres umiddelbart.
                        </p>

                        {/* Globale faktorer */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-muted uppercase tracking-wider">
                                    Generell kostnadsvekst / inflasjon
                                </label>
                                <div className="flex items-center gap-3">
                                    <EditableCell
                                        value={inflasjon}
                                        onChange={setInflasjon}
                                        suffix="%"
                                        min={-20}
                                        max={50}
                                    />
                                    <span className="text-xs text-muted">
                                        Legges på eiendomsdriftsprediksjonen (HW-tall × (1 + x/100))
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min={-10}
                                    max={30}
                                    step={0.5}
                                    value={inflasjon}
                                    onChange={(e) => setInflasjon(parseFloat(e.target.value))}
                                    className="w-full accent-amber-500"
                                />
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-medium text-muted uppercase tracking-wider">
                                    Lønnsøkning (utover HW-prediksjon)
                                </label>
                                <div className="flex items-center gap-3">
                                    <EditableCell
                                        value={lonnVekst}
                                        onChange={setLonnVekst}
                                        suffix="%"
                                        min={-20}
                                        max={50}
                                    />
                                    <span className="text-xs text-muted">
                                        Multiplikator på Holt-Winters lønnsprediksjon for 2027
                                    </span>
                                </div>
                                <input
                                    type="range"
                                    min={-5}
                                    max={20}
                                    step={0.5}
                                    value={lonnVekst}
                                    onChange={(e) => setLonnVekst(parseFloat(e.target.value))}
                                    className="w-full accent-amber-500"
                                />
                            </div>
                        </div>

                        {/* Regionfaktorer */}
                        <div>
                            <p className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
                                Region-faktorer (multiplikator etter inflasjon)
                            </p>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                {data.per_region.map((r) => (
                                    <div
                                        key={r.region}
                                        className="flex items-center justify-between gap-2 border border-border/50 rounded px-2 py-1.5 bg-muted/5"
                                    >
                                        <span className="text-sm truncate">{r.region}</span>
                                        <EditableCell
                                            value={regionFaktorer[r.region] ?? 1.0}
                                            onChange={(v) =>
                                                setRegionFaktorer((prev) => ({
                                                    ...prev,
                                                    [r.region]: v,
                                                }))
                                            }
                                            suffix="×"
                                            min={0.1}
                                            max={5}
                                        />
                                    </div>
                                ))}
                            </div>
                            <p className="text-xs text-muted mt-1.5">
                                1,00 = ingen regionspesifikk justering. 1,10 = 10 % ekstra for regionen.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Per region */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Per region"
                        open={showRegioner}
                        onToggle={() => setShowRegioner((v) => !v)}
                    />
                </div>
                {showRegioner && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30">
                                    <th className="text-left px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        Region
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        2025 GL
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        HW 2027
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-amber-600">
                                        Justert 2027
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        vs 2025
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {justert.perRegion.map((r) => (
                                    <tr
                                        key={r.region}
                                        className="border-b border-border/40 hover:bg-muted/5"
                                    >
                                        <td className="px-4 py-2.5 font-medium">{r.region}</td>
                                        <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                                            {fmtNOK(r.belop_2025)}
                                        </td>
                                        <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                                            {fmtNOK(r.belop_2027)}
                                        </td>
                                        <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-amber-700">
                                            {fmtNOK(r.justert_belop)}
                                        </td>
                                        <td className={`px-4 py-2.5 text-right tabular-nums text-xs ${r.endring_vs_2025 !== null ? pstColor(r.endring_vs_2025) : "text-muted"}`}>
                                            {r.endring_vs_2025 !== null
                                                ? fmtPst(r.endring_vs_2025)
                                                : "—"}
                                        </td>
                                    </tr>
                                ))}
                                <tr className="border-t-2 border-border bg-muted/10">
                                    <td className="px-4 py-2.5 font-bold text-xs uppercase">Totalt</td>
                                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-muted">
                                        {fmtNOK(data.total_2025_gl)}
                                    </td>
                                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-muted">
                                        {fmtNOK(data.total_2027)}
                                    </td>
                                    <td className="px-4 py-2.5 text-right tabular-nums font-bold text-amber-700">
                                        {fmtNOK(justert.totalJustert)}
                                    </td>
                                    <td className={`px-4 py-2.5 text-right tabular-nums text-xs font-semibold ${justert.totalEndring !== null ? pstColor(justert.totalEndring) : "text-muted"}`}>
                                        {justert.totalEndring !== null
                                            ? fmtPst(justert.totalEndring)
                                            : "—"}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Per kategori */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Per driftskategori"
                        open={showKategorier}
                        onToggle={() => setShowKategorier((v) => !v)}
                    />
                </div>
                {showKategorier && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30">
                                    <th className="text-left px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        Kategori
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        2025 GL
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        HW 2027
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-amber-600">
                                        Justert 2027
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {justert.perKategori.map((k) => (
                                    <tr
                                        key={k.kategori}
                                        className="border-b border-border/40 hover:bg-muted/5"
                                    >
                                        <td className="px-4 py-2.5 font-medium">{k.kategori}</td>
                                        <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                                            {fmtNOK(k.belop_2025)}
                                        </td>
                                        <td className="px-4 py-2.5 text-right tabular-nums text-muted">
                                            {fmtNOK(k.belop_2027)}
                                        </td>
                                        <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-amber-700">
                                            {fmtNOK(k.justert_belop)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Topp 20 */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Topp 20 eiendommer (justert)"
                        open={showTopp20}
                        onToggle={() => setShowTopp20((v) => !v)}
                    />
                </div>
                {showTopp20 && (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30">
                                    <th className="text-left px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted w-8">
                                        #
                                    </th>
                                    <th className="text-left px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        Eiendom
                                    </th>
                                    <th className="text-left px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        Region
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        2025 GL
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                        HW 2027
                                    </th>
                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-amber-600">
                                        Justert 2027
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {justert.topp20.map((e, i) => (
                                    <tr
                                        key={e.property_id}
                                        className="border-b border-border/40 hover:bg-muted/5"
                                    >
                                        <td className="px-4 py-2 text-muted text-xs tabular-nums">
                                            {i + 1}
                                        </td>
                                        <td className="px-4 py-2 font-medium">{e.name}</td>
                                        <td className="px-4 py-2 text-muted text-xs">{e.region}</td>
                                        <td className="px-4 py-2 text-right tabular-nums text-muted">
                                            {fmtNOK(e.belop_2025)}
                                        </td>
                                        <td className="px-4 py-2 text-right tabular-nums text-muted">
                                            {fmtNOK(e.belop_2027)}
                                        </td>
                                        <td className="px-4 py-2 text-right tabular-nums font-semibold text-amber-700">
                                            {fmtNOK(e.justert_belop)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Sanity-advarsler */}
            {data.sanity && (
                <div className="border border-border rounded-lg overflow-hidden bg-card">
                    <div className="px-4 pt-3 pb-1">
                        <SectionHeader
                            title={`Datakvalitet og advarsler${data.sanity.advarsler.length > 0 ? ` (${data.sanity.advarsler.length})` : ""}`}
                            open={showSanity}
                            onToggle={() => setShowSanity((v) => !v)}
                        />
                    </div>
                    {showSanity && (
                        <div className="px-4 pb-4 space-y-2">
                            {data.sanity.advarsler.length === 0 ? (
                                <p className="text-xs text-green-600">Ingen advarsler funnet.</p>
                            ) : (
                                data.sanity.advarsler.map((a, i) => (
                                    <div
                                        key={i}
                                        className="flex gap-2 text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded px-3 py-2"
                                    >
                                        <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                                        {a}
                                    </div>
                                ))
                            )}
                            {data.sanity.eiendommer_uten_prediksjon > 0 && (
                                <p className="text-xs text-muted">
                                    {data.sanity.eiendommer_uten_prediksjon} eiendom(mer) mangler prediksjon.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Metodikk og forutsetninger */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Metodikk og forutsetninger"
                        open={showMetodikk}
                        onToggle={() => setShowMetodikk((v) => !v)}
                    />
                </div>
                {showMetodikk && (
                    <div className="px-4 pb-5 space-y-4 text-sm">

                        {/* Hvorfor denne metoden */}
                        <div className="bg-blue-50/40 border border-blue-100 rounded-md px-3 py-2.5 space-y-1 text-xs text-foreground/80">
                            <p className="font-semibold text-blue-800 text-xs uppercase tracking-wider mb-1">Hvorfor Holt-Winters og ikke enkel %-vekst?</p>
                            <p>Eiendomskostnader vokser ikke jevnt fra år til år — de påvirkes av investeringssykluser, kontraktsjusteringer og engangseffekter. En ren «fjoråret + 5%» gir skjeve tall når fjoråret var uvanlig høyt eller lavt.</p>
                            <p>Holt-Winters gir nyere år større vekt enn eldre år, skiller mellom underliggende nivå og trend, og demper trenden jo lenger frem vi ser (φ=0,85). Modellen er robust, transparent og gir etterprøvbare resultater — i motsetning til maskinlæringsmodeller.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <h3 className="font-semibold text-xs uppercase tracking-wider text-muted">Modell</h3>
                                <div className="space-y-1.5 text-xs text-foreground/80">
                                    <p><span className="font-medium">Algoritme:</span> Holt&apos;s Linear Exponential Smoothing med dempet trend (φ=0,85)</p>
                                    <p><span className="font-medium">Nivåvekt α=0,5:</span> Halvparten av vekten på siste år, halvparten på modellens tidligere anslag. Reagerer raskt, men glatter ut enkeltstående avvik.</p>
                                    <p><span className="font-medium">Trendvekt β=0,2:</span> Trenden oppdateres sakte — modellen snur ikke retning basert på ett enkelt år. Riktig for stabile eiendomskostnader.</p>
                                    <p><span className="font-medium">Historikk:</span> GL-transaksjoner per eiendom, 2021–2025 (5 år). CPI-deflasjon til 2025-kroner (SSB KPI) før modellkjøring.</p>
                                    <p><span className="font-medium">Kort historikk (&lt;3 år):</span> Inflasjonsfallback — siste kjente år × (1+3,5%)²</p>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h3 className="font-semibold text-xs uppercase tracking-wider text-muted">Kategoriregler</h3>
                                <div className="space-y-1.5 text-xs text-foreground/80">
                                    <p><span className="font-medium">Gjennomstrømning (husleie):</span> Kun inflasjonsfremskrivning — kontraktsbasert, ikke trendbasert</p>
                                    <p><span className="font-medium">Drift, Investering, Annet:</span> Holt-Winters trend + inflasjon</p>
                                    <p><span className="font-medium">Maks veksttak:</span> Prediksjon kappes til 5× historisk median. Eiendommer som treffer taket flagges automatisk som <span className="text-red-600 font-medium">røde</span> i outlier-tabellen under — de fanges opp uansett.</p>
                                </div>
                            </div>
                        </div>

                        <div className="border-t border-border/50 pt-3 space-y-2">
                            <h3 className="font-semibold text-xs uppercase tracking-wider text-muted">Justeringslag og parameterstapling</h3>
                            <div className="space-y-1.5 text-xs text-foreground/80">
                                <p>Tallene beregnes i tre sekvensielle lag — de multipliseres, ikke adderes:</p>
                                <ol className="list-decimal list-inside space-y-1 ml-2">
                                    <li><span className="font-medium">HW 2027</span> — Holt-Winters prediksjon med intern inflasjon 3,5% per år (allerede innbakt)</li>
                                    <li><span className="font-medium">Inflasjonspåslag</span> — HW × (1 + 7,5%). <span className="font-medium text-amber-700">Total effekt over 2025-faktisk er ca. 14–15%</span>, ikke 11%, fordi lagene multipliseres. 7,5% er tiltenkt som handlingsrom — ikke et beløp som skal brukes opp automatisk.</li>
                                    <li><span className="font-medium">Regionfaktor</span> — justerbart multiplikator per region (standard 1,00 = ingen endring)</li>
                                </ol>
                                <p className="text-muted font-mono mt-1">Justert 2027 = HW 2027 × (1 + inflasjon%) × regionfaktor</p>
                            </div>
                        </div>

                        <div className="border-t border-border/50 pt-3 space-y-2">
                            <h3 className="font-semibold text-xs uppercase tracking-wider text-muted">Dekningsgrad</h3>
                            <div className="space-y-1.5 text-xs text-foreground/80">
                                <p><span className="font-medium">192 eiendommer</span> har 2027-prediksjon basert på GL-historikk.</p>
                                <p><span className="font-medium">~20 eiendommer mangler prediksjon</span> — har lønnsdata men ingen GL-transaksjoner koblet i systemet. Mulige årsaker: (a) ny eiendom uten historikk, eller (b) GL-data finnes i Agresso men koststedet er ikke koblet. Disse er ikke inkludert i totalen og må budsjetteres manuelt.</p>
                                <p><span className="font-medium">Lønn:</span> Separat Holt-Winters på lønnsdata. Lønnsøkning-justeringen legges på toppen.</p>
                            </div>
                        </div>

                        <div className="border-t border-border/50 pt-3 space-y-2">
                            <h3 className="font-semibold text-xs uppercase tracking-wider text-muted">Begrensninger — fanges ikke opp automatisk</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-xs text-foreground/70">
                                <p><span className="font-medium text-foreground/90">Planlagte investeringer</span> — kjente prosjekter må legges til manuelt</p>
                                <p><span className="font-medium text-foreground/90">Kontraktsendringer</span> — nye eller reforhandlede husleieavtaler</p>
                                <p><span className="font-medium text-foreground/90">Politiske vedtak</span> — kapasitetskutt, omstrukturering, tjenesteavvikling</p>
                                <p><span className="font-medium text-foreground/90">Datakvalitet</span> — manglende eller feilkonterte GL-transaksjoner gir misvisende prediksjoner</p>
                            </div>
                            <p className="text-muted italic text-xs pt-1">Tallene er estimater og ikke offisielle budsjettvedtak. Kilde: BEFS GL-data 2021–2025.</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Backtesting */}
            <div className="border border-border rounded-lg overflow-hidden bg-card">
                <div className="px-4 pt-3 pb-1">
                    <SectionHeader
                        title="Backtesting – historisk prediksjonsnoeyaktighet"
                        open={showBacktest}
                        onToggle={() => setShowBacktest((v) => !v)}
                    />
                </div>
                {showBacktest && (
                    <div className="px-4 pb-5 space-y-4">
                        {backtestLoading ? (
                            <p className="text-xs text-muted animate-pulse py-4">Kjorer backtesting...</p>
                        ) : !backtest || Object.keys(backtest.results).length === 0 ? (
                            <p className="text-xs text-muted py-4">Ingen backtesting-data tilgjengelig.</p>
                        ) : (
                            <>
                                <div className="bg-blue-50/40 border border-blue-100 rounded-md px-3 py-2.5 text-xs text-foreground/80 space-y-1">
                                    <p className="font-semibold text-blue-800 text-xs uppercase tracking-wider mb-1">Hva er backtesting?</p>
                                    <p>
                                        For hvert testaar trenes modellen kun pa historikk t.o.m. aaret foer, predikerer det aktuelle aaret
                                        og sammenligner med faktisk GL. Samme parametre som brukes for 2027 (α=0,5, β=0,2, φ=0,85, maks 8 %/ar).
                                        <span className="font-medium"> MAPE under 15 % er god noeyaktighet.</span>
                                    </p>
                                </div>

                                {/* Overall per år */}
                                <div>
                                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">Overordnet noeyaktighet per testaar</h3>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-xs">
                                            <thead>
                                                <tr className="border-b border-border bg-muted/10">
                                                    <th className="text-left px-3 py-2 font-medium text-muted">Testaar</th>
                                                    <th className="text-left px-3 py-2 font-medium text-muted">Trener pa</th>
                                                    <th className="text-right px-3 py-2 font-medium text-muted">Ant. eiendommer</th>
                                                    <th className="text-right px-3 py-2 font-medium text-muted">Faktisk GL</th>
                                                    <th className="text-right px-3 py-2 font-medium text-muted">Predikert</th>
                                                    <th className="text-right px-3 py-2 font-medium text-muted">Avvik %</th>
                                                    <th className="text-right px-3 py-2 font-medium text-muted">MAPE</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {backtest.test_years.map((yr) => {
                                                    const yrData = backtest.results[yr.toString()] || backtest.results[yr];
                                                    if (!yrData) return null;
                                                    const ov = yrData.overall;
                                                    const mapeColor =
                                                        ov.mape < 15 ? "text-green-700 bg-green-50" :
                                                        ov.mape < 30 ? "text-yellow-700 bg-yellow-50" :
                                                        "text-red-700 bg-red-50";
                                                    return (
                                                        <tr key={yr} className="border-b border-border/40 hover:bg-muted/5">
                                                            <td className="px-3 py-2 font-semibold">{yr}</td>
                                                            <td className="px-3 py-2 text-muted">2021–{yr - 1}</td>
                                                            <td className="px-3 py-2 text-right tabular-nums text-muted">{ov.n_properties}</td>
                                                            <td className="px-3 py-2 text-right tabular-nums">{fmtNOK(ov.actual)}</td>
                                                            <td className="px-3 py-2 text-right tabular-nums">{fmtNOK(ov.predicted)}</td>
                                                            <td className={`px-3 py-2 text-right tabular-nums font-medium ${ov.endring_pst != null && Math.abs(ov.endring_pst) > 15 ? "text-orange-600" : "text-muted"}`}>
                                                                {ov.endring_pst != null ? fmtPst(ov.endring_pst) : "—"}
                                                            </td>
                                                            <td className="px-3 py-2 text-right">
                                                                <span className={`inline-block px-2 py-0.5 rounded font-semibold tabular-nums ${mapeColor}`}>
                                                                    {ov.mape.toFixed(1)} %
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* MAPE per kategori */}
                                <div>
                                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-2">MAPE per kategori</h3>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-xs">
                                            <thead>
                                                <tr className="border-b border-border bg-muted/10">
                                                    <th className="text-left px-3 py-2 font-medium text-muted">Kategori</th>
                                                    {backtest.test_years.map((yr) => (
                                                        <th key={yr} className="text-right px-3 py-2 font-medium text-muted">{yr}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {(() => {
                                                    const allCats = new Set<string>();
                                                    backtest.test_years.forEach((yr) => {
                                                        const yrData = backtest.results[yr.toString()] || backtest.results[yr];
                                                        if (yrData) Object.keys(yrData.per_category).forEach((c) => allCats.add(c));
                                                    });
                                                    return Array.from(allCats).sort().map((cat) => (
                                                        <tr key={cat} className="border-b border-border/40 hover:bg-muted/5">
                                                            <td className="px-3 py-2 font-medium">{cat}</td>
                                                            {backtest.test_years.map((yr) => {
                                                                const yrData = backtest.results[yr.toString()] || backtest.results[yr];
                                                                const catData = yrData?.per_category?.[cat];
                                                                const mape = catData?.mape;
                                                                const mapeColor =
                                                                    mape == null ? "" :
                                                                    mape < 15 ? "text-green-700 bg-green-50" :
                                                                    mape < 30 ? "text-yellow-700 bg-yellow-50" :
                                                                    "text-red-700 bg-red-50";
                                                                return (
                                                                    <td key={yr} className="px-3 py-2 text-right">
                                                                        {mape != null ? (
                                                                            <span className={`inline-block px-2 py-0.5 rounded font-semibold tabular-nums ${mapeColor}`}>
                                                                                {mape.toFixed(1)} %
                                                                            </span>
                                                                        ) : "—"}
                                                                    </td>
                                                                );
                                                            })}
                                                        </tr>
                                                    ));
                                                })()}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                <p className="text-xs text-muted italic">
                                    MAPE = Mean Absolute Percentage Error. Under 15 % = god (grønn). 15–30 % = akseptabel (gul). Over 30 % = vurder rekalibrering (rød).
                                </p>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Outlier-flagg */}
            {data.outliers && data.outliers.length > 0 && (
                <div className="border border-amber-300 rounded-lg overflow-hidden bg-amber-50/30">
                    <div className="px-4 pt-3 pb-1">
                        <SectionHeader
                            title={`Outliers – eiendommer som bør vurderes manuelt (${data.outliers.length})`}
                            open={showOutliers}
                            onToggle={() => setShowOutliers((v) => !v)}
                        />
                    </div>
                    {showOutliers && (
                        <div className="px-4 pb-4 space-y-2">
                            <p className="text-xs text-muted mb-3">
                                Tre flaggkategorier: <span className="text-red-600 font-medium">oppblåst_ratio</span> = prediksjon &gt;5× historisk median |{" "}
                                <span className="text-orange-600 font-medium">høy_endring</span> = &gt;50% avvik fra 2025 |{" "}
                                <span className="text-yellow-700 font-medium">høy_variasjon</span> = ustabil historikk (CV &gt;0,5)
                            </p>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="border-b border-amber-200 bg-amber-100/50">
                                            <th className="text-left px-3 py-2 font-medium text-muted uppercase tracking-wider">Eiendom</th>
                                            <th className="text-left px-3 py-2 font-medium text-muted uppercase tracking-wider">Region</th>
                                            <th className="text-right px-3 py-2 font-medium text-muted uppercase tracking-wider">2025 GL</th>
                                            <th className="text-right px-3 py-2 font-medium text-muted uppercase tracking-wider">HW 2027</th>
                                            <th className="text-right px-3 py-2 font-medium text-muted uppercase tracking-wider">Endring</th>
                                            <th className="text-left px-3 py-2 font-medium text-muted uppercase tracking-wider">Flagg</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.outliers.map((o, i) => {
                                            const isRed = o.flags.includes("oppblåst_ratio");
                                            const isOrange = !isRed && o.flags.includes("høy_endring");
                                            const rowCls = isRed
                                                ? "bg-red-50 border-red-100"
                                                : isOrange
                                                ? "bg-orange-50 border-orange-100"
                                                : "bg-yellow-50/50 border-yellow-100";
                                            return (
                                                <tr key={i} className={`border-b ${rowCls}`}>
                                                    <td className="px-3 py-2 font-medium max-w-56 truncate">{o.name}</td>
                                                    <td className="px-3 py-2 text-muted">{o.region}</td>
                                                    <td className="px-3 py-2 text-right tabular-nums text-muted">{Math.round(o.b2025).toLocaleString("nb-NO")}</td>
                                                    <td className="px-3 py-2 text-right tabular-nums font-medium">{Math.round(o.b2027).toLocaleString("nb-NO")}</td>
                                                    <td className={`px-3 py-2 text-right tabular-nums ${o.endring_pct != null && Math.abs(o.endring_pct) > 50 ? "text-red-600 font-semibold" : "text-muted"}`}>
                                                        {o.endring_pct != null ? (o.endring_pct > 0 ? "+" : "") + o.endring_pct.toFixed(1) + "%" : "—"}
                                                    </td>
                                                    <td className="px-3 py-2">
                                                        <div className="flex flex-wrap gap-1">
                                                            {o.flags.map((f) => (
                                                                <span key={f} className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                                                                    f === "oppblåst_ratio" ? "bg-red-100 text-red-700" :
                                                                    f === "høy_endring" ? "bg-orange-100 text-orange-700" :
                                                                    "bg-yellow-100 text-yellow-700"
                                                                }`}>{f.replace("_", " ")}</span>
                                                            ))}
                                                            {o.ratio_vs_median != null && (
                                                                <span className="text-muted">({o.ratio_vs_median.toFixed(1)}× median)</span>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Footer */}
            <p className="text-xs text-muted/50 text-center pb-4">
                Prediksjon basert på Holt-Winters dobbeleksponentielt glatting. Tall er estimater og ikke offisielle budsjettall.
                Kilde: BEFS GL-data 2020–2025 + lønnsdata fra Innkjøpsanalyse-rapporten.
            </p>
        </div>
    );
}
