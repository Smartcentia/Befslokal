"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
    AlertTriangle,
    CheckCircle2,
    Clock,
    XCircle,
    TrendingUp,
    Building2,
    ChevronRight,
} from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DeviationStats {
    total: number;
    open: number;
    closed: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
}

interface TrendPoint {
    month: string;     // "2025-03"
    total: number;
    open: number;
    closed: number;
    high_priority: number;
}

interface OverdueItem {
    id: string;
    title: string;
    status: string;
    priority: string;
    due_date: string;
    days_overdue: number;
    property_id: string;
    property_name: string | null;
}

interface ByPropertyItem {
    property_id: string;
    property_name: string | null;
    total: number;
    open: number;
    high_priority: number;
}

// ─── Hjelpere ─────────────────────────────────────────────────────────────────

function priorityColor(p: string) {
    if (p === "critical") return "bg-red-100 text-red-700";
    if (p === "high")     return "bg-orange-100 text-orange-700";
    if (p === "medium")   return "bg-yellow-100 text-yellow-700";
    return "bg-muted text-muted-foreground";
}

function priorityLabel(p: string) {
    if (p === "critical") return "Kritisk";
    if (p === "high")     return "Høy";
    if (p === "medium")   return "Middels";
    return "Lav";
}

function monthLabel(m: string) {
    const [y, mo] = m.split("-");
    const names = ["Jan","Feb","Mar","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Des"];
    return `${names[parseInt(mo) - 1]} ${y.slice(2)}`;
}

// ─── Mini bar-chart (ren CSS) ──────────────────────────────────────────────────

function TrendChart({ data }: { data: TrendPoint[] }) {
    if (!data.length) return <p className="text-sm text-muted-foreground py-4">Ingen data</p>;
    const maxVal = Math.max(...data.map(d => d.total), 1);
    return (
        <div className="flex items-end gap-1 h-32 mt-2">
            {data.map(d => (
                <div key={d.month} className="flex-1 flex flex-col items-center gap-0.5 group">
                    <div
                        className="relative w-full flex flex-col-reverse rounded-t overflow-hidden"
                        style={{ height: `${(d.total / maxVal) * 100}%`, minHeight: d.total > 0 ? "4px" : "0" }}
                        title={`${monthLabel(d.month)}: ${d.total} totalt, ${d.open} åpne`}
                    >
                        <div className="bg-primary/30 w-full" style={{ height: `${d.closed / (d.total || 1) * 100}%` }} />
                        <div className="bg-primary w-full" style={{ height: `${d.open / (d.total || 1) * 100}%` }} />
                    </div>
                    <span className="text-[9px] text-muted-foreground rotate-45 origin-left mt-1 whitespace-nowrap hidden sm:block">
                        {monthLabel(d.month)}
                    </span>
                </div>
            ))}
        </div>
    );
}

// ─── Hoved-komponent ──────────────────────────────────────────────────────────

