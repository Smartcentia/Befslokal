"use client";

import React, { useEffect, useState } from 'react';
import { deviationService, Deviation } from '@/lib/domains/fdv/deviationService';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { fetchAPI } from '@/lib/api/client';
import { AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface Stats {
    total: number;
    open: number;
    closed: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
}

export default function AdminDeviationDashboard() {


    const [stats, setStats] = useState<Stats>({
        total: 0,
        open: 0,
        closed: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
    });
    const [loading, setLoading] = useState(true);
    const [externalStats, setExternalStats] = useState<any>(null);
    const [deviations, setDeviations] = useState<any[]>([]);
    const [measures, setMeasures] = useState<any[]>([]);
    const [activeTab, setActiveTab] = useState<'overview' | 'deviations' | 'measures' | 'evolution'>('overview');
    const [generatedTools, setGeneratedTools] = useState<any[]>([]);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                // Always load basic stats
                const statsData = await deviationService.getStats();
                if (statsData) setStats(statsData);

                try {
                    // Try to fetch external stats if endpoint exists
                    const extData = await fetchAPI('/risk/stats/external');
                    if (extData) setExternalStats(extData);
                } catch (err) {
                    console.warn("Could not fetch external stats:", err);
                }

                // Load lists if needed (or pre-load all for simplicity in this admin view)
                // In a real app we'd paginate, but for now fetch all
                const allDeviations = await deviationService.getAll(1, 100);
                setDeviations(allDeviations || []);

                // Fetch Measures (Internal Control Cases)
                try {
                    const measuresData = await fetchAPI('/internal-control/cases');
                    if (measuresData) setMeasures(measuresData);
                } catch (e) {
                    console.warn("Could not fetch measures", e);
                }

                // Fetch Generated Tools (Evolution)
                try {
                    const toolsData = await fetchAPI('/admin/evolution/tools');
                    if (toolsData) setGeneratedTools(toolsData);
                } catch (e) {
                    console.warn("Could not fetch generated tools", e);
                }

            } catch (e) {
                console.error("Failed to load dashboard data", e);
            }
            setLoading(false);
        };
        load();
    }, []);

    const approveTool = async (toolId: string) => {
        if (!confirm("Er du sikker på at du vil godkjenne dette verktøyet?")) return;
        try {
            await fetchAPI(`/admin/evolution/tools/${toolId}/approve`, { method: 'POST' });
            alert("Verktøy godkjent! (Krever restart av backend for å tre i kraft)");
            // Refresh list
            const toolsData = await fetchAPI('/admin/evolution/tools');
            if (toolsData) setGeneratedTools(toolsData);
        } catch (error) {
            console.error("Failed to approve tool", error);
            alert("Feilet å godkjenne verktøy");
        }
    };

    const statusData = [
        { name: 'Åpne', value: stats.open, color: '#F59E0B' },   // Amber
        { name: 'Lukket', value: stats.closed, color: '#10B981' }, // Emerald
    ];

    const severityData = [
        { name: 'Kritisk', value: stats.critical, color: '#EF4444' }, // Red
        { name: 'Høy', value: stats.high, color: '#F59E0B' },       // Amber
        { name: 'Middels', value: stats.medium, color: '#3B82F6' }, // Blue
        { name: 'Lav', value: stats.low, color: '#64748B' },        // Slate
    ];

    if (loading) return <div className="p-8 text-center text-muted animate-pulse">Laster systemoversikt...</div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                    <AlertTriangle className="text-blue-500" />
                    HMS & Internkontroll
                </h2>

                {/* Tabs */}
                <div className="flex bg-surface/50 p-1 rounded-lg border border-border">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-primary text-white shadow' : 'text-muted hover:text-foreground'}`}
                    >
                        Oversikt (Dashboard)
                    </button>
                    <button
                        onClick={() => setActiveTab('deviations')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'deviations' ? 'bg-primary text-white shadow' : 'text-muted hover:text-foreground'}`}
                    >
                        Alle Avvik ({deviations.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('measures')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'measures' ? 'bg-primary text-white shadow' : 'text-muted hover:text-foreground'}`}
                    >
                        Alle Tiltak ({measures.length})
                    </button>
                    <button
                        onClick={() => setActiveTab('evolution')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'evolution' ? 'bg-purple-600 text-white shadow' : 'text-muted hover:text-foreground'}`}
                    >
                        ✨ Self-Evolution ({generatedTools.filter(t => t.status === 'pending').length})
                    </button>
                </div>
            </div>

            {/* TAB: OVERVIEW */}
            {activeTab === 'overview' && (
                <div className="space-y-6 animate-in fade-in duration-300">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-surface p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
                            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
                                <AlertTriangle size={24} />
                            </div>
                            <div>
                                <div className="text-sm text-muted font-medium">Totalt Avvik</div>
                                <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                            </div>
                        </div>
                        <div className="bg-surface p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
                            <div className="p-3 bg-amber-500/10 text-amber-500 rounded-lg">
                                <Clock size={24} />
                            </div>
                            <div>
                                <div className="text-sm text-muted font-medium">Åpne Saker</div>
                                <div className="text-2xl font-bold text-foreground">{stats.open}</div>
                            </div>
                        </div>
                        <div className="bg-surface p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
                            <div className="p-3 bg-red-500/10 text-red-500 rounded-lg">
                                <AlertTriangle size={24} />
                            </div>
                            <div>
                                <div className="text-sm text-muted font-medium">Kritiske</div>
                                <div className="text-2xl font-bold text-foreground">{stats.critical}</div>
                            </div>
                        </div>
                        <div className="bg-surface p-4 rounded-xl border border-border shadow-sm flex items-center gap-4">
                            <div className="p-3 bg-purple-500/10 text-purple-500 rounded-lg">
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            </div>
                            <div>
                                <div className="text-sm text-muted font-medium">Naturfare (NVE)</div>
                                <div className="text-2xl font-bold text-foreground">{externalStats?.total_external_issues || 0}</div>
                            </div>
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="glass-card p-6 rounded-xl border border-border">
                            <h3 className="font-semibold text-foreground mb-6">Saksstatus Fordeling</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={statusData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={80}
                                            paddingAngle={5}
                                            dataKey="value"
                                            stroke="none"
                                        >
                                            {statusData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', color: 'var(--foreground)' }}
                                            itemStyle={{ color: 'var(--foreground)' }}
                                        />
                                        <Legend wrapperStyle={{ color: 'var(--text-muted)' }} />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="glass-card p-6 rounded-xl border border-border">
                            <h3 className="font-semibold text-foreground mb-6">Alvorlighetsgrad</h3>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={severityData}>
                                        <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                                        <Tooltip
                                            cursor={{ fill: 'var(--bg-overlay)' }}
                                            contentStyle={{ backgroundColor: 'var(--bg-surface)', borderColor: 'var(--border-color)', color: 'var(--foreground)' }}
                                        />
                                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                            {severityData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* External Risk Details */}
                    {externalStats && (
                        <div className="glass-card p-6 rounded-xl border border-border">
                            <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                Naturfare & Ekstern Risiko (NVE)
                            </h3>
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                <div className="bg-surface/50 p-3 rounded-lg border border-border">
                                    <span className="font-medium text-muted">Kartverket (Geo)</span>
                                    <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full font-bold border border-green-500/30">TILKOBLET (GEONORGE)</span>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-border">
                                    <div className="text-xs text-muted">Flomfare</div>
                                    <div className="text-xl font-bold text-blue-400">{externalStats.by_category?.flood || 0}</div>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-border">
                                    <div className="text-xs text-muted">Skredfare</div>
                                    <div className="text-xl font-bold text-amber-400">{externalStats.by_category?.landslide || 0}</div>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-border">
                                    <div className="text-xs text-muted">Stasjoner</div>
                                    <div className="text-xl font-bold text-cyan-400">{externalStats.by_category?.nve_proximity || 0}</div>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-border">
                                    <div className="text-xs text-muted">Eldre Bygg</div>
                                    <div className="text-xl font-bold text-foreground">{externalStats.by_category?.building_age || 0}</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* TAB: DEVIATIONS LIST */}
            {activeTab === 'deviations' && (
                <div className="glass-card p-0 rounded-xl border border-border overflow-hidden animate-in fade-in duration-300">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-surface/50 border-b border-border">
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Avvik / Risiko</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Eiendom</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Alvorlighet</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Status</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Dato</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {deviations.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted">
                                            Ingen avvik funnet.
                                        </td>
                                    </tr>
                                )}
                                {deviations.map((item) => (
                                    <tr key={item.id} className="hover:bg-surface/30 transition-colors">
                                        <td className="p-4">
                                            <div className="font-medium text-foreground">{item.title}</div>
                                            <div className="text-xs text-muted table-cell-subtitle">{item.id}</div>
                                        </td>
                                        <td className="p-4 text-muted">
                                            {item.property_name || <span className="text-muted italic">Ukjent</span>}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-medium 
                                                ${item.severity.toLowerCase() === 'critical' ? 'bg-red-500/20 text-red-500 border border-red-500/20' :
                                                    item.severity.toLowerCase() === 'high' ? 'bg-amber-500/20 text-amber-500 border border-amber-500/20' :
                                                        'bg-blue-500/20 text-blue-500 border border-blue-500/20'}`}>
                                                {item.severity}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <span className={`flex items-center gap-1.5 text-xs font-medium ${item.status === 'CLOSED' ? 'text-green-500' : 'text-muted'}`}>
                                                <span className={`w-1.5 h-1.5 rounded-full ${item.status === 'CLOSED' ? 'bg-green-500' : 'bg-muted-foreground'}`} />
                                                {item.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-muted text-sm">
                                            {new Date(item.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* TAB: MEASURES LIST */}
            {activeTab === 'measures' && (
                <div className="glass-card p-0 rounded-xl border border-border overflow-hidden animate-in fade-in duration-300">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-surface/50 border-b border-border">
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Tiltak / Oppgave</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Eiendom</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Prioritet</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Frist</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {measures.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted">
                                            Ingen tiltak registrert.
                                        </td>
                                    </tr>
                                )}
                                {measures.map((item) => (
                                    <tr key={item.case_id} className="hover:bg-surface/30 transition-colors">
                                        <td className="p-4">
                                            <div className="font-medium text-foreground">{item.title}</div>
                                            <div className="text-xs text-muted max-w-xs truncate">{item.description}</div>
                                        </td>
                                        <td className="p-4 text-muted">
                                            {item.property?.address || (item.property_id && <span className="text-xs text-muted">{item.property_id.substring(0, 8)}...</span>) || <span className="text-muted italic">Ukjent</span>}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-medium uppercase
                                                ${item.priority.toLowerCase() === 'high' ? 'bg-red-500/10 text-red-500' :
                                                    'bg-muted/20 text-muted'}`}>
                                                {item.priority}
                                            </span>
                                        </td>
                                        <td className="p-4 text-muted text-sm">
                                            {item.due_date ? new Date(item.due_date).toLocaleDateString() : '-'}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-0.5 rounded text-xs font-bold border border-border ${item.status === 'open' ? 'bg-blue-500/10 text-blue-500' : 'bg-green-500/10 text-green-500'}`}>
                                                {item.status.toUpperCase()}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* TAB: SELF-EVOLUTION */}
            {activeTab === 'evolution' && (
                <div className="glass-card p-0 rounded-xl border border-border overflow-hidden animate-in fade-in duration-300">
                    <div className="p-4 bg-surface/50 border-b border-border flex justify-between items-center">
                        <div>
                            <h3 className="font-semibold text-foreground flex items-center gap-2">
                                ✨ Candidate Tools (Auto-Generated)
                            </h3>
                            <p className="text-xs text-muted">Verktøy generert av AI Creator Agent basert på faktiske brukerspørsmål.</p>
                        </div>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-surface/50 border-b border-border">
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Navn</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Beskrivelse</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Status</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Opprettet</th>
                                    <th className="p-4 text-xs font-semibold text-muted uppercase tracking-wider">Handling</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {generatedTools.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-muted">
                                            Ingen verktøy generert ennå.
                                        </td>
                                    </tr>
                                )}
                                {generatedTools.map((tool) => (
                                    <tr key={tool.tool_id} className="hover:bg-surface/30 transition-colors">
                                        <td className="p-4 font-mono text-sm text-blue-400">
                                            {tool.name}
                                        </td>
                                        <td className="p-4 text-sm text-foreground max-w-md">
                                            {tool.description}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-medium uppercase
                                                ${tool.status === 'pending' ? 'bg-amber-500/20 text-amber-500 border border-amber-500/20' :
                                                    tool.status === 'active' ? 'bg-green-500/20 text-green-500 border border-green-500/20' :
                                                        'bg-gray-500/20 text-gray-500'}`}>
                                                {tool.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-muted text-xs">
                                            {new Date(tool.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="p-4">
                                            {tool.status === 'pending' && (
                                                <button
                                                    onClick={() => approveTool(tool.tool_id)}
                                                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-xs font-medium transition-colors shadow-sm"
                                                >
                                                    Godkjenn
                                                </button>
                                            )}
                                        </td>
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
