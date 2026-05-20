"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getParty, fetchPartyCompanySummaryFromWeb, runPartyDueDiligence, enrichPartyBrreg, runKonkursCheckSingle, runMediaMonitorSingle } from '@/lib/api';
import { CompanyFinancials } from '@/app/components/features/CompanyFinancials';
import { RiskIndicator } from '@/app/components/features/RiskIndicator'; // Import new component
import { HealthScoreCard, type HealthScore } from '@/app/components/features/HealthScoreBadge';
import { motion } from 'framer-motion';

export default function PartyDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = React.use(params);
    const [party, setParty] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [fetchingSummary, setFetchingSummary] = useState(false);
    const [summaryError, setSummaryError] = useState<string | null>(null);
    const [fetchingDD, setFetchingDD] = useState(false);
    const [ddError, setDdError] = useState<string | null>(null);
    const [fetchingBrreg, setFetchingBrreg] = useState(false);
    const [brregError, setBrregError] = useState<string | null>(null);
    const [fetchingKonkurs, setFetchingKonkurs] = useState(false);
    const [konkursError, setKonkursError] = useState<string | null>(null);
    const [fetchingMedia, setFetchingMedia] = useState(false);
    const [mediaError, setMediaError] = useState<string | null>(null);

    const loadParty = () => getParty(id).then(data => { setParty(data); setLoading(false); }).catch(console.error);

    useEffect(() => {
        loadParty();
    }, [id]);

    const hasOrgnr = party?.orgnr && String(party.orgnr).replace(/\s/g, '').length === 9;
    const ddReport = party?.external_data?.due_diligence_report;

    const onFetchCompanySummary = async () => {
        if (!hasOrgnr) return;
        setSummaryError(null);
        setFetchingSummary(true);
        try {
            await fetchPartyCompanySummaryFromWeb(id);
            await loadParty();
        } catch (e: any) {
            const msg = e?.message || '';
            const tail = msg.includes(' - ') ? msg.split(' - ').pop()?.trim() : '';
            try {
                if (tail && tail.startsWith('{')) {
                    const j = JSON.parse(tail) as { detail?: string };
                    if (typeof j?.detail === 'string') {
                        setSummaryError(j.detail);
                        return;
                    }
                }
            } catch (_) { /* ignore */ }
            setSummaryError(msg || 'Kunne ikke hente oppsummering.');
        } finally {
            setFetchingSummary(false);
        }
    };

    const onEnrichBrreg = async () => {
        if (!hasOrgnr) return;
        setBrregError(null);
        setFetchingBrreg(true);
        try {
            await enrichPartyBrreg(id);
            await loadParty();
        } catch (e: any) {
            const msg = e?.message || '';
            const tail = msg.includes(' - ') ? msg.split(' - ').pop()?.trim() : '';
            try {
                if (tail && tail.startsWith('{')) {
                    const j = JSON.parse(tail) as { detail?: string };
                    if (typeof j?.detail === 'string') {
                        setBrregError(j.detail);
                        return;
                    }
                }
            } catch (_) { /* ignore */ }
            setBrregError(msg || 'Kunne ikke hente BRREG-data.');
        } finally {
            setFetchingBrreg(false);
        }
    };

    const onRunKonkursCheck = async () => {
        if (!hasOrgnr) return;
        setKonkursError(null);
        setFetchingKonkurs(true);
        try {
            await runKonkursCheckSingle(id);
            await loadParty();
        } catch (e: any) {
            setKonkursError(e?.message || 'Kunne ikke kjøre konkurssjekk.');
        } finally {
            setFetchingKonkurs(false);
        }
    };

    const onRunMediaMonitor = async () => {
        if (!hasOrgnr) return;
        setMediaError(null);
        setFetchingMedia(true);
        try {
            await runMediaMonitorSingle(id);
            await loadParty();
        } catch (e: any) {
            setMediaError(e?.message || 'Kunne ikke kjøre media monitor.');
        } finally {
            setFetchingMedia(false);
        }
    };

    const onRunDueDiligence = async () => {
        if (!hasOrgnr) return;
        setDdError(null);
        setFetchingDD(true);
        try {
            await runPartyDueDiligence(id);
            await loadParty();
        } catch (e: any) {
            const msg = e?.message || '';
            const tail = msg.includes(' - ') ? msg.split(' - ').pop()?.trim() : '';
            try {
                if (tail && tail.startsWith('{')) {
                    const j = JSON.parse(tail) as { detail?: string };
                    if (typeof j?.detail === 'string') {
                        setDdError(j.detail);
                        return;
                    }
                }
            } catch (_) { /* ignore */ }
            setDdError(msg || 'Kunne ikke kjøre risikovurdering.');
        } finally {
            setFetchingDD(false);
        }
    };

    if (loading) return <div className="p-8 text-slate-400">Loading party details...</div>;
    if (!party) return <div className="p-8 text-rose-400">Party not found</div>;

    const brreg = party.external_data?.brreg_enhet ?? {};
    const brregRoller = party.external_data?.brreg_roller?.roller ?? [];
    const roles = party.external_data?.roles ?? {};
    const openaiSummary = party.external_data?.openai_company_summary;
    const source = party.source ?? brreg.source ?? party.external_data?.source ?? '';
    const isBrreg = source && String(source).toUpperCase().includes('BRREG');
    const partyType = party.type ?? brreg.type ?? party.external_data?.type ?? (party.orgnr ? 'Bedrift' : 'Privat');
    const displayEmail = (party.external_data?.email && party.external_data.email !== 'N/A')
        ? party.external_data.email
        : (brreg.email && brreg.email !== 'N/A')
            ? brreg.email
            : party.contact_email ?? party.email ?? 'N/A';
    const displayPhone = (party.external_data?.phone && party.external_data.phone !== 'N/A')
        ? party.external_data.phone
        : (brreg.phone && brreg.phone !== 'N/A')
            ? brreg.phone
            : party.contact_phone ?? party.phone ?? 'N/A';
    const displayAddress = (party.external_data?.address?.trim())
        ? party.external_data.address
        : (brreg.address?.trim())
            ? brreg.address
            : party.address ?? 'N/A';

    return (
        <div className="min-h-screen p-8 text-foreground bg-background">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                    <Link href="#" onClick={() => window.history.back()} className="text-primary hover:text-primary/80 transition-colors flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-7-7a1 1 0 010-1.414l7-7a1 1 0 011.414 1.414L4.414 9H17a1 1 0 110 2H4.414l5.293 5.293a1 1 0 010 1.414z" clipRule="evenodd" />
                        </svg>
                        Back
                    </Link>
                </div>

                {/* Konkurs / risk status banner – vises alltid når sjekket (OK = grønn, CRITICAL/WARNING = rød/oransje) */}
                {(() => {
                    const ks = party.external_data?.konkurs_status;
                    if (!ks) return null;
                    const isOK = ks.risk_level === 'OK';
                    const isCritical = ks.risk_level === 'CRITICAL';
                    return (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`mb-6 p-4 rounded-xl border ${isOK
                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
                                : isCritical
                                    ? 'bg-red-500/10 border-red-500/40 text-red-700 dark:text-red-400'
                                    : 'bg-orange-500/10 border-orange-500/40 text-orange-700 dark:text-orange-400'
                            }`}
                        >
                            <div className="flex items-start gap-3">
                                <span className="text-xl mt-0.5">{isOK ? '✓' : isCritical ? '🚨' : '⚠️'}</span>
                                <div className="flex-1 min-w-0">
                                    <div className="font-bold text-sm mb-1">
                                        {isOK ? 'Konkurssjekk: Ingen risiko' : (isCritical ? 'KRITISK RISIKO' : 'ADVARSEL') + ' – Konkursovervåkning'}
                                    </div>
                                    {!isOK && ks.risk_flags?.length > 0 && (
                                        <ul className="text-xs space-y-0.5">
                                            {ks.risk_flags.map((flag: string, i: number) => (
                                                <li key={i}>• {flag}</li>
                                            ))}
                                        </ul>
                                    )}
                                    {ks.checked_at && (
                                        <div className="text-[10px] opacity-60 mt-1">
                                            Sjekket: {new Date(ks.checked_at).toLocaleString('nb-NO')}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    );
                })()}

                {hasOrgnr && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6"
                    >
                        <RiskIndicator orgNr={party.orgnr} />
                    </motion.div>
                )}

                {/* Health Score card */}
                {party.health_score && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <HealthScoreCard score={party.health_score as HealthScore} />
                    </motion.div>
                )}

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card overflow-hidden"
                >
                    <div className="bg-muted/10 border-b border-border px-8 py-8 relative">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-32 w-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                        </div>
                        <div className="flex justify-between items-start relative z-10">
                            <div>
                                <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
                                    {party.name}
                                    {isBrreg && (
                                        <span className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-xs px-2 py-1 rounded-full flex items-center gap-1 shadow-sm font-bold tracking-wider" title="Data verifisert av Brønnøysundregistrene">
                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                            Verified
                                        </span>
                                    )}
                                </h1>
                                <p className="text-muted-foreground text-sm mt-2 font-mono flex items-center gap-4">
                                    <span className="flex items-center gap-2">
                                        <span className="opacity-50">ORG.NR</span>
                                        <span className="text-foreground">{party.orgnr ?? '—'}</span>
                                    </span>
                                    {party.reference_code && (
                                        <span className="flex items-center gap-2">
                                            <span className="opacity-50">REF</span>
                                            <span className="text-foreground">{party.reference_code}</span>
                                        </span>
                                    )}
                                </p>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                                <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-xs font-bold uppercase tracking-wider">{partyType}</span>
                                {party.external_data?.orgForm && (
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{party.external_data.orgForm}</span>
                                )}
                                {source && <span className="text-[10px] text-muted-foreground uppercase tracking-widest">Source: {source}</span>}
                            </div>
                        </div>
                    </div>

                    <div className="p-8">
                        <h2 className="text-lg font-semibold text-foreground mb-6 pb-2 border-b border-border flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 21h7a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v11m0 5l4.879-4.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242z" />
                            </svg>
                            Contact & Legal Information
                        </h2>
                        <ul className="space-y-6 text-muted-foreground">
                            <li className="flex items-start">
                                <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Email</span>
                                <a href={`mailto:${displayEmail}`} className="text-primary hover:text-primary/80 transition-colors font-medium break-all">
                                    {displayEmail}
                                </a>
                            </li>
                            <li className="flex items-start">
                                <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Phone</span>
                                <span className="font-medium text-foreground font-mono">
                                    {displayPhone}
                                </span>
                            </li>
                            <li className="flex items-start">
                                <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Postal Address</span>
                                <span className="font-medium text-foreground">
                                    {displayAddress}
                                </span>
                            </li>
                            {brreg.stiftelsesdato && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Stiftelsesdato</span>
                                    <span className="font-medium text-foreground">{brreg.stiftelsesdato}</span>
                                </li>
                            )}
                            {brreg.vedtektsdato && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Vedtektsdato</span>
                                    <span className="font-medium text-foreground">{brreg.vedtektsdato}</span>
                                </li>
                            )}
                            {(brreg.organisasjonsform_beskrivelse || brreg.organisasjonsform_kode) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Selskapsform</span>
                                    <span className="font-medium text-foreground">
                                        {brreg.organisasjonsform_beskrivelse || ''}
                                        {brreg.organisasjonsform_kode ? ` (${brreg.organisasjonsform_kode})` : ''}
                                    </span>
                                </li>
                            )}
                            {(brreg.naeringskode1?.beskrivelse || brreg.naeringskode1?.kode) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Næring (NACE)</span>
                                    <span className="font-medium text-foreground">
                                        {brreg.naeringskode1?.beskrivelse || ''}
                                        {brreg.naeringskode1?.kode && brreg.naeringskode1?.beskrivelse ? ` (${brreg.naeringskode1.kode})` : brreg.naeringskode1?.kode || ''}
                                    </span>
                                </li>
                            )}
                            {(brreg.naeringskode2?.beskrivelse || brreg.naeringskode2?.kode) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Næring 2 (NACE)</span>
                                    <span className="font-medium text-foreground">
                                        {brreg.naeringskode2?.beskrivelse || ''}
                                        {brreg.naeringskode2?.kode ? ` (${brreg.naeringskode2.kode})` : ''}
                                    </span>
                                </li>
                            )}
                            {(brreg.naeringskode3?.beskrivelse || brreg.naeringskode3?.kode) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Næring 3 (NACE)</span>
                                    <span className="font-medium text-foreground">
                                        {brreg.naeringskode3?.beskrivelse || ''}
                                        {brreg.naeringskode3?.kode ? ` (${brreg.naeringskode3.kode})` : ''}
                                    </span>
                                </li>
                            )}
                            {(brreg.institusjonellSektorkode_beskrivelse || brreg.institusjonellSektorkode_kode) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Institusjonell sektor</span>
                                    <span className="font-medium text-foreground">
                                        {brreg.institusjonellSektorkode_beskrivelse || ''}
                                        {brreg.institusjonellSektorkode_kode ? ` (${brreg.institusjonellSektorkode_kode})` : ''}
                                    </span>
                                </li>
                            )}
                            {brreg.antallAnsatte != null && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Antall ansatte</span>
                                    <span className="font-medium text-foreground">{brreg.antallAnsatte}</span>
                                </li>
                            )}
                            {brreg.kapital?.belop != null && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Aksjekapital</span>
                                    <span className="font-medium text-foreground">
                                        {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: brreg.kapital.valuta || 'NOK', maximumFractionDigits: 0 }).format(brreg.kapital.belop)}
                                        {brreg.kapital.antallAksjer != null ? ` · ${new Intl.NumberFormat('nb-NO').format(brreg.kapital.antallAksjer)} aksjer` : ''}
                                    </span>
                                </li>
                            )}
                            {brreg.hjemmeside && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Hjemmeside</span>
                                    <a href={String(brreg.hjemmeside).startsWith('http') ? brreg.hjemmeside : `https://${brreg.hjemmeside}`} target="_blank" rel="noopener noreferrer" className="font-medium text-primary hover:underline break-all">
                                        {brreg.hjemmeside}
                                    </a>
                                </li>
                            )}
                            {brreg.sisteInnsendteAarsregnskap && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Siste årsregnskap</span>
                                    <span className="font-medium text-foreground">{brreg.sisteInnsendteAarsregnskap}</span>
                                </li>
                            )}
                            {brreg.overordnetEnhet && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Overordnet enhet</span>
                                    <span className="font-medium text-foreground font-mono">{brreg.overordnetEnhet}</span>
                                </li>
                            )}
                            {(brreg.konkurs || brreg.underAvvikling || brreg.underTvangsavviklingEllerTvangsopplosning) && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Risikoflagg</span>
                                    <div className="flex flex-wrap gap-2">
                                        {brreg.konkurs && (
                                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30">
                                                ⚠ Konkurs{brreg.konkursdato ? ` (${brreg.konkursdato})` : ''}
                                            </span>
                                        )}
                                        {brreg.underAvvikling && (
                                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-500/30">
                                                ⚠ Under avvikling{brreg.underAvviklingDato ? ` (${brreg.underAvviklingDato})` : ''}
                                            </span>
                                        )}
                                        {brreg.underTvangsavviklingEllerTvangsopplosning && (
                                            <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30">
                                                ⚠ Under tvangsoppløsning
                                            </span>
                                        )}
                                    </div>
                                </li>
                            )}
                            {brreg.slettedato && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Slettet</span>
                                    <span className="font-medium text-red-600 dark:text-red-400">{brreg.slettedato}</span>
                                </li>
                            )}
                            {roles.dagligLeder && !brregRoller.some((r: any) => r.type_kode === 'DAGL') && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Daglig leder</span>
                                    <span className="font-medium text-foreground">{roles.dagligLeder}</span>
                                </li>
                            )}
                            {roles.styretsLeder && !brregRoller.some((r: any) => r.type_kode === 'LEDE') && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Styreleder</span>
                                    <span className="font-medium text-foreground">{roles.styretsLeder}</span>
                                </li>
                            )}
                            {roles.revisor && !brregRoller.some((r: any) => r.type_kode === 'REVI') && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Revisor</span>
                                    <span className="font-medium text-foreground">{roles.revisor}</span>
                                </li>
                            )}
                            {party.created_at && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Opprettet</span>
                                    <span className="font-medium text-foreground font-mono text-sm">{new Date(party.created_at).toLocaleDateString('nb-NO')}</span>
                                </li>
                            )}
                            {party.updated_at && (
                                <li className="flex items-start">
                                    <span className="w-40 font-bold text-label pt-1 text-muted-foreground">Sist oppdatert</span>
                                    <span className="font-medium text-foreground font-mono text-sm">{new Date(party.updated_at).toLocaleDateString('nb-NO')}</span>
                                </li>
                            )}
                        </ul>

                        {/* Vedtektsfestet formål og aktivitet */}
                        {((brreg.vedtektsfestetFormaal && brreg.vedtektsfestetFormaal.length > 0) || (brreg.aktivitet && brreg.aktivitet.length > 0)) && (
                            <div className="mt-6 space-y-3">
                                {brreg.vedtektsfestetFormaal && brreg.vedtektsfestetFormaal.length > 0 && (
                                    <div>
                                        <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Vedtektsfestet formål</div>
                                        <p className="text-sm text-foreground leading-relaxed">{Array.isArray(brreg.vedtektsfestetFormaal) ? brreg.vedtektsfestetFormaal.join(' ') : brreg.vedtektsfestetFormaal}</p>
                                    </div>
                                )}
                                {brreg.aktivitet && brreg.aktivitet.length > 0 && (
                                    <div>
                                        <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Aktivitet</div>
                                        <p className="text-sm text-foreground leading-relaxed">{Array.isArray(brreg.aktivitet) ? brreg.aktivitet.join(' ') : brreg.aktivitet}</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Styreroller fra brreg_roller */}
                        {brregRoller.length > 0 && (
                            <div className="mt-6">
                                <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">Styre og roller (BRREG)</div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    {brregRoller.map((r: any, i: number) => (
                                        <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-surface/40 border border-border">
                                            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${r.type_kode === 'DAGL' ? 'bg-emerald-500' : r.type_kode === 'LEDE' ? 'bg-purple-500' : r.type_kode === 'REGN' ? 'bg-blue-500' : r.type_kode === 'REVI' ? 'bg-amber-500' : 'bg-muted'}`} />
                                            <div className="min-w-0">
                                                <div className="text-sm font-medium text-foreground truncate">{r.navn || r.organisasjonsnummer || '—'}</div>
                                                <div className="text-[10px] text-muted-foreground uppercase tracking-wider">{r.rolletype}{r.type_kode ? ` · ${r.type_kode}` : ''}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {hasOrgnr && (
                            <div className="mt-10">
                                <CompanyFinancials orgNr={party.orgnr} companyName={party.name} />
                            </div>
                        )}

                        {hasOrgnr && (
                            <div className="mt-10 flex flex-wrap items-center gap-3">
                                <button
                                    type="button"
                                    onClick={onEnrichBrreg}
                                    disabled={fetchingBrreg}
                                    className="px-4 py-2 rounded-lg bg-slate-500/10 text-slate-700 dark:text-slate-300 border border-slate-500/20 hover:bg-slate-500/20 disabled:opacity-50 text-sm font-medium"
                                >
                                    {fetchingBrreg ? 'Henter BRREG-data…' : isBrreg ? 'Oppdater BRREG-data' : 'Hent BRREG-data'}
                                </button>
                                <button
                                    type="button"
                                    onClick={onFetchCompanySummary}
                                    disabled={fetchingSummary}
                                    className="px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 disabled:opacity-50 text-sm font-medium"
                                >
                                    {fetchingSummary ? 'Henter fra nettet…' : openaiSummary ? 'Oppdater firmaoppsummering fra nettet' : 'Hent firmaoppsummering fra nettet'}
                                </button>
                                <button
                                    type="button"
                                    onClick={onRunDueDiligence}
                                    disabled={fetchingDD}
                                    className="px-4 py-2 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 disabled:opacity-50 text-sm font-medium"
                                >
                                    {fetchingDD ? 'Kjører risikovurdering…' : ddReport ? 'Oppdater risikovurdering (Due Diligence)' : 'Kjør risikovurdering (Due Diligence)'}
                                </button>
                                <button
                                    type="button"
                                    onClick={onRunKonkursCheck}
                                    disabled={fetchingKonkurs}
                                    className="px-4 py-2 rounded-lg bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 hover:bg-red-500/20 disabled:opacity-50 text-sm font-medium"
                                >
                                    {fetchingKonkurs ? 'Sjekker…' : 'Kjør konkurssjekk'}
                                </button>
                                <button
                                    type="button"
                                    onClick={onRunMediaMonitor}
                                    disabled={fetchingMedia}
                                    className="px-4 py-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 disabled:opacity-50 text-sm font-medium"
                                >
                                    {fetchingMedia ? 'Søker nyheter…' : 'Kjør media monitor'}
                                </button>
                                {brregError && <p className="text-rose-500 text-sm">{brregError}</p>}
                                {summaryError && <p className="text-rose-500 text-sm">{summaryError}</p>}
                                {ddError && <p className="text-rose-500 text-sm">{ddError}</p>}
                                {konkursError && <p className="text-rose-500 text-sm">{konkursError}</p>}
                                {mediaError && <p className="text-rose-500 text-sm">{mediaError}</p>}
                            </div>
                        )}
                        {openaiSummary && (
                            <div className="mt-10 p-6 bg-linear-to-r from-amber-500/5 to-orange-500/5 rounded-xl border border-amber-500/20">
                                <h3 className="font-bold text-amber-600 dark:text-amber-400 mb-3 flex items-center gap-2">
                                    <span className="w-2 h-2 bg-amber-500 rounded-full"></span>
                                    Firmaoppsummering (AI)
                                </h3>
                                <div className="text-muted-foreground text-sm whitespace-pre-line leading-relaxed">{openaiSummary}</div>
                            </div>
                        )}

                        {ddReport && (
                            <div className="mt-10 p-6 rounded-xl border relative overflow-hidden bg-linear-to-r from-slate-500/5 to-slate-600/5 border-slate-500/20">
                                <div className="flex items-center justify-between gap-4 mb-4">
                                    <h3 className="font-bold text-foreground flex items-center gap-2">
                                        <span
                                            className={`w-3 h-3 rounded-full ${ddReport.risk_level === 'LAV' ? 'bg-emerald-500' :
                                                ddReport.risk_level === 'HØY' ? 'bg-rose-500' : 'bg-amber-500'
                                                }`}
                                            title={`Risikonivå: ${ddReport.risk_level}`}
                                        />
                                        Risikovurdering (Due Diligence)
                                    </h3>
                                    {ddReport.assessed_at && (
                                        <span className="text-xs text-muted-foreground">
                                            Sist vurdert: {new Date(ddReport.assessed_at).toLocaleDateString('nb-NO')}
                                        </span>
                                    )}
                                </div>
                                <p className="text-muted-foreground text-sm mb-4">{ddReport.summary}</p>
                                {ddReport.red_flags && ddReport.red_flags.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-rose-600 dark:text-rose-400 text-sm mb-2">Røde flagg</h4>
                                        <ul className="list-disc list-inside text-sm text-foreground space-y-1">
                                            {ddReport.red_flags.map((f: string, i: number) => (
                                                <li key={i}>{f}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {ddReport.detailed_analysis && Object.values(ddReport.detailed_analysis).some(Boolean) && (
                                    <div className="mb-4 space-y-2">
                                        <h4 className="font-semibold text-foreground text-sm mb-2">Detaljert analyse</h4>
                                        {ddReport.detailed_analysis.okonomi && (
                                            <details className="group">
                                                <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">Økonomi</summary>
                                                <p className="mt-1 text-sm text-muted-foreground pl-4">{ddReport.detailed_analysis.okonomi}</p>
                                            </details>
                                        )}
                                        {ddReport.detailed_analysis.juridisk && (
                                            <details className="group">
                                                <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">Juridisk</summary>
                                                <p className="mt-1 text-sm text-muted-foreground pl-4">{ddReport.detailed_analysis.juridisk}</p>
                                            </details>
                                        )}
                                        {(ddReport.detailed_analysis as Record<string, string>).omdømme && (
                                            <details className="group">
                                                <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">Omdømme</summary>
                                                <p className="mt-1 text-sm text-muted-foreground pl-4">{(ddReport.detailed_analysis as Record<string, string>).omdømme}</p>
                                            </details>
                                        )}
                                    </div>
                                )}
                                {ddReport.follow_up_questions && ddReport.follow_up_questions.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-primary text-sm mb-2">Anbefalte oppfølgingsspørsmål</h4>
                                        <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                                            {ddReport.follow_up_questions.map((q: string, i: number) => (
                                                <li key={i}>{q}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {ddReport.sources && ddReport.sources.length > 0 && (
                                    <div>
                                        <h4 className="font-semibold text-muted-foreground text-sm mb-2">Kilder</h4>
                                        <ul className="space-y-1">
                                            {ddReport.sources.map((s: { url?: string; title?: string }, i: number) => (
                                                <li key={i}>
                                                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">
                                                        {s.title || s.url || 'Kilde'}
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Media Overvåkning – sentiment fra nyhetssøk (vises når kjørt) */}
                        {party.external_data?.media_monitoring && (
                            <div className="mt-10 p-6 rounded-xl border relative overflow-hidden bg-linear-to-r from-blue-500/5 to-indigo-500/5 border-blue-500/20">
                                <div className="flex items-center justify-between gap-4 mb-4">
                                    <h3 className="font-bold text-foreground flex items-center gap-2">
                                        <span
                                            className={`w-3 h-3 rounded-full ${
                                                (party.external_data.media_monitoring.sentiment_score ?? 5) <= 3 ? 'bg-red-500' :
                                                (party.external_data.media_monitoring.sentiment_score ?? 5) <= 5 ? 'bg-amber-500' : 'bg-emerald-500'
                                            }`}
                                            title={`Sentiment: ${party.external_data.media_monitoring.sentiment_score ?? 5}/10`}
                                        />
                                        Media Overvåkning
                                    </h3>
                                    {party.external_data.media_monitoring.last_updated && (
                                        <span className="text-xs text-muted-foreground">
                                            Sist sjekket: {new Date(party.external_data.media_monitoring.last_updated).toLocaleString('nb-NO')}
                                        </span>
                                    )}
                                </div>
                                <p className="text-muted-foreground text-sm mb-4">{party.external_data.media_monitoring.summary}</p>
                                {party.external_data.media_monitoring.red_flags?.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-rose-600 dark:text-rose-400 text-sm mb-2">Røde flagg</h4>
                                        <ul className="list-disc list-inside text-sm text-foreground space-y-1">
                                            {party.external_data.media_monitoring.red_flags.map((f: string, i: number) => (
                                                <li key={i}>{f}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {party.external_data.media_monitoring.positive_news?.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-emerald-600 dark:text-emerald-400 text-sm mb-2">Positivt</h4>
                                        <ul className="list-disc list-inside text-sm text-foreground space-y-1">
                                            {party.external_data.media_monitoring.positive_news.map((n: string, i: number) => (
                                                <li key={i}>{n}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                <div className="text-xs text-muted-foreground">
                                    {party.external_data.media_monitoring.sources_checked ?? 0} kilder sjekket · Score: {(party.external_data.media_monitoring.sentiment_score ?? 5).toFixed(1)}/10 ({party.external_data.media_monitoring.sentiment_label ?? 'Nøytralt'})
                                </div>
                            </div>
                        )}

                        <div className="mt-10 p-6 bg-linear-to-r from-blue-500/5 to-purple-500/5 rounded-xl border border-blue-500/20 relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="font-bold text-primary mb-2 flex items-center shadow-blue-500/50">
                                <span className="w-2 h-2 bg-primary rounded-full mr-2 shadow-[0_0_10px_rgba(96,165,250,0.8)]"></span>
                                Smart Insight
                            </h3>
                            <p className="text-muted-foreground text-sm leading-relaxed max-w-2xl">
                                {isBrreg ? (
                                    <>Denne parten er en verifisert leietaker med <strong className="text-emerald-600 dark:text-emerald-400">Grade A</strong> kredittvurdering. De har <strong className="text-foreground">{party.active_contract_count ?? 0}</strong> aktiv{party.active_contract_count === 1 ? '' : 'e'} leieavtale{party.active_contract_count === 1 ? '' : 'r'} i porteføljen.</>
                                ) : (
                                    <>Denne parten har <strong className="text-foreground">{party.active_contract_count ?? 0}</strong> aktiv{party.active_contract_count === 1 ? '' : 'e'} leieavtale{party.active_contract_count === 1 ? '' : 'r'} i porteføljen. For å vise verifisert BRREG-data og kontaktinfo, kjør BRREG-berikelse for partier med orgnr.</>
                                )}
                            </p>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
