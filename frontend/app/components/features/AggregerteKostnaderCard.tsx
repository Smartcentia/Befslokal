"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { getInnkjøpsanalyseHusleie } from "@/lib/api/propertiesApi";

const fmt = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

interface Props {
    propertyId: string;
}

export default function AggregerteKostnaderCard({ propertyId }: Props) {
    const [data2024, setData2024] = useState<{ aggregert: number } | null>(null);
    const [data2025, setData2025] = useState<{ aggregert: number } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        Promise.all([
            getInnkjøpsanalyseHusleie(2024),
            getInnkjøpsanalyseHusleie(2025),
        ])
            .then(([d4, d5]) => {
                const p4 = d4?.by_property?.[propertyId];
                const p5 = d5?.by_property?.[propertyId];
                setData2024(p4 ?? null);
                setData2025(p5 ?? null);
            })
            .finally(() => setLoading(false));
    }, [propertyId]);

    const agg2024 = data2024?.aggregert ?? 0;
    const agg2025 = data2025?.aggregert ?? 0;
    const hasData = agg2024 > 0 || agg2025 > 0;

    return (
        <motion.div
            className="glass-card p-5"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <h3 className="font-semibold text-sm text-foreground flex items-center gap-2 mb-4">
                <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Aggregerte kostnader
            </h3>
            <p className="text-[10px] text-muted mb-3">
                Total kost (husleie + løpende) fra Innkjøpsanalyse. Leie av lokaler og tilknyttede utgifter.
            </p>

            {loading && (
                <div className="h-16 bg-muted/30 rounded animate-pulse" />
            )}

            {!loading && !hasData && (
                <p className="text-muted text-xs italic">Ingen aggregerte kostnader fra Innkjøpsanalyse.</p>
            )}

            {!loading && hasData && (
                <div className="space-y-3">
                    {agg2024 > 0 && (
                        <div className="flex justify-between items-center">
                            <span className="text-xs text-muted">2024</span>
                            <span className="font-mono font-bold text-foreground">{fmt(agg2024)}</span>
                        </div>
                    )}
                    {agg2025 > 0 && (
                        <div className="flex justify-between items-center">
                            <span className="text-xs text-muted">2025</span>
                            <span className="font-mono font-bold text-primary">{fmt(agg2025)}</span>
                        </div>
                    )}
                    <p className="text-[10px] text-muted border-t border-border pt-2 mt-2">
                        Kilde: Innkjøpsanalyse (property_husleie_csv)
                    </p>
                </div>
            )}
        </motion.div>
    );
}
