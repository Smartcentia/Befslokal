"use client";

/**
 * WelcomeBriefing – vises øverst på dashbordet ved innlogging.
 * Henter dagens aktiviteter og viser en personalisert velkomsthilsen
 * fra KI Kollega med oppgaver for dagen.
 */

import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { fetchAPI } from "@/lib/api";
import {
    BrainCircuit,
    Calendar,
    CheckCircle2,
    Clock,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    ExternalLink,
    X,
    Sparkles,
} from "lucide-react";
import Link from "next/link";

const DAILY_BRIEFING_PROMPT = "Gi meg en kort oppsummering av hva som skal gjøres i dag: hvilke HMS-aktiviteter er planlagt, finnes det kritiske avvik som krever oppfølging, og er det noe annet jeg bør vite for i dag?";

function openKiKollegaWithDailyBriefing() {
    window.dispatchEvent(
        new CustomEvent("befs:open-ki-kollega-prompt", {
            detail: { prompt: DAILY_BRIEFING_PROMPT },
        })
    );
}

interface ScheduledActivity {
    activity_id: string;
    title: string;
    description?: string;
    next_due_date: string;
    status?: string;
    priority: string;
    property_name?: string;
    property_id?: string;
    responsible_role?: string;
}

function getDagNavn(): string {
    const dager = ["søndag", "mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag"];
    return dager[new Date().getDay()];
}

function getTimeOfDayGreeting(): string {
    const h = new Date().getHours();
    if (h < 10) return "God morgen";
    if (h < 13) return "God formiddag";
    if (h < 17) return "God ettermiddag";
    return "God kveld";
}

function getPriorityStyle(priority: string) {
    const p = priority?.toLowerCase();
    if (p === "critical" || p === "kritisk")
        return { dot: "bg-red-500", text: "text-red-700", badge: "bg-red-50 border-red-200 text-red-700" };
    if (p === "high" || p === "høy")
        return { dot: "bg-orange-500", text: "text-orange-700", badge: "bg-orange-50 border-orange-200 text-orange-700" };
    if (p === "medium")
        return { dot: "bg-yellow-500", text: "text-yellow-700", badge: "bg-yellow-50 border-yellow-200 text-yellow-700" };
    return { dot: "bg-green-500", text: "text-green-700", badge: "bg-green-50 border-green-200 text-green-700" };
}

const DISMISSED_KEY = "befs_briefing_dismissed";

