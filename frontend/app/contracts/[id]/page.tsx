"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getContract, getParty } from '@/lib/api';
import { motion } from 'framer-motion';
import { ExternalDataSection } from './ExternalDataSection';

export default function ContractDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = React.use(params);
    const [contract, setContract] = useState<any>(null);
    const [party, setParty] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getContract(id)
            .then(data => {
                setContract(data);
                if (data.party_id) {
                    getParty(data.party_id).then(setParty).catch(console.error);
                }
                setLoading(false);
            })
            .catch(console.error);
    }, [id]);

    if (loading) return <div className="p-8 text-muted">Loading contract...</div>;
    if (!contract) return <div className="p-8 text-rose-400">Contract not found</div>;

    return (
        <div className="min-h-screen p-8">
            <div className="max-w-6xl mx-auto">
                <div className="mb-6">
                    <Link href="#" onClick={() => window.history.back()} className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-7-7a1 1 0 010-1.414l7-7a1 1 0 011.414 1.414L4.414 9H17a1 1 0 110 2H4.414l5.293 5.293a1 1 0 010 1.414z" clipRule="evenodd" />
                        </svg>
                        Back
                    </Link>
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="grid grid-cols-1 lg:grid-cols-3 gap-8"
                >
                    {/* Main Content - Left Column */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Warning/Alert Section */}
                        {contract.external_data?.parsing_warning && (
                            <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 flex items-start gap-3">
                                <div className="text-amber-500 mt-0.5">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold text-amber-500 uppercase tracking-wide">Advarsel fra import</h4>
                                    <p className="text-amber-900 dark:text-amber-100/80 text-sm mt-1">{contract.external_data.parsing_warning}</p>
                                </div>
                            </div>
                        )}

                        <div className="glass-card p-8">
                            <header className="mb-8 border-b border-border pb-6">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-3 mb-2">
                                            <h1 className="text-3xl font-bold text-foreground tracking-tight">
                                                {contract.contract_name || "Kontrakt"}
                                            </h1>
                                            <span className="px-2 py-1 bg-white/10 rounded text-xs font-mono text-muted">#{contract.contract_id?.substring(0, 8)}</span>
                                            {contract.archive_code && (
                                                <span className="px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded text-xs font-mono" title="Arkivkode">
                                                    {contract.archive_code}
                                                </span>
                                            )}
                                        </div>
                                        {/* Fallback to contract.party if state party is not set yet, or prefer state party if separate fetch */}
                                        {party || contract.party ? (
                                            <div className="text-lg text-foreground font-medium flex items-center gap-2">
                                                <span className={`text-xs px-2 py-0.5 rounded-full uppercase font-bold tracking-wider border ${['Utleier', 'Huseier'].includes(
                                                    (() => {
                                                        const cat = (contract.category || "").toLowerCase();
                                                        if (cat.includes('innleie') || cat.includes('leiekontrakt') || cat.includes('husleie') || cat.includes('kostnad')) return 'Utleier';
                                                        if (cat.includes('utleie') || cat.includes('fremleie') || cat.includes('inntekt')) return 'Leietaker';
                                                        return 'Motpart';
                                                    })()
                                                )
                                                    ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                                                    : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                                                    }`}>
                                                    {(() => {
                                                        const cat = (contract.category || "").toLowerCase();
                                                        // If we are paying (Innleie/Leiekontrakt), the other party is the Landlord (Utleier)
                                                        if (cat.includes('innleie') || cat.includes('leiekontrakt') || cat.includes('husleie') || cat.includes('kostnad')) return 'Utleier';
                                                        // If we are receiving money (Utleie/Fremleie), the other party is the Tenant (Leietaker)
                                                        if (cat.includes('utleie') || cat.includes('fremleie') || cat.includes('inntekt')) return 'Leietaker';
                                                        // Default fallback
                                                        return 'Motpart';
                                                    })()}
                                                </span>
                                                <Link href={`/parties/${(party || contract.party)?.party_id}`} className="hover:text-blue-400 border-b border-transparent hover:border-blue-400 transition-colors">
                                                    {(party || contract.party).name}
                                                </Link>
                                                <span className="text-muted text-sm font-normal font-mono opacity-60">({(party || contract.party).orgnr})</span>
                                            </div>
                                        ) : (
                                            <p className="text-muted mt-1">Tenant ID: {contract.party_id}</p>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {contract.category && (
                                            <span className="px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                                {contract.category}
                                            </span>
                                        )}
                                        <span className={`px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wider border ${contract.status === 'active'
                                            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                            : 'bg-slate-500/20 text-muted border-slate-500/30'
                                            }`}>
                                            {contract.status}
                                        </span>
                                    </div>
                                </div>
                            </header>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="bg-surface/50 p-5 rounded-xl border border-border">
                                    <div className="text-label mb-2 flex items-center gap-2">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        Økonomi
                                    </div>
                                    <div className="text-4xl font-bold text-foreground tracking-tight mb-1">
                                        {contract.amount?.amount_per_year ? contract.amount.amount_per_year.toLocaleString() : "—"}
                                        <span className="text-lg text-muted font-normal ml-2">{contract.amount?.currency}</span>
                                    </div>
                                    <div className="text-xs text-muted uppercase tracking-widest mt-2">Årlig Beløp</div>

                                    {/* Original Rent String from External Data */}
                                    {contract.external_data?.original_rent_string && (
                                        <div className="mt-4 pt-4 border-t border-border">
                                            <div className="text-[10px] text-muted uppercase mb-1">Opprinnelig Tekst</div>
                                            <div className="text-sm text-muted italic">"{contract.external_data.original_rent_string}"</div>
                                        </div>
                                    )}
                                </div>

                                <div className="bg-surface/50 p-5 rounded-xl border border-border">
                                    <div className="text-label mb-2 flex items-center gap-2">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                        Varighet & Perioder
                                    </div>

                                    {/* Display all periods if available; fallback to contract start_date/end_date */}
                                    {contract.periods && contract.periods.length > 0 ? (
                                        <div className="space-y-4">
                                            {contract.periods.map((period: any, index: number) => (
                                                <div key={index} className="flex items-center gap-3">
                                                    <div>
                                                        <div className={`text-xl font-bold ${index === 0 ? 'text-foreground' : 'text-muted'}`}>
                                                            {period.start_date?.split('T')[0] || "N/A"}
                                                        </div>
                                                        <div className="text-[10px] text-muted uppercase">Start</div>
                                                    </div>
                                                    <div className="h-px bg-white/10 flex-1"></div>
                                                    <div className="text-right">
                                                        <div className={`text-xl font-bold ${index === 0 ? 'text-foreground' : 'text-muted'}`}>
                                                            {period.end_date?.split('T')[0] || "Løpende"}
                                                        </div>
                                                        <div className="text-[10px] text-muted uppercase">Slutt</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (contract.start_date || contract.end_date) ? (
                                        <div className="flex items-center gap-3">
                                            <div>
                                                <div className="text-xl font-bold text-foreground">
                                                    {typeof contract.start_date === 'string' ? contract.start_date.split('T')[0] : contract.start_date}
                                                </div>
                                                <div className="text-[10px] text-muted uppercase">Start</div>
                                            </div>
                                            <div className="h-px bg-white/10 flex-1"></div>
                                            <div className="text-right">
                                                <div className="text-xl font-bold text-foreground">
                                                    {contract.end_date ? (typeof contract.end_date === 'string' ? contract.end_date.split('T')[0] : contract.end_date) : "Løpende"}
                                                </div>
                                                <div className="text-[10px] text-muted uppercase">Slutt</div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-muted Italic">Ingen perioder definert</div>
                                    )}
                                </div>

                                {/* Cost Breakdown Section – direkte kostnader + løpende fra external_data */}
                                {(() => {
                                    const ext = contract.external_data || {};
                                    const hasDirect = contract.caretaker_cost != null || contract.cleaning_cost != null || contract.parking_cost != null || contract.card_reader_cost != null;
                                    const hasRunning = ext.common_costs != null || ext.internal_maintenance_cost != null || ext.user_dependent_costs != null || ext.energy_cost != null || ext.heating_cost != null || ext.municipal_fees != null || ext.deposit != null;
                                    if (!hasDirect && !hasRunning) return null;

                                    const fmt = (v: number) => new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(v);
                                    return (
                                        <div className="md:col-span-2 bg-surface/50 p-5 rounded-xl border border-border">
                                            <div className="text-label mb-4 flex items-center gap-2">
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                                Kostnadsfordeling
                                            </div>
                                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                                {contract.caretaker_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Vaktmester</div>
                                                        <div className="font-semibold text-foreground">{fmt(contract.caretaker_cost)}</div>
                                                    </div>
                                                )}
                                                {contract.cleaning_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Renhold</div>
                                                        <div className="font-semibold text-foreground">{fmt(contract.cleaning_cost)}</div>
                                                    </div>
                                                )}
                                                {contract.parking_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Parkering</div>
                                                        <div className="font-semibold text-foreground">{fmt(contract.parking_cost)}</div>
                                                    </div>
                                                )}
                                                {contract.card_reader_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Kortleser</div>
                                                        <div className="font-semibold text-foreground">{fmt(contract.card_reader_cost)}</div>
                                                    </div>
                                                )}
                                                {ext.common_costs != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Felleskostnader</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.common_costs)}</div>
                                                    </div>
                                                )}
                                                {ext.internal_maintenance_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Indre vedlikehold</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.internal_maintenance_cost)}</div>
                                                    </div>
                                                )}
                                                {ext.user_dependent_costs != null && (
                                                    <div className="p-3 rounded-lg bg-background/50" title="Avtalt budsjettert beløp for strøm, vann, internett m.m. (brukeravhengige driftskostnader)">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Brukeravhengige driftskostnader</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.user_dependent_costs)}</div>
                                                        <div className="text-[10px] text-muted mt-0.5">Strøm, vann, internett m.m.</div>
                                                    </div>
                                                )}
                                                {ext.energy_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Energi</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.energy_cost)}</div>
                                                    </div>
                                                )}
                                                {ext.heating_cost != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Oppvarming</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.heating_cost)}</div>
                                                    </div>
                                                )}
                                                {ext.municipal_fees != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Kommunale avgifter</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.municipal_fees)}</div>
                                                    </div>
                                                )}
                                                {ext.deposit != null && (
                                                    <div className="p-3 rounded-lg bg-background/50">
                                                        <div className="text-xs text-muted uppercase tracking-wider mb-0.5">Depositum</div>
                                                        <div className="font-semibold text-foreground">{fmt(ext.deposit)}</div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })()}

                                {/* Opsjon */}
                                {(contract.has_option || contract.option_deadline || contract.option_count_total != null) && (
                                    <div className="md:col-span-2 bg-surface/50 p-5 rounded-xl border border-border">
                                        <div className="text-label mb-4 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            Opsjon
                                        </div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            <div>
                                                <div className={`text-sm font-bold ${contract.has_option ? 'text-emerald-400' : 'text-muted'}`}>
                                                    {contract.has_option ? 'Ja' : 'Nei'}
                                                </div>
                                                <div className="text-xs text-muted uppercase">Har opsjon</div>
                                            </div>
                                            {contract.option_deadline && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.option_deadline?.split('T')[0]}</div>
                                                    <div className="text-xs text-muted uppercase">Varslingsfrist</div>
                                                </div>
                                            )}
                                            {contract.option_count_total != null && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.option_count_total}</div>
                                                    <div className="text-xs text-muted uppercase">Opsjoner totalt</div>
                                                </div>
                                            )}
                                            {contract.option_count_used != null && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.option_count_used}</div>
                                                    <div className="text-xs text-muted uppercase">Benyttet</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Leieobjekt (Unit) Info Section */}
                                {contract.unit && (
                                    <div className="md:col-span-2 bg-surface/50 p-5 rounded-xl border border-border">
                                        <div className="text-label mb-4 flex items-center gap-2">
                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                            Leieobjekt
                                        </div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                            {contract.unit.purpose && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.unit.purpose?.toLowerCase() == 'barnevernsinstitusjon' ? 'Formålsbygg' : contract.unit.purpose}</div>
                                                    <div className="text-xs text-muted uppercase">Bruksformål</div>
                                                </div>
                                            )}
                                            {contract.unit.area_sqm && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.unit.area_sqm} m²</div>
                                                    <div className="text-xs text-muted uppercase">Areal</div>
                                                </div>
                                            )}
                                            {contract.unit.floor !== null && contract.unit.floor !== undefined && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.unit.floor === 0 ? "Underetasje/Kjeller" : `${contract.unit.floor}. Etasje`}</div>
                                                    <div className="text-xs text-muted uppercase">Etasje</div>
                                                </div>
                                            )}
                                            {contract.unit.zone_type && (
                                                <div>
                                                    <div className="text-sm font-bold text-foreground">{contract.unit.zone_type}</div>
                                                    <div className="text-xs text-muted uppercase">Sone Type</div>
                                                </div>
                                            )}
                                            {/* UU Compliance Badge */}
                                            <div className="flex flex-col justify-center">
                                                <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-bold ${contract.unit.uu_compliant ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-500/10 text-muted border border-slate-500/20'}`}>
                                                    <div className={`w-1.5 h-1.5 rounded-full ${contract.unit.uu_compliant ? 'bg-emerald-500' : 'bg-slate-500'}`}></div>
                                                    {contract.unit.uu_compliant ? "UU Godkjent" : "Ikke UU Vurdert"}
                                                </div>
                                            </div>
                                        </div>
                                        {contract.unit.uu_notes && (
                                            <div className="mt-4 pt-4 border-t border-border">
                                                <div className="text-[10px] text-muted uppercase mb-1">UU Notater</div>
                                                <div className="text-sm text-muted italic">"{contract.unit.uu_notes}"</div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Property Info Block */}
                            <div className="mt-8 pt-8 border-t border-border">
                                <h3 className="text-label mb-4">Relatert Eiendom</h3>
                                <div className="bg-surface/50 p-4 rounded-lg flex items-center justify-between group cursor-pointer hover:bg-white/10 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="bg-blue-500/20 p-3 rounded-lg text-blue-400">
                                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                        </div>
                                        <div>
                                            <div className="font-bold text-foreground">{contract.property?.name || contract.property?.address || "Adresse ikke tilgjengelig"}</div>
                                            <div className="text-xs text-muted flex gap-2">
                                                {contract.property?.property_id && <span className="font-mono">ID: {contract.property.property_id.substring(0, 8)}...</span>}
                                                {contract.unit_id && <span className="font-mono border-l border-border pl-2">Unit: {contract.unit_id.substring(0, 8)}...</span>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {contract.property?.property_id && (
                                    <Link href={`/properties/${contract.property.property_id}`} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-lg transition-colors">
                                        Gå til Eiendom
                                    </Link>
                                )}
                            </div>
                        </div>

                        {/* Files Section */}
                        <div className="mt-8 pt-8 border-t border-border">
                            <h3 className="text-label mb-4">Vedlegg og Filer ({contract.files?.length || 0})</h3>
                            {contract.files && contract.files.length > 0 ? (
                                <div className="grid grid-cols-1 gap-3">
                                    {contract.files.map((file: any) => (
                                        <div key={file.file_id} className="bg-surface/50 p-4 rounded-lg flex items-center justify-between hover:bg-white/10 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="bg-purple-500/20 p-2 rounded text-purple-400">
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                                </div>
                                                <div>
                                                    <div className="text-sm font-bold text-foreground max-w-[300px] truncate" title={file.path}>{file.path.split('/').pop()}</div>
                                                    <div className="text-xs text-muted">{file.file_type || "Fil"} • {file.content_type || "Ukjent type"}</div>
                                                </div>
                                            </div>
                                            <a href={`/api/v1/files/${file.file_id}/download`} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 px-3 py-1.5 rounded-full transition-colors">
                                                Last ned
                                            </a>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-muted text-sm Italic">Ingen filer knyttet til kontrakten.</div>
                            )}
                        </div>

                        {/* Additional Info / External Data Section */}
                        {(() => {
                            const extData = { ...(contract.external_data || {}) };

                            // Use the new top-level elements field if available
                            if (contract.elements) {
                                extData.elements = contract.elements;
                            }
                            // Fallback lookup: Elements/Arkivreferanse is sometimes stored on the Property during import
                            else if (!extData.elements && contract.property?.external_data?.master_data?.archive_name) {
                                extData.elements = contract.property.external_data.master_data.archive_name;
                            }

                            if (Object.keys(extData).length > 0) {
                                return <ExternalDataSection data={extData} />;
                            }
                            return null;
                        })()}

                        {/* RAW DATA INSPECTOR (For total transparency) */}
                        <div className="mt-12 pt-8 border-t border-border opacity-60 hover:opacity-100 transition-opacity">
                            <details className="group">
                                <summary className="flex items-center gap-2 cursor-pointer text-xs uppercase tracking-widest text-muted hover:text-foreground transition-colors">
                                    <svg className="w-4 h-4 group-open:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                    Vis komplett rådata (JSON)
                                </summary>
                                <div className="mt-4 bg-slate-950/50 p-6 rounded-xl border border-border font-mono text-xs text-green-400 overflow-x-auto">
                                    <pre>{JSON.stringify(contract, null, 2)}</pre>
                                </div>
                            </details>
                        </div>
                    </div>

                    {/* Sidebar - Right Column */}
                    <div className="space-y-6">
                        {/* Status Timeline / Key Dates */}
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-bold text-foreground mb-4">Nøkkelhendelser</h3>
                            <div className="relative border-l border-border ml-3 space-y-6 pb-2">
                                <div className="ml-6 relative">
                                    <div className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 ${contract.signed_at ? 'bg-emerald-500 border-emerald-900' : 'bg-slate-800 border-slate-600'}`}></div>
                                    <div className="text-sm font-bold text-foreground">Signert</div>
                                    <div className="text-xs text-muted mt-1">{contract.signed_at ? new Date(contract.signed_at).toLocaleDateString() : "Ingen dato"}</div>
                                </div>
                                <div className="ml-6 relative">
                                    <div className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 ${contract.status === 'active' ? 'bg-blue-500 border-blue-900' : 'bg-slate-800 border-slate-600'}`}></div>
                                    <div className="text-sm font-bold text-foreground">Start Dato</div>
                                    <div className="text-xs text-muted mt-1">
                                        {contract.periods?.[0]?.start_date?.split('T')[0] || (contract.start_date ? (typeof contract.start_date === 'string' ? contract.start_date.split('T')[0] : String(contract.start_date)) : "N/A")}
                                    </div>
                                </div>
                                {(contract.end_date || contract.periods?.[0]?.end_date) && (
                                    <div className="ml-6 relative">
                                        <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 bg-slate-700 border-slate-600"></div>
                                        <div className="text-sm font-bold text-foreground">Slutt Dato</div>
                                        <div className="text-xs text-muted mt-1">
                                            {contract.periods?.[0]?.end_date?.split('T')[0] || (contract.end_date ? (typeof contract.end_date === 'string' ? contract.end_date.split('T')[0] : String(contract.end_date)) : "Løpende")}
                                        </div>
                                    </div>
                                )}
                                {contract.terminated_at && (
                                    <div className="ml-6 relative">
                                        <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 bg-rose-500 border-rose-900"></div>
                                        <div className="text-sm font-bold text-foreground">Opphørt</div>
                                        <div className="text-xs text-muted mt-1">{new Date(contract.terminated_at).toLocaleDateString()}</div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Linked Party Mini-Card */}
                        {party && (
                            <div className="glass-card p-6">
                                <h3 className="text-lg font-bold text-foreground mb-4">Motpart</h3>
                                <div className="flex items-center gap-4 mb-4">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-xl font-bold text-white shadow-lg">
                                        {party.name.charAt(0)}
                                    </div>
                                    <div>
                                        <div className="font-bold text-foreground leading-tight">{party.name}</div>
                                        <div className="text-xs text-muted mt-0.5">Org: {party.orgnr}</div>
                                    </div>
                                </div>
                                <div className="space-y-3 mt-4 pt-4 border-t border-border">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Type</span>
                                        <span className="text-foreground">{party.type || "N/A"}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Adresse</span>
                                        <span className="text-foreground text-right max-w-[60%] truncate" title={party.external_data?.address || "Ikke tilgjengelig"}>
                                            {party.external_data?.address || "Ikke tilgjengelig"}
                                        </span>
                                    </div>
                                    {/* Contact Info */}
                                    {party.contact_email && (
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted">E-post</span>
                                            <a href={`mailto:${party.contact_email}`} className="text-blue-400 hover:text-blue-300 truncate max-w-[60%]">
                                                {party.contact_email}
                                            </a>
                                        </div>
                                    )}
                                    {party.contact_phone && (
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted">Telefon</span>
                                            <a href={`tel:${party.contact_phone}`} className="text-blue-400 hover:text-blue-300 truncate max-w-[60%]">
                                                {party.contact_phone}
                                            </a>
                                        </div>
                                    )}
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Kilde</span>
                                        <span className="text-foreground opacity-70">{party.source || "Intern"}</span>
                                    </div>
                                </div>
                                <Link href={`/parties/${party.party_id}`} className="mt-4 block w-full py-2 bg-surface/50 hover:bg-white/10 border border-border rounded-lg text-center text-sm font-medium transition-colors">
                                    Vis Detaljer
                                </Link>
                            </div>
                        )}

                        {/* Metadata Debug Info */}
                        <div className="p-4 rounded-lg border border-border bg-slate-800/20 text-xs font-mono text-muted overflow-hidden">
                            <div className="flex justify-between mb-1">
                                <span>Created</span>
                                <span>{contract.created_at ? new Date(contract.created_at).toLocaleDateString() : "-"}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Updated</span>
                                <span>{contract.updated_at ? new Date(contract.updated_at).toLocaleDateString() : "-"}</span>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
