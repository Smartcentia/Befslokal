"use client";

import React, { useState } from 'react';
import { fetchAPI } from '@/lib/api';

interface SearchResult {
    property_id: string;
    name: string;
    region: string;
    address: string;
    rent: number;
    costs: number;
    total: number;
    num_contracts: number;
    num_expenses: number;
    status: 'complete' | 'missing_costs' | 'missing_rent' | 'missing_all';
}

interface PropertyAnalysis {
    property_id: string;
    name: string;
    region: string;
    address: string;
    rent: number;
    costs: number;
    total: number;
    num_contracts: number;
    num_expenses: number;
    contracts: Array<{
        contract_id: string;
        rent: number;
        start_date: string | null;
        end_date: string | null;
    }>;
    cost_by_category: Array<{
        category: string;
        amount: number;
        percentage: number;
    }>;
    cost_by_provider: Array<{
        provider: string;
        amount: number;
    }>;
    data_sources?: {
        kontrakt: { annual_rent_contracted: number; num_contracts: number; description: string };
        manuelle_utgifter: { total: number; num_lines: number; description: string };
        gl_regnskap: {
            siste_ar_med_aktivitet: number | null;
            faktisk_husleie: number;
            andre_kostnader: number;
            description: string;
        };
        score_0_100: number;
        issue_codes: string[];
    };
}

