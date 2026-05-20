"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchAPI } from '@/lib/api';
import ProcessWizard from '@/app/components/features/ProcessWizard';
import { ArrowLeft, Calendar, CheckSquare, AlertTriangle, Building, User } from 'lucide-react';

export default function CaseDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [caseData, setCaseData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [showWizard, setShowWizard] = useState(false);

    useEffect(() => {
        if (params.id) loadCase();
    }, [params.id]);

    const loadCase = async () => {
        try {
            const data = await fetchAPI(`/internal-control/cases/${params.id}`);
            setCaseData(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-12 text-center text-slate-500">Laster sak...</div>;
    if (!caseData) return <div className="p-12 text-center text-red-500">Fant ikke saken.</div>;

    const checklist = caseData.process_data?.checklist || [];

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <button onClick={() => router.back()} className="flex items-center text-slate-500 hover:text-slate-800 mb-6 transition-colors">
                <ArrowLeft size={20} className="mr-2" />
                Tilbake til Innboks
            </button>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left: Case Info */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${caseData.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                                        {caseData.priority}
                                    </span>
                                    <span className="text-slate-400 text-sm flex items-center gap-1">
                                        <Calendar size={14} /> Frist: {new Date(caseData.due_date).toLocaleDateString()}
                                    </span>
                                </div>
                                <h1 className="text-3xl font-bold text-slate-900 mb-2">{caseData.title}</h1>
                                <p className="text-slate-600 text-lg leading-relaxed whitespace-pre-wrap">
                                    {caseData.description?.split('\n\n')[0]}
                                </p>
                            </div>
                        </div>

                        {/* Checklist */}
                        <div className="border-t border-slate-100 pt-6">
                            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <CheckSquare size={16} /> Sjekkpunkter
                            </h3>
                            <div className="space-y-3">
                                {checklist.map((item: any, i: number) => (
                                    <div key={i} className="flex items-start gap-4 p-4 bg-slate-50 rounded-lg">
                                        <div className="mt-1">
                                            {item.responsibility === 'TENANT' ?
                                                <span title="Leietaker ansvar" className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 rounded text-xs font-bold"><User size={14} /></span> :
                                                <span title="Gårdeier ansvar" className="flex items-center justify-center w-6 h-6 bg-orange-100 text-orange-600 rounded text-xs font-bold"><Building size={14} /></span>
                                            }
                                        </div>
                                        <div className="flex-1">
                                            <p className="font-medium text-slate-800">{item.task}</p>
                                            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                                                {item.criticality === 'CRITICAL' && <span className="text-red-600 font-bold flex items-center gap-1"><AlertTriangle size={10} /> KRITISK</span>}
                                                {item.action && <span className="text-blue-600">Handling: {item.action}</span>}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Actions */}
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow-lg border border-blue-100 p-6 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-bl-full -mr-10 -mt-10" />

                        <h3 className="text-lg font-bold text-slate-900 mb-2">Behandling</h3>
                        <p className="text-sm text-slate-500 mb-6">
                            Start prosessmotoren for å behandle avviket eller utføre kontrollen. AI-veilederen vil bistå deg.
                        </p>

                        <button
                            onClick={() => setShowWizard(true)}
                            className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-lg shadow-blue-500/30 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2"
                        >
                            <span>🚀 Start Prosess</span>
                        </button>

                        <div className="mt-6 pt-6 border-t border-slate-100">
                            <div className="flex justify-between items-center text-sm text-slate-500">
                                <span>Status:</span>
                                <span className={`font-bold ${caseData.status === 'open' ? 'text-green-600' : 'text-slate-400'}`}>
                                    {caseData.status === 'open' ? 'Åpen' : 'Lukket'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {showWizard && (
                <ProcessWizard
                    deviationId={caseData.risk_assessment_id || caseData.case_id} // Fallback to case_id if not risk
                    onClose={() => setShowWizard(false)}
                />
            )}
        </div>
    );
}
