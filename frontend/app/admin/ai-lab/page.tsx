"use client";

import { useEffect, useState } from "react";
import {
    Activity,
    CheckCircle2,
    History,
    Info,
    Brain,
    Database,
    Wrench,
    Zap
} from "lucide-react";
import { getAiVitals, getScenarios, AIVitals, Scenario } from "@/lib/api/transparencyApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const TOOL_TYPE_COLORS: Record<string, string> = {
    "Dataanalyse": "bg-blue-50 text-blue-700 border-blue-200",
    "Oppslag": "bg-purple-50 text-purple-700 border-purple-200",
    "Dokumentsøk": "bg-green-50 text-green-700 border-green-200",
    "Juridisk": "bg-amber-50 text-amber-700 border-amber-200",
    "Risikovurdering": "bg-red-50 text-red-700 border-red-200",
    "Handling": "bg-slate-50 text-slate-700 border-slate-200",
};

export default function AiLabPage() {
    const [vitals, setVitals] = useState<AIVitals | null>(null);
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [vitalsData, scenariosData] = await Promise.all([
                    getAiVitals(),
                    getScenarios()
                ]);
                setVitals(vitalsData);
                setScenarios(scenariosData.scenarios);
            } catch (error) {
                console.error("Failed to load AI Lab data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    if (loading) {
        return <div className="p-8 animate-pulse text-muted-foreground">Laster KI-Lab...</div>;
    }

    return (
        <div className="p-8 space-y-8 max-w-400 mx-auto">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">KI-Lab & Transparens</h1>
                <p className="text-muted-foreground max-w-2xl">
                    Se bak kulissene på BEFS intelligens-systemer. Her kan du se hvilke modeller og verktøy
                    som faktisk brukes, og hvordan de samarbeider.
                </p>
            </div>

            {/* Model & Architecture Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="border-purple-100 bg-purple-50/10">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium">Språkmodell (LLM)</CardTitle>
                        <Brain className="h-4 w-4 text-purple-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-purple-900">{vitals?.models.primary_llm.name}</div>
                        <p className="text-xs text-muted-foreground mt-1">Provider: {vitals?.models.primary_llm.provider}</p>
                        <Badge className="mt-4 bg-purple-100 text-purple-700 hover:bg-purple-200 border-none text-xs">
                            {vitals?.models.primary_llm.role}
                        </Badge>
                    </CardContent>
                </Card>

                <Card className="border-blue-100 bg-blue-50/10">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium">Verktøy (LangChain Tools)</CardTitle>
                        <Wrench className="h-4 w-4 text-blue-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-900">{vitals?.models.tools.length} verktøy</div>
                        <p className="text-xs text-muted-foreground mt-1">LLM-en velger selv hvilke som trengs per spørsmål.</p>
                        <div className="flex flex-wrap gap-1 mt-4">
                            {vitals?.models.tools.map(t => (
                                <Badge key={t.name} variant="outline" className={`text-[10px] ${TOOL_TYPE_COLORS[t.type] || ''}`}>
                                    {t.type}
                                </Badge>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-green-100 bg-green-50/10">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle className="text-sm font-medium">Datahenting (RAG + SQL)</CardTitle>
                        <Database className="h-4 w-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-900">{vitals?.models.data_retrieval.search_type}</div>
                        <p className="text-xs text-muted-foreground mt-1">Vektordatabase: {vitals?.models.data_retrieval.vector_db}</p>
                        <div className="flex items-center gap-2 mt-4 text-xs text-green-700">
                            <CheckCircle2 size={14} />
                            Status: {vitals?.models.data_retrieval.status}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Performance */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Activity className="h-5 w-5 text-blue-500" />
                                Ytelsesmetrikker (Siste 24t)
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-slate-50 rounded-lg">
                                    <p className="text-xs text-muted-foreground uppercase font-semibold">Totale forespørsler</p>
                                    <p className="text-2xl font-bold">{vitals?.metrics.last_24h.total_requests}</p>
                                </div>
                                <div className="p-4 bg-slate-50 rounded-lg">
                                    <p className="text-xs text-muted-foreground uppercase font-semibold">Gjennomsnittlig svartid</p>
                                    <p className="text-2xl font-bold">{vitals?.metrics.last_24h.avg_response_time_ms} ms</p>
                                </div>
                                <div className="p-4 bg-slate-50 rounded-lg">
                                    <p className="text-xs text-muted-foreground uppercase font-semibold">Feilrate</p>
                                    <p className={`text-2xl font-bold ${(vitals?.metrics.last_24h.error_rate_percent || 0) > 5 ? 'text-red-500' : 'text-green-500'}`}>
                                        {vitals?.metrics.last_24h.error_rate_percent}%
                                    </p>
                                </div>
                                <div className="p-4 bg-slate-50 rounded-lg">
                                    <p className="text-xs text-muted-foreground uppercase font-semibold">Systemhelse</p>
                                    <Badge variant={vitals?.metrics.last_24h.system_health === "Healthy" ? "default" : "destructive"}>
                                        {vitals?.metrics.last_24h.system_health}
                                    </Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Info className="h-5 w-5 text-amber-500" />
                                Agentarkitektur
                            </CardTitle>
                            <CardDescription>
                                KI-Kollega bruker en ReAct-løkke (Reason + Act). LLM-en veksler mellom å tenke og å kalle verktøy inntil den har nok informasjon til å svare.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2 text-sm">
                                {[
                                    { step: "1. Guardian", desc: "Blokkerer spørsmål med sensitiv PII (fødselsnummer, kontonummer)" },
                                    { step: "2. Agent (LLM)", desc: "Mottar spørsmål + samtalehistorikk, velger verktøy" },
                                    { step: "3. Tools", desc: "Utfører valgte verktøy mot database, dokumenter eller Lovdata" },
                                    { step: "4. Agent (LLM)", desc: "Tolker verktøyresultat, formulerer svar med entity-lenker" },
                                ].map(({ step, desc }) => (
                                    <div key={step} className="flex gap-3 p-3 border rounded-lg">
                                        <Zap className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                                        <div>
                                            <span className="font-semibold text-foreground">{step}: </span>
                                            <span className="text-muted-foreground">{desc}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Tools list */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Wrench className="h-5 w-5 text-slate-500" />
                                Tilgjengelige verktøy
                            </CardTitle>
                            <CardDescription>LLM-en velger selv hvilke verktøy som trengs for å besvare hvert spørsmål.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {vitals?.models.tools.map(t => (
                                <div key={t.name} className="flex gap-3 items-start p-3 border rounded-lg hover:bg-slate-50 transition-colors">
                                    <Badge variant="outline" className={`text-[10px] shrink-0 mt-0.5 ${TOOL_TYPE_COLORS[t.type] || ''}`}>
                                        {t.type}
                                    </Badge>
                                    <div>
                                        <p className="font-semibold text-sm font-mono">{t.name}</p>
                                        <p className="text-xs text-muted-foreground">{t.description}</p>
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Scenarios */}
            <div>
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <History className="h-5 w-5 text-blue-500" />
                    Eksempelscenarier
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {scenarios.map(scen => (
                        <Card key={scen.id} className="relative overflow-hidden group">
                            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 group-hover:w-2 transition-all" />
                            <CardHeader>
                                <CardTitle className="text-md">{scen.title}</CardTitle>
                                <CardDescription>{scen.description}</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4 text-xs">
                                    <div className="space-y-1">
                                        <p className="font-bold text-purple-600">LLM-rolle</p>
                                        <p className="text-muted-foreground">{scen.llm_role}</p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="font-bold text-blue-600">Minnerolle</p>
                                        <p className="text-muted-foreground">{scen.ml_role}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </div>
    );
}
