"use client";

import React, { useEffect, useState } from "react";
import { glossaryApi, GlossaryTerm } from "@/lib/api/glossaryApi";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Code, FileText, Database } from "lucide-react";

export default function GlossaryComponent() {
    const [terms, setTerms] = useState<GlossaryTerm[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedTerm, setSelectedTerm] = useState<GlossaryTerm | null>(null);

    useEffect(() => {
        const fetchTerms = async () => {
            try {
                const data = await glossaryApi.getTerms();
                // Sort alphabetically
                data.sort((a, b) => a.term.localeCompare(b.term));
                setTerms(data);
                if (data.length > 0) {
                    setSelectedTerm(data[0]);
                }
            } catch (error) {
                console.error("Failed to fetch glossary terms:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchTerms();
    }, []);

    const filteredTerms = terms.filter((t) =>
        t.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.definition.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex flex-col h-full">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-1">Begrepskatalog</h2>
                <p className="text-gray-600 text-sm">
                    Oversikt over definisjoner og hvor de brukes i systemet (kode, dokumentasjon, data).
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[600px]">
                {/* Term List */}
                <Card className="md:col-span-1 flex flex-col h-full">
                    <CardHeader className="pb-2">
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                            <input
                                type="search"
                                placeholder="Søk etter begrep..."
                                className="pl-8 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                value={searchQuery}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                            />
                        </div>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-hidden p-0">
                        <div className="h-full overflow-y-auto">
                            <div className="flex flex-col p-2">
                                {loading ? (
                                    <div className="p-4 text-center text-gray-500">Laster begreper...</div>
                                ) : filteredTerms.length === 0 ? (
                                    <div className="p-4 text-center text-gray-500">Ingen treff</div>
                                ) : (
                                    filteredTerms.map((term) => (
                                        <button
                                            key={term.term}
                                            onClick={() => setSelectedTerm(term)}
                                            className={`text-left px-4 py-3 rounded-md transition-colors ${selectedTerm?.term === term.term
                                                    ? "bg-blue-50 text-blue-700 font-medium"
                                                    : "hover:bg-gray-100 text-gray-700"
                                                }`}
                                        >
                                            {term.term}
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Term Detail */}
                <Card className="md:col-span-2 h-full flex flex-col overflow-hidden">
                    {selectedTerm ? (
                        <>
                            <CardHeader className="pb-4 border-b">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <CardTitle className="text-2xl mb-2">{selectedTerm.term}</CardTitle>
                                        <CardDescription className="text-base text-gray-700">
                                            {selectedTerm.definition}
                                        </CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-hidden p-0">
                                <div className="h-full overflow-y-auto p-6">
                                    <h3 className="font-semibold text-lg mb-4 flex items-center">
                                        <Code className="mr-2 h-5 w-5 text-blue-600" />
                                        Forekomster i Systemet ({selectedTerm.usage?.length || 0})
                                    </h3>

                                    {!selectedTerm.usage || selectedTerm.usage.length === 0 ? (
                                        <div className="text-gray-500 italic bg-gray-50 p-4 rounded-md">
                                            Ingen automatiske koblinger funnet i koden eller dokumentasjonen.
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {selectedTerm.usage.map((usage, idx) => (
                                                <div key={idx} className="bg-slate-50 border rounded-lg p-3 hover:bg-slate-100 transition-colors">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <div className="flex items-center gap-2">
                                                            {usage.file.endsWith('.md') ? (
                                                                <FileText className="h-4 w-4 text-orange-500" />
                                                            ) : (
                                                                <Code className="h-4 w-4 text-blue-500" />
                                                            )}
                                                            <span className="font-mono text-sm font-medium text-slate-800">
                                                                {usage.file}:{usage.line}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="text-xs text-gray-500 font-mono bg-white p-2 rounded border border-slate-200 overflow-x-auto">
                                                        {usage.context}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400">
                            <Database className="h-16 w-16 mb-4 opacity-20" />
                            <p>Velg et begrep fra listen for å se detaljer</p>
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
