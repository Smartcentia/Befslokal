"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/app/components/ui/Header";
import { fetchAPI } from "@/lib/api/client";
import {
    Building2,
    Layers,
    FileText,
    Users,
    ChevronDown,
    ChevronRight,
    ExternalLink,
    TrendingUp,
} from "lucide-react";

interface PropertyItem {
    property_id: string;
    name?: string | null;
    address?: string | null;
    city?: string | null;
    region?: string | null;
    usage?: string | null;
}

interface UnitItem {
    unit_id: string;
    property_id: string;
    property_name?: string | null;
    purpose?: string | null;
    area_sqm?: number | null;
}

interface ContractItem {
    contract_id: string;
    unit_id?: string | null;
    party_id?: string | null;
    status?: string | null;
    party_name?: string | null;
    property_name?: string | null;
    property_id?: string | null;
}

interface PartyItem {
    party_id: string;
    name: string;
    orgnr?: string | null;
}

interface OverviewData {
    properties: PropertyItem[];
    units: UnitItem[];
    contracts: ContractItem[];
    parties: PartyItem[];
}

interface RegionKategori {
    kategori: string;
    total: number;
    antall: number;
}

interface RegionRow {
    region: string;
    total: number;
    antall: number;
    kategorier: RegionKategori[];
}

interface GlRegionalData {
    year: number;
    totalt: number;
    antall_totalt: number;
    regioner: RegionRow[];
}

interface BudgetProperty {
    property_id: string;
    name: string;
    address: string;
    city: string;
    region: string;
    kategorier: Record<string, number>;
    total: number;
}

interface BudgetRegion {
    region: string;
    total: number;
    eiendommer: BudgetProperty[];
}

interface BudgetSummary {
    year: number;
    /** xgb70 | xgb50 — XGB-gulv-scenario, ikke «prosent bruk». */
    scenario?: string;
    /** f.eks. holt_winters_2027_xgb70 eller eldre holt_winters_2027 */
    budget_data_source?: string | null;
    totalt: number;
    totalt_eiendommer: number;
    antall_eiendommer: number;
    regioner: BudgetRegion[];
    uten_eiendom: {
        total: number;
        note: string;
        regioner: Array<{ region: string; total: number; kategorier: Record<string, number> }>;
    };
}

const LIMIT = 500;
const GL_YEAR = 2025;

function scenarioLabel(scenario: string | undefined): string {
    const s = (scenario || "xgb70").toLowerCase();
    if (s === "xgb50") return "xgb50 (XGB-gulv 50 %)";
    return "xgb70 (XGB-gulv 70 %)";
}

function fmt(n: number): string {
    return new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 0 }).format(n);
}

