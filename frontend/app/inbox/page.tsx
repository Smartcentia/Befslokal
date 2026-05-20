"use client";
import React, { useEffect, useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import {
    Bell, AlertTriangle, CheckSquare, Wrench, FileText,
    Clock, ChevronRight, RefreshCw, AlertCircle, PenSquare, X, Send, Loader2
} from 'lucide-react';

interface Notification {
    notification_id: string;
    title: string;
    message: string;
    created_at: string;
    is_read: boolean;
    notification_type?: string;
    related_entity_type?: string;
    related_entity_id?: string;
}

interface Task {
    id: string;
    title: string;
    description: string;
    type: 'fdvu' | 'maintenance' | 'checklist' | 'contract' | 'deviation';
    priority: 'low' | 'medium' | 'high' | 'critical';
    due_date?: string;
    property_name?: string;
    property_id?: string;
    status: string;
}

interface Deviation {
    case_id: string;
    title: string;
    description?: string;
    priority: string;
    status: string;
    created_at: string;
    property_name?: string;
    property_id?: string;
}

type Tab = 'oppgaver' | 'avvik' | 'varsler';

const PRIORITY_COLORS: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400',
    high:     'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400',
    medium:   'bg-yellow-100 text-yellow-700 dark:bg-yellow-950/40 dark:text-yellow-400',
    low:      'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400',
};

const PRIORITY_LABEL: Record<string, string> = {
    critical: 'Kritisk', high: 'Høy', medium: 'Medium', low: 'Lav',
};

function relativeTime(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const min = Math.floor(diff / 60000);
    if (min < 60) return `${min} min siden`;
    const hrs = Math.floor(min / 60);
    if (hrs < 24) return `${hrs}t siden`;
    const days = Math.floor(hrs / 24);
    return `${days} dager siden`;
}

interface UserListItem {
    user_id: string;
    email: string;
    name: string;
}

