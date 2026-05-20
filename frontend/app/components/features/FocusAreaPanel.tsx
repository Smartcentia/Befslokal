"use client";

import { useEffect, useState } from "react";
import { getDashboardStats, DashboardStatsData } from "@/lib/api";
import { AlertOctagon, ShieldAlert, Clock, CheckCircle } from "lucide-react";
import Link from "next/link";

interface RiskPanelProps {
    systemStatus?: any; // Kept for prop compatibility, ignored
    loading?: boolean;
}

export default function FocusAreaPanel({ loading: parentLoading }: RiskPanelProps) {
    const [stats, setStats] = useState<DashboardStatsData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const data = await getDashboardStats();
                setStats(data);
            } catch (err) {
                console.error("Failed to load risk stats", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const isLoading = loading || parentLoading;

    return (
        <div className="space-y-6 h-full flex flex-col">
            {/* Header for the Panel */}
            <div className="flex items-center gap-2 pb-4 border-b border-border">
                <ShieldAlert className="text-amber-500" size={20} />
                <h2 className="text-lg font-bold text-foreground tracking-tight">Mine Fokusområder</h2>
            </div>

            {/* Live Focus Areas Widget */}
            <div className="glass-card p-5 relative overflow-hidden group flex-1">

                <div className="space-y-4 relative z-10">

                    {/* 1. Critical Deviations */}
                    <Link href="/deviations?priority=critical" className="block group/item">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/5 border border-red-500/20 group-hover/item:border-red-500/50 transition-colors cursor-pointer">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-red-500/10 rounded-full text-red-500">
                                    <AlertOctagon size={18} />
                                </div>
                                <div>
                                    <div className="text-sm font-bold text-foreground">Kritiske Avvik</div>
                                    <div className="text-xs text-muted">Krever umiddelbar tiltak</div>
                                </div>
                            </div>
                            <div className="text-xl font-bold text-red-500">
                                {isLoading ? "..." : stats?.critical_deviations || 0}
                            </div>
                        </div>
                    </Link>

                    {/* 2. Expiring Contracts */}
                    <Link href="/contracts?filter=expiring" className="block group/item">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 group-hover/item:border-amber-500/50 transition-colors cursor-pointer">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-amber-500/10 rounded-full text-amber-500">
                                    <Clock size={18} />
                                </div>
                                <div>
                                    <div className="text-sm font-bold text-foreground">Utløper Snart</div>
                                    <div className="text-xs text-muted">Neste 90 dager</div>
                                </div>
                            </div>
                            <div className="text-xl font-bold text-amber-500">
                                {isLoading ? "..." : stats?.expiring_contracts || 0}
                            </div>
                        </div>
                    </Link>

                    {/* 3. Action Button / Summary */}
                    {stats && stats.critical_deviations === 0 && stats.expiring_contracts === 0 ? (
                        <div className="mt-4 p-4 text-center">
                            <CheckCircle className="mx-auto text-emerald-500 mb-2" size={32} />
                            <p className="text-sm font-bold text-emerald-500">Alt ser bra ut!</p>
                            <p className="text-xs text-muted">Ingen kritiske hendelser.</p>
                        </div>
                    ) : (
                        <div className="mt-4">
                            <Link href="/deviations" className="block w-full py-2 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider text-center rounded transition-colors">
                                Se detaljer
                            </Link>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
