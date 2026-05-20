"use client";

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
    ChevronLeft, ClipboardList, RefreshCw, ChevronDown, ChevronUp,
    CheckCircle2, Clock, Wrench, AlertTriangle, CalendarClock,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { fetchAPI } from '@/lib/api/client';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

interface MaintenanceTask {
    task_id: string;
    title: string;
    description?: string | null;
    due_date: string;
    status: string; // 'pending' | 'in_progress' | 'completed' | 'overdue' | 'cancelled'
    responsible?: string | null;
    responsible_role?: string | null;
    building_component_name?: string | null;
    completion_notes?: string | null;
    actual_cost_nok?: number | null;
}

type StatusFilter = 'pending' | 'in_progress' | 'completed' | 'overdue';

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────

const STATUS_META: Record<string, { label: string; icon: React.ReactNode; badgeColor: string; cardBorder: string }> = {
    pending:     { label: 'Venter',      icon: <Clock size={16} />,         badgeColor: 'text-muted border-border',               cardBorder: 'border-border' },
    in_progress: { label: 'Pågår',       icon: <Wrench size={16} />,        badgeColor: 'text-primary border-primary/40',          cardBorder: 'border-primary/30 bg-primary/5' },
    completed:   { label: 'Fullført',    icon: <CheckCircle2 size={16} />,  badgeColor: 'text-success border-success/40',          cardBorder: 'border-success/30 bg-success/5' },
    overdue:     { label: 'Forfalt',     icon: <AlertTriangle size={16} />, badgeColor: 'text-destructive border-destructive/40',  cardBorder: 'border-destructive/40 bg-destructive/5' },
    cancelled:   { label: 'Avlyst',      icon: <Clock size={16} />,         badgeColor: 'text-muted border-border',               cardBorder: 'border-border opacity-60' },
};

const FILTER_LABELS: { key: StatusFilter; label: string }[] = [
    { key: 'pending',     label: 'Ventende' },
    { key: 'in_progress', label: 'Pågår' },
    { key: 'overdue',     label: 'Forfalt' },
    { key: 'completed',   label: 'Fullført' },
];

const ROLE_LABELS: Record<string, string> = {
    janitor:          'Vaktmester',
    contractor:       'Leverandør',
    property_manager: 'Forvalter',
};

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('no-NO', { day: '2-digit', month: 'short', year: 'numeric' });
}

function isOverdue(task: MaintenanceTask): boolean {
    return (task.status === 'pending' || task.status === 'in_progress') &&
        new Date(task.due_date) < new Date();
}

function sortByDueDate(a: MaintenanceTask, b: MaintenanceTask): number {
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
}

// ─────────────────────────────────────────────
// TaskCard – expandable mobile-friendly card
// ─────────────────────────────────────────────

