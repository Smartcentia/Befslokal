"use client";

import React, { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Upload, CheckCircle2, XCircle, AlertTriangle, Info, ArrowLeft, ChevronDown, ChevronRight } from "lucide-react";
import { getApiAuthContext } from "@/lib/api/client";

// ─── Types ────────────────────────────────────────────────────────────────────

interface RuleResult {
    rule_id: string;
    description: string;
    status: "PASS" | "WARN" | "FAIL" | "N/A";
    passed: number;
    failed: number;
    total: number;
    pass_rate: number;
    failed_guids: string[];
}

interface DisciplineResult {
    discipline: string;
    label: string;
    overall_status: "PASS" | "WARN" | "FAIL";
    compliance_pct: number;
    total_rules: number;
    passed_rules: number;
    warn_rules: number;
    failed_rules: number;
    na_rules: number;
    rules: RuleResult[];
}

interface SIMBAReport {
    property_id: string;
    filename: string;
    schema: string;
    project_name: string;
    warnings: string[];
    summary: {
        disciplines_checked: number;
        disciplines_na: number;
        disciplines_passed: number;
        disciplines_warned: number;
        disciplines_failed: number;
    };
    disciplines: DisciplineResult[];
}

// ─── Hjelpere ─────────────────────────────────────────────────────────────────

function statusColor(status: string) {
    if (status === "PASS") return "text-green-600";
    if (status === "WARN") return "text-yellow-600";
    if (status === "FAIL") return "text-red-600";
    return "text-muted-foreground";
}

function statusBg(status: string) {
    if (status === "PASS") return "bg-green-50 border-green-200";
    if (status === "WARN") return "bg-yellow-50 border-yellow-200";
    if (status === "FAIL") return "bg-red-50 border-red-200";
    return "bg-muted border-border";
}

function StatusIcon({ status }: { status: string }) {
    if (status === "PASS") return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    if (status === "WARN") return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    if (status === "FAIL") return <XCircle className="w-4 h-4 text-red-600" />;
    return <Info className="w-4 h-4 text-muted-foreground" />;
}

function ComplianceBar({ pct }: { pct: number }) {
    const color = pct >= 90 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-500";
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
            </div>
            <span className="text-xs font-mono w-10 text-right">{pct.toFixed(0)}%</span>
        </div>
    );
}

// ─── Hoved-komponent ─────────────────────────────────────────────────────────

