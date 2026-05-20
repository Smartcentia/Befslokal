"use client";
import React, { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api/client';
import { getPropertyBudget } from '@/lib/api/budgetApi';
import DataTooltip from '@/app/components/ui/DataTooltip';

interface CostAnalysisData {
    property_id: string;
    property_name: string;
    annual_rent: number;
    synthetic_rent?: boolean;
    summary: {
        property_costs: number;
        operations_costs: number;
        investment_costs: number;
        other_costs: number;
        total_costs: number;
    };
    ratios: {
        property_ratio: number;
        operations_ratio: number;
        investment_ratio: number;
        total_ratio: number;
    };
    assessment: string;
    anomalies: Array<{
        type: string;
        provider: string;
        amount: number;
        reason: string;
    }>;
    suspected_duplicates: Array<{
        provider: string;
        amount: number;
        count: number;
        total: number;
    }>;
    expenses_by_category: {
        property: CostExpense[];
        operations: CostExpense[];
        investment: CostExpense[];
        other: CostExpense[];
    };
}

interface CostExpense {
    type: string;
    provider: string;
    amount: number;
    flags?: string[];
}

interface Props {
    propertyId: string;
    selectedYear?: number | null;
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('nb-NO', {
        style: 'currency',
        currency: 'NOK',
        maximumFractionDigits: 0
    }).format(value);
};

const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(0)}%`;
};

export default function CostAnalysisWidget({ propertyId, selectedYear }: Props) {
    const [analysis, setAnalysis] = useState<CostAnalysisData | null>(null);
    const [budget, setBudget] = useState<{ total: number; by_category: Record<string, number> } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

    useEffect(() => {
        Promise.all([
            fetchAPI(`/properties/${propertyId}/cost-analysis${selectedYear ? `?year=${selectedYear}` : ''}`),
            getPropertyBudget(propertyId, 2026).catch(() => null)
        ]).then(([data, budgetRes]) => {
            setAnalysis(data ?? null);
            if (budgetRes) {
                const byCat = budgetRes.by_category ?? (budgetRes.monthly_budgets ?? []).reduce(
                    (acc: Record<string, number>, m: { category: string; amount: number }) => {
                        acc[m.category] = (acc[m.category] ?? 0) + m.amount;
                        return acc;
                    },
                    {} as Record<string, number>
                );
                setBudget({
                    total: budgetRes.total_annual_budget,
                    by_category: {
                        property: byCat.property ?? 0,
                        operations: byCat.operations ?? 0,
                        investment: byCat.investment ?? 0,
                        other: byCat.other ?? 0,
                    }
                });
            } else {
                setBudget(null);
            }
            setLoading(false);
        }).catch(err => {
            console.error("Error loading cost analysis:", err);
            setError("Kunne ikke laste kostnadsanalyse");
            setLoading(false);
        });
    }, [propertyId, selectedYear]);

    if (loading) {
        return (
            <div className="animate-pulse space-y-4">
                <div className="h-4 bg-muted rounded w-1/3"></div>
                <div className="h-20 bg-muted rounded"></div>
            </div>
        );
    }

    if (error || !analysis) {
        return (
            <div className="text-muted text-sm p-4 border border-dashed border-border rounded-lg">
                <p className="text-center">{error || "Ingen kostnadsdata tilgjengelig"}</p>
                {budget != null && budget.total > 0 && (
                    <p className="text-center mt-3 text-emerald-600 dark:text-emerald-400 font-semibold">
                        Budsjett 2026: {formatCurrency(budget.total)}
                    </p>
                )}
            </div>
        );
    }

    const { summary, ratios, assessment, anomalies, suspected_duplicates, expenses_by_category } = analysis;

    // Determine overall status color (muted når husleie mangler – ratioer er da meningsløse)
    const getStatusColor = () => {
        if (analysis.annual_rent <= 0) return 'text-muted bg-muted/20 border-muted/40';
        if (ratios.total_ratio > 3) return 'text-red-600 dark:text-red-400 bg-red-500/10 border-red-500/30';
        if (ratios.total_ratio > 2) return 'text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30';
        if (ratios.total_ratio > 1.5) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
        return 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    };

    const categoryConfig = {
        property: { label: 'Eiendom-kostnader', color: 'blue', icon: '🏢', description: 'Husleie, fellesutgifter, vedlikehold og kommunale avgifter. Direkte knyttet til bygget.' },
        operations: { label: 'Drift-kostnader', color: 'orange', icon: '⚙️', description: 'Renhold, strøm, vakthold, vaktmester. Løpende driftsutgifter.' },
        investment: { label: 'Investeringer', color: 'purple', icon: '📈', description: 'Oppgraderinger, påkostning, inventar. Utgifter over 50 000 kr klassifiseres som investering.' },
        other: { label: 'Andre kostnader', color: 'gray', icon: '📋', description: 'Uklassifiserte utgifter som ikke passer i andre kategorier.' }
    };

    // Forklarende tooltip: beregning og betydning (viser ved hover)
    const otherRatio = analysis.annual_rent > 0 ? summary.other_costs / analysis.annual_rent : 0;
    const hasRent = analysis.annual_rent > 0;
    const budgetNote = budget ? ` Budsjett (fra budsjettgenerering) vs Faktisk (bokførte kostnader).` : '';
    const tooltipText = [
        `Bokførte kostnader: ${formatCurrency(summary.total_costs)}.`,
        budget ? `Budsjett totalt: ${formatCurrency(budget.total)}.` : '',
        hasRent
            ? `Forhold til husleie: (${formatCurrency(summary.total_costs)} ÷ ${formatCurrency(analysis.annual_rent)}) × 100% = ${formatPercent(ratios.total_ratio)}.`
            : "Manglende husleiedata – ratioer ikke beregnet (unngår deling på null).",
        `Oppdeling: Eiendomskostnader ${formatCurrency(summary.property_costs)} (${formatPercent(ratios.property_ratio)}), Drift ${formatCurrency(summary.operations_costs)} (${formatPercent(ratios.operations_ratio)}), Investeringer ${formatCurrency(summary.investment_costs)} (${formatPercent(ratios.investment_ratio)}), Andre ${formatCurrency(summary.other_costs)} (${formatPercent(otherRatio)}).`,
        `Sum: ${formatCurrency(summary.property_costs)} + ${formatCurrency(summary.operations_costs)} + ${formatCurrency(summary.investment_costs)} + ${formatCurrency(summary.other_costs)} = ${formatCurrency(summary.total_costs)}.`,
        budgetNote,
        assessment ? `Vurdering: ${assessment.replace(/\n/g, ' ')}` : ''
    ].filter(Boolean).join(' ');

    return (
        <div className="space-y-6">
            {/* Overall Assessment */}
            <DataTooltip content={tooltipText} as="div" className="block">
                <div
                    className={`p-4 rounded-xl border cursor-help ${getStatusColor()}`}
                >
                    <div className="flex items-start justify-between mb-3 gap-2">
                        <div className="min-w-0 shrink">
                            <h4 className="font-bold text-xs uppercase tracking-wider mb-1">Budsjett 2026</h4>
                            <p className="text-xs opacity-70">Forhold til husleie: {formatPercent(ratios.total_ratio)}</p>
                        </div>
                        <div className="text-right shrink-0">
                            <div className="text-base font-bold leading-tight">{formatCurrency(summary.total_costs)}</div>
                            <div className="text-xs opacity-70">vs husleie {formatCurrency(analysis.annual_rent)}{analysis.synthetic_rent ? ' (estimat)' : ''}</div>
                        </div>
                    </div>
                    <div className="text-xs whitespace-pre-line opacity-90 border-t border-border pt-3 mt-3">
                        {assessment}
                    </div>
                </div>
            </DataTooltip>

            {/* Category Breakdown: Budsjett + Faktisk per kategori */}
            <div className="grid grid-cols-2 gap-3">
                {Object.entries(categoryConfig).map(([key, config]) => {
                    const costKey = `${key}_costs` as keyof typeof summary;
                    const ratioKey = `${key}_ratio` as keyof typeof ratios;
                    const expenses = expenses_by_category[key as keyof typeof expenses_by_category] || [];
                    const cost = summary[costKey] || 0;
                    const ratio = ratios[ratioKey] || 0;
                    const budgetAmt = budget?.by_category?.[key as keyof typeof budget.by_category] ?? 0;
                    const variance = budgetAmt > 0 ? budgetAmt - cost : 0;
                    const variancePct = budgetAmt > 0 ? (variance / budgetAmt) * 100 : 0;
                    const isOverBudget = cost > budgetAmt && budgetAmt > 0;
                    const isUnderBudget = cost < budgetAmt && budgetAmt > 0;

                    const tooltipContent = [
                        `${config.label}: ${config.description}`,
                        budgetAmt > 0
                            ? `Budsjett: ${formatCurrency(budgetAmt)}. Faktisk: ${formatCurrency(cost)}. Varians: ${variance >= 0 ? '+' : ''}${formatCurrency(variance)} (${variancePct >= 0 ? '+' : ''}${variancePct.toFixed(0)}%). ${isUnderBudget ? 'Faktisk under budsjett (gunstig).' : isOverBudget ? 'Faktisk over budsjett.' : ''}`
                            : `Faktisk: ${formatCurrency(cost)}. Forhold til husleie: ${formatPercent(ratio)}.`,
                        `«Poster» = antall utgiftsposter i kategorien.`
                    ].join(' ');

                    return (
                        <DataTooltip key={key} content={tooltipContent}>
                            <button
                                type="button"
                                onClick={() => setExpandedCategory(expandedCategory === key ? null : key)}
                                title={`Se detaljer for ${config.label}`}
                                className={`p-3 rounded-lg border transition-all text-left w-full ${
                                    expandedCategory === key
                                        ? 'bg-muted border-primary'
                                        : isOverBudget
                                            ? 'bg-red-500/5 border-red-500/30 hover:border-red-500/50'
                                            : isUnderBudget
                                                ? 'bg-emerald-500/5 border-emerald-500/30 hover:border-emerald-500/50'
                                                : 'bg-muted/50 border-border hover:border-primary/50'
                                }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span>{config.icon}</span>
                                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                        {config.label}
                                    </span>
                                </div>
                                <div className="flex justify-between items-baseline gap-2 mb-0.5">
                                    {budgetAmt > 0 ? (
                                        <>
                                            <span className="text-xs text-muted">Budsjett: {formatCurrency(budgetAmt)}</span>
                                            <span className="text-xs text-muted">Faktisk: {formatCurrency(cost)}</span>
                                        </>
                                    ) : (
                                        <span className="text-sm font-bold text-foreground">{formatCurrency(cost)}</span>
                                    )}
                                </div>
                                {budgetAmt > 0 && (
                                    <div className={`text-[10px] font-medium mb-0.5 ${
                                        isOverBudget ? 'text-red-600 dark:text-red-400' : isUnderBudget ? 'text-emerald-600 dark:text-emerald-400' : 'text-muted'
                                    }`}>
                                        {isOverBudget ? `Over budsjett med ${formatCurrency(-variance)}` : isUnderBudget ? `Under budsjett med ${formatCurrency(variance)}` : 'På budsjett'}
                                    </div>
                                )}
                                <div className="text-[10px] text-muted">
                                    {formatPercent(ratio)} av husleie | {expenses.length} poster
                                </div>
                            </button>
                        </DataTooltip>
                    );
                })}
            </div>

            {/* Expanded Category Details */}
            {expandedCategory && (
                <div className="bg-muted/10 rounded-lg border border-border overflow-hidden">
                    <div className="px-4 py-2 bg-muted/20 border-b border-border flex justify-between items-center">
                        <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                            {categoryConfig[expandedCategory as keyof typeof categoryConfig]?.label}
                        </span>
                        <button
                            type="button"
                            onClick={() => setExpandedCategory(null)}
                            className="text-muted hover:text-foreground"
                            title="Lukk detaljer"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            <span className="sr-only">Lukk</span>
                        </button>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                        <table className="w-full text-xs">
                            <tbody className="divide-y divide-border">
                                {expenses_by_category[expandedCategory as keyof typeof expenses_by_category]?.slice(0, 20).map((exp, idx: number) => (
                                    <tr key={idx} className="hover:bg-muted/10">
                                        <td className="px-3 py-2 text-muted">{exp.type}</td>
                                        <td className="px-3 py-2 text-foreground truncate max-w-37.5" title={exp.provider}>
                                            {exp.provider}
                                        </td>
                                        <td className={`px-3 py-2 text-right font-mono ${exp.amount < 0 ? 'text-red-500' : 'text-foreground'}`}>
                                            {formatCurrency(exp.amount)}
                                        </td>
                                        <td className="px-3 py-2">
                                            {exp.flags?.length > 0 && (
                                                <span className="text-amber-500 text-[10px]" title={exp.flags.join(', ')}>
                                                    ⚠️
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {expenses_by_category[expandedCategory as keyof typeof expenses_by_category]?.length > 20 && (
                            <div className="px-3 py-2 text-center text-xs text-muted">
                                + {expenses_by_category[expandedCategory as keyof typeof expenses_by_category].length - 20} flere poster
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Anomalies */}
            {anomalies.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Anomalier ({anomalies.length})
                    </h4>
                    <ul className="space-y-2 text-xs">
                        {anomalies.map((anomaly, idx) => (
                            <li key={idx} className="flex justify-between items-start">
                                <div>
                                    <span className="text-foreground font-medium">{anomaly.type}</span>
                                    <span className="text-muted ml-2">- {anomaly.provider}</span>
                                    <div className="text-red-600/70 dark:text-red-400/70 text-[10px]">{anomaly.reason}</div>
                                </div>
                                <span className="text-red-600 dark:text-red-400 font-mono">{formatCurrency(anomaly.amount)}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Suspected Duplicates */}
            {suspected_duplicates.length > 0 && (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Potensielle duplikater ({suspected_duplicates.length})
                    </h4>
                    <ul className="space-y-2 text-xs">
                        {suspected_duplicates.slice(0, 5).map((dup, idx) => (
                            <li key={idx} className="flex justify-between items-center">
                                <div>
                                    <span className="text-foreground">{dup.provider || 'Ukjent'}</span>
                                    <span className="text-muted ml-2">x{dup.count} like poster</span>
                                </div>
                                <span className="text-amber-600 dark:text-amber-400 font-mono">{formatCurrency(dup.total)}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
