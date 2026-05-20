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

const GREEN = '#00ff41';
const DIM_GREEN = '#00cc33';
const DARK_GREEN = '#003300';

const Card = ({ title, children, className = "", tooltip }: { title: string; children: React.ReactNode; className?: string; tooltip?: string }) => (
    <div className={`bg-black/90 border border-[#00ff4133] rounded p-4 font-mono text-sm ${className}`} style={{ boxShadow: `0 0 10px ${GREEN}20` }}>
        <h3 className="text-[#00ff41] text-xs font-mono uppercase tracking-widest mb-4 border-b border-[#00ff4122] pb-2">
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
    <div className="bg-black/80 border border-[#00ff4122] p-4 rounded flex items-center gap-3 font-mono hover:border-[#00ff4166] transition-all group">
        <div className="p-2 rounded border border-[#00ff4133] text-[#00ff41]">
            <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
            {tooltip ? (
                <DataTooltip content={tooltip}>
                    <p className="text-[#00ff4188] text-xs uppercase tracking-wider cursor-help truncate">{title}</p>
                </DataTooltip>
            ) : (
                <p className="text-[#00ff4188] text-xs uppercase tracking-wider truncate">{title}</p>
            )}
            <div className="flex items-baseline gap-2">
                <h4 className="text-lg font-bold text-[#00ff41] truncate">{value}</h4>
                {trend !== undefined && (
                    <span className={`text-xs shrink-0 ${trend >= 0 ? 'text-[#00ff41]' : 'text-[#ff0044]'}`}>
                        {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
                    </span>
                )}
            </div>
        </div>
    </div>
);

export default function TerminalDashboard() {
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
            <div className="min-h-screen bg-black text-[#00ff41] flex items-center justify-center font-mono">
                <div className="text-center">
                    <p className="animate-pulse">&gt; LOADING_DASHBOARD...</p>
                    <p className="text-[#00ff4166] text-sm mt-2">fetching data from api</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-[#00ff41] p-8 font-mono" style={{ fontFamily: 'ui-monospace, "Cascadia Code", "Fira Code", monospace' }}>
            <header className="mb-8 flex justify-between items-center border-b border-[#00ff4122] pb-6">
                <div>
                    <h1 className="text-2xl font-bold text-[#00ff41]">
                        &gt; BEFS_ANALYTICS_DASHBOARD
                    </h1>
                    <p className="text-[#00ff4188] text-sm mt-1">sanntidsanalyse_av_eiendomsportefolje</p>
                </div>
                <div className="flex gap-2">
                    <Link
                        href="/financials"
                        className="px-4 py-2 border border-[#00ff4155] text-[#00ff41] rounded text-sm hover:bg-[#00ff4111] transition"
                    >
                        [DETALJERT_OKONOMI]
                    </Link>
                    <Link
                        href="/dashboard"
                        className="px-4 py-2 border border-[#00ff4155] text-[#00ff41] rounded text-sm hover:bg-[#00ff4111] transition"
                    >
                        [STANDARD]
                    </Link>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Netto Yield" value={`${netYield.toFixed(1)}%`} icon={Activity} trend={netYield > 0 ? 5.2 : -2.1} tooltip="(Årlig leie − Vedlikehold) ÷ Årlig leie × 100 %" />
                <KPICard title="Aktive Kontrakter" value={stats?.contracts_count || stats?.contracts || 0} icon={FileText} tooltip="Antall leie- og serviceavtaler med status «aktiv»" />
                <KPICard title="Ledighet" value={`${(100 - occupancyRate).toFixed(1)}%`} icon={Zap} trend={occupancyRate > 90 ? 2.3 : -1.5} tooltip="Andel enheter uten aktiv kontrakt" />
                <KPICard title="Eiendommer" value={stats?.properties_count || stats?.properties || 0} icon={Building2} tooltip="Totalt antall eiendommer" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <KPICard title="Total Årlig Leie" value={formatCurrency(totalRent)} icon={Wallet} tooltip="Sum årlig leie" />
                <KPICard title="Total Vedlikehold" value={formatCurrency(totalMaintenance)} icon={HardHat} tooltip="Sum vedlikeholdsutgifter" />
                <KPICard title="Kritiske Risikoer" value={stats?.risks || 0} icon={AlertTriangle} tooltip="Risikovurderinger som krever oppfølging" />
                <KPICard title="Regioner" value={regionalData.length} icon={MapPin} tooltip="Antall regioner" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <Card title="REGIONAL_FINANSIELL_OVERSIKT" className="col-span-2" tooltip="Leie og vedlikehold per region">
                    <div className="h-full w-full pb-4">
                        <ResponsiveContainer width="100%" height={360}>
                            <AreaChart data={regionalChartData}>
                                <defs>
                                    <linearGradient id="tLeie" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={GREEN} stopOpacity={0.5} />
                                        <stop offset="95%" stopColor={GREEN} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="tVedlikehold" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={DIM_GREEN} stopOpacity={0.4} />
                                        <stop offset="95%" stopColor={DIM_GREEN} stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="tNetto" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={GREEN} stopOpacity={0.2} />
                                        <stop offset="95%" stopColor={GREEN} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#00ff4122" vertical={false} />
                                <XAxis dataKey="name" stroke="#00ff4188" style={{ fontSize: '11px', fontFamily: 'inherit' }} />
                                <YAxis stroke="#00ff4188" style={{ fontSize: '11px', fontFamily: 'inherit' }} tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: `1px solid ${GREEN}44`, color: GREEN, borderRadius: '4px', fontFamily: 'inherit' }} formatter={(v: number) => formatCurrency(v)} />
                                <Area type="monotone" dataKey="leie" stroke={GREEN} fill="url(#tLeie)" strokeWidth={1.5} name="Leie" />
                                <Area type="monotone" dataKey="vedlikehold" stroke={DIM_GREEN} fill="url(#tVedlikehold)" strokeWidth={1.5} name="Vedlikehold" />
                                <Area type="monotone" dataKey="netto" stroke={GREEN} fill="url(#tNetto)" strokeWidth={1.5} name="Netto" strokeDasharray="5 5" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </Card>

                <div className="flex flex-col gap-6">
                    <Card title="KOSTNADSKATEGORIER" className="flex-1" tooltip="Fordeling av utgiftskategorier">
                        <div className="h-full min-h-[200px] flex items-center justify-center relative">
                            {pieData.length > 0 ? (
                                <>
                                    <ResponsiveContainer width="100%" height={220}>
                                        <PieChart>
                                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value" stroke="#000" strokeWidth={1}>
                                                {pieData.map((_, i) => (
                                                    <Cell key={i} fill={[GREEN, DIM_GREEN, '#00ff4166', '#00ff4133', '#00ff4122'][i % 5]} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: `1px solid ${GREEN}44`, color: GREEN, fontFamily: 'inherit' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                    <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                                        <span className="text-2xl font-bold text-[#00ff41]">{pieData.length}</span>
                                        <span className="text-xs text-[#00ff4188]">kategorier</span>
                                    </div>
                                </>
                            ) : (
                                <p className="text-[#00ff4166]">no_data</p>
                            )}
                        </div>
                    </Card>

                    <Card title="SYSTEM_STATUS">
                        <div className="flex gap-1 h-24 items-end justify-between">
                            {[65, 80, 45, 90, 55, 70, 85].map((h, i) => (
                                <div key={i} className="flex-1 bg-[#00ff4111] rounded-t border border-[#00ff4122] overflow-hidden">
                                    <div style={{ height: `${h}%` }} className="w-full bg-[#00ff41] rounded-t" />
                                </div>
                            ))}
                        </div>
                        <p className="text-[#00ff4166] text-xs mt-2 text-center">db_performance</p>
                    </Card>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="TOP_LEVERANDORER">
                    {supplierStats && supplierStats.suppliers.length > 0 ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {supplierStats.suppliers.slice(0, 8).map((supplier, idx) => (
                                <div key={idx} className="flex items-center justify-between p-2 border border-[#00ff4111] rounded hover:border-[#00ff4133] transition">
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-[#00ff41] text-sm truncate">{supplier.name}</div>
                                        <div className="text-xs text-[#00ff4188]">{supplier.property_count} eiendommer | {supplier.category}</div>
                                    </div>
                                    <div className="text-right shrink-0 ml-2">
                                        <div className="font-bold text-[#00ff41] text-sm">{formatCurrency(supplier.total_amount)}</div>
                                        <div className="text-xs text-[#00ff4188]">{((supplier.total_amount / supplierStats.total_portfolio_cost) * 100).toFixed(1)}%</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-[#00ff4166]">loading...</p>
                    )}
                </Card>

                <Card title="REGIONAL_SAMMENLIGNING" tooltip="Leie og vedlikehold per region">
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={regionalChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#00ff4122" />
                                <XAxis dataKey="name" stroke="#00ff4188" style={{ fontSize: '10px', fontFamily: 'inherit' }} />
                                <YAxis stroke="#00ff4188" style={{ fontSize: '10px', fontFamily: 'inherit' }} tickFormatter={(v) => formatCurrency(v)} />
                                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', border: `1px solid ${GREEN}44`, color: GREEN, fontFamily: 'inherit' }} formatter={(v: number) => formatCurrency(v)} />
                                <Bar dataKey="leie" fill={GREEN} radius={[2, 2, 0, 0]} name="Leie" />
                                <Bar dataKey="vedlikehold" fill={DIM_GREEN} radius={[2, 2, 0, 0]} name="Vedlikehold" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </Card>
            </div>
        </div>
    );
}