export default function SIMBAPage() {
    const { id: propertyId } = useParams<{ id: string }>();
    const router = useRouter();

    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState<SIMBAReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const toggleDisc = (code: string) =>
        setExpanded(prev => {
            const next = new Set(prev);
            next.has(code) ? next.delete(code) : next.add(code);
            return next;
        });

    const handleValidate = useCallback(async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setReport(null);
        try {
            const { token } = await getApiAuthContext();
            const form = new FormData();
            form.append("file", file);
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/fdvu/simba/${propertyId}/validate`,
                {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` },
                    body: form,
                }
            );
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            const data: SIMBAReport = await res.json();
            setReport(data);
            // Åpne disipliner med feil automatisk
            const toOpen = new Set<string>();
            data.disciplines.forEach(d => {
                if (d.overall_status === "FAIL") toOpen.add(d.discipline);
            });
            setExpanded(toOpen);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }, [file, propertyId]);

    const summary = report?.summary;

    return (
        <div className="min-h-screen bg-background text-foreground p-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex items-center gap-3">
                <button
                    onClick={() => router.back()}
                    className="p-2 rounded-lg hover:bg-accent transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold">SIMBA 2.1 Validering</h1>
                    <p className="text-sm text-muted-foreground">
                        Statsbygg BIM-krav · 12 disipliner · IFC 4
                    </p>
                </div>
            </div>

            {/* Upload-kort */}
            <div className="rounded-xl border border-border bg-card p-6 mb-6">
                <h2 className="font-semibold mb-4 flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Last opp IFC-fil for validering
                </h2>
                <div className="flex gap-3 items-start flex-wrap">
                    <label className="cursor-pointer flex-1 min-w-48">
                        <div className="border-2 border-dashed border-border rounded-lg p-4 text-center hover:border-primary transition-colors">
                            {file ? (
                                <p className="text-sm font-medium">{file.name}</p>
                            ) : (
                                <p className="text-sm text-muted-foreground">Klikk for å velge .ifc-fil</p>
                            )}
                        </div>
                        <input
                            type="file"
                            accept=".ifc"
                            className="hidden"
                            onChange={e => setFile(e.target.files?.[0] ?? null)}
                        />
                    </label>
                    <button
                        onClick={handleValidate}
                        disabled={!file || loading}
                        className="px-5 py-3 rounded-lg bg-primary text-primary-foreground font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
                    >
                        {loading ? "Validerer…" : "Valider mot SIMBA 2.1"}
                    </button>
                </div>
                {error && (
                    <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                        {error}
                    </div>
                )}
            </div>

            {/* IFC-advarsler */}
            {report?.warnings && report.warnings.length > 0 && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 mb-6">
                    {report.warnings.map((w, i) => (
                        <p key={i} className="text-sm text-yellow-800 flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                            {w}
                        </p>
                    ))}
                </div>
            )}

            {/* Sammendrag */}
            {summary && (
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
                    {[
                        { label: "Sjekket", value: summary.disciplines_checked, color: "text-foreground" },
                        { label: "Bestått", value: summary.disciplines_passed, color: "text-green-600" },
                        { label: "Advarsel", value: summary.disciplines_warned, color: "text-yellow-600" },
                        { label: "Feilet", value: summary.disciplines_failed, color: "text-red-600" },
                        { label: "Ikke relevant", value: summary.disciplines_na, color: "text-muted-foreground" },
                    ].map(card => (
                        <div key={card.label} className="rounded-xl border border-border bg-card p-4 text-center">
                            <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
                            <p className="text-xs text-muted-foreground mt-1">{card.label}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Disipliner */}
            {report && (
                <div className="space-y-3">
                    <h2 className="font-semibold text-lg">
                        Resultat per disiplin
                        <span className="text-sm font-normal text-muted-foreground ml-2">
                            · {report.project_name} · {report.schema}
                        </span>
                    </h2>

                    {report.disciplines.map(d => {
                        const isOpen = expanded.has(d.discipline);
                        const isNA = d.total_rules === 0;
                        return (
                            <div
                                key={d.discipline}
                                className={`rounded-xl border ${isNA ? "border-border bg-muted/30" : statusBg(d.overall_status)}`}
                            >
                                {/* Disiplin-header */}
                                <button
                                    className="w-full px-5 py-4 flex items-center gap-3 text-left"
                                    onClick={() => !isNA && toggleDisc(d.discipline)}
                                    disabled={isNA}
                                >
                                    <StatusIcon status={isNA ? "N/A" : d.overall_status} />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-mono font-bold text-sm">{d.discipline}</span>
                                            <span className="font-medium">{d.label}</span>
                                            {!isNA && (
                                                <span className={`text-xs font-medium ${statusColor(d.overall_status)}`}>
                                                    {d.overall_status}
                                                </span>
                                            )}
                                            {isNA && (
                                                <span className="text-xs text-muted-foreground">Ikke relevant for denne filen</span>
                                            )}
                                        </div>
                                        {!isNA && (
                                            <div className="mt-1.5 max-w-xs">
                                                <ComplianceBar pct={d.compliance_pct} />
                                            </div>
                                        )}
                                    </div>
                                    {!isNA && (
                                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                            <span className="text-green-600">{d.passed_rules} OK</span>
                                            {d.warn_rules > 0 && <span className="text-yellow-600">{d.warn_rules} adv.</span>}
                                            {d.failed_rules > 0 && <span className="text-red-600">{d.failed_rules} feil</span>}
                                            {isOpen
                                                ? <ChevronDown className="w-4 h-4" />
                                                : <ChevronRight className="w-4 h-4" />
                                            }
                                        </div>
                                    )}
                                </button>

                                {/* Regler */}
                                {isOpen && (
                                    <div className="border-t border-border divide-y divide-border">
                                        {d.rules.map(r => (
                                            <div key={r.rule_id} className="px-5 py-3 flex items-start gap-3">
                                                <StatusIcon status={r.status} />
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="font-mono text-xs text-muted-foreground">{r.rule_id}</span>
                                                        <span className="text-sm">{r.description}</span>
                                                    </div>
                                                    {r.total > 0 && (
                                                        <p className="text-xs text-muted-foreground mt-0.5">
                                                            {r.passed}/{r.total} elementer ({r.pass_rate}%)
                                                            {r.failed_guids.length > 0 && (
                                                                <span className="ml-2 text-red-600">
                                                                    Eks.: {r.failed_guids.slice(0, 3).join(", ")}
                                                                    {r.failed_guids.length > 3 ? ` +${r.failed_guids.length - 3} til` : ""}
                                                                </span>
                                                            )}
                                                        </p>
                                                    )}
                                                    {r.total === 0 && (
                                                        <p className="text-xs text-muted-foreground mt-0.5">
                                                            Ingen elementer av denne typen i filen
                                                        </p>
                                                    )}
                                                </div>
                                                <span className={`text-xs font-medium shrink-0 ${statusColor(r.status)}`}>
                                                    {r.status}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Tom tilstand */}
            {!report && !loading && (
                <div className="text-center py-16 text-muted-foreground">
                    <Upload className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p className="font-medium">Last opp en IFC-fil for å starte validering</p>
                    <p className="text-sm mt-1">
                        SIMBA 2.1 dekker 12 disipliner og over 30 individuelle krav
                    </p>
                </div>
            )}
        </div>
    );
}
