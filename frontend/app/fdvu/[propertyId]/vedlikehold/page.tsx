"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
    getMaintenancePlans, createMaintenancePlan, updateMaintenancePlan,
    deleteMaintenancePlan, generateTasks, getMaintenanceTasks,
    updateMaintenanceTask, getMaintenanceSummary,
    type MaintenancePlan, type MaintenanceTask, type MaintenanceSummary, type PlanCreate,
} from '@/lib/api/maintenanceApi';
import {
    ChevronLeft, Plus, Wrench, CheckCircle2, Clock, AlertTriangle,
    RefreshCw, ChevronRight, Trash2, Zap, CalendarCheck,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// ─────────────────────────────────────────────
// Konstanter
// ─────────────────────────────────────────────

const CATEGORY_META: Record<string, { label: string; color: string }> = {
    preventive:  { label: 'Forebyggende', color: 'text-primary bg-primary/10 border-primary/20' },
    inspection:  { label: 'Inspeksjon',   color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
    cleaning:    { label: 'Renhold',      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
    corrective:  { label: 'Korrigerende', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
    legal:       { label: 'Lovpålagt',    color: 'text-destructive bg-destructive/10 border-destructive/20' },
};

const STATUS_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    pending:    { label: 'Venter',     icon: <Clock size={13} />,         color: 'text-muted' },
    in_progress:{ label: 'Pågår',      icon: <Wrench size={13} />,        color: 'text-primary' },
    completed:  { label: 'Fullført',   icon: <CheckCircle2 size={13} />,  color: 'text-success' },
    overdue:    { label: 'Forfalt',    icon: <AlertTriangle size={13} />, color: 'text-destructive' },
    cancelled:  { label: 'Avlyst',     icon: <Clock size={13} />,         color: 'text-muted' },
    skipped:    { label: 'Hoppet',     icon: <Clock size={13} />,         color: 'text-muted' },
};

const FREQ_OPTIONS = [
    { months: 1,  label: 'Månedlig' },
    { months: 3,  label: 'Kvartalsvis' },
    { months: 6,  label: 'Halvårlig' },
    { months: 12, label: 'Årlig' },
    { months: 24, label: 'Hvert 2. år' },
];

const ROLE_LABELS: Record<string, string> = {
    janitor:          'Vaktmester',
    contractor:       'Leverandør',
    property_manager: 'Forvalter',
};

// ─────────────────────────────────────────────
// NyPlanModal
// ─────────────────────────────────────────────

function NyPlanModal({ propertyId, onClose, onSaved }: {
    propertyId: string; onClose: () => void; onSaved: () => void;
}) {
    const [form, setForm] = useState<PlanCreate>({
        property_id: propertyId,
        title: '',
        category: 'preventive',
        frequency_months: 12,
        responsible_role: 'janitor',
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const save = async () => {
        if (!form.title.trim()) { setError('Tittel er påkrevd'); return; }
        setSaving(true); setError(null);
        try {
            const plan = await createMaintenancePlan(form);
            await generateTasks(plan.plan_id, 12);
            onSaved(); onClose();
        } catch (e) { setError(e instanceof Error ? e.message : 'Feil ved lagring'); }
        finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-lg p-6 space-y-4" onClick={e => e.stopPropagation()}>
                <h2 className="font-semibold text-foreground flex items-center gap-2">
                    <Wrench size={16} className="text-primary" /> Ny vedlikeholdsplan
                </h2>

                <div className="space-y-3">
                    <div>
                        <label className="text-xs text-muted">Tittel *</label>
                        <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                            value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                            placeholder="f.eks. Sjekk brannslukker" />
                    </div>

                    <div>
                        <label className="text-xs text-muted">Kategori</label>
                        <div className="mt-1 grid grid-cols-3 gap-2">
                            {Object.entries(CATEGORY_META).map(([key, meta]) => (
                                <button key={key}
                                    onClick={() => setForm(f => ({ ...f, category: key }))}
                                    className={`px-2 py-1.5 rounded-lg border text-xs transition-colors ${form.category === key ? `${meta.color} border-current` : 'border-border text-muted hover:border-primary/40'}`}>
                                    {meta.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="text-xs text-muted">Frekvens</label>
                        <div className="mt-1 grid grid-cols-3 gap-2">
                            {FREQ_OPTIONS.map(opt => (
                                <button key={opt.months}
                                    onClick={() => setForm(f => ({ ...f, frequency_months: opt.months }))}
                                    className={`px-2 py-1.5 rounded-lg border text-xs transition-colors ${form.frequency_months === opt.months ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/40'}`}>
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="text-xs text-muted">Ansvarlig</label>
                        <div className="mt-1 grid grid-cols-3 gap-2">
                            {Object.entries(ROLE_LABELS).map(([key, label]) => (
                                <button key={key}
                                    onClick={() => setForm(f => ({ ...f, responsible_role: key }))}
                                    className={`px-2 py-1.5 rounded-lg border text-xs transition-colors ${form.responsible_role === key ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/40'}`}>
                                    {label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs text-muted">Sist utført</label>
                            <input type="date" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                                value={form.last_performed_date ?? ''}
                                onChange={e => setForm(f => ({ ...f, last_performed_date: e.target.value || null }))} />
                        </div>
                        <div>
                            <label className="text-xs text-muted">Estimert kostnad (NOK)</label>
                            <input type="number" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                                value={form.estimated_cost_nok ?? ''}
                                onChange={e => setForm(f => ({ ...f, estimated_cost_nok: e.target.value ? +e.target.value : null }))} />
                        </div>
                    </div>
                </div>

                {error && <p className="text-destructive text-xs">{error}</p>}
                <div className="flex gap-2 justify-end pt-1">
                    <button onClick={onClose} className="px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors">Avbryt</button>
                    <button onClick={save} disabled={saving}
                        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                        {saving ? 'Oppretter …' : 'Opprett + generer oppgaver'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// KomplettModal – merk oppgave som fullført
// ─────────────────────────────────────────────

function KomplettModal({ task, onClose, onSaved }: {
    task: MaintenanceTask; onClose: () => void; onSaved: () => void;
}) {
    const [notes, setNotes] = useState('');
    const [cost, setCost] = useState('');
    const [saving, setSaving] = useState(false);

    const save = async () => {
        setSaving(true);
        try {
            await updateMaintenanceTask(task.task_id, {
                status: 'completed',
                completion_notes: notes || undefined,
                actual_cost_nok: cost ? +cost : undefined,
            });
            onSaved(); onClose();
        } catch { /* silent */ }
        finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
            <div className="bg-card border border-border rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
                <h2 className="font-semibold text-foreground flex items-center gap-2">
                    <CalendarCheck size={16} className="text-success" /> Merk som fullført
                </h2>
                <p className="text-sm text-foreground">{task.title}</p>
                <p className="text-xs text-muted">Forfallsdato: {new Date(task.due_date).toLocaleDateString('no-NO')}</p>
                <div>
                    <label className="text-xs text-muted">Notat / utført av</label>
                    <textarea rows={3} value={notes} onChange={e => setNotes(e.target.value)}
                        placeholder="Beskriv hva som ble gjort …"
                        className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground resize-none focus:outline-none focus:border-primary" />
                </div>
                <div>
                    <label className="text-xs text-muted">Faktisk kostnad (NOK)</label>
                    <input type="number" value={cost} onChange={e => setCost(e.target.value)}
                        className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary" />
                </div>
                <div className="flex gap-2 justify-end">
                    <button onClick={onClose} className="px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors">Avbryt</button>
                    <button onClick={save} disabled={saving}
                        className="px-4 py-2 rounded-lg bg-success text-white text-sm font-medium hover:bg-success/90 transition-colors disabled:opacity-50">
                        {saving ? 'Lagrer …' : 'Bekreft fullføring'}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// Hovedside
// ─────────────────────────────────────────────

type Tab = 'planer' | 'oppgaver';

export default function VedlikeholdPage({ params }: { params: Promise<{ propertyId: string }> }) {
    const { propertyId } = React.use(params);
    const [plans, setPlans] = useState<MaintenancePlan[]>([]);
    const [tasks, setTasks] = useState<MaintenanceTask[]>([]);
    const [summary, setSummary] = useState<MaintenanceSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<Tab>('oppgaver');
    const [showNewPlan, setShowNewPlan] = useState(false);
    const [completingTask, setCompletingTask] = useState<MaintenanceTask | null>(null);
    const [taskFilter, setTaskFilter] = useState<string>('');

    const reload = useCallback(async () => {
        setLoading(true);
        const [p, t, s] = await Promise.all([
            getMaintenancePlans(propertyId),
            getMaintenanceTasks(propertyId),
            getMaintenanceSummary(propertyId),
        ]);
        setPlans(p); setTasks(t); setSummary(s);
        setLoading(false);
    }, [propertyId]);

    useEffect(() => { reload(); }, [reload]);

    const filteredTasks = taskFilter ? tasks.filter(t => t.status === taskFilter) : tasks;

    const isOverdue = (t: MaintenanceTask) =>
        (t.status === 'pending' || t.status === 'overdue') && new Date(t.due_date) < new Date();

    const handleDeletePlan = async (planId: string) => {
        if (!confirm('Slett planen og alle tilhørende oppgaver?')) return;
        await deleteMaintenancePlan(planId);
        await reload();
    };

    const handleGenerate = async (planId: string) => {
        await generateTasks(planId, 12);
        await reload();
    };

    return (
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Link href={`/fdvu/${propertyId}`} className="text-muted hover:text-foreground transition-colors">
                    <ChevronLeft size={20} />
                </Link>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <Wrench className="text-primary" size={22} /> Vedlikeholdsplan
                    </h1>
                    <p className="text-muted text-xs mt-0.5 font-mono">{propertyId}</p>
                </div>
                <button onClick={reload} disabled={loading}
                    className="p-2 rounded-lg border border-border text-muted hover:text-foreground transition-colors" title="Oppdater">
                    <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
                </button>
                <button onClick={() => setShowNewPlan(true)}
                    className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors">
                    <Plus size={14} /> Ny plan
                </button>
            </div>

            {/* KPI-kort */}
            {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                        { label: 'Aktive planer',   value: summary.plans_active,    color: 'text-primary' },
                        { label: 'Ventende',         value: summary.tasks_pending,   color: 'text-muted' },
                        { label: 'Forfalt',          value: summary.tasks_overdue,   color: summary.tasks_overdue > 0 ? 'text-destructive' : 'text-muted' },
                        { label: 'Fullført totalt',  value: summary.tasks_completed, color: 'text-success' },
                    ].map(({ label, value, color }) => (
                        <Card key={label} className="bg-card border-border">
                            <CardContent className="p-4 text-center">
                                <div className={`text-2xl font-bold ${color}`}>{value}</div>
                                <div className="text-xs text-muted mt-1">{label}</div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
            {summary?.next_due_date && (
                <div className="flex items-center gap-2 text-sm bg-primary/5 border border-primary/20 rounded-lg px-4 py-2.5">
                    <CalendarCheck size={15} className="text-primary shrink-0" />
                    <span className="text-muted">Neste forfallsdato:</span>
                    <span className="font-medium text-foreground">{summary.next_due_title}</span>
                    <span className="text-muted">·</span>
                    <span className="text-primary">{new Date(summary.next_due_date).toLocaleDateString('no-NO')}</span>
                </div>
            )}

            {/* Tabs */}
            <div className="flex gap-1 border-b border-border">
                {[
                    { key: 'oppgaver' as Tab, label: 'Oppgaver',   count: tasks.length },
                    { key: 'planer'   as Tab, label: 'Planer',     count: plans.length },
                ].map(({ key, label, count }) => (
                    <button key={key} onClick={() => setTab(key)}
                        className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${tab === key ? 'border-primary text-primary' : 'border-transparent text-muted hover:text-foreground'}`}>
                        {label} <span className="ml-1 text-xs text-muted">({count})</span>
                    </button>
                ))}
            </div>

            {/* TAB: Oppgaver */}
            {tab === 'oppgaver' && (
                <div className="space-y-3">
                    {/* Statusfilter */}
                    <div className="flex flex-wrap gap-2">
                        {['', 'overdue', 'pending', 'in_progress', 'completed'].map(s => (
                            <button key={s}
                                onClick={() => setTaskFilter(s)}
                                className={`px-3 py-1 rounded-full text-xs border transition-colors ${taskFilter === s ? 'bg-primary text-primary-foreground border-primary' : 'border-border text-muted hover:border-primary/50'}`}>
                                {s === '' ? 'Alle' : STATUS_META[s]?.label ?? s}
                                {s === 'overdue' && summary?.tasks_overdue ? (
                                    <span className="ml-1.5 bg-destructive text-destructive-foreground rounded-full px-1 text-[10px]">{summary.tasks_overdue}</span>
                                ) : null}
                            </button>
                        ))}
                    </div>

                    {loading ? (
                        <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-card border border-border rounded-lg animate-pulse" />)}</div>
                    ) : filteredTasks.length === 0 ? (
                        <div className="text-center py-12 space-y-3">
                            <p className="text-muted text-sm">Ingen oppgaver ennå.</p>
                            {plans.length > 0 && (
                                <p className="text-xs text-muted">Klikk <Zap size={10} className="inline" /> på en plan for å generere oppgaver.</p>
                            )}
                        </div>
                    ) : (
                        filteredTasks.map(task => {
                            const sm = STATUS_META[task.status] ?? STATUS_META.pending;
                            const overdue = isOverdue(task);
                            return (
                                <div key={task.task_id}
                                    className={`bg-card border rounded-lg px-4 py-3 flex items-center gap-4 transition-colors ${overdue ? 'border-destructive/40 bg-destructive/5' : 'border-border hover:border-primary/30'}`}>
                                    <div className={`shrink-0 ${sm.color}`}>{sm.icon}</div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-medium text-foreground">{task.title}</div>
                                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                            <span className={`text-xs ${overdue ? 'text-destructive font-semibold' : 'text-muted'}`}>
                                                {overdue ? '⚠ Forfalt ' : ''}{new Date(task.due_date).toLocaleDateString('no-NO')}
                                            </span>
                                            {task.completion_notes && (
                                                <span className="text-xs text-muted truncate max-w-xs">{task.completion_notes}</span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="shrink-0 flex items-center gap-2">
                                        <Badge className={`text-xs ${sm.color} bg-transparent border-current`}>{sm.label}</Badge>
                                        {task.status !== 'completed' && task.status !== 'cancelled' && (
                                            <button
                                                onClick={() => setCompletingTask(task)}
                                                className="text-xs px-2 py-1 rounded-lg bg-success/10 text-success border border-success/20 hover:bg-success/20 transition-colors">
                                                Fullfør
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}

            {/* TAB: Planer */}
            {tab === 'planer' && (
                <div className="space-y-3">
                    {loading ? (
                        <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-card border border-border rounded-lg animate-pulse" />)}</div>
                    ) : plans.length === 0 ? (
                        <div className="text-center py-12 space-y-3">
                            <p className="text-muted text-sm">Ingen vedlikeholdsplaner ennå.</p>
                            <button onClick={() => setShowNewPlan(true)}
                                className="flex items-center gap-2 mx-auto px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors">
                                <Plus size={14} /> Opprett første plan
                            </button>
                        </div>
                    ) : (
                        plans.map(plan => {
                            const catMeta = CATEGORY_META[plan.category] ?? CATEGORY_META.preventive;
                            const dueDate = plan.next_due_date ? new Date(plan.next_due_date) : null;
                            const isOverduePlan = dueDate && dueDate < new Date();
                            const freqLabel = FREQ_OPTIONS.find(f => f.months === plan.frequency_months)?.label ?? `${plan.frequency_months} mnd`;
                            return (
                                <div key={plan.plan_id} className="bg-card border border-border rounded-lg px-4 py-4 space-y-2 hover:border-primary/30 transition-colors">
                                    <div className="flex items-start gap-3">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-medium text-sm text-foreground">{plan.title}</span>
                                                <Badge className={`text-xs px-1.5 py-0 border ${catMeta.color}`}>{catMeta.label}</Badge>
                                                <Badge variant="outline" className="text-xs px-1.5 py-0">{freqLabel}</Badge>
                                                <Badge variant="outline" className="text-xs px-1.5 py-0">{ROLE_LABELS[plan.responsible_role] ?? plan.responsible_role}</Badge>
                                            </div>
                                            <div className="flex items-center gap-3 mt-1.5 text-xs text-muted flex-wrap">
                                                {plan.last_performed_date && (
                                                    <span>Sist: {new Date(plan.last_performed_date).toLocaleDateString('no-NO')}</span>
                                                )}
                                                {dueDate && (
                                                    <span className={isOverduePlan ? 'text-destructive font-semibold' : ''}>
                                                        {isOverduePlan ? '⚠ Forfalt ' : 'Neste: '}
                                                        {dueDate.toLocaleDateString('no-NO')}
                                                    </span>
                                                )}
                                                {plan.estimated_cost_nok && (
                                                    <span>~{plan.estimated_cost_nok.toLocaleString('no-NO')} kr</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0">
                                            <button
                                                onClick={() => handleGenerate(plan.plan_id)}
                                                title="Generer kommende oppgaver (12 mnd)"
                                                className="p-1.5 rounded-lg text-muted hover:text-primary hover:bg-primary/10 transition-colors">
                                                <Zap size={14} />
                                            </button>
                                            <Link href={`/fdvu/${propertyId}/vedlikehold`}
                                                className="p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-surface/50 transition-colors">
                                                <ChevronRight size={14} />
                                            </Link>
                                            <button
                                                onClick={() => handleDeletePlan(plan.plan_id)}
                                                className="p-1.5 rounded-lg text-muted hover:text-destructive hover:bg-destructive/10 transition-colors">
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}

            {/* Modaler */}
            {showNewPlan && (
                <NyPlanModal propertyId={propertyId} onClose={() => setShowNewPlan(false)} onSaved={reload} />
            )}
            {completingTask && (
                <KomplettModal task={completingTask} onClose={() => setCompletingTask(null)} onSaved={reload} />
            )}
        </div>
    );
}
