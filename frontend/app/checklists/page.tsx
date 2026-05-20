"use client";

import React, { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { internalControlService, InternalControlCase, ChecklistItem } from '@/lib/domains/hms/internalControlService';
import { CheckCircle, ClipboardList, AlertTriangle, Building, User } from 'lucide-react';
import Link from 'next/link';

export default function ChecklistsPage() {
    return (
        <Suspense fallback={<div className="p-8 text-center text-slate-500">Laster...</div>}>
            <ChecklistsContent />
        </Suspense>
    );
}

function ChecklistsContent() {
    const [cases, setCases] = useState<InternalControlCase[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeCase, setActiveCase] = useState<InternalControlCase | null>(null);
    const [responses, setResponses] = useState<Record<string, boolean>>({});
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    const searchParams = useSearchParams();
    const caseIdParam = searchParams.get('case_id');
    const priorityParam = searchParams.get('priority');

    useEffect(() => {
        loadCases();
    }, [priorityParam]);

    useEffect(() => {
        if (cases.length > 0 && caseIdParam) {
            const target = cases.find(c => c.case_id === caseIdParam);
            if (target) setActiveCase(target);
        }
    }, [cases, caseIdParam]);

    const loadCases = async () => {
        // Fetch open cases, optionally filtered by priority (e.g. ?priority=critical)
        const data = await internalControlService.getPropertyCases(undefined, 'open', priorityParam ?? undefined);
        setCases(data);
        setLoading(false);
    };

    const handleStartChecklist = (c: InternalControlCase) => {
        setActiveCase(c);
        setResponses({});
    };

    const toggleResponse = (index: number) => {
        setResponses(prev => ({
            ...prev,
            [index]: !prev[index]
        }));
    };

    const handleSubmit = async () => {
        if (!activeCase) return;
        setSubmitError(null);
        setSubmitting(true);
        try {
            const responsesForApi: Record<string, boolean> = {};
            Object.entries(responses).forEach(([k, v]) => {
                responsesForApi[String(k)] = v;
            });
            await internalControlService.completeChecklist(
                activeCase.case_id,
                responsesForApi,
                undefined
            );
            setActiveCase(null);
            await loadCases();
        } catch (e) {
            setSubmitError(e instanceof Error ? e.message : "Kunne ikke lagre sjekkliste.");
        } finally {
            setSubmitting(false);
        }
    };

    const getResponsibilityBadge = (resp: string) => {
        switch (resp) {
            case 'TENANT':
                return <span className="flex items-center gap-1 text-xs font-bold text-blue-300 bg-blue-500/20 border border-blue-500/30 px-2 py-1 rounded"><User size={12} /> LEIETAKER</span>;
            case 'LANDLORD':
                return <span className="flex items-center gap-1 text-xs font-bold text-orange-300 bg-orange-500/20 border border-orange-500/30 px-2 py-1 rounded"><Building size={12} /> GÅRDEIER</span>;
            case 'SHARED':
                return <span className="flex items-center gap-1 text-xs font-bold text-purple-300 bg-purple-500/20 border border-purple-500/30 px-2 py-1 rounded">FELLES</span>;
            default:
                return <span className="text-xs font-bold text-slate-400 bg-slate-500/20 border border-slate-500/30 px-2 py-1 rounded">{resp}</span>;
        }
    }

    if (loading) return <div className="p-8 text-center text-slate-500">Laster internkontroll...</div>;

    return (
        <div className="min-h-screen p-8 pt-24">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-start mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Mine Sjekklister</h1>
                        <p className="text-slate-400">Dine planlagte internkontroll-oppgaver for denne måneden.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link
                            href="/checklists/templates"
                            className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1"
                        >
                            Mine maler
                        </Link>
                        <Link
                            href="/activities/hub"
                            className="text-sm font-medium text-primary hover:text-primary/80 flex items-center gap-1"
                        >
                            Aktivitetshub
                        </Link>
                    </div>
                </div>

                {activeCase ? (
                    /* Active Case View */
                    <div className="glass-card max-w-3xl mx-auto overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
                        <div className="bg-white/5 p-6 border-b border-white/10 flex justify-between items-start">
                            <div>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${activeCase.priority === 'high' ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'}`}>
                                        {activeCase.priority === 'high' ? 'Høy' : activeCase.priority === 'medium' ? 'Middels' : activeCase.priority === 'low' ? 'Lav' : activeCase.priority}
                                    </span>
                                    <span className="text-slate-400 text-sm">{activeCase.case_type}</span>
                                </div>
                                <h2 className="text-2xl font-bold text-white">{activeCase.title}</h2>
                                <p className="text-slate-300 mt-1 whitespace-pre-wrap">{activeCase.description?.split('\n\n')[0]}</p>
                            </div>
                            <button
                                onClick={() => setActiveCase(null)}
                                className="text-slate-400 hover:text-white transition-colors"
                            >
                                Lukk
                            </button>
                        </div>

                        {/* Legal References */}
                        {activeCase.process_data?.legal_references && activeCase.process_data.legal_references.length > 0 && (
                            <div className="px-6 py-4 bg-blue-900/10 border-b border-white/5">
                                <h3 className="text-xs font-bold text-blue-300 uppercase tracking-wider mb-2 flex items-center gap-1">
                                    <span className="text-lg">⚖️</span> Hjemmel i lovverk
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {activeCase.process_data.legal_references.map((ref, i) => (
                                        <a
                                            key={i}
                                            href={ref.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 text-xs rounded border border-blue-500/30 flex items-center gap-1 transition-colors"
                                        >
                                            {ref.title} <span className="text-[10px] opacity-70">↗</span>
                                        </a>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="p-6 space-y-4">
                            {!activeCase.process_data?.checklist || activeCase.process_data.checklist.length === 0 ? (
                                <div className="text-center p-8 text-slate-500">Inneholder ingen sjekkpunkter. Se beskrivelse.</div>
                            ) : (
                                activeCase.process_data.checklist.map((item, index) => (
                                    <div
                                        key={index}
                                        onClick={() => toggleResponse(index)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-all flex items-start justify-between gap-4
                                            ${responses[index]
                                                ? 'bg-green-500/10 border-green-500/50'
                                                : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20'}`}
                                    >
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                {getResponsibilityBadge(item.responsibility)}
                                                {item.criticality === 'CRITICAL' && (
                                                    <span className="text-xs font-bold text-red-300 bg-red-900/50 border border-red-500/30 px-2 py-1 rounded flex items-center gap-1">
                                                        <AlertTriangle size={12} /> KRITISK
                                                    </span>
                                                )}
                                            </div>
                                            <span className={`font-medium block ${responses[index] ? 'text-green-400' : 'text-slate-200'}`}>
                                                {item.task}
                                            </span>
                                        </div>

                                        <div className={`mt-1 w-6 h-6 min-w-6 rounded-full border-2 flex items-center justify-center transition-colors
                                             ${responses[index] ? 'bg-green-500 border-green-500' : 'border-slate-600'}`}>
                                            {responses[index] && <CheckCircle size={16} className="text-white" />}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="p-6 bg-white/5 border-t border-white/10 flex flex-col gap-3">
                            {submitError && (
                                <p className="text-red-400 text-sm">{submitError}</p>
                            )}
                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setActiveCase(null)}
                                    disabled={submitting}
                                    className="px-4 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
                                >
                                    Avbryt
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                    className="enterprise-button disabled:opacity-50"
                                >
                                    {submitting ? "Lagrer..." : "Fullfør Sjekkliste"}
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Cases Grid */
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {cases.map(c => (
                            <div key={c.case_id} className="glass-card p-6 flex flex-col h-full group hover:border-blue-500/30">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                        <ClipboardList size={24} />
                                    </div>
                                    <span className={`px-2 py-1 text-xs font-bold uppercase rounded-md border ${c.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-slate-500/10 text-slate-400 border-slate-500/20'}`}>
                                        {c.priority === 'high' ? 'Høy' : c.priority === 'medium' ? 'Middels' : c.priority === 'low' ? 'Lav' : c.priority}
                                    </span>
                                </div>

                                <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">{c.title}</h3>
                                <p className="text-sm text-slate-400 mb-6 grow line-clamp-3">{c.description}</p>

                                {c.process_data?.risk_class && (
                                    <div className="mb-4">
                                        <span className="text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2 py-1 rounded">
                                            RKL {c.process_data.risk_class}
                                        </span>
                                    </div>
                                )}

                                <button
                                    onClick={() => handleStartChecklist(c)}
                                    className="w-full py-2 bg-slate-800 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors mt-auto border border-white/10"
                                >
                                    Start Sjekk
                                </button>
                            </div>
                        ))}

                        {/* Empty State */}
                        {cases.length === 0 && (
                            <div className="col-span-full p-12 rounded-xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center text-center text-slate-500">
                                <CheckCircle size={48} className="mb-4 opacity-50" />
                                <h3 className="font-semibold text-xl text-slate-300">Alt ser bra ut!</h3>
                                <p className="text-slate-500 mt-2">Du har ingen forfalte sjekkrunder. Ta en kaffe! ☕️</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
