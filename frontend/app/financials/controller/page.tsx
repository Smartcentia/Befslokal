"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api/client";
import Link from "next/link";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    LineChart, Line, ReferenceLine, Cell, PieChart, Pie, Legend,
} from "recharts";
import {
    TrendingUp, TrendingDown, AlertTriangle, Building2, BarChart3,
    Landmark, ChevronRight, RefreshCw, Download, ArrowUpRight,
    ArrowDownRight, Minus, Info, CheckCircle2, XCircle, Eye,
    Calendar, GitBranch, Bell,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface MonthlyRow {
    month: number; month_name: string;
    budget: number; actual: number;
    variance: number; variance_pct: number | null;
}

interface AvviksRow {
    category: string; budget: number; actual: number;
    variance: number; variance_pct: number | null;
}

interface AvskrivningAr {
    ar: number; avskrivning: number; restverdi_inngaende: number;
}

interface AnleggData {
    totalt_antall: number; aktive: number;
    total_bokfort_verdi: number; total_arlig_avskrivning: number;
    avskrivningsplan: AvskrivningAr[];
}

interface HusleieBenchmarkRow {
    property_id: string; name: string; region: string;
    total_area: number; husleie_belop: number;
    kr_per_kvm: number | null; is_statsbygg: boolean;
    active_contracts: number;
}

interface RegionAverage {
    region: string; avg_kr_per_kvm: number | null;
    total_belop: number; count: number;
}

interface HusleieData {
    year: number; total_husleie: number;
    statsbygg_belop: number; statsbygg_share: number;
    rows: HusleieBenchmarkRow[];
    region_averages: RegionAverage[];
    empty_paying: HusleieBenchmarkRow[];
}

interface OutlierSummary {
    total_outliers: number; high_risk: number; medium_risk: number;
    transaction_count: number; property_count: number;
    category_yoy_count: number; orphan_count: number;
}

interface PropertyOutlier {
    property_id: string; name: string; region: string;
    total_2025: number; region_avg: number; z_score: number; risk: string;
}

interface TxOutlier {
    bilagsnr: string; leverandor_navn: string; konto_navn: string;
    belop: number; z_score: number; category_avg: number; risk: string;
    dim1_kode: string; dim1_navn: string; tekst: string;
}

interface CashflowContract {
    contract_id: string; property_name: string; region: string;
    party_name: string; end_date: string; amount_per_year: number;
    has_option: boolean;
}

interface CashflowQuarter {
    quarter: string; count: number; amount_per_year: number;
    contracts: CashflowContract[];
}

interface CashflowAlert {
    contract_id: string; property_name: string; region: string;
    end_date: string; days_left: number; amount_per_year: number;
}

interface CashflowData {
    quarters_ahead: number; total_at_risk: number;
    total_contracts: number; alerts_count: number;
    quarters: CashflowQuarter[];
    by_region: { region: string; amount_per_year: number }[];
    alerts: CashflowAlert[];
}

interface Dim4Split {
    dim4_kode: string; belop: number; antall: number;
}

interface Dim4Item {
    property_id: string; property_name: string; region: string;
    total: number; dim4_splits: Dim4Split[];
}

interface Dim4Data {
    year: number; property_count: number; total_belop: number;
    items: Dim4Item[];
}

interface OutliersData {
    year: number; summary: OutlierSummary;
    transaction_outliers: TxOutlier[];
    property_outliers: PropertyOutlier[];
    category_yoy_outliers: Array<{konto_navn:string; amt_2024:number; amt_2025:number; change_pct:number; risk:string}>;
    orphan_outliers: Array<{bilagsnr:string; leverandor_navn:string; dim1_kode:string; belop:number; konto_navn:string; tekst:string}>;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

const fmtM = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 1, notation: "compact" }).format(n);

const fmtPct = (n: number | null) => n != null ? `${n > 0 ? "+" : ""}${n.toFixed(1)} %` : "–";

function KpiCard({ title, value, sub, icon: Icon, trend, color = "blue" }: {
    title: string; value: string; sub?: string;
    icon: React.ElementType; trend?: "up" | "down" | "neutral";
    color?: "blue" | "green" | "red" | "amber" | "purple";
}) {
    const colors = {
        blue: "text-blue-600 bg-blue-50 border-blue-100",
        green: "text-green-600 bg-green-50 border-green-100",
        red: "text-red-600 bg-red-50 border-red-100",
        amber: "text-amber-600 bg-amber-50 border-amber-100",
        purple: "text-purple-600 bg-purple-50 border-purple-100",
    };
    const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;
    return (
        <div className="bg-card border border-border rounded-xl p-5 flex flex-col gap-2">
            <div className="flex items-center justify-between">
                <span className="text-xs text-muted uppercase tracking-wider font-medium">{title}</span>
                <span className={`p-1.5 rounded-lg border ${colors[color]}`}>
                    <Icon size={14} />
                </span>
            </div>
            <div className="text-2xl font-bold text-foreground">{value}</div>
            {sub && (
                <div className="flex items-center gap-1 text-xs text-muted">
                    {trend && <TrendIcon size={12} />}
                    {sub}
                </div>
            )}
        </div>
    );
}

