"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { deviationService, Deviation } from '@/lib/api';
import { motion } from 'framer-motion';
import { AlertTriangle, Calendar, FileText, CheckCircle, ArrowLeft, Building, Activity } from 'lucide-react';

export default function DeviationDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = React.use(params);
    const [deviation, setDeviation] = useState<Deviation | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        deviationService.getById(id)
            .then(data => {
                setDeviation(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error loading deviation:", err);
                setLoading(false);
            });
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="text-blue-400 animate-pulse flex items-center gap-2">
                    <Activity className="animate-spin" /> Henter avviksdetaljer...
                </div>
            </div>
        );
    }

    if (!deviation) {
        return (
            <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-center p-8">
                <div className="bg-red-500/10 p-4 rounded-full mb-4">
                    <AlertTriangle className="w-12 h-12 text-red-500" />
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">Avvik ikke funnet</h1>
                <p className="text-slate-400 mb-6">Vi kunne ikke finne avviket med ID: {id}</p>
                <Link href="/deviations" className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors">
                    Tilbake til oversikten
                </Link>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f172a] p-4 sm:p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Navigation */}
                <Link
                    href="/deviations"
                    className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors group"
                >
                    <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                    Tilbake til avviksoversikt
                </Link>

                {/* Header Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-8 border border-slate-700/50"
                >
                    <div className="flex flex-col md:flex-row justify-between items-start gap-6">
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${deviation.severity === 'Critical' || deviation.severity === 'High'
                                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                                        : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                                    }`}>
                                    {deviation.severity} Priority
                                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${deviation.status === 'open'
                                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                        : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                                    }`}>
                                    {deviation.status === 'open' ? 'Åpen' : 'Lukket'}
                                </span>
                            </div>

                            <h1 className="text-3xl md:text-4xl font-bold text-white leading-tight">
                                {deviation.title}
                            </h1>

                            <div className="flex items-center gap-2 text-slate-400 font-mono text-sm">
                                <span className="text-slate-600">ID:</span> {deviation.id}
                            </div>
                        </div>

                        <div className="text-right space-y-1">
                            <div className="text-sm text-slate-500 uppercase tracking-wider font-bold">Opprettet</div>
                            <div className="text-white font-medium flex items-center justify-end gap-2">
                                <Calendar size={16} className="text-blue-400" />
                                {new Date(deviation.created_at).toLocaleDateString('no-NO')}
                            </div>
                        </div>
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="md:col-span-2 space-y-8">
                        {/* Description */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="glass-card p-8 border border-slate-700/50"
                        >
                            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                                    <FileText size={24} />
                                </div>
                                Beskrivelse
                            </h2>
                            <div className="prose prose-invert max-w-none text-slate-300 leading-relaxed bg-slate-800/30 p-6 rounded-xl border border-slate-700/30">
                                {deviation.description ? (
                                    <p>{deviation.description}</p>
                                ) : (
                                    <p className="text-slate-500 italic">Ingen beskrivelse tilgjengelig for dette avviket.</p>
                                )}
                            </div>
                        </motion.div>

                        {/* Recommended Actions */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="glass-card p-8 border border-slate-700/50 relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-5">
                                <Activity size={120} />
                            </div>

                            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-3 relative z-10">
                                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                                    <CheckCircle size={24} />
                                </div>
                                Anbefalte Tiltak
                            </h2>

                            <ul className="space-y-4 relative z-10">
                                <li className="flex gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700/30 hover:border-emerald-500/30 transition-colors group">
                                    <div className="mt-1 min-w-5 h-5 rounded-full border-2 border-slate-600 group-hover:border-emerald-500 transition-colors"></div>
                                    <span className="text-slate-300">Utfør ny verdivurdering av eiendommen for å kartlegge omfanget.</span>
                                </li>
                                <li className="flex gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700/30 hover:border-emerald-500/30 transition-colors group">
                                    <div className="mt-1 min-w-5 h-5 rounded-full border-2 border-slate-600 group-hover:border-emerald-500 transition-colors"></div>
                                    <span className="text-slate-300">Kontakt leietaker for avklaring av utbedringsplikt i henhold til kontrakt.</span>
                                </li>
                                <li className="flex gap-4 p-4 bg-slate-800/50 rounded-lg border border-slate-700/30 hover:border-emerald-500/30 transition-colors group">
                                    <div className="mt-1 min-w-5 h-5 rounded-full border-2 border-slate-600 group-hover:border-emerald-500 transition-colors"></div>
                                    <span className="text-slate-300">Oppdater HMS-dokumentasjon med nye funn.</span>
                                </li>
                            </ul>
                        </motion.div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-8">
                        {/* Property Card */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 }}
                            className="glass-card p-6 border border-slate-700/50"
                        >
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-700 pb-2">
                                Tilknyttet Eiendom
                            </h3>

                            <Link href={`/properties/${deviation.property_id}`} className="block group">
                                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700 group-hover:border-blue-500/50 transition-all">
                                    <div className="flex items-center gap-3 mb-2">
                                        <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400 group-hover:scale-110 transition-transform">
                                            <Building size={20} />
                                        </div>
                                        <div className="font-bold text-white group-hover:text-blue-400 transition-colors">
                                            Se Eiendom
                                        </div>
                                    </div>
                                    <div className="text-sm text-slate-400 pl-11">
                                        ID: {deviation.property_id.substring(0, 8)}...
                                    </div>
                                </div>
                            </Link>
                        </motion.div>

                        {/* Actions */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 }}
                            className="glass-card p-6 border border-slate-700/50"
                        >
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-700 pb-2">
                                Handlinger
                            </h3>

                            <div className="space-y-3">
                                <button className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl shadow-lg shadow-blue-500/20 transition-all font-medium flex items-center justify-center gap-2">
                                    Oppdater Status
                                </button>
                                <button className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition-all font-medium">
                                    Last ned PDF
                                </button>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </div>
    );
}
