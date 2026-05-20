"use client";

import { useEffect, useState } from "react";
import { TrendingUp, BarChart3, PieChart, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { getDashboardStats, DashboardStatsData } from "@/lib/api";
import Link from 'next/link';

export default function AnalysisPanel() {
    const [stats, setStats] = useState<DashboardStatsData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const data = await getDashboardStats();
                setStats(data);
            } catch (err) {
                console.error("Failed to load analysis stats", err);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    const formatCurrency = (val?: number | string) => {
        if (val === undefined || val === null) return "...";
        const numVal = Number(val);
        if (isNaN(numVal)) return "Invalid";

        // Convert to Millions (MNOK) for display if large enough, else kNOK
        if (numVal > 1000000) {
            return `${(numVal / 1000000).toFixed(1)} MNOK`;
        }
        return `${(numVal / 1000).toFixed(0)} kNOK`;
    };

    return (
        <div className="h-full flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-2 border-b border-border">
                <BarChart3 className="text-primary" size={20} />
                <h2 className="text-lg font-bold text-foreground tracking-tight">Analyse & Økonomi</h2>
            </div>

            <div className="flex flex-col gap-4 flex-1">
                {/* Widget 1: Total Leieinntekt */}
                <Link href="/financials?view=rent" className="glass-card p-5 flex flex-col justify-between group cursor-pointer hover:border-primary/50 transition-all">
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-label">Total Årlig Leie</span>
                        <PieChart size={20} className="text-muted group-hover:text-foreground transition-colors" />
                    </div>
                    <div>
                        <div className="text-3xl font-bold text-foreground tracking-tight">
                            {loading ? "..." : formatCurrency(stats?.total_annual_rent)}
                        </div>
                        <div className="flex items-center gap-1.5 text-primary text-[10px] font-bold uppercase tracking-wider mt-2">
                            <span>YTD (Estimert kostnad)</span>
                        </div>
                    </div>
                </Link>

</div>
        </div>
    );
}
