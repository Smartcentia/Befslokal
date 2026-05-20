"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Building2, FileText, AlertTriangle, Wallet, Receipt, BedDouble } from "lucide-react";
import { getDashboardStats, DashboardStatsData } from "@/lib/api";
import { fetchAPI } from "@/lib/api/client";

export default function DashboardStats() {
    const [data, setData] = useState<DashboardStatsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [plasserBud, setPlasserBud] = useState<number | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const stats = await getDashboardStats();
                setData(stats);
                setError(null);
                // Hent budsjetterte plasser
                try {
                    const pl = await fetchAPI<{ antall_budsjetterte: number }>("/plasser/total");
                    setPlasserBud(pl.antall_budsjetterte);
                } catch { /* ikke kritisk */ }
            } catch (err: any) {
                console.error("Failed to fetch dashboard stats", err);
                setError(err.message || "Failed to load data");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm border border-red-200">
                Data Error: {error}
            </div>
        );
    }

    // Bruk kun faktiske tall fra API – ingen falske fallback-verdier
    const statsData = {
        properties: data?.properties ?? 0,
        contracts: data?.contracts ?? 0,
        risks: data?.risks ?? 0,
        totalAnnualRent: data?.total_annual_rent ?? 0,
        lokaler2026Nok: (data as any)?.lokaler_2026_nok ?? 0,
        driftVedlikehold2026: (data as any)?.drift_vedlikehold_2026 ?? 0,
    };

    const formatCurrency = (val: number) => {
        if (val > 1000000) return `${(val / 1000000).toFixed(1)} MNOK`;
        if (val > 1000) return `${(val / 1000).toFixed(0)} kNOK`;
        return `${val.toFixed(0)} NOK`;
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7 gap-4 mb-8">
            {/* 1. Properties */}
            {/* 1. Properties */}
            <Link href="/properties" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                        <Building2 size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">Antall eiendommer</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading ? "..." : statsData.properties}
                    </p>
                </div>
            </Link>

            {/* 2. Contracts */}
            {/* 2. Contracts */}
            <Link href="/contracts" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                        <FileText size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">Aktive kontrakter</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading ? "..." : statsData.contracts}
                    </p>
                </div>
            </Link>

            {/* 3. Deviations */}
            {/* 3. Deviations */}
            <Link href="/deviations" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                        <AlertTriangle size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">Åpne driftsavvik</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading ? "..." : statsData.risks}
                    </p>
                </div>
            </Link>

            {/* 4. Total husleie */}
            <Link href="/financials" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                        <Wallet size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">Regnskap 2025 (Øk.)</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading ? "..." : formatCurrency(statsData.totalAnnualRent)}
                    </p>
                    <span className="text-[10px] text-muted-foreground mt-0.5 inline-block">Kontant 2025 — økonomiavdelingen</span>
                    {!loading && statsData.lokaler2026Nok > 0 && (
                        <div className="mt-1 border-t border-border pt-1">
                            <span className="text-[11px] font-semibold text-foreground">{formatCurrency(statsData.lokaler2026Nok)}</span>
                            <span className="text-[10px] text-muted-foreground ml-1">budsjett 2026 (Øk.)</span>
                        </div>
                    )}
                </div>
            </Link>

            {/* 6. Budsjetterte institusjonsplasser 2026 */}
            <Link href="/financials" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-400 rounded-lg">
                        <BedDouble size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">Budsjetterte plasser</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading || plasserBud === null ? "..." : plasserBud}
                    </p>
                    <span className="text-[10px] text-muted-foreground mt-1 inline-block">Institusjonsplasser 2026</span>
                </div>
            </Link>

            {/* 7. Drift + Vedlikehold budsjett 2026 */}
            <Link href="/financials" className="bg-surface border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer block">
                <div className="flex justify-between items-start mb-3">
                    <div className="p-2 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 rounded-lg">
                        <Receipt size={20} />
                    </div>
                </div>
                <div>
                    <h3 className="text-xs font-semibold text-muted mb-0.5">BEFS Prediksjon 2026</h3>
                    <p className="text-2xl font-extrabold text-foreground tracking-tight">
                        {loading ? "..." : formatCurrency(statsData.driftVedlikehold2026)}
                    </p>
                    <span className="text-[10px] text-muted-foreground mt-1 inline-block">BEFS estimat — økonomiavdelingen</span>
                </div>
            </Link>
        </div>
    );
}
