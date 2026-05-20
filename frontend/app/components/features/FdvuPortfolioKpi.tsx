"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchAPI } from "@/lib/api/client";
import { ShieldAlert, ShieldCheck, Clock, AlertTriangle } from "lucide-react";

interface PortfolioSummary {
    total_assignments: number;
    compliant: number;
    non_compliant: number;
    partial: number;
    not_assessed: number;
    not_applicable: number;
    overdue_reviews: number;
    compliance_rate: number;
    properties_with_assignments: number;
}

export default function FdvuPortfolioKpi() {
    const [data, setData] = useState<PortfolioSummary | null>(null);

    useEffect(() => {
        fetchAPI<PortfolioSummary>("/fdvu/compliance/portfolio-summary")
            .then(setData)
            .catch(() => null);
    }, []);

    // Don't render if no FDVU data yet
    if (!data || data.total_assignments === 0) return null;

    const rate = Math.round(data.compliance_rate * 100);
    const rateColor =
        rate >= 80 ? "text-success" : rate >= 60 ? "text-warning" : "text-destructive";
    const barColor =
        rate >= 80 ? "bg-success" : rate >= 60 ? "bg-warning" : "bg-destructive";

    return (
        <Link
            href="/fdvu"
            className="block rounded-xl border border-border bg-surface hover:border-primary/40 transition-colors mb-4"
        >
            <div className="px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-primary" />
                        <span className="text-sm font-semibold text-foreground">
                            FDVU Compliance
                        </span>
                        {data.properties_with_assignments > 0 && (
                            <span className="text-xs text-muted">
                                {data.properties_with_assignments} eiendommer
                            </span>
                        )}
                    </div>
                    <span className={`text-lg font-bold font-mono ${rateColor}`}>
                        {rate} %
                    </span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-1.5 bg-border rounded-full mb-3">
                    <div
                        className={`h-1.5 rounded-full transition-all ${barColor}`}
                        style={{ width: `${rate}%` }}
                    />
                </div>

                <div className="flex items-center gap-4 text-xs">
                    <span className="flex items-center gap-1 text-success">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        {data.compliant} OK
                    </span>
                    {data.non_compliant > 0 && (
                        <span className="flex items-center gap-1 text-destructive">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            {data.non_compliant} avvik
                        </span>
                    )}
                    {data.overdue_reviews > 0 && (
                        <span className="flex items-center gap-1 text-warning">
                            <Clock className="w-3.5 h-3.5" />
                            {data.overdue_reviews} forfalt
                        </span>
                    )}
                    {data.not_assessed > 0 && (
                        <span className="text-muted">{data.not_assessed} ikke vurdert</span>
                    )}
                </div>
            </div>
        </Link>
    );
}