export default function FinancialAnalysisPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedProperty, setSelectedProperty] = useState<PropertyAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'search' | 'details'>('search');

    const handleSearch = async () => {
        if (searchQuery.length < 2) return;

        setLoading(true);
        try {
            const data = await fetchAPI(`/admin/financial-analysis/search?query=${encodeURIComponent(searchQuery)}`);
            setSearchResults(data.results || []);
        } catch (error) {
            console.error('Search failed:', error);
            alert('Søk feilet. Sjekk at backend kjører.');
        }
        setLoading(false);
    };

    const loadPropertyDetails = async (propertyId: string) => {
        setLoading(true);
        try {
            const data = await fetchAPI(`/admin/financial-analysis/property/${propertyId}`);
            setSelectedProperty(data);
            setActiveTab('details');
        } catch (error) {
            console.error('Failed to load property:', error);
            alert('Kunne ikke laste eiendomsdata.');
        }
        setLoading(false);
    };

    const getStatusBadge = (status: string) => {
        const badges = {
            complete: { bg: 'bg-green-500/20', text: 'text-green-400', label: '✓ Komplett' },
            missing_costs: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: '⚠ Mangler kostnader' },
            missing_rent: { bg: 'bg-orange-500/20', text: 'text-orange-400', label: '⚠ Mangler husleie' },
            missing_all: { bg: 'bg-red-500/20', text: 'text-red-400', label: '✗ Mangler alt' }
        };
        const badge = badges[status as keyof typeof badges] || badges.missing_all;
        return `${badge.bg} ${badge.text} px-3 py-1 rounded-full text-xs font-semibold`;
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('nb-NO', {
            style: 'currency',
            currency: 'NOK',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    };

    return (
        <div className="min-h-screen bg-[#0B0F19] p-8">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-white mb-8">Finansiell Analyse</h1>

                {/* Tab Navigation */}
                <div className="flex gap-4 mb-6 border-b border-[#29324d]">
                    <button
                        onClick={() => setActiveTab('search')}
                        className={`px-4 py-2 font-semibold transition-colors ${activeTab === 'search'
                                ? 'text-blue-400 border-b-2 border-blue-400'
                                : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        🔍 Søk
                    </button>
                    {selectedProperty && (
                        <button
                            onClick={() => setActiveTab('details')}
                            className={`px-4 py-2 font-semibold transition-colors ${activeTab === 'details'
                                    ? 'text-blue-400 border-b-2 border-blue-400'
                                    : 'text-slate-400 hover:text-white'
                                }`}
                        >
                            📊 Detaljer
                        </button>
                    )}
                </div>

                {/* Search Tab */}
                {activeTab === 'search' && (
                    <div className="glass-card p-6 rounded-lg border border-[#29324d] bg-[#1e273b]/50">
                        <div className="flex gap-4 mb-6">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                placeholder="Søk etter eiendom..."
                                className="flex-1 px-4 py-3 bg-[#0B0F19] border border-[#29324d] rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                            />
                            <button
                                onClick={handleSearch}
                                disabled={loading || searchQuery.length < 2}
                                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold text-white transition-colors disabled:bg-slate-600 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Søker...' : 'Søk'}
                            </button>
                        </div>

                        {searchResults.length > 0 && (
                            <div className="space-y-3">
                                <p className="text-slate-400 text-sm mb-4">
                                    Fant {searchResults.length} eiendom{searchResults.length !== 1 ? 'mer' : ''}
                                </p>
                                {searchResults.map((result) => (
                                    <div
                                        key={result.property_id}
                                        onClick={() => loadPropertyDetails(result.property_id)}
                                        className="p-4 bg-[#0B0F19] border border-[#29324d] rounded-lg hover:border-blue-500 cursor-pointer transition-all"
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <h3 className="text-white font-semibold text-lg">{result.name}</h3>
                                                <p className="text-slate-400 text-sm">{result.region}</p>
                                            </div>
                                            <span className={getStatusBadge(result.status).split(' ').slice(0, -4).join(' ')}>
                                                {getStatusBadge(result.status).includes('Komplett') ? '✓ Komplett' :
                                                    getStatusBadge(result.status).includes('kostnader') ? '⚠ Mangler kostnader' :
                                                        getStatusBadge(result.status).includes('husleie') ? '⚠ Mangler husleie' : '✗ Mangler alt'}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-4 text-sm">
                                            <div>
                                                <p className="text-slate-500">Husleie</p>
                                                <p className="text-white font-semibold">{formatCurrency(result.rent)}</p>
                                            </div>
                                            <div>
                                                <p className="text-slate-500">Kostnader</p>
                                                <p className="text-white font-semibold">{formatCurrency(result.costs)}</p>
                                            </div>
                                            <div>
                                                <p className="text-slate-500">Total</p>
                                                <p className="text-white font-semibold">{formatCurrency(result.total)}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Details Tab */}
                {activeTab === 'details' && selectedProperty && (
                    <div className="space-y-6">
                        {/* Summary Card */}
                        <div className="glass-card p-6 rounded-lg border border-[#29324d] bg-[#1e273b]/50">
                            <h2 className="text-2xl font-bold text-white mb-4">{selectedProperty.name}</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                <div>
                                    <p className="text-slate-400 text-sm">Region</p>
                                    <p className="text-white font-semibold">{selectedProperty.region}</p>
                                </div>
                                <div>
                                    <p className="text-slate-400 text-sm">Husleie/år (kontrakt)</p>
                                    <p className="text-white font-semibold">{formatCurrency(selectedProperty.rent)}</p>
                                </div>
                                <div>
                                    <p className="text-slate-400 text-sm">Kostnader/år (manuelt)</p>
                                    <p className="text-white font-semibold">{formatCurrency(selectedProperty.costs)}</p>
                                </div>
                                <div>
                                    <p className="text-slate-400 text-sm">Total/år (kontrakt+manuelt)</p>
                                    <p className="text-white font-semibold text-lg">{formatCurrency(selectedProperty.total)}</p>
                                </div>
                            </div>
                        </div>

                        {selectedProperty.data_sources && (
                            <div className="glass-card p-6 rounded-lg border border-[#29324d] bg-[#1e273b]/50">
                                <h3 className="text-xl font-semibold text-white mb-2">Datakilder (to lag)</h3>
                                <p className="text-slate-400 text-sm mb-4">
                                    Kontrakt og manuelle utgifter er ikke det samme som bokført GL. Se{' '}
                                    <span className="text-slate-300">docs/DATAKILDER_EIENDOM_FINANS.md</span> i repo.
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                    <div className="rounded-lg border border-[#29324d] p-4 bg-[#0B0F19]/60">
                                        <p className="text-emerald-400 font-semibold mb-2">Kontrakt</p>
                                        <p className="text-slate-400 text-xs mb-2">{selectedProperty.data_sources.kontrakt.description}</p>
                                        <p className="text-white font-mono">{formatCurrency(selectedProperty.data_sources.kontrakt.annual_rent_contracted)}</p>
                                    </div>
                                    <div className="rounded-lg border border-[#29324d] p-4 bg-[#0B0F19]/60">
                                        <p className="text-amber-400 font-semibold mb-2">Manuelle utgifter</p>
                                        <p className="text-slate-400 text-xs mb-2">{selectedProperty.data_sources.manuelle_utgifter.description}</p>
                                        <p className="text-white font-mono">{formatCurrency(selectedProperty.data_sources.manuelle_utgifter.total)}</p>
                                    </div>
                                    <div className="rounded-lg border border-[#29324d] p-4 bg-[#0B0F19]/60">
                                        <p className="text-cyan-400 font-semibold mb-2">GL (regnskap)</p>
                                        <p className="text-slate-400 text-xs mb-2">{selectedProperty.data_sources.gl_regnskap.description}</p>
                                        <p className="text-slate-500 text-xs">År {selectedProperty.data_sources.gl_regnskap.siste_ar_med_aktivitet ?? '–'}</p>
                                        <p className="text-white font-mono">Husleie: {formatCurrency(selectedProperty.data_sources.gl_regnskap.faktisk_husleie)}</p>
                                        <p className="text-white font-mono">Øvrig: {formatCurrency(selectedProperty.data_sources.gl_regnskap.andre_kostnader)}</p>
                                    </div>
                                </div>
                                <div className="mt-4 flex flex-wrap gap-3 items-center">
                                    <span className="text-slate-400">Kompletthet score:</span>
                                    <span className="text-white font-bold">{selectedProperty.data_sources.score_0_100}</span>
                                    {selectedProperty.data_sources.issue_codes?.length > 0 && (
                                        <span className="text-orange-400 text-xs">
                                            {selectedProperty.data_sources.issue_codes.join(', ')}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Cost Breakdown */}
                        {selectedProperty.cost_by_category.length > 0 && (
                            <div className="glass-card p-6 rounded-lg border border-[#29324d] bg-[#1e273b]/50">
                                <h3 className="text-xl font-semibold text-white mb-4">Kostnader per Kategori</h3>
                                <div className="space-y-2">
                                    {selectedProperty.cost_by_category.slice(0, 10).map((cat, idx) => (
                                        <div key={idx} className="flex justify-between items-center">
                                            <span className="text-slate-300">{cat.category}</span>
                                            <div className="flex items-center gap-4">
                                                <span className="text-white font-semibold">{formatCurrency(cat.amount)}</span>
                                                <span className="text-slate-400 text-sm w-12 text-right">{cat.percentage.toFixed(1)}%</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Top Providers */}
                        {selectedProperty.cost_by_provider.length > 0 && (
                            <div className="glass-card p-6 rounded-lg border border-[#29324d] bg-[#1e273b]/50">
                                <h3 className="text-xl font-semibold text-white mb-4">Største Leverandører</h3>
                                <div className="space-y-2">
                                    {selectedProperty.cost_by_provider.slice(0, 5).map((prov, idx) => (
                                        <div key={idx} className="flex justify-between items-center">
                                            <span className="text-slate-300">{prov.provider}</span>
                                            <span className="text-white font-semibold">{formatCurrency(prov.amount)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