function TaskCard({ task, onCompleted }: { task: MaintenanceTask; onCompleted: () => void }) {
    const [expanded, setExpanded] = useState(false);
    const [completing, setCompleting] = useState(false);
    const [notes, setNotes] = useState('');
    const [error, setError] = useState<string | null>(null);

    const overdue = isOverdue(task);
    const statusKey = overdue && task.status !== 'completed' ? 'overdue' : task.status;
    const meta = STATUS_META[statusKey] ?? STATUS_META.pending;

    const handleComplete = async () => {
        setCompleting(true);
        setError(null);
        try {
            await fetchAPI(`/fdvu/maintenance/tasks/${task.task_id}`, {
                method: 'PATCH',
                body: JSON.stringify({
                    status: 'completed',
                    completion_notes: notes || undefined,
                }),
            });
            onCompleted();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Feil ved oppdatering');
        } finally {
            setCompleting(false);
        }
    };

    return (
        <div className={`bg-card border rounded-2xl overflow-hidden transition-colors ${meta.cardBorder}`}>
            {/* Main tap area */}
            <button
                className="w-full text-left px-5 py-4 flex items-start gap-4"
                onClick={() => setExpanded(prev => !prev)}
                aria-expanded={expanded}
            >
                {/* Status icon */}
                <span className={`shrink-0 mt-0.5 ${meta.badgeColor.split(' ')[0]}`}>
                    {meta.icon}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-base font-semibold text-foreground leading-snug">{task.title}</p>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
                        {/* Due date */}
                        <span className={`flex items-center gap-1 text-sm ${overdue ? 'text-destructive font-semibold' : 'text-muted'}`}>
                            <CalendarClock size={13} className="shrink-0" />
                            {overdue ? '⚠ ' : ''}{formatDate(task.due_date)}
                        </span>

                        {/* Component */}
                        {task.building_component_name && (
                            <span className="text-xs text-muted truncate max-w-[160px]">
                                {task.building_component_name}
                            </span>
                        )}

                        {/* Responsible */}
                        {(task.responsible || task.responsible_role) && (
                            <span className="text-xs text-muted">
                                {task.responsible ?? ROLE_LABELS[task.responsible_role ?? ''] ?? task.responsible_role}
                            </span>
                        )}
                    </div>
                </div>

                {/* Status badge + chevron */}
                <div className="shrink-0 flex items-center gap-2 mt-0.5">
                    <Badge className={`text-xs border ${meta.badgeColor} hidden sm:flex`}>
                        {meta.label}
                    </Badge>
                    {expanded
                        ? <ChevronUp size={18} className="text-muted" />
                        : <ChevronDown size={18} className="text-muted" />}
                </div>
            </button>

            {/* Expanded detail panel */}
            {expanded && (
                <div className="px-5 pb-5 pt-0 space-y-4 border-t border-border">
                    {/* Description */}
                    {task.description && (
                        <p className="text-sm text-muted leading-relaxed pt-3">{task.description}</p>
                    )}

                    {/* Completion notes (if already done) */}
                    {task.completion_notes && (
                        <div className="bg-success/5 border border-success/20 rounded-xl px-4 py-3">
                            <p className="text-xs font-medium text-success mb-1">Notat ved fullføring</p>
                            <p className="text-sm text-foreground">{task.completion_notes}</p>
                        </div>
                    )}

                    {/* Mark as done – only for non-completed tasks */}
                    {task.status !== 'completed' && task.status !== 'cancelled' && (
                        <div className="space-y-3 pt-1">
                            <div>
                                <label className="text-xs text-muted block mb-1">Notat (valgfritt)</label>
                                <textarea
                                    rows={2}
                                    value={notes}
                                    onChange={e => setNotes(e.target.value)}
                                    placeholder="Beskriv hva som ble utført …"
                                    className="w-full bg-background border border-border rounded-xl px-4 py-2.5 text-sm text-foreground resize-none focus:outline-none focus:border-primary"
                                />
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 text-destructive text-xs bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                                    <AlertTriangle size={13} className="shrink-0" />
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleComplete}
                                disabled={completing}
                                className="w-full py-3 rounded-xl bg-success text-white text-sm font-semibold hover:bg-success/90 active:scale-[0.98] transition-all disabled:opacity-50"
                            >
                                {completing ? 'Lagrer …' : '✓ Merk som fullført'}
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────
// Hovedside
// ─────────────────────────────────────────────

export default function ArbeidsOrdrePage({ params }: { params: Promise<{ propertyId: string }> }) {
    const { propertyId } = React.use(params);
    const [tasks, setTasks] = useState<MaintenanceTask[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<StatusFilter>('pending');

    const loadTasks = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchAPI<MaintenanceTask[]>(
                `/fdvu/maintenance/tasks?property_id=${propertyId}&status=${filter}`
            );
            setTasks(Array.isArray(data) ? data.sort(sortByDueDate) : []);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Kunne ikke hente arbeidsordre');
            setTasks([]);
        } finally {
            setLoading(false);
        }
    }, [propertyId, filter]);

    useEffect(() => {
        loadTasks();
    }, [loadTasks]);

    const overdueCount = tasks.filter(t => isOverdue(t)).length;

    return (
        <div className="p-4 sm:p-6 space-y-5 max-w-2xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Link href={`/fdvu/${propertyId}`} className="text-muted hover:text-foreground transition-colors p-1">
                    <ChevronLeft size={22} />
                </Link>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <ClipboardList className="text-primary" size={22} /> Arbeidsordre
                    </h1>
                    <p className="text-muted text-xs mt-0.5 font-mono">{propertyId}</p>
                </div>
                <button
                    onClick={loadTasks}
                    disabled={loading}
                    className="p-2.5 rounded-xl border border-border text-muted hover:text-foreground transition-colors"
                    title="Oppdater"
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            {/* Filter bar */}
            <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 sm:mx-0 sm:px-0">
                {FILTER_LABELS.map(({ key, label }) => {
                    const isActive = filter === key;
                    const isOverdueFilter = key === 'overdue';
                    return (
                        <button
                            key={key}
                            onClick={() => setFilter(key)}
                            className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap border transition-colors ${
                                isActive
                                    ? 'bg-primary text-primary-foreground border-primary'
                                    : 'border-border text-muted hover:border-primary/50 hover:text-foreground'
                            }`}
                        >
                            {label}
                            {isOverdueFilter && overdueCount > 0 && (
                                <span className={`rounded-full px-1.5 py-0.5 text-xs font-bold ${
                                    isActive ? 'bg-white/20' : 'bg-destructive text-destructive-foreground'
                                }`}>
                                    {overdueCount}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Error banner */}
            {error && (
                <div className="flex items-start gap-2 text-destructive text-xs bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-3">
                    <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                    <span>{error}</span>
                </div>
            )}

            {/* Task list */}
            {loading ? (
                <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-24 bg-card border border-border rounded-2xl animate-pulse" />
                    ))}
                </div>
            ) : tasks.length === 0 ? (
                <div className="text-center py-16 space-y-3">
                    <ClipboardList size={40} className="mx-auto text-muted opacity-30" />
                    <p className="text-muted text-base font-medium">Ingen {FILTER_LABELS.find(f => f.key === filter)?.label.toLowerCase()} oppgaver</p>
                    <p className="text-xs text-muted">
                        {filter === 'completed'
                            ? 'Ingen oppgaver er merket som fullført ennå.'
                            : 'Alle oppgaver er à jour – bra jobbet!'}
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {tasks.map(task => (
                        <TaskCard
                            key={task.task_id}
                            task={task}
                            onCompleted={loadTasks}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
