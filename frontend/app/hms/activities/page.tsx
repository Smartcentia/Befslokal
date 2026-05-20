"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { fetchAPI } from '@/lib/api';
import Link from 'next/link';
import { CalendarDays, AlertTriangle, CheckCircle2, Clock, Filter, RefreshCw, ChevronRight } from 'lucide-react';

interface ScheduledActivity {
    activity_id: string;
    property_id: string | null;
    property_name?: string;
    title: string;
    description?: string;
    activity_type?: string;
    category: string;
    priority: string;
    next_due_date: string;
    enabled?: boolean;
    last_completed_date?: string | null;
    status?: string;
}

const PRIORITY_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode; order: number }> = {
    critical: { label: 'Kritisk', color: 'text-red-500 bg-red-500/10 border-red-500/20', icon: <AlertTriangle size={13} className="text-red-500" />, order: 0 },
    high:     { label: 'Høy',     color: 'text-orange-500 bg-orange-500/10 border-orange-500/20', icon: <AlertTriangle size={13} className="text-orange-500" />, order: 1 },
    medium:   { label: 'Middels', color: 'text-yellow-600 bg-yellow-500/10 border-yellow-500/20', icon: <Clock size={13} className="text-yellow-600" />, order: 2 },
    low:      { label: 'Lav',     color: 'text-green-600 bg-green-500/10 border-green-500/20', icon: <CheckCircle2 size={13} className="text-green-600" />, order: 3 },
};

const CATEGORY_LABELS: Record<string, string> = {
    brann: 'Brann',
    teknisk: 'Teknisk',
    hms: 'HMS',
    sikkerhet: 'Sikkerhet',
    renhold: 'Renhold',
    utvendig: 'Utvendig',
    admin: 'Admin',
};

