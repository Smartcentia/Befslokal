"use client";

import React, { useEffect, useState } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import {
    Activity, Globe, Zap, Server, Building2, Wallet, HardHat,
    TrendingUp, AlertTriangle, FileText, Users, MapPin
} from 'lucide-react';
import DataTooltip from '@/app/components/ui/DataTooltip';
import {
    getDashboardStats,
    getRegionalFinancials,
    DashboardStatsData,
    financialAnalysisApi,
    CommonPatterns,
    SupplierStats
} from '@/lib/api';
import Link from 'next/link';

// Cyberpunk color palette
const COLORS = {
    cyan: '#06b6d4',
    purple: '#8b5cf6',
    emerald: '#10b981',
    pink: '#ec4899',
    amber: '#f59e0b',
};

const CYBER_COLORS = [COLORS.cyan, COLORS.purple, COLORS.emerald, COLORS.pink];

interface RegionalData {
    region: string;
    maintenance: number;
    rent: number;
}

const Card = ({ title, children, className = "", tooltip }: { title: string; children: React.ReactNode; className?: string; tooltip?: string }) => (
    <div className={`bg-slate-800/50 backdrop-blur-md border border-slate-700/50 rounded-xl p-5 shadow-lg shadow-cyan-500/5 ${className}`}>
        <h3 className="text-white text-base font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
            {tooltip ? (
                <DataTooltip content={tooltip}>
                    <span className="cursor-help">{title}</span>
                </DataTooltip>
            ) : (
                title
            )}
        </h3>
        {children}
    </div>
);

