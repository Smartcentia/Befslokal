"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
    AlertOctagon,
    FileCheck,
    Building2,
    Activity,
    CalendarClock,
    Sparkles,
} from "lucide-react";
import {
    getRecentActivity,
    getDashboardStats,
    type RecentActivityItem,
} from "@/lib/api";

const iconMap: Record<string, React.ComponentType<{ size?: number }>> = {
    AlertOctagon,
    FileCheck,
    Building2,
    Activity,
};

function formatTime(timeStr: string): string {
    const d = new Date(timeStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    if (diffHours < 1) return "Nettopp";
    if (diffHours < 24) return `${diffHours}t siden`;
    if (diffDays === 1) return "I går";
    if (diffDays < 7) return `${diffDays} dager siden`;
    return d.toLocaleDateString("nb-NO", { day: "numeric", month: "short" });
}

export default function RecentUpdatesPanel() {
    const [activity, setActivity] = useState<RecentActivityItem[]>([]);
    const [expiringCount, setExpiringCount] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [act, stats] = await Promise.all([
                    getRecentActivity(7),
                    getDashboardStats(),
                ]);
                setActivity(Array.isArray(act) ? act : []);
                setExpiringCount(
                    (stats as { expiring_contracts?: number })?.expiring_contracts ?? 0
                );
            } catch {
                setActivity([]);
                setExpiringCount(0);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    return (
        <div className="glass-card p-6 bg-background/60 flex flex-col h-full">
            <div className="flex items-center gap-2 mb-5">
                <Sparkles size={20} className="text-primary" />
                <h3 className="text-xl font-bold text-foreground">Nye oppdateringer</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
                Siste aktivitet og kommende hendelser
            </p>

            {/* Kontrakter utløper snart */}
            {expiringCount > 0 && (
                <Link
                    href="/contracts"
                    className="mb-4 p-3 rounded-xl border border-warning/30 bg-warning/10 hover:bg-warning/15 transition-colors flex items-center gap-3 group"
                >
                    <div className="p-2 rounded-lg bg-warning/20">
                        <CalendarClock size={18} className="text-warning" />
                    </div>
                    <div className="flex-1">
                        <span className="font-semibold text-foreground">
                            {expiringCount} kontrakt{expiringCount !== 1 ? "er" : ""} utløper innen 90 dager
                        </span>
                        <span className="block text-xs text-muted-foreground mt-0.5">
                            Klikk for å se oversikt
                        </span>
                    </div>
                    <span className="text-muted group-hover:text-primary text-xs transition-colors">
                        →
                    </span>
                </Link>
            )}

            {/* Aktivitetslogg */}
            <div className="flex-1 min-h-[180px] overflow-hidden flex flex-col">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">
                    Siste aktivitet
                </h4>
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Activity className="animate-spin text-muted" size={24} />
                    </div>
                ) : activity.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-muted text-sm py-8 rounded-xl border border-dashed border-border">
                        Ingen nylige hendelser
                    </div>
                ) : (
                    <div className="space-y-2 overflow-y-auto custom-scrollbar pr-1">
                        {activity.slice(0, 6).map((item, i) => {
                            const Icon = iconMap[item.icon] || Activity;
                            return (
                                <div
                                    key={i}
                                    className="flex items-start gap-3 p-3 rounded-lg bg-surface/50 hover:bg-surface border border-transparent hover:border-border/50 transition-colors"
                                >
                                    <div
                                        className={`p-1.5 rounded-md flex-shrink-0 ${
                                            item.type === "deviation"
                                                ? "bg-amber-500/10 text-amber-500"
                                                : item.type === "contract"
                                                  ? "bg-blue-500/10 text-blue-500"
                                                  : "bg-muted/10 text-muted-foreground"
                                        }`}
                                    >
                                        <Icon size={14} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-foreground truncate">{item.text}</p>
                                        <span className="text-xs text-muted font-mono">
                                            {formatTime(item.time)}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
                {!loading && activity.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                        <Link
                            href="/activities/hub"
                            className="text-xs font-semibold text-primary hover:opacity-80"
                        >
                            Se all aktivitet →
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}