function formatDate(iso: string) {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString('nb-NO', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getDaysUntil(iso: string): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(iso);
    due.setHours(0, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / 86400000);
}

function DueBadge({ iso }: { iso: string }) {
    const days = getDaysUntil(iso);
    if (days < 0) return <span className="text-xs font-medium text-red-500 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full">Forfalt ({Math.abs(days)}d)</span>;
    if (days === 0) return <span className="text-xs font-medium text-orange-500 bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded-full">I dag</span>;
    if (days <= 7) return <span className="text-xs font-medium text-yellow-600 bg-yellow-500/10 border border-yellow-500/20 px-2 py-0.5 rounded-full">Om {days}d</span>;
    return <span className="text-xs text-muted-foreground">{formatDate(iso)}</span>;
}

export default function HMSActivitiesPage() {
    const [activities, setActivities] = useState<ScheduledActivity[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [filterPriority, setFilterPriority] = useState('all');
    const [filterCategory, setFilterCategory] = useState('all');
    const [daysAhead, setDaysAhead] = useState(30);
    const [searchTerm, setSearchTerm] = useState('');

    const loadActivities = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const data = await fetchAPI<ScheduledActivity[]>(`/hms/activities/upcoming?days_ahead=${daysAhead}`);
            setActivities(Array.isArray(data) ? data : []);
        } catch (e) {
            console.error('Failed to load activities', e);
            setError('Kunne ikke laste aktiviteter. Prøv igjen.');
        } finally {
            setLoading(false);
        }
    }, [daysAhead]);

    useEffect(() => {
        loadActivities();
    }, [loadActivities]);

    const filtered = activities.filter(a => {
        if (filterPriority !== 'all' && a.priority !== filterPriority) return false;
        if (filterCategory !== 'all' && a.category !== filterCategory) return false;
        if (searchTerm) {
            const q = searchTerm.toLowerCase();
            if (!a.title.toLowerCase().includes(q) && !(a.property_name ?? '').toLowerCase().includes(q)) return false;
        }
        return true;
    }).sort((a, b) => {
        const pa = PRIORITY_CONFIG[a.priority]?.order ?? 99;
        const pb = PRIORITY_CONFIG[b.priority]?.order ?? 99;
        if (pa !== pb) return pa - pb;
        return new Date(a.next_due_date).getTime() - new Date(b.next_due_date).getTime();
    });

    const criticalCount = activities.filter(a => a.priority === 'critical').length;
    const overdueCount = activities.filter(a => getDaysUntil(a.next_due_date) < 0).length;
    const todayCount = activities.filter(a => getDaysUntil(a.next_due_date) === 0).length;

    const categories = [...new Set(activities.map(a => a.category).filter(Boolean))];

    return (
        <div className="text-foreground">
            {/* Header */}
            <div className="flex flex-wrap justify-between items-start gap-4 mb-6">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-foreground">HMS-aktiviteter</h1>
                    <p className="text-muted-foreground mt-1 text-sm">Planlagte kontroller og vedlikeholdsoppgaver</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        value={daysAhead}
                        onChange={e => setDaysAhead(Number(e.target.value))}
                        className="text-sm border border-border rounded-lg px-3 py-2 bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
                    >
                        <option value={7}>Neste 7 dager</option>
                        <option value={14}>Neste 14 dager</option>
                        <option value={30}>Neste 30 dager</option>
                        <option value={90}>Neste 3 måneder</option>
                        <option value={180}>Neste 6 måneder</option>
                    </select>
                    <button
                        onClick={loadActivities}
                        className="p-2 border border-border rounded-lg bg-background hover:bg-border/30 text-muted-foreground transition-colors"
                        title="Oppdater"
                    >
                        <RefreshCw size={16} />
                    </button>
                </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                {[
                    { label: 'Totalt', value: activities.length, color: 'text-foreground', bg: 'bg-surface' },
                    { label: 'Forfalt', value: overdueCount, color: 'text-red-500', bg: 'bg-red-500/5 border border-red-500/10' },
                    { label: 'I dag', value: todayCount, color: 'text-orange-500', bg: 'bg-orange-500/5 border border-orange-500/10' },
                    { label: 'Kritisk prioritet', value: criticalCount, color: 'text-red-600', bg: 'bg-red-600/5 border border-red-600/10' },
                ].map(stat => (
                    <div key={stat.label} className={`${stat.bg} rounded-xl p-4`}>
                        <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                        <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-5 items-center">
                <div className="relative flex-1 min-w-[200px]">
                    <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Søk i tittel eller eiendom…"
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="w-full pl-8 pr-3 py-2 text-sm border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
                    />
                </div>
                <select
                    value={filterPriority}
                    onChange={e => setFilterPriority(e.target.value)}
                    className="text-sm border border-border rounded-lg px-3 py-2 bg-background text-foreground focus:outline-none"
                >
                    <option value="all">Alle prioriteter</option>
                    <option value="critical">Kritisk</option>
                    <option value="high">Høy</option>
                    <option value="medium">Middels</option>
                    <option value="low">Lav</option>
                </select>
                <select
                    value={filterCategory}
                    onChange={e => setFilterCategory(e.target.value)}
                    className="text-sm border border-border rounded-lg px-3 py-2 bg-background text-foreground focus:outline-none"
                >
                    <option value="all">Alle kategorier</option>
                    {categories.map(cat => (
                        <option key={cat} value={cat}>{CATEGORY_LABELS[cat] ?? cat}</option>
                    ))}
                </select>
            </div>

            {/* Activity list */}
            <div className="bg-surface border border-border rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-border flex justify-between items-center bg-background/50">
                    <h2 className="font-semibold text-foreground text-sm">
                        <CalendarDays size={15} className="inline mr-1.5 mb-0.5 text-primary" />
                        Aktiviteter ({filtered.length})
                    </h2>
                    {filtered.length !== activities.length && (
                        <span className="text-xs text-muted-foreground">
                            Viser {filtered.length} av {activities.length}
                        </span>
                    )}
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
                        Laster aktiviteter…
                    </div>
                ) : error ? (
                    <div className="flex items-center justify-center h-40 text-red-500 text-sm">{error}</div>
                ) : filtered.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-40 text-muted-foreground text-sm gap-2">
                        <CheckCircle2 size={28} className="text-green-500/50" />
                        Ingen aktiviteter funnet for valgte filtre
                    </div>
                ) : (
                    <ul className="divide-y divide-border">
                        {filtered.map(activity => {
                            const pri = PRIORITY_CONFIG[activity.priority] ?? PRIORITY_CONFIG.low;
                            const catLabel = CATEGORY_LABELS[activity.category] ?? activity.category;
                            return (
                                <li key={activity.activity_id} className="flex items-start gap-4 px-5 py-4 hover:bg-border/10 transition-colors">
                                    <div className="mt-0.5 flex-shrink-0">
                                        {pri.icon}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex flex-wrap items-center gap-2 mb-1">
                                            <span className="font-medium text-sm text-foreground truncate">{activity.title}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${pri.color}`}>
                                                {pri.label}
                                            </span>
                                            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium">
                                                {catLabel}
                                            </span>
                                        </div>
                                        {activity.property_name && (
                                            <div className="text-xs text-muted-foreground mb-1">
                                                {activity.property_id ? (
                                                    <Link href={`/properties/${activity.property_id}`} className="hover:text-primary hover:underline">
                                                        {activity.property_name}
                                                    </Link>
                                                ) : activity.property_name}
                                            </div>
                                        )}
                                        {activity.description && (
                                            <p className="text-xs text-muted-foreground/80 line-clamp-1">{activity.description}</p>
                                        )}
                                    </div>
                                    <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
                                        <DueBadge iso={activity.next_due_date} />
                                        {activity.property_id && (
                                            <Link
                                                href={`/properties/${activity.property_id}`}
                                                className="text-xs text-muted-foreground hover:text-primary flex items-center gap-0.5 transition-colors"
                                            >
                                                Se eiendom <ChevronRight size={12} />
                                            </Link>
                                        )}
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </div>

            {/* Link to calendar */}
            <div className="mt-4 text-center">
                <Link href="/kalender" className="text-sm text-primary hover:underline inline-flex items-center gap-1">
                    <CalendarDays size={14} />
                    Vis i kalender
                </Link>
            </div>
        </div>
    );
}
