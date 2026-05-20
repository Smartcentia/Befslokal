"use client";

import React from "react";
import { TrendingUp, TrendingDown, Minus, Users, Building2, MessageSquare } from "lucide-react";
import DataTooltip from "@/app/components/ui/DataTooltip";
import type { YearSummary } from "@/lib/api/financialAnalysisApi";

// Korte forklaringer per år — basert på GL-dataanalyse og kjente hendelser
const ANNOTATIONS: Record<number, { short: string; detail: string }> = {
    2020: {
        short: "COVID-19: redusert aktivitet",
        detail: "Pandemi-år: lavere drifts- og vedlikeholdsaktivitet. Husleie holdes stabil men andre kostnader faller markant.",
    },
    2021: {
        short: "Husleie -20%: kontraktsgap",
        detail: "Overgangsår med kontrakt-gap og færre registrerte eiendommer i GL. Andre kostnader stabile.",
    },
    2022: {
        short: "Energikrise + Statsbygg-renovering",
        detail: "Strøm +65% (europeisk energikrise). To store Statsbygg-oppgraderinger i Q4: 11.6 + 10.3 MNOK. Reell kostnadsøkning.",
    },
    2023: {
        short: "Normalisering etter renovering",
        detail: "Energipriser stabilisert, store renoveringsprosjekter avsluttet. Husleie +2.3% i tråd med KPI.",
    },
    2024: {
        short: "Andre kost. -9.9%: nettokorreksjon",
        detail: "Vedlikehold og reparasjon netto lavere — ÅB-reversaler balanserer ut kostposter fra 2022–2023.",
    },
    2025: {
        short: "Stabil drift, ny kontoplan",
        detail: "Agresso innførte ny kontokode 'Fast bygningsinventar og påkostning, leide bygg'. Netto andre kostnader tilbake til normalnivå (~203 MNOK).",
    },
    2026: {
        short: "Estimat — ingen GL-data ennå",
        detail: "Budsjettert basert på 2025-nivå + prisjustering. GL-import for 2026 foreligger ikke.",
    },
};

// Ansattetall fra offentlige årsrapporter (Bufdir/Bufetat)
const ANSATTE: Record<number, { antall: number | null; kilde: string }> = {
    2020: { antall: 6100,  kilde: "Bufetat årsrapport 2020 (estimert)" },
    2021: { antall: 6200,  kilde: "Bufetat årsrapport 2021 (estimert)" },
    2022: { antall: 6518,  kilde: "Bufdir årsrapport 2024 (historisk)" },
    2023: { antall: 6464,  kilde: "Bufdir årsrapport 2024 (historisk)" },
    2024: { antall: 6550,  kilde: "Bufdir årsrapport 2024" },
    2025: { antall: null,  kilde: "Ikke publisert ennå" },
    2026: { antall: null,  kilde: "Ikke publisert ennå" },
};

function fmtM(n: number): string {
    if (n === 0) return "—";
    return (n / 1_000_000).toFixed(1) + " M";
}

function DeltaBadge({ current, prev }: { current: number; prev: number | undefined }) {
    if (!prev || prev === 0 || current === 0) return null;
    const pct = ((current - prev) / prev) * 100;
    if (Math.abs(pct) < 0.05) {
        return <span className="text-[10px] text-muted flex items-center gap-0.5"><Minus size={9} /> 0%</span>;
    }
    const up = pct > 0;
    const color = up ? "text-rose-400" : "text-emerald-400";
    const Icon = up ? TrendingUp : TrendingDown;
    return (
        <span className={`flex items-center gap-0.5 text-[10px] font-semibold ${color}`}>
            <Icon size={9} />
            {up ? "+" : ""}{pct.toFixed(1)}%
        </span>
    );
}

interface Props {
    data: YearSummary[];
    selectedYear: number;
    onYearChange: (y: number) => void;
}