export default function HMSDashboard() {
    const [stats, setStats] = useState<DeviationStats | null>(null);
    const [trend, setTrend] = useState<TrendPoint[]>([]);
    const [overdue, setOverdue] = useState<OverdueItem[]>([]);
    const [byProp, setByProp] = useState<ByPropertyItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            setLoading(true);
            try {
                const [s, t, o, bp] = await Promise.allSettled([
                    fetchAPI<DeviationStats>("/deviations/stats"),
                    fetchAPI<{ trend: TrendPoint[] }>("/deviations/trend"),
                    fetchAPI<{ overdue: OverdueItem[] }>("/deviations/overdue"),
                    fetchAPI<{ by_property: ByPropertyItem[] }>("/deviations/by-property"),
                ]);
                if (s.status === "fulfilled") setStats(s.value);
                if (t.status === "fulfilled") setTrend(t.value.trend ?? []);
                if (o.status === "fulfilled") setOverdue(o.value.overdue ?? []);
                if (bp.status === "fulfilled") setByProp(bp.value.by_property ?? []);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const priorityDistrib = stats
        ? [
            { label: "Kritisk", value: stats.critical, color: "bg-red-500" },
            { label: "Høy",     value: stats.high,     color: "bg-orange-400" },
            { label: "Middels", value: stats.medium,   color: "bg-yellow-400" },
            { label: "Lav",     value: stats.low,      color: "bg-green-400" },
          ]
        : [];
    const totalPriority = priorityDistrib.reduce((s, d) => s + d.value, 0) || 1;

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <p className="text-muted-foreground">Laster HMS-data…</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h1 className="text-2xl font-bold">HMS Avvik – Dashboard</h1>
                    <p className="text-sm text-muted-foreground">Oversikt, trend og forfalt</p>
                </div>
                <Link
                    href="/deviations"
                    className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted/30 transition-colors"
                >
                    Alle avvik <ChevronRight size={14} />
                </Link>
            </div>

            {/* KPI-kort */}
            {stats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    {[
                        { label: "Totalt", value: stats.total, icon: <AlertTriangle className="w-5 h-5" />, color: "text-foreground" },
                        { label: "Åpne",   value: stats.open,  icon: <Clock className="w-5 h-5" />,         color: "text-yellow-600" },
                        { label: "Lukket", value: stats.closed, icon: <CheckCircle2 className="w-5 h-5" />, color: "text-green-600" },
                        { label: "Kritisk/høy", value: stats.critical + stats.high, icon: <XCircle className="w-5 h-5" />, color: "text-red-600" },
                    ].map(card => (
                        <div key={card.label} className="rounded-xl border border-border bg-card p-5 flex items-center gap-4">
                            <div className={`${card.color} opacity-70`}>{card.icon}</div>
                            <div>
                                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                                <p className="text-xs text-muted-foreground">{card.label}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Trend */}
                <div className="rounded-xl border border-border bg-card p-5">
                    <h2 className="font-semibold mb-1 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" /> Trend siste 12 måneder
                    </h2>
                    <div className="flex gap-4 text-xs text-muted-foreground mb-2">
                        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-primary inline-block" /> Åpne</span>
                        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-primary/30 inline-block" /> Lukket</span>
                    </div>
                    <TrendChart data={trend} />
                </div>

                {/* Prioritetsfordeling */}
                <div className="rounded-xl border border-border bg-card p-5">
                    <h2 className="font-semibold mb-4">Fordeling etter prioritet</h2>
                    <div className="space-y-3">
                        {priorityDistrib.map(d => (
                            <div key={d.label}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span>{d.label}</span>
                                    <span className="font-mono">{d.value}</span>
                                </div>
                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${d.color}`}
                                        style={{ width: `${(d.value / totalPriority) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Forfalt */}
                <div className="rounded-xl border border-border bg-card p-5">
                    <h2 className="font-semibold mb-4 flex items-center gap-2 text-red-700">
                        <Clock className="w-4 h-4" /> Forfalt ({overdue.length})
                    </h2>
                    {overdue.length === 0 ? (
                        <p className="text-sm text-green-600 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" /> Ingen forfalt avvik 🎉
                        </p>
                    ) : (
                        <div className="space-y-2 max-h-72 overflow-y-auto">
                            {overdue.map(item => (
                                <Link
                                    key={item.id}
                                    href={`/deviations/${item.id}`}
                                    className="block p-3 rounded-lg border border-border hover:bg-muted/30 transition-colors"
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <p className="text-sm font-medium line-clamp-1">{item.title}</p>
                                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${priorityColor(item.priority)}`}>
                                            {priorityLabel(item.priority)}
                                        </span>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-0.5">
                                        {item.property_name} · <span className="text-red-600">{item.days_overdue}d forfalt</span>
                                    </p>
                                </Link>
                            ))}
                        </div>
                    )}
                </div>

                {/* Per eiendom */}
                <div className="rounded-xl border border-border bg-card p-5">
                    <h2 className="font-semibold mb-4 flex items-center gap-2">
                        <Building2 className="w-4 h-4" /> Åpne avvik per eiendom
                    </h2>
                    {byProp.length === 0 ? (
                        <p className="text-sm text-muted-foreground">Ingen data</p>
                    ) : (
                        <div className="space-y-2 max-h-72 overflow-y-auto">
                            {byProp.map(item => (
                                <div key={item.property_id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                                    <div>
                                        <p className="text-sm font-medium">{item.property_name ?? item.property_id}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {item.open} åpne · {item.high_priority} høy/kritisk
                                        </p>
                                    </div>
                                    <Link
                                        href={`/deviations?property_id=${item.property_id}`}
                                        className="text-xs text-primary hover:underline flex items-center gap-1"
                                    >
                                        Se <ChevronRight size={12} />
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
