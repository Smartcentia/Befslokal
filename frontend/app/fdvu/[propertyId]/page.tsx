"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
    getAssignments, getComplianceSummary, getFdvDocuments, getFdvuSections,
    autoGenerateAssignments, upsertAssessment, createFdvuSection,
    getPropertyComponents, updateTilstand, bulkAssess,
    fdvuKiAssist,
    type AssignmentWithAssessment, type ComplianceSummary,
    type FdvDocument, type FdvuSection, type ComponentTilstand,
    type FdvuSectionCreate, type KiAssistResponse,
} from '@/lib/api/fdvuApi';
import { fetchAPI } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
    ShieldCheck, Clock, FileText, ChevronLeft,
    RefreshCw, Zap, CheckCircle2, XCircle, Minus, HelpCircle,
    ExternalLink, Plus, Wrench, AlertCircle, Download, Square, CheckSquare,
    Sparkles, ThumbsUp, ThumbsDown, Loader2, FileSearch, Leaf, ClipboardList,
} from 'lucide-react';

// ─────────────────────────────────────────────
// Konstanter
// ─────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    compliant:      { label: 'Oppfylt',      color: 'text-success',     icon: <CheckCircle2 size={14} className="text-success" /> },
    non_compliant:  { label: 'Avvik',         color: 'text-destructive', icon: <XCircle size={14} className="text-destructive" /> },
    partial:        { label: 'Delvis',        color: 'text-warning',     icon: <Minus size={14} className="text-warning" /> },
    not_assessed:   { label: 'Ikke vurdert',  color: 'text-muted',       icon: <HelpCircle size={14} className="text-muted" /> },
    not_applicable: { label: 'Ikke aktuelt',  color: 'text-muted',       icon: <Minus size={14} className="text-muted" /> },
};

const SEV_META: Record<string, string> = {
    critical: 'bg-destructive/15 text-destructive border-destructive/30',
    high:     'bg-orange-500/15 text-orange-400 border-orange-500/30',
    medium:   'bg-warning/15 text-warning border-warning/30',
    low:      'bg-success/15 text-success border-success/30',
};

const REGULATION_LABELS: Record<string, string> = {
    RKL6: 'Risikoklasse 6', BVL: 'Barnevernloven', TEK17: 'TEK17',
    HMS: 'HMS / AML', KVALITETSFORSKRIFTEN: 'Kvalitetsforskriften', INTERN: 'Intern',
};

const TG_META: Record<string, { label: string; desc: string; color: string; bg: string }> = {
    TG0: { label: 'TG0', desc: 'Ingen symptomer', color: 'text-success',     bg: 'bg-success/15 border-success/30' },
    TG1: { label: 'TG1', desc: 'Svake symptomer',  color: 'text-warning',     bg: 'bg-warning/15 border-warning/30' },
    TG2: { label: 'TG2', desc: 'Middels',          color: 'text-orange-400',  bg: 'bg-orange-500/15 border-orange-500/30' },
    TG3: { label: 'TG3', desc: 'Kraftige avvik',   color: 'text-destructive', bg: 'bg-destructive/15 border-destructive/30' },
};

const SECTION_TYPES = ['boform', 'fellesareal', 'administrasjon', 'uteareal'];

// ─────────────────────────────────────────────
// SummaryBar
// ─────────────────────────────────────────────

