"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    Building2, MapPin, Layers, ShieldCheck, Wrench,
    CheckCircle2, ChevronRight, ChevronLeft, Zap, Plus,
} from 'lucide-react';
import { fetchAPI } from '@/lib/api/client';
import { autoGenerateAssignments } from '@/lib/api/fdvuApi';
import { createMaintenancePlan } from '@/lib/api/maintenanceApi';

// ─────────────────────────────────────────────
// Steg-metadata
// ─────────────────────────────────────────────

const STEPS = [
    { id: 1, icon: <Building2 size={18} />, title: 'Eiendomsinfo',    desc: 'Navn og basisdata' },
    { id: 2, icon: <MapPin size={18} />,    title: 'Adresse',         desc: 'Lokasjon og region' },
    { id: 3, icon: <Layers size={18} />,    title: 'Seksjoner',       desc: 'Rom og avdelinger' },
    { id: 4, icon: <ShieldCheck size={18} />, title: 'Compliance',    desc: 'Auto-tildel krav' },
    { id: 5, icon: <Wrench size={18} />,    title: 'Vedlikehold',     desc: 'Startplaner' },
];

const PROPERTY_TYPES = [
    'barnevernsinstitusjon', 'familiesenter', 'kontorbygg',
    'omsorgsbolig', 'barnehage', 'annet',
];

const SECTION_TYPE_OPTIONS = ['boform', 'fellesareal', 'administrasjon', 'uteareal'];

const MAINTENANCE_TEMPLATES = [
    { title: 'Sjekk brannslukker og -varslere', category: 'legal', frequency_months: 12 },
    { title: 'Utvendig vedlikehold og inspeksjon', category: 'inspection', frequency_months: 12 },
    { title: 'Kontroll av ventilasjon og filter', category: 'preventive', frequency_months: 6 },
    { title: 'Månedlig rengjøring fellesarealer', category: 'cleaning', frequency_months: 1 },
];