export default function WelcomeBriefing() {
    const { user, loading: authLoading } = useAuth();
    const [activities, setActivities] = useState<ScheduledActivity[]>([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(true);
    const [dismissed, setDismissed] = useState(false);

    // Sjekk om brukeren allerede har lukket briefingen i dag
    useEffect(() => {
        const key = `${DISMISSED_KEY}_${new Date().toISOString().split("T")[0]}`;
        const wasDismissed = localStorage.getItem(key) === "1";
        setDismissed(wasDismissed);
    }, []);

    useEffect(() => {
        if (authLoading || !user) return;

        // Hent aktiviteter som forfaller innen 1 dag (dvs. i dag + morgendagen)
        fetchAPI<ScheduledActivity[]>(`/hms/activities/upcoming?days_ahead=1`)
            .then((data) => setActivities(Array.isArray(data) ? data.slice(0, 8) : []))
            .catch(() => setActivities([]))
            .finally(() => setLoading(false));
    }, [user, authLoading]);

    const handleAskKI = () => {
        openKiKollegaWithDailyBriefing();
    };

    const handleDismiss = () => {
        const key = `${DISMISSED_KEY}_${new Date().toISOString().split("T")[0]}`;
        localStorage.setItem(key, "1");
        setDismissed(true);
    };

    if (dismissed || authLoading || !user) return null;

    const firstName = user.email?.split("@")[0]?.split(".")?.[0] ?? "der";
    const capitalFirst = firstName.charAt(0).toUpperCase() + firstName.slice(1);
    const greeting = `${getTimeOfDayGreeting()}, ${capitalFirst}!`;
    const dagNavn = getDagNavn();

    const criticalCount = activities.filter((a) =>
        ["critical", "kritisk", "high", "høy"].includes((a.priority || "").toLowerCase())
    ).length;

    return (
        <div className="mb-6 rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5">
                <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-9 h-9 rounded-full bg-blue-600 shadow-sm">
                        <BrainCircuit size={18} className="text-white" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-blue-900">{greeting}</p>
                        <p className="text-xs text-blue-600/80 flex items-center gap-1">
                            <Calendar size={11} />
                            <span className="capitalize">{dagNavn}</span>
                            {" "}
                            {new Date().toLocaleDateString("nb-NO", {
                                day: "numeric",
                                month: "long",
                                year: "numeric",
                            })}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleAskKI}
                        className="flex items-center gap-1.5 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 px-3 py-1.5 rounded-lg transition-colors"
                        title="Spør KI Kollega om dagen"
                    >
                        <Sparkles size={13} />
                        Spør KI Kollega
                    </button>
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="text-blue-500 hover:text-blue-700 p-1.5 rounded-lg hover:bg-blue-100 transition-colors"
                        title={expanded ? "Minimer" : "Vis oppgaver"}
                    >
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    <button
                        onClick={handleDismiss}
                        className="text-blue-400 hover:text-blue-600 p-1.5 rounded-lg hover:bg-blue-100 transition-colors"
                        title="Lukk for i dag"
                    >
                        <X size={15} />
                    </button>
                </div>
            </div>

            {/* Innhold */}
            {expanded && (
                <div className="px-5 pb-4 border-t border-blue-100">
                    {loading ? (
                        <div className="flex items-center gap-2 py-3 text-sm text-blue-500">
                            <Sparkles size={14} className="animate-pulse" />
                            KI Kollega henter dagens oppgaver...
                        </div>
                    ) : activities.length === 0 ? (
                        <div className="py-3">
                            <p className="text-sm text-blue-700 flex items-center gap-2">
                                <CheckCircle2 size={16} className="text-green-500" />
                                Ingen planlagte aktiviteter for i dag — god dag!
                            </p>
                            <p className="text-xs text-blue-500 mt-1">
                                Du kan søke opp fremtidige aktiviteter i{" "}
                                <Link href="/hms/activities" className="underline hover:text-blue-700">
                                    HMS-aktiviteter
                                </Link>
                                .
                            </p>
                        </div>
                    ) : (
                        <div className="pt-3">
                            <div className="flex items-center justify-between mb-3">
                                <p className="text-xs font-medium text-blue-700 flex items-center gap-1.5">
                                    <Clock size={12} />
                                    {activities.length} aktivitet{activities.length !== 1 ? "er" : ""} forfaller i dag
                                    {criticalCount > 0 && (
                                        <span className="ml-1 flex items-center gap-0.5 text-red-600">
                                            <AlertTriangle size={11} />
                                            {criticalCount} prioritert
                                        </span>
                                    )}
                                </p>
                                <Link
                                    href="/hms/activities"
                                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-0.5 hover:underline"
                                >
                                    Se alle <ExternalLink size={10} />
                                </Link>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                                {activities.map((a) => {
                                    const style = getPriorityStyle(a.priority);
                                    return (
                                        <Link
                                            key={a.activity_id}
                                            href={a.property_id ? `/properties/${a.property_id}` : "/hms/activities"}
                                            className="flex items-start gap-2.5 bg-white/70 hover:bg-white border border-blue-100 rounded-lg px-3 py-2.5 transition-colors group"
                                        >
                                            <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />
                                            <div className="min-w-0">
                                                <p className="text-xs font-medium text-gray-800 truncate group-hover:text-blue-700 transition-colors">
                                                    {a.title}
                                                </p>
                                                {a.property_name && (
                                                    <p className="text-xs text-gray-400 truncate mt-0.5">{a.property_name}</p>
                                                )}
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