function SummaryBar({ summary }: { summary: ComplianceSummary }) {
    const pct = Math.round(summary.compliance_rate * 100);
    const barColor = pct >= 90 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444';
    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
                <span className="text-muted">Compliance-rate</span>
                <span className="font-bold" style={{ color: barColor }}>{pct}%</span>
            </div>
            <div className="h-2 bg-border rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: barColor }} />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs text-center mt-2">
                <div><div className="text-success font-semibold">{summary.compliant}</div><div className="text-muted">Oppfylt</div></div>
                <div><div className="text-destructive font-semibold">{summary.non_compliant}</div><div className="text-muted">Avvik</div></div>
                <div><div className="text-warning font-semibold">{summary.overdue_reviews}</div><div className="text-muted">Forfalt</div></div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// NySeksjonModal
// ─────────────────────────────────────────────

function NySeksjonModal({ propertyId, onClose, onSaved }: {
    propertyId: string; onClose: () => void; onSaved: () => void;
}) {
    const [form, setForm] = useState<FdvuSectionCreate>({
        property_id: propertyId, name: '', section_type: 'boform',
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const save = async () => {
        if (!form.name.trim()) { setError('Navn er påkrevd'); return; }
        setSaving(true); setError(null);
        try {
            await createFdvuSection(form);
            onSaved(); onClose();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Lagring feilet');
        } finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
                <h2 className="font-semibold text-foreground">Ny seksjon / avdeling</h2>
                <div className="space-y-3">
                    <div>
                        <label className="text-xs text-muted">Navn *</label>
                        <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                            value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="f.eks. Avdeling A" />
                    </div>
                    <div>
                        <label className="text-xs text-muted">Type</label>
                        <div className="mt-1 grid grid-cols-2 gap-2">
                            {SECTION_TYPES.map(t => (
                                <button key={t} onClick={() => setForm(f => ({ ...f, section_type: t }))}
                                    className={`px-3 py-2 rounded-lg border text-sm transition-colors ${form.section_type === t ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                    {t}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs text-muted">Etasje</label>
                            <input type="number" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                                value={form.floor ?? ''} onChange={e => setForm(f => ({ ...f, floor: e.target.value ? +e.target.value : undefined }))} />
                        </div>
                        <div>
                            <label className="text-xs text-muted">Areal (m²)</label>
                            <input type="number" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                                value={form.area_sqm ?? ''} onChange={e => setForm(f => ({ ...f, area_sqm: e.target.value ? +e.target.value : undefined }))} />
                        </div>
                    </div>
                    <div>
                        <label className="text-xs text-muted">Kapasitet (plasser)</label>
                        <input type="number" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                            value={form.capacity ?? ''} onChange={e => setForm(f => ({ ...f, capacity: e.target.value ? +e.target.value : undefined }))} />
                    </div>
                </div>
                {error && <p className="text-destructive text-xs">{error}</p>}
                <div className="flex gap-2 justify-end">
                    <button onClick={onClose} className="px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors">Avbryt</button>
                    <button onClick={save} disabled={saving} className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                        {saving ? 'Lagrer …' : 'Opprett'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// AssessmentModal
// ─────────────────────────────────────────────

const CONFIDENCE_META: Record<string, { label: string; cls: string }> = {
    high:   { label: 'Høy sikkerhet',   cls: 'text-success bg-success/10 border-success/30' },
    medium: { label: 'Middels sikkerhet', cls: 'text-warning bg-warning/10 border-warning/30' },
    low:    { label: 'Lav sikkerhet',    cls: 'text-muted bg-muted/10 border-border' },
};

function AssessmentModal({ propertyId, assignment, onClose, onSaved }: {
    propertyId: string;
    assignment: AssignmentWithAssessment; onClose: () => void; onSaved: () => void;
}) {
    const [assessStatus, setAssessStatus] = useState(assignment.compliance_assessment?.status ?? 'not_assessed');
    const [notes, setNotes] = useState(assignment.compliance_assessment?.evidence_notes ?? '');
    const [nextReview, setNextReview] = useState(assignment.compliance_assessment?.next_review_date ?? '');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // KI-assist state
    const [kiSuggestion, setKiSuggestion] = useState<KiAssistResponse | null>(null);
    const [kiLoading, setKiLoading] = useState(false);
    const [kiDismissed, setKiDismissed] = useState(false);

    const save = async () => {
        setSaving(true); setError(null);
        try {
            await upsertAssessment({ assignment_id: assignment.assignment_id, status: assessStatus, evidence_notes: notes || undefined, next_review_date: nextReview || undefined });
            onSaved(); onClose();
        } catch (e) { setError(e instanceof Error ? e.message : 'Lagring feilet'); }
        finally { setSaving(false); }
    };

    const handleKiAssist = async () => {
        setKiLoading(true);
        setKiDismissed(false);
        try {
            const suggestion = await fdvuKiAssist(propertyId, assignment.assignment_id);
            setKiSuggestion(suggestion);
        } catch {
            setError('KI-vurdering feilet – prøv igjen');
        } finally { setKiLoading(false); }
    };

    const acceptSuggestion = () => {
        if (!kiSuggestion) return;
        setAssessStatus(kiSuggestion.suggested_status);
        setNotes(kiSuggestion.evidence_notes);
        if (kiSuggestion.next_review_months) {
            const d = new Date();
            d.setMonth(d.getMonth() + kiSuggestion.next_review_months);
            setNextReview(d.toISOString().split('T')[0]);
        }
        setKiDismissed(true);
    };

    const req = assignment.requirement;
    const confMeta = kiSuggestion ? (CONFIDENCE_META[kiSuggestion.confidence] ?? CONFIDENCE_META.low) : null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div>
                    <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                            <div className="text-xs text-muted font-mono mb-1">{req?.code}</div>
                            <h2 className="font-semibold text-foreground">{req?.title}</h2>
                            {req?.description && <p className="text-xs text-muted mt-1 leading-relaxed">{req.description}</p>}
                        </div>
                        {/* KI-forslag knapp */}
                        <button
                            onClick={handleKiAssist}
                            disabled={kiLoading}
                            title="Be KI om vurderingsforslag basert på eiendomsdata"
                            className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary/40 bg-primary/5 text-primary hover:bg-primary/15 transition-colors text-xs font-medium disabled:opacity-60"
                        >
                            {kiLoading
                                ? <Loader2 size={13} className="animate-spin" />
                                : <Sparkles size={13} />}
                            {kiLoading ? 'Analyserer …' : 'KI-forslag'}
                        </button>
                    </div>
                    {assessStatus === 'non_compliant' && (
                        <div className="mt-2 flex items-center gap-2 text-xs text-warning bg-warning/10 rounded-lg px-3 py-2">
                            <AlertCircle size={12} />
                            Et avvik (InternalControlCase) opprettes automatisk ved lagring.
                        </div>
                    )}
                </div>

                {/* KI-forslagskort */}
                {kiSuggestion && !kiDismissed && (
                    <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 space-y-3">
                        <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                                <Sparkles size={14} className="text-primary" />
                                <span className="text-xs font-semibold text-primary">KI-anbefaling</span>
                            </div>
                            {confMeta && (
                                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${confMeta.cls}`}>
                                    {confMeta.label}
                                </span>
                            )}
                        </div>

                        {/* Foreslått status */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-muted">Foreslått status:</span>
                            <span className={`text-xs font-semibold ${STATUS_META[kiSuggestion.suggested_status]?.color ?? 'text-foreground'}`}>
                                {STATUS_META[kiSuggestion.suggested_status]?.label ?? kiSuggestion.suggested_status}
                            </span>
                            {kiSuggestion.next_review_months && (
                                <span className="text-xs text-muted ml-1">· neste revisjon om {kiSuggestion.next_review_months} mnd</span>
                            )}
                        </div>

                        {/* Forklaring */}
                        <p className="text-xs text-foreground/80 leading-relaxed">{kiSuggestion.explanation}</p>

                        {/* Dokumentasjonsnotat */}
                        {kiSuggestion.evidence_notes && (
                            <div className="bg-background/60 rounded-lg px-3 py-2 text-xs text-muted italic leading-relaxed">
                                &ldquo;{kiSuggestion.evidence_notes}&rdquo;
                            </div>
                        )}

                        {/* Aksjon-knapper */}
                        <div className="flex gap-2 pt-1">
                            <button
                                onClick={acceptSuggestion}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors"
                            >
                                <ThumbsUp size={12} /> Bruk forslag
                            </button>
                            <button
                                onClick={() => setKiDismissed(true)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted hover:text-foreground transition-colors"
                            >
                                <ThumbsDown size={12} /> Avvis
                            </button>
                        </div>
                    </div>
                )}

                {/* Status-velger */}
                <div className="space-y-1">
                    <label className="text-xs text-muted font-medium">Status</label>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(STATUS_META).map(([key, meta]) => (
                            <button key={key} onClick={() => setAssessStatus(key)}
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors ${assessStatus === key ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                {meta.icon} {meta.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-muted font-medium">Neste revisjonsdato</label>
                    <input type="date" value={nextReview} onChange={e => setNextReview(e.target.value)}
                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary" />
                </div>
                <div className="space-y-1">
                    <label className="text-xs text-muted font-medium">Dokumentasjon / merknader</label>
                    <textarea rows={3} value={notes} onChange={e => setNotes(e.target.value)}
                        placeholder="Beskriv tiltak, avvik eller dokumentasjonsreferanse …"
                        className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground resize-none focus:outline-none focus:border-primary" />
                </div>
                {error && <p className="text-destructive text-xs">{error}</p>}
                <div className="flex gap-2 justify-end">
                    <button onClick={onClose} className="px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors">Avbryt</button>
                    <button onClick={save} disabled={saving}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 ${assessStatus === 'non_compliant' ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90' : 'bg-primary text-primary-foreground hover:bg-primary/90'}`}>
                        {saving ? 'Lagrer …' : assessStatus === 'non_compliant' ? 'Lagre + opprett avvik' : 'Lagre'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// FdvuKiPanel – flytende KI-assistent
// ─────────────────────────────────────────────

interface KiMessage { role: 'user' | 'assistant'; text: string; }

function FdvuKiPanel({ propertyId }: { propertyId: string }) {
    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState<KiMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, open]);

    const send = async () => {
        const q = input.trim();
        if (!q || loading) return;
        setInput('');
        setMessages(m => [...m, { role: 'user', text: q }]);
        setLoading(true);
        try {
            const res = await fetchAPI('/ki-kollega/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: q,
                    context: `Eiendom ID: ${propertyId}. Brukeren ser på FDVU compliance-siden for denne eiendommen.`,
                }),
            }) as { response?: string; message?: string };
            setMessages(m => [...m, { role: 'assistant', text: res.response ?? res.message ?? '(ingen svar)' }]);
        } catch {
            setMessages(m => [...m, { role: 'assistant', text: '⚠ KI-Kollega er ikke tilgjengelig akkurat nå.' }]);
        } finally { setLoading(false); }
    };

    const STARTER_QUESTIONS = [
        'Hva er status på compliance for denne eiendommen?',
        'Hvilke krav har avvik?',
        'Hva bør prioriteres nå?',
    ];

    return (
        <>
            {/* Flytende knapp */}
            <button
                onClick={() => setOpen(o => !o)}
                className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-2xl shadow-2xl shadow-primary/30 hover:bg-primary/90 transition-all text-sm font-medium"
                title="Spør KI-Kollega om denne eiendommen"
            >
                <Sparkles size={16} />
                {open ? 'Lukk KI' : 'Spør KI'}
            </button>

            {/* Chat-panel */}
            {open && (
                <div className="fixed bottom-20 right-6 z-40 w-80 sm:w-96 bg-card border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                    style={{ maxHeight: '60vh' }}>
                    {/* Panel-header */}
                    <div className="flex items-center gap-2 px-4 py-3 bg-primary/5 border-b border-border">
                        <Sparkles size={14} className="text-primary" />
                        <span className="text-sm font-semibold text-foreground">KI-Kollega · FDVU</span>
                        <span className="ml-auto text-xs text-muted">Eiendom {propertyId.slice(0, 8)}…</span>
                    </div>

                    {/* Meldinger */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm">
                        {messages.length === 0 && (
                            <div className="space-y-2">
                                <p className="text-xs text-muted text-center pt-2">Spør om compliance, tilstandsgrad, krav eller tiltak for denne eiendommen.</p>
                                <div className="flex flex-col gap-1.5 pt-1">
                                    {STARTER_QUESTIONS.map((q) => (
                                        <button key={q}
                                            onClick={() => { setInput(q); }}
                                            className="text-left text-xs px-3 py-2 rounded-lg border border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 transition-colors">
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                        {messages.map((m, i) => (
                            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
                                    m.role === 'user'
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-surface border border-border text-foreground'
                                }`}>
                                    {m.text}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex justify-start">
                                <div className="bg-surface border border-border rounded-xl px-3 py-2 text-xs text-muted flex items-center gap-1.5">
                                    <Loader2 size={11} className="animate-spin" /> Tenker …
                                </div>
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    {/* Input */}
                    <div className="flex items-center gap-2 px-3 py-2 border-t border-border bg-background">
                        <input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                            placeholder="Spør om compliance …"
                            className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted outline-none"
                        />
                        <button onClick={send} disabled={loading || !input.trim()}
                            className="p-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40">
                            <Zap size={13} />
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}

// ─────────────────────────────────────────────
// TilstandModal
// ─────────────────────────────────────────────

function TilstandModal({ component, onClose, onSaved }: {
    component: ComponentTilstand; onClose: () => void; onSaved: () => void;
}) {
    const [tg, setTg] = useState(component.condition_grade ?? '');
    const [criticality, setCriticality] = useState(component.criticality_level ?? '');
    const [replYear, setReplYear] = useState(component.replacement_year?.toString() ?? '');
    const [barcode, setBarcode] = useState(component.barcode ?? '');
    const [serial, setSerial] = useState(component.serial_number ?? '');
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const save = async () => {
        setSaving(true); setError(null);
        try {
            await updateTilstand(component.component_id, {
                condition_grade: tg || null,
                criticality_level: criticality || null,
                replacement_year: replYear ? +replYear : null,
                barcode: barcode || null,
                serial_number: serial || null,
            });
            onSaved(); onClose();
        } catch (e) { setError(e instanceof Error ? e.message : 'Lagring feilet'); }
        finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
                <div>
                    <h2 className="font-semibold text-foreground">{component.name}</h2>
                    <p className="text-xs text-muted mt-0.5">{component.type}{component.ns3451_code ? ` · NS3451: ${component.ns3451_code}` : ''}</p>
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-muted font-medium">Tilstandsgrad (NS 3600)</label>
                    <div className="grid grid-cols-4 gap-2">
                        {Object.entries(TG_META).map(([key, meta]) => (
                            <button key={key} onClick={() => setTg(tg === key ? '' : key)}
                                className={`flex flex-col items-center py-2 px-1 rounded-lg border text-xs transition-colors ${tg === key ? `${meta.bg} ${meta.color} border-current` : 'border-border text-muted hover:border-primary/50'}`}>
                                <span className="font-bold text-base">{meta.label}</span>
                                <span className="text-[10px] leading-tight text-center">{meta.desc}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-muted font-medium">Kritikalitet</label>
                    <div className="grid grid-cols-3 gap-2">
                        {['critical', 'important', 'standard'].map(c => (
                            <button key={c} onClick={() => setCriticality(criticality === c ? '' : c)}
                                className={`py-2 rounded-lg border text-xs transition-colors capitalize ${criticality === c ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                {c === 'critical' ? 'Kritisk' : c === 'important' ? 'Viktig' : 'Standard'}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="text-xs text-muted">Utskiftningsår</label>
                        <input type="number" placeholder="2032" value={replYear} onChange={e => setReplYear(e.target.value)}
                            className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary" />
                    </div>
                    <div>
                        <label className="text-xs text-muted">Strekkode / QR</label>
                        <input value={barcode} onChange={e => setBarcode(e.target.value)}
                            className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary" />
                    </div>
                </div>
                <div>
                    <label className="text-xs text-muted">Serienummer</label>
                    <input value={serial} onChange={e => setSerial(e.target.value)}
                        className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary" />
                </div>

                {error && <p className="text-destructive text-xs">{error}</p>}
                <div className="flex gap-2 justify-end">
                    <button onClick={onClose} className="px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors">Avbryt</button>
                    <button onClick={save} disabled={saving} className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                        {saving ? 'Lagrer …' : 'Lagre tilstand'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────

type Tab = 'krav' | 'komponenter' | 'dokumenter';

export default function PropertyCompliancePage({ params }: { params: Promise<{ propertyId: string }> }) {
    const { propertyId } = React.use(params);

    const [summary, setSummary] = useState<ComplianceSummary | null>(null);
    const [assignments, setAssignments] = useState<AssignmentWithAssessment[]>([]);
    const [documents, setDocuments] = useState<FdvDocument[]>([]);
    const [sections, setSections] = useState<FdvuSection[]>([]);
    const [components, setComponents] = useState<ComponentTilstand[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>('krav');
    const [filterReg, setFilterReg] = useState('');
    const [editingAssignment, setEditingAssignment] = useState<AssignmentWithAssessment | null>(null);
    const [editingComponent, setEditingComponent] = useState<ComponentTilstand | null>(null);
    const [showNewSection, setShowNewSection] = useState(false);

    const reload = useCallback(async () => {
        setLoading(true);
        const [s, a, d, sec, comp] = await Promise.all([
            getComplianceSummary(propertyId),
            getAssignments(propertyId),
            getFdvDocuments(propertyId),
            getFdvuSections(propertyId),
            getPropertyComponents(propertyId),
        ]);
        setSummary(s); setAssignments(a); setDocuments(d); setSections(sec); setComponents(comp);
        setLoading(false);
    }, [propertyId]);

    useEffect(() => { reload(); }, [reload]);

    const handleAutoGenerate = async () => {
        setGenerating(true);
        try {
            const res = await autoGenerateAssignments(propertyId);
            if (res.created > 0) await reload();
            else alert(`Ingen nye krav (${res.skipped_already_assigned} allerede tildelt, ${res.skipped_not_applicable} ikke aktuelt).`);
        } catch (e) { alert(e instanceof Error ? e.message : 'Feil'); }
        finally { setGenerating(false); }
    };

    // ── Batch-vurdering state ────────────────────────────────────────────────
    const [selected, setSelected] = useState<Set<string>>(new Set());
    const [bulkSaving, setBulkSaving] = useState(false);

    const toggleSelect = (id: string) =>
        setSelected(prev => { const s = new Set(prev); s.has(id) ? s.delete(id) : s.add(id); return s; });

    const toggleSelectAll = (ids: string[]) =>
        setSelected(prev => ids.every(id => prev.has(id)) ? new Set() : new Set(ids));

    const handleBulkAssess = async (status: string) => {
        if (selected.size === 0) return;
        setBulkSaving(true);
        try {
            const res = await bulkAssess({ assignment_ids: [...selected], status });
            setSelected(new Set());
            await reload();
            // kort tilbakemelding
            const msg = `✓ ${res.total} vurderinger lagret`;
            if (status === 'non_compliant' && res.created > 0) alert(`${msg}\n⚠ ${res.created} avvikssak(er) opprettet.`);
        } catch (e) { alert(e instanceof Error ? e.message : 'Feil'); }
        finally { setBulkSaving(false); }
    };

    const handleDownloadRapport = () => {
        window.open(`/fdvu/${propertyId}/rapport`, '_blank');
    };

    const regulationSets = [...new Set(assignments.map(a => a.requirement?.regulation_set ?? ''))].filter(Boolean);
    const filtered = filterReg ? assignments.filter(a => a.requirement?.regulation_set === filterReg) : assignments;

    // TG summary
    const tgCounts = components.reduce<Record<string, number>>((acc, c) => {
        if (c.condition_grade) acc[c.condition_grade] = (acc[c.condition_grade] ?? 0) + 1;
        return acc;
    }, {});
    const tg2plus = (tgCounts['TG2'] ?? 0) + (tgCounts['TG3'] ?? 0);

    const TABS: { key: Tab; label: string; count: number }[] = [
        { key: 'krav',       label: 'Krav & vurderinger', count: assignments.length },
        { key: 'komponenter',label: 'Komponenter',         count: components.length },
        { key: 'dokumenter', label: 'FDV-dokumenter',      count: documents.length },
    ];

    return (
        <div className="p-6 space-y-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Link href="/fdvu" className="text-muted hover:text-foreground transition-colors">
                    <ChevronLeft size={20} />
                </Link>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <ShieldCheck className="text-primary" size={22} /> FDVU Compliance
                    </h1>
                    <p className="text-muted text-xs mt-0.5 font-mono">{propertyId}</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={reload} disabled={loading}
                        className="p-2 rounded-lg border border-border text-muted hover:text-foreground transition-colors" title="Oppdater">
                        <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
                    </button>
                    <button onClick={handleDownloadRapport}
                        className="p-2 rounded-lg border border-border text-muted hover:text-foreground transition-colors" title="Åpne FDVU-rapport (PDF-utskrift)">
                        <Download size={15} />
                    </button>
                    <Link href={`/fdvu/${propertyId}/vedlikehold`}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border text-muted hover:text-foreground text-xs font-medium transition-colors"
                        title="Vedlikeholdsplan">
                        <Wrench size={14} /> Vedlikehold
                    </Link>
                    <Link href={`/fdvu/${propertyId}/miljo`}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border text-muted hover:text-foreground text-xs font-medium transition-colors"
                        title="Miljø, EOS og BREEAM">
                        <Leaf size={14} /> Miljø
                    </Link>
                    <Link href={`/fdvu/${propertyId}/arbeidsordre`}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border text-muted hover:text-foreground text-xs font-medium transition-colors"
                        title="Arbeidsordrer">
                        <ClipboardList size={14} /> Arbeidsordre
                    </Link>
                    <Link href={`/fdvu/${propertyId}/dokumenter`}
                        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg text-sm text-foreground hover:bg-primary/10 transition-colors"
                        title="Dokumentsøk">
                        <FileSearch size={15} />
                        Dokumentsøk
                    </Link>
                    {assignments.length === 0 && (
                        <button onClick={handleAutoGenerate} disabled={generating}
                            className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
                            <Zap size={14} />{generating ? 'Genererer …' : 'Auto-tildel krav'}
                        </button>
                    )}
                </div>
            </div>

            {/* Summary + seksjoner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="bg-card border-border md:col-span-2">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold text-muted">Compliance-oversikt</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="h-20 flex items-center justify-center text-muted text-sm">Laster …</div>
                        ) : summary ? (
                            <>
                                <SummaryBar summary={summary} />
                                {tg2plus > 0 && (
                                    <div className="mt-3 flex items-center gap-2 text-xs text-orange-400 bg-orange-500/10 rounded-lg px-3 py-2">
                                        <Wrench size={12} />
                                        {tg2plus} komponent{tg2plus > 1 ? 'er' : ''} med TG2 eller TG3 — krever tiltak
                                    </div>
                                )}
                            </>
                        ) : assignments.length === 0 ? (
                            <div className="text-center py-6 space-y-3">
                                <p className="text-muted text-sm">Ingen krav tildelt ennå.</p>
                                <button onClick={handleAutoGenerate} disabled={generating}
                                    className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
                                    <Zap size={14} />{generating ? 'Genererer …' : 'Start med auto-tildeling'}
                                </button>
                            </div>
                        ) : (
                            <p className="text-muted text-sm">Ingen vurderinger ennå.</p>
                        )}
                    </CardContent>
                </Card>

                {/* Seksjoner */}
                <Card className="bg-card border-border">
                    <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-sm font-semibold text-muted">Seksjoner</CardTitle>
                            <button onClick={() => setShowNewSection(true)}
                                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors">
                                <Plus size={13} /> Ny
                            </button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {sections.length === 0 ? (
                            <div className="text-center py-3">
                                <p className="text-muted text-xs mb-2">Ingen seksjoner registrert.</p>
                                <button onClick={() => setShowNewSection(true)}
                                    className="text-xs text-primary underline underline-offset-2">
                                    Legg til seksjon
                                </button>
                            </div>
                        ) : (
                            <ul className="space-y-2">
                                {sections.map(sec => (
                                    <li key={sec.section_id} className="flex items-center justify-between gap-2 text-sm">
                                        <div className="min-w-0">
                                            <div className="text-foreground truncate">{sec.name}</div>
                                            {(sec.area_sqm || sec.capacity) && (
                                                <div className="text-xs text-muted">
                                                    {sec.area_sqm ? `${sec.area_sqm} m²` : ''}{sec.capacity ? ` · ${sec.capacity} pl.` : ''}
                                                </div>
                                            )}
                                        </div>
                                        <Badge variant="outline" className="text-xs shrink-0">{sec.section_type}</Badge>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border">
                {TABS.map(({ key, label, count }) => (
                    <button key={key} onClick={() => setActiveTab(key)}
                        className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${activeTab === key ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-foreground'}`}>
                        {label} <span className="ml-1 text-xs text-muted">({count})</span>
                    </button>
                ))}
            </div>

            {/* TAB: Krav */}
            {activeTab === 'krav' && (
                <div className="space-y-4">
                    {regulationSets.length > 1 && (
                        <div className="flex flex-wrap gap-2">
                            <button onClick={() => setFilterReg('')}
                                className={`px-3 py-1 rounded-full text-xs border transition-colors ${!filterReg ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                Alle
                            </button>
                            {regulationSets.map(reg => (
                                <button key={reg} onClick={() => setFilterReg(reg)}
                                    className={`px-3 py-1 rounded-full text-xs border transition-colors ${filterReg === reg ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                    {REGULATION_LABELS[reg] ?? reg}
                                </button>
                            ))}
                        </div>
                    )}
                    {/* Velg-alle rad */}
                    {!loading && filtered.length > 0 && (
                        <div className="flex items-center gap-3 px-2 py-1">
                            <button onClick={() => toggleSelectAll(filtered.map(a => a.assignment_id))}
                                className="flex items-center gap-2 text-xs text-muted hover:text-foreground transition-colors">
                                {filtered.every(a => selected.has(a.assignment_id))
                                    ? <CheckSquare size={14} className="text-primary" />
                                    : <Square size={14} />}
                                Velg alle ({filtered.length})
                            </button>
                            {selected.size > 0 && (
                                <span className="text-xs text-primary font-medium">{selected.size} valgt</span>
                            )}
                        </div>
                    )}
                    {loading ? (
                        <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-card border border-border rounded-lg animate-pulse" />)}</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12 text-muted text-sm">Ingen krav.</div>
                    ) : (
                        <div className="space-y-2">
                            {filtered.map(a => {
                                const req = a.requirement;
                                const ca = a.compliance_assessment;
                                const statusMeta = STATUS_META[ca?.status ?? 'not_assessed'] ?? STATUS_META.not_assessed;
                                const sevClass = SEV_META[req?.severity_if_breached ?? ''] ?? '';
                                const isOverdue = ca?.next_review_date && new Date(ca.next_review_date) < new Date() && ca.status !== 'not_applicable';
                                const isChecked = selected.has(a.assignment_id);
                                return (
                                    <div key={a.assignment_id}
                                        className={`bg-card border rounded-lg px-4 py-3 flex items-center gap-3 hover:border-primary/30 transition-colors group ${isChecked ? 'border-primary/50 bg-primary/5' : 'border-border'}`}>
                                        {/* Checkbox */}
                                        <button
                                            onClick={e => { e.stopPropagation(); toggleSelect(a.assignment_id); }}
                                            className="shrink-0 text-muted hover:text-primary transition-colors">
                                            {isChecked ? <CheckSquare size={16} className="text-primary" /> : <Square size={16} />}
                                        </button>
                                        {/* Status-ikon */}
                                        <div className="shrink-0">{statusMeta.icon}</div>
                                        {/* Innhold */}
                                        <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setEditingAssignment(a)}>
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-mono text-xs text-muted">{req?.code}</span>
                                                {req?.severity_if_breached && <Badge className={`text-xs px-1.5 py-0 ${sevClass}`}>{req.severity_if_breached}</Badge>}
                                                {isOverdue && <Badge className="text-xs px-1.5 py-0 bg-warning/15 text-warning border-warning/30"><Clock size={10} className="mr-1" />forfalt</Badge>}
                                                {ca?.status === 'non_compliant' && <Badge className="text-xs px-1.5 py-0 bg-destructive/15 text-destructive border-destructive/30"><AlertCircle size={10} className="mr-1" />avvik</Badge>}
                                            </div>
                                            <div className="text-sm text-foreground truncate">{req?.title}</div>
                                            {ca?.evidence_notes && <div className="text-xs text-muted truncate mt-0.5">{ca.evidence_notes}</div>}
                                        </div>
                                        <div className="shrink-0 text-right">
                                            <div className={`text-xs font-medium ${statusMeta.color}`}>{statusMeta.label}</div>
                                            <div className="text-xs text-muted">{REGULATION_LABELS[req?.regulation_set ?? ''] ?? req?.regulation_set}</div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* TAB: Komponenter */}
            {activeTab === 'komponenter' && (
                <div className="space-y-2">
                    {/* TG-legend */}
                    <div className="flex flex-wrap gap-2 pb-2">
                        {Object.entries(TG_META).map(([key, meta]) => (
                            <div key={key} className={`flex items-center gap-1.5 px-2 py-1 rounded-full border text-xs ${meta.bg} ${meta.color}`}>
                                <span className="font-bold">{meta.label}</span>
                                <span className="opacity-75">{meta.desc}</span>
                                {tgCounts[key] ? <span className="font-semibold ml-1">({tgCounts[key]})</span> : null}
                            </div>
                        ))}
                    </div>
                    {loading ? (
                        <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-14 bg-card border border-border rounded-lg animate-pulse" />)}</div>
                    ) : components.length === 0 ? (
                        <div className="text-center py-12 text-muted text-sm">
                            Ingen komponenter registrert for denne eiendommen.<br />
                            <span className="text-xs">Legg til via Anleggsregister.</span>
                        </div>
                    ) : (
                        components.map(comp => {
                            const tgMeta = TG_META[comp.condition_grade ?? ''];
                            return (
                                <div key={comp.component_id}
                                    className="bg-card border border-border rounded-lg px-4 py-3 flex items-center gap-4 hover:border-primary/30 transition-colors cursor-pointer"
                                    onClick={() => setEditingComponent(comp)}>
                                    <Wrench size={15} className={tgMeta?.color ?? 'text-muted'} />
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-foreground">{comp.name}</div>
                                        <div className="text-xs text-muted">
                                            {comp.type ?? 'Ukjent type'}
                                            {comp.ns3451_code ? ` · ${comp.ns3451_code}` : ''}
                                            {comp.replacement_year ? ` · Utskifting ${comp.replacement_year}` : ''}
                                        </div>
                                    </div>
                                    <div className="shrink-0 flex items-center gap-2">
                                        {comp.criticality_level && (
                                            <Badge variant="outline" className="text-xs">
                                                {comp.criticality_level === 'critical' ? 'Kritisk' : comp.criticality_level === 'important' ? 'Viktig' : 'Standard'}
                                            </Badge>
                                        )}
                                        {tgMeta ? (
                                            <Badge className={`text-xs ${tgMeta.bg} ${tgMeta.color} border-current`}>{tgMeta.label}</Badge>
                                        ) : (
                                            <Badge variant="outline" className="text-xs text-muted">Ikke vurdert</Badge>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}

            {/* TAB: Dokumenter */}
            {activeTab === 'dokumenter' && (
                <div className="space-y-2">
                    {loading ? (
                        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-14 bg-card border border-border rounded-lg animate-pulse" />)}</div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-12 text-muted text-sm">Ingen FDV-dokumenter registrert.</div>
                    ) : (
                        documents.map(doc => (
                            <div key={doc.document_id} className="bg-card border border-border rounded-lg px-4 py-3 flex items-center gap-4">
                                <FileText size={16} className="text-primary shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-foreground truncate">{doc.title}</div>
                                    <div className="text-xs text-muted">{doc.document_type}{doc.document_number ? ` · ${doc.document_number}` : ''}</div>
                                </div>
                                <div className="shrink-0 text-right">
                                    <Badge variant="outline" className={`text-xs ${doc.status === 'active' ? 'text-success border-success/30' : 'text-muted'}`}>{doc.status}</Badge>
                                    {doc.valid_until && (
                                        <div className={`text-xs mt-0.5 ${new Date(doc.valid_until) < new Date() ? 'text-destructive' : 'text-muted'}`}>
                                            Utløper {new Date(doc.valid_until).toLocaleDateString('no-NO')}
                                        </div>
                                    )}
                                </div>
                                {doc.external_url && (
                                    <a href={doc.external_url} target="_blank" rel="noopener noreferrer" className="text-muted hover:text-primary">
                                        <ExternalLink size={14} />
                                    </a>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Modaler */}
            {showNewSection && <NySeksjonModal propertyId={propertyId} onClose={() => setShowNewSection(false)} onSaved={reload} />}
            {editingAssignment && <AssessmentModal propertyId={propertyId} assignment={editingAssignment} onClose={() => setEditingAssignment(null)} onSaved={reload} />}
            {editingComponent && <TilstandModal component={editingComponent} onClose={() => setEditingComponent(null)} onSaved={reload} />}

            {/* Flytende KI-assistent */}
            <FdvuKiPanel propertyId={propertyId} />

            {/* Sticky batch-aksjonslinje */}
            {selected.size > 0 && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-card border border-primary/40 rounded-2xl shadow-2xl px-4 py-3 animate-in slide-in-from-bottom-4">
                    <span className="text-sm font-semibold text-foreground mr-2">{selected.size} krav valgt</span>
                    {[
                        { status: 'compliant',      label: 'Oppfylt',     cls: 'bg-success/15 text-success border-success/30 hover:bg-success/25' },
                        { status: 'partial',        label: 'Delvis',      cls: 'bg-warning/15 text-warning border-warning/30 hover:bg-warning/25' },
                        { status: 'non_compliant',  label: 'Avvik',       cls: 'bg-destructive/15 text-destructive border-destructive/30 hover:bg-destructive/25' },
                        { status: 'not_applicable', label: 'Ikke aktuelt',cls: 'bg-muted/30 text-muted border-border hover:bg-muted/50' },
                    ].map(({ status, label, cls }) => (
                        <button key={status}
                            onClick={() => handleBulkAssess(status)}
                            disabled={bulkSaving}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors disabled:opacity-50 ${cls}`}>
                            {bulkSaving ? '…' : label}
                        </button>
                    ))}
                    <button onClick={() => setSelected(new Set())}
                        className="ml-2 text-xs text-muted hover:text-foreground transition-colors px-2 py-1 rounded-lg hover:bg-surface/50">
                        Avbryt
                    </button>
                </div>
            )}
        </div>
    );
}
