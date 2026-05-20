"use client";
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { propertyService } from '@/lib/api';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import PropertyMap from '@/app/components/features/PropertyMap';
import AccessibilityStats from '@/app/components/features/AccessibilityStats';
import InternalControlWidget from '@/app/components/features/InternalControlWidget';
import AIInsightsWidget from '@/app/components/features/AIInsightsWidget';
import CostAnalysisWidget from '@/app/components/features/CostAnalysisWidget';
import PropertySteeringPanel from '@/app/components/features/PropertySteeringPanel';
import DataTooltip from '@/app/components/ui/DataTooltip';
import { getFinanceBudgetByProperty, type FinanceBudgetPropertyDetail } from '@/lib/api/financeBudgetApi';

const BUDGET_CATEGORY_LABELS: Record<string, string> = {
    property: "Eiendom-kostnader",
    operations: "Drift-kostnader",
    investment: "Investeringer",
    other: "Andre",
};

/** Unngår fast tittel «Barnevernsinstitusjon» når e-don2 sier f.eks. Familievernkontor. */
function resolveBufdirSectionTitle(property: { usage?: string | null; unit_type_derived?: string | null }): {
    title: string;
    conflictNote?: string;
} {
    const u = (property.usage || "").toLowerCase();
    const d = (property.unit_type_derived || "").toLowerCase();
    const fam =
        u.includes("familievern") ||
        u.includes("familievernkontor") ||
        d.includes("familievern") ||
        d.includes("familievernkontor");
    // Kun eksplisitt barnevernsinstitusjon (ikke «institusjonsavdeling» alene – kan gjelde annet virksomhetsområde)
    const bv = u.includes("barnevernsinstitusjon") || d.includes("barnevernsinstitusjon");
    if (fam && bv) {
        return {
            title: "Bufdir",
            conflictNote:
                "Datakildene sier ulike ting om type (familievern vs. barnevernsinstitusjon). Sjekk «Formål (utledet)» og Bufdir før du bruker dette formelt.",
        };
    }
    if (fam) return { title: "Familievernkontor (Bufdir)" };
    if (bv) return { title: "Barnevernsinstitusjon (Bufdir)" };
    return { title: "Bufdir" };
}

function formatBufdirPhoneDisplay(phone: string): string {
    const d = phone.replace(/\D/g, "");
    if (d.length === 8) {
        return `${d.slice(0, 3)} ${d.slice(3, 5)} ${d.slice(5, 8)}`;
    }
    return phone;
}

function bufdirHtmlToPlainText(html: string): string {
    if (!html) return "";
    return html
        .replace(/<script[\s\S]*?<\/script>/gi, "")
        .replace(/<style[\s\S]*?<\/style>/gi, "")
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/<\/p>/gi, "\n")
        .replace(/<\/div>/gi, "\n")
        .replace(/<\/h[1-6]>/gi, "\n")
        .replace(/<\/li>/gi, "\n")
        .replace(/<[^>]+>/g, " ")
        .replace(/&nbsp;/g, " ")
        .replace(/&amp;/g, "&")
        .replace(/&lt;/g, "<")
        .replace(/&gt;/g, ">")
        .replace(/\n{3,}/g, "\n\n")
        .replace(/[ \t]+/g, " ")
        .trim();
}

