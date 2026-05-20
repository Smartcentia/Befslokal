"use client";

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
    AlertCircle,
    CheckCircle2,
    Clock,
    FileText,
    Loader2,
    Search,
    Sparkles,
} from 'lucide-react';
import {
    searchFdvDocuments,
    processDocument,
    processAllDocuments,
    type DocSearchResult,
    type FdvDocumentWithStatus,
} from '@/lib/api/docSearchApi';
import { fetchAPI } from '@/lib/api/client';

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function useDebounce<T>(value: T, delay: number): T {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const t = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(t);
    }, [value, delay]);
    return debounced;
}

// ─────────────────────────────────────────────
// Status badge
// ─────────────────────────────────────────────

function StatusBadge({ status }: { status: FdvDocumentWithStatus['extraction_status'] }) {
    if (status === 'done') {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 border border-green-500/30">
                <CheckCircle2 size={11} /> Ferdig
            </span>
        );
    }
    if (status === 'processing') {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 animate-pulse">
                <Loader2 size={11} className="animate-spin" /> Prosesserer
            </span>
        );
    }
    if (status === 'failed') {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/30">
                <AlertCircle size={11} /> Feilet
            </span>
        );
    }
    // pending
    return (
        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-500/15 text-gray-400 border border-gray-500/30">
            <Clock size={11} /> Venter
        </span>
    );
}

// ─────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────