export default function OversiktPage() {
    const [data, setData] = useState<OverviewData | null>(null);
    const [glData, setGlData] = useState<GlRegionalData | null>(null);
    const [budgetSummary, setBudgetSummary] = useState<BudgetSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [openSection, setOpenSection] = useState<"eiendommer" | "avdelinger" | "kontrakter" | "leietakere" | "gl-regional" | "prognose-2027" | null>("eiendommer");
    const [expandedRegion, setExpandedRegion] = useState<string | null>(null);
    const [expandedBudgetRegion, setExpandedBudgetRegion] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                setLoading(true);
                setError(null);
                const [res, gl, budget] = await Promise.all([
                    fetchAPI<OverviewData>(`/overview?limit=${LIMIT}`),
                    fetchAPI<GlRegionalData>(`/dashboard/gl-regional-costs?year=${GL_YEAR}`).catch(() => null),
                    fetchAPI<BudgetSummary>(`/financials/budget-summary?year=2027`).catch(() => null),
                ]);
                setData(res);
                setGlData(gl);
                setBudgetSummary(budget);
            } catch (e) {
                setError(e instanceof Error ? e.message : "Kunne ikke laste oversikt");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    if (loading && !data) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <Header />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 pt-24">
                    <div className="flex items-center gap-3 text-muted">
                        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        Laster oversikt…
                    </div>
                </main>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-background text-foreground">
                <Header />
                <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 pt-24">
                    <p className="text-destructive">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                    >
                        Prøv igjen
                    </button>
                </main>
            </div>
        );
    }

    const d = data!;
    const sections = [
        {
            id: "eiendommer" as const,
            title: "Eiendommer",
            count: d.properties.length,
            icon: Building2,
        },
        {
            id: "avdelinger" as const,
            title: "Avdelinger / Enheter",
            count: d.units.length,
            icon: Layers,
        },
        {
            id: "kontrakter" as const,
            title: "Kontrakter",
            count: d.contracts.length,
            icon: FileText,
        },
        {
            id: "leietakere" as const,
            title: "Leietakere",
            count: d.parties.length,
            icon: Users,
        },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground font-sans pb-20">
            <Header />
            <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-foreground tracking-tight">
                        Oversikt
                    </h1>
                    <p className="text-muted mt-2">
                        Alle eiendommer, avdelinger, kontrakter og leietakere (tilgangsfiltrert).
                    </p>
                </div>

                <div className="space-y-4">
                    {sections.map(({ id, title, count, icon: Icon }) => (
                        <div
                            key={id}
                            className="rounded-xl border border-border bg-surface overflow-hidden"
                        >
                            <button
                                type="button"
                                onClick={() =>
                                    setOpenSection(openSection === id ? null : id)
                                }
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    {openSection === id ? (
                                        <ChevronDown className="w-5 h-5 text-primary shrink-0" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-muted shrink-0" />
                                    )}
                                    <Icon className="w-5 h-5 text-primary shrink-0" />
                                    <span className="font-semibold text-foreground">{title}</span>
                                    <span className="text-sm text-muted">({count})</span>
                                </div>
                            </button>

                            {openSection === id && (
                                <div className="border-t border-border bg-background/50 overflow-x-auto">
                                    {id === "eiendommer" && (
                                        <table className="w-full enterprise-table">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-3 text-left">Navn</th>
                                                    <th className="px-4 py-3 text-left">Adresse</th>
                                                    <th className="px-4 py-3 text-left">Sted</th>
                                                    <th className="px-4 py-3 text-left">Region</th>
                                                    <th className="w-10"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {d.properties.map((p) => (
                                                    <tr key={p.property_id} className="border-t border-border">
                                                        <td className="px-4 py-3 font-medium">{p.name || "—"}</td>
                                                        <td className="px-4 py-3 text-muted">{p.address || "—"}</td>
                                                        <td className="px-4 py-3 text-muted">{p.city || "—"}</td>
                                                        <td className="px-4 py-3 text-muted">{p.region || "—"}</td>
                                                        <td>
                                                            <Link
                                                                href={`/properties/${p.property_id}`}
                                                                className="p-2 text-primary hover:bg-primary/10 rounded"
                                                                title="Åpne eiendom"
                                                            >
                                                                <ExternalLink size={16} />
                                                            </Link>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}

                                    {id === "avdelinger" && (
                                        <table className="w-full enterprise-table">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-3 text-left">Enhet</th>
                                                    <th className="px-4 py-3 text-left">Eiendom</th>
                                                    <th className="px-4 py-3 text-left">Formål</th>
                                                    <th className="px-4 py-3 text-right">Areal (m²)</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {d.units.map((u) => (
                                                    <tr key={u.unit_id} className="border-t border-border">
                                                        <td className="px-4 py-3 font-mono text-sm">{String(u.unit_id).slice(0, 8)}…</td>
                                                        <td className="px-4 py-3 text-muted">{u.property_name || "—"}</td>
                                                        <td className="px-4 py-3 text-muted">{u.purpose || "—"}</td>
                                                        <td className="px-4 py-3 text-right text-muted">{u.area_sqm ?? "—"}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}

                                    {id === "kontrakter" && (
                                        <table className="w-full enterprise-table">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-3 text-left">Leietaker</th>
                                                    <th className="px-4 py-3 text-left">Eiendom</th>
                                                    <th className="px-4 py-3 text-left">Status</th>
                                                    <th className="w-10"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {d.contracts.map((c) => (
                                                    <tr key={c.contract_id} className="border-t border-border">
                                                        <td className="px-4 py-3 font-medium">{c.party_name || "—"}</td>
                                                        <td className="px-4 py-3 text-muted">{c.property_name || "—"}</td>
                                                        <td className="px-4 py-3">
                                                            <span
                                                                className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                                                                    c.status === "active"
                                                                        ? "bg-green-500/20 text-green-600 dark:text-green-400"
                                                                        : "bg-muted text-muted"
                                                                }`}
                                                            >
                                                                {c.status === "active" ? "Aktiv" : c.status || "—"}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <Link
                                                                href={`/contracts/${c.contract_id}`}
                                                                className="p-2 text-primary hover:bg-primary/10 rounded"
                                                                title="Åpne kontrakt"
                                                            >
                                                                <ExternalLink size={16} />
                                                            </Link>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}

                                    {id === "leietakere" && (
                                        <table className="w-full enterprise-table">
                                            <thead>
                                                <tr>
                                                    <th className="px-4 py-3 text-left">Navn</th>
                                                    <th className="px-4 py-3 text-left">Org.nr</th>
                                                    <th className="w-10"></th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {d.parties.map((p) => (
                                                    <tr key={p.party_id} className="border-t border-border">
                                                        <td className="px-4 py-3 font-medium">{p.name}</td>
                                                        <td className="px-4 py-3 text-muted font-mono text-sm">{p.orgnr || "—"}</td>
                                                        <td>
                                                            <Link
                                                                href={`/parties/${p.party_id}`}
                                                                className="p-2 text-primary hover:bg-primary/10 rounded"
                                                                title="Åpne part"
                                                            >
                                                                <ExternalLink size={16} />
                                                            </Link>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}

                                    {((id === "eiendommer" && d.properties.length === 0) ||
                                        (id === "avdelinger" && d.units.length === 0) ||
                                        (id === "kontrakter" && d.contracts.length === 0) ||
                                        (id === "leietakere" && d.parties.length === 0)) && (
                                        <p className="px-5 py-8 text-center text-muted">Ingen rader å vise.</p>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}

                    {/* GL Regional / Administrative Costs */}
                    {glData && glData.totalt > 0 && (
                        <div className="rounded-xl border border-border bg-surface overflow-hidden">
                            <button
                                type="button"
                                onClick={() => setOpenSection(openSection === "gl-regional" ? null : "gl-regional")}
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    {openSection === "gl-regional" ? (
                                        <ChevronDown className="w-5 h-5 text-primary shrink-0" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-muted shrink-0" />
                                    )}
                                    <TrendingUp className="w-5 h-5 text-primary shrink-0" />
                                    <span className="font-semibold text-foreground">
                                        Regionale / administrative kostnader {GL_YEAR}
                                    </span>
                                    <span className="text-sm text-muted">
                                        ({fmt(glData.antall_totalt)} transaksjoner · ikke koblet til eiendom)
                                    </span>
                                </div>
                                <span className="font-mono font-semibold text-foreground shrink-0">
                                    {fmt(glData.totalt)} kr
                                </span>
                            </button>

                            {openSection === "gl-regional" && (
                                <div className="border-t border-border bg-background/50 overflow-x-auto">
                                    <table className="w-full enterprise-table">
                                        <thead>
                                            <tr>
                                                <th className="px-4 py-3 text-left">Region</th>
                                                <th className="px-4 py-3 text-right">Totalt (kr)</th>
                                                <th className="px-4 py-3 text-right">Andel</th>
                                                <th className="px-4 py-3 text-right">Transaksjoner</th>
                                                <th className="px-4 py-3 text-left">Kategorier</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {glData.regioner.map((reg) => (
                                                <>
                                                    <tr
                                                        key={reg.region}
                                                        className="border-t border-border cursor-pointer hover:bg-muted/20"
                                                        onClick={() =>
                                                            setExpandedRegion(
                                                                expandedRegion === reg.region ? null : reg.region
                                                            )
                                                        }
                                                    >
                                                        <td className="px-4 py-3 font-medium flex items-center gap-2">
                                                            {expandedRegion === reg.region ? (
                                                                <ChevronDown className="w-4 h-4 text-muted" />
                                                            ) : (
                                                                <ChevronRight className="w-4 h-4 text-muted" />
                                                            )}
                                                            {reg.region}
                                                        </td>
                                                        <td className="px-4 py-3 text-right font-mono text-sm">
                                                            {fmt(reg.total)}
                                                        </td>
                                                        <td className="px-4 py-3 text-right text-muted text-sm">
                                                            {glData.totalt > 0
                                                                ? ((reg.total / glData.totalt) * 100).toFixed(1)
                                                                : "0"}
                                                            %
                                                        </td>
                                                        <td className="px-4 py-3 text-right text-muted text-sm">
                                                            {fmt(reg.antall)}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-muted">
                                                            {reg.kategorier.map((k) => k.kategori).join(", ")}
                                                        </td>
                                                    </tr>
                                                    {expandedRegion === reg.region &&
                                                        reg.kategorier.map((k) => (
                                                            <tr
                                                                key={`${reg.region}-${k.kategori}`}
                                                                className="border-t border-border/50 bg-muted/10"
                                                            >
                                                                <td className="px-4 py-2 pl-10 text-sm text-muted">
                                                                    {k.kategori}
                                                                </td>
                                                                <td className="px-4 py-2 text-right font-mono text-sm text-muted">
                                                                    {fmt(k.total)}
                                                                </td>
                                                                <td className="px-4 py-2 text-right text-xs text-muted">
                                                                    {reg.total > 0
                                                                        ? ((k.total / reg.total) * 100).toFixed(1)
                                                                        : "0"}
                                                                    %
                                                                </td>
                                                                <td className="px-4 py-2 text-right text-sm text-muted">
                                                                    {fmt(k.antall)}
                                                                </td>
                                                                <td></td>
                                                            </tr>
                                                        ))}
                                                </>
                                            ))}
                                        </tbody>
                                        <tfoot>
                                            <tr className="border-t-2 border-border font-semibold">
                                                <td className="px-4 py-3">Totalt</td>
                                                <td className="px-4 py-3 text-right font-mono">
                                                    {fmt(glData.totalt)}
                                                </td>
                                                <td className="px-4 py-3 text-right text-muted">100%</td>
                                                <td className="px-4 py-3 text-right font-mono">
                                                    {fmt(glData.antall_totalt)}
                                                </td>
                                                <td></td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            )}
                        </div>
                    )}
                    {/* Prognose 2027 */}
                    {budgetSummary && budgetSummary.antall_eiendommer > 0 && (
                        <div className="rounded-xl border border-blue-500/30 bg-surface overflow-hidden">
                            <div className="px-5 py-3 border-b border-blue-500/20 bg-amber-500/5 dark:bg-amber-950/20">
                                <p className="text-xs font-semibold uppercase tracking-wide text-amber-800 dark:text-amber-200 mb-2">
                                    Viktig — hva tallene betyr
                                </p>
                                <ul className="text-sm text-foreground/90 space-y-1.5 list-disc pl-4">
                                    <li>
                                        Prosentene <strong>70 %</strong> og <strong>50 %</strong> i Excel er{" "}
                                        <strong>XGBoost-gulv-scenarier</strong> (hvor streng den nedre grensen er mot ML-prediksjon),{" "}
                                        ikke «indre forbruk», aktivitetsnivå eller Holt-Winters α/β.
                                    </li>
                                    <li>
                                        <strong>GL {GL_YEAR}</strong> ovenfor er faktiske transaksjoner; <strong>prognose 2027</strong> her er modellert budsjett — samme sammenligning som i Excel krever bevisst tolkning.
                                    </li>
                                    <li>
                                        Denne totalen bruker scenario{" "}
                                        <span className="font-mono font-medium">{scenarioLabel(budgetSummary.scenario)}</span>
                                        {budgetSummary.budget_data_source != null && budgetSummary.budget_data_source !== "" && (
                                            <>
                                                {" "}
                                                (<span className="font-mono text-xs">{budgetSummary.budget_data_source}</span>
                                                {budgetSummary.budget_data_source === `holt_winters_${budgetSummary.year}` && " — eldre datakilde uten xgb-suffiks"})
                                            </>
                                        )}
                                        . Eiendommer uten prediksjon inngår ikke i summen.
                                    </li>
                                </ul>
                                <p className="mt-2 text-xs text-muted-foreground">
                                    Mer forklaring:{" "}
                                    <Link href="/financials/prediksjon" className="text-primary underline-offset-2 hover:underline">
                                        Prediksjon 2027
                                    </Link>
                                    {" · "}
                                    ark <strong>Forklaring</strong> i Excel-eksport.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setOpenSection(openSection === "prognose-2027" ? null : "prognose-2027")}
                                className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                            >
                                <div className="flex items-center gap-3 flex-wrap">
                                    {openSection === "prognose-2027" ? (
                                        <ChevronDown className="w-5 h-5 text-blue-400 shrink-0" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-muted shrink-0" />
                                    )}
                                    <TrendingUp className="w-5 h-5 text-blue-400 shrink-0" />
                                    <span className="font-semibold text-foreground">Prognose 2027 — Holt-Winters + XGB-gulv</span>
                                    <span className="text-sm text-muted">
                                        ({budgetSummary.antall_eiendommer} eiendommer · alle regioner)
                                    </span>
                                    <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded-full">α=0.7 β=0.3</span>
                                    <span className="text-xs px-2 py-0.5 bg-amber-500/15 text-amber-800 dark:text-amber-200 rounded-full">
                                        {scenarioLabel(budgetSummary.scenario)}
                                    </span>
                                </div>
                                <span className="font-mono font-semibold text-foreground shrink-0">
                                    {fmt(budgetSummary.totalt)} kr
                                </span>
                            </button>

                            {openSection === "prognose-2027" && (
                                <div className="border-t border-border bg-background/50">
                                    {/* Region-accordion */}
                                    {budgetSummary.regioner.map((reg) => (
                                        <div key={reg.region} className="border-b border-border/50">
                                            <button
                                                type="button"
                                                onClick={() => setExpandedBudgetRegion(expandedBudgetRegion === reg.region ? null : reg.region)}
                                                className="w-full flex items-center justify-between px-5 py-3 hover:bg-muted/20 transition-colors text-sm"
                                            >
                                                <div className="flex items-center gap-2">
                                                    {expandedBudgetRegion === reg.region ? (
                                                        <ChevronDown className="w-4 h-4 text-muted" />
                                                    ) : (
                                                        <ChevronRight className="w-4 h-4 text-muted" />
                                                    )}
                                                    <span className="font-semibold">{reg.region}</span>
                                                    <span className="text-muted">({reg.eiendommer.length} eiendommer)</span>
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <span className="text-xs text-muted">
                                                        {budgetSummary.totalt_eiendommer > 0
                                                            ? ((reg.total / budgetSummary.totalt_eiendommer) * 100).toFixed(1)
                                                            : "0"}% av total
                                                    </span>
                                                    <span className="font-mono font-semibold">{fmt(reg.total)} kr</span>
                                                </div>
                                            </button>

                                            {expandedBudgetRegion === reg.region && (
                                                <div className="overflow-x-auto">
                                                    <table className="w-full enterprise-table text-sm">
                                                        <thead>
                                                            <tr className="bg-muted/10">
                                                                <th className="px-6 py-2 text-left font-medium">Eiendom</th>
                                                                <th className="px-4 py-2 text-left font-medium text-muted">Sted</th>
                                                                <th className="px-4 py-2 text-right font-medium">Drift</th>
                                                                <th className="px-4 py-2 text-right font-medium">Investering</th>
                                                                <th className="px-4 py-2 text-right font-medium">Eiendom</th>
                                                                <th className="px-4 py-2 text-right font-medium">Totalt (kr)</th>
                                                                <th className="w-8"></th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {reg.eiendommer
                                                                .sort((a, b) => b.total - a.total)
                                                                .map((prop) => (
                                                                    <tr key={prop.property_id} className="border-t border-border/40 hover:bg-muted/10">
                                                                        <td className="px-6 py-2 font-medium">{prop.name}</td>
                                                                        <td className="px-4 py-2 text-muted">{prop.city || prop.address || "—"}</td>
                                                                        <td className="px-4 py-2 text-right font-mono text-muted">
                                                                            {prop.kategorier.operations ? fmt(prop.kategorier.operations) : "—"}
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-mono text-muted">
                                                                            {prop.kategorier.investment ? fmt(prop.kategorier.investment) : "—"}
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-mono text-muted">
                                                                            {prop.kategorier.property ? fmt(prop.kategorier.property) : "—"}
                                                                        </td>
                                                                        <td className="px-4 py-2 text-right font-mono font-semibold">{fmt(prop.total)}</td>
                                                                        <td className="pr-2">
                                                                            <Link
                                                                                href={`/properties/${prop.property_id}`}
                                                                                className="p-1 text-primary hover:bg-primary/10 rounded inline-flex"
                                                                            >
                                                                                <ExternalLink size={14} />
                                                                            </Link>
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                        </tbody>
                                                        <tfoot>
                                                            <tr className="border-t-2 border-border bg-muted/10 font-semibold">
                                                                <td className="px-6 py-2" colSpan={5}>Regiontotal</td>
                                                                <td className="px-4 py-2 text-right font-mono">{fmt(reg.total)}</td>
                                                                <td></td>
                                                            </tr>
                                                        </tfoot>
                                                    </table>
                                                </div>
                                            )}
                                        </div>
                                    ))}

                                    {/* Regionale/admin kostnader uten eiendom */}
                                    {budgetSummary.uten_eiendom.total > 0 && (
                                        <div className="border-b border-border/50">
                                            <div className="flex items-center justify-between px-5 py-3 text-sm bg-muted/5">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-muted">Regionale / administrative kostnader</span>
                                                    <span className="text-xs text-muted/70">(ikke koblet til eiendom — {budgetSummary.uten_eiendom.note})</span>
                                                </div>
                                                <span className="font-mono font-semibold text-muted">{fmt(budgetSummary.uten_eiendom.total)} kr</span>
                                            </div>
                                        </div>
                                    )}

                                    {/* Totalsum */}
                                    <div className="flex items-center justify-between px-5 py-4 bg-blue-500/5 border-t border-blue-500/20">
                                        <span className="font-semibold text-foreground">Total prognose 2027</span>
                                        <span className="font-mono font-bold text-foreground text-lg">{fmt(budgetSummary.totalt)} kr</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
