import React, { useState, useMemo, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { getDPIA } from '../../lib/api/governanceApi';
import GlossaryComponent from './GlossaryComponent';
import {
    Shield,
    Database,
    Search,
    AlertTriangle,
    Lock,
    Eye,
    FileJson,
    Activity,
    Server,
    DollarSign,
    BrainCircuit,
    Building,
    Info,
    UserCheck,
    Scale,
    History,
    HardDrive,
    LucideIcon
} from 'lucide-react';

// --- DATA STRUCTURE ---
// Extended catalog with Governance Metadata: Owner, Retention, Source, Legal Basis

const RAW_DATA = [
    // --- IDENTITET & SIKKERHET (Identity) ---
    {
        name: 'users',
        domain: 'identity',
        risk: 3,
        desc: 'Kjernebrukere, passord og roller',
        owner: 'Frank Vevle',
        retention: 'Slettes 30 dager etter opphør av tilgang',
        source: 'Registrering / HR System',
        legal: 'GDPR Art. 6.1.b (Kontrakt)',
        columns: [
            { name: 'hashed_password', type: 'VARCHAR', level: 'Level 3: Restricted', description: 'Lagret passord i hash-format (Argon2).' },
            { name: 'email', type: 'VARCHAR', level: 'Level 3: Restricted (PII)', description: 'Unik brukeridentifikator.' },
            { name: 'mfa_enabled', type: 'BOOLEAN', level: 'Level 3: Restricted', description: 'Status for tofaktorautentisering.' }
        ]
    },
    {
        name: 'nextauth_accounts',
        domain: 'identity',
        risk: 3,
        desc: 'OAuth koblinger mot eksterne tilbydere',
        owner: 'Frank Vevle',
        retention: 'Løpende så lenge konto er aktiv',
        source: 'Google / Microsoft Entra ID',
        legal: 'GDPR Art. 6.1.a (Samtykke)',
        columns: [
            { name: 'access_token', type: 'TEXT', level: 'Level 3: Restricted', description: 'Opaque token for API-tilgang.' },
            { name: 'refresh_token', type: 'TEXT', level: 'Level 3: Restricted', description: 'Token for å fornye sesjon uten re-autentisering.' }
        ]
    },

    // --- ØKONOMI & FINANS (Finance) ---
    {
        name: 'contracts',
        domain: 'finance',
        risk: 3,
        desc: 'Leiekontrakter og betalingsbetingelser',
        owner: 'Frank Vevle',
        hasJson: true,
        retention: '10 år (Regnskapsloven)',
        source: 'Visma / Manuell registrering',
        legal: 'Regnskapsloven § 13',
        columns: [
            { name: 'amount', type: 'JSONB', level: 'Level 3: Mixed Content', description: 'Kompleks prisstruktur inkl. mva og justeringer.' },
            { name: 'caretaker_cost', type: 'DOUBLE', level: 'Level 3: Restricted', description: 'Andel felleskostnader vaktmester.' }
        ]
    },
    {
        name: 'suppliers',
        domain: 'finance',
        risk: 1,
        desc: 'Leverandørregister med kontaktinfo',
        owner: 'Frank Vevle',
        retention: '5 år etter siste transaksjon',
        source: 'Brønnøysundregistrene (API)',
        legal: 'Bokføringsloven',
        columns: [
            { name: 'name', type: 'TEXT', level: 'Level 2: Internal', description: 'Firmanavn.' },
            { name: 'orgnr', type: 'VARCHAR', level: 'Level 1: Public', description: 'Offentlig organisasjonsnummer.' }
        ]
    },

    // --- AI & DATA (AI) ---
    {
        name: 'query_logs',
        domain: 'ai',
        risk: 2,
        desc: 'Logg av brukerspørsmål til AI-assistenten',
        owner: 'Frank Vevle',
        retention: '90 dager (Anonymiseres deretter)',
        source: 'Søknadsplattform (Internt)',
        legal: 'GDPR Art. 6.1.f (Berettiget interesse)',
        columns: [
            { name: 'user_question', type: 'TEXT', level: 'Level 3: Restricted', description: 'Brukerens input-tekst (kan inneholde PII).' },
            { name: 'context_data', type: 'JSONB', level: 'Level 3: Mixed Content', description: 'Data hentet for RAG-kontekst.' }
        ]
    },
    {
        name: 'action_recommendations',
        domain: 'ai',
        risk: 1,
        desc: 'Anbefalinger generert av AI',
        owner: 'Frank Vevle',
        retention: '1 år',
        source: 'AI Inference Engine',
        legal: 'Ingen spesifikk (Driftsstøtte)',
        columns: [
            { name: 'ai_rationale', type: 'TEXT', level: 'Level 1: Internal', description: 'Forklaring på hvorfor tiltaket anbefales.' }
        ]
    },

    // --- SENSORER & IOT (IoT) ---
    {
        name: 'sensor_readings',
        domain: 'iot',
        risk: 1,
        desc: 'Tidsseriedata fra bygningssensorer',
        owner: 'Frank Vevle',
        retention: '3 år (Aggregeres deretter)',
        source: 'IoT Gateway / MQTT',
        legal: 'Avtale om eiendomsdrift',
        columns: [
            { name: 'value', type: 'DOUBLE', level: 'Level 1: Public', description: 'Måleverdi (Raw).' },
            { name: 'device_id', type: 'VARCHAR', level: 'Level 1: Internal', description: 'Unik ID for sensor.' }
        ]
    },

    // --- ANNET (Other) ---
    {
        name: 'audit_logs',
        domain: 'compliance',
        risk: 2,
        desc: 'Systemrevisjonsspor',
        owner: 'Frank Vevle',
        retention: 'uendelig (WORM Storage)',
        source: 'System Kernel',
        legal: 'GDPR Art. 32 (Sikkerhet)',
        columns: [
            { name: 'action', type: 'VARCHAR', level: 'Level 2: Internal', description: 'Type operasjon.' },
            { name: 'actor', type: 'VARCHAR', level: 'Level 2: Internal', description: 'Hvem utførte handlingen.' }
        ]
    }
];

const DOMAINS: Record<string, { label: string; icon: LucideIcon; color: string; bg: string }> = {
    identity: { label: 'Identitet & Tilgang', icon: Lock, color: 'text-red-600', bg: 'bg-red-50' },
    finance: { label: 'Økonomi', icon: DollarSign, color: 'text-amber-600', bg: 'bg-amber-50' },
    property: { label: 'Eiendom', icon: Building, color: 'text-blue-600', bg: 'bg-blue-50' },
    iot: { label: 'Sensorer & IoT', icon: Activity, color: 'text-cyan-600', bg: 'bg-cyan-50' },
    ai: { label: 'AI & Data', icon: BrainCircuit, color: 'text-purple-600', bg: 'bg-purple-50' },
    compliance: { label: 'Compliance & Logg', icon: Shield, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    other: { label: 'Annet / Tech', icon: Server, color: 'text-gray-600', bg: 'bg-gray-50' }
};

const RISK_LEVELS: Record<number, { label: string; color: string; icon: LucideIcon }> = {
    3: { label: 'Nivå 3: Restricted', color: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle },
    2: { label: 'Nivå 2: Internal', color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: Eye },

    1: { label: 'Nivå 1: Public/Internal', color: 'bg-green-100 text-green-800 border-green-200', icon: Database },
};

// --- DETAILED FINANCIAL MODELS ---
const FINANCIAL_MODELS = [
    {
        name: 'budget',
        description: 'Budsjetttall per eiendom og kategori (Årsbudsjett)',
        source: 'Xledger / Excel Import',
        fields: [
            { name: 'budget_id', type: 'UUID', description: 'Unik identifikator for budsjettposten.' },
            { name: 'property_id', type: 'UUID', description: 'Kobling mot eiendomstabellen.' },
            { name: 'year', type: 'INTEGER', description: 'Budsjettår (f.eks. 2025).' },
            { name: 'month', type: 'INTEGER', description: 'Måned (1-12).' },
            { name: 'category', type: 'VARCHAR', description: 'Standardisert kostnadskategori (e.g. "Strøm", "Vedlikehold").' },
            { name: 'amount', type: 'DECIMAL', description: 'Budsjettert beløp (NOK).' },
            { name: 'created_at', type: 'TIMESTAMP', description: 'Tidspunkt for opprettelse.' },
            { name: 'updated_at', type: 'TIMESTAMP', description: 'Sist oppdatert.' }
        ]
    },
    {
        name: 'gl_transactions',
        description: 'Hovedbokstransaksjoner (Faktiske kostnader)',
        source: 'Regnskapssystem (API)',
        fields: [
            { name: 'transaction_id', type: 'UUID', description: 'Unik ID.' },
            { name: 'property_id', type: 'UUID', description: 'Referanse til eiendom.' },
            { name: 'transaction_date', type: 'DATE', description: 'Bilagsdato.' },
            { name: 'year', type: 'INTEGER', description: 'Regnskapsår.' },
            { name: 'month', type: 'INTEGER', description: 'Regnskapsperiode (1-12).' },
            { name: 'amount', type: 'DECIMAL', description: 'Beløp (Eks. mva hvis spesifisert).' },
            { name: 'category', type: 'VARCHAR', description: 'Kostnadskategori (Standardisert).' },
            { name: 'account_code', type: 'VARCHAR', description: 'Hovedbokskonto (e.g. 6300).' },
            { name: 'vendor', type: 'VARCHAR', description: 'Leverandørnavn.' },
            { name: 'description', type: 'TEXT', description: 'Bilagstekst / Beskrivelse.' },
            { name: 'source_system', type: 'VARCHAR', description: 'Kildesystem (f.eks. "Visma", "Xledger").' }
        ]
    },
    {
        name: 'contracts',
        description: 'Leiekontrakter (Inntektsstrøm & Vilkår)',
        source: 'Forvaltningssystem',
        fields: [
            { name: 'contract_id', type: 'UUID', description: 'Unik kontrakt-ID.' },
            { name: 'status', type: 'ENUM', description: 'Status (active, terminated).' },
            { name: 'category', type: 'VARCHAR', description: 'Kontraktstype (Leie, Service, etc.).' },
            { name: 'start_date', type: 'DATE', description: 'Kontraktens startdato.' },
            { name: 'end_date', type: 'DATE', description: 'Utløpsdato (hvis tidsbestemt).' },

            // JSON Fields extracted
            { name: 'amount.amount_per_year', type: 'DECIMAL', description: 'Årlig leiebeløp (Beregnet/Import).' },
            { name: 'amount.monthly_rent', type: 'DECIMAL', description: 'Månedlig leie.' },
            { name: 'amount.total_per_year', type: 'DECIMAL', description: 'Alternativt felt for total årlig leie.' },

            // Options & Notifications
            { name: 'has_option', type: 'BOOLEAN', description: 'Har leietaker opsjon på forlengelse?' },
            { name: 'option_deadline', type: 'DATE', description: 'Frist for å melde opsjon.' },
            { name: 'option_count_total', type: 'INTEGER', description: 'Totalt antall opsjoner.' },
            { name: 'option_count_used', type: 'INTEGER', description: 'Antall opsjoner benyttet.' },

            // Legacy / Specific Costs
            { name: 'caretaker_cost', type: 'FLOAT', description: 'Vaktmesterkostnad (Legacy).' },
            { name: 'cleaning_cost', type: 'FLOAT', description: 'Renholdskostnad (Legacy).' },
            { name: 'parking_cost', type: 'FLOAT', description: 'Parkeringsleie (Legacy).' },
            { name: 'card_reader_cost', type: 'FLOAT', description: 'Kortleserkostnad.' },

            { name: 'signed_at', type: 'TIMESTAMP', description: 'Signeringstidspunkt.' },
            { name: 'terminated_at', type: 'TIMESTAMP', description: 'Oppsigelsestidspunkt.' }
        ]
    },
    {
        name: 'property_financials',
        description: 'Eiendomsspesifikke Data (JSON/External)',
        source: 'Beriket Data / Import',
        fields: [
            { name: 'external_data.financials.manual_expenses', type: 'ARRAY', description: 'Liste over manuelle utgifter.' },
            { name: 'manual_expenses[].amount', type: 'DECIMAL', description: 'Beløp på utgift.' },
            { name: 'manual_expenses[].type', type: 'VARCHAR', description: 'Utgiftstype (Kategori).' },
            { name: 'manual_expenses[].provider', type: 'VARCHAR', description: 'Leverandør for utgift.' },
            { name: 'manual_expenses[].date', type: 'DATE', description: 'Dato for utgift.' },
            { name: 'construction_year', type: 'INTEGER', description: 'Byggeår (Påvirker vedlikeholdskostnader).' },
            { name: 'energy_label', type: 'VARCHAR', description: 'Energimerking (A-G).' },
            { name: 'total_area', type: 'FLOAT', description: 'Totalt areal (kvm) for nøkkeltall.' }
        ]
    },
    {
        name: 'unit_economics',
        description: 'Enhetsøkonomi (Leieobjekter)',
        source: 'Core Domain',
        fields: [
            { name: 'unit_id', type: 'UUID', description: 'Unik ID for leieobjekt.' },
            { name: 'area_sqm', type: 'FLOAT', description: 'Areal på enheten.' },
            { name: 'purpose', type: 'VARCHAR', description: 'Formål (Kontor, Lager, etc.).' },
            { name: 'external_data.usage_type', type: 'VARCHAR', description: 'Detaljert brukstype for analyse.' }
        ]
    },
    {
        name: 'financial_kpis',
        description: 'Beregnete nøkkeltall (Derived Metrics)',
        source: 'Internal Analytics Engine (financial_analysis_service.py)',
        fields: [
            { name: 'cost_to_rent_ratio', type: 'FLOAT', description: 'Kostnadsprosent (Kostnader / Leieinntekter).' },
            { name: 'cost_per_sqm', type: 'FLOAT', description: 'Driftskostnad per kvadratmeter.' },
            { name: 'supplier_concentration', type: 'FLOAT', description: 'Andel kostnader til største leverandør (%).' },
            { name: 'price_variation_cv', type: 'FLOAT', description: 'Prisvariasjon hos samme leverandør (CV %).' },
            { name: 'risk_score_economic', type: 'INTEGER', description: 'Samlet økonomisk risikoscore.' },
            { name: 'budget_variance', type: 'FLOAT', description: 'Avvik mellom budsjett og regnskap (%).' }
        ]
    }
];

type Tab = 'catalog' | 'dpia' | 'glossary' | 'finance_detail';

export default function DataGovernanceDashboard() {
    const [activeTab, setActiveTab] = useState<Tab>('catalog');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedDomain, setSelectedDomain] = useState('all');
    const [selectedRisk, setSelectedRisk] = useState('all');
    const [selectedTable, setSelectedTable] = useState<typeof RAW_DATA[0] | null>(null);

    // DPIA State
    const [dpiaContent, setDpiaContent] = useState<string | null>(null);
    const [loadingDpia, setLoadingDpia] = useState(false);

    useEffect(() => {
        if (activeTab === 'dpia' && !dpiaContent && !loadingDpia) {
            const fetchDPIA = async () => {
                setLoadingDpia(true);
                try {
                    const article = await getDPIA();
                    setDpiaContent(article.content);
                } catch (err) {
                    console.error("Failed to fetch DPIA", err);
                    setDpiaContent("# DPIA Not Found\nCould not load the DPIA document.");
                } finally {
                    setLoadingDpia(false);
                }
            };
            fetchDPIA();
        }
    }, [activeTab, dpiaContent, loadingDpia]);

    // Use RAW_DATA for now (in real implementation, merge this with the big list)
    const filteredData = useMemo(() => {
        return RAW_DATA.filter(item => {
            const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                item.desc.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesDomain = selectedDomain === 'all' || item.domain === selectedDomain;
            const matchesRisk = selectedRisk === 'all' || String(item.risk) === selectedRisk;
            return matchesSearch && matchesDomain && matchesRisk;
        });
    }, [searchTerm, selectedDomain, selectedRisk]);

    return (
        <div className="min-h-screen bg-gray-50 text-slate-800 font-sans">
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-indigo-600 rounded-lg shadow-sm">
                                <Shield className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-gray-900 leading-tight">Data Governance Center</h1>
                                <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Classification & Compliance</p>
                            </div>
                        </div>

                        {/* Tab Navigation */}
                        <div className="flex bg-gray-100 p-1 rounded-lg">
                            <button
                                type="button"
                                onClick={() => setActiveTab('catalog')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'catalog'
                                    ? 'bg-white text-indigo-600 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Data Catalog
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('dpia')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'dpia'
                                    ? 'bg-white text-indigo-600 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                DPIA (Sikkerhetsanalyse)
                            </button>

                            <button
                                type="button"
                                onClick={() => setActiveTab('finance_detail')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'finance_detail'
                                    ? 'bg-white text-indigo-600 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Finansiell Oversikt
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab('glossary')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'glossary'
                                    ? 'bg-white text-indigo-600 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                Begrepskatalog
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {activeTab === 'finance_detail' ? (
                    <div className="space-y-8">
                        <div className="bg-linear-to-r from-slate-800 to-slate-900 rounded-xl p-8 text-white shadow-lg">
                            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                                <DollarSign className="w-8 h-8 text-emerald-400" />
                                Finansiell Datakatalog
                            </h2>
                            <p className="text-slate-300 max-w-3xl text-lg">
                                En komplett oversikt over alle økonomiske datafelt, modeller og beregningsgrunnlag i systemet.
                                Denne oversikten brukes for datavask, integrasjoner og kvalitetskurering.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {FINANCIAL_MODELS.map((model) => (
                                <div key={model.name} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col h-full">
                                    <div className="p-6 border-b border-gray-100 bg-gray-50/50">
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                                    <Database className="w-4 h-4 text-indigo-500" />
                                                    {model.name}
                                                </h3>
                                                <p className="text-sm text-gray-600 mt-1">{model.description}</p>
                                            </div>
                                            <span className="text-xs font-medium px-2 py-1 bg-white border border-gray-200 rounded text-gray-500">
                                                {model.source}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex-1 overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Feltnavn</th>
                                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Type</th>
                                                    <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Beskrivelse</th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {model.fields.map((field, idx) => (
                                                    <tr key={idx} className="hover:bg-gray-50/50 transition-colors">
                                                        <td className="px-6 py-3 whitespace-nowrap text-sm font-mono text-indigo-600">
                                                            {field.name}
                                                        </td>
                                                        <td className="px-6 py-3 whitespace-nowrap text-xs text-slate-500 font-mono">
                                                            {field.type}
                                                        </td>
                                                        <td className="px-6 py-3 text-sm text-gray-600">
                                                            {field.description}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : activeTab === 'glossary' ? (
                    <GlossaryComponent />
                ) : activeTab === 'catalog' ? (
                    <>
                        {/* Controls */}
                        <div className="mb-8 flex gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                                <input
                                    type="text"
                                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg bg-gray-50 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                                    placeholder="Søk etter tabell..."
                                    value={searchTerm}
                                    title="Søk etter tabell"
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                            <select
                                className="block w-48 pl-3 pr-10 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none"
                                value={selectedRisk}
                                title="Filtrer på risikonivå"
                                onChange={(e) => setSelectedRisk(e.target.value)}
                            >
                                <option value="all">Alle Risikonivåer</option>
                                <option value="3">Nivå 3: Restricted</option>
                                <option value="2">Nivå 2: Internal</option>
                                <option value="1">Nivå 1: Public</option>
                            </select>
                            <select
                                className="block w-48 pl-3 pr-10 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none"
                                value={selectedDomain}
                                title="Filtrer på domene"
                                onChange={(e) => setSelectedDomain(e.target.value)}
                            >
                                <option value="all">Alle Domener</option>
                                {Object.entries(DOMAINS).map(([key, val]) => (
                                    <option key={key} value={key}>{val.label}</option>
                                ))}
                            </select>
                        </div>

                        {/* Grid Layout */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">

                            {/* Main List */}
                            <div className={`${selectedTable ? 'md:col-span-8' : 'md:col-span-12'} transition-all`}>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {filteredData.map((table) => {
                                        const DomainIcon = DOMAINS[table.domain].icon;
                                        const riskStyle = RISK_LEVELS[table.risk];
                                        const isSelected = selectedTable?.name === table.name;

                                        return (
                                            <button
                                                type="button"
                                                key={table.name}
                                                onClick={() => setSelectedTable(isSelected ? null : table)}
                                                title={`Vis detaljer for ${table.name}`}
                                                className={`
                                relative flex flex-col items-start text-left w-full p-4 rounded-xl border transition-all duration-200
                                ${isSelected
                                                        ? 'bg-indigo-50 border-indigo-500 ring-1 ring-indigo-500 shadow-md'
                                                        : 'bg-white border-gray-200 hover:border-indigo-300 hover:shadow-md'}
                            `}
                                            >
                                                <div className="flex justify-between w-full mb-3">
                                                    <div className={`p-2 rounded-lg ${DOMAINS[table.domain].bg}`}>
                                                        <DomainIcon className={`w-5 h-5 ${DOMAINS[table.domain].color}`} />
                                                    </div>
                                                    {table.hasJson && (
                                                        <div className="p-1.5 bg-amber-50 rounded text-amber-600">
                                                            <FileJson className="w-4 h-4" />
                                                        </div>
                                                    )}
                                                </div>
                                                <h3 className="font-bold text-gray-900 mb-1">{table.name}</h3>
                                                <p className="text-xs text-gray-500 mb-4 h-8 overflow-hidden">{table.desc}</p>
                                                <div className="mt-auto w-full">
                                                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full border ${riskStyle.color}`}>
                                                        {riskStyle.label}
                                                    </span>
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Details Panel */}
                            {selectedTable && (
                                <div className="md:col-span-4 flex flex-col h-full sticky top-24">
                                    <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden animate-in slide-in-from-right-4">

                                        <div className="p-5 border-b border-gray-100 bg-gray-50/50">
                                            <div className="flex justify-between items-center mb-2">
                                                <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${RISK_LEVELS[selectedTable.risk].color}`}>
                                                    <AlertTriangle className="w-3 h-3" />
                                                    {RISK_LEVELS[selectedTable.risk].label}
                                                </div>
                                                <button
                                                    type="button"
                                                    onClick={() => setSelectedTable(null)}
                                                    className="text-gray-400 hover:text-gray-600"
                                                    title="Lukk detaljer"
                                                >
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                    <span className="sr-only">Lukk</span>
                                                </button>
                                            </div>
                                            <h2 className="text-xl font-bold text-gray-900">{selectedTable.name}</h2>
                                            <p className="text-sm text-gray-600 mt-1">{selectedTable.desc}</p>
                                        </div>

                                        {/* Metadata Grid */}
                                        <div className="grid grid-cols-2 gap-px bg-gray-200 border-b border-gray-200">
                                            <div className="bg-white p-3">
                                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                                    <UserCheck className="w-3 h-3" /> Eier/Ansvarlig
                                                </div>
                                                <div className="text-sm font-medium text-gray-900">{selectedTable.owner || 'Ikke definert'}</div>
                                            </div>
                                            <div className="bg-white p-3">
                                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                                    <History className="w-3 h-3" /> Lagringstid
                                                </div>
                                                <div className="text-sm font-medium text-gray-900">{selectedTable.retention || 'Standard'}</div>
                                            </div>
                                            <div className="bg-white p-3">
                                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                                    <HardDrive className="w-3 h-3" /> Kilde
                                                </div>
                                                <div className="text-sm font-medium text-gray-900">{selectedTable.source || 'Intern DB'}</div>
                                            </div>
                                            <div className="bg-white p-3">
                                                <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                                                    <Scale className="w-3 h-3" /> Lovhjemmel
                                                </div>
                                                <div className="text-sm font-medium text-gray-900">{selectedTable.legal || 'N/A'}</div>
                                            </div>
                                        </div>

                                        <div className="p-0 overflow-y-auto max-h-150">
                                            <ul className="divide-y divide-gray-100">
                                                {selectedTable.columns.map((col, idx: number) => (
                                                    <li key={idx} className="p-4 hover:bg-gray-50">
                                                        <div className="flex justify-between items-start mb-1">
                                                            <span className="font-mono text-sm font-semibold text-gray-800">{col.name}</span>
                                                            <span className="text-[10px] font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{col.type}</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5 mt-1">
                                                            <span className={`text-xs ${col.level.includes("Restricted") ? "text-red-600" : "text-gray-500"}`}>
                                                                {col.level}
                                                            </span>
                                                        </div>
                                                        {col.description && (
                                                            <div className="flex gap-2 text-xs text-gray-600 bg-gray-50/80 p-2 rounded border border-gray-100 mt-2">
                                                                <Info className="w-3 h-3 mt-0.5 text-gray-400 shrink-0" />
                                                                <span>{col.description}</span>
                                                            </div>
                                                        )}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 min-h-125">
                        {loadingDpia ? (
                            <div className="flex justify-center items-center h-48">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                            </div>
                        ) : (
                            <div className="prose prose-indigo max-w-none">
                                <ReactMarkdown
                                    components={{
                                        h1: ({ ...props }) => <h1 className="text-3xl font-bold text-gray-900 mb-6 pb-4 border-b border-gray-100" {...props} />,
                                        h2: ({ ...props }) => <h2 className="text-2xl font-bold text-gray-800 mt-8 mb-4" {...props} />,
                                        h3: ({ ...props }) => <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3" {...props} />,
                                        table: ({ ...props }) => <div className="overflow-x-auto my-6"><table className="min-w-full divide-y divide-gray-200 border border-gray-200" {...props} /></div>,
                                        th: ({ ...props }) => <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" {...props} />,
                                        td: ({ ...props }) => <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 border-t border-gray-100" {...props} />,
                                        blockquote: ({ ...props }) => <blockquote className="border-l-4 border-indigo-200 pl-4 py-2 italic text-gray-600 bg-indigo-50/30 rounded-r-lg" {...props} />,
                                    }}
                                >
                                    {dpiaContent || ''}
                                </ReactMarkdown>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
