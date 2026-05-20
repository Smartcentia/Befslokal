"use client";

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Calendar, momentLocalizer, Event } from 'react-big-calendar';
import moment from 'moment';
import 'moment/locale/nb';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useAuth } from "@/hooks/useAuth";
import { fetchAPI } from '../../lib/api/client';
import CalendarEventModal from './CalendarEventModal';
import {
    Loader2,
    Calendar as CalendarIcon,
    Info,
    Filter,
    Building2,
    Tag,
    User as UserIcon,
    AlertCircle,
    Play
} from "lucide-react";

moment.locale('nb');
const localizer = momentLocalizer(moment);

interface ScheduledActivity {
    activity_id: string;
    property_id: string;
    title: string;
    description: string;
    activity_type: string;
    category: string;
    priority: string;
    next_due_date: string;
    responsible_role: string;
}

interface InternalControlCase {
    case_id: string;
    property_id: string;
    title: string;
    description: string;
    status: string;
    priority: string;
    due_date?: string;
    created_at: string;
}

interface Property {
    property_id: string;
    name?: string;
    address: string;
}

interface CalendarEvent extends Event {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'planned' | 'active_case';
    resource?: ScheduledActivity | InternalControlCase;
    priority: string;
}

export default function GeneralCalendarPage() {
    const { email, role } = useAuth();
    const [activities, setActivities] = useState<ScheduledActivity[]>([]);
    const [cases, setCases] = useState<InternalControlCase[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedProperty, setSelectedProperty] = useState<string>('all');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [selectedRole, setSelectedRole] = useState<string>('all');
    const [properties, setProperties] = useState<Property[]>([]);
    const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const isAdmin = email === "admin@befs.no" ||
        email === "frankvevle@gmail.com" ||
        role === "ADMIN";

    const fetchProperties = async () => {
        try {
            const data = await fetchAPI('/properties');
            setProperties(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Failed to fetch properties:', error);
        }
    };

    const fetchActivities = async () => {
        try {
            const data = await fetchAPI('/hms/activities/scheduled');
            setActivities(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Failed to fetch activities:', error);
            setActivities([]);
        }
    };

    const fetchCases = async () => {
        try {
            const data = await fetchAPI('/internal-control/cases');
            setCases(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Failed to fetch cases:', error);
            setCases([]);
        }
    };

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            await Promise.all([
                fetchProperties(),
                fetchActivities(),
                fetchCases()
            ]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleSelectEvent = (event: CalendarEvent) => {
        setSelectedEvent(event);
        setIsModalOpen(true);
    };

    const events = useMemo(() => {
        const plannedEvents: CalendarEvent[] = activities
            .filter(act => {
                if (selectedProperty !== 'all' && act.property_id !== selectedProperty) return false;
                if (selectedCategory !== 'all' && act.category !== selectedCategory) return false;
                if (selectedRole !== 'all' && act.responsible_role !== selectedRole) return false;
                return true;
            })
            .map(activity => {
                const startDate = new Date(activity.next_due_date);
                return {
                    id: activity.activity_id,
                    title: `[Plan] ${activity.title}`,
                    start: startDate,
                    end: startDate,
                    type: 'planned',
                    priority: activity.priority,
                    resource: activity
                };
            });

        const activeCaseEvents: CalendarEvent[] = cases
            .filter(c => {
                if (selectedProperty !== 'all' && c.property_id !== selectedProperty) return false;
                // Cases don't have category yet in model, but we can add filter later
                return true;
            })
            .filter(c => c.due_date) // Only show if it has a due date
            .map(c => {
                const startDate = new Date(c.due_date!);
                return {
                    id: c.case_id,
                    title: `[Sak] ${c.title}`,
                    start: startDate,
                    end: startDate,
                    type: 'active_case',
                    priority: c.priority,
                    resource: c
                };
            });

        return [...plannedEvents, ...activeCaseEvents];
    }, [activities, cases, selectedProperty, selectedCategory, selectedRole]);

    const handleGenerateActivities = async () => {
        if (!confirm('Vil du generere alle HMS-aktiviteter på nytt? Dette kan opprette mange nye aktiviteter.')) {
            return;
        }

        try {
            const stats = await fetchAPI('/hms/activities/generate', {
                method: 'POST',
            });
            alert(`Generert ${stats.total_activities_generated} aktiviteter for ${stats.properties_with_activities} eiendommer`);
            fetchActivities();
        } catch (error) {
            console.error('Failed to generate activities:', error);
            alert('Feil ved generering av aktiviteter');
        }
    };

    const eventStyleGetter = (event: CalendarEvent) => {
        let backgroundColor = 'hsl(var(--primary))';
        let borderStyle = 'solid';
        let borderWidth = '1px';
        let borderColor = 'transparent';

        // Base color by priority
        switch (event.priority) {
            case 'critical':
                backgroundColor = '#dc2626'; // red
                break;
            case 'high':
                backgroundColor = '#ea580c'; // orange
                break;
            case 'medium':
                backgroundColor = '#2563eb'; // blue
                break;
            case 'low':
                backgroundColor = '#16a34a'; // green
                break;
        }

        // Style by type
        if (event.type === 'planned') {
            borderStyle = 'dashed';
            borderWidth = '2px';
            borderColor = 'rgba(255,255,255,0.4)';
        }

        return {
            style: {
                backgroundColor,
                borderRadius: '6px',
                opacity: 0.9,
                color: 'white',
                borderStyle,
                borderWidth,
                borderColor,
                display: 'block',
                padding: '2px 6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }
        };
    };

    const messages = {
        today: 'I dag',
        previous: 'Forrige',
        next: 'Neste',
        month: 'Måned',
        week: 'Uke',
        day: 'Dag',
        agenda: 'Agenda',
        date: 'Dato',
        time: 'Tid',
        event: 'Hendelse',
        noEventsInRange: 'Ingen aktiviteter i dette tidsrommet',
        showMore: (total: number) => `+ ${total} flere`
    };

    return (
        <div className="space-y-8 max-w-400 mx-auto p-4 md:p-8">
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                <div className="space-y-1">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <CalendarIcon className="h-8 w-8 text-primary" />
                        </div>
                        <h2 className="text-3xl font-extrabold tracking-tight">Årshjul & Kalender</h2>
                    </div>
                    <p className="text-muted-foreground text-lg ml-12">
                        Planlagte HMS-aktiviteter, internkontroll og rapporteringsfrister på tvers av porteføljen.
                    </p>
                </div>

                {isAdmin && (
                    <button
                        onClick={handleGenerateActivities}
                        className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:scale-105 active:scale-95 transition-all font-semibold shadow-lg shadow-primary/20"
                    >
                        <Play size={18} />
                        Generer Aktiviteter
                    </button>
                )}
            </div>

            <div className="flex flex-col xl:flex-row gap-8">
                {/* Filters Sidebar */}
                <div className="w-full xl:w-80 shrink-0 space-y-6">
                    <div className="bg-surface p-6 rounded-2xl border border-border shadow-xl space-y-6">
                        <div className="flex items-center gap-3 pb-2 border-b border-border/50">
                            <Filter size={20} className="text-primary" />
                            <h3 className="font-bold text-lg">Filtrering</h3>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <Building2 size={14} />
                                    Eiendom
                                </label>
                                <select
                                    value={selectedProperty}
                                    title="Velg eiendom"
                                    onChange={(e) => setSelectedProperty(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background/50 border border-border rounded-xl focus:ring-4 focus:ring-primary/10 outline-none text-sm transition-all"
                                >
                                    <option value="all">Alle eiendommer</option>
                                    {properties.map(prop => (
                                        <option key={prop.property_id} value={prop.property_id}>
                                            {prop.name || prop.address}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <Tag size={14} />
                                    Kategori
                                </label>
                                <select
                                    value={selectedCategory}
                                    title="Velg kategori"
                                    onChange={(e) => setSelectedCategory(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background/50 border border-border rounded-xl focus:ring-4 focus:ring-primary/10 outline-none text-sm transition-all"
                                >
                                    <option value="all">Alle kategorier</option>
                                    <option value="brann">Brannvern</option>
                                    <option value="teknisk">Teknisk</option>
                                    <option value="hms">HMS</option>
                                    <option value="sikkerhet">Sikkerhet</option>
                                    <option value="inneklima">Inneklima</option>
                                    <option value="rapportering">Rapportering</option>
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <UserIcon size={14} />
                                    Rolle
                                </label>
                                <select
                                    value={selectedRole}
                                    title="Velg rolle"
                                    onChange={(e) => setSelectedRole(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background/50 border border-border rounded-xl focus:ring-4 focus:ring-primary/10 outline-none text-sm transition-all"
                                >
                                    <option value="all">Alle roller</option>
                                    <option value="vaktmester">Vaktmester</option>
                                    <option value="eiendomsansvarlig">Eiendomsansvarlig</option>
                                    <option value="områdeleder">Områdeleder</option>
                                    <option value="admin">Systemadmin</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="bg-surface p-6 rounded-2xl border border-border shadow-xl space-y-6">
                        <h3 className="font-bold flex items-center gap-2 border-b border-border/50 pb-2">
                            <Info size={18} className="text-primary" />
                            Forklaring
                        </h3>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Type</p>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-sm">
                                        <div className="w-4 h-4 border-2 border-dashed border-white/40 bg-primary/40 rounded"></div>
                                        <span className="text-muted-foreground italic">Planlagt HMS</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm">
                                        <div className="w-4 h-4 bg-primary rounded shadow-sm"></div>
                                        <span>Aktiv Sak</span>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Prioritet</p>
                                <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
                                    <div className="flex items-center gap-2 px-2 py-1 bg-red-500/10 text-red-500 rounded-lg">
                                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                                        Kritisk
                                    </div>
                                    <div className="flex items-center gap-2 px-2 py-1 bg-orange-500/10 text-orange-500 rounded-lg">
                                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                                        Høy
                                    </div>
                                    <div className="flex items-center gap-2 px-2 py-1 bg-blue-500/10 text-blue-500 rounded-lg">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                                        Medium
                                    </div>
                                    <div className="flex items-center gap-2 px-2 py-1 bg-green-500/10 text-green-500 rounded-lg">
                                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                        Lav
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Calendar View */}
                <div className="flex-1 min-w-0">
                    <div className="bg-surface rounded-4xl border border-border shadow-2xl p-4 md:p-8 overflow-hidden min-h-212.5 relative">
                        {loading && (
                            <div className="absolute inset-0 z-50 bg-surface/80 backdrop-blur-sm flex flex-col items-center justify-center gap-4">
                                <div className="p-4 bg-background border border-border rounded-2xl shadow-xl flex items-center gap-3">
                                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                                    <p className="font-bold text-lg animate-pulse">Oppdaterer årshjul...</p>
                                </div>
                            </div>
                        )}

                        <div className="h-187.5 calendar-container custom-calendar">
                            <Calendar
                                localizer={localizer}
                                events={events}
                                startAccessor="start"
                                endAccessor="end"
                                style={{ height: '100%' }}
                                messages={messages}
                                eventPropGetter={eventStyleGetter}
                                onSelectEvent={handleSelectEvent}
                                popup
                                dayPropGetter={(date: Date) => {
                                    const day = date.getDay();
                                    if (day === 0 || day === 6) {
                                        return { className: 'bg-background/20 opacity-60' };
                                    }
                                    return {};
                                }}
                                tooltipAccessor={(event: CalendarEvent) =>
                                    event.resource ? `${event.title}: ${event.resource.description || 'Ingen beskrivelse'}` : ''
                                }
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Upcoming Activities List */}
            <div className="bg-surface rounded-4xl border border-border shadow-2xl overflow-hidden">
                <div className="p-8 border-b border-border/50 flex justify-between items-center bg-background/50">
                    <h2 className="text-2xl font-bold flex items-center gap-3">
                        <AlertCircle className="text-primary" />
                        Neste 14 dager (Prioriterte hendelser)
                    </h2>
                    <div className="flex gap-4 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-primary/40 border border-dashed border-white/20 rounded-full"></div>
                            <span className="text-muted-foreground">Planlagt</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-primary rounded-full"></div>
                            <span className="text-muted-foreground">Utestående saken</span>
                        </div>
                    </div>
                </div>

                <div className="p-8">
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[...activities.map(a => ({ ...a, source: 'planned' as const, date: a.next_due_date })),
                        ...cases.map(c => ({ ...c, source: 'case' as const, date: c.due_date }))]
                            .filter(item => {
                                if (!item.date) return false;
                                const date = new Date(item.date);
                                const now = new Date();
                                const horizon = new Date();
                                horizon.setDate(horizon.getDate() + 14);
                                return date >= now && date <= horizon;
                            })
                            .sort((a, b) => new Date(a.date!).getTime() - new Date(b.date!).getTime())
                            .map((item, idx) => (
                                <div
                                    key={idx}
                                    className={`group p-5 rounded-2xl border ${item.source === 'case' ? 'border-primary/30 bg-primary/5' : 'border-border bg-background/30'} hover:border-primary/50 hover:shadow-lg transition-all relative overflow-hidden`}
                                >
                                    {/* Priority Indicator */}
                                    <div className={`absolute top-0 right-0 w-2 h-full ${item.priority === 'critical' ? 'bg-red-500' :
                                        item.priority === 'high' ? 'bg-orange-500' :
                                            item.priority === 'medium' ? 'bg-blue-500' : 'bg-green-500'
                                        }`} />

                                    <div className="space-y-3">
                                        <div className="flex justify-between items-start">
                                            <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${item.source === 'case' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                                                }`}>
                                                {item.source === 'case' ? 'Utestående' : 'Planlagt'}
                                            </span>
                                            <span className="text-xs font-mono font-medium text-muted-foreground">
                                                {moment(item.date).format('DD. MMM')}
                                            </span>
                                        </div>

                                        <h4 className="font-bold leading-tight group-hover:text-primary transition-colors pr-2">
                                            {item.title}
                                        </h4>

                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                            <div className="flex items-center gap-1">
                                                <Building2 size={12} />
                                                <span className="truncate max-w-25">
                                                    {properties.find(p => p.property_id === item.property_id)?.name || 'Ukjent Eiendom'}
                                                </span>
                                            </div>
                                            {('responsible_role' in item) && item.responsible_role && (
                                                <div className="flex items-center gap-1">
                                                    <UserIcon size={12} />
                                                    {item.responsible_role}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))
                        }
                        {events.length === 0 && (
                            <div className="col-span-full py-20 text-center space-y-4 bg-background/30 rounded-3xl border-2 border-dashed border-border">
                                <Info className="mx-auto h-12 w-12 text-muted-foreground opacity-20" />
                                <p className="text-muted-foreground font-medium italic">Ingen aktiviteter planlagt de neste 14 dagene.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {isModalOpen && selectedEvent && (
                <CalendarEventModal
                    event={selectedEvent}
                    onClose={() => {
                        setIsModalOpen(false);
                        setSelectedEvent(null);
                    }}
                    onRefresh={loadData}
                    propertyName={properties.find(p => p.property_id === selectedEvent.resource?.property_id)?.name}
                />
            )}

            <style jsx global>{`
                .calendar-container .rbc-calendar {
                    font-family: inherit;
                }
                .calendar-container .rbc-header {
                    padding: 16px 8px;
                    font-weight: 700;
                    text-transform: uppercase;
                    font-size: 0.85rem;
                    letter-spacing: 0.05em;
                    color: hsl(var(--muted-foreground));
                    border-bottom: 0px solid hsl(var(--border)) !important;
                    background: hsl(var(--surface));
                }
                .calendar-container .rbc-month-view {
                    border: 1px solid hsl(var(--border));
                    border-radius: 24px;
                    overflow: hidden;
                    background: hsl(var(--surface));
                }
                .calendar-container .rbc-day-bg {
                    background: transparent;
                }
                .calendar-container .rbc-day-bg + .rbc-day-bg {
                    border-left: 1px solid hsl(var(--border));
                }
                .calendar-container .rbc-month-row + .rbc-month-row {
                    border-top: 1px solid hsl(var(--border));
                }
                .calendar-container .rbc-off-range-bg {
                    background: hsl(var(--muted) / 0.1);
                }
                .calendar-container .rbc-today {
                    background: hsl(var(--primary) / 0.05);
                }
                
                /* Date Cell Styling - IMPACT: Make dates visible */
                .calendar-container .rbc-date-cell {
                    padding: 12px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    color: hsl(var(--foreground));
                    opacity: 0.7;
                    text-align: right;
                }
                .calendar-container .rbc-date-cell.rbc-now {
                    font-weight: 800;
                    color: hsl(var(--primary));
                    opacity: 1;
                }
                .calendar-container .rbc-date-cell > a {
                    color: inherit;
                    text-decoration: none;
                }

                /* Toolbar Styling */
                .calendar-container .rbc-toolbar {
                    margin-bottom: 24px;
                    gap: 12px;
                }
                .calendar-container .rbc-toolbar-label {
                    font-size: 1.5rem;
                    font-weight: 800;
                    text-transform: capitalize;
                    color: hsl(var(--foreground));
                }
                .calendar-container .rbc-toolbar button {
                    color: hsl(var(--foreground));
                    border: 1px solid hsl(var(--border));
                    border-radius: 12px;
                    font-size: 0.9rem;
                    font-weight: 500;
                    padding: 8px 16px;
                    transition: all 0.2s;
                }
                .calendar-container .rbc-toolbar button:active, 
                .calendar-container .rbc-toolbar button.rbc-active {
                    background-color: hsl(var(--primary));
                    color: hsl(var(--primary-foreground));
                    border-color: hsl(var(--primary));
                    box-shadow: 0 4px 12px hsl(var(--primary) / 0.3);
                }
                .calendar-container .rbc-toolbar button:hover {
                    background-color: hsl(var(--muted) / 0.5);
                    transform: translateY(-1px);
                }

                /* Event Styling */
                .calendar-container .rbc-event {
                    padding: 2px 5px;
                    border-radius: 6px;
                }
                .calendar-container .rbc-show-more {
                    color: hsl(var(--primary));
                    background: transparent;
                    font-weight: 600;
                    font-size: 0.8rem;
                    padding: 4px;
                    border-radius: 4px;
                }
                .calendar-container .rbc-show-more:hover {
                    background: hsl(var(--primary) / 0.1);
                    text-decoration: none;
                }
            `}</style>

        </div>
    );
}