export default function DokumenterPage() {
    const params = useParams();
    const propertyId = params?.propertyId as string;

    const [query, setQuery] = useState('');
    const debouncedQuery = useDebounce(query, 400);

    const [searchResults, setSearchResults] = useState<DocSearchResult[]>([]);
    const [searching, setSearching] = useState(false);
    const [searchError, setSearchError] = useState<string | null>(null);

    const [documents, setDocuments] = useState<FdvDocumentWithStatus[]>([]);
    const [docsLoading, setDocsLoading] = useState(true);
    const [docsError, setDocsError] = useState<string | null>(null);

    const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
    const [processAllLoading, setProcessAllLoading] = useState(false);
    const [processAllMsg, setProcessAllMsg] = useState<string | null>(null);

    // ── Load documents list ─────────────────────────────────────────────────
    const loadDocuments = useCallback(async () => {
        if (!propertyId) return;
        setDocsLoading(true);
        setDocsError(null);
        try {
            const data = await fetchAPI<FdvDocumentWithStatus[]>(
                `/fdvu/documents?property_id=${propertyId}`,
            );
            setDocuments(data);
        } catch (e) {
            setDocsError(e instanceof Error ? e.message : 'Kunne ikke laste dokumenter');
        } finally {
            setDocsLoading(false);
        }
    }, [propertyId]);

    useEffect(() => {
        loadDocuments();
    }, [loadDocuments]);

    // ── Semantic search ─────────────────────────────────────────────────────
    useEffect(() => {
        if (!debouncedQuery.trim()) {
            setSearchResults([]);
            setSearchError(null);
            return;
        }
        let cancelled = false;
        setSearching(true);
        setSearchError(null);
        searchFdvDocuments(debouncedQuery, propertyId, 10)
            .then((res) => {
                if (!cancelled) setSearchResults(res);
            })
            .catch((e) => {
                if (!cancelled) setSearchError(e instanceof Error ? e.message : 'Søk feilet');
            })
            .finally(() => {
                if (!cancelled) setSearching(false);
            });
        return () => {
            cancelled = true;
        };
    }, [debouncedQuery, propertyId]);

    // ── Process single document ─────────────────────────────────────────────
    const handleProcess = async (documentId: string) => {
        setProcessingIds((prev) => new Set(prev).add(documentId));
        try {
            await processDocument(documentId);
            // Reload after brief delay to pick up status change
            setTimeout(loadDocuments, 1500);
        } catch (e) {
            console.error('Process document failed:', e);
        } finally {
            setProcessingIds((prev) => {
                const next = new Set(prev);
                next.delete(documentId);
                return next;
            });
        }
    };

    // ── Process all ─────────────────────────────────────────────────────────
    const handleProcessAll = async () => {
        if (!propertyId) return;
        setProcessAllLoading(true);
        setProcessAllMsg(null);
        try {
            const res = await processAllDocuments(propertyId);
            setProcessAllMsg(`${res.queued} dokumenter satt i kø`);
            setTimeout(loadDocuments, 2000);
        } catch (e) {
            setProcessAllMsg('Prosessering feilet');
        } finally {
            setProcessAllLoading(false);
        }
    };

    const showSearch = debouncedQuery.trim().length > 0;

    return (
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <Link
                        href={`/fdvu/${propertyId}`}
                        className="text-muted-foreground hover:text-foreground transition-colors text-sm"
                    >
                        ← Tilbake
                    </Link>
                    <div>
                        <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                            <FileText className="text-primary" size={20} />
                            Dokumentsøk
                        </h1>
                        <p className="text-muted-foreground text-xs mt-0.5 font-mono">{propertyId}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {processAllMsg && (
                        <span className="text-xs text-muted-foreground">{processAllMsg}</span>
                    )}
                    <button
                        onClick={handleProcessAll}
                        disabled={processAllLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                        {processAllLoading ? (
                            <Loader2 size={14} className="animate-spin" />
                        ) : (
                            <Sparkles size={14} />
                        )}
                        Prosesser alle
                    </button>
                </div>
            </div>

            {/* Search box */}
            <div className="relative">
                <Search
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Semantisk søk i FDV-dokumenter…"
                    className="w-full bg-card border border-border rounded-lg pl-9 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                />
                {searching && (
                    <Loader2
                        size={15}
                        className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-muted-foreground"
                    />
                )}
            </div>

            {/* Search results */}
            {showSearch && (
                <div className="space-y-3">
                    <h2 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                        <Sparkles size={14} className="text-primary" />
                        Søkeresultater
                    </h2>

                    {searchError && (
                        <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-3">
                            <AlertCircle size={14} />
                            {searchError}
                        </div>
                    )}

                    {!searching && !searchError && searchResults.length === 0 && (
                        <p className="text-sm text-muted-foreground">Ingen treff funnet.</p>
                    )}

                    {searchResults.map((r) => (
                        <div
                            key={r.document_id}
                            className="bg-card border border-border rounded-lg px-4 py-3 space-y-1 hover:border-primary/30 transition-colors"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-foreground truncate">{r.title}</p>
                                    <p className="text-xs text-muted-foreground">{r.document_type}</p>
                                </div>
                                <span className="shrink-0 text-xs font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">
                                    {Math.round(r.similarity * 100)}%
                                </span>
                            </div>
                            {r.excerpt && (
                                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                                    {r.excerpt}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Document list */}
            <div className="space-y-3">
                <h2 className="text-sm font-semibold text-foreground">Alle dokumenter</h2>

                {docsError && (
                    <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-lg px-4 py-3">
                        <AlertCircle size={14} />
                        {docsError}
                    </div>
                )}

                {docsLoading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 size={14} className="animate-spin" /> Laster dokumenter…
                    </div>
                )}

                {!docsLoading && documents.length === 0 && !docsError && (
                    <p className="text-sm text-muted-foreground">Ingen dokumenter funnet for denne eiendommen.</p>
                )}

                {documents.map((doc) => {
                    const isProcessing = processingIds.has(doc.document_id);
                    const canProcess =
                        doc.extraction_status === 'pending' || doc.extraction_status === 'failed';

                    return (
                        <div
                            key={doc.document_id}
                            className="bg-card border border-border rounded-lg px-4 py-3 flex items-center gap-4"
                        >
                            <FileText size={18} className="shrink-0 text-muted-foreground" />
                            <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-foreground truncate">{doc.title}</p>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <span className="text-xs text-muted-foreground">{doc.document_type}</span>
                                    {doc.page_count != null && (
                                        <span className="text-xs text-muted-foreground">· {doc.page_count} sider</span>
                                    )}
                                </div>
                            </div>
                            <div className="shrink-0 flex items-center gap-2">
                                <StatusBadge status={doc.extraction_status} />
                                {canProcess && (
                                    <button
                                        onClick={() => handleProcess(doc.document_id)}
                                        disabled={isProcessing}
                                        className="text-xs px-2.5 py-1 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors disabled:opacity-50 flex items-center gap-1"
                                    >
                                        {isProcessing ? (
                                            <Loader2 size={11} className="animate-spin" />
                                        ) : (
                                            <Sparkles size={11} />
                                        )}
                                        Prosesser
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
