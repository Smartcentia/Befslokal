"use client";

import { motion } from "framer-motion";
import { Landmark, Users, Wallet } from "lucide-react";
import DataTooltip from "@/app/components/ui/DataTooltip";
import type { FinancialSummary } from "@/lib/api/propertiesApi";

const fmtNok = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

export interface PropertyFinanceYearCardProps {
    costYear: number | null;
    availableCostYears: number[];
    onYearChange: (year: number | null) => void;
    costStatusLoading: boolean;
    hasCostsForYear: boolean | null;
    costTotals: { total: number; rent: number; other: number } | null;
    lonnInfo: FinancialSummary["lonn"] | null;
    motionDelay?: number;
}

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
    return (
        <span
            className={
                ok
                    ? "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/25"
                    : "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-red-500/12 text-red-700 dark:text-red-400 border border-red-500/20"
            }
        >
            {label}: {ok ? "Ja" : "Nei"}
        </span>
    );
}

export default function PropertyFinanceYearCard({
    costYear,
    availableCostYears,
    onYearChange,
    costStatusLoading,
    hasCostsForYear,
    costTotals,
    lonnInfo,
    motionDelay = 0.23,
}: PropertyFinanceYearCardProps) {
    const glHarData = Boolean(
        costTotals && (costTotals.total > 0.0001 || costTotals.rent > 0 || costTotals.other > 0)
    );
    const harLonn = Boolean(lonnInfo?.har_data);
    const harRegnskap = glHarData;

    return (
        <motion.div
            className="glass-card p-0 overflow-hidden border border-border/60"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: motionDelay }}
        >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-5 pt-5 pb-3 border-b border-border/50 bg-muted/20">
                <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                        <Landmark className="h-5 w-5" aria-hidden />
                    </div>
                    <div className="min-w-0">
                        <DataTooltip content="Regnskapsdata fra GL (Agresso) koblet til eiendommen. Lønn kommer fra egen import (salary_costs), ikke fra GL-utdraget.">
                            <h3 className="font-bold text-foreground leading-tight">Regnskap og lønn</h3>
                        </DataTooltip>
                        <p className="text-[11px] text-muted-foreground mt-0.5">
                            Kostnader og husleie fra bokføring · lønn per eiendom
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <label htmlFor="property-finance-year" className="text-xs text-muted-foreground sr-only">
                        År
                    </label>
                    <select
                        id="property-finance-year"
                        value={costYear ?? ""}
                        onChange={(e) => onYearChange(e.target.value ? Number(e.target.value) : null)}
                        className="enterprise-input text-xs py-2 px-3 min-w-[5.5rem] rounded-lg border-border/80 bg-background/80"
                        aria-label="Velg år for regnskap og lønn"
                    >
                        {availableCostYears.map((yr) => (
                            <option key={yr} value={yr}>
                                {yr}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="p-5">
                {costStatusLoading ? (
                    <div className="space-y-2 animate-pulse">
                        <div className="h-4 bg-muted/40 rounded w-2/3" />
                        <div className="h-16 bg-muted/30 rounded-lg" />
                    </div>
                ) : costYear == null ? (
                    <p className="text-xs text-muted-foreground">Velg år.</p>
                ) : (
                    <div className="space-y-4">
                        <div className="flex flex-wrap gap-2">
                            <StatusPill ok={harRegnskap} label="GL / bokført" />
                            <StatusPill ok={harLonn} label="Lønnsdata" />
                            {lonnInfo?.har_data && lonnInfo.is_partial_year && (
                                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/25">
                                    Delår
                                </span>
                            )}
                        </div>
                        {hasCostsForYear === true && !glHarData && (
                            <p className="text-[11px] text-muted-foreground">
                                Andre kostnadsregistreringer for året finnes (se årskostnader under).
                            </p>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="rounded-xl border border-border/50 bg-background/40 p-4 space-y-3">
                                <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                                    <Wallet className="h-3.5 w-3.5 text-muted-foreground" aria-hidden />
                                    Bokført ({costYear})
                                </div>
                                {costTotals ? (
                                    <dl className="space-y-2 text-xs">
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">Total</dt>
                                            <dd className="font-mono tabular-nums font-medium text-foreground">
                                                {fmtNok(costTotals.total || 0)}
                                            </dd>
                                        </div>
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">Husleie</dt>
                                            <dd className="font-mono tabular-nums text-muted-foreground">
                                                {fmtNok(costTotals.rent || 0)}
                                            </dd>
                                        </div>
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">Andre kostnader</dt>
                                            <dd className="font-mono tabular-nums text-muted-foreground">
                                                {fmtNok(costTotals.other || 0)}
                                            </dd>
                                        </div>
                                    </dl>
                                ) : (
                                    <p className="text-xs text-muted-foreground">Ingen summer tilgjengelig.</p>
                                )}
                            </div>

                            <div className="rounded-xl border border-border/50 bg-background/40 p-4 space-y-3">
                                <DataTooltip content="Importert til salary_costs (f.eks. innkjøpsanalyse / Agresso-uttrekk). Ikke del av GL-kortet til venstre.">
                                    <div className="flex items-center gap-2 text-xs font-semibold text-foreground cursor-help">
                                        <Users className="h-3.5 w-3.5 text-muted-foreground shrink-0" aria-hidden />
                                        Lønn ({costYear})
                                    </div>
                                </DataTooltip>
                                {lonnInfo?.har_data ? (
                                    <dl className="space-y-2 text-xs">
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">Faste stillinger</dt>
                                            <dd className="font-mono tabular-nums text-muted-foreground">
                                                {fmtNok(lonnInfo.faste_stillinger || 0)}
                                            </dd>
                                        </div>
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">Vikarer</dt>
                                            <dd className="font-mono tabular-nums text-muted-foreground">
                                                {fmtNok(lonnInfo.vikarer || 0)}
                                            </dd>
                                        </div>
                                        <div className="flex justify-between gap-2">
                                            <dt className="text-muted-foreground">AGA</dt>
                                            <dd className="font-mono tabular-nums text-muted-foreground">
                                                {fmtNok(lonnInfo.arbeidsgiveravgift || 0)}
                                            </dd>
                                        </div>
                                        <div className="flex justify-between gap-2 pt-1 border-t border-border/40">
                                            <dt className="font-medium text-foreground">Sum</dt>
                                            <dd className="font-mono tabular-nums font-semibold text-foreground">
                                                {fmtNok(lonnInfo.totalt || 0)}
                                            </dd>
                                        </div>
                                    </dl>
                                ) : (
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        Ingen lønnsrad for {costYear}. Importer til <span className="font-mono">salary_costs</span> for denne eiendommen.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
