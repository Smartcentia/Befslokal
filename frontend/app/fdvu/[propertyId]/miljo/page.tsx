"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
    ChevronLeft, Leaf, RefreshCw, Thermometer, Droplets, Wind,
    AlertTriangle, CheckCircle2, Info,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { fetchAPI } from '@/lib/api/client';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

interface SensorSummary {
    sensor_id: string;
    name: string;
    type: string; // 'temperature' | 'humidity' | 'co2' | 'energy' | 'other'
    value: number | null;
    unit: string;
    last_reading: string | null;
    status: string | null; // 'ok' | 'warning' | 'error'
    location?: string | null;
}

interface SensorSummaryResponse {
    sensors: SensorSummary[];
    property_id: string;
}

interface Requirement {
    requirement_id: string;
    title: string;
    description?: string | null;
    regulation_set: string;
    category?: string | null;
    status?: string | null; // 'compliant' | 'non_compliant' | 'pending'
    notes?: string | null;
}

type Tab = 'eos' | 'inneklima' | 'breeam';

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function formatKwh(value: number): string {
    if (value >= 1_000_000) return `${(value / 1_000_000).toLocaleString('no-NO', { maximumFractionDigits: 2 })} MWh`;
    if (value >= 1_000) return `${(value / 1_000).toLocaleString('no-NO', { maximumFractionDigits: 1 })} kWh`;
    return `${value.toLocaleString('no-NO', { maximumFractionDigits: 1 })} kWh`;
}

