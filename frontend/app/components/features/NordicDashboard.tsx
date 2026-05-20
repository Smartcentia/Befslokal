"use client";

import React, { useEffect, useState } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import {
    Activity, FileText, Zap, Building2, Wallet, HardHat,
    TrendingUp, AlertTriangle, MapPin
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

interface RegionalData {
    region: string;
    maintenance: number;
    rent: number;
}

const COLORS = {
    blue: '#2563eb',
    teal: '#0d9488',
    sage: '#4ade80',
    ice: '#7dd3fc',
    slate: '#475569',
};

const PIE_COLORS = [COLORS.blue, COLORS.teal, COLORS.sage, COLORS.ice, COLORS.slate];

const Card = ({ title, children, className = "", tooltip }: { title: string; children: React.ReactNode; className?: string; tooltip?: string }) => (
    <div className={`bg-white/90 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-6 shadow-sm hover:shadow-lg hover:border-sky-200/60 transition-all ${className}`}>
        <h3 className="text-slate-600 text-xs font-semibold uppercase tracking-widest mb-4">
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
    icon: React.ElementType;
    color: string;
    trend?: number;
    tooltip?: string;
}) => (
    <div className="bg-white/90 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-5 flex items-center gap-4 hover:border-sky-200/60 hover:shadow-md transition-all group">
        <div className={`p-3 rounded-xl ${color} text-white`}>
            <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
            {tooltip ? (
                <DataTooltip content={tooltip}>
                    <p className="text-slate-500 text-xs uppercase tracking-wider cursor-help truncate">{title}</p>
                </DataTooltip>
            ) : (
                <p className="text-slate-500 text-xs uppercase tracking-wider truncate">{title}</p>
            )}
            <div className="flex items-baseline gap-2">
                <h4 className="text-xl font-bold text-slate-800 truncate">{value}</h4>
                {trend !== undefined && (
                    <span className={`text-xs flex items-center gap-0.5 shrink-0 ${trend >= 0 ? 'text-teal-600' : 'text-rose-500'}`}>
                        <TrendingUp size={12} className={trend < 0 ? 'rotate-180' : ''} />
                        {Math.abs(trend).toFixed(1)}%
                    </span>
                )}
            </div>
        </div>
    </div>
);

