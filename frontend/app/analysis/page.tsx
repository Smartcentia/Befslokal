"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Map,
    FileText,
    AlertTriangle,
    ShieldAlert,
    Wrench,
    FileSearch,
    LayoutDashboard,
    Search,
    Sparkles,
    ArrowRight
} from 'lucide-react';
import Accordion from '../components/ui/Accordion';
import AnalysisResult from '../components/features/AnalysisResult';
import { agentService } from '../../lib/domains/innsikt/agentService';


// Analysis Categories and Modules Configuration
const analysisCategories = [
    {
        id: 'geo',
        title: 'Geografiske analyser',
        icon: <Map size={24} />,
        modules: [
            { id: 'geo-risk', title: 'Eiendomsrisiko vs. geografi', description: 'Heatmap av risiko per bydel' },
            { id: 'geo-cluster', title: 'Geografisk klynging', description: 'Klynging av avvik og risiko' },
            { id: 'geo-prox', title: 'Nærhetsanalyse', description: 'Analyse av avstand til nøkkeltjenester' },
            { id: 'geo-geology', title: 'Geologi og risiko', description: 'Korrelasjon mellom grunnforhold og skade' },
        ]
    },
    {
        id: 'contracts',
        title: 'Kontraktsanalyser',
        icon: <FileText size={24} />,
        modules: [
            { id: 'con-finance', title: 'Økonomi vs. Risiko', description: 'Sammenheng mellom leiepris og risikoscore' },
            { id: 'con-length', title: 'Kontraktslengde', description: 'Analyse av avvikende løpetider' },
            { id: 'con-bench', title: 'Markedspris Benchmarking', description: 'Sammenligning mot markedsdata' },
            { id: 'con-abnormal', title: 'Abnormale kontrakter', description: 'AI-deteksjon av uvanlige klausuler' },
        ]
    },
    {
        id: 'deviations',
        title: 'Avviksanalyser',
        icon: <AlertTriangle size={24} />,
        modules: [
            { id: 'dev-trends', title: 'Trendanalyse', description: 'Utvikling av avvik over tid' },
            { id: 'dev-response', title: 'Responstid', description: 'Gjennomsnittlig tid til lukking' },
            { id: 'dev-recurring', title: 'Gjentakende avvik', description: 'Identifiser systematiske problemer' },
        ]
    },
    {
        id: 'risk',
        title: 'Risikoanalyser',
        icon: <ShieldAlert size={24} />,
        modules: [
            { id: 'risk-pred', title: 'Prediktiv Risikomodell', description: 'Framskriving av eiendomsrisiko' },
            { id: 'risk-multi', title: 'Multifaktor Analyse', description: 'Kombinert analyse av teknisk og økonomisk risiko' },
            { id: 'risk-kpi', title: 'KPI Anomalier', description: 'Deteksjon av avvik i nøkkeltall' },
        ]
    },
    {
        id: 'maintenance',
        title: 'Vedlikeholdsanalyser',
        icon: <Wrench size={24} />,
        modules: [
            { id: 'maint-cost', title: 'Kostnadsanalyse', description: 'Analyse av serviceavtaler' },
            { id: 'maint-plan', title: 'Planlagt vs. Utført', description: 'Effektivitet i vedlikeholdsarbeid' },
            { id: 'maint-check', title: 'Sjekklistestatus', description: 'Etterlevelse av rutiner' },
        ]
    },
    {
        id: 'pdf',
        title: 'PDF-baserte analyser',
        icon: <FileSearch size={24} />,
        modules: [
            { id: 'pdf-mining', title: 'Klausul-mining', description: 'Masseanalyse av skannede kontrakter' },
            { id: 'pdf-cluster', title: 'Dokumentklynging', description: 'Automatisk sortering basert på innhold' },
            { id: 'pdf-meta', title: 'Metadata-analyse', description: 'Kvalitetssjekk av arkivdata' },
        ]
    },
    {
        id: 'dashboard',
        title: 'Dashboards',
        icon: <LayoutDashboard size={24} />,
        modules: [
            { id: 'dash-ops', title: 'Driftsdashboard', description: 'Daglig operativ oversikt' },
            { id: 'dash-risk', title: 'Risikodashboard', description: 'Ledelsesrapportering på risiko' },
            { id: 'dash-env', title: 'Miljø & Geologi', description: 'Oversikt for ytre miljø' },
        ]
    },
];

