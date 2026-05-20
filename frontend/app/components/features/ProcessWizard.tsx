"use client";
import React, { useState, useEffect, useCallback } from 'react';
import { fetchAPI } from '@/lib/api';

interface ProcessWizardProps {
    deviationId: string;
    onClose: () => void;
}

export default function ProcessWizard({ deviationId, onClose }: ProcessWizardProps) {
    const [process, setProcess] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [pedagogueHelp, setPedagogueHelp] = useState<string>("");

    // Form States
    const [analysisText, setAnalysisText] = useState("");
    const [measureText, setMeasureText] = useState("");

    // Define before usage to satisfy lint and TDZ
    const askPedagogue = async (step: string) => {
        try {
            const data = await fetchAPI(`/agent/processes/ai-help`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ step, context: "Internal Control" })
            });
            setPedagogueHelp(data.guidance);
        } catch (e) {
            console.error(e);
        }
    };

    const fetchProcess = useCallback(async () => {
        try {
            const data = await fetchAPI(`/agent/processes/${deviationId}`);
            setProcess(data);
            setLoading(false);

            // Auto-fetch help for current step
            if (data.status) askPedagogue(data.status);

        } catch (error) {
            console.error(error);
        }
    }, [deviationId]);

    useEffect(() => {
        fetchProcess();
    }, [fetchProcess]);

    

    const handleTransition = async (action: string, payload: Record<string, unknown> = {}) => {
        setLoading(true);
        try {
            const data = await fetchAPI(`/agent/processes/${deviationId}/next`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, data: payload })
            });
            setProcess(data);
            if (data.status) askPedagogue(data.status);
        } catch (e) {
            alert("Kunne ikke gå videre i prosessen.");
        }
        setLoading(false);
    };

    if (loading && !process) return <div className="p-4 bg-white rounded shadow">Laster prosessmotor...</div>;

    const currentStep = process?.status || "Opprettet";
    const history = process?.history || [];

    return (
        <div className="fixed inset-0 bg-overlay flex items-center justify-center z-50 p-4">
            <div className="bg-surface w-full max-w-5xl h-[80vh] rounded-xl shadow-2xl flex overflow-hidden border border-border">

                {/* LEFT: Process Steps & Forms */}
                <div className="flex-1 flex flex-col">
                    {/* Header */}
                    <div className="bg-surface border-b border-border p-6 flex justify-between items-center">
                        <div>
                            <h2 className="text-xl font-bold text-foreground">Internkontroll Prosess</h2>
                            <p className="text-muted text-sm">Avvik ID: {deviationId} • Status: <span className="text-amber-500 font-bold">{currentStep}</span></p>
                        </div>
                        <button onClick={onClose} className="text-muted hover:text-foreground transition-colors">
                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                        </button>
                    </div>

                    {/* Progress Bar */}
                    <div className="bg-background/50 p-4 border-b border-border">
                        <div className="flex justify-between max-w-2xl mx-auto">
                            {['Opprettet', 'Analyse', 'Tiltak', 'Kontroll', 'Lukket'].map((step, idx) => (
                                <div key={step} className={`flex flex-col items-center ${process.current_step_index >= idx ? 'text-primary' : 'text-muted'}`}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mb-1 
                                        ${process.current_step_index > idx ? 'bg-primary text-primary-foreground' :
                                            process.current_step_index === idx ? 'bg-primary/10 border-2 border-primary' : 'bg-muted/20'}`}>
                                        {idx + 1}
                                    </div>
                                    <span className="text-xs font-medium">{step}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Main Content Area */}
                    <div className="flex-1 p-8 overflow-y-auto bg-background">

                        {currentStep === "Opprettet" && (
                            <div className="text-center py-10">
                                <h3 className="text-2xl font-bold text-foreground mb-4">Start Behandling</h3>
                                <p className="text-muted mb-8 max-w-md mx-auto">
                                    Du er i ferd med å starte behandlingen av dette avviket. Prosessen vil lede deg gjennom årsaksanalyse, tiltak og verifisering.
                                </p>
                                <button
                                    onClick={() => handleTransition("start_analysis")}
                                    className="bg-primary text-primary-foreground px-8 py-3 rounded-lg font-bold hover:bg-primary/90 shadow-lg transition-transform hover:scale-105"
                                >
                                    Start Analyse
                                </button>
                            </div>
                        )}

                        {currentStep === "Analyse" && (
                            <div className="max-w-2xl mx-auto">
                                <h3 className="text-xl font-bold text-foreground mb-4">Steg 2: Årsaksanalyse</h3>
                                <div className="bg-surface p-6 rounded-lg shadow-sm border border-border mb-6">
                                    <label className="block font-medium text-foreground mb-2">Beskriv rotårsaken (Hvorfor skjedde dette?)</label>
                                    <textarea
                                        className="w-full h-32 p-3 bg-background border border-border text-foreground rounded focus:ring-2 focus:ring-primary outline-none"
                                        placeholder="F.eks. Manglende vedlikehold, feil bruk, eller systemfeil..."
                                        value={analysisText}
                                        onChange={(e) => setAnalysisText(e.target.value)}
                                    />
                                </div>
                                <div className="flex justify-end">
                                    <button
                                        onClick={() => handleTransition("submit_analysis", { root_cause: analysisText })}
                                        disabled={analysisText.length < 5}
                                        className="bg-primary text-primary-foreground px-6 py-2 rounded font-bold hover:bg-primary/90 disabled:opacity-50"
                                    >
                                        Lagre og Gå Videre →
                                    </button>
                                </div>
                            </div>
                        )}

                        {currentStep === "Tiltak" && (
                            <div className="max-w-2xl mx-auto">
                                <h3 className="text-xl font-bold text-foreground mb-4">Steg 3: Beslutt Tiltak</h3>
                                <div className="bg-surface p-6 rounded-lg shadow-sm border border-border mb-6">
                                    <label className="block font-medium text-foreground mb-2">Hvilke tiltak skal gjennomføres?</label>
                                    <textarea
                                        className="w-full h-32 p-3 bg-background border border-border text-foreground rounded focus:ring-2 focus:ring-primary outline-none"
                                        placeholder="Beskriv tiltaket (f.eks. Bestille service, Oppdatere rutine...)"
                                        value={measureText}
                                        onChange={(e) => setMeasureText(e.target.value)}
                                    />
                                </div>
                                <div className="flex justify-end">
                                    <button
                                        onClick={() => handleTransition("submit_measures", { measure: measureText })}
                                        disabled={measureText.length < 5}
                                        className="bg-primary text-primary-foreground px-6 py-2 rounded font-bold hover:bg-primary/90 disabled:opacity-50"
                                    >
                                        Iverksett Tiltak →
                                    </button>
                                </div>
                            </div>
                        )}

                        {currentStep === "Kontroll" && (
                            <div className="text-center py-10">
                                <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mx-auto mb-6">
                                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                </div>
                                <h3 className="text-2xl font-bold text-foreground mb-4">Klar for Verifisering</h3>
                                <p className="text-muted mb-8 max-w-md mx-auto">
                                    Tiltaket er registrert. Du må nå verifisere at tiltaket har fungert og at risikoen er redusert.
                                </p>
                                <button
                                    onClick={() => handleTransition("approve")}
                                    className="bg-green-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-green-700 shadow-lg"
                                >
                                    Godkjenn og Lukk Avvik
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT: AI Pedagogue Sidebar */}
                <div className="w-96 bg-primary/5 border-l border-border flex flex-col">
                    <div className="p-4 bg-primary/10 border-b border-border">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-surface border border-border rounded-full flex items-center justify-center shadow-sm text-2xl">
                                🤖
                            </div>
                            <div>
                                <h4 className="font-bold text-foreground">Din Pedagog</h4>
                                <p className="text-xs text-muted">AI-støttet veileder</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto space-y-4">
                        {pedagogueHelp && (
                            <div className="bg-surface p-4 rounded-lg shadow-sm border border-border animate-in fade-in slide-in-from-right-4">
                                <p className="text-sm font-bold text-primary mb-2">Veiledning:</p>
                                <div className="text-sm text-foreground whitespace-pre-wrap leading-relaxed prose prose-sm max-w-none">
                                    {pedagogueHelp}
                                </div>
                            </div>
                        )}

                        {/* Chat History would go here if we stored it */}
                    </div>

                    <div className="p-4 border-t border-border bg-surface">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="Spør pedagogen..."
                                className="flex-1 p-2 bg-background border border-border rounded text-sm focus:outline-none focus:border-primary text-foreground"
                                onKeyDown={async (e) => {
                                    if (e.key === 'Enter') {
                                        const input = e.currentTarget;
                                        const msg = input.value;
                                        if (!msg.trim()) return;

                                        input.value = ''; // clear
                                        setPedagogueHelp((prev) => prev + `\n\nDu: ${msg}\n...`); // optimistic UI

                                        try {
                                            const res = await fetchAPI('/agent/chat', {
                                                method: 'POST',
                                                body: JSON.stringify({
                                                    message: msg,
                                                    context: {
                                                        step: currentStep,
                                                        case: process // Pass full case context
                                                    }
                                                })
                                            });
                                            setPedagogueHelp(res.response);
                                        } catch (err) {
                                            console.error(err);
                                        }
                                    }
                                }}
                            />
                        </div>
                        <p className="text-[10px] text-center text-muted mt-2">
                            Pedagogen kjenner saken din. Spør om hva som helst.
                        </p>
                    </div>
                </div>

            </div>
        </div>
    );
}
