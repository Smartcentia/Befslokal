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

const COLORS = ['#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0', '#f1f5f9'];

const Card = ({ title, children, className = "", tooltip }: { title: string; children: React.ReactNode; className?: string; tooltip?: string }) => (
    <div className={`bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow ${className}`}>
        <h3 className="text-slate-500 text-xs font-medium uppercase tracking-widest mb-4">
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

const KPICard = ({ title, value, icon: Icon, trend, tooltip }: {
    title: string;
    value: string | number;
    icon: React.ElementType;
    trend?: number;
    tooltip?: string;
}) => (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 flex items-center gap-4 hover:border-slate-300 transition-colors group">
        <div className="p-2.5 rounded-xl bg-slate-100 text-slate-600 group-hover:bg-slate-200 transition-colors">
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
                <h4 className="text-xl font-semibold text-slate-900 truncate">{value}</h4>
                {trend !== undefined && (
                    <span className={`text-xs flex items-center gap-0.5 shrink-0 ${trend >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        <TrendingUp size={12} className={trend < 0 ? 'rotate-180' : ''} />
                        {Math.abs(trend).toFixed(1)}%
                    </span>
                )}
            </div>
        </div>
    </div>
);

export default function MinimalistDashboard() {
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

    const totalRent = stats?.total_annual_rent || regionalData.reduce((sum, r) => sum + r.rent, 0);
    const totalMaintenance = stats?.total_maintenance_cost || regionalData.reduce((sum, r) => sum + r.maintenance, 0);
    const netYield = totalRent > 0 ? ((totalRent - totalMaintenance) / totalRent * 100) : 0;
    const occupancyRate = stats?.occupancy_rate || 0;

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 text-slate-700 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-500 text-sm">Laster dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
            <header className="mb-10 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
                        BEFS Analytics
                    </h1>
                    <p className="text-slate-500 text-sm mt-0.5">Sanntidsanalyse av eiendomsportefølje</p>
                </div>
                <div className="flex gap-3">
                    <Link
                        href="/financials"
                        className="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg text-sm hover:bg-white hover:border-slate-400 transition"
                    >
                        Detaljert Økonomi
                    </Link>
                    <Link
                        href="/dashboard"
                        className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 transition"
                    >
                        Standard Dashboard
                    </Link>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Netto Yield" value={`${netYield.toFixed(1)}%`} icon={Activity} trend={netYield > 0 ? 5.2 : -2.1} tooltip="(Årlig leie − Vedlikehold) ÷ Årlig leie × 100 %" />
                <KPICard title="Aktive Kontrakter" value={stats?.contracts_count || stats?.contracts || 0} icon={FileText} tooltip="Antall leie- og serviceavtaler med status «aktiv»" />
                <KPICard title="Ledighet" value={`${(100 - occupancyRate).toFixed(1)}%`} icon={Zap} trend={occupancyRate > 90 ? 2.3 : -1.5} tooltip="Andel enheter uten aktiv kontrakt" />
                <KPICard title="Eiendommer" value={stats?.properties_count || stats?.properties || 0} icon={Building2} tooltip="Totalt antall eiendommer i porteføljen" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Total Årlig Leie" value={formatCurrency(totalRent)} icon={Wallet} tooltip="Sum årlig leie fra alle aktive kontrakter" />
                <KPICard title="Total Vedlikehold" value={formatCurrency(totalMaintenance)} icon={HardHat} tooltip="Sum vedlikeholds- og driftsutgifter" />
                <KPICard title="Kritiske Risikoer" value={stats?.risks || 0} icon={AlertTriangle} tooltip="Antall risikovurderinger som krever oppfølging" />
                <KPICard title="Regioner" value={regionalData.length} icon={MapPin} tooltip="Antall regioner i porteføljen" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <Card title="Regional Finansiell Oversikt (NOK)" className="col-span-2" tooltip="Leie og vedlikehold per region">
                    <div className="h-full w-full pb-4">
                        <ResponsiveContainer width="100%" height={360}>
                            <AreaChart data={regionalChartData}>
                                <defs>
                                    <linearGradient id="mLeie" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="mVedlikehold" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#64748b" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#64748b" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="mNetto" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0f172a" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#0f172a" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                                <XAxis dataKey="name" stroke="#64748b" style={{ fontSize: '11px' }} />
                                <YAxis stroke="#64748b" style={{ fontSize: '11px' }} tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} formatter={(v: number) => formatCurrency(v)} />
                                <Area type="monotone" dataKey="leie" stroke="#94a3b8" fill="url(#mLeie)" strokeWidth={1.5} name="Leie" />
                                <Area type="monotone" dataKey="vedlikehold" stroke="#64748b" fill="url(#mVedlikehold)" strokeWidth={1.5} name="Vedlikehold" />
                                <Area type="monotone" dataKey="netto" stroke="#0f172a" fill="url(#mNetto)" strokeWidth={1.5} name="Netto" />
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
                                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                                                {pieData.map((_, i) => (
                                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                                        <span className="text-2xl font-semibold text-slate-900">{pieData.length}</span>
                                        <span className="text-xs text-slate-500">Kategorier</span>
                                    </div>
                                </>
                            ) : (
                                <div className="text-slate-500 text-sm">Ingen data</div>
                            )}
                        </div>
                    </Card>

                    <Card title="System Status">
                        <div className="flex gap-1.5 h-24 items-end justify-between">
                            {[65, 80, 45, 90, 55, 70, 85].map((h, i) => (
                                <div key={i} className="flex-1 bg-slate-200 rounded-t overflow-hidden">
                                    <div style={{ height: `${h}%` }} className="w-full bg-slate-400 rounded-t transition-all duration-500" />
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
                                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 hover:border-slate-200 transition">
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-slate-900 text-sm truncate">{supplier.name}</div>
                                        <div className="text-xs text-slate-500">{supplier.property_count} eiendommer • {supplier.category}</div>
                                    </div>
                                    <div className="text-right shrink-0 ml-2">
                                        <div className="font-semibold text-slate-900 text-sm">{formatCurrency(supplier.total_amount)}</div>
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
                                <Tooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }} formatter={(v: number) => formatCurrency(v)} />
                                <Bar dataKey="leie" fill="#94a3b8" radius={[4, 4, 0, 0]} name="Leie" />
                                <Bar dataKey="vedlikehold" fill="#64748b" radius={[4, 4, 0, 0]} name="Vedlikehold" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </Card>
            </div>
        </div>
    );
}
