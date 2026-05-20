"use client";

import React, { useState, useEffect } from 'react';
import { fetchAPI } from '@/lib/api';

interface ContractCostReportItem {
    id: string;
    contract_id: string;
    prop_name: string;
    category: string;
    status: string;
    rent: number;
    extra: number;
    total: number;
}

interface ContractCostsResponse {
    count: number;
    total_rent: number;
    total_extra: number;
    total_overall: number;
    data: ContractCostReportItem[];
}

export default function ContractCostsPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [report, setReport] = useState<ContractCostsResponse | null>(null);

    // Filters
    const [searchTerm, setSearchTerm] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await fetchAPI<ContractCostsResponse>('/admin/contracts/costs');
                setReport(data);
            } catch (err: any) {
                console.error("Failed to load contract costs:", err);
                setError("Kunne ikke laste kontraktskostnader. Prøv igjen senere.");
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const filteredData = report?.data.filter(item => {
        const matchesSearch = item.prop_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            item.category.toLowerCase().includes(searchTerm.toLowerCase());

        const matchesStatus = statusFilter === "all" || item.status === statusFilter;

        return matchesSearch && matchesStatus;
    }) || [];

    // Format currency
    const formatNOK = (amount: number) => {
        return new Intl.NumberFormat('no-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(amount);
    };

    if (loading) {
        return (
            <div className="min-h-[50vh] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin"></div>
                    <p className="text-muted-foreground animate-pulse">Henter kontraktsdata...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 max-w-4xl mx-auto mt-8">
                <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-xl text-center">
                    <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <h2 className="text-xl font-bold text-red-500 mb-2">En feil oppstod</h2>
                    <p className="text-red-400/80">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-7xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">Kontraktskostnader</h1>
                        <p className="text-muted-foreground mt-1">Oversikt over alle leiekostnader uavhengig av avdelingsbudsjetter.</p>
                    </div>
                </div>

                {/* Summary Cards */}
                {report && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="glass-card p-6 bg-gradient-to-br from-violet-500/10 to-transparent border-violet-500/20">
                            <h3 className="text-sm font-medium text-muted-foreground mb-1">Total Husleie / Årsleie</h3>
                            <div className="text-3xl font-bold tracking-tight text-foreground">{formatNOK(report.total_rent)}</div>
                        </div>
                        <div className="glass-card p-6">
                            <h3 className="text-sm font-medium text-muted-foreground mb-1">Tilleggskostnader i kontrakter</h3>
                            <div className="text-3xl font-bold tracking-tight text-foreground">{formatNOK(report.total_extra)}</div>
                        </div>
                        <div className="glass-card p-6 border-l-4 border-l-violet-500">
                            <h3 className="text-sm font-medium text-muted-foreground mb-1">Total sum kostnader</h3>
                            <div className="text-3xl font-bold tracking-tight text-violet-500">{formatNOK(report.total_overall)}</div>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="glass-card p-4 flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Søk (eiendom, kategori)</label>
                        <div className="relative">
                            <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                            <input
                                type="text"
                                placeholder="Søk etter eiendom..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-background border border-border rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                            />
                        </div>
                    </div>
                    <div className="w-full sm:w-48">
                        <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Status</label>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="w-full bg-background border border-border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                        >
                            <option value="all">Alle</option>
                            <option value="active">Aktiv</option>
                            <option value="terminated">Avsluttet / Oppsagt</option>
                        </select>
                    </div>
                </div>

                {/* Table */}
                <div className="glass-card overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-muted-foreground bg-muted/30 border-b border-border">
                                <tr>
                                    <th className="px-6 py-4 font-semibold">Eiendom</th>
                                    <th className="px-6 py-4 font-semibold">Kategori</th>
                                    <th className="px-6 py-4 font-semibold">Status</th>
                                    <th className="px-6 py-4 font-semibold text-right">Husleie</th>
                                    <th className="px-6 py-4 font-semibold text-right">Andre Kostnader</th>
                                    <th className="px-6 py-4 font-semibold text-right text-violet-500">Total</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border/50">
                                {filteredData.length > 0 ? (
                                    filteredData.map((item, idx) => (
                                        <tr key={item.id || idx} className="hover:bg-muted/10 transition-colors">
                                            <td className="px-6 py-4 font-medium text-foreground">{item.prop_name}</td>
                                            <td className="px-6 py-4 text-muted-foreground">{item.category}</td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${item.status === 'active' ? 'bg-green-500/10 text-green-500' :
                                                        item.status === 'terminated' ? 'bg-red-500/10 text-red-500' :
                                                            'bg-slate-500/10 text-slate-500'
                                                    }`}>
                                                    {item.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-right tabular-nums">{formatNOK(item.rent)}</td>
                                            <td className="px-6 py-4 text-right tabular-nums text-muted-foreground">{formatNOK(item.extra)}</td>
                                            <td className="px-6 py-4 text-right tabular-nums font-bold text-foreground">{formatNOK(item.total)}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                                            Ingen kontrakter funnet som samsvarer med filteret.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="p-4 bg-muted/20 border-t border-border/50 text-xs text-muted-foreground text-center">
                        Viser {filteredData.length} av totalt {report?.count || 0} kontrakter
                    </div>
                </div>

            </div>
        </div>
    );
}
