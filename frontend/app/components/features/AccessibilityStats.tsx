"use client";
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { propertyService, AccessibilitySummary } from '@/lib/domains/core/propertyService';
import { ShieldCheck, Train, School, ShoppingCart, Trees, Siren, Hospital, BusFront, GraduationCap } from 'lucide-react';

// ── Terskler fra Bufetat-workshopkrav (mai 2026) ──────────────────────────────
const KEY_THRESHOLDS = [
    {
        label: 'Blålys',
        types: ['police', 'fire_station', 'ambulance'],
        maxMin: 15,
        useTime: true,
        icon: <Siren size={15} />,
        color: 'red',
    },
    {
        label: 'Sykehus',
        types: ['hospital', 'emergency_room'],
        maxMin: 30,
        useTime: true,
        icon: <Hospital size={15} />,
        color: 'rose',
    },
    {
        label: 'BUP',
        types: ['bup'],
        maxKm: 30,
        maxMin: 30,
        useTime: true,
        icon: <ShieldCheck size={15} />,
        color: 'violet',
    },
    {
        label: 'Kollektiv',
        types: ['transit_station', 'bus_station', 'train_station', 'subway_station'],
        maxKm: 1,
        useTime: false,
        icon: <BusFront size={15} />,
        color: 'blue',
    },
    {
        label: 'Skole',
        types: ['school', 'high_school'],
        maxKm: 3,
        useTime: false,
        icon: <GraduationCap size={15} />,
        color: 'amber',
    },
] as const;

type ThresholdStatus = 'ok' | 'warn' | 'over' | 'unknown';

function thresholdStatus(
    nearest: AccessibilitySummary['nearest_by_type'][string] | undefined,
    maxKm?: number,
    maxMin?: number,
    useTime?: boolean
): ThresholdStatus {
    if (!nearest) return 'unknown';
    if (useTime && maxMin && nearest.travel_time_minutes != null) {
        const ratio = nearest.travel_time_minutes / maxMin;
        if (ratio <= 0.8) return 'ok';
        if (ratio <= 1.0) return 'warn';
        return 'over';
    }
    if (maxKm && nearest.distance_meters != null) {
        const ratio = nearest.distance_meters / (maxKm * 1000);
        if (ratio <= 0.8) return 'ok';
        if (ratio <= 1.0) return 'warn';
        return 'over';
    }
    return 'unknown';
}

const STATUS_STYLES: Record<ThresholdStatus, string> = {
    ok:      'bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-700/30 dark:text-green-400',
    warn:    'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/20 dark:border-amber-700/30 dark:text-amber-400',
    over:    'bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-700/30 dark:text-red-400',
    unknown: 'bg-muted/20 border-border text-muted-foreground',
};

