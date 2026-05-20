"use client";

import { useState, useEffect, useCallback } from "react";
import { TrendingUp, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, Printer, RefreshCw, X, ChevronRight, ArrowLeft, FileSpreadsheet, SlidersHorizontal } from "lucide-react";
import Link from "next/link";
import { API_BASE_URL } from "@/lib/api/client";
import { supabase } from "@/lib/supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const BEARER = "befs-super-secret-key-12345";

/** Samme auth som fetchAPI – nødvendig for blob-nedlasting (kan ikke bruke ren href). */
async function buildAuthHeaders(): Promise<Record<string, string>> {
    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || "befs-super-secret-key-12345";
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    const { data: { session } } = await supabase.auth.getSession();
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

function fmt(n: number | null | undefined, decimals = 0): string {
    if (n == null) return "—";
    if (Math.abs(n) >= 1_000_000)
        return (n / 1_000_000).toFixed(1).replace(".", ",") + " M";
    if (Math.abs(n) >= 1_000)
        return (n / 1_000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " k";
    return n.toFixed(decimals).replace(".", ",");
}

function fmtPst(n: number | null | undefined): string {
    if (n == null) return "—";
    return (n > 0 ? "+" : "") + n.toFixed(1).replace(".", ",") + " %";
}

function endringColor(pst: number | null | undefined): string {
    if (pst == null) return "";
    if (pst > 30) return "text-red-600";
    if (pst > 15) return "text-yellow-600";
    return "text-green-600";
}

// ── Interfaces ──────────────────────────────────────────────────────────────

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

interface KontoRow {
    konto: string | null;
    konto_navn: string | null;
    belop: number;
    antall_transaksjoner: number;
}

interface TransaksjonRow {
    transaction_id: string;
    supplier_name: string | null;
    description: string | null;
    invoice_number: string | null;
    amount: number;
    transaction_date: string | null;
    period: string | null;
}

interface Sanity {
    ok: boolean;
    advarsler: string[];
    eiendommer_uten_prediksjon: number;
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
}

interface PropertyDetail {
    property_id: string;
    name: string;
    region: string;
    historikk: Record<string, number>;
    prediksjon_2027: number;
    per_kategori: KategoriRow[];
}

type DrawerState =
    | { type: "region"; region: string }
    | { type: "kategori"; kategori: string }
    | { type: "eiendom"; property_id: string; name: string }
    | { type: "konto"; property_id: string; property_name: string; srs_kategori: string; year: number }
    | null;

interface BacktestYearResult {
    overall: { mape: number | null; predicted: number; actual: number; endring_pst: number | null; n_properties: number };
    per_category: Record<string, { mape: number | null; mae: number; predicted: number; actual: number; n_properties: number; endring_pst: number | null }>;
}

interface BacktestData {
    test_years: number[];
    parameters: Record<string, number>;
    results: Record<string, BacktestYearResult>;
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function PredPage() {
    const [data, setData] = useState<PredData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [metodOpen, setMetodOpen] = useState(false);
    const [backtestOpen, setBacktestOpen] = useState(false);
    const [backtest, setBacktest] = useState<BacktestData | null>(null);
    const [backtestLoading, setBacktestLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [generatingSalary, setGeneratingSalary] = useState(false);
    const [drawer, setDrawer] = useState<DrawerState>(null);
    const [downloadingExcel, setDownloadingExcel] = useState(false);
    const [downloadErr, setDownloadErr] = useState<string | null>(null);
    const [simOpen, setSimOpen] = useState(false);
    const [globalAdj, setGlobalAdj] = useState(0); // prosent, brukes som fallback for alle kategorier
    const [katAdj, setKatAdj] = useState<Record<string, number>>({}); // per-kategori %-override

    async function downloadPrediksjonExcel() {
        if (!API_BASE_URL) {
            setDownloadErr("NEXT_PUBLIC_API_URL er ikke satt.");
            return;
        }
        setDownloadErr(null);
        setDownloadingExcel(true);
        try {
            const url = `${API_BASE_URL}/financials/prediksjon-2027/export.xlsx?scenario=xgb70`;
            await downloadBlob(url, "prediksjon_2027_export.xlsx");
        } catch (e: unknown) {
            setDownloadErr(e instanceof Error ? e.message : String(e));
        } finally {
            setDownloadingExcel(false);
        }
    }

    async function load() {
        setLoading(true);
        setError(null);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(`${API_BASE}/api/v1/financials/prediksjon-2027`, { headers });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            setData(await res.json());
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function generate() {
        setGenerating(true);
        try {
            const headers = await buildAuthHeaders();
            await fetch(`${API_BASE}/api/v1/financials/predict-budget`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ year: 2027 }),
            });
            await load();
        } catch {
            await load();
        } finally {
            setGenerating(false);
        }
    }

    async function generateSalary() {
        setGeneratingSalary(true);
        try {
            const headers = await buildAuthHeaders();
            await fetch(`${API_BASE}/api/v1/financials/salary-costs/predict?year=2027`, {
                method: "POST",
                headers,
            });
            // Wait ~15s for background task, then reload
            await new Promise((r) => setTimeout(r, 15000));
            await load();
        } catch {
            await load();
        } finally {
            setGeneratingSalary(false);
        }
    }

    useEffect(() => { load(); }, []);

    async function loadBacktest() {
        setBacktestLoading(true);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(`${API_BASE}/api/v1/financials/backtest`, { headers });
            if (res.ok) setBacktest(await res.json());
        } finally {
            setBacktestLoading(false);
        }
    }

    // Close drawer on Escape
    useEffect(() => {
        function onKey(e: KeyboardEvent) { if (e.key === "Escape") setDrawer(null); }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    if (loading) return (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
            Laster prediksjon 2027…
        </div>
    );

    if (error) return (
        <div className="p-6">
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
                <strong>Feil ved lasting av prediksjon:</strong> {error}
                {error.includes("403") && (
                    <p className="mt-1 text-red-600">Du har ikke tilgang til denne siden. Kontakt administrator.</p>
                )}
                {error.includes("404") && (
                    <p className="mt-1 text-muted-foreground">Prediksjon ikke generert ennå. Klikk &quot;Generer prediksjon&quot; for å starte.</p>
                )}
            </div>
        </div>
    );

    if (!data) return null;

    const { generert, antall_eiendommer, total_2027, total_2025_gl, endring_pst, per_region, per_eiendom_topp20, per_kategori, sanity, lonn_2027, lonn_2025, lonn_generert, lonn_endring_pst } = data;

    const simPerKat = per_kategori.map(k => {
        const adj = katAdj[k.kategori] ?? globalAdj;
        return { ...k, belop_sim: k.belop_2027 * (1 + adj / 100) };
    });
    const simTotal = simPerKat.reduce((s, k) => s + k.belop_sim, 0);
    const simDelta = simTotal - total_2027;

    return (
        <>
        <div className="p-6 max-w-7xl mx-auto space-y-6 print:p-2">

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <TrendingUp className="text-blue-600" size={24} />
                        Budsjettprediksjon 2027 — Holt-Winters
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        α = 0,70 (vekting nyere år) · β = 0,30 (trendglattning) · Inflasjonsfallback = 3,5 %
                        · Historikk 2021–2025
                    </p>
                </div>
                <div className="flex gap-2 print:hidden">
                    <button
                        onClick={() => window.print()}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-muted transition-colors"
                    >
                        <Printer size={15} /> Skriv ut
                    </button>
                    <button
                        onClick={load}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-muted transition-colors"
                    >
                        <RefreshCw size={15} /> Oppdater
                    </button>
                    <button
                        type="button"
                        onClick={() => void downloadPrediksjonExcel()}
                        disabled={downloadingExcel}
                        title="Excel: Sammendrag, Alle eiendommer, Forklaring, pluss drill-ark. Lokal viewer-pakke: ZIP BEFS-Prediksjon2027-Excel.zip (tools/). API: …/prediksjon-2027/export.xlsx?scenario=xgb70"
                        className="flex items-center gap-1 px-3 py-1.5 text-sm border border-emerald-600/40 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/40 disabled:opacity-50 transition-colors"
                    >
                        <FileSpreadsheet size={15} />
                        {downloadingExcel ? "Laster…" : "Last ned Excel"}
                    </button>
                    <Link
                        href="/financials/prediksjon/budsjett"
                        className="flex items-center gap-1 px-3 py-1.5 text-sm border border-amber-500/40 bg-amber-50 dark:bg-amber-950/30 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/40 transition-colors"
                    >
                        <SlidersHorizontal size={15} />
                        Juster budsjett
                    </Link>
                    <button
                        onClick={generate}
                        disabled={generating}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {generating ? "Genererer…" : "Generer prediksjoner"}
                    </button>
                    <button
                        onClick={generateSalary}
                        disabled={generatingSalary}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 transition-colors"
                    >
                        {generatingSalary ? "Genererer lønn…" : "Generer lønnsprediksjon"}
                    </button>
                </div>
            </div>
            {downloadErr && (
                <p className="text-sm text-red-600 print:hidden" role="alert">
                    Nedlasting: {downloadErr}
                </p>
            )}

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 dark:bg-amber-950/25 px-4 py-3 text-sm print:border print:bg-muted/20">
                <p className="text-xs font-semibold uppercase tracking-wide text-amber-900 dark:text-amber-100 mb-2">
                    Viktig — les før du tolker prosenter og kolonner
                </p>
                <ul className="space-y-1.5 list-disc pl-4 text-foreground/90">
                    <li>
                        <strong>70 %</strong> og <strong>50 %</strong> i Excel er{" "}
                        <strong>XGBoost-gulv-scenarier</strong> (strenghet på nedre grense mot maskinlæringsprediksjon etter Holt-Winters),{" "}
                        ikke «prosent forbruk», aktivitet eller Holt-Winters α.
                    </li>
                    <li>
                        <strong>2025 (GL)</strong> er faktisk regnskapsgrunnlag; <strong>2027 (pred.)</strong> er modellert — ikke samme definisjon som et rent år-over-år GL-sammenligning.
                    </li>
                    <li>
                        Nedlastet Excel bruker som standard scenario <span className="font-mono">xgb70</span>. Eiendommer uten prediksjon påvirker totaler og Excel-rader ulikt; se sanity-varslene under.
                    </li>
                </ul>
            </div>

            {/* KPI-kort */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KpiCard label="Total 2027 (pred.)" value={fmt(total_2027)} sub="NOK" color="blue" />
                <KpiCard label="2025 faktisk (GL)" value={fmt(total_2025_gl)} sub="NOK" color="gray" />
                <KpiCard
                    label="Endring 2025 → 2027"
                    value={fmtPst(endring_pst)}
                    sub="estimert vekst"
                    color={endring_pst != null && endring_pst > 10 ? "red" : "green"}
                />
                <KpiCard
                    label="Eiendommer med pred."
                    value={generert ? antall_eiendommer.toString() : "Ikke generert"}
                    sub={generert ? "av totalt" : "Klikk 'Generer'"}
                    color={generert ? "green" : "red"}
                />
            </div>

            {/* Lønn KPI-kort */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg border border-rose-200 bg-rose-50 dark:bg-rose-950/20 p-4">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Lønn 2027 (pred.)</div>
                    <div className="text-2xl font-bold text-rose-600">
                        {lonn_generert ? fmt(lonn_2027) : "Ikke generert"}
                    </div>
                    {lonn_generert && (
                        <div className="text-xs text-muted-foreground mt-1">
                            fra {fmt(lonn_2025)} i 2025
                            {lonn_endring_pst !== null && (
                                <span className={`ml-1 ${lonn_endring_pst >= 0 ? "text-green-600" : "text-red-600"}`}>
                                    {lonn_endring_pst >= 0 ? "+" : ""}{lonn_endring_pst.toFixed(1).replace(".", ",")} %
                                </span>
                            )}
                        </div>
                    )}
                    {!lonn_generert && (
                        <div className="text-xs text-muted-foreground mt-1">
                            Klikk &apos;Generer lønnsprediksjon&apos; for å beregne
                        </div>
                    )}
                </div>
                <div className="rounded-lg border border-rose-200 bg-rose-50/50 dark:bg-rose-950/10 p-4">
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Lønn 2025 (faktisk)</div>
                    <div className="text-2xl font-bold text-rose-500">
                        {lonn_2025 > 0 ? fmt(lonn_2025) : "—"}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                        Grunnlag for Holt-Winters lønnsprediksjon · α = 0,70 · inflasjon 4,5 %
                    </div>
                </div>
            </div>

            {/* Sanity-panel */}
            <div className={`rounded-lg border p-4 ${sanity.ok ? "border-green-300 bg-green-50" : "border-yellow-300 bg-yellow-50"}`}>
                <div className="flex items-center gap-2 font-medium">
                    {sanity.ok
                        ? <><CheckCircle size={18} className="text-green-600" /> Alle prediksjoner ser rimelige ut</>
                        : <><AlertTriangle size={18} className="text-yellow-600" /> Kvalitetsadvarsler</>
                    }
                </div>
                {sanity.advarsler.length > 0 && (
                    <ul className="mt-2 space-y-1 text-sm">
                        {sanity.advarsler.map((a, i) => (
                            <li key={i} className="flex items-start gap-1">
                                <span className="text-yellow-600 mt-0.5">⚠</span> {a}
                            </li>
                        ))}
                    </ul>
                )}
                {sanity.eiendommer_uten_prediksjon > 0 && (
                    <p className="mt-1 text-sm text-yellow-700">
                        {sanity.eiendommer_uten_prediksjon} eiendommer har GL-data for 2025 men mangler 2027-prediksjon.
                    </p>
                )}
                {sanity.ok && sanity.eiendommer_uten_prediksjon === 0 && (
                    <p className="mt-1 text-sm text-green-700">Alle eiendommer er dekket.</p>
                )}
            </div>

            {/* Per kategori */}
            <section>
                <h2 className="font-semibold mb-3">Fordeling per SRS-kategori
                    <span className="ml-2 text-xs font-normal text-muted-foreground">— klikk for detaljer</span>
                </h2>
                <div className="overflow-x-auto rounded-lg border">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-4 py-2 text-left">Kategori</th>
                                <th className="px-4 py-2 text-right">2025 (GL)</th>
                                <th className="px-4 py-2 text-right">2027 (pred.)</th>
                                <th className="px-4 py-2 text-right">Endring %</th>
                                <th className="px-4 py-2 w-8"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {per_kategori.map((k) => (
                                <tr
                                    key={k.kategori}
                                    className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                    onClick={() => setDrawer({ type: "kategori", kategori: k.kategori })}
                                >
                                    <td className="px-4 py-2 font-medium">{k.kategori}</td>
                                    <td className="px-4 py-2 text-right tabular-nums">{fmt(k.belop_2025)}</td>
                                    <td className="px-4 py-2 text-right tabular-nums font-semibold">{fmt(k.belop_2027)}</td>
                                    <td className={`px-4 py-2 text-right tabular-nums ${endringColor(k.endring_pst)}`}>
                                        {fmtPst(k.endring_pst)}
                                    </td>
                                    <td className="px-4 py-2 text-muted-foreground"><ChevronRight size={14} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Region-tabell */}
            <section>
                <h2 className="font-semibold mb-3">Per region
                    <span className="ml-2 text-xs font-normal text-muted-foreground">— klikk for eiendommer</span>
                </h2>
                <div className="overflow-x-auto rounded-lg border">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-4 py-2 text-left">Region</th>
                                <th className="px-4 py-2 text-right">2025 (GL)</th>
                                <th className="px-4 py-2 text-right">2027 (pred.)</th>
                                <th className="px-4 py-2 text-right">Endring %</th>
                                <th className="px-4 py-2 w-8"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {per_region.map((r) => (
                                <tr
                                    key={r.region}
                                    className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                    onClick={() => setDrawer({ type: "region", region: r.region })}
                                >
                                    <td className="px-4 py-2 font-medium">{r.region}</td>
                                    <td className="px-4 py-2 text-right tabular-nums">{fmt(r.belop_2025)}</td>
                                    <td className="px-4 py-2 text-right tabular-nums font-semibold">{fmt(r.belop_2027)}</td>
                                    <td className={`px-4 py-2 text-right tabular-nums ${endringColor(r.endring_pst)}`}>
                                        {fmtPst(r.endring_pst)}
                                    </td>
                                    <td className="px-4 py-2 text-muted-foreground"><ChevronRight size={14} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* Topp 20 eiendommer */}
            <section>
                <h2 className="font-semibold mb-3">Topp 20 eiendommer etter 2027-budsjett
                    <span className="ml-2 text-xs font-normal text-muted-foreground">— klikk for detaljer</span>
                </h2>
                <div className="overflow-x-auto rounded-lg border">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-4 py-2 text-left">#</th>
                                <th className="px-4 py-2 text-left">Eiendom</th>
                                <th className="px-4 py-2 text-left">Region</th>
                                <th className="px-4 py-2 text-right">2025 (GL)</th>
                                <th className="px-4 py-2 text-right">2027 (pred.)</th>
                                <th className="px-4 py-2 text-right">Endring %</th>
                                <th className="px-4 py-2 w-8"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {per_eiendom_topp20.map((e, i) => (
                                <tr
                                    key={e.property_id}
                                    className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                    onClick={() => setDrawer({ type: "eiendom", property_id: e.property_id, name: e.name })}
                                >
                                    <td className="px-4 py-2 text-muted-foreground">{i + 1}</td>
                                    <td className="px-4 py-2 font-medium max-w-xs truncate" title={e.name}>{e.name}</td>
                                    <td className="px-4 py-2 text-muted-foreground">{e.region}</td>
                                    <td className="px-4 py-2 text-right tabular-nums">{fmt(e.belop_2025)}</td>
                                    <td className="px-4 py-2 text-right tabular-nums font-semibold">{fmt(e.belop_2027)}</td>
                                    <td className={`px-4 py-2 text-right tabular-nums ${endringColor(e.endring_pst)}`}>
                                        {fmtPst(e.endring_pst)}
                                    </td>
                                    <td className="px-4 py-2 text-muted-foreground"><ChevronRight size={14} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* ── Scenario-simulator ── */}
            <section className="border rounded-lg print:hidden">
                <button
                    onClick={() => setSimOpen(!simOpen)}
                    className="w-full flex items-center justify-between px-4 py-3 font-medium hover:bg-muted/30 transition-colors"
                >
                    <span className="flex items-center gap-2">
                        <SlidersHorizontal size={16} className="text-blue-600" />
                        Scenario-simulator — justér og sammenlign med modell
                    </span>
                    {simOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {simOpen && (
                    <div className="border-t px-4 pb-5 pt-4 space-y-4">
                        <p className="text-xs text-muted-foreground">
                            Justér prediksjonene for å lage et samstemt budsjettforslag.
                            Global slider endrer alle kategorier likt. Skriv inn % per kategori for finere kontroll.
                        </p>

                        {/* Global slider */}
                        <div className="max-w-md">
                            <label className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                                Global justering: {globalAdj >= 0 ? "+" : ""}{globalAdj.toFixed(1)} %
                            </label>
                            <input
                                type="range"
                                min={-30}
                                max={40}
                                step={0.5}
                                value={globalAdj}
                                onChange={(e) => setGlobalAdj(parseFloat(e.target.value))}
                                aria-label="Global justering for scenario-simulator"
                                title="Global justering for scenario-simulator"
                                className="w-full h-2 mt-1 accent-blue-600"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-0.5">
                                <span>-30 %</span><span>0 %</span><span>+40 %</span>
                            </div>
                        </div>

                        {/* Per kategori-tabell */}
                        <div className="overflow-x-auto rounded-lg border">
                            <table className="w-full text-sm">
                                <thead className="bg-muted/50">
                                    <tr>
                                        <th className="px-4 py-2 text-left">Kategori</th>
                                        <th className="px-4 py-2 text-right">2025 (GL)</th>
                                        <th className="px-4 py-2 text-right">2027 modell</th>
                                        <th className="px-4 py-2 text-center w-28">Justér (%)</th>
                                        <th className="px-4 py-2 text-right">2027 justert</th>
                                        <th className="px-4 py-2 text-right">Delta</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {simPerKat.map(k => {
                                        const adjVal = katAdj[k.kategori] ?? globalAdj;
                                        const delta = k.belop_sim - k.belop_2027;
                                        return (
                                            <tr key={k.kategori} className="border-t hover:bg-muted/10">
                                                <td className="px-4 py-2 font-medium">{k.kategori}</td>
                                                <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmt(k.belop_2025)}</td>
                                                <td className="px-4 py-2 text-right tabular-nums">{fmt(k.belop_2027)}</td>
                                                <td className="px-4 py-2 text-center">
                                                    <input
                                                        type="number"
                                                        step={0.5}
                                                        value={adjVal}
                                                        onChange={(e) => {
                                                            const v = parseFloat(e.target.value);
                                                            setKatAdj(prev => ({ ...prev, [k.kategori]: isNaN(v) ? 0 : v }));
                                                        }}
                                                        aria-label={`Juster prosent for ${k.kategori}`}
                                                        title={`Juster prosent for ${k.kategori}`}
                                                        className="w-20 text-center border rounded px-2 py-1 text-xs bg-background focus:ring-1 focus:ring-blue-400 outline-none"
                                                    />
                                                </td>
                                                <td className="px-4 py-2 text-right tabular-nums font-semibold text-blue-700">{fmt(k.belop_sim)}</td>
                                                <td className={`px-4 py-2 text-right tabular-nums text-xs ${delta > 0 ? "text-red-600" : delta < 0 ? "text-green-600" : "text-muted-foreground"}`}>
                                                    {delta !== 0 ? (delta > 0 ? "+" : "") + fmt(delta) : "—"}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                    {/* Eiendom total */}
                                    <tr className="border-t bg-muted/20 font-semibold text-sm">
                                        <td className="px-4 py-2">Sum eiendom</td>
                                        <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmt(total_2025_gl)}</td>
                                        <td className="px-4 py-2 text-right tabular-nums">{fmt(total_2027)}</td>
                                        <td />
                                        <td className="px-4 py-2 text-right tabular-nums text-blue-700">{fmt(simTotal)}</td>
                                        <td className={`px-4 py-2 text-right tabular-nums text-xs ${simDelta > 0 ? "text-red-600" : "text-green-600"}`}>
                                            {simDelta > 0 ? "+" : ""}{fmt(simDelta)}
                                        </td>
                                    </tr>
                                    {/* Lønn */}
                                    {lonn_generert && (
                                        <tr className="border-t text-sm">
                                            <td className="px-4 py-2 text-muted-foreground italic">+ Lønn (pred.)</td>
                                            <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">{fmt(lonn_2025)}</td>
                                            <td className="px-4 py-2 text-right tabular-nums">{fmt(lonn_2027)}</td>
                                            <td className="px-4 py-2 text-center text-xs text-muted-foreground">ikke justert</td>
                                            <td className="px-4 py-2 text-right tabular-nums">{fmt(lonn_2027)}</td>
                                            <td />
                                        </tr>
                                    )}
                                    {/* Samlet */}
                                    {lonn_generert && (
                                        <tr className="border-t bg-blue-50/60 dark:bg-blue-950/30 font-bold text-sm">
                                            <td className="px-4 py-2 text-blue-800 dark:text-blue-200">Samlet budsjett 2027</td>
                                            <td className="px-4 py-2 text-right tabular-nums">{fmt(total_2025_gl + lonn_2025)}</td>
                                            <td className="px-4 py-2 text-right tabular-nums">{fmt(total_2027 + lonn_2027)}</td>
                                            <td />
                                            <td className="px-4 py-2 text-right tabular-nums text-blue-700">{fmt(simTotal + lonn_2027)}</td>
                                            <td className={`px-4 py-2 text-right tabular-nums text-xs ${simDelta > 0 ? "text-red-600" : "text-green-600"}`}>
                                                {simDelta > 0 ? "+" : ""}{fmt(simDelta)}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        <div className="flex items-center gap-3 flex-wrap">
                            <button
                                onClick={() => { setGlobalAdj(0); setKatAdj({}); }}
                                className="px-3 py-1.5 text-xs border rounded hover:bg-muted/30 transition-colors"
                            >
                                Nullstill justeringer
                            </button>
                            <span className="text-xs text-muted-foreground">
                                Tallene lagres kun i nettleseren — ingen endringer sendes til databasen.
                            </span>
                        </div>
                    </div>
                )}
            </section>

            {/* Backtesting og uteliggere */}
            <section className="border rounded-lg">
                <button
                    onClick={() => { setBacktestOpen(!backtestOpen); if (!backtest && !backtestLoading) loadBacktest(); }}
                    className="w-full flex items-center justify-between px-4 py-3 font-medium hover:bg-muted/30 transition-colors"
                >
                    <span className="flex items-center gap-2">
                        <AlertTriangle size={16} className="text-amber-500" />
                        Backtesting og uteliggere — modellkvalitet og kjente dataproblem
                    </span>
                    {backtestOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {backtestOpen && (
                    <div className="border-t px-4 pb-5 pt-4 space-y-5">

                        {/* Konto 6300 uteligger-boks */}
                        <div className="rounded-lg border border-red-300 bg-red-50 dark:bg-red-950/20 p-4">
                            <div className="flex items-start gap-2 mb-3">
                                <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
                                <div>
                                    <p className="font-semibold text-red-800 dark:text-red-300 text-sm">
                                        Kjent dataavvik: Konto 6300 «Leie lokaler» i 2024
                                    </p>
                                    <p className="text-xs text-red-700 dark:text-red-400 mt-0.5">
                                        Bilag 800285205 · Oktober 2024 · Tekst: «Husl. Q4 feilfakturert»
                                    </p>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="text-muted-foreground border-b">
                                            <th className="text-left pb-1">År</th>
                                            {[2021,2022,2023,2024,2025].map(y => (
                                                <th key={y} className={`text-right pb-1 px-2 ${y === 2024 ? "text-red-700 font-bold" : ""}`}>{y}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td className="py-1 text-muted-foreground">6300 Leie lokaler (NOK)</td>
                                            {[116_986_270, 146_922_170, 173_607_921, 1_328_878_123, 280_799_862].map((v, i) => (
                                                <td key={i} className={`text-right px-2 py-1 tabular-nums ${i === 3 ? "text-red-700 font-bold bg-red-100 dark:bg-red-900/30 rounded" : ""}`}>
                                                    {(v / 1_000_000).toFixed(0)} M
                                                </td>
                                            ))}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <p className="text-xs text-red-700 dark:text-red-400 mt-3">
                                Én enkelt feilfakturering på <strong>1 145 MNOK</strong> i oktober 2024 forstyrret
                                hele 2024-tallgrunnlaget. Modellen bruker nå netto-summering (positiv + negativ) per
                                eiendom/år/kategori slik at reverserte feilfaktureringer nuller seg automatisk ut.
                            </p>
                        </div>

                        {/* Backtesting-resultater */}
                        {backtestLoading && (
                            <p className="text-sm text-muted-foreground animate-pulse">Kjører backtesting…</p>
                        )}
                        {backtest && !backtestLoading && (
                            <div className="space-y-3">
                                <h3 className="font-semibold text-sm">MAPE per testår — ut-av-sample (lavere er bedre)</h3>
                                <p className="text-xs text-muted-foreground">
                                    For hvert testår trenes modellen på historikk t.o.m. året før og predikerer teståret.
                                    Gjennomstrømning ekskludert fra MAPE. Kun eiendommer med ≥ 3 år treningsdata teller.
                                </p>
                                <div className="overflow-x-auto rounded-lg border">
                                    <table className="w-full text-sm">
                                        <thead className="bg-muted/50">
                                            <tr>
                                                <th className="px-3 py-2 text-left">Testår</th>
                                                <th className="px-3 py-2 text-left text-xs text-muted-foreground">Trener på</th>
                                                <th className="px-3 py-2 text-right">Ant. eid.</th>
                                                <th className="px-3 py-2 text-right">Faktisk GL</th>
                                                <th className="px-3 py-2 text-right">Predikert</th>
                                                <th className="px-3 py-2 text-right">MAPE</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {backtest.test_years.map(yr => {
                                                const yd = backtest.results[yr] ?? backtest.results[String(yr)];
                                                if (!yd) return null;
                                                const ov = yd.overall;
                                                const mape = ov.mape;
                                                const mapeColor = mape == null ? "" : mape < 15 ? "bg-green-100 text-green-800" : mape < 30 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800";
                                                return (
                                                    <tr key={yr} className="border-t">
                                                        <td className="px-3 py-2 font-semibold">{yr}</td>
                                                        <td className="px-3 py-2 text-xs text-muted-foreground">2021–{yr - 1}</td>
                                                        <td className="px-3 py-2 text-right tabular-nums">{ov.n_properties}</td>
                                                        <td className="px-3 py-2 text-right tabular-nums">{fmt(ov.actual)}</td>
                                                        <td className="px-3 py-2 text-right tabular-nums">{fmt(ov.predicted)}</td>
                                                        <td className="px-3 py-2 text-right">
                                                            {mape != null
                                                                ? <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${mapeColor}`}>{mape.toFixed(1)} %</span>
                                                                : <span className="text-muted-foreground text-xs">—</span>}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>

                                {/* Per kategori */}
                                <div className="overflow-x-auto rounded-lg border">
                                    <table className="w-full text-sm">
                                        <thead className="bg-muted/50">
                                            <tr>
                                                <th className="px-3 py-2 text-left">Kategori</th>
                                                {backtest.test_years.map(yr => (
                                                    <th key={yr} className="px-3 py-2 text-right">{yr}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Array.from(new Set(backtest.test_years.flatMap(yr => {
                                                const yd = backtest.results[yr] ?? backtest.results[String(yr)];
                                                return yd ? Object.keys(yd.per_category) : [];
                                            }))).sort().map(cat => (
                                                <tr key={cat} className="border-t">
                                                    <td className="px-3 py-2 font-medium">{cat}</td>
                                                    {backtest.test_years.map(yr => {
                                                        const yd = backtest.results[yr] ?? backtest.results[String(yr)];
                                                        const mape = yd?.per_category[cat]?.mape ?? null;
                                                        const mapeColor = mape == null ? "" : mape < 15 ? "bg-green-100 text-green-800" : mape < 30 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800";
                                                        return (
                                                            <td key={yr} className="px-3 py-2 text-right">
                                                                {mape != null
                                                                    ? <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${mapeColor}`}>{mape.toFixed(1)} %</span>
                                                                    : <span className="text-muted-foreground text-xs">—</span>}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Grønn &lt; 15 % · Gul 15–30 % · Rød &gt; 30 % ·
                                    Gjennomstrømning vises ikke (inflasjonspåslag, ikke prediksjon).
                                </p>
                            </div>
                        )}
                        {!backtest && !backtestLoading && (
                            <button
                                onClick={loadBacktest}
                                className="px-3 py-1.5 text-xs border rounded hover:bg-muted/30 transition-colors"
                            >
                                Last backtesting-resultater
                            </button>
                        )}
                    </div>
                )}
            </section>

            {/* Metodebeskrivelse */}
            <section className="border rounded-lg">
                <button
                    onClick={() => setMetodOpen(!metodOpen)}
                    className="w-full flex items-center justify-between px-4 py-3 font-medium hover:bg-muted/30 transition-colors"
                >
                    <span>Metodebeskrivelse — for revisor og regnskapsavdeling</span>
                    {metodOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {metodOpen && (
                    <div className="px-4 pb-4 text-sm space-y-3 text-muted-foreground border-t pt-3">
                        <p>
                            <strong className="text-foreground">Algoritme:</strong> Holt-Winters dobbel eksponentiell glattning
                            (Double Exponential Smoothing) — SES med trendkomponent.
                        </p>
                        <p>
                            <strong className="text-foreground">Parametre:</strong> α = 0,70 (nivå-vekting — nyere år gis mer vekt),
                            β = 0,30 (trend-glattning). Valgt for å vektlegge 2024–2025-kostnadsnivå sterkt.
                        </p>
                        <p>
                            <strong className="text-foreground">Datagrunnlag:</strong> Agresso GL-transaksjoner 2021–2025,
                            gruppert per eiendom (property_id) og SRS-kategori (Drift / Investering / Gjennomstrømning).
                            Netto-summering per eiendom/år/kategori (positiv + negativ) slik at reverserte feilfaktureringer
                            automatisk nuller seg ut. Kun grupper med netto &gt; 0 og kobling til BEFS-eiendom er inkludert.
                        </p>
                        <p>
                            <strong className="text-foreground">Inflasjonsfallback:</strong> 3,5 % for eiendommer med kun
                            1 år GL-historikk (utilstrekkelig for Holt-Winters). Basert på SSB KPI-prognose 2026–2027.
                        </p>
                        <p>
                            <strong className="text-foreground">Output:</strong> 12 månedlige budsjettlinjer per eiendom
                            per kategori lagret i <code>budget</code>-tabellen med
                            <code> is_synthetic=true</code>, <code>data_source=&quot;holt_winters_2027&quot;</code>.
                        </p>
                        <p>
                            <strong className="text-foreground">Begrensninger:</strong> Modellen tar ikke hensyn til
                            nybygg, vesentlige strukturendringer eller politiske vedtak etter 2025.
                            Tallene er estimater — ikke godkjente budsjetttall.
                        </p>
                    </div>
                )}
            </section>
        </div>

        {/* Drill-down Drawer */}
        <DrillDrawer drawer={drawer} setDrawer={setDrawer} />
        </>
    );
}

// ── Drill-down Drawer ─────────────────────────────────────────────────────────

function DrillDrawer({
    drawer,
    setDrawer,
}: {
    drawer: DrawerState;
    setDrawer: (d: DrawerState) => void;
}) {
    const [rows, setRows] = useState<EiendomRow[]>([]);
    const [detail, setDetail] = useState<PropertyDetail | null>(null);
    const [loading, setLoading] = useState(false);
    const [subDrawer, setSubDrawer] = useState<{ property_id: string; name: string } | null>(null);
    const [kontoRows, setKontoRows] = useState<KontoRow[]>([]);
    const [kontoState, setKontoState] = useState<{ property_id: string; property_name: string; srs_kategori: string; year: number } | null>(null);
    const [transaksjonRows, setTransaksjonRows] = useState<TransaksjonRow[]>([]);
    const [transaksjonState, setTransaksjonState] = useState<{ property_id: string; konto: string; konto_navn: string; year: number } | null>(null);

    const fetchRows = useCallback(async (url: string) => {
        setLoading(true);
        setRows([]);
        setDetail(null);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(url, { headers });
            if (res.ok) setRows(await res.json());
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchDetail = useCallback(async (property_id: string) => {
        setLoading(true);
        setDetail(null);
        try {
            const headers = await buildAuthHeaders();
            const res = await fetch(
                `${API_BASE}/api/v1/financials/prediksjon-2027/eiendom/${property_id}`,
                { headers }
            );
            if (res.ok) setDetail(await res.json());
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchKonto = useCallback(async (property_id: string, srs_kategori: string, year: number) => {
        setLoading(true);
        setKontoRows([]);
        try {
            const headers = await buildAuthHeaders();
            const params = new URLSearchParams({ srs_kategori, year: String(year) });
            const res = await fetch(
                `${API_BASE}/api/v1/financials/prediksjon-2027/eiendom/${property_id}/konto?${params}`,
                { headers }
            );
            if (res.ok) setKontoRows(await res.json());
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!drawer) { setRows([]); setDetail(null); setSubDrawer(null); setKontoState(null); setKontoRows([]); setTransaksjonState(null); setTransaksjonRows([]); return; }
        setSubDrawer(null);
        setKontoState(null);
        setKontoRows([]);
        setTransaksjonState(null);
        setTransaksjonRows([]);
        if (drawer.type === "region") {
            fetchRows(`${API_BASE}/api/v1/financials/prediksjon-2027/region/${encodeURIComponent(drawer.region)}`);
        } else if (drawer.type === "kategori") {
            fetchRows(`${API_BASE}/api/v1/financials/prediksjon-2027/kategori/${encodeURIComponent(drawer.kategori)}`);
        } else if (drawer.type === "eiendom") {
            fetchDetail(drawer.property_id);
        }
    }, [drawer, fetchRows, fetchDetail]);

    useEffect(() => {
        if (subDrawer) { setKontoState(null); setKontoRows([]); setTransaksjonState(null); setTransaksjonRows([]); fetchDetail(subDrawer.property_id); }
    }, [subDrawer, fetchDetail]);

    const fetchTransaksjoner = useCallback(async (property_id: string, konto: string, year: number) => {
        setLoading(true);
        setTransaksjonRows([]);
        try {
            const headers = await buildAuthHeaders();
            const params = new URLSearchParams({ property_id, year: String(year), account_code: konto, size: "500" });
            const res = await fetch(
                `${API_BASE}/api/v1/accounting/transactions?${params}`,
                { headers }
            );
            if (res.ok) {
                const data = await res.json();
                setTransaksjonRows(data.items ?? []);
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (kontoState) fetchKonto(kontoState.property_id, kontoState.srs_kategori, kontoState.year);
    }, [kontoState, fetchKonto]);

    useEffect(() => {
        if (transaksjonState) fetchTransaksjoner(transaksjonState.property_id, transaksjonState.konto, transaksjonState.year);
    }, [transaksjonState, fetchTransaksjoner]);

    if (!drawer) return null;

    const title =
        drawer.type === "region" ? `Region: ${drawer.region}` :
        drawer.type === "kategori" ? `Kategori: ${drawer.kategori}` :
        drawer.type === "eiendom" ? drawer.name :
        "";

    return (
        <>
            {/* Dimming */}
            <div
                className="fixed inset-0 bg-black/30 z-40"
                onClick={() => setDrawer(null)}
            />
            {/* Drawer */}
            <div className="fixed inset-y-0 right-0 w-full md:w-[540px] bg-background border-l shadow-xl z-50 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b">
                    <div className="flex items-center gap-2">
                        {(subDrawer || kontoState || transaksjonState) && (
                            <button
                                onClick={() => {
                                    if (transaksjonState) { setTransaksjonState(null); setTransaksjonRows([]); }
                                    else if (kontoState) { setKontoState(null); setKontoRows([]); }
                                    else { setSubDrawer(null); setDetail(null); }
                                }}
                                aria-label="Gå tilbake"
                                title="Gå tilbake"
                                className="p-1 rounded hover:bg-muted transition-colors"
                            >
                                <ArrowLeft size={16} />
                            </button>
                        )}
                        <h2 className="font-semibold text-base truncate max-w-xs">
                            {transaksjonState
                                ? `${transaksjonState.konto_navn || transaksjonState.konto}`
                                : kontoState
                                ? `${kontoState.srs_kategori} — kontodetaljer`
                                : subDrawer
                                ? subDrawer.name
                                : title}
                        </h2>
                    </div>
                    <button
                        onClick={() => setDrawer(null)}
                        aria-label="Lukk panel"
                        title="Lukk panel"
                        className="p-1 rounded hover:bg-muted transition-colors"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-5">
                    {loading && (
                        <p className="text-sm text-muted-foreground">Laster…</p>
                    )}

                    {/* Transaksjon panel (5. nivå) */}
                    {!loading && transaksjonState && (
                        <TransaksjonListPanel rows={transaksjonRows} konto={transaksjonState.konto} />
                    )}

                    {/* Konto panel (4. nivå) */}
                    {!loading && !transaksjonState && kontoState && (
                        <KontoListPanel
                            rows={kontoRows}
                            kategori={kontoState.srs_kategori}
                            onKontoSelect={(r) => setTransaksjonState({
                                property_id: kontoState.property_id,
                                konto: r.konto ?? "",
                                konto_navn: r.konto_navn ?? r.konto ?? "",
                                year: kontoState.year,
                            })}
                        />
                    )}

                    {/* List panel (region / kategori) */}
                    {!loading && !transaksjonState && !kontoState && !subDrawer && (drawer.type === "region" || drawer.type === "kategori") && (
                        <EiendomListPanel
                            rows={rows}
                            onSelect={(row) => setSubDrawer({ property_id: row.property_id, name: row.name })}
                        />
                    )}

                    {/* Property detail panel */}
                    {!loading && !transaksjonState && !kontoState && (subDrawer || drawer.type === "eiendom") && detail && (
                        <PropertyDetailPanel
                            detail={detail}
                            onKategoriSelect={(kat) =>
                                setKontoState({
                                    property_id: subDrawer?.property_id ?? (drawer.type === "eiendom" ? drawer.property_id : ""),
                                    property_name: subDrawer?.name ?? (drawer.type === "eiendom" ? drawer.name : ""),
                                    srs_kategori: kat,
                                    year: 2025,
                                })
                            }
                        />
                    )}
                </div>
            </div>
        </>
    );
}

// ── EiendomListPanel ──────────────────────────────────────────────────────────

function EiendomListPanel({ rows, onSelect }: { rows: EiendomRow[]; onSelect: (r: EiendomRow) => void }) {
    if (rows.length === 0) return <p className="text-sm text-muted-foreground">Ingen eiendommer funnet.</p>;

    return (
        <div className="space-y-1">
            <p className="text-xs text-muted-foreground mb-3">{rows.length} eiendommer — klikk for å se detaljer</p>
            <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-3 py-2 text-left">Eiendom</th>
                            <th className="px-3 py-2 text-right">2025</th>
                            <th className="px-3 py-2 text-right">2027</th>
                            <th className="px-3 py-2 text-right">Δ%</th>
                            <th className="px-3 py-2 w-6"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r) => (
                            <tr
                                key={r.property_id}
                                className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                onClick={() => onSelect(r)}
                            >
                                <td className="px-3 py-2 font-medium max-w-[160px] truncate" title={r.name}>{r.name}</td>
                                <td className="px-3 py-2 text-right tabular-nums text-xs">{fmt(r.belop_2025)}</td>
                                <td className="px-3 py-2 text-right tabular-nums text-xs font-semibold">{fmt(r.belop_2027)}</td>
                                <td className={`px-3 py-2 text-right tabular-nums text-xs ${endringColor(r.endring_pst)}`}>
                                    {fmtPst(r.endring_pst)}
                                </td>
                                <td className="px-3 py-2 text-muted-foreground"><ChevronRight size={13} /></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ── PropertyDetailPanel ───────────────────────────────────────────────────────

function PropertyDetailPanel({ detail, onKategoriSelect }: { detail: PropertyDetail; onKategoriSelect: (kategori: string) => void }) {
    const hist = detail.historikk;
    const years = ["2021", "2022", "2023", "2024", "2025"];
    const gl2025 = hist["2025"] ?? 0;
    const endring = gl2025 > 0 ? ((detail.prediksjon_2027 - gl2025) / gl2025 * 100) : null;

    return (
        <div className="space-y-5">
            {/* KPI-kort */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="rounded-lg border p-3 bg-gray-50">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">GL 2025</p>
                    <p className="text-lg font-bold mt-0.5">{fmt(gl2025)}</p>
                </div>
                <div className="rounded-lg border p-3 bg-blue-50 border-blue-200">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Pred. 2027</p>
                    <p className="text-lg font-bold mt-0.5">{fmt(detail.prediksjon_2027)}</p>
                </div>
                <div className={`rounded-lg border p-3 ${endring != null && endring > 30 ? "bg-red-50 border-red-200" : endring != null && endring > 15 ? "bg-yellow-50 border-yellow-200" : "bg-green-50 border-green-200"}`}>
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">Endring</p>
                    <p className={`text-lg font-bold mt-0.5 ${endringColor(endring)}`}>{fmtPst(endring)}</p>
                </div>
            </div>

            {/* Historikk + prediksjon */}
            <div>
                <h3 className="text-sm font-semibold mb-2">Historikk 2021–2025 + Prediksjon 2027</h3>
                <div className="rounded-lg border overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-3 py-2 text-left">År</th>
                                <th className="px-3 py-2 text-right">Beløp (GL/pred.)</th>
                                <th className="px-3 py-2 text-right">Endring YoY</th>
                            </tr>
                        </thead>
                        <tbody>
                            {years.map((yr, i) => {
                                const val = hist[yr] ?? null;
                                const prev = i > 0 ? (hist[years[i - 1]] ?? null) : null;
                                const yoy = val != null && prev != null && prev > 0
                                    ? ((val - prev) / prev * 100)
                                    : null;
                                return (
                                    <tr key={yr} className="border-t">
                                        <td className="px-3 py-2 text-muted-foreground">{yr}</td>
                                        <td className="px-3 py-2 text-right tabular-nums font-medium">{val != null ? fmt(val) : "—"}</td>
                                        <td className={`px-3 py-2 text-right tabular-nums text-xs ${endringColor(yoy)}`}>{fmtPst(yoy)}</td>
                                    </tr>
                                );
                            })}
                            {/* 2027 prediksjon */}
                            <tr className="border-t bg-blue-50/50">
                                <td className="px-3 py-2 font-semibold text-blue-700">2027 ✦</td>
                                <td className="px-3 py-2 text-right tabular-nums font-bold text-blue-700">{fmt(detail.prediksjon_2027)}</td>
                                <td className={`px-3 py-2 text-right tabular-nums text-xs font-semibold ${endringColor(endring)}`}>{fmtPst(endring)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p className="text-xs text-muted-foreground mt-1">✦ Prediksjon (Holt-Winters) — ikke faktisk regnskap</p>
            </div>

            {/* Per kategori */}
            {detail.per_kategori.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold mb-2">Per SRS-kategori
                        <span className="ml-2 text-xs font-normal text-muted-foreground">— klikk for kontodetaljer</span>
                    </h3>
                    <div className="rounded-lg border overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-muted/50">
                                <tr>
                                    <th className="px-3 py-2 text-left">Kategori</th>
                                    <th className="px-3 py-2 text-right">2025 (GL)</th>
                                    <th className="px-3 py-2 text-right">2027 (pred.)</th>
                                    <th className="px-3 py-2 text-right">Δ%</th>
                                    <th className="px-3 py-2 w-6"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {detail.per_kategori.map((k) => (
                                    <tr
                                        key={k.kategori}
                                        className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                        onClick={() => onKategoriSelect(k.kategori)}
                                    >
                                        <td className="px-3 py-2 text-muted-foreground">{k.kategori}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">{fmt(k.belop_2025)}</td>
                                        <td className="px-3 py-2 text-right tabular-nums font-medium">{fmt(k.belop_2027)}</td>
                                        <td className={`px-3 py-2 text-right tabular-nums text-xs ${endringColor(k.endring_pst)}`}>{fmtPst(k.endring_pst)}</td>
                                        <td className="px-3 py-2 text-muted-foreground"><ChevronRight size={13} /></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── KontoListPanel ────────────────────────────────────────────────────────────

function KontoListPanel({ rows, kategori, onKontoSelect }: { rows: KontoRow[]; kategori: string; onKontoSelect: (r: KontoRow) => void }) {
    if (rows.length === 0)
        return <p className="text-sm text-muted-foreground">Ingen kontolinjer funnet for {kategori}.</p>;

    const total = rows.reduce((s, r) => s + r.belop, 0);

    return (
        <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
                {rows.length} kontoer · Total: {fmt(total)}
            </p>
            <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-3 py-2 text-left">Konto</th>
                            <th className="px-3 py-2 text-left">Navn</th>
                            <th className="px-3 py-2 text-right">Beløp 2025</th>
                            <th className="px-3 py-2 text-right">Ant.</th>
                            <th className="px-3 py-2 w-6"></th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r, i) => (
                            <tr
                                key={r.konto ?? i}
                                className="border-t hover:bg-muted/30 cursor-pointer transition-colors"
                                onClick={() => onKontoSelect(r)}
                            >
                                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{r.konto ?? "—"}</td>
                                <td className="px-3 py-2 max-w-[140px] truncate" title={r.konto_navn ?? ""}>{r.konto_navn ?? "—"}</td>
                                <td className="px-3 py-2 text-right tabular-nums font-medium">{fmt(r.belop)}</td>
                                <td className="px-3 py-2 text-right tabular-nums text-xs text-muted-foreground">{r.antall_transaksjoner}</td>
                                <td className="px-3 py-2 text-muted-foreground"><ChevronRight size={13} /></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <p className="text-xs text-muted-foreground">— klikk konto for å se enkeltbilag</p>
        </div>
    );
}

// ── TransaksjonListPanel ───────────────────────────────────────────────────────

function TransaksjonListPanel({ rows, konto }: { rows: TransaksjonRow[]; konto: string }) {
    if (rows.length === 0)
        return <p className="text-sm text-muted-foreground">Ingen transaksjoner funnet for konto {konto}.</p>;

    const total = rows.reduce((s, r) => s + r.amount, 0);

    return (
        <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
                {rows.length} bilag · Total: {fmt(total)}
            </p>
            <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-3 py-2 text-left">Dato</th>
                            <th className="px-3 py-2 text-left">Leverandør</th>
                            <th className="px-3 py-2 text-left">Tekst</th>
                            <th className="px-3 py-2 text-right">Beløp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r) => (
                            <tr key={r.transaction_id} className="border-t">
                                <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
                                    {r.transaction_date ? r.transaction_date.slice(0, 10) : (r.period ?? "—")}
                                </td>
                                <td className="px-3 py-2 max-w-[120px] truncate text-xs" title={r.supplier_name ?? ""}>{r.supplier_name ?? "—"}</td>
                                <td className="px-3 py-2 max-w-[130px] truncate text-xs text-muted-foreground" title={r.description ?? ""}>{r.description ?? r.invoice_number ?? "—"}</td>
                                <td className="px-3 py-2 text-right tabular-nums font-medium">{fmt(r.amount)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// ── KpiCard ───────────────────────────────────────────────────────────────────

function KpiCard({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
    const colors: Record<string, string> = {
        blue: "border-blue-200 bg-blue-50",
        green: "border-green-200 bg-green-50",
        red: "border-red-200 bg-red-50",
        gray: "border-gray-200 bg-gray-50",
    };
    return (
        <div className={`rounded-lg border p-4 ${colors[color] || colors.gray}`}>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>
        </div>
    );
}