// ─────────────────────────────────────────────
// Hjelpe-komponenter
// ─────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
    return (
        <div className="flex items-center gap-0 mb-8">
            {STEPS.map((step, i) => (
                <React.Fragment key={step.id}>
                    <div className={`flex flex-col items-center gap-1 ${i < STEPS.length - 1 ? 'flex-1' : ''}`}>
                        <div className={`w-9 h-9 rounded-full border-2 flex items-center justify-center transition-all ${
                            current > step.id ? 'bg-success border-success text-white' :
                            current === step.id ? 'bg-primary border-primary text-primary-foreground' :
                            'border-border text-muted bg-card'
                        }`}>
                            {current > step.id ? <CheckCircle2 size={16} /> : step.icon}
                        </div>
                        <span className={`text-[10px] font-medium hidden sm:block ${current === step.id ? 'text-primary' : 'text-muted'}`}>
                            {step.title}
                        </span>
                    </div>
                    {i < STEPS.length - 1 && (
                        <div className={`flex-1 h-0.5 mx-1 mb-4 transition-all ${current > step.id ? 'bg-success' : 'bg-border'}`} />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
}

// ─────────────────────────────────────────────
// Wizard
// ─────────────────────────────────────────────

export default function OnboardingPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [propertyId, setPropertyId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Steg 1 – Eiendomsinfo
    const [name, setName] = useState('');
    const [propertyType, setPropertyType] = useState('barnevernsinstitusjon');
    const [isBarnevern, setIsBarnevern] = useState(true);
    const [capacity, setCapacity] = useState('');

    // Steg 2 – Adresse
    const [address, setAddress] = useState('');
    const [postalCode, setPostalCode] = useState('');
    const [city, setCity] = useState('');
    const [region, setRegion] = useState('');

    // Steg 3 – Seksjoner
    const [sections, setSections] = useState([
        { name: 'Avdeling A', section_type: 'boform', area_sqm: '' },
    ]);

    // Steg 4 – Compliance (auto)
    const [complianceResult, setComplianceResult] = useState<{ created: number; skipped: number } | null>(null);

    // Steg 5 – Vedlikehold
    const [selectedTemplates, setSelectedTemplates] = useState<number[]>([0, 1, 2]);
    const [maintenanceResult, setMaintenanceResult] = useState<number | null>(null);

    // ── Navigasjon ──────────────────────────────

    const goNext = async () => {
        setError(null);
        if (step === 1) {
            if (!name.trim()) { setError('Navn er påkrevd'); return; }
            setStep(2);
        } else if (step === 2) {
            if (!address.trim()) { setError('Adresse er påkrevd'); return; }
            // Opprett eiendommen
            setLoading(true);
            try {
                const prop = await fetchAPI('/properties', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name,
                        address,
                        postal_code: postalCode,
                        city,
                        region: region || undefined,
                        property_type: propertyType,
                        is_barnevern: isBarnevern,
                        capacity: capacity ? +capacity : undefined,
                    }),
                }) as { property_id: string };
                setPropertyId(prop.property_id);
                setStep(3);
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Kunne ikke opprette eiendom');
            } finally { setLoading(false); }
        } else if (step === 3) {
            // Opprett seksjoner
            if (propertyId && sections.some(s => s.name.trim())) {
                setLoading(true);
                try {
                    for (const sec of sections.filter(s => s.name.trim())) {
                        await fetchAPI('/fdvu/sections', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                property_id: propertyId,
                                name: sec.name,
                                section_type: sec.section_type,
                                area_sqm: sec.area_sqm ? +sec.area_sqm : undefined,
                            }),
                        });
                    }
                } catch { /* seksjoner er valgfritt */ }
                finally { setLoading(false); }
            }
            setStep(4);
        } else if (step === 4) {
            // Auto-generer compliance-krav
            if (propertyId) {
                setLoading(true);
                try {
                    const res = await autoGenerateAssignments(propertyId);
                    setComplianceResult({ created: res.created, skipped: res.skipped_already_assigned });
                } catch { /* ikke kritisk */ }
                finally { setLoading(false); }
            }
            setStep(5);
        } else if (step === 5) {
            // Opprett valgte vedlikeholdsplaner
            if (propertyId) {
                setLoading(true);
                let created = 0;
                for (const idx of selectedTemplates) {
                    const tmpl = MAINTENANCE_TEMPLATES[idx];
                    try {
                        await createMaintenancePlan({
                            property_id: propertyId,
                            title: tmpl.title,
                            category: tmpl.category,
                            frequency_months: tmpl.frequency_months,
                            responsible_role: 'janitor',
                        });
                        created++;
                    } catch { /* continue */ }
                }
                setMaintenanceResult(created);
                setLoading(false);
            }
            // Ferdig
            router.push(propertyId ? `/fdvu/${propertyId}` : '/fdvu');
        }
    };

    const goBack = () => setStep(s => Math.max(1, s - 1));

    // ── Rendrer ──────────────────────────────────

    return (
        <div className="min-h-screen bg-background flex items-center justify-center p-6">
            <div className="w-full max-w-xl">
                {/* Topptekst */}
                <div className="mb-6 text-center">
                    <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center text-primary-foreground font-bold text-xl shadow-lg shadow-primary/20 mx-auto mb-3">B</div>
                    <h1 className="text-2xl font-bold text-foreground">Ny eiendom</h1>
                    <p className="text-muted text-sm mt-1">Guided oppsett — tar ca. 3 minutter</p>
                </div>

                <StepIndicator current={step} />

                {/* Steg-innhold */}
                <div className="bg-card border border-border rounded-2xl p-6 shadow-xl space-y-5">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            {STEPS[step - 1].icon}
                        </div>
                        <div>
                            <div className="font-semibold text-foreground text-sm">{STEPS[step - 1].title}</div>
                            <div className="text-xs text-muted">{STEPS[step - 1].desc}</div>
                        </div>
                        <span className="ml-auto text-xs text-muted">{step} / {STEPS.length}</span>
                    </div>

                    {/* ── Steg 1: Eiendomsinfo ── */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-muted font-medium">Navn på eiendom *</label>
                                <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                    value={name} onChange={e => setName(e.target.value)}
                                    placeholder="f.eks. Solheim barnevernsinstitusjon" autoFocus />
                            </div>
                            <div>
                                <label className="text-xs text-muted font-medium">Eiendomstype</label>
                                <div className="mt-1 grid grid-cols-2 gap-2">
                                    {PROPERTY_TYPES.map(t => (
                                        <button key={t} onClick={() => {
                                            setPropertyType(t);
                                            setIsBarnevern(t === 'barnevernsinstitusjon' || t === 'familiesenter');
                                        }}
                                            className={`px-3 py-2 rounded-lg border text-xs text-left capitalize transition-colors ${propertyType === t ? 'bg-primary/15 border-primary text-primary' : 'border-border text-muted hover:border-primary/40'}`}>
                                            {t}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-muted font-medium">Kapasitet (plasser)</label>
                                <input type="number" className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                    value={capacity} onChange={e => setCapacity(e.target.value)} placeholder="f.eks. 8" />
                            </div>
                        </div>
                    )}

                    {/* ── Steg 2: Adresse ── */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-muted font-medium">Gateadresse *</label>
                                <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                    value={address} onChange={e => setAddress(e.target.value)}
                                    placeholder="f.eks. Storgata 12" autoFocus />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-muted font-medium">Postnummer</label>
                                    <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                        value={postalCode} onChange={e => setPostalCode(e.target.value)} placeholder="0001" />
                                </div>
                                <div>
                                    <label className="text-xs text-muted font-medium">By</label>
                                    <input className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                        value={city} onChange={e => setCity(e.target.value)} placeholder="Oslo" />
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-muted font-medium">Region (Bufetat)</label>
                                <select className="mt-1 w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm text-foreground focus:outline-none focus:border-primary"
                                    value={region} onChange={e => setRegion(e.target.value)}>
                                    <option value="">Velg region</option>
                                    {['Øst', 'Vest', 'Sør', 'Midt', 'Nord'].map(r => (
                                        <option key={r} value={r}>Region {r}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}

                    {/* ── Steg 3: Seksjoner ── */}
                    {step === 3 && (
                        <div className="space-y-3">
                            <p className="text-xs text-muted">Legg til seksjoner/avdelinger (valgfritt — kan gjøres senere).</p>
                            {sections.map((sec, i) => (
                                <div key={i} className="flex gap-2 items-start">
                                    <div className="flex-1 space-y-2">
                                        <input
                                            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary"
                                            value={sec.name} onChange={e => setSections(ss => ss.map((s, j) => j === i ? { ...s, name: e.target.value } : s))}
                                            placeholder="Seksjonsnavn" />
                                        <div className="flex gap-2">
                                            <select
                                                className="flex-1 bg-background border border-border rounded-lg px-2 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary"
                                                value={sec.section_type} onChange={e => setSections(ss => ss.map((s, j) => j === i ? { ...s, section_type: e.target.value } : s))}>
                                                {SECTION_TYPE_OPTIONS.map(t => <option key={t} value={t}>{t}</option>)}
                                            </select>
                                            <input type="number" placeholder="m²"
                                                className="w-20 bg-background border border-border rounded-lg px-2 py-1.5 text-xs text-foreground focus:outline-none focus:border-primary"
                                                value={sec.area_sqm} onChange={e => setSections(ss => ss.map((s, j) => j === i ? { ...s, area_sqm: e.target.value } : s))} />
                                        </div>
                                    </div>
                                    {sections.length > 1 && (
                                        <button onClick={() => setSections(ss => ss.filter((_, j) => j !== i))}
                                            className="text-muted hover:text-destructive text-xs pt-2">✕</button>
                                    )}
                                </div>
                            ))}
                            <button onClick={() => setSections(ss => [...ss, { name: '', section_type: 'boform', area_sqm: '' }])}
                                className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors">
                                <Plus size={13} /> Legg til seksjon
                            </button>
                        </div>
                    )}

                    {/* ── Steg 4: Compliance ── */}
                    {step === 4 && (
                        <div className="space-y-4">
                            <div className="bg-primary/5 border border-primary/20 rounded-xl p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <Zap size={16} className="text-primary" />
                                    <span className="text-sm font-semibold text-primary">Auto-tildeling av krav</span>
                                </div>
                                <p className="text-xs text-muted leading-relaxed">
                                    BEFS tildeler automatisk relevante krav fra {isBarnevern ? 'RKL6, BVL, Kvalitetsforskriften, TEK17 og HMS' : 'TEK17 og HMS'} basert på eiendomstypen.
                                    {isBarnevern && <span className="text-primary font-medium"> Som barnevernsinstitusjon aktiveres alle Bufetat-spesifikke krav.</span>}
                                </p>
                            </div>
                            <p className="text-xs text-muted">Klikk «Neste» for å kjøre auto-tildeling. Du kan justere krav individuelt etterpå.</p>
                            {complianceResult && (
                                <div className="flex items-center gap-2 text-xs text-success bg-success/10 border border-success/20 rounded-lg px-3 py-2">
                                    <CheckCircle2 size={13} />
                                    {complianceResult.created} krav tildelt, {complianceResult.skipped} allerede tildelt.
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Steg 5: Vedlikehold ── */}
                    {step === 5 && (
                        <div className="space-y-3">
                            <p className="text-xs text-muted">Velg startplaner for vedlikehold (genereres automatisk for 12 måneder fremover):</p>
                            {MAINTENANCE_TEMPLATES.map((tmpl, i) => (
                                <label key={i} className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selectedTemplates.includes(i) ? 'border-primary/40 bg-primary/5' : 'border-border hover:border-primary/20'}`}>
                                    <input type="checkbox" className="mt-0.5 accent-primary"
                                        checked={selectedTemplates.includes(i)}
                                        onChange={() => setSelectedTemplates(ss => ss.includes(i) ? ss.filter(x => x !== i) : [...ss, i])} />
                                    <div>
                                        <div className="text-sm font-medium text-foreground">{tmpl.title}</div>
                                        <div className="text-xs text-muted">{tmpl.frequency_months === 1 ? 'Månedlig' : tmpl.frequency_months === 6 ? 'Halvårlig' : 'Årlig'} · {tmpl.category}</div>
                                    </div>
                                </label>
                            ))}
                            {maintenanceResult !== null && (
                                <div className="flex items-center gap-2 text-xs text-success bg-success/10 border border-success/20 rounded-lg px-3 py-2">
                                    <CheckCircle2 size={13} /> {maintenanceResult} vedlikeholdsplaner opprettet.
                                </div>
                            )}
                        </div>
                    )}

                    {error && <p className="text-destructive text-xs">{error}</p>}

                    {/* Navigasjonsknapper */}
                    <div className="flex gap-2 justify-between pt-2">
                        <button onClick={goBack} disabled={step === 1}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-border text-sm text-muted hover:text-foreground transition-colors disabled:opacity-30">
                            <ChevronLeft size={15} /> Tilbake
                        </button>
                        <button onClick={goNext} disabled={loading}
                            className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
                            {loading ? 'Lagrer …' : step === STEPS.length ? (
                                <><CheckCircle2 size={15} /> Fullfør oppsett</>
                            ) : (
                                <>Neste <ChevronRight size={15} /></>
                            )}
                        </button>
                    </div>
                </div>

                {/* Fremgang-tekst */}
                <p className="text-center text-xs text-muted mt-4">
                    Steg {step} av {STEPS.length} · {Math.round((step / STEPS.length) * 100)}% ferdig
                </p>
            </div>
        </div>
    );
}
