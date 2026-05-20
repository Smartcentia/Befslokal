"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { getPropertyAnnualCosts, type PropertyAnnualCost } from "@/lib/api/propertiesApi";

const AVAILABLE_YEARS = [2025, 2026];

const COST_ROWS: { key: keyof PropertyAnnualCost; label: string }[] = [
    { key: "kpi_adjusted_rent",    label: "KPI-justert leie" },
    { key: "internal_maintenance", label: "Indre vedlikehold" },
    { key: "common_costs",         label: "Felleskostnader" },
    { key: "energy_costs",         label: "Energi" },
    { key: "heating_costs",        label: "Oppvarming" },
    { key: "cleaning_costs",       label: "Renhold" },
    { key: "parking_rent",         label: "Parkering" },
    { key: "caretaker_cost",       label: "Vaktmester" },
    { key: "card_reader_cost",     label: "Kortleser" },
];

const fmt = (n: number | null) =>
    n == null || n === 0
        ? null
        : new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

interface AnnualCostsCardProps {
    propertyId: string;
    selectedYear?: number | null;
    onYearChange?: (year: number | null) => void;
    showYearSelector?: boolean;
}

export default function AnnualCostsCard({
    propertyId,
    selectedYear: selectedYearProp,
    onYearChange,
    showYearSelector = true,
}: AnnualCostsCardProps) {
    const [internalSelectedYear, setInternalSelectedYear] = useState<number | null>(null);
    const [costs, setCosts] = useState<PropertyAnnualCost[]>([]);
    const [loading, setLoading] = useState(false);

    const selectedYear = selectedYearProp ?? internalSelectedYear;

    useEffect(() => {
        if (selectedYearProp !== undefined) {
            setInternalSelectedYear(selectedYearProp);
        }
    }, [selectedYearProp]);

    const handleYearChange = (year: number | null) => {
        if (selectedYearProp === undefined) {
            setInternalSelectedYear(year);
        }
        onYearChange?.(year);
    };

    useEffect(() => {
        if (!selectedYear) return;
        setLoading(true);
        setCosts([]);
        getPropertyAnnualCosts(propertyId, selectedYear)
            .then(setCosts)
            .finally(() => setLoading(false));
    }, [propertyId, selectedYear]);

    const cost = costs[0] ?? null;

    const total = cost
        ? COST_ROWS.reduce((sum, { key }) => sum + (Number(cost[key]) || 0), 0)
        : null;

    return (
        <motion.div
            className="glass-card p-5"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
                    <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Kostnader per år
                </h3>
                {showYearSelector && (
                    <select
                        value={selectedYear ?? ""}
                        onChange={(e) => handleYearChange(e.target.value ? Number(e.target.value) : null)}
                        className="enterprise-input text-xs py-1 px-2 w-24"
                        aria-label="Velg år"
                    >
                        <option value="">Velg år</option>
                        {AVAILABLE_YEARS.map((y) => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                )}
            </div>

            {/* States */}
            {!selectedYear && (
                <p className="text-muted text-xs">Velg et år for å laste kostnadsoversikt.</p>
            )}

            {selectedYear && loading && (
                <div className="flex items-center gap-2 text-muted text-xs">
                    <svg className="animate-spin h-3.5 w-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Laster {selectedYear}…
                </div>
            )}

            {selectedYear && !loading && !cost && (
                <p className="text-muted text-xs italic">Ingen kostnadsdata registrert for {selectedYear}.</p>
            )}

            {selectedYear && !loading && cost && (
                <div className="space-y-1.5">
                    {COST_ROWS.map(({ key, label }) => {
                        const display = fmt(cost[key] as number | null);
                        if (!display) return null;
                        return (
                            <div key={key} className="flex justify-between items-center text-xs">
                                <span className="text-muted">{label}</span>
                                <span className="font-mono text-foreground tabular-nums">{display}</span>
                            </div>
                        );
                    })}

                    {total != null && total > 0 && (
                        <div className="flex justify-between items-center text-xs font-bold border-t border-border pt-2 mt-1">
                            <span className="text-foreground uppercase tracking-wide text-[10px]">Sum</span>
                            <span className="font-mono text-foreground tabular-nums">{fmt(total)}</span>
                        </div>
                    )}

                    {cost.other_costs && Object.keys(cost.other_costs).length > 0 && (
                        <details className="mt-2 group">
                            <summary className="text-[10px] text-muted cursor-pointer list-none flex items-center gap-1 hover:text-foreground transition-colors">
                                <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
                                Andre kostnader ({Object.keys(cost.other_costs).length})
                            </summary>
                            <div className="mt-1.5 space-y-1 pl-3">
                                {Object.entries(cost.other_costs).map(([k, v]) => (
                                    <div key={k} className="flex justify-between text-[10px]">
                                        <span className="text-muted">{k}</span>
                                        <span className="font-mono tabular-nums">{fmt(v as number) ?? "—"}</span>
                                    </div>
                                ))}
                            </div>
                        </details>
                    )}

                    <p className="text-[10px] text-muted/60 pt-1 border-t border-border/50 mt-1">
                        Kilde: Eiendomsportefølje {selectedYear}
                    </p>
                </div>
            )}
        </motion.div>
    );
}
