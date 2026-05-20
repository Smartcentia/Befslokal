"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api/client";
import { getPropertyBudget } from "@/lib/api/budgetApi";
import { internalControlService } from "@/lib/domains/hms/internalControlService";
import DataTooltip from "@/app/components/ui/DataTooltip";

interface RiskAssessment {
    overall_risk_score?: number;
    risk_category?: string;
}

interface Props {
    propertyId: string;
    latestRiskAssessment?: RiskAssessment | null;
    /** År for GL-kostnader i kostnadsanalyse (samme som kostnadsår på eiendomssiden). */
    analysisYear?: number | null;
}

const formatCurrency = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

export default function PropertySteeringPanel({ propertyId, latestRiskAssessment, analysisYear }: Props) {
    const [costAnalysis, setCostAnalysis] = useState<{
        annual_rent: number;
        summary?: { operations_costs: number; investment_costs: number; total_costs: number };
    } | null>(null);
    const [budgetTotal, setBudgetTotal] = useState<number>(0);
    const [openDeviations, setOpenDeviations] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const yearQ =
            analysisYear != null && analysisYear > 0
                ? `?year=${analysisYear}`
                : "";
        Promise.all([
            fetchAPI(`/properties/${propertyId}/cost-analysis${yearQ}`).catch(() => null),
            getPropertyBudget(propertyId, 2026).catch(() => null),
            internalControlService.getPropertyCases(propertyId).then((cases) =>
                cases.filter((c) => c.status !== "closed" && c.status !== "lukket").length
            ),
        ]).then(([cost, budgetRes, count]) => {
            setCostAnalysis(cost ?? null);
            setBudgetTotal(budgetRes?.total_annual_budget ?? 0);
            setOpenDeviations(count ?? 0);
            setLoading(false);
        });
    }, [propertyId, analysisYear]);

    if (loading) {
        return (
            <div className="glass-card p-4 animate-pulse">
                <div className="h-4 bg-muted rounded w-1/3 mb-3" />
                <div className="grid grid-cols-2 gap-2">
                    <div className="h-10 bg-muted rounded" />
                    <div className="h-10 bg-muted rounded" />
                </div>
            </div>
        );
    }

    const annualRent = costAnalysis?.annual_rent ?? 0;
    const totalCosts = costAnalysis?.summary?.total_costs ?? 0;
    const annualCost = annualRent + totalCosts;
    const opex = costAnalysis?.summary?.operations_costs ?? 0;
    const capex = costAnalysis?.summary?.investment_costs ?? 0;
    const budgetCoverage = annualCost > 0 && budgetTotal > 0 ? (budgetTotal / annualCost) * 100 : 0;
    const riskScore = latestRiskAssessment?.overall_risk_score ?? 0;

    return (
        <div className="glass-card p-4">
            <DataTooltip content="Styringspanel: Nøkkeltall for prioritering og ressursallokering. Brukes til beslutningsstøtte.">
                <h3 className="font-bold text-sm mb-3 flex items-center gap-2 text-foreground">
                    <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Styringspanel
                </h3>
            </DataTooltip>
            <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                    <DataTooltip content="Risikoscore: 0–100. Brukes som prioriteringsparameter for ressursallokering.">
                        <div className="text-muted font-medium">Risikoscore</div>
                    </DataTooltip>
                    <div className={`font-bold ${riskScore > 75 ? "text-destructive" : riskScore > 40 ? "text-amber-500" : "text-foreground"}`}>
                        {Math.round(riskScore)}
                    </div>
                </div>
                <div>
                    <DataTooltip content="Årlig kostnad: Husleie + utgifter (Drift + Investering). Brukes i prioriteringsindeks.">
                        <div className="text-muted font-medium">Årlig kostnad</div>
                    </DataTooltip>
                    <div className="font-bold text-foreground">{formatCurrency(annualCost)}</div>
                </div>
                <div>
                    <DataTooltip content="Drift: Driftskostnader (renhold, strøm, felleskostnader). Investeringer: Større påkostninger.">
                        <div className="text-muted font-medium">Drift / Investering</div>
                    </DataTooltip>
                    <div className="font-bold text-foreground">
                        {formatCurrency(opex)} / {formatCurrency(capex)}
                    </div>
                </div>
                <div>
                    <DataTooltip content="Budsjettdekning: Budsjett som andel av årlig kostnad. 100% = full dekning.">
                        <div className="text-muted font-medium">Budsjettdekning</div>
                    </DataTooltip>
                    <div className="font-bold text-foreground">{budgetCoverage > 0 ? `${Math.round(budgetCoverage)}%` : "-"}</div>
                </div>
                <div className="col-span-2">
                    <DataTooltip content="Tiltaksstatus: Antall åpne avvik i internkontroll som venter på oppfølging.">
                        <div className="text-muted font-medium">Åpne avvik</div>
                    </DataTooltip>
                    <div className="font-bold text-foreground">{openDeviations}</div>
                </div>
            </div>
        </div>
    );
}