function SectionHeader({ title, subtitle, link }: { title: string; subtitle?: string; link?: string }) {
    return (
        <div className="flex items-center justify-between mb-4">
            <div>
                <h2 className="text-base font-semibold text-foreground">{title}</h2>
                {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
            </div>
            {link && (
                <Link href={link} className="flex items-center gap-1 text-xs text-primary hover:underline">
                    Se mer <ChevronRight size={12} />
                </Link>
            )}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function FinansiellKontrollerPage() {
    const [year, setYear] = useState(2025);
    const [tab, setTab] = useState<"budsjett" | "husleie" | "anlegg" | "cashflow" | "dim4" | "avvik">("budsjett");

    const [monthly, setMonthly] = useState<MonthlyRow[]>([]);
    const [avviks, setAvviks] = useState<AvviksRow[]>([]);
    const [anlegg, setAnlegg] = useState<AnleggData | null>(null);
    const [husleie, setHusleie] = useState<HusleieData | null>(null);
    const [outliers, setOutliers] = useState<OutliersData | null>(null);
    const [cashflow, setCashflow] = useState<CashflowData | null>(null);
    const [dim4, setDim4] = useState<Dim4Data | null>(null);
    const [loading, setLoading] = useState(true);
    const [outliersLoading, setOutliersLoading] = useState(false);
    const [cashflowLoading, setCashflowLoading] = useState(false);
    const [dim4Loading, setDim4Loading] = useState(false);
    const [expandedQuarter, setExpandedQuarter] = useState<string | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [mon, avv, anl, hus] = await Promise.allSettled([
                fetchAPI(`/financials/monthly-budget-actual?year=${year}`),
                fetchAPI(`/cost-management/costs/analysis/budget-variance?year=${year}`),
                fetchAPI(`/financials/srs17/anlegg`),
                fetchAPI(`/financials/husleie-benchmark?year=${year}`),
            ]);
            if (mon.status === "fulfilled") setMonthly(mon.value as MonthlyRow[]);
            if (avv.status === "fulfilled") {
                const d = avv.value as { items?: AvviksRow[] };
                setAvviks(d?.items ?? (Array.isArray(avv.value) ? avv.value as AvviksRow[] : []));
            }
            if (anl.status === "fulfilled") setAnlegg(anl.value as AnleggData);
            if (hus.status === "fulfilled") setHusleie(hus.value as HusleieData);
        } finally {
            setLoading(false);
        }
    }, [year]);

    const loadOutliers = useCallback(async () => {
        setOutliersLoading(true);
        try {
            const data = await fetchAPI(`/financials/outliers?year=${year}`);
            setOutliers(data as OutliersData);
        } catch {
            // ignore
        } finally {
            setOutliersLoading(false);
        }
    }, [year]);

    const loadCashflow = useCallback(async () => {
        setCashflowLoading(true);
        try {
            const data = await fetchAPI(`/financials/cashflow-prognose?quarters_ahead=8`);
            setCashflow(data as CashflowData);
        } catch { /* ignore */ } finally { setCashflowLoading(false); }
    }, []);

    const loadDim4 = useCallback(async () => {
        setDim4Loading(true);
        try {
            const data = await fetchAPI(`/financials/dim4-splitt?year=${year}`);
            setDim4(data as Dim4Data);
        } catch { /* ignore */ } finally { setDim4Loading(false); }
    }, [year]);

    useEffect(() => { load(); }, [load]);
    useEffect(() => { if (tab === "avvik") loadOutliers(); }, [tab, loadOutliers]);
    useEffect(() => { if (tab === "cashflow") loadCashflow(); }, [tab, loadCashflow]);
    useEffect(() => { if (tab === "dim4") loadDim4(); }, [tab, loadDim4]);

    // ── Derived stats ──────────────────────────────────────────────────────────
    const totalBudget = monthly.reduce((s, r) => s + r.budget, 0);
    const totalActual = monthly.reduce((s, r) => s + r.actual, 0);
    const ytdVariance = totalBudget - totalActual;
    const ytdVariancePct = totalBudget > 0 ? (ytdVariance / totalBudget * 100) : 0;
    const overBudgetMonths = monthly.filter(r => r.variance < 0).length;

    const monthlyChartData = monthly.map(r => ({
        name: r.month_name,
        Budsjett: r.budget,
        Faktisk: r.actual,
        Varians: r.variance,
    }));

    // ── Render ─────────────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="bg-card border-b border-border px-6 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-2 text-xs text-muted mb-1">
                            <Link href="/financials" className="hover:text-primary">Økonomi</Link>
                            <ChevronRight size={10} />
                            <span>Finanscontroller</span>
                        </div>
                        <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                            <BarChart3 size={20} className="text-primary" />
                            Finanscontroller
                        </h1>
                        <p className="text-xs text-muted mt-0.5">
                            Budget vs. regnskap · SRS-avskrivninger · Husleie-benchmark · Avviksanalyse
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={year}
                            onChange={e => setYear(Number(e.target.value))}
                            className="text-sm border border-border rounded-lg px-3 py-1.5 bg-background text-foreground"
                        >
                            {[2023, 2024, 2025, 2026].map(y => (
                                <option key={y} value={y}>{y}</option>
                            ))}
                        </select>
                        <button
                            onClick={load}
                            disabled={loading}
                            className="p-2 rounded-lg border border-border hover:bg-muted/30 text-muted"
                        >
                            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
                {/* KPI Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <KpiCard
                        title="YTD Budsjett"
                        value={fmtM(totalBudget)}
                        icon={Landmark}
                        color="blue"
                    />
                    <KpiCard
                        title="YTD Faktisk"
                        value={fmtM(totalActual)}
                        sub={`${fmtPct(ytdVariancePct)} vs budsjett`}
                        icon={BarChart3}
                        trend={ytdVariance >= 0 ? "up" : "down"}
                        color={ytdVariance >= 0 ? "green" : "red"}
                    />
                    <KpiCard
                        title="Total husleie"
                        value={husleie ? fmtM(husleie.total_husleie) : "–"}
                        sub={husleie ? `${husleie.statsbygg_share} % Statsbygg` : undefined}
                        icon={Building2}
                        color="purple"
                    />
                    <KpiCard
                        title="Bokførte anleggsmidler"
                        value={anlegg ? fmtM(anlegg.total_bokfort_verdi) : "–"}
                        sub={anlegg ? `${anlegg.aktive} aktive (SRS 17)` : undefined}
                        icon={TrendingDown}
                        color="amber"
                    />
                </div>

                {/* Tabs */}
                <div className="flex gap-1 border-b border-border">
                    {([
                        { key: "budsjett", label: "Budget vs. Regnskap" },
                        { key: "husleie", label: "Husleie-benchmark" },
                        { key: "anlegg", label: "SRS 17 Avskrivninger" },
                        { key: "cashflow", label: "Cashflow-prognose" },
                    { key: "dim4", label: "Dim4-splitt" },
                    { key: "avvik", label: "Avviksanalyse" },
                    ] as { key: typeof tab; label: string }[]).map(t => (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                                tab === t.key
                                    ? "border-primary text-primary"
                                    : "border-transparent text-muted hover:text-foreground"
                            }`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* ── Tab: Budget vs. Regnskap ───────────────────────────────────── */}
                {tab === "budsjett" && (
                    <div className="space-y-6">
                        {/* Monthly bar chart */}
                        <div className="bg-card border border-border rounded-xl p-5">
                            <SectionHeader
                                title={`Budget vs. Faktisk ${year} – månedlig`}
                                subtitle="Blå = budsjett, grønn = faktisk. Negativ varians betyr overforbruk."
                            />
                            {monthly.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={monthlyChartData} barGap={4}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                                        <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} />
                                        <Tooltip
                                            formatter={(val: number, name: string) => [fmt(val), name]}
                                            contentStyle={{ fontSize: 12 }}
                                        />
                                        <Bar dataKey="Budsjett" fill="#3b82f6" opacity={0.7} radius={[3,3,0,0]} />
                                        <Bar dataKey="Faktisk" radius={[3,3,0,0]}>
                                            {monthlyChartData.map((entry, idx) => (
                                                <Cell
                                                    key={idx}
                                                    fill={entry.Faktisk <= entry.Budsjett ? "#22c55e" : "#ef4444"}
                                                />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-48 flex items-center justify-center text-muted text-sm">
                                    Ingen budsjettdata for {year}
                                </div>
                            )}
                        </div>

                        {/* Variance line */}
                        <div className="bg-card border border-border rounded-xl p-5">
                            <SectionHeader
                                title="Månedlig varians (budsjett − faktisk)"
                                subtitle="Positiv = under budsjett (bra). Negativ = overforbruk (rødt)."
                            />
                            {monthly.length > 0 ? (
                                <ResponsiveContainer width="100%" height={180}>
                                    <LineChart data={monthly.map(r => ({
                                        name: r.month_name,
                                        Varians: r.variance,
                                    }))}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                                        <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} />
                                        <Tooltip formatter={(v: number) => [fmt(v), "Varians"]} contentStyle={{ fontSize: 12 }} />
                                        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 4" />
                                        <Line
                                            type="monotone" dataKey="Varians"
                                            stroke="#3b82f6" strokeWidth={2} dot={false}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-24 flex items-center justify-center text-muted text-sm">Ingen data</div>
                            )}
                        </div>

                        {/* Monthly table */}
                        <div className="bg-card border border-border rounded-xl p-5">
                            <SectionHeader title="Detaljert månedstabell" />
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-border text-xs text-muted uppercase">
                                            <th className="text-left py-2 pr-4">Måned</th>
                                            <th className="text-right py-2 pr-4">Budsjett</th>
                                            <th className="text-right py-2 pr-4">Faktisk</th>
                                            <th className="text-right py-2 pr-4">Varians</th>
                                            <th className="text-right py-2">Varians %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {monthly.map((r, i) => (
                                            <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                <td className="py-2 pr-4 font-medium">{r.month_name}</td>
                                                <td className="py-2 pr-4 text-right text-muted">{fmt(r.budget)}</td>
                                                <td className="py-2 pr-4 text-right">{fmt(r.actual)}</td>
                                                <td className={`py-2 pr-4 text-right font-medium ${r.variance >= 0 ? "text-green-600" : "text-red-600"}`}>
                                                    {r.variance >= 0 ? "+" : ""}{fmt(r.variance)}
                                                </td>
                                                <td className={`py-2 text-right text-xs ${r.variance >= 0 ? "text-green-600" : "text-red-500"}`}>
                                                    {fmtPct(r.variance_pct)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                    {monthly.length > 0 && (
                                        <tfoot>
                                            <tr className="border-t-2 border-border font-semibold">
                                                <td className="py-2 pr-4">Sum</td>
                                                <td className="py-2 pr-4 text-right">{fmt(totalBudget)}</td>
                                                <td className="py-2 pr-4 text-right">{fmt(totalActual)}</td>
                                                <td className={`py-2 pr-4 text-right ${ytdVariance >= 0 ? "text-green-600" : "text-red-600"}`}>
                                                    {ytdVariance >= 0 ? "+" : ""}{fmt(ytdVariance)}
                                                </td>
                                                <td className={`py-2 text-right text-xs ${ytdVariance >= 0 ? "text-green-600" : "text-red-500"}`}>
                                                    {fmtPct(ytdVariancePct)}
                                                </td>
                                            </tr>
                                        </tfoot>
                                    )}
                                </table>
                            </div>
                        </div>

                        {/* Category variance */}
                        {avviks.length > 0 && (
                            <div className="bg-card border border-border rounded-xl p-5">
                                <SectionHeader
                                    title="Avvik per kostnadskategori"
                                    subtitle="Kategorier sortert etter avvik"
                                />
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border text-xs text-muted uppercase">
                                                <th className="text-left py-2 pr-4">Kategori</th>
                                                <th className="text-right py-2 pr-4">Budsjett</th>
                                                <th className="text-right py-2 pr-4">Faktisk</th>
                                                <th className="text-right py-2 pr-4">Avvik</th>
                                                <th className="text-right py-2">Avvik %</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {avviks.slice(0, 15).map((r, i) => (
                                                <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                    <td className="py-2 pr-4 font-medium capitalize">{r.category}</td>
                                                    <td className="py-2 pr-4 text-right text-muted">{fmt(r.budget)}</td>
                                                    <td className="py-2 pr-4 text-right">{fmt(r.actual)}</td>
                                                    <td className={`py-2 pr-4 text-right font-medium ${r.variance >= 0 ? "text-green-600" : "text-red-600"}`}>
                                                        {r.variance >= 0 ? "+" : ""}{fmt(r.variance)}
                                                    </td>
                                                    <td className={`py-2 text-right text-xs ${(r.variance_pct ?? 0) >= 0 ? "text-green-600" : "text-red-500"}`}>
                                                        {fmtPct(r.variance_pct)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Husleie-benchmark ─────────────────────────────────────── */}
                {tab === "husleie" && (
                    <div className="space-y-6">
                        {husleie ? (
                            <>
                                {/* KPI row */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <KpiCard
                                        title="Total husleie"
                                        value={fmtM(husleie.total_husleie)}
                                        icon={Building2} color="blue"
                                    />
                                    <KpiCard
                                        title="Statsbygg-andel"
                                        value={`${husleie.statsbygg_share} %`}
                                        sub={`${fmtM(husleie.statsbygg_belop)} til Statsbygg`}
                                        icon={Landmark} color="purple"
                                    />
                                    <KpiCard
                                        title="Eiendommer analysert"
                                        value={String(husleie.rows.length)}
                                        icon={Building2} color="green"
                                    />
                                    <KpiCard
                                        title="Tomme betaler husleie"
                                        value={String(husleie.empty_paying.length)}
                                        sub={husleie.empty_paying.length > 0 ? "Ingen aktive kontrakter" : "Ingen funn"}
                                        icon={AlertTriangle}
                                        color={husleie.empty_paying.length > 0 ? "red" : "green"}
                                    />
                                </div>

                                {/* Region averages chart */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <SectionHeader
                                        title="Gjennomsnittlig husleie kr/kvm per region"
                                        subtitle="Regionalt benchmark – høye verdier kan indikere lite areal-effektive eiendommer"
                                    />
                                    {husleie.region_averages.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={220}>
                                            <BarChart data={husleie.region_averages} layout="vertical">
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                                                <XAxis type="number" tickFormatter={v => `${v.toLocaleString("nb-NO")} kr`} tick={{ fontSize: 11 }} />
                                                <YAxis dataKey="region" type="category" width={80} tick={{ fontSize: 11 }} />
                                                <Tooltip
                                                    formatter={(v: number) => [`${v.toLocaleString("nb-NO")} kr/kvm`, "Snitt kr/kvm"]}
                                                    contentStyle={{ fontSize: 12 }}
                                                />
                                                <Bar dataKey="avg_kr_per_kvm" fill="#8b5cf6" radius={[0,4,4,0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-32 flex items-center justify-center text-muted text-sm">
                                            Ingen kr/kvm-data tilgjengelig (sjekk at properties har total_area satt)
                                        </div>
                                    )}
                                </div>

                                {/* Statsbygg vs Private pie */}
                                <div className="grid md:grid-cols-2 gap-6">
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Statsbygg vs. privat utleier"
                                            subtitle="Fordeling av husleiebelastning"
                                        />
                                        <ResponsiveContainer width="100%" height={180}>
                                            <PieChart>
                                                <Pie
                                                    data={[
                                                        { name: "Statsbygg", value: husleie.statsbygg_belop },
                                                        { name: "Private/andre", value: husleie.total_husleie - husleie.statsbygg_belop },
                                                    ]}
                                                    cx="50%" cy="50%" outerRadius={70}
                                                    dataKey="value"
                                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)} %`}
                                                    labelLine={false}
                                                >
                                                    <Cell fill="#8b5cf6" />
                                                    <Cell fill="#3b82f6" />
                                                </Pie>
                                                <Tooltip formatter={(v: number) => [fmt(v), ""]} contentStyle={{ fontSize: 12 }} />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>

                                    {/* Empty but paying */}
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Eiendommer uten kontrakter – betaler likevel husleie"
                                            subtitle="Mulig feilbooking eller tomme eiendommer"
                                        />
                                        {husleie.empty_paying.length === 0 ? (
                                            <div className="flex items-center gap-2 text-green-600 text-sm mt-4">
                                                <CheckCircle2 size={16} />
                                                Ingen funn – alle husleiebetalende eiendommer har aktive kontrakter
                                            </div>
                                        ) : (
                                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                                {husleie.empty_paying.map((r, i) => (
                                                    <div key={i} className="flex items-center justify-between text-sm py-1 border-b border-border/50">
                                                        <div>
                                                            <Link href={`/properties/${r.property_id}`} className="font-medium text-foreground hover:text-primary">
                                                                {r.name}
                                                            </Link>
                                                            <div className="text-xs text-muted">{r.region}</div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="font-medium text-red-600">{fmt(r.husleie_belop)}</div>
                                                            <div className="text-xs text-muted">0 kontrakter</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Full table */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <SectionHeader
                                        title="Husleie per eiendom"
                                        subtitle="Sortert etter kr/kvm – høyeste øverst"
                                    />
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-border text-xs text-muted uppercase">
                                                    <th className="text-left py-2 pr-4">Eiendom</th>
                                                    <th className="text-left py-2 pr-4">Region</th>
                                                    <th className="text-right py-2 pr-4">Areal (kvm)</th>
                                                    <th className="text-right py-2 pr-4">Husleie</th>
                                                    <th className="text-right py-2 pr-4">Kr/kvm</th>
                                                    <th className="text-center py-2">Statsbygg</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {husleie.rows.map((r, i) => {
                                                    const regionAvg = husleie.region_averages.find(a => a.region === r.region)?.avg_kr_per_kvm ?? null;
                                                    const aboveAvg = r.kr_per_kvm != null && regionAvg != null && r.kr_per_kvm > regionAvg * 1.2;
                                                    return (
                                                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                            <td className="py-2 pr-4">
                                                                <Link href={`/properties/${r.property_id}`} className="font-medium hover:text-primary">
                                                                    {r.name}
                                                                </Link>
                                                            </td>
                                                            <td className="py-2 pr-4 text-muted text-xs">{r.region}</td>
                                                            <td className="py-2 pr-4 text-right text-muted">
                                                                {r.total_area > 0 ? r.total_area.toLocaleString("nb-NO") : "–"}
                                                            </td>
                                                            <td className="py-2 pr-4 text-right">{fmt(r.husleie_belop)}</td>
                                                            <td className={`py-2 pr-4 text-right font-medium ${aboveAvg ? "text-amber-600" : ""}`}>
                                                                {r.kr_per_kvm != null ? `${r.kr_per_kvm.toLocaleString("nb-NO")} kr` : "–"}
                                                                {aboveAvg && <span className="ml-1 text-xs">↑</span>}
                                                            </td>
                                                            <td className="py-2 text-center">
                                                                {r.is_statsbygg
                                                                    ? <span className="text-purple-600 text-xs font-medium">Statsbygg</span>
                                                                    : <span className="text-muted text-xs">Privat</span>
                                                                }
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="bg-card border border-border rounded-xl p-10 text-center text-muted">
                                {loading ? "Laster husleie-data..." : "Ingen husleie-data tilgjengelig"}
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: SRS 17 Avskrivninger ─────────────────────────────────── */}
                {tab === "anlegg" && (
                    <div className="space-y-6">
                        {anlegg ? (
                            <>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <KpiCard
                                        title="Totalt antall anlegg"
                                        value={String(anlegg.totalt_antall)}
                                        icon={Building2} color="blue"
                                    />
                                    <KpiCard
                                        title="Aktive anlegg"
                                        value={String(anlegg.aktive)}
                                        icon={CheckCircle2} color="green"
                                    />
                                    <KpiCard
                                        title="Bokført verdi"
                                        value={fmtM(anlegg.total_bokfort_verdi)}
                                        sub="Inngående balanse"
                                        icon={Landmark} color="purple"
                                    />
                                    <KpiCard
                                        title="Årl. avskrivning"
                                        value={fmtM(anlegg.total_arlig_avskrivning)}
                                        sub="SRS 17 lineær"
                                        icon={TrendingDown} color="amber"
                                    />
                                </div>

                                {/* SRS 10 note */}
                                <div className="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm">
                                    <Info size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                                    <div className="text-blue-800">
                                        <strong>SRS 10 nøytralisering:</strong> Alle avskrivninger på bruksrettseiendeler (konto 1268/6830)
                                        skal motposteres på konto 3390 (overføring fra staten). Netto resultateffekt = 0 for statlig etat.
                                        Kontroller at Agresso er konfigurert med automatisk motpost på bilagsart AVS.
                                    </div>
                                </div>

                                {/* Avskrivningsplan chart */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <SectionHeader
                                        title="Avskrivningsplan 2025–2030 (SRS 17)"
                                        subtitle="Lineær avskrivning over MIN(levetid, gjenværende leieperiode)"
                                    />
                                    {anlegg.avskrivningsplan.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={260}>
                                            <BarChart data={anlegg.avskrivningsplan}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                                <XAxis dataKey="ar" tick={{ fontSize: 11 }} />
                                                <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} yAxisId="left" />
                                                <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} yAxisId="right" orientation="right" />
                                                <Tooltip
                                                    formatter={(v: number, name: string) => [fmt(v), name]}
                                                    contentStyle={{ fontSize: 12 }}
                                                />
                                                <Bar yAxisId="left" dataKey="avskrivning" fill="#f59e0b" radius={[4,4,0,0]} name="Avskrivning" />
                                                <Bar yAxisId="right" dataKey="restverdi_inngaende" fill="#3b82f6" opacity={0.5} radius={[4,4,0,0]} name="Restverdi (inng.)" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-48 flex items-center justify-center text-muted text-sm">
                                            Ingen avskrivningsplan – kjør SRS 17 populate fra Anlegg-siden
                                        </div>
                                    )}
                                </div>

                                {/* Plan table */}
                                {anlegg.avskrivningsplan.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader title="Detaljert avskrivningsplan" />
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-border text-xs text-muted uppercase">
                                                    <th className="text-left py-2 pr-4">År</th>
                                                    <th className="text-right py-2 pr-4">Avskrivning</th>
                                                    <th className="text-right py-2 pr-4">Restverdi inngående</th>
                                                    <th className="text-right py-2">Restverdi utgående</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {anlegg.avskrivningsplan.map((r, i) => (
                                                    <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                        <td className="py-2 pr-4 font-medium">{r.ar}</td>
                                                        <td className="py-2 pr-4 text-right text-amber-700">{fmt(r.avskrivning)}</td>
                                                        <td className="py-2 pr-4 text-right">{fmt(r.restverdi_inngaende)}</td>
                                                        <td className="py-2 text-right text-muted">{fmt(Math.max(0, r.restverdi_inngaende - r.avskrivning))}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <div className="mt-4 flex gap-3">
                                            <Link
                                                href="/financials/anlegg"
                                                className="flex items-center gap-1.5 text-sm text-primary hover:underline"
                                            >
                                                <Eye size={14} /> Administrer anlegg (SRS 17)
                                            </Link>
                                            <Link
                                                href="/financials/srs"
                                                className="flex items-center gap-1.5 text-sm text-primary hover:underline"
                                            >
                                                <BarChart3 size={14} /> SRS-rapport
                                            </Link>
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="bg-card border border-border rounded-xl p-10 text-center text-muted">
                                {loading ? "Laster anleggsdata..." : "Ingen SRS 17-data tilgjengelig"}
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Cashflow-prognose ────────────────────────────────────── */}
                {tab === "cashflow" && (
                    <div className="space-y-6">
                        {cashflowLoading ? (
                            <div className="bg-card border border-border rounded-xl p-10 text-center text-muted">
                                <RefreshCw size={20} className="animate-spin mx-auto mb-2" />
                                Henter kontraktdata...
                            </div>
                        ) : cashflow ? (
                            <>
                                {/* Alerts banner */}
                                {cashflow.alerts.length > 0 && (
                                    <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
                                        <Bell size={16} className="text-red-600 mt-0.5 flex-shrink-0" />
                                        <div>
                                            <div className="text-sm font-semibold text-red-700">
                                                {cashflow.alerts.length} kontrakt{cashflow.alerts.length !== 1 ? "er" : ""} utløper innen 90 dager – uten opsjon
                                            </div>
                                            <div className="mt-2 space-y-1">
                                                {cashflow.alerts.slice(0, 5).map((a, i) => (
                                                    <div key={i} className="text-xs text-red-600 flex items-center gap-2">
                                                        <span className="font-medium">{a.property_name}</span>
                                                        <span>({a.region})</span>
                                                        <span>→</span>
                                                        <span>{a.days_left} dager</span>
                                                        <span className="font-mono">{fmt(a.amount_per_year)}/år</span>
                                                    </div>
                                                ))}
                                                {cashflow.alerts.length > 5 && (
                                                    <div className="text-xs text-red-500">+ {cashflow.alerts.length - 5} til…</div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* KPIs */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <KpiCard title="Totalt eksponering" value={fmtM(cashflow.total_at_risk)}
                                        sub="Sum årsleie som utløper" icon={TrendingDown} color="red" />
                                    <KpiCard title="Antall kontrakter" value={String(cashflow.total_contracts)}
                                        sub="Utløper innen 8 kv." icon={Calendar} color="amber" />
                                    <KpiCard title="Kritiske varsler" value={String(cashflow.alerts_count)}
                                        sub="< 90 dager, ingen opsjon" icon={Bell}
                                        color={cashflow.alerts_count > 0 ? "red" : "green"} />
                                    <KpiCard title="Regioner berørt" value={String(cashflow.by_region.length)}
                                        icon={Building2} color="blue" />
                                </div>

                                {/* Quarter bar chart */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <SectionHeader
                                        title="Kontraktsutløp per kvartal – årsleieeksponering"
                                        subtitle="Høye søyler = kvartal med stor reforhandlingsrisiko"
                                    />
                                    {cashflow.quarters.length > 0 ? (
                                        <ResponsiveContainer width="100%" height={240}>
                                            <BarChart data={cashflow.quarters.map(q => ({
                                                name: q.quarter,
                                                "Årsleie": q.amount_per_year,
                                                "Antall": q.count,
                                            }))}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                                                <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} />
                                                <Tooltip
                                                    formatter={(v: number, name: string) =>
                                                        name === "Årsleie" ? [fmt(v), name] : [v, name]
                                                    }
                                                    contentStyle={{ fontSize: 12 }}
                                                />
                                                <Bar dataKey="Årsleie" fill="#ef4444" radius={[4,4,0,0]} opacity={0.85} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    ) : (
                                        <div className="h-40 flex items-center justify-center text-muted text-sm">
                                            Ingen kontrakter utløper de neste 8 kvartalene
                                        </div>
                                    )}
                                </div>

                                {/* Region breakdown */}
                                {cashflow.by_region.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Eksponering per region"
                                            subtitle="Sum årsleie som utløper innen 8 kvartaler"
                                        />
                                        <ResponsiveContainer width="100%" height={Math.max(120, cashflow.by_region.length * 36)}>
                                            <BarChart data={cashflow.by_region} layout="vertical">
                                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                                                <XAxis type="number" tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} />
                                                <YAxis dataKey="region" type="category" width={80} tick={{ fontSize: 11 }} />
                                                <Tooltip formatter={(v: number) => [fmt(v), "Årsleie"]} contentStyle={{ fontSize: 12 }} />
                                                <Bar dataKey="amount_per_year" fill="#f97316" radius={[0,4,4,0]} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}

                                {/* Quarter detail accordion */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <SectionHeader
                                        title="Detaljer per kvartal"
                                        subtitle="Klikk på et kvartal for å se alle kontrakter"
                                    />
                                    <div className="space-y-2">
                                        {cashflow.quarters.map((q) => (
                                            <div key={q.quarter} className="border border-border rounded-lg overflow-hidden">
                                                <button
                                                    onClick={() => setExpandedQuarter(expandedQuarter === q.quarter ? null : q.quarter)}
                                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/20 text-sm"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <span className="font-mono font-semibold text-foreground">{q.quarter}</span>
                                                        <span className="text-muted text-xs">{q.count} kontrakt{q.count !== 1 ? "er" : ""}</span>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <span className="font-semibold text-red-600">{fmt(q.amount_per_year)}/år</span>
                                                        <ChevronRight size={14} className={`text-muted transition-transform ${expandedQuarter === q.quarter ? "rotate-90" : ""}`} />
                                                    </div>
                                                </button>
                                                {expandedQuarter === q.quarter && (
                                                    <div className="border-t border-border">
                                                        <table className="w-full text-xs">
                                                            <thead>
                                                                <tr className="bg-muted/20 text-muted uppercase">
                                                                    <th className="text-left px-4 py-2">Eiendom</th>
                                                                    <th className="text-left px-4 py-2">Utleier</th>
                                                                    <th className="text-left px-4 py-2">Region</th>
                                                                    <th className="text-right px-4 py-2">Utløper</th>
                                                                    <th className="text-right px-4 py-2">Årsleie</th>
                                                                    <th className="text-center px-4 py-2">Opsjon</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {q.contracts.map((c, i) => (
                                                                    <tr key={i} className="border-t border-border/50 hover:bg-muted/10">
                                                                        <td className="px-4 py-2 font-medium">{c.property_name}</td>
                                                                        <td className="px-4 py-2 text-muted">{c.party_name}</td>
                                                                        <td className="px-4 py-2 text-muted">{c.region}</td>
                                                                        <td className="px-4 py-2 text-right font-mono">{c.end_date}</td>
                                                                        <td className="px-4 py-2 text-right font-medium">{fmt(c.amount_per_year)}</td>
                                                                        <td className="px-4 py-2 text-center">
                                                                            {c.has_option
                                                                                ? <span className="text-green-600">✓</span>
                                                                                : <span className="text-muted">–</span>
                                                                            }
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="bg-card border border-border rounded-xl p-10 text-center">
                                <button onClick={loadCashflow}
                                    className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
                                    <Calendar size={16} /> Hent cashflow-prognose
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Dim4-splitt ───────────────────────────────────────────── */}
                {tab === "dim4" && (
                    <div className="space-y-6">
                        {dim4Loading ? (
                            <div className="bg-card border border-border rounded-xl p-10 text-center text-muted">
                                <RefreshCw size={20} className="animate-spin mx-auto mb-2" />
                                Analyserer tildelingsbrev-splitt...
                            </div>
                        ) : dim4 ? (
                            <>
                                <div className="flex items-start gap-3 bg-amber-50 border border-amber-100 rounded-xl p-4 text-sm">
                                    <Info size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
                                    <div className="text-amber-800">
                                        <strong>Dim4 = tildelingsbrev / finansieringskilde</strong> (DFØ-rapporteringsdimensjon).
                                        Samme leiekostnad som splittes på 2+ Dim4-koder kan indikere feilbooking i Agresso,
                                        eller en bevisst splitt mellom tildelingsbrev som bør dokumenteres separat.
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    <KpiCard title="Eiendommer med splitt" value={String(dim4.property_count)}
                                        icon={GitBranch} color={dim4.property_count > 0 ? "amber" : "green"} />
                                    <KpiCard title="Total eksponering" value={fmtM(dim4.total_belop)}
                                        sub="Sum GL-beløp i splittet" icon={Landmark} color="blue" />
                                    <KpiCard title="År analysert" value={String(dim4.year)}
                                        icon={BarChart3} color="purple" />
                                </div>

                                {dim4.items.length === 0 ? (
                                    <div className="bg-card border border-border rounded-xl p-10 text-center">
                                        <CheckCircle2 size={32} className="text-green-600 mx-auto mb-2" />
                                        <div className="text-sm text-muted">
                                            Ingen eiendommer med Dim4-splitt funnet for {dim4.year}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title={`Eiendommer med splitt på 2+ tildelingsbrev – ${dim4.year}`}
                                            subtitle="Sortert etter samlet belastning"
                                        />
                                        <div className="space-y-3">
                                            {dim4.items.map((item, i) => (
                                                <div key={i} className="border border-border rounded-lg p-4">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div>
                                                            <Link href={`/properties/${item.property_id}`}
                                                                className="font-semibold text-sm hover:text-primary">
                                                                {item.property_name}
                                                            </Link>
                                                            <span className="ml-2 text-xs text-muted">{item.region}</span>
                                                        </div>
                                                        <div className="font-semibold text-sm">{fmt(item.total)}</div>
                                                    </div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {item.dim4_splits.map((split, j) => {
                                                            const pct = item.total > 0
                                                                ? Math.round(split.belop / item.total * 100)
                                                                : 0;
                                                            return (
                                                                <div key={j} className="flex items-center gap-2 bg-muted/30 rounded-lg px-3 py-1.5 text-xs">
                                                                    <span className="font-mono font-semibold text-foreground">{split.dim4_kode}</span>
                                                                    <span className="text-muted">{fmt(split.belop)}</span>
                                                                    <span className="bg-amber-100 text-amber-700 rounded px-1 font-medium">{pct} %</span>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                    {/* Visual bar */}
                                                    <div className="mt-2 h-2 rounded-full overflow-hidden flex">
                                                        {item.dim4_splits.map((split, j) => {
                                                            const pct = item.total > 0 ? (split.belop / item.total * 100) : 0;
                                                            const colors = ["bg-blue-400", "bg-amber-400", "bg-purple-400", "bg-green-400", "bg-red-400"];
                                                            return (
                                                                <div key={j}
                                                                    style={{ width: `${pct}%` }}
                                                                    className={`${colors[j % colors.length]} transition-all`}
                                                                    title={`${split.dim4_kode}: ${pct.toFixed(1)} %`}
                                                                />
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="bg-card border border-border rounded-xl p-10 text-center">
                                <button onClick={loadDim4}
                                    className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
                                    <GitBranch size={16} /> Analyser Dim4-splitt {year}
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Avviksanalyse / Mønsterdeteksjon ─────────────────────── */}
                {tab === "avvik" && (
                    <div className="space-y-6">
                        {outliersLoading ? (
                            <div className="bg-card border border-border rounded-xl p-10 text-center text-muted">
                                <RefreshCw size={20} className="animate-spin mx-auto mb-2" />
                                Kjører z-score analyse...
                            </div>
                        ) : outliers ? (
                            <>
                                {/* Summary KPIs */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <KpiCard
                                        title="Totale avvik"
                                        value={String(outliers.summary.total_outliers)}
                                        icon={AlertTriangle}
                                        color={outliers.summary.high_risk > 0 ? "red" : "amber"}
                                    />
                                    <KpiCard
                                        title="Høy risiko"
                                        value={String(outliers.summary.high_risk)}
                                        sub="z-score > 2.5"
                                        icon={XCircle}
                                        color={outliers.summary.high_risk > 0 ? "red" : "green"}
                                    />
                                    <KpiCard
                                        title="Eiendoms-outliers"
                                        value={String(outliers.summary.property_count)}
                                        sub="vs. regionssnitt"
                                        icon={Building2} color="amber"
                                    />
                                    <KpiCard
                                        title="Bilag uten eiendom"
                                        value={String(outliers.summary.orphan_count)}
                                        sub="> 100 000 kr"
                                        icon={AlertTriangle}
                                        color={outliers.summary.orphan_count > 0 ? "red" : "green"}
                                    />
                                </div>

                                {/* Transaction outliers */}
                                {outliers.transaction_outliers.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Transaksjons-outliers (z-score)"
                                            subtitle="Bilag som statistisk avviker fra normalt mønster for sin kontokategori"
                                        />
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b border-border text-xs text-muted uppercase">
                                                        <th className="text-left py-2 pr-4">Leverandør</th>
                                                        <th className="text-left py-2 pr-4">Konto</th>
                                                        <th className="text-right py-2 pr-4">Beløp</th>
                                                        <th className="text-right py-2 pr-4">Snitt kat.</th>
                                                        <th className="text-right py-2 pr-4">Z-score</th>
                                                        <th className="text-center py-2">Risiko</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {outliers.transaction_outliers.slice(0, 20).map((r, i) => (
                                                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                            <td className="py-2 pr-4">
                                                                <div className="font-medium truncate max-w-[180px]">{r.leverandor_navn}</div>
                                                                <div className="text-xs text-muted">{r.dim1_kode} – {r.tekst.slice(0, 40)}</div>
                                                            </td>
                                                            <td className="py-2 pr-4 text-xs text-muted">{r.konto_navn}</td>
                                                            <td className="py-2 pr-4 text-right font-medium">{fmt(r.belop)}</td>
                                                            <td className="py-2 pr-4 text-right text-muted text-xs">{fmt(r.category_avg)}</td>
                                                            <td className="py-2 pr-4 text-right font-mono text-xs">
                                                                {r.z_score > 0 ? "+" : ""}{r.z_score.toFixed(2)}
                                                            </td>
                                                            <td className="py-2 text-center">
                                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                                                    r.risk === "HØY"
                                                                        ? "bg-red-100 text-red-700"
                                                                        : "bg-amber-100 text-amber-700"
                                                                }`}>
                                                                    {r.risk}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Property outliers */}
                                {outliers.property_outliers.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Eiendommer med uvanlig høye kostnader"
                                            subtitle="Sammenlignet med regionalt gjennomsnitt (z-score)"
                                        />
                                        <div className="space-y-2">
                                            {outliers.property_outliers.slice(0, 10).map((r, i) => {
                                                const pct = r.region_avg > 0
                                                    ? ((r.total_2025 - r.region_avg) / r.region_avg * 100)
                                                    : 0;
                                                return (
                                                    <div key={i} className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                                                        <div className="flex-1">
                                                            <Link href={`/properties/${r.property_id}`} className="font-medium hover:text-primary text-sm">
                                                                {r.name}
                                                            </Link>
                                                            <div className="text-xs text-muted">{r.region} · z-score: {r.z_score.toFixed(2)}</div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="font-semibold text-sm">{fmt(r.total_2025)}</div>
                                                            <div className="text-xs text-muted">Snitt: {fmt(r.region_avg)}</div>
                                                        </div>
                                                        <div className={`ml-4 text-sm font-medium w-20 text-right ${pct > 0 ? "text-red-600" : "text-green-600"}`}>
                                                            {pct > 0 ? "+" : ""}{pct.toFixed(0)} %
                                                        </div>
                                                        <span className={`ml-3 text-xs px-2 py-0.5 rounded-full font-medium ${
                                                            r.risk === "HØY"
                                                                ? "bg-red-100 text-red-700"
                                                                : "bg-amber-100 text-amber-700"
                                                        }`}>
                                                            {r.risk}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                {/* YoY outliers */}
                                {outliers.category_yoy_outliers.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Kontoer med stor YoY-endring (> 50 %)"
                                            subtitle="Mulige feilklassifiseringer eller store engangsbeløp"
                                        />
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b border-border text-xs text-muted uppercase">
                                                        <th className="text-left py-2 pr-4">Konto</th>
                                                        <th className="text-right py-2 pr-4">{year - 1}</th>
                                                        <th className="text-right py-2 pr-4">{year}</th>
                                                        <th className="text-right py-2 pr-4">Endring %</th>
                                                        <th className="text-center py-2">Risiko</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {outliers.category_yoy_outliers.slice(0, 15).map((r, i) => (
                                                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                            <td className="py-2 pr-4 font-medium">{r.konto_navn}</td>
                                                            <td className="py-2 pr-4 text-right text-muted">{fmt(r.amt_2024)}</td>
                                                            <td className="py-2 pr-4 text-right">{fmt(r.amt_2025)}</td>
                                                            <td className={`py-2 pr-4 text-right font-medium ${r.change_pct > 0 ? "text-red-600" : "text-green-600"}`}>
                                                                {r.change_pct > 0 ? "+" : ""}{r.change_pct.toFixed(1)} %
                                                            </td>
                                                            <td className="py-2 text-center">
                                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                                                    r.risk === "HØY"
                                                                        ? "bg-red-100 text-red-700"
                                                                        : "bg-amber-100 text-amber-700"
                                                                }`}>
                                                                    {r.risk}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Orphan bilag */}
                                {outliers.orphan_outliers.length > 0 && (
                                    <div className="bg-card border border-border rounded-xl p-5">
                                        <SectionHeader
                                            title="Store bilag uten koblet eiendom"
                                            subtitle="Transaksjoner > 100 000 kr uten property_id – kan ikke allokeres til eiendom"
                                        />
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b border-border text-xs text-muted uppercase">
                                                        <th className="text-left py-2 pr-4">Bilag</th>
                                                        <th className="text-left py-2 pr-4">Leverandør</th>
                                                        <th className="text-left py-2 pr-4">Koststed</th>
                                                        <th className="text-right py-2 pr-4">Beløp</th>
                                                        <th className="text-left py-2">Konto</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {outliers.orphan_outliers.slice(0, 15).map((r, i) => (
                                                        <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                            <td className="py-2 pr-4 font-mono text-xs">{r.bilagsnr}</td>
                                                            <td className="py-2 pr-4 text-sm">{r.leverandor_navn}</td>
                                                            <td className="py-2 pr-4 text-xs text-muted">{r.dim1_kode}</td>
                                                            <td className="py-2 pr-4 text-right font-medium text-amber-700">{fmt(r.belop)}</td>
                                                            <td className="py-2 text-xs text-muted">{r.konto_navn}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {outliers.summary.total_outliers === 0 && (
                                    <div className="bg-card border border-border rounded-xl p-10 text-center">
                                        <CheckCircle2 size={32} className="text-green-600 mx-auto mb-2" />
                                        <div className="text-sm text-muted">Ingen statistiske avvik funnet for {year}</div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="bg-card border border-border rounded-xl p-10 text-center">
                                <button
                                    onClick={loadOutliers}
                                    className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium"
                                >
                                    <BarChart3 size={16} /> Kjør avviksanalyse {year}
                                </button>
                                <p className="text-xs text-muted mt-3">
                                    Z-score analyse av transaksjoner, eiendommer og kontoer
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