export default function InboxPage() {
    const [activeTab, setActiveTab] = useState<Tab>('oppgaver');
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [deviations, setDeviations] = useState<Deviation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    // Compose state
    const [showCompose, setShowCompose] = useState(false);
    const [users, setUsers] = useState<UserListItem[]>([]);
    const [toEmail, setToEmail] = useState('');
    const [composeTitle, setComposeTitle] = useState('');
    const [composeMessage, setComposeMessage] = useState('');
    const [composeSending, setComposeSending] = useState(false);
    const [composeError, setComposeError] = useState<string | null>(null);
    const [composeSent, setComposeSent] = useState(false);

    useEffect(() => {
        loadAll();
        fetchAPI('/internal-control/users/list').then((u: UserListItem[]) => setUsers(u ?? [])).catch(() => {});
    }, []);

    const loadAll = async () => {
        setLoading(true);
        setError(null);
        try {
            const [notifs, devs] = await Promise.allSettled([
                fetchAPI('/internal-control/notifications'),
                fetchAPI('/internal-control/cases?status=open&limit=50'),
            ]);
            if (notifs.status === 'fulfilled') setNotifications(notifs.value ?? []);
            if (devs.status === 'fulfilled') {
                const data = devs.value;
                setDeviations(Array.isArray(data) ? data : (data?.cases ?? data?.items ?? []));
            }
            // Kontrakter som utløper i inneværende år — for admin: alle, ellers kun tilgjengelige
            const thisYearEnd = new Date(new Date().getFullYear(), 11, 31); // 31. des i år
            const today = new Date();
            const contractTasks: Task[] = await fetchAPI('/contracts?status=active&limit=1000').then((c: any[]) => {
                return (Array.isArray(c) ? c : [])
                    .filter((ct: any) => {
                        // Hent sluttdato fra end_date eller periods[0].end_date
                        const rawEnd = ct.end_date ?? ct.periods?.[0]?.end_date;
                        if (!rawEnd) return false;
                        const endDate = new Date(rawEnd);
                        return endDate >= today && endDate <= thisYearEnd;
                    })
                    .sort((a: any, b: any) => {
                        const aEnd = a.end_date ?? a.periods?.[0]?.end_date ?? '';
                        const bEnd = b.end_date ?? b.periods?.[0]?.end_date ?? '';
                        return aEnd < bEnd ? -1 : 1;
                    })
                    .map((ct: any) => {
                        // Eiendomsnavn via unit.property (eager-loaded av backend)
                        const propName = ct.unit?.property?.name ?? null;
                        const propId   = ct.unit?.property_id ?? ct.unit?.property?.property_id ?? null;
                        const partyName = ct.party?.name ?? null;

                        const rawEnd = ct.end_date ?? ct.periods?.[0]?.end_date;
                        const daysLeft = rawEnd
                            ? Math.ceil((new Date(rawEnd).getTime() - today.getTime()) / 86400000)
                            : 999;

                        const priority: Task['priority'] =
                            daysLeft <= 30 ? 'critical' :
                            daysLeft <= 60 ? 'high' :
                            daysLeft <= 90 ? 'medium' : 'low';

                        return {
                            id: ct.contract_id,
                            title: ct.contract_name ?? 'Kontrakt utløper snart',
                            description: [propName, partyName].filter(Boolean).join(' · ')
                                || `Utløper ${rawEnd ?? ''}`,
                            type: 'contract' as const,
                            priority,
                            due_date: rawEnd,
                            property_name: propName ?? undefined,
                            property_id: propId ?? undefined,
                            status: 'open',
                        };
                    });
            }).catch(() => []);
            setTasks(contractTasks);
        } catch (e) {
            setError('Kunne ikke laste innboks.');
        } finally {
            setLoading(false);
        }
    };

    const openCompose = () => {
        setShowCompose(true);
        setToEmail('');
        setComposeTitle('');
        setComposeMessage('');
        setComposeError(null);
        setComposeSent(false);
    };

    const sendMessage = async () => {
        if (!toEmail || !composeTitle || !composeMessage) {
            setComposeError('Fyll ut alle felt.');
            return;
        }
        setComposeSending(true);
        setComposeError(null);
        try {
            await fetchAPI('/internal-control/messages/send', {
                method: 'POST',
                body: JSON.stringify({ to_email: toEmail, title: composeTitle, message: composeMessage }),
            });
            setComposeSent(true);
            setTimeout(() => setShowCompose(false), 1500);
        } catch {
            setComposeError('Kunne ikke sende melding. Prøv igjen.');
        } finally {
            setComposeSending(false);
        }
    };

    const markRead = async (n: Notification) => {
        if (!n.is_read) {
            await fetchAPI(`/internal-control/notifications/${n.notification_id}/read`, { method: 'POST' }).catch(() => {});
            setNotifications(prev => prev.map(p => p.notification_id === n.notification_id ? { ...p, is_read: true } : p));
        }
        if (n.related_entity_type === 'case' && n.related_entity_id) router.push(`/cases/${n.related_entity_id}`);
        else if (n.related_entity_id) router.push(`/properties/${n.related_entity_id}`);
    };

    const unreadCount = notifications.filter(n => !n.is_read).length;
    const openDeviations = deviations.filter(d => d.status?.toLowerCase() === 'open');

    const tabs: { id: Tab; label: string; icon: React.ReactNode; count: number }[] = [
        { id: 'oppgaver', label: 'Oppgaver', icon: <CheckSquare size={16} />, count: tasks.length },
        { id: 'avvik',    label: 'Avvik',    icon: <AlertTriangle size={16} />, count: openDeviations.length },
        { id: 'varsler',  label: 'Varsler',  icon: <Bell size={16} />, count: unreadCount },
    ];

    return (
        <div className="min-h-screen bg-transparent p-6 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                        <Bell size={24} className="text-primary" />
                        Innboks
                    </h1>
                    <p className="text-sm text-muted-foreground mt-0.5">Dine oppgaver, avvik og varsler</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={openCompose}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        <PenSquare size={15} />
                        Ny melding
                    </button>
                    <button onClick={loadAll} className="p-2 rounded-lg hover:bg-muted transition-colors" title="Oppdater">
                        <RefreshCw size={16} className="text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Faner */}
            <div className="flex gap-1 mb-6 bg-muted/40 rounded-xl p-1">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                            activeTab === tab.id
                                ? 'bg-surface shadow-sm text-foreground'
                                : 'text-muted-foreground hover:text-foreground'
                        }`}
                    >
                        {tab.icon}
                        {tab.label}
                        {tab.count > 0 && (
                            <span className={`text-xs rounded-full px-1.5 py-0.5 font-bold ${
                                activeTab === tab.id ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                            }`}>
                                {tab.count}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {error && (
                <div className="mb-4 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-400 text-sm">
                    <AlertCircle size={16} /> {error}
                </div>
            )}

            {loading ? (
                <div className="flex items-center justify-center py-20 text-muted-foreground">
                    <RefreshCw size={20} className="animate-spin mr-2" /> Laster...
                </div>
            ) : (
                <>
                    {/* OPPGAVER */}
                    {activeTab === 'oppgaver' && (
                        <div className="space-y-3">
                            {tasks.length === 0 ? (
                                <EmptyState icon={<CheckSquare size={32} />} text="Ingen aktive oppgaver" />
                            ) : tasks.map(task => (
                                <div
                                    key={task.id}
                                    onClick={() => task.property_id && router.push(`/properties/${task.property_id}`)}
                                    className="bg-surface border border-border rounded-xl p-4 flex items-start gap-4 hover:shadow-md transition-all cursor-pointer group"
                                >
                                    <div className="p-2 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 rounded-lg mt-0.5">
                                        {task.type === 'contract' ? <FileText size={18} /> : <Wrench size={18} />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <span className="font-semibold text-foreground text-sm">{task.title}</span>
                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${PRIORITY_COLORS[task.priority]}`}>
                                                {PRIORITY_LABEL[task.priority]}
                                            </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground truncate">{task.description}</p>
                                        {task.due_date && (
                                            <div className="flex items-center gap-1 mt-1 text-xs text-orange-600 dark:text-orange-400">
                                                <Clock size={11} /> Utløper {task.due_date}
                                            </div>
                                        )}
                                    </div>
                                    <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors mt-1" />
                                </div>
                            ))}
                        </div>
                    )}

                    {/* AVVIK */}
                    {activeTab === 'avvik' && (
                        <div className="space-y-3">
                            {openDeviations.length === 0 ? (
                                <EmptyState icon={<AlertTriangle size={32} />} text="Ingen åpne avvik" />
                            ) : openDeviations.map(dev => (
                                <div
                                    key={dev.case_id}
                                    onClick={() => router.push(`/cases/${dev.case_id}`)}
                                    className="bg-surface border border-border rounded-xl p-4 flex items-start gap-4 hover:shadow-md transition-all cursor-pointer group"
                                >
                                    <div className="p-2 bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 rounded-lg mt-0.5">
                                        <AlertTriangle size={18} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-0.5">
                                            <span className="font-semibold text-foreground text-sm">{dev.title}</span>
                                            {dev.priority && (
                                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${PRIORITY_COLORS[dev.priority.toLowerCase()] ?? PRIORITY_COLORS.medium}`}>
                                                    {PRIORITY_LABEL[dev.priority.toLowerCase()] ?? dev.priority}
                                                </span>
                                            )}
                                        </div>
                                        {dev.property_name && (
                                            <p className="text-xs text-muted-foreground">{dev.property_name}</p>
                                        )}
                                        <p className="text-xs text-muted-foreground mt-0.5">{relativeTime(dev.created_at)}</p>
                                    </div>
                                    <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors mt-1" />
                                </div>
                            ))}
                        </div>
                    )}

                    {/* VARSLER */}
                    {activeTab === 'varsler' && (
                        <div className="space-y-3">
                            {notifications.length === 0 ? (
                                <EmptyState icon={<Bell size={32} />} text="Ingen varsler" />
                            ) : notifications.map(n => (
                                <div
                                    key={n.notification_id}
                                    onClick={() => markRead(n)}
                                    className={`bg-surface border rounded-xl p-4 flex items-start gap-4 hover:shadow-md transition-all cursor-pointer group ${
                                        !n.is_read ? 'border-primary/40 bg-primary/5' : 'border-border'
                                    }`}
                                >
                                    <div className={`w-2.5 h-2.5 rounded-full mt-2 flex-shrink-0 ${!n.is_read ? 'bg-primary' : 'bg-muted'}`} />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm mb-0.5 ${!n.is_read ? 'font-bold text-foreground' : 'font-medium text-muted-foreground'}`}>
                                            {n.title}
                                        </p>
                                        <p className="text-xs text-muted-foreground line-clamp-1">{n.message}</p>
                                        <p className="text-xs text-muted-foreground mt-1">{relativeTime(n.created_at)}</p>
                                    </div>
                                    <ChevronRight size={16} className="text-muted-foreground group-hover:text-foreground transition-colors mt-1" />
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
            {/* Compose modal */}
            {showCompose && (
                <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
                    <div className="bg-surface border border-border rounded-2xl shadow-xl w-full max-w-lg">
                        {/* Modal header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                            <h2 className="font-semibold text-foreground flex items-center gap-2">
                                <PenSquare size={16} className="text-primary" />
                                Ny melding
                            </h2>
                            <button onClick={() => setShowCompose(false)} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                                <X size={16} className="text-muted-foreground" />
                            </button>
                        </div>

                        {composeSent ? (
                            <div className="px-5 py-10 text-center text-sm text-green-600 dark:text-green-400 font-medium">
                                ✓ Melding sendt!
                            </div>
                        ) : (
                            <div className="px-5 py-4 space-y-4">
                                {/* To */}
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Til</label>
                                    {users.length > 0 ? (
                                        <select
                                            value={toEmail}
                                            onChange={e => setToEmail(e.target.value)}
                                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                                        >
                                            <option value="">Velg mottaker…</option>
                                            {users.map(u => (
                                                <option key={u.user_id} value={u.email}>{u.name} ({u.email})</option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            type="email"
                                            placeholder="mottaker@example.com"
                                            value={toEmail}
                                            onChange={e => setToEmail(e.target.value)}
                                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                                        />
                                    )}
                                </div>

                                {/* Title */}
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Emne</label>
                                    <input
                                        type="text"
                                        placeholder="Skriv emne…"
                                        value={composeTitle}
                                        onChange={e => setComposeTitle(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                                    />
                                </div>

                                {/* Message */}
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">Melding</label>
                                    <textarea
                                        rows={5}
                                        placeholder="Skriv din melding her…"
                                        value={composeMessage}
                                        onChange={e => setComposeMessage(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                                    />
                                </div>

                                {composeError && (
                                    <p className="text-xs text-red-600 dark:text-red-400">{composeError}</p>
                                )}

                                {/* Actions */}
                                <div className="flex justify-end gap-3 pt-1">
                                    <button
                                        onClick={() => setShowCompose(false)}
                                        className="px-4 py-2 rounded-lg border border-border text-sm text-muted-foreground hover:bg-muted transition-colors"
                                    >
                                        Avbryt
                                    </button>
                                    <button
                                        onClick={sendMessage}
                                        disabled={composeSending}
                                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
                                    >
                                        {composeSending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                                        Send
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function EmptyState({ icon, text }: { icon: React.ReactNode; text: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
            <div className="opacity-30">{icon}</div>
            <p className="text-sm">{text}</p>
        </div>
    );
}