export default function YearlyCostInsightBox({ data, selectedYear, onYearChange }: Props) {
    if (!data || data.length === 0) return null;

    return (
        <div className="mb-6 mt-4">
            <div className="flex items-center gap-2 mb-3">
                <span className="text-sm font-bold uppercase tracking-widest text-muted">
                    Kostnadsutvikling 2020–2026
                </span>
                <span className="text-xs text-muted/50">· Klikk år for å velge</span>
            </div>

            <div className="grid grid-cols-7 gap-2">
                {data.map((yr, idx) => {
                    const prev = idx > 0 ? data[idx - 1] : undefined;
                    const isSelected = yr.year === selectedYear;
                    const ansatte = ANSATTE[yr.year];
                    const annotation = ANNOTATIONS[yr.year];
                    const hasData = yr.gl_totalt > 0;

                    return (
                        <button
                            key={yr.year}
                            onClick={() => onYearChange(yr.year)}
                            className={`glass-card p-3 text-left transition-all rounded-lg border cursor-pointer
                                ${isSelected
                                    ? "border-amber-500 shadow-md shadow-amber-500/20 bg-amber-500/5"
                                    : "border-border/50 hover:border-primary/40 hover:bg-muted/5"
                                }`}
                        >
                            {/* År-header */}
                            <div className={`text-sm font-bold mb-2 flex items-center gap-1 ${isSelected ? "text-amber-400" : "text-muted"}`}>
                                {yr.year}
                                {yr.year === 2026 && (
                                    <span className="text-[9px] text-muted/50 font-normal">est.</span>
                                )}
                            </div>

                            {hasData ? (
                                <>
                                    {/* Husleie */}
                                    <div className="mb-2">
                                        <div className="text-[9px] text-sky-400 uppercase tracking-wide font-semibold mb-0.5">Husleie</div>
                                        <div className="flex items-center gap-1 flex-wrap">
                                            <span className="text-xs font-semibold tabular-nums">{fmtM(yr.gl_husleie)}</span>
                                            <DeltaBadge current={yr.gl_husleie} prev={prev?.gl_husleie} />
                                        </div>
                                    </div>

                                    {/* Andre kostnader */}
                                    <div className="mb-2">
                                        <div className="text-[9px] text-amber-400 uppercase tracking-wide font-semibold mb-0.5">Andre kost.</div>
                                        <div className="flex items-center gap-1 flex-wrap">
                                            <span className="text-xs font-semibold tabular-nums">{fmtM(yr.gl_andre)}</span>
                                            <DeltaBadge current={yr.gl_andre} prev={prev?.gl_andre} />
                                        </div>
                                    </div>

                                    {/* Lønn */}
                                    {yr.salary_totalt > 0 && (
                                        <div className="mb-2">
                                            <div className="text-[9px] text-rose-400 uppercase tracking-wide font-semibold mb-0.5">Lønn</div>
                                            <div className="flex items-center gap-1 flex-wrap">
                                                <span className="text-xs font-semibold tabular-nums">{fmtM(yr.salary_totalt)}</span>
                                                <DeltaBadge current={yr.salary_totalt} prev={prev?.salary_totalt} />
                                            </div>
                                        </div>
                                    )}

                                    {/* Separator */}
                                    <div className="border-t border-border/30 mt-2 pt-1.5 space-y-1">
                                        {/* Eiendommer */}
                                        <div className="flex items-center gap-1">
                                            <Building2 size={9} className="text-muted/40 shrink-0" />
                                            <span className="text-[10px] text-muted tabular-nums">
                                                {yr.property_count} eiendom{yr.property_count !== 1 ? "mer" : ""}
                                            </span>
                                        </div>

                                        {/* Ansatte */}
                                        {ansatte && (
                                            <DataTooltip content={`Kilde: ${ansatte.kilde}`}>
                                                <div className="flex items-center gap-1">
                                                    <Users size={9} className="text-muted/40 shrink-0" />
                                                    <span className="text-[10px] text-muted tabular-nums">
                                                        {ansatte.antall != null
                                                            ? "~" + ansatte.antall.toLocaleString("no-NO") + " ans."
                                                            : "—"}
                                                    </span>
                                                </div>
                                            </DataTooltip>
                                        )}
                                    </div>

                                    {/* Kommentar / årsforklaring */}
                                    {annotation && (
                                        <DataTooltip content={annotation.detail}>
                                            <div className="border-t border-border/20 mt-2 pt-1.5 flex items-start gap-1 cursor-help">
                                                <MessageSquare size={8} className="text-muted/30 shrink-0 mt-0.5" />
                                                <span className="text-[9px] text-muted/50 italic leading-tight line-clamp-2">
                                                    {annotation.short}
                                                </span>
                                            </div>
                                        </DataTooltip>
                                    )}
                                </>
                            ) : (
                                <>
                                    <div className="text-xs text-muted/40 mt-1 italic">Ingen data</div>
                                    {annotation && (
                                        <DataTooltip content={annotation.detail}>
                                            <div className="border-t border-border/20 mt-2 pt-1.5 flex items-start gap-1 cursor-help">
                                                <MessageSquare size={8} className="text-muted/30 shrink-0 mt-0.5" />
                                                <span className="text-[9px] text-muted/50 italic leading-tight line-clamp-2">
                                                    {annotation.short}
                                                </span>
                                            </div>
                                        </DataTooltip>
                                    )}
                                </>
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