function timeAgo(isoString: string | null): string {
    if (!isoString) return 'ukjent tid';
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 1) return 'akkurat nå';
    if (mins < 60) return `${mins} min siden`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} t siden`;
    return `${Math.floor(hours / 24)} d siden`;
}

const STATUS_COLOR: Record<string, string> = {
    ok: 'text-success',
    warning: 'text-orange-400',
    error: 'text-destructive',
};

const COMPLIANCE_META: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    compliant:     { label: 'Oppfylt',      color: 'text-success bg-success/10 border-success/20',         icon: <CheckCircle2 size={13} /> },
    non_compliant: { label: 'Ikke oppfylt', color: 'text-destructive bg-destructive/10 border-destructive/20', icon: <AlertTriangle size={13} /> },
    pending:       { label: 'Ikke vurdert', color: 'text-muted bg-muted/10 border-border',                  icon: <Info size={13} /> },
};

// ─────────────────────────────────────────────
// EOS Tab
// ─────────────────────────────────────────────

function EosTab({ sensors, loading }: { sensors: SensorSummary[]; loading: boolean }) {
    const energySensors = sensors.filter(s => s.type === 'energy');

    if (loading) {
        return (
            <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-20 bg-card border border-border rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Connection placeholder card */}
            <div className="flex items-start gap-4 bg-primary/5 border border-primary/20 rounded-xl px-5 py-4">
                <Info size={18} className="text-primary shrink-0 mt-0.5" />
                <div>
                    <p className="text-sm font-medium text-foreground">Koble til SD-anlegg / energimåler for sanntidsdata</p>
                    <p className="text-xs text-muted mt-1">
                        Energidata kan hentes automatisk ved å koble SD-anlegget eller en energimåler til plattformen.
                        Kontakt systemadministrator for oppsett.
                    </p>
                </div>
            </div>

            {energySensors.length === 0 ? (
                <div className="text-center py-12 space-y-2">
                    <Leaf size={32} className="mx-auto text-muted opacity-40" />
                    <p className="text-muted text-sm">Ingen energimålere koblet til ennå.</p>
                    <p className="text-xs text-muted">Registrer et SD-anlegg eller energimåler for å se forbruksdata.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {energySensors.map(sensor => (
                        <Card key={sensor.sensor_id} className="bg-card border-border">
                            <CardContent className="p-4">
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <p className="text-sm font-medium text-foreground">{sensor.name}</p>
                                        {sensor.location && (
                                            <p className="text-xs text-muted mt-0.5">{sensor.location}</p>
                                        )}
                                    </div>
                                    {sensor.status && (
                                        <span className={`text-xs ${STATUS_COLOR[sensor.status] ?? 'text-muted'}`}>
                                            ●
                                        </span>
                                    )}
                                </div>
                                <div className="mt-3">
                                    <span className="text-2xl font-bold text-primary">
                                        {sensor.value !== null ? formatKwh(sensor.value) : '—'}
                                    </span>
                                </div>
                                <p className="text-xs text-muted mt-1">Oppdatert {timeAgo(sensor.last_reading)}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────
// Inneklima Tab
// ─────────────────────────────────────────────

const CLIMATE_TYPES = ['temperature', 'humidity', 'co2'] as const;

const CLIMATE_META: Record<string, { label: string; unit: string; icon: React.ReactNode; goodRange: string }> = {
    temperature: { label: 'Temperatur',  unit: '°C',  icon: <Thermometer size={16} />, goodRange: '20–24 °C' },
    humidity:    { label: 'Luftfuktighet', unit: '%', icon: <Droplets size={16} />,    goodRange: '30–60 %' },
    co2:         { label: 'CO₂',          unit: 'ppm', icon: <Wind size={16} />,       goodRange: '< 1000 ppm' },
};

function InneklimaTab({ sensors, loading }: { sensors: SensorSummary[]; loading: boolean }) {
    const climateSensors = sensors.filter(s => CLIMATE_TYPES.includes(s.type as typeof CLIMATE_TYPES[number]));

    if (loading) {
        return (
            <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-16 bg-card border border-border rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    if (climateSensors.length === 0) {
        return (
            <div className="text-center py-12 space-y-2">
                <Thermometer size={32} className="mx-auto text-muted opacity-40" />
                <p className="text-muted text-sm">Ingen inneklima-sensorer registrert.</p>
                <p className="text-xs text-muted">Koble til SD-anlegg med temperatur-, fuktighets- eller CO₂-sensorer for å se data her.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {CLIMATE_TYPES.map(type => {
                const meta = CLIMATE_META[type];
                const typeSensors = climateSensors.filter(s => s.type === type);
                if (typeSensors.length === 0) return null;
                return (
                    <div key={type}>
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-primary">{meta.icon}</span>
                            <h3 className="text-sm font-semibold text-foreground">{meta.label}</h3>
                            <span className="text-xs text-muted ml-auto">Anbefalt: {meta.goodRange}</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                            {typeSensors.map(sensor => (
                                <Card key={sensor.sensor_id} className="bg-card border-border">
                                    <CardContent className="p-4">
                                        <div className="flex items-center justify-between gap-2 mb-2">
                                            <p className="text-xs text-muted truncate">{sensor.name}</p>
                                            {sensor.status && (
                                                <span className={`text-xs ${STATUS_COLOR[sensor.status] ?? 'text-muted'}`}>●</span>
                                            )}
                                        </div>
                                        <div className="text-xl font-bold text-foreground">
                                            {sensor.value !== null
                                                ? `${sensor.value.toLocaleString('no-NO', { maximumFractionDigits: 1 })} ${meta.unit}`
                                                : '—'}
                                        </div>
                                        {sensor.location && (
                                            <p className="text-xs text-muted mt-1">{sensor.location}</p>
                                        )}
                                        <p className="text-xs text-muted mt-1">Oppdatert {timeAgo(sensor.last_reading)}</p>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// ─────────────────────────────────────────────
// BREEAM Tab
// ─────────────────────────────────────────────

function BreeamTab({ requirements, loading }: { requirements: Requirement[]; loading: boolean }) {
    if (loading) {
        return (
            <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-16 bg-card border border-border rounded-lg animate-pulse" />
                ))}
            </div>
        );
    }

    if (requirements.length === 0) {
        return (
            <div className="text-center py-12 space-y-3">
                <CheckCircle2 size={32} className="mx-auto text-muted opacity-40" />
                <p className="text-muted text-sm">Ingen BREEAM-krav registrert for denne eiendommen.</p>
                <p className="text-xs text-muted">
                    BREEAM In-Use krav kan legges til via administrasjonspanelet eller seedes fra standardmalen.
                </p>
            </div>
        );
    }

    const grouped = requirements.reduce<Record<string, Requirement[]>>((acc, req) => {
        const cat = req.category ?? 'Annet';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(req);
        return acc;
    }, {});

    return (
        <div className="space-y-6">
            {/* Summary counts */}
            <div className="grid grid-cols-3 gap-3">
                {(['compliant', 'non_compliant', 'pending'] as const).map(status => {
                    const meta = COMPLIANCE_META[status];
                    const count = requirements.filter(r => (r.status ?? 'pending') === status).length;
                    return (
                        <Card key={status} className="bg-card border-border">
                            <CardContent className="p-4 text-center">
                                <div className={`text-2xl font-bold ${meta.color.split(' ')[0]}`}>{count}</div>
                                <div className="text-xs text-muted mt-1">{meta.label}</div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>

            {/* Requirements grouped by category */}
            {Object.entries(grouped).map(([category, reqs]) => (
                <div key={category}>
                    <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">{category}</h3>
                    <div className="space-y-2">
                        {reqs.map(req => {
                            const status = req.status ?? 'pending';
                            const meta = COMPLIANCE_META[status] ?? COMPLIANCE_META.pending;
                            return (
                                <div key={req.requirement_id}
                                    className="bg-card border border-border rounded-lg px-4 py-3 flex items-start gap-3 hover:border-primary/30 transition-colors">
                                    <span className={`shrink-0 mt-0.5 ${meta.color.split(' ')[0]}`}>{meta.icon}</span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-foreground">{req.title}</p>
                                        {req.description && (
                                            <p className="text-xs text-muted mt-0.5 line-clamp-2">{req.description}</p>
                                        )}
                                        {req.notes && (
                                            <p className="text-xs text-muted mt-1 italic">{req.notes}</p>
                                        )}
                                    </div>
                                    <Badge className={`text-xs shrink-0 border ${meta.color}`}>{meta.label}</Badge>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
}

// ─────────────────────────────────────────────
// Hovedside
// ─────────────────────────────────────────────

export default function MiljoPage({ params }: { params: Promise<{ propertyId: string }> }) {
    const { propertyId } = React.use(params);
    const [tab, setTab] = useState<Tab>('eos');
    const [sensors, setSensors] = useState<SensorSummary[]>([]);
    const [requirements, setRequirements] = useState<Requirement[]>([]);
    const [loadingSensors, setLoadingSensors] = useState(true);
    const [loadingReqs, setLoadingReqs] = useState(true);
    const [errorSensors, setErrorSensors] = useState<string | null>(null);
    const [errorReqs, setErrorReqs] = useState<string | null>(null);

    const loadSensors = useCallback(async () => {
        setLoadingSensors(true);
        setErrorSensors(null);
        try {
            const data = await fetchAPI<SensorSummaryResponse>(
                `/fdvu/sensors/${propertyId}/summary`
            );
            setSensors(data.sensors ?? []);
        } catch (e) {
            setErrorSensors(e instanceof Error ? e.message : 'Kunne ikke hente sensordata');
            setSensors([]);
        } finally {
            setLoadingSensors(false);
        }
    }, [propertyId]);

    const loadRequirements = useCallback(async () => {
        setLoadingReqs(true);
        setErrorReqs(null);
        try {
            const data = await fetchAPI<Requirement[]>(
                `/fdvu/requirements?regulation_set=BREEAM&property_id=${propertyId}`
            );
            setRequirements(Array.isArray(data) ? data : []);
        } catch (e) {
            setErrorReqs(e instanceof Error ? e.message : 'Kunne ikke hente BREEAM-krav');
            setRequirements([]);
        } finally {
            setLoadingReqs(false);
        }
    }, [propertyId]);

    useEffect(() => {
        loadSensors();
        loadRequirements();
    }, [loadSensors, loadRequirements]);

    const reload = () => {
        loadSensors();
        loadRequirements();
    };

    const isLoading = tab === 'breeam' ? loadingReqs : loadingSensors;
    const error = tab === 'breeam' ? errorReqs : errorSensors;

    const TABS: { key: Tab; label: string }[] = [
        { key: 'eos',      label: 'EOS – Energioppfølging' },
        { key: 'inneklima', label: 'Inneklima (SD)' },
        { key: 'breeam',   label: 'BREEAM In-Use' },
    ];

    return (
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Link href={`/fdvu/${propertyId}`} className="text-muted hover:text-foreground transition-colors">
                    <ChevronLeft size={20} />
                </Link>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <Leaf className="text-primary" size={22} /> Miljø &amp; Inneklima
                    </h1>
                    <p className="text-muted text-xs mt-0.5 font-mono">{propertyId}</p>
                </div>
                <button
                    onClick={reload}
                    disabled={loadingSensors || loadingReqs}
                    className="p-2 rounded-lg border border-border text-muted hover:text-foreground transition-colors"
                    title="Oppdater"
                >
                    <RefreshCw size={15} className={loadingSensors || loadingReqs ? 'animate-spin' : ''} />
                </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border overflow-x-auto">
                {TABS.map(({ key, label }) => (
                    <button
                        key={key}
                        onClick={() => setTab(key)}
                        className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
                            tab === key
                                ? 'border-primary text-primary'
                                : 'border-transparent text-muted hover:text-foreground'
                        }`}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {/* Error banner */}
            {error && (
                <div className="flex items-start gap-2 text-destructive text-xs bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                    <AlertTriangle size={13} className="shrink-0 mt-0.5" />
                    <span>{error}</span>
                </div>
            )}

            {/* Tab content */}
            {tab === 'eos' && <EosTab sensors={sensors} loading={loadingSensors} />}
            {tab === 'inneklima' && <InneklimaTab sensors={sensors} loading={loadingSensors} />}
            {tab === 'breeam' && <BreeamTab requirements={requirements} loading={loadingReqs} />}
        </div>
    );
}