/** Viser økonomiavdelingens budsjett/regnskap per eiendom fra finance_budget-tabellen. */
function OkonomiFinansCard({ propertyId }: { propertyId: string }) {
    const [data2026, setData2026] = useState<FinanceBudgetPropertyDetail | null>(null);
    const [data2025, setData2025] = useState<FinanceBudgetPropertyDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        Promise.all([
            getFinanceBudgetByProperty(propertyId, 2026, 'finance_dept_2026'),
            getFinanceBudgetByProperty(propertyId, 2025, 'finance_dept_2025'),
        ]).then(([d26, d25]) => {
            setData2026(d26 && d26.total > 0 ? d26 : null);
            setData2025(d25 && d25.total > 0 ? d25 : null);
        }).finally(() => setLoading(false));
    }, [propertyId]);

    const fmt = (n: number) =>
        new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(n);

    const MONTH_NAMES = ['Jan','Feb','Mar','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Des'];

    // Aggregate monthly data to month-level summary
    const monthlyByMonth2026: Record<number, number> = {};
    (data2026?.monthly ?? []).forEach(m => {
        monthlyByMonth2026[m.month] = (monthlyByMonth2026[m.month] ?? 0) + m.amount;
    });

    const hasAnyData = data2026 || data2025;

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-6"
        >
            <h3 className="font-bold flex items-center gap-2 mb-4 text-foreground">
                <svg className="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Økonomidata (vedtatt)
            </h3>
            {loading ? (
                <div className="space-y-2">
                    <div className="h-6 bg-muted/30 rounded animate-pulse" />
                    <div className="h-4 bg-muted/20 rounded animate-pulse w-2/3" />
                </div>
            ) : !hasAnyData ? (
                <p className="text-xs text-muted">Ingen økonomidata registrert for denne eiendommen.</p>
            ) : (
                <div className="space-y-4">
                    {/* Summary row */}
                    <div className="flex flex-wrap gap-3">
                        {data2025 && (
                            <div className="flex-1 min-w-24 bg-teal-50 dark:bg-teal-900/20 rounded-lg p-3 border border-teal-200 dark:border-teal-800">
                                <div className="text-[10px] font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wider mb-1">Budsj. 2025</div>
                                <div className="text-base font-bold text-teal-700 dark:text-teal-300">{fmt(data2025.total)}</div>
                            </div>
                        )}
                        {data2026 && (
                            <div className="flex-1 min-w-24 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
                                <div className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1">Budsj. 2026</div>
                                <div className="text-base font-bold text-blue-700 dark:text-blue-300">{fmt(data2026.total)}</div>
                            </div>
                        )}
                    </div>

                    {/* Category breakdown for 2026 */}
                    {data2026 && Object.keys(data2026.by_category).length > 0 && (
                        <div>
                            <div className="text-[10px] font-bold text-muted uppercase tracking-wider mb-2">Kategorifordeling 2026 (Øk.)</div>
                            <div className="space-y-1">
                                {Object.entries(data2026.by_category)
                                    .sort(([,a],[,b]) => b - a)
                                    .map(([cat, amt]) => (
                                        <div key={cat} className="flex justify-between text-xs">
                                            <span className="text-muted-foreground truncate mr-2">{cat}</span>
                                            <span className="font-mono text-foreground shrink-0">{fmt(amt)}</span>
                                        </div>
                                    ))}
                            </div>
                        </div>
                    )}

                    {/* Monthly distribution 2026 */}
                    {Object.keys(monthlyByMonth2026).length > 0 && (
                        <div>
                            <div className="text-[10px] font-bold text-muted uppercase tracking-wider mb-2">Månedlig budsjett 2026 (Øk.)</div>
                            <div className="grid grid-cols-6 gap-1">
                                {Array.from({ length: 12 }, (_, i) => i + 1).map(month => {
                                    const amt = monthlyByMonth2026[month] ?? 0;
                                    const maxAmt = Math.max(...Object.values(monthlyByMonth2026));
                                    const barH = maxAmt > 0 ? Math.round((amt / maxAmt) * 32) : 0;
                                    return (
                                        <div key={month} className="flex flex-col items-center gap-0.5">
                                            <div className="w-full flex items-end justify-center" style={{ height: 36 }}>
                                                {amt > 0 && (
                                                    <div
                                                        className="w-full bg-blue-400/60 dark:bg-blue-500/40 rounded-sm"
                                                        style={{ height: barH }}
                                                        title={`${MONTH_NAMES[month-1]}: ${fmt(amt)}`}
                                                    />
                                                )}
                                            </div>
                                            <div className="text-[9px] text-muted">{MONTH_NAMES[month-1]}</div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </motion.div>
    );
}

export default function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = React.use(params);
    const [detailView, setDetailView] = useState<any>(null);
    const [proximityServices, setProximityServices] = useState<any[]>([]);
    const [proximityRefreshing, setProximityRefreshing] = useState(false);
    const [proximityRefreshKey, setProximityRefreshKey] = useState(0);
    const [loading, setLoading] = useState(true);
    const [costYear, setCostYear] = useState<number | null>(null);
    const [availableCostYears, setAvailableCostYears] = useState<number[]>([]);
    const [costStatusLoading, setCostStatusLoading] = useState(false);
    const [hasCostsForYear, setHasCostsForYear] = useState<boolean | null>(null);
    const [costTotals, setCostTotals] = useState<{ total: number; rent: number; other: number } | null>(null);
    const [expensesExpanded, setExpensesExpanded] = useState(true);
    const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
    const [expandedContentSections, setExpandedContentSections] = useState<Record<number, boolean>>({});
    const [bufdirSlide, setBufdirSlide] = useState(0);

    useEffect(() => {
        setBufdirSlide(0);
    }, [id]);

    useEffect(() => {
        // 1. Først kun GET /properties/{id} – vis eiendom med en gang hvis den finnes
        propertyService.fetch(id)
            .then(property => {
                setDetailView({
                    property,
                    units: [],
                    contracts: [],
                    parties: [],
                    latest_risk_assessment: null
                });
                setLoading(false);
                // 2. Hent utvidet data i bakgrunnen (ikke blokker visning)
                propertyService.getDetailView(id, true)
                    .then(data => {
                        if (data?.property) setDetailView(data);
                        return propertyService.getProximityServices(id);
                    })
                    .then(services => setProximityServices(services || []))
                    .catch(() => { /* stille – vi har allerede vist eiendom */ });
            })
            .catch(err => {
                console.error("Error loading property:", err);
                setLoading(false);
            });
    }, [id]);

    const { property, units, contracts, parties, latest_risk_assessment } = detailView || {};

    useEffect(() => {
        const g = property?.external_data?.bufdir?.gallery;
        const n = Array.isArray(g) ? g.length : 0;
        if (n === 0) {
            setBufdirSlide(0);
            return;
        }
        setBufdirSlide((s) => Math.min(s, n - 1));
    }, [property?.external_data?.bufdir?.gallery, property?.property_id]);

    const validActiveContracts = (contracts?.filter((c: any) => c.status === 'active' && !!c.party_id) || []);
    const hasUnits = (units?.length || 0) > 0;
    const hasTenants = (parties?.length || 0) > 0;

    const handleRefreshProximity = () => {
        if (!property?.property_id || proximityRefreshing) return;
        setProximityRefreshing(true);
        propertyService.refreshProximityServices(property.property_id, true)
            .then(({ services }) => {
                setProximityServices(services || []);
                setProximityRefreshKey(k => k + 1);
            })
            .catch(() => { })
            .finally(() => setProximityRefreshing(false));
    };

    useEffect(() => {
        // Alltid bruk 2026 — økonomiavd. regnskap er eneste kilde
        setAvailableCostYears([2026]);
        setCostYear(2026);
    }, [property?.property_id]);

    useEffect(() => {
        if (!property?.property_id) {
            setHasCostsForYear(null);
            setCostTotals(null);
            return;
        }

        setCostStatusLoading(true);
        getFinanceBudgetByProperty(property.property_id, 2026, 'finance_dept_2026')
            .then((detail) => {
                if (!detail || detail.total === 0) {
                    setHasCostsForYear(false);
                    setCostTotals({ total: 0, rent: 0, other: 0 });
                    return;
                }
                const rent = Number(detail.by_category?.['Lokaler'] ?? 0);
                const drift = Number(detail.by_category?.['Drift'] ?? 0);
                const vedlikehold = Number(detail.by_category?.['Vedlikehold'] ?? 0);
                const other = drift + vedlikehold;
                const total = detail.total;
                setHasCostsForYear(total > 0);
                setCostTotals({ total, rent, other });
            })
            .catch(() => {
                setHasCostsForYear(false);
                setCostTotals({ total: 0, rent: 0, other: 0 });
            })
            .finally(() => setCostStatusLoading(false));
    }, [property?.property_id]);

    // Helper to group expenses by category – foretrekker GL-transaksjonsdata fremfor aggregerte JSONB-data
    const groupedExpenses = React.useMemo(() => {
        const glByCategory = property?.external_data?.financials?.gl_by_category || {};

        // Dersom GL-data finnes: bruk den (inneholder leverandør + beskrivelse per linje)
        if (Object.keys(glByCategory).length > 0) {
            const groups: Record<string, any[]> = {};
            for (const [catName, catData] of Object.entries(glByCategory as Record<string, any>)) {
                const lines: any[] = catData?.lines || [];
                if (lines.length > 0) {
                    groups[catName] = lines.map((line: any) => ({
                        description: line.description || '',
                        provider: line.supplier || 'Ukjent',
                        amount: line.amount,
                        amount_parsed: line.amount,
                        invoice: line.invoice,
                        period: line.period,
                        source: 'gl_transactions'
                    }));
                }
            }
            return groups;
        }

        // Fallback: bruk manual_expenses fra JSONB
        const expenses = property?.external_data?.financials?.manual_expenses || [];
        const groups: Record<string, any[]> = {};
        expenses.forEach((expense: any) => {
            const type = expense.account || expense.type || 'Annet';
            if (!groups[type]) groups[type] = [];
            groups[type].push(expense);
        });
        return groups;
    }, [property]);

    // Risk Analysis Calculations
    const { economicRiskScore, externalRiskScore, totalCosts, finalAnnualRent } = React.useMemo(() => {
        if (!property) return { economicRiskScore: 0, externalRiskScore: 0, totalCosts: 0, finalAnnualRent: 0 };

        // 1. Calculate Financials
        const activeContracts = contracts?.filter((c: any) => c.status === 'active' && !!c.party_id) || [];
        const totalRent = activeContracts.reduce((sum: number, c: any) =>
            sum + ((typeof c.amount === 'object' ? c.amount.amount_per_year : c.amount) || 0), 0
        );
        const syntheticRent = property.external_data?.financials?.rent_summary != null && property.external_data?.financials?.synthetic_rent_ytd;
        const finalAnnualRent = totalRent > 0 ? totalRent : (syntheticRent ? Number(property.external_data.financials.rent_summary) : 0);

        const fin = property.external_data?.financials || {};
        const totalCosts = Number(fin.total_maintenance) ||
            (Number(fin.total_manual_expenses) || 0) +
            (Number(fin.total_spend_csv) || 0);

        // 2. Economic Risk (Simplified Proxy: Cost/Rent Ratio)
        let ecoScore = 0;
        if (finalAnnualRent > 0) {
            const ratio = totalCosts / finalAnnualRent;
            if (ratio > 1.0) ecoScore += 40;
            else if (ratio > 0.8) ecoScore += 20;
        }

        // 3. External Risk
        const extFactors = latest_risk_assessment?.factors?.filter((f: any) => f.category === 'external') || [];
        const extScore = extFactors.reduce((sum: number, f: any) => sum + (f.calculated_score || 0), 0);

        return {
            economicRiskScore: Math.min(100, ecoScore),
            externalRiskScore: Math.min(100, extScore),
            totalCosts,
            finalAnnualRent
        };
    }, [property, contracts, latest_risk_assessment]);

    // FIX React Error #310: Moved conditional rendering inside return to ensure hooks always run.

    return (
        <div className="min-h-screen p-8 text-foreground">
            {loading ? (
                <div className="max-w-7xl mx-auto p-8 text-slate-600 dark:text-slate-400">Henter eiendomsdetaljer...</div>
            ) : (!detailView || !detailView.property) ? (
                <div className="max-w-7xl mx-auto p-8 text-red-400">Eiendom ikke funnet</div>
            ) : (
                <div className="max-w-7xl mx-auto">
                    <div className="mb-8 flex justify-between items-center">
                        <Link href="/properties" className="text-slate-600 dark:text-slate-400 hover:text-primary transition-colors flex items-center gap-2 font-medium">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-7-7a1 1 0 010-1.414l7-7a1 1 0 011.414 1.414L4.414 9H17a1 1 0 110 2H4.414l5.293 5.293a1 1 0 010 1.414z" clipRule="evenodd" />
                            </svg>
                            Tilbake til oversikt
                        </Link>
                        <div className="flex gap-3 flex-wrap">
                            <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-[10px] font-bold uppercase tracking-wider">
                                {property.usage?.toLowerCase() === 'barnevernsinstitusjon' ? 'Formålsbygg' : (property.usage || "Næringseiendom")}
                            </span>
                            <DataTooltip content="Syntetisk: Eiendomsdata er delvis generert eller estimert (f.eks. syntetisk leie fra areal/vedlikehold). Brukes for demo eller når faktiske data mangler.">
                                <span className="px-3 py-1 bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 rounded-full text-[10px] font-bold uppercase tracking-wider">
                                    Syntetisk
                                </span>
                            </DataTooltip>
                            <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full text-[10px] font-bold uppercase tracking-wider">
                                ID: {property.property_id.substring(0, 8)}
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Left & Center Columns: Main Info */}
                        <div className="lg:col-span-2 space-y-8">
                            {/* Header Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="glass-card p-8"
                            >
                                <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">{property.name || property.address}</h1>
                                <div className="flex flex-col gap-1">
                                    <p className="text-xl text-slate-600 dark:text-slate-400 flex items-center gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                                        </svg>
                                        {property.address}, {property.postal_code} {property.city}
                                    </p>
                                    {property.center_name && (
                                        <p className="text-sm text-primary font-medium flex items-center gap-2 mt-1">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                            </svg>
                                            Tilhører: {property.center_name}
                                        </p>
                                    )}
                                    {property.primary_lease_party_name && (
                                        <p className="text-sm text-muted-foreground mt-2">
                                            <span className="font-medium text-foreground/90">Kontraktsleverandør: </span>
                                            {property.primary_lease_party_name}
                                        </p>
                                    )}
                                </div>

                                <div className="mt-6">
                                    <AIInsightsWidget property={property} />
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-10 border-t border-border pt-8">
                                    <div>
                                        <DataTooltip content="Areal: Total bruttoareal for eiendommen i m². Kilde: Eiendomsregister eller masterdata.">
                                            <label className="text-label block mb-1">Areal</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">{property.total_area || "N/A"} m²</div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Byggeår: År da bygget ble ferdigstilt. Brukes bl.a. i energiberegninger.">
                                            <label className="text-label block mb-1">Byggeår</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">{property.construction_year || "N/A"}</div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Energimerking: Energiklasse (A–G) fra energikart. Lavere bokstav = bedre energieffektivitet.">
                                            <label className="text-label block mb-1">Energimerking</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-success">{property.energy_label || "B"}</div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Godkjente Plasser: Antall plasser godkjent for bruk (f.eks. barnevernsinstitusjon). Fra Bufdir eller tilsyn.">
                                            <label className="text-label block mb-1">Godkjente Plasser</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">{property.approved_places || property.external_data?.stats?.approved_places || "-"}</div>
                                    </div>

                                    <div>
                                        <DataTooltip content="Budsjetterte Plasser: Planlagt antall plasser i henhold til driftsavtale eller budsjett. Fra e-don2.">
                                            <label className="text-label block mb-1">Budsjetterte Plasser</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">{property.budgeted_places || "-"}</div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Tilhørighet: Organisatorisk tilhørighet eller eierinstans. Fra e-don2.">
                                            <label className="text-label block mb-1">Tilhørighet</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground truncate" title={property.affiliation}>
                                            {property.affiliation || "-"}
                                        </div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Tilhørende Avdeling: Den organisatoriske avdelingen (Senteret) som denne eiendommen er knyttet til.">
                                            <label className="text-label block mb-1">Tilhørende Avdeling</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-primary">{property.center_name || "Ikke tilknyttet"}</div>
                                    </div>

                                    {/* Second row of details */}
                                    <div>
                                        <DataTooltip content="Eierskap: Type eierskap (Statlig/Privat). Fra e-don2.">
                                            <label className="text-label block mb-1">Eierskap</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">
                                            {property.ownership_type || "Ikke angitt"}
                                        </div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Hjemmelshaver: Eiendomsrettighetshaver fra grunnboken. Fra masterdata/Elements.">
                                            <label className="text-label block mb-1">Hjemmelshaver</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground truncate" title={property.external_data?.master_data?.title_holder}>
                                            {property.external_data?.master_data?.title_holder || "Ikke angitt"}
                                        </div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Enhet ID: Intern identifikator fra ERP-systemet. Brukes til kobling mot regnskap.">
                                            <label className="text-label block mb-1">Enhet ID (ERP)</label>
                                        </DataTooltip>
                                        <div className="text-base font-bold text-foreground">{property.unit_id_erp || "–"}</div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Enhetstype fra e-don2 (Enhetskorttype). Skiller avdeling under en institusjon fra hele barnevernsinstitusjonen. Brukes i kostnadsfordeling.">
                                            <label className="text-label block mb-1">Enhetstype</label>
                                        </DataTooltip>
                                        <div className="text-sm font-semibold leading-snug text-foreground wrap-break-word whitespace-normal">
                                            {property.unit_short_type || "–"}
                                        </div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Formål (utledet) fra e-don2: f.eks. Barnevernsinstitusjon, Institusjonsavdeling, Omsorgssenter.">
                                            <label className="text-label block mb-1">Formål (utledet)</label>
                                        </DataTooltip>
                                        <div className="text-sm font-semibold leading-snug text-foreground wrap-break-word whitespace-normal">
                                            {property.unit_type_derived || "–"}
                                        </div>
                                    </div>
                                    <div>
                                        <DataTooltip content="Status: Driftsstatus for eiendommen. «Operativ» = i normal drift. «Nedlagt» vises hvis nedleggelsesdato er passert.">
                                            <label className="text-label block mb-1">Status</label>
                                        </DataTooltip>
                                        <div className={`text-base font-bold uppercase tracking-wide ${property.closed_at && new Date(property.closed_at) <= new Date() ? 'text-red-500' : 'text-success'}`}>
                                            {property.closed_at && new Date(property.closed_at) <= new Date() ? 'Nedlagt' : 'Operativ'}
                                        </div>
                                    </div>
                                </div>

                                {property.legal_basis && (
                                    <div className="mt-8 pt-8 border-t border-border">
                                        <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-4">Institusjonelle Detaljer</h3>
                                        <div className="glass-card p-4 bg-primary/5">
                                            <div className="flex items-start gap-3">
                                                <svg className="w-5 h-5 text-primary mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                                </svg>
                                                <div>
                                                    <p className="text-xs font-bold text-primary uppercase mb-1">Hjemmelsgrunnlag (Legal Basis)</p>
                                                    <p className="text-sm text-foreground leading-relaxed">{property.legal_basis}</p>
                                                </div>
                                            </div>
                                            {property.closed_at && (
                                                <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground italic">
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                    Planlagt/faktisk nedleggelsesdato: {new Date(property.closed_at).toLocaleDateString('nb-NO')}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </motion.div>

                            {/* Bufdir – tittel tilpasses usage / Formål (utledet) (ikke alltid barnevernsinstitusjon) */}
                            {(property.external_data?.bufdir || property.external_data?.bufdir_institution) && (() => {
                                const { title: bufdirSectionTitle, conflictNote: bufdirTypeConflict } =
                                    resolveBufdirSectionTitle(property);
                                const bufdir = property.external_data?.bufdir || property.external_data?.bufdir_institution;
                                const name = bufdir?.institution_name ?? bufdir?.bufdir_name ?? bufdir?.name;
                                const description = bufdir?.description;
                                const imagePath = bufdir?.image_path;
                                const imageUrl = bufdir?.image_url;
                                const legalBases = Array.isArray(bufdir?.legal_bases) ? bufdir.legal_bases : [];
                                const ownerType = bufdir?.owner_type;
                                const bufdirUrl = bufdir?.bufdir_url;
                                const email = bufdir?.email;
                                const phone = bufdir?.phone;
                                const imgSrc = imagePath ? imagePath : imageUrl;
                                const rawGallery = Array.isArray(bufdir?.gallery) ? bufdir.gallery : [];
                                const gallerySlides =
                                    rawGallery.length > 0
                                        ? rawGallery
                                              .map((g: Record<string, unknown>) => ({
                                                  src: (g.local_path || g.url) as string,
                                                  caption: g.caption as string | undefined,
                                                  credit: g.credit as string | undefined,
                                                  alt: (g.alt as string) || name || "Institusjon",
                                              }))
                                              .filter((x: { src: string }) => Boolean(x.src))
                                        : imgSrc
                                          ? [
                                                {
                                                    src: imgSrc,
                                                    caption: undefined as string | undefined,
                                                    credit: undefined as string | undefined,
                                                    alt: name || "Institusjon",
                                                },
                                            ]
                                          : [];
                                const slideIdx =
                                    gallerySlides.length > 0
                                        ? Math.min(bufdirSlide, gallerySlides.length - 1)
                                        : 0;
                                const summaryBullets: string[] = Array.isArray(bufdir?.summary?.raw_bullets)
                                    ? bufdir.summary.raw_bullets
                                    : [];
                                const contentSections = Array.isArray(bufdir?.content_sections)
                                    ? bufdir.content_sections
                                    : [];
                                const postal = bufdir?.contact_postal_address as string | undefined;
                                const phoneDisplay = phone ? formatBufdirPhoneDisplay(String(phone)) : null;
                                return (
                                    <motion.div
                                        key="bufdir"
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.08 }}
                                        className="glass-card p-8"
                                    >
                                        <h2 className={`text-2xl font-bold flex items-center gap-2 text-foreground ${bufdirTypeConflict ? "mb-2" : "mb-6"}`}>
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                            </svg>
                                            {bufdirSectionTitle}
                                        </h2>
                                        {bufdirTypeConflict && (
                                            <p className="text-sm text-amber-700 dark:text-amber-400/90 mb-6 border border-amber-500/30 rounded-lg px-3 py-2 bg-amber-500/10">
                                                {bufdirTypeConflict}
                                            </p>
                                        )}
                                        <div className="flex flex-col gap-8">
                                            {gallerySlides.length > 0 && (
                                                <DataTooltip content="Bilder fra Bufdir (offentlig informasjonsside).">
                                                    <div className="space-y-3 w-full">
                                                        <div className="relative rounded-lg overflow-hidden border border-border bg-muted/20 aspect-video max-h-[min(420px,70vh)] flex items-center justify-center">
                                                            <img
                                                                src={gallerySlides[slideIdx].src}
                                                                alt={gallerySlides[slideIdx].alt || name || "Institusjon"}
                                                                className="max-w-full max-h-[min(420px,70vh)] object-contain"
                                                            />
                                                            {gallerySlides.length > 1 && (
                                                                <>
                                                                    <button
                                                                        type="button"
                                                                        aria-label="Forrige bilde"
                                                                        className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-background/90 border border-border p-2 shadow-sm hover:bg-background"
                                                                        onClick={() =>
                                                                            setBufdirSlide((s) =>
                                                                                (s - 1 + gallerySlides.length) %
                                                                                gallerySlides.length
                                                                            )
                                                                        }
                                                                    >
                                                                        <ChevronLeft className="w-5 h-5" />
                                                                    </button>
                                                                    <button
                                                                        type="button"
                                                                        aria-label="Neste bilde"
                                                                        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-background/90 border border-border p-2 shadow-sm hover:bg-background"
                                                                        onClick={() =>
                                                                            setBufdirSlide(
                                                                                (s) => (s + 1) % gallerySlides.length
                                                                            )
                                                                        }
                                                                    >
                                                                        <ChevronRight className="w-5 h-5" />
                                                                    </button>
                                                                    <span className="absolute bottom-2 right-2 text-xs bg-background/90 border border-border px-2 py-1 rounded-md tabular-nums">
                                                                        {slideIdx + 1} / {gallerySlides.length}
                                                                    </span>
                                                                </>
                                                            )}
                                                        </div>
                                                        {gallerySlides[slideIdx]?.caption && (
                                                            <p className="text-sm text-foreground font-medium">
                                                                {gallerySlides[slideIdx].caption}
                                                            </p>
                                                        )}
                                                        {gallerySlides[slideIdx]?.credit && (
                                                            <p className="text-xs text-muted-foreground">
                                                                {gallerySlides[slideIdx].credit}
                                                            </p>
                                                        )}
                                                        {gallerySlides.length > 1 && (
                                                            <div className="flex gap-2 overflow-x-auto pb-1 pt-1">
                                                                {gallerySlides.map((s, i) => (
                                                                    <button
                                                                        key={i}
                                                                        type="button"
                                                                        onClick={() => setBufdirSlide(i)}
                                                                        className={`shrink-0 w-16 h-16 rounded-md border overflow-hidden transition ring-offset-2 ${
                                                                            i === slideIdx
                                                                                ? "ring-2 ring-primary border-primary"
                                                                                : "border-border opacity-90 hover:opacity-100"
                                                                        }`}
                                                                    >
                                                                        <img
                                                                            src={s.src}
                                                                            alt=""
                                                                            className="w-full h-full object-cover"
                                                                        />
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </DataTooltip>
                                            )}
                                            <div className="space-y-4">
                                                {name && <p className="text-xl font-bold text-foreground">{name}</p>}
                                                {description && (
                                                    <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                                                        {description}
                                                    </p>
                                                )}
                                                {summaryBullets.length > 0 && (
                                                    <ul className="list-disc list-inside text-sm text-foreground space-y-1 bg-muted/30 rounded-lg px-4 py-3 border border-border">
                                                        {summaryBullets.map((b, i) => (
                                                            <li key={i}>{b}</li>
                                                        ))}
                                                    </ul>
                                                )}
                                                {ownerType && (
                                                    <p className="text-sm">
                                                        <span className="text-label font-medium">Eierform:</span>{" "}
                                                        <span className="text-foreground">{ownerType}</span>
                                                    </p>
                                                )}
                                                {(bufdir?.placement_type || bufdir?.capacity != null) && (
                                                    <div className="flex flex-wrap gap-3 text-sm text-foreground">
                                                        {bufdir?.placement_type && (
                                                            <span className="px-2 py-1 rounded border border-border bg-background">
                                                                Plassering: {String(bufdir.placement_type)}
                                                            </span>
                                                        )}
                                                        {bufdir?.capacity != null && (
                                                            <span className="px-2 py-1 rounded border border-border bg-background">
                                                                Kapasitet: {String(bufdir.capacity)}
                                                            </span>
                                                        )}
                                                    </div>
                                                )}
                                                {legalBases.length > 0 && (
                                                    <div className="flex flex-wrap gap-2">
                                                        {legalBases.map((lb: string, i: number) => (
                                                            <span
                                                                key={i}
                                                                className="px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded text-xs font-medium"
                                                            >
                                                                {lb}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                                {(postal || email || phoneDisplay) && (
                                                    <div className="rounded-lg border border-border bg-muted/20 px-4 py-3 space-y-2 text-sm">
                                                        <p className="text-label font-medium text-xs uppercase tracking-wide">
                                                            Kontakt
                                                        </p>
                                                        {postal && (
                                                            <p className="text-foreground">
                                                                <span className="text-muted-foreground">Postadresse: </span>
                                                                {postal}
                                                            </p>
                                                        )}
                                                        {(email || phoneDisplay) && (
                                                            <p className="text-slate-600 dark:text-slate-400">
                                                                {email && <span>{email}</span>}
                                                                {email && phoneDisplay && " · "}
                                                                {phoneDisplay && <span>{phoneDisplay}</span>}
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                                {bufdir?.contact_rich_html && (
                                                    <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                                                        {bufdirHtmlToPlainText(String(bufdir.contact_rich_html))}
                                                    </p>
                                                )}
                                                {contentSections.length > 0 && (
                                                    <div className="space-y-3 pt-4 border-t border-border">
                                                        {contentSections.map(
                                                            (
                                                                sec: {
                                                                    title?: string;
                                                                    intro_html?: string;
                                                                    subsections?: Array<{
                                                                        title?: string;
                                                                        body_html?: string;
                                                                    }>;
                                                                },
                                                                si: number
                                                            ) => {
                                                                const isOpen = expandedContentSections[si] !== false; // default open
                                                                const toggleSection = () =>
                                                                    setExpandedContentSections(prev => ({ ...prev, [si]: !isOpen }));
                                                                return (
                                                                    <div key={si} className="rounded-xl border border-border overflow-hidden">
                                                                        {/* Accordion header */}
                                                                        <button
                                                                            type="button"
                                                                            onClick={toggleSection}
                                                                            className="w-full flex items-center justify-between px-5 py-3 bg-surface hover:bg-border/30 transition-colors text-left select-none"
                                                                        >
                                                                            <span className="font-semibold text-foreground text-sm">
                                                                                {sec.title || `Seksjon ${si + 1}`}
                                                                            </span>
                                                                            <svg
                                                                                className={`w-4 h-4 text-muted-foreground transition-transform duration-200 flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`}
                                                                                fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                                                            >
                                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                                            </svg>
                                                                        </button>
                                                                        {/* Accordion body */}
                                                                        {isOpen && (
                                                                            <div className="px-5 py-4 space-y-4 bg-background/50">
                                                                                {sec.intro_html && (
                                                                                    <p className="text-sm text-foreground whitespace-pre-wrap">
                                                                                        {bufdirHtmlToPlainText(sec.intro_html)}
                                                                                    </p>
                                                                                )}
                                                                                {(sec.subsections || []).map((sub, sj) => (
                                                                                    <div
                                                                                        key={sj}
                                                                                        className="rounded-lg border border-border/80 bg-surface p-4 space-y-2"
                                                                                    >
                                                                                        {sub.title && (
                                                                                            <h4 className="text-sm font-semibold text-foreground">
                                                                                                {sub.title}
                                                                                            </h4>
                                                                                        )}
                                                                                        {sub.body_html && (
                                                                                            <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                                                                                                {bufdirHtmlToPlainText(sub.body_html)}
                                                                                            </p>
                                                                                        )}
                                                                                    </div>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                );
                                                            }
                                                        )}
                                                    </div>
                                                )}
                                                {bufdir?.scraped_at && (
                                                    <p className="text-xs text-muted-foreground">
                                                        Bufdir-data synket:{" "}
                                                        {new Date(String(bufdir.scraped_at)).toLocaleString("nb-NO")}
                                                    </p>
                                                )}
                                                {bufdirUrl && (
                                                    <a
                                                        href={bufdirUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1 text-primary hover:underline text-sm font-medium"
                                                    >
                                                        Åpne på bufdir.no
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                                        </svg>
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })()}

                            {/* Units & Contracts */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                                className="glass-card p-8"
                            >
                                <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-foreground">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                    </svg>
                                    Enheter og Leietakere
                                </h2>
                                <div className="overflow-x-auto">
                                    <table className="enterprise-table">
                                        <thead>
                                            <tr>
                                                <th><DataTooltip content="Enhet: Bruksformål eller identifikator for leiligheten/lokalet (f.eks. «Leilighet 1», «Kontor»).">Enhet</DataTooltip></th>
                                                <th><DataTooltip content="Areal: Bruttoareal i kvadratmeter (m²) for enheten. Kilde: Masterdata eller kontrakt.">Areal</DataTooltip></th>
                                                <th><DataTooltip content="Sone: Pris-/brukssone (A, B, C) som brukes til leieberegning. Høyere sone = høyere leie.">Sone</DataTooltip></th>
                                                <th><DataTooltip content="UU: Universell Utforming. «OK» = enheten oppfyller tilgjengelighetskrav. «Nei» = mangler dokumentasjon eller oppfyller ikke kravene.">UU</DataTooltip></th>
                                                <th><DataTooltip content="Leietaker / Kontrakt: Motpart (leietaker) og tilknyttet leiekontrakt. Klikk for å åpne detaljer.">Leietaker / Kontrakt</DataTooltip></th>
                                                <th><DataTooltip content="Org.nr: Organisasjonsnummer (9 siffer) fra Brønnøysundregistrene. Identifiserer leietaker juridisk.">Org.nr</DataTooltip></th>
                                                <th><DataTooltip content="Husleie (År): Årlig leiebeløp fra kontrakten. Beregnes som avtalt beløp per år.">Husleie (År)</DataTooltip></th>
                                                <th><DataTooltip content="Status: Kontraktens status (f.eks. «active» = aktiv, «expired» = utløpt).">Status</DataTooltip></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {hasUnits ? units?.map((unit: any) => {
                                                const contract = contracts?.find((c: any) => c.unit_id === unit.unit_id);
                                                const party = parties?.find((p: any) => p.party_id === contract?.party_id);

                                                // Format Rent
                                                let rentDisplay = "-";
                                                if (contract?.amount) {
                                                    const amountVal = typeof contract.amount === 'object' ? contract.amount.amount_per_year : contract.amount;
                                                    if (amountVal) {
                                                        rentDisplay = new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(amountVal);
                                                    }
                                                }

                                                return (
                                                    <tr key={unit.unit_id}>
                                                        <td className="font-bold text-foreground">{unit.purpose}</td>
                                                        <td className="text-muted">{unit.area_sqm} m²</td>
                                                        {/* Zone Column */}
                                                        <td>
                                                            {unit.zone_type ? (
                                                                <span className="px-2 py-1 bg-primary/10 text-primary border border-primary/20 rounded text-[10px] font-mono uppercase font-bold">
                                                                    {unit.zone_type}
                                                                </span>
                                                            ) : <span className="text-slate-400">-</span>}
                                                        </td>
                                                        {/* UU Column */}
                                                        <td>
                                                            {unit.uu_compliant ? (
                                                                <span title="Universelt Utformet" className="text-success flex items-center gap-1">
                                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
                                                                    <span className="text-[10px] font-bold uppercase">OK</span>
                                                                </span>
                                                            ) : <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Nei</span>}
                                                        </td>
                                                        <td>
                                                            {party ? (
                                                                <div className="space-y-1">
                                                                    <Link href={`/parties/${party.party_id}`} className="font-bold text-primary hover:underline transition-colors block">
                                                                        {party.name}
                                                                    </Link>
                                                                    {contract && (
                                                                        <Link href={`/contracts/${contract.contract_id}`} className="text-[10px] text-slate-500 dark:text-slate-400 hover:text-primary font-bold uppercase tracking-widest transition-colors flex items-center gap-1">
                                                                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                                                            Vis Kontrakt
                                                                        </Link>
                                                                    )}
                                                                </div>
                                                            ) : (
                                                                <span className="text-slate-400 italic">Ledig</span>
                                                            )}
                                                        </td>
                                                        <td className="text-xs text-muted font-mono">
                                                            {party?.orgnr || "-"}
                                                        </td>
                                                        <td className="font-bold text-primary">
                                                            {rentDisplay}
                                                        </td>
                                                        <td>
                                                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${contract?.status === 'active' ? 'bg-success/20 text-success' : 'bg-muted/20 text-muted'}`}>
                                                                {contract?.status || "Ingen"}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            }) : (
                                                <tr>
                                                    <td colSpan={8} className="px-4 py-6 text-center text-sm text-muted italic">
                                                        Ingen enheter, kontrakter eller leietakere registrert for denne eiendommen.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </motion.div>

                            {/* Financial Overview */}
                            <motion.div
                                id="financials"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="glass-card p-8 border-t-4 border-t-primary/50"
                            >
                                <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-foreground">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    Finansiell Oversikt
                                </h2>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                                    <div className="p-4 glass-card">
                                        <DataTooltip content="Husleie (Årsleie): Sum av årlig leie fra alle aktive kontrakter. Kilde: Kontrakt.amount_per_year.">
                                            <div className="text-label mb-1">Husleie (Årsleie)</div>
                                        </DataTooltip>
                                        <div className="text-2xl font-bold text-primary">
                                            {(() => {
                                                const activeContracts = validActiveContracts;
                                                const totalRent = activeContracts.reduce((sum: number, c: any) =>
                                                    sum + ((typeof c.amount === 'object' ? c.amount.amount_per_year : c.amount) || 0), 0
                                                );
                                                const syntheticRent = property.external_data?.financials?.rent_summary != null && property.external_data?.financials?.synthetic_rent_ytd;
                                                if (totalRent > 0) {
                                                    return new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(totalRent);
                                                }
                                                if (syntheticRent && Number(property.external_data?.financials?.rent_summary) > 0) {
                                                    return (
                                                        <span title="Estimat basert på areal/vedlikehold (syntetisk data)">
                                                            {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.external_data.financials.rent_summary))}
                                                            <span className="text-xs font-normal text-muted ml-1">(estimat)</span>
                                                        </span>
                                                    );
                                                }
                                                return <span className="text-base text-muted">Ingen kontrakter</span>;
                                            })()}
                                        </div>
                                        <DataTooltip content="Årsleie: Total husleie per år fra aktive kontrakter. Mangler enheter: Eiendommen har ingen registrerte leiligheter/lokaler.">
                                            <div className="text-[10px] text-muted font-bold uppercase tracking-wider mt-2">
                                                Årsleie fra {validActiveContracts.length || 0} aktive kontrakter
                                                {property.external_data?.financials?.synthetic_rent_ytd && (
                                                    <span className="block text-amber-500/90 mt-1">Leie: syntetisk estimat</span>
                                                )}
                                                {!hasUnits && (
                                                    <span className="block text-orange-500 mt-1">Mangler enheter</span>
                                                )}
                                                {!hasTenants && (
                                                    <span className="block text-orange-500 mt-1">Ingen leietaker registrert</span>
                                                )}
                                            </div>
                                        </DataTooltip>
                                    </div>
                                    <div className="p-4 glass-card border-l-2 border-l-primary/30">
                                        <DataTooltip content="Lokaler budsjett 2026: Økonomiavdelingens vedtatte budsjett for lokaler/husleie (finance_dept_2026). Dette er budsjettall, ikke faktisk forbruk.">
                                            <div className="text-label mb-1">Lokaler — budsjett 2026</div>
                                        </DataTooltip>
                                        <div className="text-xl font-bold text-foreground leading-tight">
                                            {costStatusLoading ? (
                                                <span className="text-base text-muted animate-pulse">Laster…</span>
                                            ) : (() => {
                                                const rent = costTotals?.rent ?? 0;
                                                if (!rent) return <span className="text-base text-muted">0 kr</span>;
                                                return new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(rent);
                                            })()}
                                        </div>
                                        <div className="text-[10px] text-muted font-bold uppercase tracking-wider mt-2">
                                            {(costTotals?.rent ?? 0) > 0
                                                ? 'Økonomiavd. vedtatt budsjett 2026'
                                                : 'Ingen lokaler i budsjett 2026'}
                                        </div>
                                    </div>
                                    <div className="p-4 glass-card">
                                        <DataTooltip content="Drift + vedlikehold budsjett 2026: Økonomiavdelingens vedtatte budsjett for drift og vedlikehold. Dette er budsjettall, ikke faktisk forbruk.">
                                            <div className="text-label mb-1">Drift + vedlikehold — budsjett 2026</div>
                                        </DataTooltip>
                                        <div className="text-xl font-bold text-danger leading-tight">
                                            {costStatusLoading ? (
                                                <span className="text-base text-muted animate-pulse">Laster…</span>
                                            ) : (() => {
                                                const total = costTotals?.other ?? 0;
                                                return new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(total);
                                            })()}
                                        </div>
                                        <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mt-2">
                                            {(costTotals?.other ?? 0) > 0 ? 'Økonomiavd. vedtatt budsjett 2026' : 'Ingen drift/vedlikehold i budsjett 2026'}
                                        </div>
                                    </div>
                                </div>

                                {Object.keys(groupedExpenses).length > 0 && (
                                    <div className="mt-8 space-y-6">
                                        <h3
                                            className="font-semibold text-slate-300 flex items-center gap-2 cursor-pointer hover:text-slate-200 transition-colors select-none"
                                            onClick={() => setExpensesExpanded(!expensesExpanded)}
                                        >
                                            <svg
                                                className={`w-4 h-4 transition-transform duration-200 ${expensesExpanded ? 'rotate-90' : ''}`}
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                                            <DataTooltip content="Spesifiserte Utgifter: Bokførte kostnader gruppert etter kontotype/kategori (f.eks. fellesutgifter, renhold, vedlikehold). Beløpene er avrundet til hele kroner. Kilde: Regnskap og manuelle poster.">Spesifiserte Utgifter (Gruppert)</DataTooltip>
                                        </h3>

                                        {expensesExpanded && (
                                            <div className="space-y-6">
                                                {/* Master Data Costs */}
                                                {(property.external_data?.financials?.municipal_fees || property.external_data?.financials?.energy_cost) && (
                                                    <div className="glass-card rounded-lg overflow-hidden mb-4">
                                                        <div className="px-4 py-3 bg-surface border-b border-border flex justify-between items-center">
                                                            <DataTooltip content="Faste Kostnader: Kommunale avgifter (avfall, vann, kloakk), energi og oppvarming. Hentes fra masterdata ved import. Ikke inkludert i regnskaps-CSV.">
                                                                <span className="font-bold text-foreground text-[10px] uppercase tracking-wider">Faste Kostnader (Masterdata)</span>
                                                            </DataTooltip>
                                                        </div>
                                                        <table className="w-full text-left text-sm">
                                                            <tbody className="divide-y divide-border">
                                                                {property.external_data.financials.municipal_fees > 0 && (
                                                                    <tr className="hover:bg-surface/50">
                                                                        <td className="px-4 py-2 text-muted text-xs w-2/3 font-medium">
                                                                            <DataTooltip content="Kommunale avgifter: Avfall, vann, kloakk og andre kommunale tjenester. Fra masterdata.">Kommunale avgifter</DataTooltip>
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-bold text-foreground text-xs">
                                                                            {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(property.external_data.financials.municipal_fees)}
                                                                        </td>
                                                                    </tr>
                                                                )}
                                                                {property.external_data.financials.energy_cost > 0 && (
                                                                    <tr className="hover:bg-surface/50">
                                                                        <td className="px-4 py-2 text-muted text-xs w-2/3 font-medium">
                                                                            <DataTooltip content="Energi / Strøm: Strømforbruk og energikostnader. Fra masterdata eller regnskap.">Energi / Strøm</DataTooltip>
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-bold text-foreground text-xs">
                                                                            {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(property.external_data.financials.energy_cost)}
                                                                        </td>
                                                                    </tr>
                                                                )}
                                                                {property.external_data.financials.heating_cost > 0 && (
                                                                    <tr className="hover:bg-surface/50">
                                                                        <td className="px-4 py-2 text-muted text-xs w-2/3 font-medium">
                                                                            <DataTooltip content="Oppvarming: Varmekostnader (fjernvarme, olje, etc.). Fra masterdata.">Oppvarming</DataTooltip>
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-bold text-foreground text-xs">
                                                                            {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(property.external_data.financials.heating_cost)}
                                                                        </td>
                                                                    </tr>
                                                                )}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                )}

                                                <div className="space-y-4">
                                                    {Object.entries(groupedExpenses).sort((a, b) => a[0].localeCompare(b[0])).map(([type, expenses]: [string, any[]]) => {
                                                        const isExpanded = expandedGroups[type] !== false; // Default true
                                                        const toggleGroup = () => setExpandedGroups(prev => ({ ...prev, [type]: !isExpanded }));

                                                        return (
                                                            <div key={type} className="glass-card rounded-lg overflow-hidden">
                                                                <div
                                                                    className="px-4 py-3 bg-surface border-b border-border flex justify-between items-center cursor-pointer hover:bg-surface/80 transition-colors select-none"
                                                                    onClick={toggleGroup}
                                                                >
                                                                    <div className="flex items-center gap-2">
                                                                        <svg
                                                                            className={`w-4 h-4 transition-transform duration-200 text-muted ${isExpanded ? 'rotate-90' : ''}`}
                                                                            fill="none"
                                                                            viewBox="0 0 24 24"
                                                                            stroke="currentColor"
                                                                        >
                                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                                                        </svg>
                                                                        <DataTooltip content={`${type}: Utgiftskategori fra regnskap. Beløp avrundet til hele kroner. Klikk for å se underkategorier og leverandører.`}>
                                                                            <span className="font-bold text-foreground text-[10px] uppercase tracking-wider">{type}</span>
                                                                        </DataTooltip>
                                                                    </div>
                                                                    <span className="text-xs font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded">
                                                                        {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(
                                                                            expenses.reduce((sum, e) => sum + (e.amount_parsed || e.amount || 0), 0)
                                                                        )}
                                                                    </span>
                                                                </div>
                                                                {isExpanded && (
                                                                    <table className="w-full text-left text-sm">
                                                                        <tbody className="divide-y divide-border">
                                                                            {expenses.map((expense: any, idx: number) => (
                                                                                <tr key={idx} className="hover:bg-surface/50 transition-colors">
                                                                                    <td className="px-4 py-2 text-muted text-xs w-2/3 font-medium">
                                                                                        {expense.description || expense.provider || "Ukjent"}
                                                                                    </td>
                                                                                    <td className="px-4 py-2 text-right font-bold text-foreground text-xs">
                                                                                        {expense.amount_parsed ?
                                                                                            new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(expense.amount_parsed)
                                                                                            : expense.amount
                                                                                        }
                                                                                    </td>
                                                                                </tr>
                                                                            ))}
                                                                        </tbody>
                                                                    </table>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                </div>

                                                <div className="flex justify-between items-center pt-4 border-t border-border font-bold">
                                                    <DataTooltip content="Sum Driftsutgift: Total av alle bokførte driftskostnader. Kilde: Regnskapssystem (GL-transaksjoner) eller manuelle poster.">
                                                        <span className="text-label">SUM DRIFTSUTGIFT</span>
                                                    </DataTooltip>
                                                    <span className="text-2xl text-danger">
                                                        {(() => {
                                                            const fin = property.external_data?.financials || {};
                                                            const glTotal = Number(fin.total_spend_csv) || 0;
                                                            const manualTotal = Number(fin.total_manual_expenses) || 0;
                                                            // Beregn sum fra grupperte utgifter som fallback
                                                            const computedTotal = Object.values(groupedExpenses)
                                                                .flat()
                                                                .reduce((s: number, e: any) => s + (Number(e.amount_parsed) || Number(e.amount) || 0), 0);
                                                            const total = glTotal || manualTotal || computedTotal;
                                                            return total > 0
                                                                ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(total)
                                                                : '-';
                                                        })()}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </motion.div>

                            {/* Relationship Mapping Widget */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="glass-card rounded-2xl p-8 overflow-hidden relative"
                            >
                                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                                    <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24"><path d="M17 11V3l-5 4-5-4v8H3l9 10 9-10h-4z" /></svg>
                                </div>

                                <DataTooltip content="Systemisk Relasjonskart: Viser koblingen Eiendom → Kontrakt → Leietaker. Kontrakter hentes via matrikkel/elements. Klikk for å navigere til detaljer.">
                                    <h2 className="text-xl font-bold mb-8 text-foreground flex items-center gap-3">
                                        <div className="p-2 bg-primary/10 rounded-lg">
                                            <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                                        </div>
                                        Systemisk Relasjonskart
                                    </h2>
                                </DataTooltip>

                                <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative">
                                    {/* Connection lines (mobile) */}
                                    <div className="absolute inset-0 flex flex-col items-center justify-around md:hidden opacity-10 pointer-events-none">
                                        <div className="w-0.5 h-12 bg-blue-500"></div>
                                        <div className="w-0.5 h-12 bg-blue-500"></div>
                                    </div>

                                    {/* Parent Property Node (conditionally added) */}
                                    {property.parent_property_id && property.affiliation && (
                                        <>
                                            <Link
                                                href={`/properties/${property.parent_property_id}`}
                                                className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all block"
                                            >
                                                <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">Tilhørighet (Hovedeiendom)</div>
                                                <div className="font-bold truncate text-foreground" title={property.affiliation}>{property.affiliation}</div>
                                            </Link>

                                            <div className="hidden md:block w-8 shrink-0 h-0.5 bg-linear-to-r from-primary to-indigo-500 opacity-20 relative">
                                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary/10 p-1 rounded-full border border-primary/20">
                                                    <svg className="w-3 h-3 text-primary rotate-90 md:rotate-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                                                </div>
                                            </div>
                                        </>
                                    )}

                                    {/* Property Node */}
                                    <Link
                                        href={`/properties/${property.property_id}`}
                                        className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all block"
                                    >
                                        <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">{property.unit_short_type === 'Avdeling' ? 'Eiendom (Avdeling)' : 'Eiendom'}</div>
                                        <div className="font-bold truncate text-foreground" title={property.name || property.address}>{property.name || property.address}</div>
                                    </Link>

                                    <div className="hidden md:block w-8 shrink-0 h-0.5 bg-linear-to-r from-primary to-indigo-500 opacity-20 relative">
                                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary/10 p-1 rounded-full border border-primary/20">
                                            <svg className="w-3 h-3 text-primary rotate-90 md:rotate-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                                        </div>
                                    </div>

                                    {/* Contract Node(s) */}
                                    {validActiveContracts.length > 0 ? (
                                        <Link
                                            href={`/contracts/${validActiveContracts[0].contract_id}`}
                                            className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all block text-left"
                                        >
                                            <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">Kontrakt</div>
                                            <div className="font-bold text-foreground">
                                                <div className="flex flex-col">
                                                    <span>{validActiveContracts.length} Aktiv{validActiveContracts.length > 1 ? 'e' : ''}</span>
                                                    <span className="text-[10px] text-gray-400">Oppslag via matrikkel</span>
                                                </div>
                                            </div>
                                        </Link>
                                    ) : (
                                        <div className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all text-foreground">
                                            <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">Kontrakt</div>
                                            <div className="font-bold">Ingen registrert</div>
                                        </div>
                                    )}

                                    <div className="hidden md:block w-8 shrink-0 h-0.5 bg-linear-to-r from-indigo-500 to-purple-500 opacity-20 relative">
                                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary/10 p-1 rounded-full border border-primary/20">
                                            <svg className="w-3 h-3 text-primary rotate-90 md:rotate-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                                        </div>
                                    </div>

                                    {/* Party Node(s) */}
                                    {hasTenants ? (
                                        <Link
                                            href={`/parties/${parties[0].party_id}`}
                                            className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all block text-left"
                                        >
                                            <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">Motpart / Leietaker</div>
                                            <div className="font-bold truncate text-foreground">
                                                {parties[0].name}
                                            </div>
                                        </Link>
                                    ) : (
                                        <div className="z-10 glass-card p-4 w-full md:flex-1 group hover:border-primary transition-all text-foreground">
                                            <div className="text-[10px] text-primary font-bold uppercase tracking-widest mb-1">Motpart / Leietaker</div>
                                            <div className="font-bold">Ingen registrert</div>
                                        </div>
                                    )}
                                </div>
                            </motion.div>

                            {/* Nearby Services */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                                className="glass-card p-8"
                            >
                                <div className="flex items-center justify-between mb-6">
                                    <DataTooltip content="Nærliggende Tjenester: Skoler, helsetjenester, kollektivtilbud innen reiseavstand fra eiendommen. Brukes til tilgjengelighetsvurdering.">
                                        <h2 className="text-2xl font-bold flex items-center gap-2">
                                            <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                            </svg>
                                            Nærliggende Tjenester
                                        </h2>
                                    </DataTooltip>
                                    <button
                                        type="button"
                                        onClick={handleRefreshProximity}
                                        disabled={proximityRefreshing}
                                        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border border-border bg-background hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <RefreshCw size={16} className={proximityRefreshing ? 'animate-spin' : ''} />
                                        {proximityRefreshing ? 'Oppdaterer...' : 'Oppdater'}
                                    </button>
                                </div>
                                <AccessibilityStats propertyId={property.property_id} refreshKey={proximityRefreshKey} />
                            </motion.div>

                            {/* Leieforhold & Kontraktsøkonomi */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.25 }}
                                className="glass-card p-8"
                            >
                                <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-foreground">
                                    <svg className="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    Leieforhold &amp; Kontraktsøkonomi
                                </h2>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                                    {[
                                        { label: 'Lokaliserings-ID', value: property.lokalisering_id },
                                        { label: 'Målgruppe', value: property.malgruppe },
                                        { label: 'Lok: Distrikt', value: property.lok_distrikt },
                                        { label: 'Lok: Område', value: property.lok_omrade },
                                        { label: 'Fylke', value: property.fylke },
                                        { label: 'Utleier kategori', value: property.utleier_kategori != null ? (property.utleier_kategori === 1 ? '1 – Statsbygg' : property.utleier_kategori === 2 ? '2 – Privat' : String(property.utleier_kategori)) : null },
                                        { label: 'Areal (leiekontrakt)', value: property.leased_area_kvm != null ? `${property.leased_area_kvm} kvm` : null },
                                        { label: 'Eksklusivt areal', value: property.eksklusivt_areal_kvm != null ? `${property.eksklusivt_areal_kvm} kvm` : null },
                                        { label: 'Tilleggsareal', value: property.tilleggsareal_kvm != null ? `${property.tilleggsareal_kvm} kvm` : null },
                                        { label: 'Reduksjon/addendum', value: property.reduksjon_addendum_kvm != null ? `${property.reduksjon_addendum_kvm} kvm` : null },
                                        { label: 'Elements (arkiv)', value: property.elements_id },
                                        { label: 'Matrikkel Gnr', value: property.gnr },
                                        { label: 'Matrikkel Bnr', value: property.bnr },
                                        { label: 'Matrikkel Knr', value: property.municipality_code },
                                        { label: 'Kommune', value: property.municipality },
                                        { label: 'Tilstandsgrad', value: property.tilstandsgrad },
                                        { label: 'Antall ansatte', value: property.antall_ansatte },
                                        { label: 'Parkeringsplasser', value: property.p_plasser },
                                        { label: 'KPI-justert kontraktsleie', value: property.contract_rent_nok != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.contract_rent_nok)) : null },
                                        { label: 'Indre vedlikehold', value: property.contract_maint_nok != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.contract_maint_nok)) : null },
                                        { label: 'Felleskostnader', value: property.contract_common_nok != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.contract_common_nok)) : null },
                                        { label: 'Brukeravhengige drift', value: property.contract_user_ops_nok != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.contract_user_ops_nok)) : null },
                                        { label: 'Kontraktsleie ved oppstart', value: property.kontraktsleie_ved_oppstart_kr != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.kontraktsleie_ved_oppstart_kr)) : null },
                                        { label: 'KPI-oppstartsdato', value: property.kpi_oppstartsdato ? new Date(property.kpi_oppstartsdato).toLocaleDateString('nb-NO') : null },
                                        { label: 'Kommunale gebyrer', value: property.kommunale_gebyrer_kr != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.kommunale_gebyrer_kr)) : null },
                                        { label: 'Energi kr/år', value: property.energi_kr_per_ar != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.energi_kr_per_ar)) : null },
                                        { label: 'Oppvarming kr/år', value: property.oppvarming_kr_per_ar != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.oppvarming_kr_per_ar)) : null },
                                        { label: 'MVA-kompensasjon kr/år', value: property.mva_kompensasjon_kr_per_ar != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.mva_kompensasjon_kr_per_ar)) : null },
                                        { label: 'Kontantinnskudd', value: property.kontantinnskudd_kr != null ? new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(Number(property.kontantinnskudd_kr)) : null },
                                        { label: 'Leieregulering', value: property.price_adj_clause },
                                        { label: 'Forlengelse & vilkår', value: property.extension_terms },
                                    ].map(({ label, value }) =>
                                        value != null && value !== '' ? (
                                            <div key={label}>
                                                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-0.5">{label}</div>
                                                <div className="text-sm font-medium text-foreground break-words">{String(value)}</div>
                                            </div>
                                        ) : null
                                    )}
                                </div>
                                {property.kommentar && (
                                    <div className="mt-6 pt-6 border-t border-border">
                                        <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-1">Kommentar</div>
                                        <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{property.kommentar}</p>
                                    </div>
                                )}
                            </motion.div>

                        </div>

                        {/* Right Column: Map & Risk */}
                        <div className="space-y-8">
                            {/* Map */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="glass-card overflow-hidden"
                            >
                                <div className="p-6 border-b border-border flex justify-between items-center bg-surface/50">
                                    <DataTooltip content="Lokasjon: Eiendommens koordinater (lat/long). Kartet viser eiendom og nærliggende tjenester (skoler, helsetjenester). Bruker Mapbox for kartvisning.">
                                        <h3 className="font-bold flex items-center gap-2 text-foreground">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-rose-500" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                                            </svg>
                                            Lokasjon
                                        </h3>
                                    </DataTooltip>
                                    <DataTooltip content="Mapbox: Karttjeneste som leverer bakgrunnskart og geokoding.">
                                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">MAPBOX</span>
                                    </DataTooltip>
                                </div>
                                <div className="h-64">
                                    <PropertyMap
                                        latitude={property.latitude || 59.9139}
                                        longitude={property.longitude || 10.7522}
                                        propertyName={property.name}
                                        services={proximityServices}
                                    />
                                </div>
                            </motion.div>

                            {/* Ansvarlige (Managers) */}
                            {property.managers && property.managers.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 }}
                                    className="glass-card p-6"
                                >
                                    <h3 className="font-bold flex items-center gap-2 mb-4 text-foreground">
                                        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                        </svg>
                                        Ansvarlige
                                    </h3>
                                    <div className="space-y-3">
                                        {property.managers.map((manager) => (
                                            <div key={manager.user_id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface/50 transition-colors">
                                                <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-xs">
                                                    {manager.name.split(' ').map(n => n[0]).join('')}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium text-sm text-foreground truncate">{manager.name}</div>
                                                    <div className="text-[10px] text-gray-400 truncate">{manager.email}</div>
                                                </div>
                                                <a href={`mailto:${manager.email}`} aria-label={`Send e-post til ${manager.name}`} className="p-1.5 hover:bg-primary/10 rounded-full text-primary transition-colors">
                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                                    </svg>
                                                </a>
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}

                            {/* KPI-vurdering */}
                            {validActiveContracts.length > 0 && (() => {
                                const kpiContracts = validActiveContracts.map((c: any) => {
                                    const ext = c.external_data || {};
                                    const reg: string = ext.regulation_type || '';
                                    const match = reg.match(/(\d+)%/);
                                    const pct = match ? parseInt(match[1]) : null;
                                    const amount = typeof c.amount === 'object'
                                        ? (c.amount?.amount_per_year ?? 0)
                                        : (c.amount ?? 0);
                                    const party = parties?.find((p: any) => p.party_id === c.party_id);
                                    return { c, reg, pct, amount, party };
                                });
                                const totalLeie = kpiContracts.reduce((s: number, x: any) => s + Number(x.amount), 0);
                                const nok = (v: number) => new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(v);
                                const nextKpiDate = property.kpi_oppstartsdato
                                    ? (() => {
                                        const d = new Date(property.kpi_oppstartsdato);
                                        const now = new Date();
                                        d.setFullYear(now.getFullYear() + (new Date(d.setFullYear(now.getFullYear())) <= now ? 1 : 0));
                                        return new Date(property.kpi_oppstartsdato.replace(/\d{4}/, String(d.getFullYear())));
                                    })() : null;
                                return (
                                    <motion.div
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.12 }}
                                        className="glass-card p-6"
                                    >
                                        <h2 className="text-lg font-bold mb-4 text-foreground flex items-center gap-2">
                                            <span className="p-1.5 bg-blue-500/10 rounded-lg">
                                                <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                                            </span>
                                            KPI-vurdering
                                        </h2>

                                        {/* Kontrakter */}
                                        <div className="space-y-2 mb-4">
                                            {kpiContracts.map(({ c, reg, pct, amount, party }: any) => (
                                                <div key={c.contract_id} className="flex items-start justify-between gap-2 p-3 rounded-lg bg-muted/40 text-sm">
                                                    <div className="min-w-0">
                                                        <div className="font-medium text-foreground truncate">{party?.name || c.contract_name || 'Ukjent utleier'}</div>
                                                        {reg ? (
                                                            <div className="flex items-center gap-1.5 mt-0.5">
                                                                <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${pct === 100 ? 'bg-green-500' : pct !== null && pct >= 80 ? 'bg-yellow-500' : 'bg-orange-500'}`} />
                                                                <span className="text-xs text-muted-foreground">{reg}</span>
                                                            </div>
                                                        ) : (
                                                            <div className="text-xs text-muted-foreground mt-0.5">Reguleringstype ikke registrert</div>
                                                        )}
                                                    </div>
                                                    <div className="text-right flex-shrink-0">
                                                        <div className="font-semibold text-foreground">{nok(Number(amount))}</div>
                                                        <div className="text-[10px] text-muted-foreground">per år</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Totalt + neste regulering */}
                                        <div className="border-t border-border pt-3 flex justify-between items-end">
                                            <div>
                                                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Total leie per år</div>
                                                <div className="text-xl font-bold text-foreground">{nok(totalLeie)}</div>
                                                {nextKpiDate && (
                                                    <div className="text-xs text-muted-foreground mt-1">
                                                        Neste KPI-regulering: <span className="font-medium text-foreground">{nextKpiDate.toLocaleDateString('nb-NO')}</span>
                                                    </div>
                                                )}
                                            </div>
                                            <div className="text-right">
                                                <div className={`text-xs font-bold px-2 py-1 rounded-full ${
                                                    kpiContracts.every((x: any) => x.pct === 100) ? 'bg-green-500/10 text-green-600' :
                                                    kpiContracts.some((x: any) => x.pct !== null) ? 'bg-yellow-500/10 text-yellow-600' :
                                                    'bg-muted text-muted-foreground'
                                                }`}>
                                                    {kpiContracts.every((x: any) => x.pct === 100) ? '100% KPI' :
                                                     kpiContracts.some((x: any) => x.pct !== null) ? 'Blandet KPI' : 'KPI ukjent'}
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })()}

                            {/* Styringspanel */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.15 }}
                            >
                                <PropertySteeringPanel
                                    propertyId={property.property_id}
                                    latestRiskAssessment={latest_risk_assessment}
                                />
                            </motion.div>

                            {/* Risk Assessment */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.2 }}
                                className="glass-card p-8"
                            >
                                <DataTooltip content="Risiko & Avvik: Operasjonell risiko basert på aktive avvik. Ekstern risiko fra NVE/Kartverket (flom, skred). Score 0% = ingen risiko, høyere = mer risiko.">
                                    <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-foreground">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                        </svg>
                                        Risiko & Avvik
                                    </h2>
                                </DataTooltip>

                                {latest_risk_assessment ? (
                                    <div className="space-y-6">
                                        {/* Operational Risk (Deviations) - Main Score */}
                                        <div className={`p-4 rounded-lg border ${latest_risk_assessment.overall_risk_score > 0 ? (latest_risk_assessment.overall_risk_score > 75 ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-warning/10 border-warning/20 text-warning') : 'bg-success/10 border-success/20 text-success'}`}>
                                            <h4 className="font-bold flex items-center justify-between mb-2">
                                                <span>Operasjonell Risiko</span>
                                                <span className="text-3xl">{Math.round(latest_risk_assessment.overall_risk_score)}%</span>
                                            </h4>
                                            <p className="text-[10px] uppercase tracking-wider font-bold opacity-70 mb-2">
                                                {latest_risk_assessment.overall_risk_score === 0 ? "Ingen aktive avvik" : "Basert på avvik & tiltak"}
                                            </p>

                                            {/* List operational factors if any */}
                                            {latest_risk_assessment.factors?.filter((f: any) => f.category === 'operational').length > 0 && (
                                                <ul className="space-y-1 mt-3 pt-3 border-t border-border text-sm">
                                                    {latest_risk_assessment.factors
                                                        .filter((f: any) => f.category === 'operational')
                                                        .map((f: any, i: number) => (
                                                            <li key={i} className="flex items-start gap-2">
                                                                <span>•</span>
                                                                <span className="font-medium">{f.factor_name}</span>
                                                            </li>
                                                        ))}
                                                </ul>
                                            )}
                                        </div>

                                        {/* External Risk Section */}
                                        <div className="space-y-2 pt-4 border-t border-border">
                                            <div className="flex justify-between items-center mb-2">
                                                <label className="text-label">Ekstern Risiko (NVE / Kartverket)</label>
                                                {externalRiskScore > 0 && (
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${externalRiskScore > 50 ? 'bg-destructive/10 text-destructive border-destructive/20' : 'bg-surface text-foreground border-border'}`}>
                                                        Score: {Math.round(externalRiskScore)}%
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-sm p-4 glass-card">
                                                {latest_risk_assessment?.factors?.filter((f: any) => f.category === 'external').length > 0 ? (
                                                    <ul className="space-y-2">
                                                        {latest_risk_assessment.factors
                                                            .filter((f: any) => f.category === 'external')
                                                            .map((f: any, i: number) => (
                                                                <li key={i} className="flex items-start gap-2">
                                                                    <span className="text-primary mt-1">●</span>
                                                                    <div className="flex-1">
                                                                        <div className="font-medium text-foreground">{f.factor_name}</div>
                                                                        {f.calculated_score > 0 && (
                                                                            <div className="text-xs text-muted">Bidrag: {Math.round(f.calculated_score)}%</div>
                                                                        )}
                                                                    </div>
                                                                </li>
                                                            ))}
                                                    </ul>
                                                ) : (
                                                    <div className="text-gray-400 italic flex items-center gap-2 font-medium">
                                                        <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                                        Ingen kjente eksterne risikofaktorer
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Economic Risk Section */}
                                        <div className="space-y-2 pt-4 border-t border-border">
                                            <div className="flex justify-between items-center mb-2">
                                                <label className="text-label">Økonomisk Risiko (Indikatorer)</label>
                                                {economicRiskScore > 0 && (
                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${economicRiskScore > 40 ? 'bg-destructive/10 text-destructive border-destructive/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}`}>
                                                        Score: {Math.round(economicRiskScore)}%
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-sm p-4 glass-card space-y-3">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-muted">Kostnad/Leie forhold</span>
                                                    <span className={`font-mono font-bold ${finalAnnualRent > 0 && (totalCosts / finalAnnualRent) > 1 ? 'text-destructive' : 'text-foreground'}`}>
                                                        {finalAnnualRent > 0 ? ((totalCosts / finalAnnualRent) * 100).toFixed(0) : 0}%
                                                    </span>
                                                </div>
                                                {finalAnnualRent > 0 && (totalCosts / finalAnnualRent) > 0.8 && (
                                                    <div className="text-xs text-amber-500 flex items-center gap-1">
                                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                                        Høyt kostnadsnivå i forhold til leieinntekter (+{(totalCosts / finalAnnualRent) > 1.0 ? 40 : 20}%)
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="text-right text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                                            Sist vurdert: {new Date(latest_risk_assessment.assessment_date).toLocaleDateString()}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-8 text-center text-muted border border-dashed border-border rounded-xl font-medium">
                                        Ingen aktive risikovurderinger funnet.
                                    </div>
                                )}
                            </motion.div>

                            {/* Internal Control Widget */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.25 }}
                                className="glass-card p-6"
                            >
                                <DataTooltip content="Internkontroll: Avvik fra sjekklister og HMS-tiltak. Et avvik er en avvikelse fra krav eller plan (f.eks. manglende brannslukker, forfalt inspeksjon). Sjekklister brukes til systematisk oppfølging.">
                                    <h3 className="font-bold flex items-center gap-2 mb-4 text-foreground">
                                        <span className="text-xl">📋</span> Internkontroll
                                    </h3>
                                </DataTooltip>
                                <InternalControlWidget propertyId={property.property_id} />
                            </motion.div>

                            {/* Økonomiavd. regnskap 2026 — kostnadssjekk */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.23 }}
                                className="glass-card p-6"
                            >
                                <div className="flex items-center justify-between gap-3 mb-3">
                                    <h3 className="font-bold text-foreground">Økonomi 2026</h3>
                                    <span className="text-xs text-muted bg-surface/60 px-2 py-0.5 rounded border border-border">Regnskap 2026</span>
                                </div>

                                {costStatusLoading ? (
                                    <p className="text-xs text-muted">Sjekker kostnader…</p>
                                ) : (
                                    <div className="space-y-2">
                                        <p className="text-sm">
                                            Har data i 2026:{" "}
                                            <span className={hasCostsForYear ? "font-bold text-success" : "font-bold text-danger"}>
                                                {hasCostsForYear ? "Ja" : "Nei"}
                                            </span>
                                        </p>
                                        {costTotals && (
                                            <div className="text-xs text-muted space-y-0.5">
                                                <div>Total: {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(costTotals.total || 0)}</div>
                                                <div>Lokaler: {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(costTotals.rent || 0)}</div>
                                                <div>Drift + vedlikehold: {new Intl.NumberFormat('nb-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(costTotals.other || 0)}</div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </motion.div>

                            {/* Økonomiavdelingens vedtatte budsjett 2026 */}
                            <OkonomiFinansCard propertyId={property.property_id} />

                            {/* Cost Analysis Widget */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3 }}
                                className="glass-card p-6"
                            >
                                <DataTooltip content="Kostnadsanalyse: Sammenligner bokførte kostnader med husleie. Forhold = kostnader ÷ husleie. Grønt &lt; 150%, gul/rød = høyt forhold. «Poster» = antall utgiftsposter i kategorien.">
                                    <h3 className="font-bold flex items-center gap-2 mb-4 text-foreground">
                                        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                        </svg>
                                        Kostnadsanalyse
                                    </h3>
                                </DataTooltip>
                                <CostAnalysisWidget propertyId={property.property_id} selectedYear={costYear} />
                            </motion.div>

                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
