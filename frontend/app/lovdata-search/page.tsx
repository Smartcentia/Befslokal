"use client";

import React, { useState } from 'react';
import { fetchAPI } from '@/lib/api';
import { Search, Gavel, FileText, ExternalLink, Loader2 } from 'lucide-react';

export default function LovdataSearchPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        try {
            const data = await fetchAPI(`/external/fetch-lovdata?query=${encodeURIComponent(query)}`, {
                method: 'POST'
            });
            // Search results might be in a specific field depending on Lovdata API
            setResults(data.results || data.items || []);
        } catch (err: any) {
            console.error("Lovdata search failed", err);
            setError("Kunne ikke utføre søk mot Lovdata. Sjekk integrasjonsstatus.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground">
            <div className="max-w-5xl mx-auto px-6 pt-32 pb-20">
                {/* Header Section */}
                <div className="flex items-center gap-4 mb-12">
                    <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center text-primary border border-primary/20 shadow-lg shadow-primary/10">
                        <Gavel size={32} />
                    </div>
                    <div>
                        <h1 className="text-4xl font-bold text-foreground tracking-tight">Lovdata Søk</h1>
                        <p className="text-muted mt-2 text-lg">Finn lover, forskrifter og rettsinformasjon direkte i systemet.</p>
                    </div>
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="relative mb-12 group">
                    <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                        <Search className="h-6 w-6 text-muted group-focus-within:text-primary transition-colors" />
                    </div>
                    <input
                        type="text"
                        className="block w-full pl-16 pr-32 py-6 bg-surface border border-border rounded-3xl text-xl text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-2xl backdrop-blur-md"
                        placeholder="Søk etter f.eks. 'plan- og bygningsloven' eller 'leieavtale'..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="absolute right-3 top-3 bottom-3 px-8 bg-primary hover:opacity-90 text-primary-foreground font-bold rounded-2xl transition-all flex items-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-50"
                    >
                        {loading ? <Loader2 className="animate-spin" size={20} /> : "Søk"}
                    </button>
                </form>

                {error && (
                    <div className="bg-danger/10 border border-danger/20 text-danger p-6 rounded-2xl mb-8 flex items-center gap-4">
                        <div className="w-12 h-12 bg-danger/20 rounded-full flex items-center justify-center flex-shrink-0">
                            <Gavel size={24} />
                        </div>
                        <p className="font-medium">{error}</p>
                    </div>
                )}

                {/* Results Section */}
                <div className="space-y-4">
                    {results.length > 0 ? (
                        results.map((item, index) => (
                            <div
                                key={index}
                                className="glass-card p-6 hover:border-primary/30 hover:bg-surface/50 transition-all group"
                            >
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <FileText size={16} className="text-primary" />
                                            <span className="text-xs font-bold text-primary uppercase tracking-widest">{item.type || 'Dokument'}</span>
                                        </div>
                                        <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors mb-2">
                                            {item.title || item.name || 'Uten tittel'}
                                        </h3>
                                        <p className="text-muted line-clamp-2 text-sm leading-relaxed">
                                            {item.summary || item.snippet || 'Ingen beskrivelse tilgjengelig.'}
                                        </p>
                                    </div>
                                    <a
                                        href={item.url || `https://lovdata.no/dokument/${item.id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-3 bg-surface hover:bg-primary text-muted hover:text-primary-foreground transition-all rounded-xl border border-border"
                                    >
                                        <ExternalLink size={20} />
                                    </a>
                                </div>
                            </div>
                        ))
                    ) : !loading && query && (
                        <div className="text-center py-20 glass-card border-dashed">
                            <Search className="h-16 w-16 text-muted mx-auto mb-6 opacity-50" />
                            <h3 className="text-2xl font-bold text-foreground mb-2">Ingen treff</h3>
                            <p className="text-muted text-lg">Vi fant ingen dokumenter i Lovdata som matcher "{query}".</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
