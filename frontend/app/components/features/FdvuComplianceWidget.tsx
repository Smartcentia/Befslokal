"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getComplianceSummary, getAssignments, type ComplianceSummary, type AssignmentWithAssessment } from '@/lib/api/fdvuApi';
import { ShieldCheck, AlertTriangle, Clock, ChevronRight, Zap } from 'lucide-react';
import { autoGenerateAssignments } from '@/lib/api/fdvuApi';

interface Props {
    propertyId: string;
}

export default function FdvuComplianceWidget({ propertyId }: Props) {
    const [summary, setSummary] = useState<ComplianceSummary | null>(null);
    const [assignments, setAssignments] = useState<AssignmentWithAssessment[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [autoMsg, setAutoMsg] = useState<string | null>(null);

    useEffect(() => {
        if (!propertyId) { setLoading(false); return; }
        Promise.all([
            getComplianceSummary(propertyId),
            getAssignments(propertyId),
        ]).then(([s, a]) => {
            setSummary(s);
            setAssignments(a);
            setLoading(false);
        });
    }, [propertyId]);

    const handleAutoGenerate = async () => {
        if (!propertyId) return;
        setGenerating(true);
        setAutoMsg(null);
        try {
            const res = await autoGenerateAssignments(propertyId);
            if (res.created > 0) {
                const [s, a] = await Promise.all([
                    getComplianceSummary(propertyId),
                    getAssignments(propertyId),
                ]);
                setSummary(s);
                setAssignments(a);
                setAutoMsg(`${res.created} krav tildelt.`);
            } else {
                setAutoMsg("Ingen nye krav å tildele for denne eiendommen.");
            }
        } catch {
            setAutoMsg("Feil ved auto-tildeling. Prøv igjen.");
        } finally {
            setGenerating(false);
        }
    };

    const pct = summary ? Math.round(summary.compliance_rate * 100) : null;
    const barColor = pct === null ? '#64748b' : pct >= 90 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444';

    return (
        <div className="bg-card border border-border rounded-xl p-5 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-sm text-foreground">
                    <ShieldCheck size={16} className="text-primary" />
                    FDVU Compliance
                </div>
                <Link
                    href={`/fdvu/${propertyId}`}
                    className="flex items-center gap-1 text-xs text-muted hover:text-primary transition-colors"
                >
                    Åpne <ChevronRight size={13} />
                </Link>
            </div>

            {loading ? (
                <div className="space-y-2 animate-pulse">
                    <div className="h-3 bg-border rounded-full w-full" />
                    <div className="h-3 bg-border rounded-full w-2/3" />
                </div>
            ) : assignments.length === 0 ? (
                <div className="space-y-3">
                    <p className="text-xs text-muted">Ingen krav tildelt ennå.</p>
                    <button
                        onClick={handleAutoGenerate}
                        disabled={generating}
                        className="flex items-center gap-2 w-full justify-center px-3 py-2 bg-primary/10 text-primary text-xs rounded-lg hover:bg-primary/20 transition-colors border border-primary/20 disabled:opacity-50"
                    >
                        <Zap size={12} />
                        {generating ? 'Genererer …' : 'Auto-tildel krav'}
                    </button>
                    {autoMsg && (
                        <p className="text-xs text-muted text-center">{autoMsg}</p>
                    )}
                </div>
            ) : (
                <>
                    {/* Progress bar */}
                    <div className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                            <span className="text-muted">Compliance-rate</span>
                            <span className="font-bold" style={{ color: barColor }}>{pct}%</span>
                        </div>
                        <div className="h-1.5 bg-border rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all"
                                style={{ width: `${pct}%`, backgroundColor: barColor }}
                            />
                        </div>
                    </div>

                    {/* Mini stats */}
                    <div className="grid grid-cols-3 gap-2 text-xs text-center">
                        <div className="bg-success/10 rounded-lg py-2">
                            <div className="font-bold text-success">{summary?.compliant ?? 0}</div>
                            <div className="text-muted">Oppfylt</div>
                        </div>
                        <div className="bg-destructive/10 rounded-lg py-2">
                            <div className="font-bold text-destructive">{summary?.non_compliant ?? 0}</div>
                            <div className="text-muted">Avvik</div>
                        </div>
                        <div className={`rounded-lg py-2 ${(summary?.overdue_reviews ?? 0) > 0 ? 'bg-warning/10' : 'bg-border/30'}`}>
                            <div className={`font-bold ${(summary?.overdue_reviews ?? 0) > 0 ? 'text-warning' : 'text-muted'}`}>
                                {summary?.overdue_reviews ?? 0}
                            </div>
                            <div className="text-muted">Forfalt</div>
                        </div>
                    </div>

                    {/* Alerts */}
                    {(summary?.non_compliant ?? 0) > 0 && (
                        <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">
                            <AlertTriangle size={12} />
                            {summary!.non_compliant} avvik krever oppfølging
                        </div>
                    )}
                    {(summary?.overdue_reviews ?? 0) > 0 && (
                        <div className="flex items-center gap-2 text-xs text-warning bg-warning/10 rounded-lg px-3 py-2">
                            <Clock size={12} />
                            {summary!.overdue_reviews} revisjon{summary!.overdue_reviews > 1 ? 'er' : ''} er forfalt
                        </div>
                    )}

                    {/* Not assessed nudge */}
                    {(summary?.not_assessed ?? 0) > 0 && (
                        <p className="text-xs text-muted">
                            {summary!.not_assessed} krav mangler vurdering.{' '}
                            <Link href={`/fdvu/${propertyId}`} className="text-primary underline underline-offset-2">
                                Vurder nå →
                            </Link>
                        </p>
                    )}
                </>
            )}
        </div>
    );
}
