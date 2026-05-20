import { Metadata } from 'next';
import Link from 'next/link';
import {
    Wrench, ShieldCheck, FileText, ClipboardList, AlertTriangle,
    Building2, BookOpen, CheckCircle2, Clock, BarChart3, Leaf,
    ArrowRight, Info, Layers, Zap,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const metadata: Metadata = { title: 'Om FDVU – Forvaltning, Drift, Vedlikehold og Utvikling' };

const FDUV_PHASES = [
    {
        letter: 'F',
        title: 'Forvaltning',
        color: 'text-blue-400',
        bg: 'bg-blue-500/10 border-blue-500/20',
        icon: Building2,
        desc: 'Strategisk eiendomsstyring — eierskap, økonomi, juridiske forpliktelser og langtidsplanlegging.',
        examples: ['Budsjett og økonomiplan', 'Leiekontrakter og avtaler', 'Forsikring og risikostyring', 'Areal- og kapasitetsplanlegging'],
    },
    {
        letter: 'D',
        title: 'Drift',
        color: 'text-green-400',
        bg: 'bg-green-500/10 border-green-500/20',
        icon: Zap,
        desc: 'Daglig og løpende drift av bygninger og tekniske anlegg for å opprettholde funksjonalitet.',
        examples: ['Renhold og vaktmestertjenester', 'Energistyring og -overvåking', 'Drift av VVS, ventilasjon og elektro', 'Serviceavtaler og leverandørstyring'],
    },
    {
        letter: 'V',
        title: 'Vedlikehold',
        color: 'text-orange-400',
        bg: 'bg-orange-500/10 border-orange-500/20',
        icon: Wrench,
        desc: 'Planlagt og korrektivt vedlikehold for å bevare bygningens verdi og teknisk standard.',
        examples: ['Tilstandsanalyser (TG0–TG3)', 'Vedlikeholdsplaner og arbeidsordrer', 'Utskiftning av bygningskomponenter', 'Periodisk kontroll og inspeksjon'],
    },
    {
        letter: 'U',
        title: 'Utvikling',
        color: 'text-purple-400',
        bg: 'bg-purple-500/10 border-purple-500/20',
        icon: BarChart3,
        desc: 'Forbedring og oppgradering av eiendommer for å øke verdi, funksjon og bærekraft.',
        examples: ['Rehabilitering og ombygning', 'Energioppgradering (ENØK)', 'Tilpasning til nye krav (TEK17)', 'BIM-modellering og digitalisering'],
    },
];

const REGULATORY_FRAMEWORK = [
    { code: 'TEK17', label: 'TEK17 – Byggteknisk forskrift', desc: 'Minimumskrav til bygningsteknisk utførelse, energi, brann og universell utforming.', color: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
    { code: 'RKL6', label: 'Risikoklasse 6 – Barnevernloven', desc: 'Strengeste brannsikkerhetskrav for institusjoner med overnattende beboere uten rømningsevne.', color: 'bg-red-500/15 text-red-300 border-red-500/30' },
    { code: 'HMS', label: 'HMS / Arbeidsmiljøloven', desc: 'Internkontrollforskriften — krav til systematisk helse-, miljø- og sikkerhetsarbeid.', color: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30' },
    { code: 'NS 3451', label: 'NS 3451 – Bygningsdelstabell', desc: 'Standardisert klassifisering av bygningskomponenter brukt i BEFS for kost- og tilstandskategorisering.', color: 'bg-green-500/15 text-green-300 border-green-500/30' },
    { code: 'BVL', label: 'Barnevernloven § 5-1', desc: 'Krav til fysiske rammer for statlige barneverninstitusjoner — areal, standard og sikkerhet.', color: 'bg-orange-500/15 text-orange-300 border-orange-500/30' },
    { code: 'ISO 55000', label: 'ISO 55000 – Asset Management', desc: 'Internasjonal standard for strategisk forvaltning av fysiske eiendeler over livsløpet.', color: 'bg-purple-500/15 text-purple-300 border-purple-500/30' },
];

const BEFS_FDVU_MODULES = [
    {
        title: 'Compliance-dashboard',
        href: '/fdvu',
        icon: ShieldCheck,
        desc: 'Porteføljeoversikt over kravoppfyllelse for alle eiendommer. Compliance-rate, avvik og forfalne revisjoner.',
        status: 'live',
    },
    {
        title: 'Kravkatalog',
        href: '/fdvu/krav',
        icon: BookOpen,
        desc: 'Alle gjeldende krav per regelverk (TEK17, RKL6, HMS, BVL). Filter på kategori og alvorlighetsgrad.',
        status: 'live',
    },
    {
        title: 'FDVU Avvik',
        href: '/fdvu/avvik',
        icon: AlertTriangle,
        desc: 'Registrerte avvik fra FDVU-kravene. Kobler compliance-avvik til HMS-avvikssystemet for felles oppfølging.',
        status: 'live',
    },
    {
        title: 'Tilstandsregistrering',
        href: '/fdvu',
        icon: Wrench,
        desc: 'Tilstandsgrader (TG0–TG3) per bygningskomponent basert på NS 3451-klassifisering.',
        status: 'live',
    },
    {
        title: 'FDV-dokumentasjon',
        href: '/fdvu',
        icon: FileText,
        desc: 'Strukturert dokumentbibliotek for tegninger, brukermanualer, servicerapporter og sertifikater.',
        status: 'live',
    },
    {
        title: 'Vedlikeholdsplan',
        href: '/fdvu',
        icon: ClipboardList,
        desc: 'Planlagte og utførte vedlikeholdsaktiviteter per eiendom med kostnads- og ressurssporing.',
        status: 'live',
    },
    {
        title: 'Arbeidsordrer',
        href: '/fdvu',
        icon: CheckCircle2,
        desc: 'Opprett og følg opp vedlikeholdsoppdrag internt eller mot leverandør. Integrasjon med kalender.',
        status: 'live',
    },
    {
        title: 'Miljødata',
        href: '/fdvu',
        icon: Leaf,
        desc: 'Energiforbruk, CO₂-utslipp og bærekraftsindikatorer per eiendom. Grunnlag for energirapportering.',
        status: 'live',
    },
    {
        title: 'BIM-vedlikehold',
        href: '/fdvu',
        icon: Layers,
        desc: 'Import og visualisering av IFC-modeller. Rombasert tilstandsregistrering og vedlikehold.',
        status: 'beta',
    },
];

const CONDITION_GRADES = [
    { grade: 'TG0', label: 'Ingen symptomer', desc: 'Bygningsdelen er i god stand. Ingen umiddelbare tiltak nødvendig.', color: 'bg-green-500/15 text-green-300 border-green-500/30' },
    { grade: 'TG1', label: 'Svake symptomer', desc: 'Normale alderstegn. Bør følges opp ved neste planlagte vedlikehold.', color: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30' },
    { grade: 'TG2', label: 'Middels symptomer', desc: 'Vesentlig forringelse. Tiltak bør planlegges innen 1–3 år.', color: 'bg-orange-500/15 text-orange-300 border-orange-500/30' },
    { grade: 'TG3', label: 'Kraftige symptomer', desc: 'Stor skade eller alvorlig risiko. Strakstiltak nødvendig.', color: 'bg-red-500/15 text-red-300 border-red-500/30' },
];

export default function OmFdvuPage() {
    return (
        <div className="p-6 space-y-10 max-w-5xl mx-auto pb-20">

            {/* ── Hero ── */}
            <div className="space-y-3">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                        <Wrench className="text-primary" size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">FDVU i BEFS</h1>
                        <p className="text-muted text-sm">Forvaltning, Drift, Vedlikehold og Utvikling</p>
                    </div>
                </div>
                <p className="text-foreground/80 text-sm leading-relaxed max-w-3xl">
                    FDVU er den norske standarden for eiendomsforvaltning gjennom et byggs livsløp.
                    I BEFS er FDVU-modulen et verktøy for systematisk oppfølging av Bufetats ~211 eiendommer
                    — fra daglig drift til langsiktig utvikling og dokumentasjon av lovpålagte krav.
                </p>
                <div className="flex gap-2 flex-wrap pt-1">
                    <Link href="/fdvu" className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90 transition-colors">
                        <ShieldCheck size={13} /> Åpne compliance-oversikt
                    </Link>
                    <Link href="/fdvu/avvik" className="flex items-center gap-1.5 px-3 py-1.5 bg-card border border-border rounded-lg text-xs font-medium text-foreground hover:bg-primary/5 transition-colors">
                        <AlertTriangle size={13} /> Se avvik
                    </Link>
                    <Link href="/fdvu/krav" className="flex items-center gap-1.5 px-3 py-1.5 bg-card border border-border rounded-lg text-xs font-medium text-foreground hover:bg-primary/5 transition-colors">
                        <BookOpen size={13} /> Kravkatalog
                    </Link>
                </div>
            </div>

            {/* ── De fire fasene ── */}
            <section className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <Info size={18} className="text-primary" /> Hva betyr F-D-V-U?
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {FDUV_PHASES.map(({ letter, title, color, bg, icon: Icon, desc, examples }) => (
                        <Card key={letter} className={`border ${bg}`}>
                            <CardHeader className="pb-2 pt-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-lg ${bg} border`}>
                                        <span className={color}>{letter}</span>
                                    </div>
                                    <div>
                                        <CardTitle className="text-base font-semibold flex items-center gap-2">
                                            <Icon size={15} className={color} />
                                            {title}
                                        </CardTitle>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-2 pb-4">
                                <p className="text-sm text-muted leading-relaxed">{desc}</p>
                                <ul className="space-y-1">
                                    {examples.map(ex => (
                                        <li key={ex} className="flex items-center gap-2 text-xs text-foreground/70">
                                            <CheckCircle2 size={11} className={color} />
                                            {ex}
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </section>

            {/* ── Tilstandsgrader ── */}
            <section className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <Wrench size={18} className="text-primary" /> Tilstandsgrader (TG) — NS 3600
                </h2>
                <p className="text-sm text-muted max-w-2xl">
                    BEFS bruker norsk standard for tilstandsbeskrivelse av bygningsdeler.
                    Tilstandsgrad settes ved inspeksjon og styrer prioritering av vedlikeholdsbudsjettet.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {CONDITION_GRADES.map(({ grade, label, desc, color }) => (
                        <div key={grade} className={`rounded-xl border p-3 ${color}`}>
                            <div className="text-lg font-bold mb-1">{grade}</div>
                            <div className="text-xs font-medium mb-1">{label}</div>
                            <div className="text-xs opacity-80 leading-relaxed">{desc}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Regelverk ── */}
            <section className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <ShieldCheck size={18} className="text-primary" /> Gjeldende regelverk og standarder
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {REGULATORY_FRAMEWORK.map(({ code, label, desc, color }) => (
                        <div key={code} className={`rounded-xl border p-3 ${color}`}>
                            <div className="flex items-center gap-2 mb-1">
                                <Badge className={`text-xs px-2 py-0 ${color}`}>{code}</Badge>
                            </div>
                            <div className="text-xs font-medium mb-1">{label}</div>
                            <div className="text-xs opacity-80 leading-relaxed">{desc}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── Moduler i BEFS ── */}
            <section className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <Layers size={18} className="text-primary" /> Moduler i BEFS-FDVU
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {BEFS_FDVU_MODULES.map(({ title, href, icon: Icon, desc, status }) => (
                        <Link key={title} href={href} className="group block">
                            <Card className="h-full border border-border hover:border-primary/40 hover:bg-primary/5 transition-all">
                                <CardContent className="pt-4 pb-4">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <Icon size={15} className="text-primary" />
                                            <span className="text-sm font-medium text-foreground">{title}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            {status === 'beta' && (
                                                <Badge variant="outline" className="text-[10px] px-1.5 py-0 text-warning border-warning/40">beta</Badge>
                                            )}
                                            <ArrowRight size={13} className="text-muted group-hover:text-primary transition-colors" />
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted leading-relaxed">{desc}</p>
                                </CardContent>
                            </Card>
                        </Link>
                    ))}
                </div>
            </section>

            {/* ── Dataflyt ── */}
            <section className="space-y-4">
                <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                    <BarChart3 size={18} className="text-primary" /> Hvordan data flyter i BEFS-FDVU
                </h2>
                <Card className="bg-card border-border">
                    <CardContent className="pt-5 pb-5">
                        <div className="space-y-3 text-sm">
                            {[
                                { step: '1', label: 'Eiendom registreres', desc: 'Adresse, region, type og areal legges inn. Avdelinger kobles til hovedeiendom.' },
                                { step: '2', label: 'Krav tildeles automatisk', desc: 'Basert på eiendomstype (barnevernsinstitusjon, kontor, bolig) genereres relevante FDVU-krav fra kravkatalogen (TEK17, RKL6, HMS, BVL).' },
                                { step: '3', label: 'Tilstandsinspeksjon', desc: 'Bygningskomponenter registreres med tilstandsgrad TG0–TG3 per NS 3451-kode. Danner grunnlag for vedlikeholdsplan.' },
                                { step: '4', label: 'Compliance-vurdering', desc: 'Hvert krav vurderes som Oppfylt / Delvis / Avvik / Ikke vurdert. KI-assistenten foreslår status basert på eiendomsdata.' },
                                { step: '5', label: 'Avvik følges opp', desc: 'Non-compliant krav genererer avvik med frist og ansvarlig. Avvik kobles til HMS-avvikssystemet for felles oppfølging.' },
                                { step: '6', label: 'Rapportering', desc: 'Porteføljeoverview, per-eiendom compliance-rapport og vedlikeholdslogg eksporteres til PDF/Excel.' },
                            ].map(({ step, label, desc }) => (
                                <div key={step} className="flex gap-3">
                                    <div className="w-6 h-6 rounded-full bg-primary/15 text-primary text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">{step}</div>
                                    <div>
                                        <div className="font-medium text-foreground text-sm">{label}</div>
                                        <div className="text-muted text-xs leading-relaxed">{desc}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* ── Kobling til HMS ── */}
            <section>
                <Card className="bg-primary/5 border-primary/20">
                    <CardContent className="pt-5 pb-5">
                        <div className="flex items-start gap-3">
                            <Info size={18} className="text-primary flex-shrink-0 mt-0.5" />
                            <div className="space-y-1">
                                <div className="text-sm font-semibold text-foreground">Kobling mellom FDVU og HMS</div>
                                <p className="text-xs text-muted leading-relaxed">
                                    FDVU og HMS deler avvikssystemet i BEFS. Tekniske avvik fra FDVU (f.eks. rømluftsanlegg ikke godkjent)
                                    registreres i FDVU-avvik og synkroniseres automatisk som HMS-avvik der HMS-kategori er relevant.
                                    Sjekklister for brannvern og risikoklasse 6 er felles for begge modulene.
                                </p>
                                <div className="flex gap-2 mt-3">
                                    <Link href="/deviations" className="flex items-center gap-1 text-xs text-primary hover:underline">
                                        <ArrowRight size={12} /> Se HMS-avvik
                                    </Link>
                                    <Link href="/checklists" className="flex items-center gap-1 text-xs text-primary hover:underline">
                                        <ArrowRight size={12} /> Sjekklister
                                    </Link>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* ── Footer nav ── */}
            <div className="flex items-center justify-between pt-2 border-t border-border">
                <Link href="/fdvu" className="flex items-center gap-1.5 text-sm text-muted hover:text-foreground transition-colors">
                    <Building2 size={14} /> Tilbake til FDVU-oversikt
                </Link>
                <Link href="/fdvu/krav" className="flex items-center gap-1.5 text-sm text-primary hover:text-primary/80 transition-colors">
                    Kravkatalog <ArrowRight size={14} />
                </Link>
            </div>
        </div>
    );
}
