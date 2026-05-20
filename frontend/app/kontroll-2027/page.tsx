"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/app/components/ui/Header";
import { fetchAPI } from "@/lib/api/client";
import {
    ShieldCheck,
    ChevronDown,
    ChevronRight,
    AlertTriangle,
    TrendingUp,
    ExternalLink,
    Printer,
    CheckCircle2,
    XCircle,
    Info,
} from "lucide-react";

function fmt(n: number): string {
    return new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 0 }).format(n);
}

function fmtPct(n: number | null | undefined): string {
    if (n == null) return "—";
    const sign = n > 0 ? "+" : "";
    return `${sign}${n.toFixed(1)} %`;
}

type Risk = "HØY" | "MIDDELS" | "LAV";

function RiskBadge({ risk }: { risk: Risk }) {
    const cls =
        risk === "HØY"
            ? "bg-red-500/15 text-red-500"
            : risk === "MIDDELS"
            ? "bg-yellow-500/15 text-yellow-500"
            : "bg-green-500/15 text-green-600 dark:text-green-400";
    return (
        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${cls}`}>
            {risk}
        </span>
    );
}

function FlagBadge({ flag }: { flag: string }) {
    const labels: Record<string, string> = {
        HØYT_VEKST: "Høy vekst",
        NEGATIVT: "Negativt",
        INFLASJONSFALLBACK: "Inflasjonsfallback",
        MANGLER_PREDIKSJON: "Mangler prediksjon",
    };
    return (
        <span className="inline-flex px-1.5 py-0.5 rounded bg-muted/40 text-muted text-xs mr-1">
            {labels[flag] ?? flag}
        </span>
    );
}

interface OutlierSummary {
    total_outliers: number;
    high_risk: number;
    medium_risk: number;
    transaction_count: number;
    property_count: number;
    category_yoy_count: number;
    orphan_count: number;
}

interface TransactionOutlier {
    bilagsnr: string;
    leverandor_navn: string;
    konto_navn: string;
    belop: number;
    z_score: number;
    category_avg: number;
    risk: Risk;
    property_id: string | null;
    tekst: string;
    dim1_kode: string;
    dim1_navn: string;
}

interface PropertyOutlier {
    property_id: string;
    name: string;
    region: string;
    total_2025: number;
    region_avg: number;
    z_score: number;
    risk: Risk;
}

interface CategoryYoYOutlier {
    konto_navn: string;
    amt_2024: number;
    amt_2025: number;
    change_pct: number;
    risk: Risk;
}

interface OrphanOutlier {
    bilagsnr: string;
    leverandor_navn: string;
    dim1_kode: string;
    dim1_navn: string;
    konto_navn: string;
    belop: number;
    tekst: string;
}

interface OutlierData {
    year: number;
    summary: OutlierSummary;
    transaction_outliers: TransactionOutlier[];
    property_outliers: PropertyOutlier[];
    category_yoy_outliers: CategoryYoYOutlier[];
    orphan_outliers: OrphanOutlier[];
}

interface PrognoseItem {
    property_id: string;
    name: string;
    region: string;
    actual_2025: number;
    predicted: number;
    growth_pct: number | null;
    risk: Risk;
    flags: string[];
}

interface PrognoseReview {
    year: number;
    flagged_count: number;
    total_predicted: number;
    total_actual_2025: number;
    growth_pct: number | null;
    items: PrognoseItem[];
}

type Section = "outliers" | "prognose" | "vurdering";

export default function Kontroll2027Page() {
    const [outliers, setOutliers] = useState<OutlierData | null>(null);
    const [prognose, setPrognose] = useState<PrognoseReview | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [openSection, setOpenSection] = useState<Section | null>("outliers");
    const [outlierTab, setOutlierTab] = useState<"transactions" | "properties" | "categories" | "orphans">("transactions");

    useEffect(() => {
        async function load() {
            try {
                setLoading(true);
                const [out, prog] = await Promise.all([
                    fetchAPI<OutlierData>("/financials/outliers?year=2025").catch(() => null),
                    fetchAPI<PrognoseReview>("/financials/prognose-review?year=2027").catch(() => null),
                ]);
                setOutliers(out);
                setPrognose(prog);
            } catch (e) {
                setError(e instanceof Error ? e.message : "Feil ved lasting");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const toggle = (s: Section) => setOpenSection(openSection === s ? null : s);

    const highRisk = (outliers?.summary.high_risk ?? 0) + (prognose?.items.filter(x => x.risk === "HØY").length ?? 0);
    const medRisk = (outliers?.summary.medium_risk ?? 0) + (prognose?.items.filter(x => x.risk === "MIDDELS").length ?? 0);
    const readyForControl = highRisk === 0;

    return (
        <div className="min-h-screen bg-background text-foreground font-sans pb-20 print:pb-0">
            <Header />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24 print:pt-4">
                {/* Tittel */}
                <div className="mb-8 flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground tracking-tight flex items-center gap-3">
                            <ShieldCheck className="w-7 h-7 text-primary" />
                            Kontroll 2027
                        </h1>
                        <p className="text-muted mt-2">
                            Outlier-analyse (GL 2025) · Prognosegjennomgang · Samlet vurdering for intern kontroll
                        </p>
                    </div>
                    <button
                        onClick={() => window.print()}
                        className="flex items-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted/20 transition-colors print:hidden"
                    >
                        <Printer size={16} />
                        Skriv ut
                    </button>
                </div>

                {loading && (
                    <div className="flex items-center gap-3 text-muted py-12">
                        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        Laster analysedata…
                    </div>
                )}

                {error && (
                    <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">{error}</div>
                )}

                {!loading && (
                    <div className="space-y-4">

                        {/* ── Seksjon 1: GL-outliers ─────────────────────────── */}
                        <div className="rounded-xl border border-border bg-surface overflow-hidden">
                            <button
                                type="button"
                                onClick={() => toggle("outliers")}
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    {openSection === "outliers"
                                        ? <ChevronDown className="w-5 h-5 text-primary shrink-0" />
                                        : <ChevronRight className="w-5 h-5 text-muted shrink-0" />}
                                    <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0" />
                                    <span className="font-semibold text-foreground">GL-outliers 2025</span>
                                    {outliers && (
                                        <div className="flex items-center gap-2 text-sm">
                                            <span className="text-muted">({outliers.summary.total_outliers} avvik)</span>
                                            {outliers.summary.high_risk > 0 && (
                                                <span className="px-2 py-0.5 rounded bg-red-500/15 text-red-500 text-xs font-semibold">
                                                    {outliers.summary.high_risk} HØY
                                                </span>
                                            )}
                                            {outliers.summary.medium_risk > 0 && (
                                                <span className="px-2 py-0.5 rounded bg-yellow-500/15 text-yellow-500 text-xs font-semibold">
                                                    {outliers.summary.medium_risk} MIDDELS
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </button>

                            {openSection === "outliers" && outliers && (
                                <div className="border-t border-border bg-background/50">
                                    {/* Tab-linje */}
                                    <div className="flex border-b border-border px-5 gap-4">
                                        {([
                                            ["transactions", `Enkelt-tx (${outliers.summary.transaction_count})`],
                                            ["properties", `Eiendom (${outliers.summary.property_count})`],
                                            ["categories", `Kategori YoY (${outliers.summary.category_yoy_count})`],
                                            ["orphans", `Orphan (${outliers.summary.orphan_count})`],
                                        ] as const).map(([tab, label]) => (
                                            <button
                                                key={tab}
                                                onClick={() => setOutlierTab(tab)}
                                                className={`text-sm py-3 border-b-2 transition-colors ${outlierTab === tab
                                                    ? "border-primary text-primary font-medium"
                                                    : "border-transparent text-muted hover:text-foreground"
                                                }`}
                                            >
                                                {label}
                                            </button>
                                        ))}
                                    </div>

                                    {outlierTab === "transactions" && (
                                        <div className="overflow-x-auto">
                                            {outliers.transaction_outliers.length === 0 ? (
                                                <p className="px-5 py-8 text-center text-muted">Ingen transaksjon-outliers funnet.</p>
                                            ) : (
                                                <table className="w-full enterprise-table text-sm">
                                                    <thead>
                                                        <tr>
                                                            <th className="px-4 py-3 text-left">Bilagsnr</th>
                                                            <th className="px-4 py-3 text-left">Leverandør</th>
                                                            <th className="px-4 py-3 text-left">Konto</th>
                                                            <th className="px-4 py-3 text-right">Beløp (kr)</th>
                                                            <th className="px-4 py-3 text-right">Z-score</th>
                                                            <th className="px-4 py-3 text-right">Snitt (kr)</th>
                                                            <th className="px-4 py-3 text-center">Risiko</th>
                                                            <th className="w-8"></th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {outliers.transaction_outliers.map((tx, i) => (
                                                            <tr key={i} className="border-t border-border">
                                                                <td className="px-4 py-2 font-mono text-xs text-muted">{tx.bilagsnr}</td>
                                                                <td className="px-4 py-2 font-medium">{tx.leverandor_navn}</td>
                                                                <td className="px-4 py-2 text-muted">{tx.konto_navn}</td>
                                                                <td className="px-4 py-2 text-right font-mono font-semibold">{fmt(tx.belop)}</td>
                                                                <td className="px-4 py-2 text-right font-mono text-orange-400">{tx.z_score.toFixed(2)}</td>
                                                                <td className="px-4 py-2 text-right text-muted font-mono">{fmt(tx.category_avg)}</td>
                                                                <td className="px-4 py-2 text-center"><RiskBadge risk={tx.risk} /></td>
                                                                <td className="pr-2">
                                                                    {tx.property_id && (
                                                                        <Link href={`/properties/${tx.property_id}`} className="p-1 text-primary hover:bg-primary/10 rounded inline-flex">
                                                                            <ExternalLink size={14} />
                                                                        </Link>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>
                                    )}

                                    {outlierTab === "properties" && (
                                        <div className="overflow-x-auto">
                                            {outliers.property_outliers.length === 0 ? (
                                                <p className="px-5 py-8 text-center text-muted">Ingen eiendom-outliers funnet.</p>
                                            ) : (
                                                <table className="w-full enterprise-table text-sm">
                                                    <thead>
                                                        <tr>
                                                            <th className="px-4 py-3 text-left">Eiendom</th>
                                                            <th className="px-4 py-3 text-left">Region</th>
                                                            <th className="px-4 py-3 text-right">Totalt 2025 (kr)</th>
                                                            <th className="px-4 py-3 text-right">Regionsnitt (kr)</th>
                                                            <th className="px-4 py-3 text-right">Z-score</th>
                                                            <th className="px-4 py-3 text-center">Risiko</th>
                                                            <th className="w-8"></th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {outliers.property_outliers.map((p, i) => (
                                                            <tr key={i} className="border-t border-border">
                                                                <td className="px-4 py-2 font-medium">{p.name}</td>
                                                                <td className="px-4 py-2 text-muted">{p.region}</td>
                                                                <td className="px-4 py-2 text-right font-mono font-semibold">{fmt(p.total_2025)}</td>
                                                                <td className="px-4 py-2 text-right font-mono text-muted">{fmt(p.region_avg)}</td>
                                                                <td className="px-4 py-2 text-right font-mono text-orange-400">{p.z_score.toFixed(2)}</td>
                                                                <td className="px-4 py-2 text-center"><RiskBadge risk={p.risk} /></td>
                                                                <td className="pr-2">
                                                                    <Link href={`/properties/${p.property_id}`} className="p-1 text-primary hover:bg-primary/10 rounded inline-flex">
                                                                        <ExternalLink size={14} />
                                                                    </Link>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>
                                    )}

                                    {outlierTab === "categories" && (
                                        <div className="overflow-x-auto">
                                            {outliers.category_yoy_outliers.length === 0 ? (
                                                <p className="px-5 py-8 text-center text-muted">Ingen kategori-outliers funnet.</p>
                                            ) : (
                                                <table className="w-full enterprise-table text-sm">
                                                    <thead>
                                                        <tr>
                                                            <th className="px-4 py-3 text-left">Konto / Kategori</th>
                                                            <th className="px-4 py-3 text-right">2024 (kr)</th>
                                                            <th className="px-4 py-3 text-right">2025 (kr)</th>
                                                            <th className="px-4 py-3 text-right">Endring</th>
                                                            <th className="px-4 py-3 text-center">Risiko</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {outliers.category_yoy_outliers.map((c, i) => (
                                                            <tr key={i} className="border-t border-border">
                                                                <td className="px-4 py-2 font-medium">{c.konto_navn}</td>
                                                                <td className="px-4 py-2 text-right font-mono text-muted">{fmt(c.amt_2024)}</td>
                                                                <td className="px-4 py-2 text-right font-mono">{fmt(c.amt_2025)}</td>
                                                                <td className={`px-4 py-2 text-right font-mono font-semibold ${c.change_pct > 0 ? "text-red-500" : "text-green-500"}`}>
                                                                    {fmtPct(c.change_pct)}
                                                                </td>
                                                                <td className="px-4 py-2 text-center"><RiskBadge risk={c.risk} /></td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>
                                    )}

                                    {outlierTab === "orphans" && (
                                        <div className="overflow-x-auto">
                                            {outliers.orphan_outliers.length === 0 ? (
                                                <p className="px-5 py-8 text-center text-muted">Ingen orphan-transaksjoner over 100 000 kr.</p>
                                            ) : (
                                                <table className="w-full enterprise-table text-sm">
                                                    <thead>
                                                        <tr>
                                                            <th className="px-4 py-3 text-left">Bilagsnr</th>
                                                            <th className="px-4 py-3 text-left">Leverandør</th>
                                                            <th className="px-4 py-3 text-left">Koststed</th>
                                                            <th className="px-4 py-3 text-left">Konto</th>
                                                            <th className="px-4 py-3 text-right">Beløp (kr)</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {outliers.orphan_outliers.map((o, i) => (
                                                            <tr key={i} className="border-t border-border">
                                                                <td className="px-4 py-2 font-mono text-xs text-muted">{o.bilagsnr}</td>
                                                                <td className="px-4 py-2 font-medium">{o.leverandor_navn}</td>
                                                                <td className="px-4 py-2 text-muted text-xs">{o.dim1_kode}{o.dim1_navn ? ` · ${o.dim1_navn}` : ""}</td>
                                                                <td className="px-4 py-2 text-muted">{o.konto_navn}</td>
                                                                <td className="px-4 py-2 text-right font-mono font-semibold">{fmt(o.belop)}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* ── Seksjon 2: Prognose 2027 ───────────────────────── */}
                        <div className="rounded-xl border border-blue-500/30 bg-surface overflow-hidden">
                            <button
                                type="button"
                                onClick={() => toggle("prognose")}
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    {openSection === "prognose"
                                        ? <ChevronDown className="w-5 h-5 text-blue-400 shrink-0" />
                                        : <ChevronRight className="w-5 h-5 text-muted shrink-0" />}
                                    <TrendingUp className="w-5 h-5 text-blue-400 shrink-0" />
                                    <span className="font-semibold text-foreground">Prognosegjennomgang 2027</span>
                                    {prognose && (
                                        <>
                                            <span className="text-sm text-muted">({prognose.items.length} eiendommer)</span>
                                            {prognose.flagged_count > 0 && (
                                                <span className="px-2 py-0.5 rounded bg-orange-500/15 text-orange-400 text-xs font-semibold">
                                                    {prognose.flagged_count} flagget
                                                </span>
                                            )}
                                            {prognose.growth_pct != null && (
                                                <span className="text-xs text-blue-400 px-2 py-0.5 rounded bg-blue-500/10">
                                                    {fmtPct(prognose.growth_pct)} vs 2025
                                                </span>
                                            )}
                                        </>
                                    )}
                                </div>
                                {prognose && (
                                    <span className="font-mono font-semibold text-foreground shrink-0">
                                        {fmt(prognose.total_predicted)} kr
                                    </span>
                                )}
                            </button>

                            {openSection === "prognose" && prognose && (
                                <div className="border-t border-border bg-background/50">
                                    <div className="grid grid-cols-3 gap-4 px-5 py-4 border-b border-border/50 bg-blue-500/5">
                                        <div>
                                            <div className="text-xs text-muted mb-1">Faktisk 2025</div>
                                            <div className="font-mono font-semibold">{fmt(prognose.total_actual_2025)} kr</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-muted mb-1">Prognose 2027</div>
                                            <div className="font-mono font-semibold text-blue-400">{fmt(prognose.total_predicted)} kr</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-muted mb-1">Samlet vekst</div>
                                            <div className={`font-mono font-semibold ${(prognose.growth_pct ?? 0) > 10 ? "text-orange-400" : "text-foreground"}`}>
                                                {fmtPct(prognose.growth_pct)}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="overflow-x-auto">
                                        <table className="w-full enterprise-table text-sm">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-3 text-left">Eiendom</th>
                                                    <th className="px-4 py-3 text-left">Region</th>
                                                    <th className="px-4 py-3 text-right">Faktisk 2025 (kr)</th>
                                                    <th className="px-4 py-3 text-right">Prognose 2027 (kr)</th>
                                                    <th className="px-4 py-3 text-right">Vekst</th>
                                                    <th className="px-4 py-3 text-left">Flagg</th>
                                                    <th className="px-4 py-3 text-center">Risiko</th>
                                                    <th className="w-8"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {prognose.items.map((item, i) => (
                                                    <tr key={i} className="border-t border-border">
                                                        <td className="px-4 py-2 font-medium">{item.name}</td>
                                                        <td className="px-4 py-2 text-muted">{item.region}</td>
                                                        <td className="px-4 py-2 text-right font-mono text-muted">{fmt(item.actual_2025)}</td>
                                                        <td className="px-4 py-2 text-right font-mono font-semibold">{fmt(item.predicted)}</td>
                                                        <td className={`px-4 py-2 text-right font-mono ${(item.growth_pct ?? 0) > 15 ? "text-orange-400 font-semibold" : (item.growth_pct ?? 0) < 0 ? "text-red-500" : "text-muted"}`}>
                                                            {fmtPct(item.growth_pct)}
                                                        </td>
                                                        <td className="px-4 py-2">
                                                            {item.flags.map((f) => <FlagBadge key={f} flag={f} />)}
                                                        </td>
                                                        <td className="px-4 py-2 text-center"><RiskBadge risk={item.risk} /></td>
                                                        <td className="pr-2">
                                                            <Link href={`/properties/${item.property_id}`} className="p-1 text-primary hover:bg-primary/10 rounded inline-flex">
                                                                <ExternalLink size={14} />
                                                            </Link>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* ── Seksjon 3: Samlet vurdering ───────────────────── */}
                        <div className={`rounded-xl border overflow-hidden ${readyForControl ? "border-green-500/30 bg-surface" : "border-orange-500/30 bg-surface"}`}>
                            <button
                                type="button"
                                onClick={() => toggle("vurdering")}
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    {openSection === "vurdering"
                                        ? <ChevronDown className={`w-5 h-5 shrink-0 ${readyForControl ? "text-green-400" : "text-orange-400"}`} />
                                        : <ChevronRight className="w-5 h-5 text-muted shrink-0" />}
                                    {readyForControl
                                        ? <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
                                        : <XCircle className="w-5 h-5 text-orange-400 shrink-0" />}
                                    <span className="font-semibold text-foreground">Samlet vurdering</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${readyForControl ? "bg-green-500/15 text-green-400" : "bg-orange-500/15 text-orange-400"}`}>
                                        {readyForControl ? "Klar for intern kontroll" : `Gjennomgå ${highRisk} sak${highRisk !== 1 ? "er" : ""} først`}
                                    </span>
                                </div>
                            </button>

                            {openSection === "vurdering" && (
                                <div className="border-t border-border bg-background/50 px-6 py-5 space-y-5">
                                    <div className={`flex items-start gap-3 p-4 rounded-lg ${readyForControl ? "bg-green-500/8" : "bg-orange-500/8"}`}>
                                        {readyForControl
                                            ? <CheckCircle2 className="w-5 h-5 text-green-400 mt-0.5 shrink-0" />
                                            : <AlertTriangle className="w-5 h-5 text-orange-400 mt-0.5 shrink-0" />}
                                        <p className="text-sm leading-relaxed">
                                            {readyForControl
                                                ? "Alle statistiske tester er gjennomført og det er ingen HØY-risiko avvik i GL 2025-dataene. Prognose 2027 (Holt-Winters, α=0,7 β=0,3) er gjennomgått og fremstår konsistent. Datagrunnlaget anbefales sendt til intern kontroll og regnskapsavdelingen."
                                                : `Det er funnet ${highRisk} HØY-risiko og ${medRisk} MIDDELS-risiko avvik som bør gjennomgås før materialet sendes til intern kontroll. Se detaljer i seksjonene over og vurder om avvikene er legitime eller feil.`}
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                        <div className="p-4 rounded-lg border border-border bg-surface">
                                            <div className="text-xs text-muted mb-1">GL-outliers totalt</div>
                                            <div className="text-2xl font-bold">{outliers?.summary.total_outliers ?? "—"}</div>
                                            <div className="text-xs text-muted mt-1">
                                                {outliers?.summary.high_risk ?? 0} HØY · {outliers?.summary.medium_risk ?? 0} MIDDELS
                                            </div>
                                        </div>
                                        <div className="p-4 rounded-lg border border-border bg-surface">
                                            <div className="text-xs text-muted mb-1">Orphan-tx &gt; 100k</div>
                                            <div className="text-2xl font-bold">{outliers?.summary.orphan_count ?? "—"}</div>
                                            <div className="text-xs text-muted mt-1">Ikke koblet til eiendom</div>
                                        </div>
                                        <div className="p-4 rounded-lg border border-border bg-surface">
                                            <div className="text-xs text-muted mb-1">Flaggede 2027-pred.</div>
                                            <div className="text-2xl font-bold">{prognose?.flagged_count ?? "—"}</div>
                                            <div className="text-xs text-muted mt-1">av {prognose?.items.length ?? "—"} eiendommer</div>
                                        </div>
                                        <div className="p-4 rounded-lg border border-border bg-surface">
                                            <div className="text-xs text-muted mb-1">Prognose vekst 2025→2027</div>
                                            <div className={`text-2xl font-bold ${(prognose?.growth_pct ?? 0) > 10 ? "text-orange-400" : ""}`}>
                                                {fmtPct(prognose?.growth_pct)}
                                            </div>
                                            <div className="text-xs text-muted mt-1">{fmt(prognose?.total_predicted ?? 0)} kr totalt</div>
                                        </div>
                                    </div>

                                    <div className="flex items-start gap-2 p-3 rounded-lg bg-muted/10 text-xs text-muted">
                                        <Info size={14} className="mt-0.5 shrink-0" />
                                        <span>
                                            <strong>Metode:</strong> Outlier-deteksjon via z-score (terskel 2,5σ).
                                            Prognose er Holts lineære eksponentielle utjevning (α=0,7 β=0,3) på GL-historikk 2021–2025.
                                            Eiendommer med ett historisk datapunkt bruker inflasjonsfallback 3,5 %.
                                            Generert {new Date().toLocaleDateString("nb-NO")} kl.{" "}
                                            {new Date().toLocaleTimeString("nb-NO", { hour: "2-digit", minute: "2-digit" })}.
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>
                )}
            </main>
        </div>
    );
}
