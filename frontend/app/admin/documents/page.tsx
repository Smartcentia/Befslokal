"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { uploadService, UploadResponse } from '@/lib/services/uploadService';
import { getContracts, Contract } from '@/lib/api';

export default function AdminDocumentsPage() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<UploadResponse | null>(null);

    // Contract Linking State
    const [contracts, setContracts] = useState<Contract[]>([]);
    const [selectedContractId, setSelectedContractId] = useState<string>("");
    const [searchTerm, setSearchTerm] = useState("");
    const [loadingContracts, setLoadingContracts] = useState(false);

    useEffect(() => {
        const fetchContracts = async () => {
            setLoadingContracts(true);
            try {
                // Fetch all contracts for the dropdown/search
                // In a real app with thousands of contracts, we'd use server-side search.
                const data = await getContracts();
                setContracts(data);
            } catch (e) {
                console.error("Failed to fetch contracts", e);
            } finally {
                setLoadingContracts(false);
            }
        };
        fetchContracts();
    }, []);

    // Filter contracts based on search
    const filteredContracts = contracts.filter(c => {
        const cNum = c.contractNumber || c.external_data?.contract_number || "";
        const pName = c.unit?.property?.name || c.property?.name || "";
        const tName = c.party?.name || "";

        return (
            cNum.toLowerCase().includes(searchTerm.toLowerCase()) ||
            pName.toLowerCase().includes(searchTerm.toLowerCase()) ||
            tName.toLowerCase().includes(searchTerm.toLowerCase())
        );
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // Pass the selected contract ID (if any)
            const contractIdToUse = selectedContractId || undefined;

            // Use SAS Direct Upload for robustness
            const response = await uploadService.uploadFileSAS(file, contractIdToUse);

            setResult(response);
            setFile(null); // Clear input on success
            setSelectedContractId(""); // Clear selection
            setSearchTerm("");
        } catch (err: any) {
            console.error("Upload failed:", err);
            setError(err.message || "En ukjent feil oppstod under opplasting.");
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const scanRes = await uploadService.scanFiles();
            setResult({
                file_id: "scan-batch",
                path: "Lokal Storage",
                message: `Scan Complete: ${scanRes.scanned} scanned, ${scanRes.newly_imported} new files imported.`,
                indexing_stats: { chunks: 0, total_chars: 0 } // Dummy stats
            });
        } catch (err: any) {
            console.error("Scan failed:", err);
            setError("Scan failed: " + (err.message || "Unknown error"));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/admin" className="p-2 bg-white rounded-lg shadow-sm text-slate-600 hover:bg-slate-50 transition-colors">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                    </Link>
                    <h1 className="text-3xl font-bold text-slate-800">Dokumentarkiv</h1>
                </div>

                {/* --- Scanner Section --- */}
                <div className="bg-linear-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100 mb-8 flex items-center justify-between">
                    <div>
                        <h3 className="font-bold text-blue-900 text-lg">Oppdater filliste</h3>
                        <p className="text-sm text-blue-700 mt-1 max-w-lg">
                            Skann backend storage og oppdater dokumentlisten.
                        </p>
                    </div>
                    <button
                        onClick={handleScan}
                        disabled={loading}
                        className="bg-white text-blue-600 font-bold py-2 px-6 rounded-lg shadow-sm border border-blue-200 hover:bg-blue-50 hover:shadow-md transition-all flex items-center gap-2"
                    >
                        {loading ? (
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        ) : (
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                        )}
                        Scan & Importer
                    </button>
                </div>

                <div className="bg-white p-8 rounded-xl shadow-md border border-slate-200 mb-8">
                    <h2 className="text-xl font-semibold mb-6 text-slate-800">Manuell Opplasting (PDF)</h2>

                    {/* Contract Selection Section */}
                    <div className="mb-8 p-4 bg-slate-50 rounded-lg border border-slate-200">
                        <label className="block text-sm font-medium text-slate-700 mb-2">
                            Koble til Kontrakt (Valgfritt)
                        </label>
                        <p className="text-xs text-slate-500 mb-3">
                            Søk etter kontraktsnummer, eiendom eller leietaker for å koble dokumentet til riktig kontrakt.
                        </p>

                        <div className="relative">
                            <div className="flex items-center gap-2 mb-2">
                                <svg className="w-5 h-5 text-slate-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                                <input
                                    type="text"
                                    placeholder="Søk etter kontrakt..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full pl-10 p-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                />
                            </div>

                            {/* Dropdown / Selection Area */}
                            {loadingContracts ? (
                                <div className="text-sm text-slate-500 py-2">Laster kontrakter...</div>
                            ) : (
                                <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-md bg-white">
                                    {filteredContracts.length === 0 ? (
                                        <div className="p-3 text-sm text-slate-400 text-center">Ingen kontrakter funnet</div>
                                    ) : (
                                        filteredContracts.map(contract => (
                                            <div
                                                key={contract.contract_id}
                                                onClick={() => setSelectedContractId(contract.contract_id === selectedContractId ? "" : contract.contract_id)}
                                                className={`p-3 text-sm cursor-pointer border-b border-slate-100 last:border-0 hover:bg-blue-50 transition-colors flex justify-between items-center
                                                    ${selectedContractId === contract.contract_id ? 'bg-blue-100 border-l-4 border-l-blue-600' : ''}`}
                                            >
                                                <div>
                                                    <div className="font-medium text-slate-800">
                                                        {contract.contractNumber || contract.external_data?.contract_number || "Ikke nr"} - {contract.unit?.property?.name || contract.property?.name || "Ukjent eiendom"}
                                                    </div>
                                                    <div className="text-slate-500">{contract.party?.name || "Ukjent part"}</div>
                                                </div>
                                                {selectedContractId === contract.contract_id && (
                                                    <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}

                            {selectedContractId && (
                                <div className="mt-2 text-sm text-green-700 flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                                    Koblet til valgt kontrakt
                                </div>
                            )}
                        </div>
                    </div>


                    <div className="mb-6">
                        <label className="block text-sm font-medium text-slate-700 mb-2">Velg PDF-fil</label>
                        <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-lg hover:bg-slate-50 transition-colors cursor-pointer relative">
                            <input
                                type="file"
                                accept="application/pdf"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            <div className="space-y-1 text-center">
                                <svg className="mx-auto h-12 w-12 text-slate-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                                <div className="flex text-sm text-slate-600 justify-center">
                                    <span className="font-medium text-indigo-600 hover:text-indigo-500">Last opp en fil</span>
                                    <p className="pl-1">eller dra og slipp</p>
                                </div>
                                <p className="text-xs text-slate-500">
                                    PDF opp til 10MB
                                </p>
                                {file && (
                                    <p className="mt-2 text-sm font-bold text-indigo-600">
                                        Valgt fil: {file.name}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <button
                            onClick={handleUpload}
                            disabled={!file || loading}
                            className={`px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-[1.02] flex items-center gap-2
                                ${!file || loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 shadow-lg'}`}
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    Laster opp og analyserer...
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                    Start Opplasting
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-lg mb-8 flex items-start gap-4 shadow-sm animate-fade-in">
                        <svg className="w-6 h-6 shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        <div>
                            <div className="font-bold text-lg mb-1">Opplasting Feilet</div>
                            <div>{error}</div>
                        </div>
                    </div>
                )}

                {result && (
                    <div className="bg-green-50 border border-green-200 text-green-800 p-6 rounded-lg mb-8 shadow-sm animate-fade-in">
                        <div className="flex items-center gap-3 mb-4">
                            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            <h3 className="text-xl font-bold">Suksess!</h3>
                        </div>

                        <div className="bg-white/50 p-4 rounded-md border border-green-100 mb-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <span className="text-sm text-green-600 font-semibold uppercase tracking-wider">Fil ID</span>
                                    <div className="font-mono text-sm mt-1 select-all">{result.file_id}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-green-600 font-semibold uppercase tracking-wider">Lagring</span>
                                    <div className="font-mono text-sm mt-1 truncate" title={result.path}>{result.path}</div>
                                </div>
                            </div>
                        </div>

                        {result.indexing_stats && (
                            <div className="bg-blue-50 border border-blue-200 p-4 rounded-md">
                                <h4 className="flex items-center gap-2 font-bold text-blue-800 mb-2">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                    AI Analyse (OCR)
                                </h4>
                                <ul className="space-y-1 text-sm text-blue-800">
                                    <li>• Sider analysert: <strong>{result.indexing_stats.chunks}</strong></li>
                                    <li>• Tekststørrelse: <strong>{result.indexing_stats.total_chars} tegn</strong></li>
                                    <li>• Status: <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">INDEKSERT</span></li>
                                </ul>
                                <p className="mt-2 text-xs text-blue-600">
                                    Dokumentet er nå søkbart. Prøv å spørre AI-kollegaen om innholdet.
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
