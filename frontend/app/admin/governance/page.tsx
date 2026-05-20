'use client';

import React, { useState, useEffect } from 'react';
import { 
    getGovernanceCatalog, 
    getClassificationStats,
    CatalogEntry,
    ClassificationStats 
} from '@/lib/api/governanceApi';
import SchemaGraphView from '@/components/governance/SchemaGraphView';
import { Shield, Database, Lock, AlertTriangle, Search, Filter, GitBranch, Table2 } from 'lucide-react';

type GovernanceTab = 'catalog' | 'schema';

export default function DataGovernancePage() {
    const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
    const [stats, setStats] = useState<ClassificationStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [filter, setFilter] = useState<'ALL' | 'PII' | 'FINANCIAL' | 'RESTRICTED' | 'PUBLIC'>('ALL');
    const [activeTab, setActiveTab] = useState<GovernanceTab>('catalog');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [catalogData, statsData] = await Promise.all([
                    getGovernanceCatalog(),
                    getClassificationStats()
                ]);
                setCatalog(catalogData);
                setStats(statsData);
            } catch (err) {
                console.error('Failed to fetch governance data:', err);
                setError(err instanceof Error ? err.message : 'Kunne ikke hente datakatalog');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredCatalog = catalog.filter(entry => {
        const matchesSearch = 
            entry.table.toLowerCase().includes(searchTerm.toLowerCase()) ||
            entry.column.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (entry.description || '').toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesFilter = filter === 'ALL' || entry.classification === filter;
        
        return matchesSearch && matchesFilter;
    });

    const getClassificationColor = (cls: string) => {
        switch (cls) {
            case 'PII': return 'text-red-600 bg-red-50 border-red-200';
            case 'FINANCIAL': return 'text-amber-600 bg-amber-50 border-amber-200';
            case 'RESTRICTED': return 'text-purple-600 bg-purple-50 border-purple-200';
            case 'PUBLIC': return 'text-green-600 bg-green-50 border-green-200';
            default: return 'text-gray-600 bg-gray-50 border-gray-200';
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Shield className="w-8 h-8 text-blue-600" />
                        Data Governance & Klassifisering
                    </h1>
                    <p className="text-gray-500 mt-1">Oversikt over dataopphav, sensitivitet og personvern (PII).</p>
                </div>
                <div
                    className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1 self-start"
                    role="tablist"
                    aria-label="Data governance visning"
                >
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === 'catalog'}
                        onClick={() => setActiveTab('catalog')}
                        className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'catalog'
                                ? 'bg-white text-gray-900 shadow-sm'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        <Table2 className="w-4 h-4" />
                        Katalog
                    </button>
                    <button
                        type="button"
                        role="tab"
                        aria-selected={activeTab === 'schema'}
                        onClick={() => setActiveTab('schema')}
                        className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                            activeTab === 'schema'
                                ? 'bg-white text-gray-900 shadow-sm'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        <GitBranch className="w-4 h-4" />
                        Relasjonskart
                    </button>
                </div>
            </div>

            {activeTab === 'schema' && <SchemaGraphView />}

            {/* Stats Cards */}
            {activeTab === 'catalog' && error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    Katalog kunne ikke lastes: {error}. Relasjonskart-fanen kan fortsatt være tilgjengelig.
                </div>
            )}
            {activeTab === 'catalog' && loading && (
                <div className="py-12 text-center text-gray-600">Laster datakatalog…</div>
            )}
            {activeTab === 'catalog' && !loading && !error && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="text-sm text-gray-500 flex items-center gap-2">
                        <Database className="w-4 h-4" /> Total Tabeller
                    </div>
                    <div className="text-2xl font-bold mt-1">{stats?.total_tables || 0}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="text-sm text-red-600 flex items-center gap-2 font-medium">
                        <AlertTriangle className="w-4 h-4" /> PII Felt
                    </div>
                    <div className="text-2xl font-bold mt-1">{stats?.classification_counts.PII || 0}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="text-sm text-amber-600 flex items-center gap-2 font-medium">
                        <Lock className="w-4 h-4" /> Finansielle Data
                    </div>
                    <div className="text-2xl font-bold mt-1">{stats?.classification_counts.FINANCIAL || 0}</div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <div className="text-sm text-purple-600 flex items-center gap-2 font-medium">
                        <AlertTriangle className="w-4 h-4" /> Begrensede Data
                    </div>
                    <div className="text-2xl font-bold mt-1">{stats?.classification_counts.RESTRICTED || 0}</div>
                </div>
            </div>
            )}

            {/* Controls */}
            {activeTab === 'catalog' && !loading && !error && (
            <div className="flex flex-col md:flex-row gap-4 items-center bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="relative flex-1 w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input 
                        type="text" 
                        placeholder="Søk i tabeller, kolonner eller beskrivelser..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                </div>
                <div className="flex items-center gap-2 w-full md:w-auto">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select 
                        value={filter}
                        title="Filtrer etter kategori"
                        onChange={(e) => setFilter(e.target.value as 'ALL' | 'PII' | 'FINANCIAL' | 'RESTRICTED' | 'PUBLIC')}
                        className="flex-1 md:w-48 px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 outline-none"
                    >
                        <option value="ALL">Alle kategorier</option>
                        <option value="PII">Personopplysninger (PII)</option>
                        <option value="FINANCIAL">Finansiell Data</option>
                        <option value="RESTRICTED">Begrenset</option>
                        <option value="PUBLIC">Offentlig</option>
                    </select>
                </div>
            </div>
            )}

            {/* Catalog Table */}
            {activeTab === 'catalog' && !loading && !error && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Tabell</th>
                                <th className="px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Kolonne</th>
                                <th className="px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                                <th className="px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Klassifisering</th>
                                <th className="px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Beskrivelse</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {filteredCatalog.map((entry, idx) => (
                                <tr key={`${entry.table}-${entry.column}-${idx}`} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{entry.table}</td>
                                    <td className="px-6 py-4 text-sm font-mono text-gray-600">{entry.column}</td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{entry.type}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getClassificationColor(entry.classification)}`}>
                                            {entry.classification}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs">{entry.description || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filteredCatalog.length === 0 && (
                    <div className="p-8 text-center text-gray-500">Ingen treff på valgt filter/sikt.</div>
                )}
            </div>
            )}
        </div>
    );
}