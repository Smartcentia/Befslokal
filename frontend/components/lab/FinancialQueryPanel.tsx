'use client';

import React, { useState, useEffect } from 'react';
import { runFinancialQuery, compareProperties, type FinancialQueryRequest, type FinancialQueryResponse } from '@/lib/api';
import { propertyService, type Property } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface FinancialQueryPanelProps {
    onToolCreated?: (toolId: string) => void;
}

export default function FinancialQueryPanel({ onToolCreated }: FinancialQueryPanelProps) {
    const [query, setQuery] = useState('');
    const [selectedProperties, setSelectedProperties] = useState<string[]>([]);
    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<FinancialQueryResponse | null>(null);
    const [showPropertySelector, setShowPropertySelector] = useState(false);

    // Load properties on mount
    useEffect(() => {
        loadProperties();
    }, []);

    const loadProperties = async () => {
        try {
            const data = await propertyService.getAll(0, 500);
            setProperties(data);
        } catch (error) {
            console.error('Failed to load properties:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setResult(null);

        try {
            const request: FinancialQueryRequest = {
                query: query.trim(),
                property_ids: selectedProperties.length > 0 ? selectedProperties : undefined
            };

            const response = await runFinancialQuery(request);
            setResult(response);

            if (response.tool_id && onToolCreated) {
                onToolCreated(response.tool_id);
            }
        } catch (error: any) {
            setResult({
                status: 'error',
                intent: 'unknown',
                confidence: 0,
                error: error.message || 'Failed to process query'
            });
        } finally {
            setLoading(false);
        }
    };

    const quickActions = [
        {
            label: 'Finn outliers i kostnader',
            query: 'Finn eiendommer med unormalt høye driftskostnader sammenlignet med andre'
        },
        {
            label: 'Sammenlign valgte eiendommer',
            query: 'Sammenlign totale kostnader, leie og vedlikehold for å identifisere mønstre'
        },
        {
            label: 'Vis korrelasjoner',
            query: 'Analyser korrelasjoner mellom leiekostnader og vedlikeholdskostnader'
        }
    ];

    const togglePropertySelection = (propertyId: string) => {
        setSelectedProperties(prev =>
            prev.includes(propertyId)
                ? prev.filter(id => id !== propertyId)
                : [...prev, propertyId]
        );
    };

    return (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-full">
            {/* Left Column: Inputs & Controls */}
            <div className="space-y-6 flex flex-col h-full">
                {/* Header */}
                <div className="border-b border-border pb-4">
                    <h2 className="text-2xl font-bold bg-linear-to-r from-accent to-primary bg-clip-text text-transparent">
                        Financial Intelligence
                    </h2>
                    <p className="text-muted mt-2 text-sm">
                        Still spørsmål i naturlig språk eller bruk hurtigvalg for å generere analyser
                    </p>
                </div>

                {/* Property Selector */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted">
                            Velg eiendommer (valgfritt)
                        </label>
                        <button
                            onClick={() => setShowPropertySelector(!showPropertySelector)}
                            className="text-primary hover:text-primary/80 text-sm font-medium"
                        >
                            {showPropertySelector ? 'Skjul' : 'Vis'} liste ({selectedProperties.length} valgt)
                        </button>
                    </div>

                    {showPropertySelector && (
                        <div className="bg-surface border border-border rounded-lg p-4 max-h-64 overflow-y-auto custom-scrollbar">
                            {properties.map(property => (
                                <label
                                    key={property.id}
                                    className="flex items-center space-x-3 p-2 hover:bg-muted/10 rounded cursor-pointer transition-colors"
                                >
                                    <input
                                        type="checkbox"
                                        checked={selectedProperties.includes(property.id)}
                                        onChange={() => togglePropertySelection(property.id)}
                                        className="w-4 h-4 text-primary rounded focus:ring-primary border-border bg-input"
                                    />
                                    <span className="text-sm text-foreground">
                                        {property.name}
                                    </span>
                                </label>
                            ))}
                        </div>
                    )}
                </div>

                {/* Quick Actions */}
                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted">Hurtigvalg</label>
                    <div className="flex flex-wrap gap-2">
                        {quickActions.map((action, idx) => (
                            <button
                                key={idx}
                                onClick={() => setQuery(action.query)}
                                className="px-4 py-2 bg-surface hover:bg-muted/10 border border-border hover:border-primary/50 rounded-lg text-sm text-muted hover:text-foreground transition-all duration-200"
                            >
                                {action.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Query Input */}
                <form onSubmit={handleSubmit} className="space-y-4 flex-1 flex flex-col">
                    <div className="flex-1">
                        <label className="text-sm font-medium text-muted mb-2 block">
                            Din forespørsel
                        </label>
                        <textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="F.eks: Sammenlign 8 eiendommer for å finne outliers i vedlikeholdskostnader..."
                            className="w-full h-40 enterprise-input resize-none"
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="w-full py-3 bg-linear-to-r from-primary to-accent hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all shadow-md"
                    >
                        {loading ? 'Analyserer...' : 'Analyser'}
                    </button>
                </form>
            </div>

            {/* Right Column: Results */}
            <div className="flex flex-col h-full min-h-[400px]">
                {result ? (
                    <div className="bg-surface/50 border border-border rounded-lg p-6 space-y-4 h-full flex flex-col animate-fadeIn">
                        {/* Status Badge */}
                        <div className="flex items-center justify-between pb-4 border-b border-border">
                            <div className="flex items-center space-x-3">
                                <span
                                    className={`px-3 py-1 rounded-full text-xs font-semibold ${result.status === 'tool_created'
                                        ? 'bg-green-500/10 text-green-500 border border-green-500/20'
                                        : result.status === 'error'
                                            ? 'bg-red-500/10 text-red-500 border border-red-500/20'
                                            : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                                        }`}
                                >
                                    {result.status}
                                </span>
                                <span className="text-sm text-muted">
                                    Intent: <span className="text-foreground font-medium">{result.intent}</span>
                                </span>
                                <span className="text-sm text-muted">
                                    Confidence: <span className="text-foreground font-medium">{result.confidence ? (result.confidence * 100).toFixed(0) : 0}%</span>
                                </span>
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto space-y-6 pr-2 custom-scrollbar">
                            {/* Tool ID */}
                            {result.tool_id && (
                                <div className="bg-background rounded p-3 border border-border">
                                    <p className="text-xs text-muted mb-1">Tool ID</p>
                                    <p className="text-sm font-mono text-primary">{result.tool_id}</p>
                                </div>
                            )}

                            {/* Visualization */}
                            {result.data && Array.isArray(result.data) && result.data.length > 0 && (
                                <div className="h-80 w-full bg-surface border border-border rounded-lg p-4">
                                    <p className="text-sm font-medium text-muted mb-4">Grafisk fremstilling</p>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={result.data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.1} />
                                            <XAxis
                                                dataKey="name"
                                                stroke="hsl(var(--muted-foreground))"
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                            />
                                            <YAxis
                                                stroke="hsl(var(--muted-foreground))"
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                                tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                                            />
                                            <Tooltip
                                                cursor={{ fill: 'hsl(var(--muted)/0.2)' }}
                                                contentStyle={{
                                                    backgroundColor: 'hsl(var(--popover))',
                                                    borderColor: 'hsl(var(--border))',
                                                    borderRadius: 'var(--radius)',
                                                    color: 'hsl(var(--popover-foreground))'
                                                }}
                                            />
                                            <Bar dataKey="value" name="Verdi" radius={[4, 4, 0, 0]}>
                                                {result.data.map((entry: any, index: number) => (
                                                    <Cell key={`cell-${index}`} fill={`hsl(var(--primary))`} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Text Summary */}
                            {result.summary && (
                                <div className="space-y-4">
                                    <div className="prose prose-invert max-w-none text-sm text-foreground/90">
                                        <p>{result.summary}</p>
                                    </div>
                                </div>
                            )}

                            {/* Generated Code */}
                            {result.code && (
                                <div className="space-y-2">
                                    <p className="text-sm font-medium text-muted">Generert kode:</p>
                                    <pre className="bg-slate-950 border border-border rounded p-4 text-xs text-green-400 overflow-x-auto font-mono">
                                        {result.code}
                                    </pre>
                                </div>
                            )}

                            {/* Error */}
                            {result.error && (
                                <div className="bg-red-500/5 border border-red-500/20 rounded p-4">
                                    <p className="text-sm text-red-500">{result.error}</p>
                                </div>
                            )}

                            {/* Success Message */}
                            {result.status === 'tool_created' && !result.error && (
                                <div className="bg-green-500/5 border border-green-500/20 rounded p-4">
                                    <p className="text-sm text-green-500">
                                        ✓ Verktøy opprettet! Gå til Library-tab for å kjøre det.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="h-full border border-dashed border-border rounded-lg flex flex-col items-center justify-center p-12 text-center bg-surface/30">
                        <div className="text-6xl mb-4 opacity-20">📊</div>
                        <h3 className="text-lg font-medium text-foreground mb-2">Ingen analyse kjørt</h3>
                        <p className="text-muted max-w-sm">
                            Bruk skjemaet til venstre for å generere finansielle analyser og verktøy. Resultatene vil vises her.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