export default function AnalysisPage() {
    const [filter, setFilter] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<{ title: string, content: string } | null>(null);

    const handleAnalyze = async (module: any) => {
        setIsLoading(true);
        try {
            // Contextual Prompt for the Agent
            const prompt = `Vennligst utfør analysen: "${module.title}". Beskrivelse: ${module.description}. Hvis relevant, generer en Python-plot av dataene.`;

            const response = await agentService.chat([{ role: 'user', content: prompt }]);

            setResult({
                title: module.title,
                content: response.response // Accessing nested response object from backend
            });
        } catch (error) {
            console.error("Analysis failed", error);
            setResult({
                title: "Feil",
                content: "Kunne ikke utføre analysen. Vennligst prøv igjen."
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleAgentClick = async () => {
        setIsLoading(true);
        try {
            const response = await agentService.chat([{ role: 'user', content: "Hei! Hva kan du hjelpe meg med av analyser?" }]);
            setResult({
                title: "KI Assistent",
                content: response.response
            });
        } catch (e) {
            setResult({ title: "Feil", content: "Kunne ikke koble til agenten." });
        } finally {
            setIsLoading(false);
        }
    };


    const filteredCategories = analysisCategories.filter(cat => {
        const matchTitle = cat.title.toLowerCase().includes(filter.toLowerCase());
        const matchModule = cat.modules.some(mod =>
            mod.title.toLowerCase().includes(filter.toLowerCase()) ||
            mod.description.toLowerCase().includes(filter.toLowerCase())
        );
        return matchTitle || matchModule;
    });

    return (
        <div className="min-h-screen bg-background p-8 pb-32 text-foreground">
            {/* Page Header */}
            <div className="max-w-5xl mx-auto mb-12">
                <motion.div
                    initial={{ opacity: 1, y: 0 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35 }}
                >
                    <h1 className="mb-4 bg-gradient-to-r from-primary via-indigo-400 to-purple-500 bg-clip-text text-4xl font-bold tracking-tight text-transparent">
                        Analyser
                    </h1>
                    <p className="max-w-2xl text-xl text-muted">
                        Avanserte analyser og innsikter basert på alle data i systemet.
                        Utforsk trender, risiko og sammenhenger i porteføljen.
                    </p>
                </motion.div>

                {/* Filter Bar */}
                <motion.div
                    initial={{ opacity: 1, y: 0 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05, duration: 0.35 }}
                    className="mt-8 relative"
                >
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Search className="h-5 w-5 text-muted" />
                    </div>
                    <input
                        type="text"
                        placeholder="Filtrer analyser (f.eks. 'risiko', 'geografi', 'kontrakt')..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="w-full rounded-xl border border-border bg-card py-4 pr-4 pl-12 text-foreground shadow-lg placeholder:text-muted transition-all focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary/40"
                    />
                </motion.div>
            </div>

            {/* Accordion List */}
            <div className="max-w-5xl mx-auto space-y-4">
                {filteredCategories.map((category, index) => (
                    <motion.div
                        key={category.id}
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.02, duration: 0.25 }}
                    >
                        <Accordion
                            title={category.title}
                            icon={category.icon}
                            defaultOpen={index === 0 && filter === ''} // Open first by default if not filtering
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {category.modules.map((module) => (
                                    <button
                                        key={module.id}
                                        onClick={() => handleAnalyze(module)}
                                        disabled={isLoading}
                                        className="group relative flex flex-col items-start overflow-hidden rounded-lg border border-border bg-surface/60 p-4 text-left transition-all hover:border-primary/35 hover:bg-surface disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        <div className="mb-3 rounded-lg bg-primary/10 p-2 transition-colors group-hover:bg-primary/20">
                                            <Sparkles className="h-5 w-5 text-primary" />
                                        </div>
                                        <h3 className="mb-1 text-sm font-semibold text-foreground transition-colors group-hover:text-primary">
                                            {module.title}
                                        </h3>
                                        <p className="mb-4 line-clamp-2 text-xs text-muted">
                                            {module.description}
                                        </p>
                                        <div className="mt-auto flex translate-y-2 transform items-center text-xs font-medium text-primary opacity-0 transition-all group-hover:translate-y-0 group-hover:opacity-100">
                                            Gå til analyse <ArrowRight className="w-3 h-3 ml-1" />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </Accordion>
                    </motion.div>
                ))}

                {filteredCategories.length === 0 && (
                    <div className="py-12 text-center text-muted">
                        Ingen analyser funnet for "{filter}"
                    </div>
                )}
            </div>

            {/* AI Result Modal */}
            <AnimatePresence>
                {result && (
                    <AnalysisResult
                        title={result.title}
                        content={result.content}
                        onClose={() => setResult(null)}
                    />
                )}
            </AnimatePresence>

            {/* Loading Indicator */}
            {isLoading && (
                <div className="fixed inset-0 z-60 flex items-center justify-center bg-overlay/80 backdrop-blur-sm">
                    <div className="flex flex-col items-center gap-4">
                        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
                        <p className="animate-pulse font-medium text-foreground">Analyserer...</p>
                    </div>
                </div>
            )}

            {/* Floating AI Action Button */}
            <motion.button
                onClick={handleAgentClick}
                initial={{ scale: 1 }}
                animate={{ scale: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="fixed bottom-8 right-8 z-50 flex items-center gap-3 rounded-full border border-border bg-gradient-to-r from-primary to-indigo-600 px-6 py-4 text-primary-foreground shadow-xl shadow-primary/25 transition-all hover:shadow-primary/40"
            >
                <Sparkles className="w-6 h-6" />
                <span className="font-semibold">Din KI assistent</span>
            </motion.button>
        </div>
    );
}
