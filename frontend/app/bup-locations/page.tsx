"use client";
import React, { useState, useEffect } from 'react';
import Header from '@/app/components/ui/Header';

import { getBUPLocations } from '@/lib/api';
import { BUPLocation } from '@/lib/types';

export default function BUPLocationsPage() {
    const [locations, setLocations] = useState<BUPLocation[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await getBUPLocations();
                setLocations(data.locations);
            } catch (error) {
                console.error("Failed to load BUP locations", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    const filtered = locations.filter(l =>
        l.adresse.toLowerCase().includes(searchTerm.toLowerCase()) ||
        l.region.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="container mx-auto py-8 px-4 text-white">
            <Header />
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-transparent bg-clip-text bg-linear-to-r from-blue-400 to-purple-400">
                        BUP Lokasjoner
                    </h1>
                    <p className="text-slate-400 mt-2">
                        Oversikt over Barne- og ungdomspsykiatriske poliklinikker
                    </p>
                </div>
            </div>

            <div className="mb-8">
                <input
                    type="text"
                    placeholder="Søk i adresse eller region..."
                    className="w-full p-4 bg-surface border border-slate-700 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>



            <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
                    <h2 className="font-bold text-white">Liste over lokasjoner ({filtered.length})</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-white/5 text-slate-400 text-xs uppercase font-semibold">
                            <tr>
                                <th className="px-6 py-3">Adresse</th>
                                <th className="px-6 py-3">Region</th>
                                <th className="px-6 py-3">Telefon</th>
                                <th className="px-6 py-3">Koordinater</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/10">
                            {filtered.map((loc) => (
                                <tr key={loc.id} className="hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4 font-medium text-white">{loc.adresse}</td>
                                    <td className="px-6 py-4">
                                        <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs font-bold uppercase border border-blue-500/30">{loc.region}</span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-400">{loc.telefon || '-'}</td>
                                    <td className="px-6 py-4 text-xs font-mono text-slate-500">
                                        {loc.latitude && loc.longitude ?
                                            `${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}` :
                                            <span className="text-red-400 italic">Mangler</span>
                                        }
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && !loading && (
                                <tr>
                                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Ingen resultater funnet</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