function ProximityThresholds({ summary }: { summary: AccessibilitySummary }) {
    return (
        <div className="mb-5">
            <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Nærhetskrav (Bufetat)</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                {KEY_THRESHOLDS.map(t => {
                    // Pick nearest across all relevant types
                    let nearest: AccessibilitySummary['nearest_by_type'][string] | undefined;
                    for (const type of t.types) {
                        const entry = summary.nearest_by_type[type];
                        if (entry && (!nearest || entry.distance_meters < nearest.distance_meters)) {
                            nearest = entry;
                        }
                    }
                    const status = thresholdStatus(nearest, (t as any).maxKm, (t as any).maxMin, t.useTime);
                    const timeVal = nearest?.travel_time_minutes;
                    const kmVal = nearest ? (nearest.distance_meters / 1000).toFixed(1) : null;
                    const displayVal = t.useTime && timeVal != null
                        ? `${Math.round(timeVal)} min`
                        : kmVal != null ? `${kmVal} km` : '–';
                    const threshold = t.useTime
                        ? `maks ${(t as any).maxMin} min`
                        : `maks ${(t as any).maxKm} km`;

                    return (
                        <div key={t.label} className={`rounded-xl border px-3 py-2.5 flex flex-col gap-1 ${STATUS_STYLES[status]}`}>
                            <div className="flex items-center gap-1.5 font-semibold text-xs">
                                {t.icon}
                                {t.label}
                            </div>
                            <div className="text-lg font-bold leading-none">{displayVal}</div>
                            <div className="text-[10px] opacity-70">{threshold}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

const categories = [
    {
        title: "Helse & Sikkerhet",
        types: ["hospital", "doctor", "pharmacy", "police", "fire_station", "bup"],
        icon: <ShieldCheck size={18} className="text-rose-500" />,
        color: "bg-rose-50/50 border-rose-200 dark:bg-rose-500/10 dark:border-rose-500/20",
        hoverColor: "hover:bg-rose-100/50 dark:hover:bg-rose-500/20"
    },
    {
        title: "Transport",
        types: ["transit_station", "bus_station", "train_station", "subway_station"],
        icon: <Train size={18} className="text-blue-500" />,
        color: "bg-blue-50/50 border-blue-200 dark:bg-blue-500/10 dark:border-blue-500/20",
        hoverColor: "hover:bg-blue-100/50 dark:hover:bg-blue-500/20"
    },
    {
        title: "Utdanning & Barn",
        types: ["school"],
        icon: <School size={18} className="text-amber-500" />,
        color: "bg-amber-50/50 border-amber-200 dark:bg-amber-500/10 dark:border-amber-500/20",
        hoverColor: "hover:bg-amber-100/50 dark:hover:bg-amber-500/20"
    },
    {
        title: "Dagligvare",
        types: ["supermarket"],
        icon: <ShoppingCart size={18} className="text-emerald-500" />,
        color: "bg-emerald-50/50 border-emerald-200 dark:bg-emerald-500/10 dark:border-emerald-500/20",
        hoverColor: "hover:bg-emerald-100/50 dark:hover:bg-emerald-500/20"
    },
    {
        title: "Fritid & Kultur",
        types: ["park", "gym", "movie_theater", "museum", "library"],
        icon: <Trees size={18} className="text-purple-500" />,
        color: "bg-purple-50/50 border-purple-200 dark:bg-purple-500/10 dark:border-purple-500/20",
        hoverColor: "hover:bg-purple-100/50 dark:hover:bg-purple-500/20"
    }
];

interface AccessibilityStatsProps {
    propertyId: string;
    refreshKey?: number;
}

export default function AccessibilityStats({ propertyId, refreshKey = 0 }: AccessibilityStatsProps) {
    const [summary, setSummary] = useState<AccessibilitySummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState<string | null>(null);

    useEffect(() => {
        propertyService.getAccessibilitySummary(propertyId)
            .then(data => {
                setSummary(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load accessibility summary", err);
                setLoading(false);
            });
    }, [propertyId, refreshKey]);

    const toggleExpand = (title: string) => {
        setExpanded(expanded === title ? null : title);
    };

    return (
        <>
            {loading ? (
                <div className="h-32 animate-pulse bg-muted/10 rounded-xl"></div>
            ) : !summary ? null : (
                <div className="space-y-3">
                    <ProximityThresholds summary={summary} />
                    {categories.map((cat, idx) => {
                        // Find nearest service in this category & total count
                        let nearest: { name: string, distance: number, travelTime: number | null, type: string } | null = null;
                        let count = 0;

                        for (const type of cat.types) {
                            const typeCount = summary.service_counts[type] || 0;
                            count += typeCount;

                            const nearestType = summary.nearest_by_type[type];
                            if (nearestType) {
                                if (!nearest || nearestType.distance_meters < nearest.distance) {
                                    nearest = {
                                        name: nearestType.name,
                                        distance: nearestType.distance_meters,
                                        travelTime: nearestType.travel_time_minutes ?? null,
                                        type: type
                                    };
                                }
                            }
                        }

                        const isExpanded = expanded === cat.title;

                        return (
                            <div
                                key={cat.title}
                                className={`rounded-xl border ${cat.color} overflow-hidden transition-all duration-200 shadow-sm ${cat.hoverColor}`}
                            >
                                <button
                                    onClick={() => toggleExpand(cat.title)}
                                    className="w-full p-4 flex items-center justify-between text-left focus:outline-none"
                                >
                                    <div className="flex items-center gap-3 font-bold text-sm md:text-base text-foreground">
                                        {cat.icon}
                                        <span>{cat.title}</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {nearest && (
                                            <div className="text-[10px] text-right hidden sm:block">
                                                <div className="text-foreground font-bold uppercase tracking-tight">{(nearest.distance / 1000).toFixed(1)} km</div>
                                                <div className="text-muted font-mono font-medium">
                                                    {nearest.travelTime != null ? `${Math.round(nearest.travelTime)} min` : `${Math.ceil(nearest.distance / 500)} min`}
                                                </div>
                                            </div>
                                        )}
                                        <span className="text-xs font-mono font-bold bg-background/50 dark:bg-white/10 px-2 py-1 rounded min-w-7.5 text-center border border-border text-foreground">
                                            {count}
                                        </span>
                                        <svg
                                            className={`w-4 h-4 text-muted transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                                            fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                        >
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </button>

                                <AnimatePresence>
                                    {isExpanded && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <div className="px-4 pb-4 pt-0 border-t border-border">
                                                {nearest ? (
                                                    <div className="mt-4 text-sm">
                                                        <div className="flex justify-between items-start">
                                                            <div>
                                                                <div className="text-label mb-1">Nærmeste Tjeneste</div>
                                                                <div className="font-bold text-foreground">{nearest.name}</div>
                                                                <div className="text-xs text-muted capitalize mt-0.5 font-medium">{nearest.type}</div>
                                                            </div>
                                                            <div className="text-right bg-muted/10 p-2 rounded-lg border border-border">
                                                                <div className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{(nearest.distance / 1000).toFixed(2)} km</div>
                                                                <div className="text-[10px] text-muted font-bold uppercase tracking-widest">avstand</div>
                                                            </div>
                                                        </div>

                                                        {/* Future: Could list top 3 services here if the API supported returning a list per category */}
                                                    </div>
                                                ) : (
                                                    <div className="py-4 text-sm text-muted italic text-center font-medium">
                                                        Ingen tjenester registrert i denne kategorien.
                                                    </div>
                                                )}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        );
                    })}
                </div>
            )}
        </>
    );
}