const KPICard = ({ title, value, icon: Icon, color, trend, tooltip }: {
    title: string;
    value: string | number;
    icon: any;
    color: string;
    trend?: number;
    tooltip?: string;
}) => (
    <div className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/30 flex items-center gap-4 hover:border-cyan-500/50 transition-all group">
        <div className={`p-3 rounded-lg bg-opacity-20 ${color} group-hover:shadow-lg group-hover:shadow-cyan-500/20 transition-all`}>
            <Icon className={`w-6 h-6 ${color.replace('bg-', 'text-')}`} />
        </div>
        <div className="flex-1">
            {tooltip ? (
                <DataTooltip content={tooltip}>
                    <p className="text-slate-400 text-xs uppercase tracking-wider cursor-help">{title}</p>
                </DataTooltip>
            ) : (
                <p className="text-slate-400 text-xs uppercase tracking-wider">{title}</p>
            )}
            <div className="flex items-baseline gap-2">
                <h4 className="text-2xl font-bold text-white">{value}</h4>
                {trend !== undefined && (
                    <span className={`text-xs flex items-center gap-1 ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        <TrendingUp size={12} className={trend < 0 ? 'rotate-180' : ''} />
                        {Math.abs(trend).toFixed(1)}%
                    </span>
                )}
            </div>
        </div>
    </div>
);

export default function CyberpunkDashboard() {
    const [stats, setStats] = useState<DashboardStatsData | null>(null);
    const [regionalData, setRegionalData] = useState<RegionalData[]>([]);
    const [commonPatterns, setCommonPatterns] = useState<CommonPatterns | null>(null);
    const [supplierStats, setSupplierStats] = useState<SupplierStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            try {
                const [dashboardStats, regional, patterns, suppliers] = await Promise.all([
                    getDashboardStats(),
                    getRegionalFinancials(),
                    financialAnalysisApi.getCommonPatterns().catch(() => null),
                    financialAnalysisApi.getSupplierStats().catch(() => null),
                ]);

                setStats(dashboardStats);
                setRegionalData(regional as RegionalData[]);
                setCommonPatterns(patterns);
                setSupplierStats(suppliers);
            } catch (err) {
                console.error("Failed to load dashboard data", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    const formatCurrency = (amount: number) => {
        if (amount > 1000000) return `${(amount / 1000000).toFixed(1)} MNOK`;
        if (amount > 1000) return `${(amount / 1000).toFixed(0)} kNOK`;
        return `${amount.toFixed(0)} NOK`;
    };

    // Prepare chart data
    const regionalChartData = regionalData.map(reg => ({
        name: reg.region.length > 8 ? reg.region.substring(0, 8) + '...' : reg.region,
        leie: reg.rent,
        vedlikehold: reg.maintenance,
        netto: reg.rent - reg.maintenance,
    }));

    const pieData = commonPatterns?.common_categories.slice(0, 5).map(cat => ({
        name: cat.category,
        value: cat.property_count,
    })) || [];

    // Calculate KPIs
    const totalRent = stats?.total_annual_rent || regionalData.reduce((sum, r) => sum + r.rent, 0);
    const totalMaintenance = stats?.total_maintenance_cost || regionalData.reduce((sum, r) => sum + r.maintenance, 0);
    const netYield = totalRent > 0 ? ((totalRent - totalMaintenance) / totalRent * 100) : 0;
    const occupancyRate = stats?.occupancy_rate || 0;

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0b1120] text-white flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-400">Laster dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0b1120] text-white p-8 font-sans">
            {/* HEADER */}
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-linear-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                        BEFS ANALYTICS DASHBOARD
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">Sanntidsanalyse av eiendomsportefølje</p>
                </div>
                <div className="flex gap-4">
                    <Link
                        href="/financials"
                        className="px-4 py-2 bg-cyan-500/10 text-cyan-400 border border-cyan-500/50 rounded-lg text-sm hover:bg-cyan-500/20 transition"
                    >
                        Detaljert Økonomi
                    </Link>
                    <Link
                        href="/dashboard"
                        className="px-4 py-2 bg-purple-500/10 text-purple-400 border border-purple-500/50 rounded-lg text-sm hover:bg-purple-500/20 transition"
                    >
                        Standard Dashboard
                    </Link>
                </div>
            </header>

            {/* TOP KPI ROW */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <KPICard
                    title="Netto Yield"
                    value={`${netYield.toFixed(1)}%`}
                    icon={Activity}
                    color="bg-cyan-500 text-cyan-400"
                    trend={netYield > 0 ? 5.2 : -2.1}
                    tooltip="(Årlig leie − Vedlikehold) ÷ Årlig leie × 100 %. Viser avkastning på porteføljen."
                />
                <KPICard
                    title="Aktive Kontrakter"
                    value={stats?.contracts_count || stats?.contracts || 0}
                    icon={FileText}
                    color="bg-purple-500 text-purple-400"
                    tooltip="Antall leie- og serviceavtaler med status «aktiv»."
                />
                <KPICard
                    title="Ledighet"
                    value={`${(100 - occupancyRate).toFixed(1)}%`}
                    icon={Zap}
                    color="bg-emerald-500 text-emerald-400"
                    trend={occupancyRate > 90 ? 2.3 : -1.5}
                    tooltip="Andel enheter uten aktiv kontrakt. 100 − beleggsgrad."
                />
                <KPICard
                    title="Eiendommer"
                    value={stats?.properties_count || stats?.properties || 0}
                    icon={Building2}
                    color="bg-pink-500 text-pink-400"
                    tooltip="Totalt antall eiendommer i porteføljen."
                />
            </div>

            {/* SECONDARY KPI ROW */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <KPICard
                    title="Total Årlig Leie"
                    value={formatCurrency(totalRent)}
                    icon={Wallet}
                    color="bg-cyan-500 text-cyan-400"
                    tooltip="Sum årlig leie fra alle aktive kontrakter i porteføljen."
                />
                <KPICard
                    title="Total Vedlikehold"
                    value={formatCurrency(totalMaintenance)}
                    icon={HardHat}
                    color="bg-amber-500 text-amber-400"
                    tooltip="Sum bokførte vedlikeholds- og driftsutgifter (regnskap + manuelle poster)."
                />
                <KPICard
                    title="Kritiske Risikoer"
                    value={stats?.risks || 0}
                    icon={AlertTriangle}
                    color="bg-red-500 text-red-400"
                    tooltip="Antall risikovurderinger som krever oppfølging."
                />
                <KPICard
                    title="Regioner"
                    value={regionalData.length}
                    icon={MapPin}
                    color="bg-purple-500 text-purple-400"
                    tooltip="Antall regioner i porteføljen (Nord, Midt-Norge, Vest, Sør, Bufdir)."
                />
            </div>

            {/* MAIN GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

                {/* CHART 1: Regional Financial Overview */}
                <Card
                    title="Regional Finansiell Oversikt (NOK)"
                    className="col-span-2"
                    tooltip="Leie (blå) og vedlikehold (oransje) per region. Netto = Leie − Vedlikehold. Data fra aktive kontrakter og regnskap."
                >
                    <div className="h-full w-full pb-6">
                        <ResponsiveContainer width="100%" height={400}>
                            <AreaChart data={regionalChartData}>
                                <defs>
                                    <linearGradient id="colorLeie" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.cyan} stopOpacity={0.8} />
                                        <stop offset="95%" stopColor={COLORS.cyan} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorVedlikehold" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.amber} stopOpacity={0.8} />
                                        <stop offset="95%" stopColor={COLORS.amber} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorNetto" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.emerald} stopOpacity={0.8} />
                                        <stop offset="95%" stopColor={COLORS.emerald} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis
                                    dataKey="name"
                                    stroke="#ffffff"
                                    tick={{ fill: '#ffffff', fontSize: 14 }}
                                />
                                <YAxis
                                    stroke="#ffffff"
                                    tick={{ fill: '#ffffff', fontSize: 14 }}
                                    tickFormatter={(value) => formatCurrency(value)}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1e293b',
                                        borderColor: COLORS.cyan,
                                        color: '#ffffff',
                                        fontSize: 14,
                                        borderRadius: '8px',
                                        boxShadow: `0 0 20px ${COLORS.cyan}40`
                                    }}
                                    formatter={(value: number) => formatCurrency(value)}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="leie"
                                    stroke={COLORS.cyan}
                                    fillOpacity={1}
                                    fill="url(#colorLeie)"
                                    strokeWidth={2}
                                    name="Leie"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="vedlikehold"
                                    stroke={COLORS.amber}
                                    fillOpacity={1}
                                    fill="url(#colorVedlikehold)"
                                    strokeWidth={2}
                                    name="Vedlikehold"
                                />
                                <Area
                                    type="monotone"
                                    dataKey="netto"
                                    stroke={COLORS.emerald}
                                    fillOpacity={1}
                                    fill="url(#colorNetto)"
                                    strokeWidth={2}
                                    name="Netto"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </Card>

                {/* SIDE BAR: Pie Chart & Mini Stats */}
                <div className="flex flex-col gap-6">
                    <Card
                        title="Vanligste Kostnadskategorier"
                        className="flex-1"
                        tooltip="Fordeling av utgiftskategorier (f.eks. vedlikehold, strøm, fellesutgifter) på tvers av eiendommer. Størrelse = antall eiendommer med kategorien."
                    >
                        <div className="h-full w-full flex items-center justify-center relative">
                            {pieData.length > 0 ? (
                                <>
                                    <ResponsiveContainer width="100%" height={250}>
                                        <PieChart>
                                            <Pie
                                                data={pieData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={90}
                                                paddingAngle={3}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                {pieData.map((entry, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={CYBER_COLORS[index % CYBER_COLORS.length]}
                                                        style={{ filter: `drop-shadow(0 0 8px ${CYBER_COLORS[index % CYBER_COLORS.length]}80)` }}
                                                    />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: '#1e293b',
                                                    borderColor: COLORS.purple,
                                                    color: '#fff',
                                                    borderRadius: '8px'
                                                }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                                        <span className="text-3xl font-bold text-white">{pieData.length}</span>
                                        <span className="text-xs text-slate-400">Kategorier</span>
                                    </div>
                                </>
                            ) : (
                                <div className="text-slate-400 text-sm">Ingen data tilgjengelig</div>
                            )}
                        </div>
                    </Card>

                    <Card title="System Status" className="h-1/3">
                        <div className="flex gap-2 h-full items-end pb-4 justify-between">
                            {[65, 80, 45, 90, 55, 70, 85].map((h, i) => (
                                <div key={i} className="w-full bg-slate-700/50 rounded-t-sm relative group">
                                    <div
                                        style={{ height: `${h}%` }}
                                        className="absolute bottom-0 w-full bg-gradient-to-t from-emerald-500 to-cyan-400 rounded-t-sm transition-all duration-500 group-hover:opacity-110 shadow-[0_0_10px_rgba(52,211,153,0.5)]"
                                    ></div>
                                </div>
                            ))}
                        </div>
                        <div className="text-xs text-slate-400 mt-2 text-center">Database Performance</div>
                    </Card>
                </div>
            </div>

            {/* BOTTOM ROW: Supplier Stats & Regional Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Suppliers */}
                <Card title="Top Leverandører">
                    {supplierStats && supplierStats.suppliers.length > 0 ? (
                        <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
                            {supplierStats.suppliers.slice(0, 8).map((supplier, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:border-cyan-500/50 transition-all group"
                                >
                                    <div className="flex-1">
                                        <div className="font-medium text-white text-sm group-hover:text-cyan-400 transition-colors">
                                            {supplier.name}
                                        </div>
                                        <div className="text-xs text-slate-400">
                                            {supplier.property_count} eiendommer • {supplier.category}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-bold text-white">{formatCurrency(supplier.total_amount)}</div>
                                        <div className="text-xs text-slate-400">
                                            {((supplier.total_amount / supplierStats.total_portfolio_cost) * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-slate-400 text-sm">Laster leverandørdata...</div>
                    )}
                </Card>

                {/* Regional Breakdown Bar Chart */}
                <Card
                    title="Regional Sammenligning"
                    tooltip="Leie (blå) og vedlikehold (oransje) per region. Lav leie kan skyldes få aktive kontrakter i regionen."
                >
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={regionalChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis
                                    dataKey="name"
                                    stroke="#ffffff"
                                    tick={{ fill: '#ffffff', fontSize: 14 }}
                                />
                                <YAxis
                                    stroke="#ffffff"
                                    tick={{ fill: '#ffffff', fontSize: 14 }}
                                    tickFormatter={(value) => formatCurrency(value)}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1e293b',
                                        borderColor: COLORS.purple,
                                        color: '#ffffff',
                                        fontSize: 14,
                                        borderRadius: '8px'
                                    }}
                                    formatter={(value: number) => formatCurrency(value)}
                                />
                                <Bar
                                    dataKey="leie"
                                    fill={COLORS.cyan}
                                    radius={[4, 4, 0, 0]}
                                    name="Leie"
                                />
                                <Bar
                                    dataKey="vedlikehold"
                                    fill={COLORS.amber}
                                    radius={[4, 4, 0, 0]}
                                    name="Vedlikehold"
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </Card>
            </div>
        </div>
    );
}
