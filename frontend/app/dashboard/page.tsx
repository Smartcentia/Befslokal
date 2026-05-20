"use client";
import React, { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import PropertyDashboard from '../components/features/PropertyDashboard';
import Link from 'next/link';
import DashboardStats from '../components/features/DashboardStats';
import MapComponent from '../components/features/MapComponent';
import TopTenantsPanel from '../components/features/TopTenantsPanel';
import ActivityWheel from '../components/features/ActivityWheel';
import RecentUpdatesPanel from '../components/features/RecentUpdatesPanel';
import { propertyService, type Property } from '@/lib/domains/core/propertyService';
import { type InternalControlCase } from '@/lib/domains/hms/internalControlService';
import { fetchAPI } from '@/lib/api/client';

function formatRelativeDate(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'I dag';
    if (diffDays === 1) return 'I går';
    if (diffDays < 7) return `${diffDays} dager siden`;
    return d.toLocaleDateString('nb-NO', { day: 'numeric', month: 'short' });
}

function SeverityBadge({ severity }: { severity: string }) {
    const isHigh = severity?.toLowerCase() === 'high' || severity?.toLowerCase() === 'critical';
    const isMedium = severity?.toLowerCase() === 'medium';
    const label = isHigh ? 'Høy' : isMedium ? 'Medium' : 'Lav';
    const classes = isHigh
        ? 'bg-danger/20 text-danger'
        : isMedium
            ? 'bg-warning/20 text-warning'
            : 'bg-muted/20 text-muted-foreground';
    return (
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${classes}`}>
            {label}
        </span>
    );
}

interface CriticalCaseItem {
    id: string;
    title: string;
    status: string;
    property_id: string;
    property_name?: string;
    severity: string;
    created_at: string;
    isCase: boolean;
    assignee_name?: string;
}

function JanitorDashboard({ displayName }: { displayName: string }) {
    const hour = new Date().getHours();
    const greeting = hour < 10 ? 'God morgen' : hour < 12 ? 'God formiddag' : hour < 17 ? 'God ettermiddag' : 'God kveld';

    return (
        <div className="text-foreground">
            {/* Velkomst */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">
                    {greeting}, {displayName}!
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    {new Date().toLocaleDateString('nb-NO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Aktivitetshjul — viser HMS/internkontroll oppgaver */}
                <div className="lg:col-span-1">
                    <div className="glass-card p-6 bg-surface/80 h-80">
                        <ActivityWheel />
                    </div>
                </div>

                {/* Hurtiglenker for vaktmester */}
                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {[
                        { href: '/checklists', label: 'Sjekklister', desc: 'Se og gjennomfør HMS-sjekklister', emoji: '✅' },
                        { href: '/deviations', label: 'Avvikshåndtering', desc: 'Registrer og følg opp avvik', emoji: '⚠️' },
                        { href: '/fdvu', label: 'FDVU Oversikt', desc: 'Krav og compliance per eiendom', emoji: '🔧' },
                        { href: '/properties', label: 'Mine eiendommer', desc: 'Se alle dine tilknyttede eiendommer', emoji: '🏢' },
                    ].map(item => (
                        <Link key={item.href} href={item.href}
                            className="glass-card p-5 bg-surface hover:bg-surface/60 border border-border rounded-xl transition-colors group">
                            <div className="text-2xl mb-2">{item.emoji}</div>
                            <div className="font-semibold text-foreground group-hover:text-primary transition-colors">{item.label}</div>
                            <div className="text-xs text-muted-foreground mt-1">{item.desc}</div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Kritiske og forfalne oppgaver */}
            <div className="mt-6">
                <h2 className="text-lg font-bold text-foreground mb-4">Kritiske avvik</h2>
                <div className="glass-card p-6 bg-surface/80">
                    <p className="text-sm text-muted-foreground italic">
                        Gå til <Link href="/deviations" className="text-primary underline">Avvikshåndtering</Link> for å se og registrere avvik på dine eiendommer.
                    </p>
                </div>
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [properties, setProperties] = useState<Property[]>([]);
    const [criticalDeviations, setCriticalDeviations] = useState<CriticalCaseItem[]>([]);
    const [deviationsLoading, setDeviationsLoading] = useState(true);
    const [deviationsError, setDeviationsError] = useState<string | null>(null);
    const { role, user, name: authName, email: authEmail } = useAuth();

    // Check for Property Manager role (and not Admin)
    const isPropertyManager = role === 'PROPERTY_MANAGER';
    const isJanitor = role === 'JANITOR';

    useEffect(() => {
        propertyService.getAll(0, 500).then((res) => {
            if (res && Array.isArray(res)) {
                setProperties(res.filter((p) => !p.closed_at));
            }
        });
    }, []);

    useEffect(() => {
        async function loadCriticalDeviations() {
            setDeviationsLoading(true);
            setDeviationsError(null);
            try {
                // Hent alle åpne saker (én kall), filtrer for critical/high på klientsiden
                const res = await fetchAPI<InternalControlCase[]>('/internal-control/cases?status=open');
                const allOpen = Array.isArray(res) ? res : [];
                const criticalAndHigh = allOpen.filter(
                    (c) => c.priority && ['critical', 'high'].includes(c.priority.toLowerCase())
                );
                const mapCase = (c: InternalControlCase): CriticalCaseItem => ({
                    id: c.case_id,
                    title: c.title,
                    status: c.status,
                    property_id: c.property_id ?? '',
                    property_name: c.property?.name ?? c.property?.address,
                    severity: c.priority,
                    created_at: c.created_at ?? '',
                    isCase: true,
                    assignee_name: c.assigned_user?.name || c.assigned_user?.email?.split('@')[0],
                });
                setCriticalDeviations(criticalAndHigh.map(mapCase).slice(0, 5));
            } catch (err) {
                setCriticalDeviations([]);
                setDeviationsError(err instanceof Error ? err.message : 'Kunne ikke laste avvik');
                console.error('Kritiske avvik – API-feil:', err);
            } finally {
                setDeviationsLoading(false);
            }
        }
        loadCriticalDeviations();
    }, []);

    if (isPropertyManager) {
        return <PropertyDashboard />;
    }

    if (isJanitor) {
        return <JanitorDashboard displayName={authName || authEmail?.split('@')[0] || 'Vaktmester'} />;
    }

    return (
        <div className="min-h-screen text-foreground">
            {/* Header Section */}
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-2xl font-bold tracking-tight text-foreground">Oversikt</h1>
            </div>

            <DashboardStats />

            {/* Spør KI Kollega - forhåndsvalgt spørsmål */}
            <div className="glass-card p-4 mb-6 flex flex-wrap items-center gap-4 border border-primary/20 bg-primary/5">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">Spør KI Kollega</span>
                    <span className="text-xs text-muted">Åpne chat-widgeten nederst til høyre og prøv:</span>
                </div>
                <p className="text-sm text-muted-foreground italic">
                    «Hva er de 5 eiendommer med høyest kostnad per kvadratmeter?»
                </p>
            </div>

            {/* Mapbox - center */}
            <div className="glass-card mb-6 rounded-xl overflow-hidden border border-border bg-surface h-112.5">
                <MapComponent properties={properties} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Venstre: Nye oppdateringer + 5 største leietakere */}
                <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <RecentUpdatesPanel />
                    <div className="glass-card p-6 bg-surface/80">
                        <TopTenantsPanel limit={5} />
                    </div>
                </div>

                {/* Kritiske Avvik - fra API */}
                <div className="md:col-span-1 space-y-6">
                    {/* Activity Wheel Widget */}
                    <div className="glass-card p-6 bg-surface/80">
                        <ActivityWheel />
                    </div>

                    <div className="glass-card p-6 bg-surface/80">
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-foreground">Kritiske Avvik</h3>
                                <p className="text-sm text-foreground/80 mt-0.5">Krever oppfølging</p>
                            </div>
                            <Link href="/checklists?priority=critical" className="text-sm font-semibold text-primary hover:opacity-80 hover:underline">
                                Se alle
                            </Link>
                        </div>
                        <div className="space-y-4">
                            {deviationsLoading ? (
                                <div className="text-base text-foreground py-8 text-center">Laster avvik…</div>
                            ) : deviationsError ? (
                                <div className="text-base text-foreground py-8 px-4 text-center bg-danger/10 rounded-xl border border-danger/30 text-danger">
                                    {deviationsError}
                                </div>
                            ) : criticalDeviations.length === 0 ? (
                                <div className="text-base text-foreground py-8 px-4 text-center bg-surface/50 rounded-xl border border-border">
                                    Ingen kritiske avvik
                                </div>
                            ) : (
                                criticalDeviations.map((d) => (
                                    <Link
                                        key={d.id}
                                        href={d.isCase ? `/cases/${d.id}` : `/deviations/${d.id}`}
                                        className="block p-4 border border-border rounded-xl bg-surface/50 hover:bg-surface transition-colors group cursor-pointer"
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <SeverityBadge severity={d.severity} />
                                            <span className="text-xs text-muted">{formatRelativeDate(d.created_at)}</span>
                                        </div>
                                        <h4 className="font-bold text-foreground text-sm mb-1">{d.title}</h4>
                                        <div className="flex items-center gap-1 text-xs text-muted mb-3">
                                            <span className="w-1 h-1 bg-muted rounded-full"></span>
                                            {d.property_name || d.property_id}
                                            {d.assignee_name && (
                                                <>
                                                    <span className="mx-1">•</span>
                                                    <span className="text-primary/70">{d.assignee_name}</span>
                                                </>
                                            )}
                                        </div>
                                        <div className="flex justify-between items-center pt-2 border-t border-border">
                                            <span className="text-xs font-medium text-muted">{d.status}</span>
                                            <span className="text-muted group-hover:text-primary text-xs transition-colors">→</span>
                                        </div>
                                    </Link>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