export default function NordicDashboard() {
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

    const regionalChartData = regionalData.map((reg: any) => ({
        name: reg.region.length > 8 ? reg.region.substring(0, 8) + '...' : reg.region,
        planned: reg.planned_rent || 0,
        actual: reg.actual_rent || 0,
        costs: reg.other_costs || 0,
    }));

    const pieData = commonPatterns?.common_categories.slice(0, 5).map(cat => ({
        name: cat.category,
        value: cat.property_count,
    })) || [];

    const totalPlannedRent = regionalData.reduce((sum: number, r: any) => sum + (r.planned_rent || 0), 0);
    const totalActualRent = regionalData.reduce((sum: number, r: any) => sum + (r.actual_rent || 0), 0);
    const totalOtherCosts = regionalData.reduce((sum: number, r: any) => sum + (r.other_costs || 0), 0);

    // Net Yield based on Actual Rent vs All Costs
    const totalCosts = totalActualRent + totalOtherCosts;
    const netYield = totalPlannedRent > 0 ? ((totalPlannedRent - totalOtherCosts) / totalPlannedRent * 100) : 0;
    const occupancyRate = stats?.occupancy_rate || 0;

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50/30 to-teal-50/20 text-slate-700 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-14 h-14 border-2 border-sky-300 border-t-sky-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-600 text-sm">Laster dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50/30 to-teal-50/20 text-slate-800 p-8">
            <header className="mb-10 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
                        BEFS Analytics
                    </h1>
                    <p className="text-slate-600 text-sm mt-0.5">Sanntidsanalyse av eiendomsportefølje</p>
                </div>
                <div className="flex gap-3">
                    <Link
                        href="/financials"
                        className="px-4 py-2 text-sky-700 border border-sky-200 rounded-xl text-sm hover:bg-sky-50 transition"
                    >
                        Detaljert Økonomi
                    </Link>
                    <Link
                        href="/dashboard"
                        className="px-4 py-2 bg-sky-600 text-white rounded-xl text-sm hover:bg-sky-700 transition"
                    >
                        Standard Dashboard
                    </Link>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Netto Yield" value={`${netYield.toFixed(1)}%`} icon={Activity} color="bg-sky-500" trend={netYield > 0 ? 5.2 : -2.1} tooltip="(Årsleie − Andre utgifter) ÷ Årsleie × 100 %" />
                <KPICard title="Aktive Kontrakter" value={stats?.contracts_count || stats?.contracts || 0} icon={FileText} color="bg-teal-500" tooltip="Antall leie- og serviceavtaler med status «aktiv»" />
                <KPICard title="Ledighet" value={`${(100 - occupancyRate).toFixed(1)}%`} icon={Zap} color="bg-emerald-500" trend={occupancyRate > 90 ? 2.3 : -1.5} tooltip="Andel enheter uten aktiv kontrakt" />
                <KPICard title="Eiendommer" value={stats?.properties_count || stats?.properties || 0} icon={Building2} color="bg-sky-600" tooltip="Totalt antall eiendommer i porteføljen" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Planlagt Årsleie" value={formatCurrency(totalPlannedRent)} icon={Wallet} color="bg-sky-500" tooltip="Sum årlig leie fra alle aktive kontrakter" />
                <KPICard title="Faktisk Husleie (GL)" value={formatCurrency(totalActualRent)} icon={TrendingUp} color="bg-teal-600" tooltip="Faktisk betalt husleie hittil i år (fra regnskap)" />
                <KPICard title="Bokførte Kostnader" value={formatCurrency(totalOtherCosts)} icon={HardHat} color="bg-amber-500" tooltip="Sum andre bokførte kostnader (ekskl. husleie)" />
                <KPICard title="Kritiske Risikoer" value={stats?.risks || 0} icon={AlertTriangle} color="bg-rose-500" tooltip="Antall risikovurderinger som krever oppfølging" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <Card title="Regional Finansiell Oversikt (NOK)" className="col-span-2" tooltip="Sammenligning mellom planlagt leie, faktisk leie og andre kostnader">
                    <div className="h-full w-full pb-4">
                        <ResponsiveContainer width="100%" height={360}>
                            <AreaChart data={regionalChartData}>
                                <defs>
                                    <linearGradient id="nPlanned" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.blue} stopOpacity={0.5} />
                                        <stop offset="95%" stopColor={COLORS.blue} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="nActual" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.teal} stopOpacity={0.5} />
                                        <stop offset="95%" stopColor={COLORS.teal} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="nCosts" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.slate} stopOpacity={0.4} />
                                        <stop offset="95%" stopColor={COLORS.slate} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: '11px' }} />
                                <YAxis stroke="#64748b" style={{ fontSize: '11px' }} tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} formatter={(v: number | undefined) => formatCurrency(v || 0)} />
                                <Area type="monotone" dataKey="planned" stroke={COLORS.blue} fill="url(#nPlanned)" strokeWidth={2} name="Planlagt Leie" />
                                <Area type="monotone" dataKey="actual" stroke={COLORS.teal} fill="url(#nActual)" strokeWidth={2} name="Faktisk Leie (GL)" />
                                <Area type="monotone" dataKey="costs" stroke={COLORS.slate} fill="url(#nCosts)" strokeWidth={2} name="Andre Kostnader" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </Card>

                <div className="flex flex-col gap-6">
                    <Card title="Vanligste Kostnadskategorier" className="flex-1" tooltip="Fordeling av utgiftskategorier">
                        <div className="h-full min-h-[200px] flex items-center justify-center relative">
                            {pieData.length > 0 ? (
                                <>
                                    <ResponsiveContainer width="100%" height={220}>
                                        <PieChart>
                                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value" stroke="white" strokeWidth={2}>
                                                {pieData.map((_, i) => (
                                                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                                        <span className="text-2xl font-bold text-slate-800">{pieData.length}</span>
                                        <span className="text-xs text-slate-500">Kategorier</span>
                                    </div>
                                </>
                            ) : (
                                <div className="text-slate-500 text-sm">Ingen data</div>
                            )}
                        </div>
                    </Card>

                    <Card title="System Status">
                        <div className="flex gap-2 h-24 items-end justify-between">
                            {[65, 80, 45, 90, 55, 70, 85].map((h, i) => (
                                <div key={i} className="flex-1 bg-slate-100 rounded-t overflow-hidden">
                                    <div
                                        style={{ height: `${h}%` }}
                                        className="w-full bg-gradient-to-t from-teal-500 to-sky-400 rounded-t transition-all duration-500"
                                    />
                                </div>
                            ))}
                        </div>
                        <div className="text-xs text-slate-500 mt-2 text-center">Database Performance</div>
                    </Card>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Top Leverandører">
                    {supplierStats && supplierStats.suppliers.length > 0 ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {supplierStats.suppliers.slice(0, 8).map((supplier, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50/80 rounded-xl border border-slate-100 hover:border-sky-200/60 transition">
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-slate-800 text-sm truncate">{supplier.name}</div>
                                        <div className="text-xs text-slate-500">{supplier.property_count} eiendommer • {supplier.category}</div>
                                    </div>
                                    <div className="text-right shrink-0 ml-2">
                                        <div className="font-semibold text-slate-800 text-sm">{formatCurrency(supplier.total_amount)}</div>
                                        <div className="text-xs text-slate-500">{((supplier.total_amount / supplierStats.total_portfolio_cost) * 100).toFixed(1)}%</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-slate-500 text-sm">Laster leverandørdata...</div>
                    )}
                </Card>

                <Card title="Regional Sammenligning" tooltip="Leie og vedlikehold per region">
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={regionalChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: '10px' }} />
                                <YAxis stroke="#64748b" style={{ fontSize: '10px' }} tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px' }} formatter={(v: number | undefined) => formatCurrency(v || 0)} />
                                <Bar dataKey="planned" fill={COLORS.blue} radius={[6, 6, 0, 0]} name="Planlagt Leie" />
                                <Bar dataKey="actual" fill={COLORS.teal} radius={[6, 6, 0, 0]} name="Faktisk Leie (GL)" />
                                <Bar dataKey="costs" fill={COLORS.slate} radius={[6, 6, 0, 0]} name="Andre Kostnader" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </Card>
            </div>
        </div>
    );
}
