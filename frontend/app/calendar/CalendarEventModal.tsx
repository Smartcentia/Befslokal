"use client";

import { X, Calendar, Activity, Building2, User, ArrowRight, Play, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import moment from "moment";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { fetchAPI } from "../../lib/api/client";

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

interface CalendarEvent {
    id: string;
    title: string;
    start: Date;
    end: Date;
    type: 'planned' | 'active_case';
    resource?: ScheduledActivity | InternalControlCase;
    priority: string;
}

interface CalendarEventModalProps {
    event: CalendarEvent | null;
    onClose: () => void;
    onRefresh: () => void;
    propertyName?: string;
}

export default function CalendarEventModal({ event, onClose, onRefresh, propertyName }: CalendarEventModalProps) {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    if (!event) return null;

    const isPlanned = event.type === 'planned';
    const resource = event.resource;

    const handleStartActivity = async () => {
        if (!resource || !('activity_id' in resource)) return;
        
        setLoading(true);
        try {
            await fetchAPI(`/hms/activities/scheduled/${resource.activity_id}/trigger`, {
                method: 'POST'
            });
            onRefresh();
            onClose();
        } catch (error) {
            console.error("Failed to start activity:", error);
            alert("Feil ved start av aktivitet");
        } finally {
            setLoading(false);
        }
    };

    const handleGoToCase = () => {
        const caseId = (resource && 'case_id' in resource) ? resource.case_id : event.id;
        if (caseId) {
            router.push(`/cases/${caseId}`);
        }
    };

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                />

                <motion.div
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    className="relative w-full max-w-lg bg-[#0f172a] rounded-3xl shadow-2xl border border-white/10 overflow-hidden"
                >
                    <div className="p-6 border-b border-white/5 bg-white/5 flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isPlanned ? 'bg-blue-500/20 text-blue-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                {isPlanned ? <Calendar size={20} /> : <CheckCircle2 size={20} />}
                            </div>
                            <h3 className="text-xl font-bold">{isPlanned ? 'Planlagt Aktivitet' : 'Aktiv Sak'}</h3>
                        </div>
                        <button 
                            onClick={onClose} 
                            className="p-2 hover:bg-white/5 rounded-full transition-colors text-slate-400"
                            title="Lukk"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="p-8 space-y-6">
                        <div className="space-y-4">
                            <h2 className="text-2xl font-extrabold leading-tight text-white">{event.title.replace(/^\[.*?\]\s*/, '')}</h2>
                            <p className="text-slate-400 leading-relaxed">
                                {resource?.description || "Ingen beskrivelse tilgjengelig for denne aktiviteten."}
                            </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-1">
                                    <Calendar size={10} /> Dato
                                </p>
                                <p className="font-semibold text-slate-200">{moment(event.start).format('DD. MMMM YYYY')}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 flex items-center gap-1">
                                    <Activity size={10} /> Prioritet
                                </p>
                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                                    event.priority === 'critical' ? 'bg-red-500/10 text-red-500' :
                                    event.priority === 'high' ? 'bg-orange-500/10 text-orange-500' :
                                    event.priority === 'medium' ? 'bg-blue-500/10 text-blue-400' : 'bg-emerald-500/10 text-emerald-400'
                                }`}>
                                    <div className={`w-1.5 h-1.5 rounded-full ${
                                        event.priority === 'critical' ? 'bg-red-500' :
                                        event.priority === 'high' ? 'bg-orange-500' :
                                        event.priority === 'medium' ? 'bg-blue-400' : 'bg-emerald-400'
                                    }`} />
                                    {event.priority?.toUpperCase()}
                                </span>
                            </div>
                        </div>

                        <div className="space-y-4 p-4 bg-white/5 rounded-2xl border border-white/5">
                            <div className="flex items-center gap-3 text-sm">
                                <Building2 size={16} className="text-slate-500" />
                                <div>
                                    <p className="text-[10px] font-bold uppercase text-slate-500">Eiendom</p>
                                    <p className="font-medium text-slate-200">{propertyName || "Ukjent Eiendom"}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 text-sm">
                                <User size={16} className="text-slate-500" />
                                <div>
                                    <p className="text-[10px] font-bold uppercase text-slate-500">Ansvarlig</p>
                                    <p className="font-medium text-slate-200">
                                        {(resource && 'responsible_role' in resource) ? resource.responsible_role : "Vaktmester (standard)"}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="p-6 bg-slate-900/50 border-t border-white/5 flex gap-3">
                        {isPlanned ? (
                            <button
                                onClick={handleStartActivity}
                                disabled={loading}
                                className="flex-1 flex items-center justify-center gap-2 py-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-500 active:scale-[0.98] transition-all disabled:opacity-50"
                            >
                                {loading ? "Starter..." : (
                                    <>
                                        <Play size={18} fill="currentColor" />
                                        Start HMS-oppgave nå
                                    </>
                                )}
                            </button>
                        ) : (
                            <button
                                onClick={handleGoToCase}
                                className="flex-1 flex items-center justify-center gap-2 py-4 bg-emerald-600 text-white rounded-2xl font-bold hover:bg-emerald-500 active:scale-[0.98] transition-all"
                            >
                                <ArrowRight size={18} />
                                Gå til saksbehandling
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            className="px-6 py-4 bg-white/5 text-slate-300 rounded-2xl font-bold hover:bg-white/10 transition-all border border-white/10"
                        >
                            Lukk
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
