
"use client";

import { useState, useEffect, useTransition } from "react";
import { getProperties, getContracts, getRegionalFinancials, Property, Contract } from "@/lib/api";
import { useFeatureFlags } from "@/contexts/FeatureFlagsContext";
import { financialAnalysisApi, SupplierStats, CommonPatterns } from "@/lib/api/financialAnalysisApi";
import { getBudgetSummary, getSalaryCosts, type SalaryCostSummary } from "@/lib/api/budgetApi";
import { getFinanceBudgetSummary, type FinanceBudgetSummary, type FinanceBudgetByProperty } from "@/lib/api/financeBudgetApi";
import Sammenligning2026 from "@/components/financial/Sammenligning2026";
import { getGLFinancialBulk, getPropertiesWithoutCosts, getDiscontinuedProperties, getCostsWithoutProperty, getCostsWithoutPropertyPivot, getOrphanTransactions, getInnkjøpsanalyseHusleie, getGodkjenteEiendommer, getTotalKostPerRegion, type TotalKostPerRegion, PropertyWithoutCosts, DiscontinuedProperty, OrphanTransaction, CostsWithoutPropertyPivot } from "@/lib/api/propertiesApi";
import Header from "@/app/components/ui/Header";
import Accordion from "@/app/components/ui/Accordion";
import { motion, AnimatePresence } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import DataTooltip from "@/app/components/ui/DataTooltip";
import { ChevronDown, ChevronUp, ChevronRight, TrendingUp, Building2, MapPin, BadgePercent, Wallet, HardHat, TrendingDown, AlertTriangle, BarChart3, Users, History, Clock, Ruler, Zap, Home, Link2, Landmark, Hash, Layers, GitBranch } from "lucide-react";
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import React, { Suspense } from "react";
import TransactionExplorer from "@/components/financials/TransactionExplorer";
import ContractsPivotView from "@/components/financials/ContractsPivotView";
import { isUtgatt } from "@/lib/utils/utgatt";

interface FinancialRow {
    property: Property;
    contractedRent: number;   // Kontraktsfestet: fra Innkjøpsanalyse eller kontrakter
    aggregertHusleie: number; // Sum på tvers av regioner (fra Innkjøpsanalyse)
    glRent: number;           // Fra GL-bokføring (faktisk betalt husleie)
    actualAccountingSpend: number;
    totalPropertyExpense: number;
    budget?: number;           // BEFS 2026 prediksjon
    budget2027?: number;
    financeBudget2026?: number; // Vedtatt budsjett 2026 fra økonomi-avdelingen (Beløp DA)
    kontant2026?: number;      // Faktisk brukt 2026 YTD (Kontantbeløp)
    okoRegn2025?: number;      // Økonomi regnskap 2025 (Kontant 2025)
    okoRegn2025ByCategory?: Record<string, number>; // Kategorifordeling for BEFS-beregning
    befsPred2026?: number;     // BEFS prediksjon 2026 = okoRegn2025 × vekstfaktorer
    salaryCost?: number;
    activeContracts: Contract[];
    expenses: any[];
}

interface RegionalData {
    region: string;
    maintenance: number;
    rent: number;        // Kontraktsfestet husleie
    glRent: number;      // GL-bokført husleie
    budget: number;
    budget2027: number;
    financeBudget2026: number; // Vedtatt budsjett 2026 fra økonomi-avdelingen (Beløp DA)
    kontant2026: number;       // Faktisk brukt 2026 YTD (Kontantbeløp)
    okoRegn2025: number;       // Økonomi regnskap 2025
    befsPred2026: number;      // BEFS prediksjon 2026 = okoRegn2025 × vekstfaktorer
    salaryCost: number;
    rows: FinancialRow[];
}

/** Klassifiserer leverandør: leietaker = utleier vi betaler leie til; løpende = leverandør for drift/vedlikehold */
function getSupplierType(category: string): "leietaker" | "løpende" {
    if (!category || typeof category !== "string") return "løpende";
    const c = category.toLowerCase();
    // Eksplisitte fraser for leie/utleier (unngår falske treff som "fellesutgifter")
    if (c.includes("leie lokaler")) return "leietaker";
    if (c.includes("husleie")) return "leietaker";
    if (c.includes("leie av lokaler")) return "leietaker";
    if (c.includes("leieavtale")) return "leietaker";
    return "løpende";
}

/** Underkategori for løpende utgifter (strøm, fellesutgifter, annen kostnad). */
function getLøpendeSubcategory(category: string): string {
    if (!category || typeof category !== "string") return "Annen kostnad";
    const c = category.toLowerCase();
    if (c.includes("strøm") || c.includes("oppvarming")) return "Strøm og oppvarming";
    if (c.includes("fellesutgift")) return "Fellesutgifter";
    return "Annen kostnad";
}

/** Vekstfaktorer per kategori for BEFS-prediksjon 2026 (basert på økonomi 2025 regnskap) */
const BEFS_VEKSTFAKTORER: Record<string, number> = {
    Lokaler: 1.047,      // Husleie: KPI-justert +4,7%
    Drift: 1.100,        // Drift og løpende: +10,0%
    Vedlikehold: 1.100,  // Vedlikehold: +10,0%
};

/** Beregn BEFS 2026-prediksjon basert på økonomi 2025 regnskap × vekstfaktorer per kategori */
function computeBefsPred2026(byCategory: Record<string, number>): number {
    return Object.entries(byCategory).reduce((sum, [cat, amount]) => {
        const factor = BEFS_VEKSTFAKTORER[cat] ?? 1.050; // default +5% for ukjente kategorier
        return sum + amount * factor;
    }, 0);
}

/** Hent forbruk (total_costs) for siste 3 år fra eiendoms financial_history. */
function getLast3YearsForbruk(property: Property): { year: number; total_costs: number }[] {
    const history = property?.external_data?.financial_history;
    if (!history || typeof history !== "object") return [];
    const entries = Object.entries(history)
        .filter(([, data]) => data && typeof data === "object" && typeof (data as { total_costs?: number }).total_costs === "number")
        .map(([yearStr, data]) => ({ year: parseInt(yearStr, 10), total_costs: (data as { total_costs: number }).total_costs }));
    return entries.sort((a, b) => b.year - a.year).slice(0, 3);
}

const FORBRUK_TOOLTIP =
    "Totale utgifter (vedlikehold, strøm, fellesutgifter m.m.) per år fra historisk regnskapsdata. Ikke bare strøm – alle kostnader for eiendommen/regionen.";

/** Aggreger forbruk siste 3 år på tvers av eiendommer i en region. */
function getRegionalLast3YearsForbruk(rows: FinancialRow[]): { year: number; total_costs: number }[] {
    const byYear: Record<number, number> = {};
    rows.forEach((row) => {
        getLast3YearsForbruk(row.property).forEach(({ year, total_costs }) => {
            byYear[year] = (byYear[year] ?? 0) + total_costs;
        });
    });
    return Object.entries(byYear)
        .map(([y, t]) => ({ year: parseInt(y, 10), total_costs: t }))
        .sort((a, b) => b.year - a.year)
        .slice(0, 3);
}

function FinancialsContent() {
    const searchParams = useSearchParams();
    const viewType = searchParams.get('view') || 'rent';

    const [regionalRows, setRegionalRows] = useState<RegionalData[]>([]);
    const [allPropertyRows, setAllPropertyRows] = useState<FinancialRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedProperty, setExpandedProperty] = useState<string | null>(null);
    const [supplierStats, setSupplierStats] = useState<SupplierStats | null>(null);
    const [commonPatterns, setCommonPatterns] = useState<CommonPatterns | null>(null);
    const [loadingAnalysis, setLoadingAnalysis] = useState(false);
    const [activeTab, setActiveTab] = useState<'overview' | 'suppliers' | 'catalog' | 'invoices' | 'patterns' | 'transactions' | 'missing-costs' | 'discontinued-properties' | 'costs-without-property' | 'contracts-pivot' | 'sammenligning-2026'>('overview');
    const [isTabPending, startTabTransition] = useTransition();
    const [supplierFilter, setSupplierFilter] = useState<'all' | 'leietaker' | 'løpende'>('all');
    const [supplierSearch, setSupplierSearch] = useState('');
    const [supplierDetailsModal, setSupplierDetailsModal] = useState<SupplierStats["suppliers"][0] | null>(null);
    const [supplierCatalog, setSupplierCatalog] = useState<Array<{ Leverandør: string; Tjenester: string }>>([]);
    const [catalogLoaded, setCatalogLoaded] = useState(false);
    const [catalogLoading, setCatalogLoading] = useState(false);
    const [invoicesLoaded, setInvoicesLoaded] = useState(false);
    const [catalogVisibleCount, setCatalogVisibleCount] = useState(50);
    const [invoicesVisibleCount, setInvoicesVisibleCount] = useState(50);
    const [statsVisibleCount, setStatsVisibleCount] = useState(50);
    const [selectedYear, setSelectedYear] = useState<number>(2025);

    // Nye analyser – lazy-load
    const [rentGapData, setRentGapData] = useState<any[]>([]);
    const [rentGapLoaded, setRentGapLoaded] = useState(false);
    const [rentGapLoading, setRentGapLoading] = useState(false);
    const [rentReconciliation, setRentReconciliation] = useState<{
        year: number; contracted_rent_total: number; gl_lease_total: number;
        gl_lease_with_property: number; gl_lease_orphan: number; gl_other_total: number;
        gap: number; gap_pct: number | null; accounts: Array<{ account_name: string; total: number; with_property: number; orphan: number; is_lease: boolean }>;
        contract_count: number;
    } | null>(null);
    const [rentReconciliationLoading, setRentReconciliationLoading] = useState(false);

    // Reset avstemming når år endres
    useEffect(() => {
        setRentReconciliation(null);
    }, [selectedYear]);
    const [yoyData, setYoyData] = useState<any[]>([]);
    const [yoyLoaded, setYoyLoaded] = useState(false);
    const [yoyLoading, setYoyLoading] = useState(false);
    const [monthlyData, setMonthlyData] = useState<any[]>([]);
    const [monthlyLoaded, setMonthlyLoaded] = useState(false);
    const [monthlyLoading, setMonthlyLoading] = useState(false);

    const [missingCostsData, setMissingCostsData] = useState<PropertyWithoutCosts[]>([]);
    const [missingCostsLoaded, setMissingCostsLoaded] = useState(false);
    const [missingCostsLoading, setMissingCostsLoading] = useState(false);

    const [discontinuedPropertiesData, setDiscontinuedPropertiesData] = useState<DiscontinuedProperty[]>([]);
    const [discontinuedPropertiesLoaded, setDiscontinuedPropertiesLoaded] = useState(false);
    const [discontinuedPropertiesLoading, setDiscontinuedPropertiesLoading] = useState(false);
    const [discontinuedBudgetAvailable, setDiscontinuedBudgetAvailable] = useState(true);

    const [orphanGLRent, setOrphanGLRent] = useState(0);
    const [orphanAndreKostnader, setOrphanAndreKostnader] = useState(0);
    const [costsWithoutPropertyData, setCostsWithoutPropertyData] = useState<Array<{ department_code: string; department_name: string; total: number; transaction_count: number }>>([]);
    const [costsWithoutPropertyTotal, setCostsWithoutPropertyTotal] = useState(0);
    const [costsWithoutPropertyLoaded, setCostsWithoutPropertyLoaded] = useState(false);
    const [costsWithoutPropertyLoading, setCostsWithoutPropertyLoading] = useState(false);
    const [costsWithoutPropertyViewMode, setCostsWithoutPropertyViewMode] = useState<'list' | 'pivot'>('list');
    const [costsWithoutPropertyPivotData, setCostsWithoutPropertyPivotData] = useState<CostsWithoutPropertyPivot | null>(null);
    const [costsWithoutPropertyPivotLoaded, setCostsWithoutPropertyPivotLoaded] = useState(false);
    const [costsWithoutPropertyPivotLoading, setCostsWithoutPropertyPivotLoading] = useState(false);
    const [overviewViewMode, setOverviewViewMode] = useState<'accordion' | 'pivot'>('accordion');
    const [expandedOrphanDept, setExpandedOrphanDept] = useState<string | null>(null);
    const [orphanTransactions, setOrphanTransactions] = useState<OrphanTransaction[]>([]);
    const [orphanTxLoading, setOrphanTxLoading] = useState(false);
    const [innkjøpsanalyseTotal, setInnkjøpsanalyseTotal] = useState<number | null>(null);
    const [totalKostPerRegion, setTotalKostPerRegion] = useState<TotalKostPerRegion | null>(null);
    const [godkjenteList, setGodkjenteList] = useState<string[]>([]);
    const [innkjøpsanalyse2025, setInnkjøpsanalyse2025] = useState<{ by_property: Record<string, { aggregert: number }> } | null>(null);
    const [glBulk2024, setGlBulk2024] = useState<{ by_property: Record<string, { faktisk_husleie: number; andre_kostnader: number; totalt: number }>; orphan_faktisk_husleie?: number; orphan_andre_kostnader?: number } | null>(null);
    const [glBulk2025, setGlBulk2025] = useState<{ by_property: Record<string, { faktisk_husleie: number; andre_kostnader: number; totalt: number }>; orphan_faktisk_husleie?: number; orphan_andre_kostnader?: number } | null>(null);
    const [innkjøpsanalyse2024, setInnkjøpsanalyse2024] = useState<{ by_property: Record<string, { aggregert: number }>; total?: number } | null>(null);

    // Vedtatt økonomi-budsjett 2026 (finance_budget-tabellen — adskilt fra prediksjoner)
    const [financeBudget2026, setFinanceBudget2026] = useState<FinanceBudgetSummary | null>(null);
    // Økonomi 2025: regnskap (Kontant 2025) — brukes som base for BEFS-prediksjon 2026
    const [okoRegn2025, setOkoRegn2025] = useState<FinanceBudgetSummary | null>(null);
    // Faktisk brukt 2026 YTD (Kontantbeløp fra Budsjett 2025_2026-fanen)
    const [kontant2026, setKontant2026] = useState<FinanceBudgetSummary | null>(null);

    // Lønnskostnader
    const [salaryCosts, setSalaryCosts] = useState<SalaryCostSummary | null>(null);
    const [salaryByPropertyId, setSalaryByPropertyId] = useState<Map<string, number>>(new Map());

    useEffect(() => {
        async function loadData() {
            setLoading(true);

            try {
                // Parallel fetch inkl. budsjett-oppsummering, GL-data og Innkjøpsanalyse husleie
                const BUDGET_YEAR = 2026;
                const [propsData, contractsData, regionalStats, budgetSummary, financeBudget2026Summary, budgetSummary2027, glBulk, innkjøpsanalyse, godkjenteListData, innkjøpsanalyse2025Data, glBulk2024Data, glBulk2025Data, innkjøpsanalyse2024Data, salaryCostsData, okoRegn2025Summary, kontant2026Summary] = await Promise.all([
                    getProperties(0, 3000),
                    getContracts({ limit: 3000 }),
                    getRegionalFinancials(selectedYear).catch((e) => {
                        console.warn("Failed regional stats, using fallback", e);
                        return [];
                    }),
                    // GL-basert BEFS-prediksjon (beholdes i bakgrunnen for referanse)
                    getBudgetSummary(BUDGET_YEAR, { excludeDataSource: 'holt_winters_2026_xgb70' }).catch(() => null),
                    // Økonomi-avdelingens vedtatte budsjett 2026 (finance_budget-tabellen)
                    getFinanceBudgetSummary(BUDGET_YEAR).catch(() => null),
                    getBudgetSummary(2027).catch(() => null),
                    getGLFinancialBulk(selectedYear).catch(() => null),
                    getInnkjøpsanalyseHusleie(selectedYear).catch(() => null),
                    getGodkjenteEiendommer().catch(() => []),
                    getInnkjøpsanalyseHusleie(2025).catch(() => null),
                    getGLFinancialBulk(2024).catch(() => null),
                    getGLFinancialBulk(2025).catch(() => null),
                    getInnkjøpsanalyseHusleie(2024).catch(() => null),
                    getSalaryCosts(selectedYear).catch(() => null),
                    // Økonomi 2025 regnskap (Kontant 2025) — base for BEFS-prediksjon
                    getFinanceBudgetSummary(2025, 'kontant_2025').catch(() => null),
                    // Faktisk brukt 2026 YTD (Kontantbeløp fra Budsjett 2025_2026-fanen)
                    getFinanceBudgetSummary(2026, 'kontant_2026').catch(() => null),
                ]);
                setGlBulk2024(glBulk2024Data ?? null);
                setGlBulk2025(glBulk2025Data ?? null);
                setInnkjøpsanalyse2024(innkjøpsanalyse2024Data ?? null);
                setSalaryCosts(salaryCostsData ?? null);
                const newSalaryMap = new Map<string, number>();
                (salaryCostsData?.by_property ?? []).forEach((e) => newSalaryMap.set(e.property_id, e.total));
                setSalaryByPropertyId(newSalaryMap);
                setFinanceBudget2026(financeBudget2026Summary ?? null);
                setOkoRegn2025(okoRegn2025Summary ?? null);
                setKontant2026(kontant2026Summary ?? null);
                const budgetByPropertyId = new Map(
                    (budgetSummary?.by_property ?? []).map((b) => [b.property_id, b.total_annual_budget])
                );
                const budgetByPropertyId2027 = new Map(
                    (budgetSummary2027?.by_property ?? []).map((b) => [b.property_id, b.total_annual_budget])
                );
                const financeBudget2026ByPropertyId = new Map(
                    (financeBudget2026Summary?.by_property ?? []).map((b) => [b.property_id, b.total])
                );
                // okoRegn2025: store full object (total + by_category) for BEFS-prediksjon
                const okoRegn2025ByPropertyId = new Map<string, FinanceBudgetByProperty>(
                    (okoRegn2025Summary?.by_property ?? []).map((b) => [b.property_id, b])
                );
                const kontant2026ByPropertyId = new Map(
                    (kontant2026Summary?.by_property ?? []).map((b) => [b.property_id, b.total])
                );

                // Load analysis data (catalog loaded lazily on demand)
                try {
                    const [suppliers, patterns] = await Promise.all([
                        financialAnalysisApi.getSupplierStats(selectedYear),
                        financialAnalysisApi.getCommonPatterns(selectedYear),
                    ]);
                    setSupplierStats(suppliers);
                    setCommonPatterns(patterns);
                } catch (err) {
                    console.error("Failed to load analysis data", err);
                }

                // Map contracts to properties
                const contractsByProperty: Record<string, Contract[]> = {};
                contractsData.forEach(c => {
                    const propId = c.property?.property_id;
                    if (propId) {
                        if (!contractsByProperty[propId]) contractsByProperty[propId] = [];
                        contractsByProperty[propId].push(c);
                    }
                });

                function normalizeRegion(dbRegion: string | null | undefined): string {
                    if (!dbRegion) return "Nasjonal";
                    const val = dbRegion.toLowerCase();
                    if (val.includes("nord") || val.startsWith("01") || val.includes("finnmark")) return "Nord";
                    if (val.includes("midt") || val.includes("trønd") || val.includes("møre") || val.startsWith("50")) return "Midt-Norge";
                    if (val.includes("vest") || val.startsWith("46") || val.includes("rogaland")) {
                        if (val.includes("vestfold")) return "Sør";
                        return "Vest";
                    }
                    if (val.includes("sør") || val.includes("agder") || val.includes("telemark") || val.includes("vestfold")) return "Sør";
                    if (val.includes("øst") || val.includes("oslo") || val.includes("viken") || val.includes("innlandet") || val.includes("akershus")) return "Øst";
                    return dbRegion || "Ukjent Region";
                }

                // Build property rows (Kontraktsfestet fra Innkjøpsanalyse når tilgjengelig, ellers kontrakter)
                const allRows: FinancialRow[] = propsData.map(p => {
                    const pContracts = contractsByProperty[p.property_id] || [];
                    const activeContracts = pContracts.filter(c => c.status === 'active');
                    const contractedFromContracts = activeContracts.reduce((sum, c) =>
                        sum + ((typeof c.amount === 'object' ? c.amount?.amount_per_year : c.amount) || 0), 0
                    );
                    const reg = normalizeRegion(p.region);
                    const innkjøpsData = innkjøpsanalyse?.by_property?.[p.property_id];
                    const contractedRent = innkjøpsData
                        ? (innkjøpsData.by_region[reg] ?? 0)
                        : contractedFromContracts;
                    const aggregertHusleie = innkjøpsData?.aggregert ?? contractedFromContracts;

                    const financials = p.external_data?.financials || {};
                    // Bug fix: bruk eksplisitt sum (ikke ||) – OR-operatoren droppet csv+manual når total_maintenance var satt
                    const actualAccountingSpend =
                        (Number(financials.total_maintenance) || 0) +
                        (Number(financials.total_spend_csv) || 0) +
                        (Number(financials.total_manual_expenses) || 0);

                    const budget = budgetByPropertyId.get(p.property_id);
                    const budget2027 = budgetByPropertyId2027.get(p.property_id);
                    const financeBudget2026Val = financeBudget2026ByPropertyId.get(p.property_id);
                    const kontant2026Val = kontant2026ByPropertyId.get(p.property_id);
                    const okoRegn2025Data = okoRegn2025ByPropertyId.get(p.property_id);
                    const okoRegn2025Val = okoRegn2025Data?.total;
                    // BEFS prediksjon 2026: hent fra okonomi_regional_2026 i budget-tabellen
                    // (regionale vekstrater reverse-engineered fra økonomibudsjettet, ikke gammel kategorimodell)
                    const befsPred2026Val = budgetByPropertyId.get(p.property_id);
                    const salaryCost = newSalaryMap.get(p.property_id);

                    return {
                        property: p,
                        contractedRent,
                        aggregertHusleie,
                        glRent: 0,  // Berika fra GL nedenfor
                        actualAccountingSpend,
                        totalPropertyExpense: actualAccountingSpend,
                        budget: Number(budget ?? 0),
                        budget2027: Number(budget2027 ?? 0),
                        financeBudget2026: financeBudget2026Val != null ? Number(financeBudget2026Val) : undefined,
                        kontant2026: kontant2026Val != null ? Number(kontant2026Val) : undefined,
                        okoRegn2025: okoRegn2025Val != null ? Number(okoRegn2025Val) : undefined,
                        okoRegn2025ByCategory: okoRegn2025Data?.by_category,
                        befsPred2026: befsPred2026Val != null ? Number(befsPred2026Val) : undefined,
                        salaryCost,
                        activeContracts,
                        expenses: financials?.manual_expenses || []
                    };
                });

                // Group by Region
                const grouped: Record<string, RegionalData> = {};

                // Initialize from regionalStats to ensure all regions are present
                // Bug fix: backend returnerer planned_rent / other_costs, ikke rent / maintenance
                regionalStats.forEach((stat: any) => {
                    grouped[stat.region] = {
                        region: stat.region,
                        maintenance: stat.other_costs ?? stat.maintenance ?? 0,
                        rent: stat.planned_rent ?? stat.rent ?? 0,
                        glRent: 0,
                        budget: 0,
                        budget2027: 0,
                        financeBudget2026: 0,
                        okoRegn2025: 0,
                        befsPred2026: 0,
                        salaryCost: 0,
                        rows: []
                    };
                });

                allRows.forEach(row => {
                    let reg = normalizeRegion(row.property.region);

                    if (!grouped[reg]) {
                        grouped[reg] = { region: reg, maintenance: 0, rent: 0, glRent: 0, budget: 0, budget2027: 0, financeBudget2026: 0, kontant2026: 0, okoRegn2025: 0, befsPred2026: 0, salaryCost: 0, rows: [] };
                    }

                    // Berik med GL-data for valgt år
                    const glData = glBulk?.by_property?.[row.property.property_id];
                    if (glData) {
                        row.actualAccountingSpend = glData.andre_kostnader;
                        row.glRent = glData.faktisk_husleie || 0;
                        // contractedRent beholdes uendret fra kontrakter
                    } else {
                        // Bug fix: IKKE null-still actualAccountingSpend – behold verdien fra external_data.financials
                        row.glRent = 0;
                    }

                    grouped[reg].rows.push(row);
                    if (row.budget != null) grouped[reg].budget += row.budget;
                    if (row.budget2027 != null) grouped[reg].budget2027 += row.budget2027;
                    if (row.financeBudget2026 != null) grouped[reg].financeBudget2026 += row.financeBudget2026;
                    if (row.kontant2026 != null) grouped[reg].kontant2026 += row.kontant2026;
                    if (row.okoRegn2025 != null) grouped[reg].okoRegn2025 += row.okoRegn2025;
                    if (row.befsPred2026 != null) grouped[reg].befsPred2026 += row.befsPred2026;
                    if (row.salaryCost != null) grouped[reg].salaryCost += row.salaryCost;
                });

                // Legg til direktorat-rader per region (Bufdir er 100% direktorat)
                const addDirektorat = (summary: any, field: 'financeBudget2026' | 'kontant2026' | 'okoRegn2025') => {
                    const byRegion = summary?.direktorat?.by_region ?? {};
                    Object.entries(byRegion).forEach(([reg, data]: [string, any]) => {
                        const normReg = normalizeRegion(reg);
                        if (!grouped[normReg]) {
                            grouped[normReg] = {
                                region: normReg, maintenance: 0, rent: 0, glRent: 0,
                                budget: 0, budget2027: 0, financeBudget2026: 0,
                                okoRegn2025: 0, befsPred2026: 0, salaryCost: 0, rows: []
                            };
                        }
                        grouped[normReg][field] += (data.total ?? 0);
                    });
                };
                addDirektorat(financeBudget2026Summary, 'financeBudget2026');
                addDirektorat(kontant2026Summary, 'kontant2026');
                addDirektorat(okoRegn2025Summary, 'okoRegn2025');

                // Aggreger rent, glRent og vedlikehold fra rader
                // For 2026: kun budsjett – nullstill andre kostnader
                const is2026Only = selectedYear === 2026;
                Object.values(grouped).forEach(g => {
                    if (g.rows.length > 0) {
                        g.rent = is2026Only ? 0 : g.rows.reduce((sum, r) => sum + r.contractedRent, 0);
                        g.glRent = is2026Only ? 0 : g.rows.reduce((sum, r) => sum + r.glRent, 0);
                        g.maintenance = is2026Only ? 0 : g.rows.reduce((sum, r) => sum + r.actualAccountingSpend, 0);
                        g.salaryCost = g.rows.reduce((sum, r) => sum + (r.salaryCost ?? 0), 0);
                    }
                });

                const finalRegionalData = Object.values(grouped).sort((a, b) => a.region.localeCompare(b.region));
                setRegionalRows(finalRegionalData);
                setAllPropertyRows(allRows);
                setOrphanGLRent(glBulk?.orphan_faktisk_husleie ?? 0);
                setOrphanAndreKostnader(glBulk?.orphan_andre_kostnader ?? 0);
                setInnkjøpsanalyseTotal(innkjøpsanalyse?.total > 0 ? innkjøpsanalyse.total : null);
                setGodkjenteList(godkjenteListData);
                setInnkjøpsanalyse2025(innkjøpsanalyse2025Data ?? null);
            } catch (err) {
                console.error("Failed to load financial data", err);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [selectedYear]);

    useEffect(() => {
        setMissingCostsLoaded(false);
        setDiscontinuedPropertiesLoaded(false);
        setCostsWithoutPropertyLoaded(false);
    }, [selectedYear]);

    useEffect(() => {
        if (activeTab === 'missing-costs' && !missingCostsLoaded && !missingCostsLoading) {
            setMissingCostsLoading(true);
            getPropertiesWithoutCosts(selectedYear)
                .then((res) => {
                    if (res) {
                        setMissingCostsData(res.properties);
                        setMissingCostsLoaded(true);
                    }
                })
                .catch(() => {})
                .finally(() => setMissingCostsLoading(false));
        }
    }, [activeTab, selectedYear, missingCostsLoaded, missingCostsLoading]);

    useEffect(() => {
        if (activeTab === 'discontinued-properties' && !discontinuedPropertiesLoaded && !discontinuedPropertiesLoading) {
            setDiscontinuedPropertiesLoading(true);
            getDiscontinuedProperties(2025, selectedYear)
                .then((res) => {
                    if (res) {
                        setDiscontinuedPropertiesData(res.properties);
                        setDiscontinuedBudgetAvailable(res.budget_available);
                        setDiscontinuedPropertiesLoaded(true);
                    }
                })
                .catch(() => {})
                .finally(() => setDiscontinuedPropertiesLoading(false));
        }
    }, [activeTab, selectedYear, discontinuedPropertiesLoaded, discontinuedPropertiesLoading]);

    useEffect(() => {
        if (activeTab === 'costs-without-property' && !costsWithoutPropertyLoaded && !costsWithoutPropertyLoading) {
            setCostsWithoutPropertyLoading(true);
            getCostsWithoutProperty(selectedYear)
                .then((res) => {
                    if (res) {
                        setCostsWithoutPropertyData(res.cost_centers);
                        setCostsWithoutPropertyTotal(res.total_amount);
                        setCostsWithoutPropertyLoaded(true);
                    }
                })
                .catch(() => {})
                .finally(() => setCostsWithoutPropertyLoading(false));
        }
    }, [activeTab, selectedYear, costsWithoutPropertyLoaded, costsWithoutPropertyLoading]);

    useEffect(() => {
        if (activeTab === 'costs-without-property' && costsWithoutPropertyViewMode === 'pivot' && !costsWithoutPropertyPivotLoaded && !costsWithoutPropertyPivotLoading) {
            setCostsWithoutPropertyPivotLoading(true);
            getCostsWithoutPropertyPivot(selectedYear)
                .then((res) => {
                    if (res) {
                        setCostsWithoutPropertyPivotData(res);
                        setCostsWithoutPropertyPivotLoaded(true);
                    }
                })
                .catch(() => {})
                .finally(() => setCostsWithoutPropertyPivotLoading(false));
        }
    }, [activeTab, selectedYear, costsWithoutPropertyViewMode, costsWithoutPropertyPivotLoaded, costsWithoutPropertyPivotLoading]);

    useEffect(() => {
        setCostsWithoutPropertyPivotLoaded(false);
    }, [selectedYear]);

    useEffect(() => {
        if (selectedYear === 2025) {
            getTotalKostPerRegion(2025).then(setTotalKostPerRegion);
        } else {
            setTotalKostPerRegion(null);
        }
    }, [selectedYear]);


    const formatCurrency = (amount: number) => {
        if (amount == null || isNaN(amount)) return "—";
        const abs = Math.abs(amount);
        const sign = amount < 0 ? '-' : '';
        if (abs >= 1000000) return `${sign}${(abs / 1000000).toFixed(1)} MNOK`;
        if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(0)} kNOK`;
        return `${amount.toFixed(0)} NOK`;
    };

    const formatFullCurrency = (amount: number) => {
        if (amount == null || isNaN(amount)) return "—";
        return new Intl.NumberFormat('no-NO', { style: 'currency', currency: 'NOK', maximumFractionDigits: 0 }).format(amount);
    };

    // Total kost: bruk full oversikt fra total_kost_per_region (alle eiendommer/avdelinger) når tilgjengelig
    // Fallback: ERP-total 504,079,834 bekreftet fra Agresso (alle lokalkostnadskategorier 2025)
    const ERP_REAL_TOTAL_2025 = 504_079_834;
    const totalKostFull = totalKostPerRegion && Object.keys(totalKostPerRegion.by_category).length > 0
        ? Object.values(totalKostPerRegion.by_category).reduce((sum, cat) => {
            const totals = cat.by_region_totals || {};
            return sum + Object.values(totals).reduce((a, b) => a + b, 0);
          }, 0)
        : null;
    // For 2025: foretrekk API-total → fallback til ERP-konstant → fallback til innkjøpsanalyse/kontrakter
    const totalPortfolioGLRent = regionalRows.reduce((sum, r) => sum + r.glRent, 0) + orphanGLRent;    // Fra GL inkl. kostnader uten eiendom
    const totalPortfolioMaint = regionalRows.reduce((sum, r) => sum + r.maintenance, 0) + orphanAndreKostnader;
    const glTotalFallback = totalPortfolioGLRent + totalPortfolioMaint; // Brukes som fallback når Innkjøpsanalyse mangler
    const totalPortfolioRent = selectedYear === 2025
        ? (totalKostFull ?? innkjøpsanalyseTotal ?? ERP_REAL_TOTAL_2025)
        : ((innkjøpsanalyseTotal ?? glTotalFallback) || regionalRows.reduce((sum, r) => sum + r.rent, 0));
    const totalPortfolioBudget = regionalRows.reduce((sum, r) => sum + r.budget, 0);
    const totalPortfolioBudget2027 = regionalRows.reduce((sum, r) => sum + r.budget2027, 0);
    const totalPortfolioFinanceBudget2026 = financeBudget2026?.total_nok ?? 0;
    const financeBudget2026HasData = totalPortfolioFinanceBudget2026 > 0;
    const totalKontant2026 = kontant2026?.total_nok ?? 0;
    const kontant2026HasData = totalKontant2026 > 0;
    const totalPortfolioSalary = salaryCosts?.total ?? regionalRows.reduce((sum, r) => sum + r.salaryCost, 0);
    const totalOkoRegn2025 = okoRegn2025?.total_nok ?? 0;
    const okoRegn2025HasData = totalOkoRegn2025 > 0;
    // BEFS prediksjon 2026: sum fra per-property beregning (okoRegn2025 × vekstfaktorer)
    const totalBefsPred2026 = regionalRows.reduce((sum, r) => sum + r.befsPred2026, 0);
    const befsPred2026HasData = totalBefsPred2026 > 0;
    const budgetOnlyView = selectedYear === 2026;  // For 2026: kun budsjett per eiendom og total
    const portfolioLast3Years = (() => {
        const byYear: Record<number, number> = {};
        regionalRows.forEach((reg) => {
            getRegionalLast3YearsForbruk(reg.rows).forEach(({ year, total_costs }) => {
                byYear[year] = (byYear[year] ?? 0) + total_costs;
            });
        });
        return Object.entries(byYear)
            .map(([y, t]) => ({ year: parseInt(y, 10), total_costs: t }))
            .sort((a, b) => b.year - a.year)
            .slice(0, 3);
    })();

    return (
        <div className="min-h-screen font-sans text-foreground pb-20">
            <Header />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24 text-foreground">

                {/* Dashboard header */}
                <div className="flex items-center gap-4 mb-3">
                    <h1 className="text-2xl font-bold tracking-tight">
                        Økonomi & Finansielle Analyser
                    </h1>
                    <div className="flex gap-1">
                        {[2025, 2026].map(y => (
                            <button
                                key={y}
                                onClick={() => setSelectedYear(y)}
                                className={`text-sm px-3 py-1 rounded border font-medium transition-colors ${
                                    selectedYear === y
                                        ? 'bg-primary text-primary-foreground border-primary'
                                        : 'border-border text-muted hover:text-foreground'
                                }`}
                            >
                                {y}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Dashboard Stats — alle kort på én rad */}
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 mb-8">
                    {/* Regnskap 2025 */}
                    <div className="glass-card p-3 border-l-4 border-primary shadow-sm">
                        <div className="text-[9px] font-bold text-primary uppercase tracking-widest mb-1">Regnskap 2025 (Øk.)</div>
                        <div className="text-base font-bold leading-tight">{okoRegn2025HasData ? formatCurrency(totalOkoRegn2025) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">Kontant 2025</div>
                    </div>
                    {/* BEFS Prediksjon 2026 */}
                    <div className="glass-card p-3 border-l-4 border-emerald-500/50">
                        <div className="text-[9px] font-bold text-emerald-600 dark:text-emerald-500 uppercase tracking-widest mb-1">BEFS Pred. 2026</div>
                        <div className="text-base font-bold leading-tight">{befsPred2026HasData ? formatCurrency(totalBefsPred2026) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">Regionale vekstrater</div>
                    </div>
                    {/* Budsjett 2026 (Økonomi) */}
                    <div className="glass-card p-3 border-l-4 border-teal-500/70">
                        <div className="text-[9px] font-bold text-teal-600 dark:text-teal-400 uppercase tracking-widest mb-1">Budsjett 2026 (Øk.)</div>
                        <div className="text-base font-bold leading-tight">{financeBudget2026HasData ? formatCurrency(totalPortfolioFinanceBudget2026) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">Vedtatt (Beløp DA)</div>
                    </div>
                    {/* Faktisk brukt 2026 YTD */}
                    <div className="glass-card p-3 border-l-4 border-cyan-500/70">
                        <div className="text-[9px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-widest mb-1">Faktisk 2026 YTD</div>
                        <div className="text-base font-bold leading-tight">{kontant2026HasData ? formatCurrency(totalKontant2026) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">Kontant per apr. 2026</div>
                    </div>
                    {/* Avvik: BEFS vs Økonomi */}
                    <div className="glass-card p-3 border-l-4 border-amber-500/50">
                        <div className="text-[9px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-widest mb-1">Avvik 2026</div>
                        {financeBudget2026HasData && befsPred2026HasData ? (() => {
                            const diff = totalBefsPred2026 - totalPortfolioFinanceBudget2026;
                            const pct = totalPortfolioFinanceBudget2026 > 0 ? (diff / totalPortfolioFinanceBudget2026) * 100 : 0;
                            return (
                                <>
                                    <div className={`text-base font-bold leading-tight ${diff > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}`}>
                                        {diff > 0 ? "+" : ""}{formatCurrency(diff)}
                                    </div>
                                    <div className="text-[9px] text-muted mt-1">{pct.toFixed(1)}% vs økonomi</div>
                                </>
                            );
                        })() : <div className="text-base font-bold leading-tight">—</div>}
                    </div>
                    {/* Prediksjon 2027 */}
                    <div className="glass-card p-3 border-l-4 border-violet-500/50">
                        <div className="text-[9px] font-bold text-violet-600 dark:text-violet-400 uppercase tracking-widest mb-1">Prediksjon 2027</div>
                        <div className="text-base font-bold leading-tight">{totalPortfolioBudget2027 > 0 ? formatCurrency(totalPortfolioBudget2027) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">BEFS prediksjon</div>
                    </div>
                    {/* Lønnskostnad */}
                    <div className="glass-card p-3 border-l-4 border-rose-500/50">
                        <div className="text-[9px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-widest mb-1">Lønnskostnad</div>
                        <div className="text-base font-bold leading-tight text-rose-700 dark:text-rose-300">{totalPortfolioSalary > 0 ? formatCurrency(totalPortfolioSalary) : "—"}</div>
                        <div className="text-[9px] text-muted mt-1">Alle eiendommer {selectedYear}</div>
                    </div>
                </div>

                {/* Kostnadskilde-analyse: 504M vs 805M */}
                {selectedYear === 2025 && supplierStats && (() => {
                    // Statisk fallback: ERP-total fra Agresso (alle lokalkostnadskategorier, bekreftet 2025)
                    // Brukes når total_kost_per_region-API ikke returnerer data (f.eks. manglende JSON-fil på Railway)
                    const ERP_REAL_TOTAL = 504_079_834;
                    // Bruk API-beregnet total om tilgjengelig, ellers fallback til bekreftet ERP-total
                    const innkjøpsTotal = totalKostFull ?? ERP_REAL_TOTAL;
                    const usingFallback = totalKostFull == null;

                    // Build GL category map from supplierStats
                    const glCatMap: Record<string, number> = {};
                    supplierStats.suppliers.forEach(s => {
                        // Sum all detail lines by their category
                        (s.details || []).forEach((d: { category: string; amount: number }) => {
                            glCatMap[d.category] = (glCatMap[d.category] ?? 0) + d.amount;
                        });
                    });
                    const glTotal = supplierStats.total_portfolio_cost;

                    // Innkjøpsanalyse categories (from totalKostPerRegion, if available)
                    const csvCats = Object.entries(totalKostPerRegion?.by_category ?? {})
                        .map(([name, data]) => ({
                            name,
                            total: Object.values((data as { by_region_totals?: Record<string, number> }).by_region_totals ?? {}).reduce((a, b) => a + b, 0)
                        }))
                        .filter(c => c.total > 0)
                        .sort((a, b) => b.total - a.total);

                    // GL categories sorted by amount, top 12
                    const glCatsSorted = Object.entries(glCatMap)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 12);

                    // Determine if a GL cat is covered by CSV / ERP (fuzzy match on known lokalkostnad-terms)
                    const knownLokalkostnad = ["leie", "husleie", "strøm", "oppvarming", "fellesutgift", "vedlikehold", "renhold", "parkering", "vakthold"];
                    const csvNames = csvCats.length > 0
                        ? csvCats.map(c => c.name.toLowerCase())
                        : knownLokalkostnad;
                    const isCsvCovered = (cat: string) => {
                        const c = cat.toLowerCase();
                        return csvNames.some(n => n.includes(c.split(' ')[0]) || c.includes(n.split(' ')[0]));
                    };

                    const gap = glTotal > innkjøpsTotal ? glTotal - innkjøpsTotal : 0;
                    const maxBar = glTotal;

                    return (
                        <div className="glass-card p-6 mb-6">
                            <div className="flex items-center gap-3 mb-5">
                                <div className="p-2 bg-amber-500/10 rounded-lg"><TrendingUp size={18} className="text-amber-600 dark:text-amber-400" /></div>
                                <div>
                                    <h3 className="font-bold text-foreground text-base">Kostnadskilde-analyse — kva er med i kva total?</h3>
                                    <p className="text-xs text-muted mt-0.5">Innkjøpsanalyse (ERP-eksport) dekker kun <em>lokalkostnader</em>. GL-databasen har alle kontoer.</p>
                                </div>
                            </div>

                            {/* Side by side totals */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6">
                                <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 text-center">
                                    <div className="text-xs text-muted uppercase tracking-widest mb-1">Innkjøpsanalyse (ERP)</div>
                                    <div className="text-xl font-bold text-primary">{formatCurrency(innkjøpsTotal)}</div>
                                    <div className="text-[10px] text-muted mt-1">{usingFallback ? "Alle lokalkategorier (Agresso 2025)" : "Leie + strøm + annen kostnad"}</div>
                                </div>
                                <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20 text-center flex flex-col justify-center">
                                    <div className="text-xs text-muted uppercase tracking-widest mb-1">Mangler i Innkjøpsanalyse</div>
                                    <div className="text-xl font-bold text-rose-600 dark:text-rose-400">{gap > 0 ? `+ ${formatCurrency(gap)}` : "—"}</div>
                                    <div className="text-[10px] text-muted mt-1">Lønn, renhold, reparasjon, parkering m.m.</div>
                                </div>
                                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-center">
                                    <div className="text-xs text-muted uppercase tracking-widest mb-1">GL totalt (alle kontoer)</div>
                                    <div className="text-xl font-bold text-amber-600 dark:text-amber-400">{formatCurrency(glTotal)}</div>
                                    <div className="text-[10px] text-muted mt-1">Fullstendig bilde av eiendomskostnader</div>
                                </div>
                            </div>

                            {/* GL category bars */}
                            <div className="space-y-2">
                                <div className="text-xs font-bold text-muted uppercase tracking-widest mb-3">GL-kategorier (top 12 av totalt {formatCurrency(glTotal)})</div>
                                {glCatsSorted.map(([cat, amt]) => {
                                    const pct = (amt / maxBar) * 100;
                                    const inCsv = isCsvCovered(cat);
                                    return (
                                        <div key={cat} className="flex items-center gap-3 text-xs group">
                                            <div className="w-5 shrink-0 text-center">
                                                {inCsv
                                                    ? <span title="Dekket av CSV" className="text-emerald-500">✓</span>
                                                    : <span title="MANGLER i CSV" className="text-rose-500">✗</span>
                                                }
                                            </div>
                                            <div className="w-56 shrink-0 text-muted truncate" title={cat}>{cat}</div>
                                            <div className="flex-1 bg-muted/20 rounded-full h-2 relative">
                                                <div
                                                    className={`h-2 rounded-full transition-all ${inCsv ? 'bg-primary/60' : 'bg-rose-500/60'}`}
                                                    style={{ width: `${pct}%` }}
                                                />
                                            </div>
                                            <div className={`w-24 text-right font-mono font-bold shrink-0 ${inCsv ? 'text-foreground' : 'text-rose-600 dark:text-rose-400'}`}>
                                                {formatCurrency(amt)}
                                            </div>
                                        </div>
                                    );
                                })}
                                <div className="flex items-center gap-3 text-xs pt-2 border-t border-border mt-2">
                                    <div className="w-5 shrink-0" />
                                    <div className="w-56 shrink-0 font-bold text-muted">Øvrige kategorier</div>
                                    <div className="flex-1" />
                                    <div className="w-24 text-right font-mono text-muted">
                                        {formatCurrency(glTotal - glCatsSorted.reduce((s, [, a]) => s + a, 0))}
                                    </div>
                                </div>
                            </div>

                            {/* CSV breakdown */}
                            {csvCats.length > 0 && (
                                <div className="mt-5 pt-4 border-t border-border">
                                    <div className="text-xs font-bold text-muted uppercase tracking-widest mb-3">Innkjøpsanalyse CSV — kategorier inkludert</div>
                                    <div className="flex flex-wrap gap-2">
                                        {csvCats.map(c => (
                                            <span key={c.name} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary font-medium">
                                                <span className="text-emerald-500">✓</span>
                                                {c.name}: {formatCurrency(c.total)}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })()}

                {/* Total kost per region (kun 2025) */}
                {selectedYear === 2025 && totalKostPerRegion && Object.keys(totalKostPerRegion.by_category).length > 0 && (
                    <Accordion title="Total kost per region – Leie av lokaler og tilknyttede utgifter" icon={<Layers size={22} className="text-primary" />} defaultOpen={false}>
                        <div className="space-y-6">
                            <p className="text-sm text-muted">Region-totalsum per kategori. Kilde: Innkjøpsanalyse-import.</p>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm border-collapse">
                                    <thead>
                                        <tr className="border-b border-border">
                                            <th className="text-left py-2 px-2 font-semibold">Kategori</th>
                                            <th className="text-right py-2 px-2 font-semibold">Midt-Norge</th>
                                            <th className="text-right py-2 px-2 font-semibold">Nord</th>
                                            <th className="text-right py-2 px-2 font-semibold">Sør</th>
                                            <th className="text-right py-2 px-2 font-semibold">Vest</th>
                                            <th className="text-right py-2 px-2 font-semibold">Øst</th>
                                            <th className="text-right py-2 px-2 font-semibold">Bufdir</th>
                                            <th className="text-right py-2 px-2 font-semibold">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {Object.entries(totalKostPerRegion.by_category).map(([category, data]) => {
                                            const totals = data.by_region_totals || {};
                                            const rowTotal = Object.values(totals).reduce((a, b) => a + b, 0);
                                            return (
                                                <tr key={category} className="border-b border-border/50 hover:bg-muted/20">
                                                    <td className="py-2 px-2">{category}</td>
                                                    {["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"].map(reg => (
                                                        <td key={reg} className="text-right py-2 px-2 tabular-nums">
                                                            {(totals[reg] ?? 0) > 0 ? formatFullCurrency(totals[reg]) : "—"}
                                                        </td>
                                                    ))}
                                                    <td className="text-right py-2 px-2 font-medium tabular-nums">{formatFullCurrency(rowTotal)}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            <details className="group">
                                <summary className="cursor-pointer text-sm font-medium text-muted hover:text-foreground">Enhetsfordeling per kategori</summary>
                                <div className="mt-3 space-y-4 pl-2 border-l-2 border-border">
                                    {Object.entries(totalKostPerRegion.by_category).map(([category, data]) => {
                                        const radetikett = data.by_region_radetikett || {};
                                        const hasData = Object.values(radetikett).some(arr => arr?.length > 0);
                                        if (!hasData) return null;
                                        return (
                                            <div key={category} className="space-y-2">
                                                <div className="font-medium text-sm">{category}</div>
                                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                                    {Object.entries(radetikett).map(([region, items]) => {
                                                        if (!items?.length) return null;
                                                        return (
                                                            <div key={region} className="bg-muted/20 rounded p-2 text-xs">
                                                                <div className="font-semibold mb-1">{region}</div>
                                                                <div className="space-y-0.5 max-h-32 overflow-y-auto">
                                                                    {items.slice(0, 10).map((item, i) => (
                                                                        <div key={i} className="flex justify-between">
                                                                            <span className="truncate max-w-[120px]" title={item.radetikett}>{item.radetikett}</span>
                                                                            <span className="tabular-nums shrink-0">{formatFullCurrency(item.amount)}</span>
                                                                        </div>
                                                                    ))}
                                                                    {items.length > 10 && <div className="text-muted">+ {items.length - 10} flere</div>}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </details>
                        </div>
                    </Accordion>
                )}

                {/* Husleie 2026 – KPI-justert */}
                {(() => {
                    const h2026Props = (allPropertyRows || [])
                        .filter(r => r.property && (r.property as any).husleie_2026 > 0)
                        .sort((a, b) => ((b.property as any).husleie_2026 || 0) - ((a.property as any).husleie_2026 || 0));
                    if (h2026Props.length === 0) return null;
                    const totalH2026 = h2026Props.reduce((s, r) => s + ((r.property as any).husleie_2026 || 0), 0);
                    const totalStartpris = h2026Props.reduce((s, r) => s + ((r.property as any).contract_rent_nok || 0), 0);
                    return (
                        <Accordion title={`Husleie 2026 – KPI-justert (${h2026Props.length} eiendommer)`} icon={<TrendingUp size={22} className="text-emerald-500" />} defaultOpen={false}>
                            <div className="space-y-4">
                                {/* KPI-kort */}
                                <div className="grid grid-cols-3 gap-4">
                                    <div className="bg-emerald-500/10 p-4 rounded-lg border border-emerald-500/30 text-center">
                                        <div className="text-xs text-muted font-bold uppercase mb-1">KPI-justert husleie 2026</div>
                                        <div className="text-xl font-bold text-emerald-600">{formatCurrency(totalH2026)}</div>
                                        <div className="text-[11px] text-muted mt-1">Beregnet fra SSB KPI okt. 2025</div>
                                    </div>
                                    <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 text-center">
                                        <div className="text-xs text-muted font-bold uppercase mb-1">Startpris (kontrakt)</div>
                                        <div className="text-xl font-bold text-primary">{totalStartpris > 0 ? formatCurrency(totalStartpris) : "—"}</div>
                                        <div className="text-[11px] text-muted mt-1">Avtalefestet startleie</div>
                                    </div>
                                    <div className="bg-amber-500/10 p-4 rounded-lg border border-amber-500/30 text-center">
                                        <div className="text-xs text-muted font-bold uppercase mb-1">KPI-økning totalt</div>
                                        <div className="text-xl font-bold text-amber-600">
                                            {totalStartpris > 0 ? `+${(((totalH2026 / totalStartpris) - 1) * 100).toFixed(1)} %` : "—"}
                                        </div>
                                        <div className="text-[11px] text-muted mt-1">Gjennomsnittlig prisvekst</div>
                                    </div>
                                </div>

                                {/* Tabell */}
                                <div className="overflow-hidden rounded-xl border border-border bg-background">
                                    <table className="w-full text-left text-sm">
                                        <thead>
                                            <tr className="border-b border-border bg-muted/30">
                                                <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Eiendom</th>
                                                <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Region</th>
                                                <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Startpris (kr)</th>
                                                <th className="px-4 py-3 text-right font-bold text-emerald-600 uppercase text-xs">Husleie 2026 (KPI)</th>
                                                <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">KPI-økning</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border">
                                            {h2026Props.slice(0, 50).map((r, i) => {
                                                const h2026 = (r.property as any).husleie_2026 || 0;
                                                const start = (r.property as any).contract_rent_nok || 0;
                                                const note = (r.property as any).husleie_2026_kpi_note || "";
                                                return (
                                                    <tr key={r.property.property_id} className="hover:bg-muted/5 transition-colors">
                                                        <td className="px-4 py-3 font-medium text-foreground truncate max-w-48">{r.property.name || r.property.address}</td>
                                                        <td className="px-4 py-3 text-muted text-xs">{r.property.region || "—"}</td>
                                                        <td className="px-4 py-3 text-right font-mono text-xs">{start > 0 ? formatFullCurrency(start) : "—"}</td>
                                                        <td className="px-4 py-3 text-right font-mono text-emerald-700 dark:text-emerald-400 font-semibold">{formatFullCurrency(h2026)}</td>
                                                        <td className="px-4 py-3 text-right text-xs text-muted">{note}</td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                        <tfoot>
                                            <tr className="border-t-2 border-border bg-muted/20">
                                                <td colSpan={2} className="px-4 py-3 font-bold">Totalt ({h2026Props.length} eiendommer)</td>
                                                <td className="px-4 py-3 text-right font-bold font-mono">{totalStartpris > 0 ? formatFullCurrency(totalStartpris) : "—"}</td>
                                                <td className="px-4 py-3 text-right font-bold font-mono text-emerald-700 dark:text-emerald-400">{formatFullCurrency(totalH2026)}</td>
                                                <td className="px-4 py-3 text-right text-xs text-muted">
                                                    {totalStartpris > 0 ? `+${(((totalH2026 / totalStartpris) - 1) * 100).toFixed(1)} %` : ""}
                                                </td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                                <p className="text-xs text-muted">
                                    Beregnet via SSB KPI-indeks (tabell 03013, Konsumgrp=TOTAL) med oktober 2025 som referansemåned.
                                    Formel: ny leie = startleie × (reg% × KPI_okt2025 / KPI_start + (1 − reg%)).
                                    628 eiendommer mangler kontrakt/startpris og er ikke inkludert.
                                </p>
                            </div>
                        </Accordion>
                    );
                })()}

                {/* Tab Navigation */}
                <div className="mb-6">
                    <div className="flex gap-4 border-b border-border overflow-x-auto pb-1 -mx-1">
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('overview'))}
                            className={`px-4 py-2 font-semibold transition-colors border-b-2 shrink-0 ${activeTab === 'overview'
                                ? 'text-primary border-primary'
                                : 'text-muted border-transparent hover:text-foreground'
                                }`}
                        >
                            Regional Oversikt
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('suppliers'))}
                            className={`px-4 py-2 font-semibold transition-colors border-b-2 shrink-0 ${activeTab === 'suppliers'
                                ? 'text-primary border-primary'
                                : 'text-muted border-transparent hover:text-foreground'
                                }`}
                        >
                            Leverandørstatistikk
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('catalog'))}
                            className={`px-4 py-2 font-semibold transition-colors border-b-2 shrink-0 ${activeTab === 'catalog'
                                ? 'text-primary border-primary'
                                : 'text-muted border-transparent hover:text-foreground'
                                }`}
                        >
                            Leverandørregister
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('invoices'))}
                            className={`px-4 py-2 font-semibold transition-colors border-b-2 shrink-0 ${activeTab === 'invoices'
                                ? 'text-primary border-primary'
                                : 'text-muted border-transparent hover:text-foreground'
                                }`}
                        >
                            Fakturadetaljer
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('patterns'))}
                            className={`px-4 py-2 font-semibold transition-colors border-b-2 shrink-0 ${activeTab === 'patterns'
                                ? 'text-primary border-primary'
                                : 'text-muted border-transparent hover:text-foreground'
                                }`}
                        >
                            Kostnadsmønstre
                        </button>
                    </div>
                    <div className="flex gap-3 mt-2 text-sm">
                        <span className="text-muted py-1">Datakvalitet:</span>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('missing-costs'))}
                            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${activeTab === 'missing-costs'
                                ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40'
                                : 'text-muted hover:text-foreground hover:bg-muted/50'
                                }`}
                        >
                            Manglende kostnader
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('costs-without-property'))}
                            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${activeTab === 'costs-without-property'
                                ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40'
                                : 'text-muted hover:text-foreground hover:bg-muted/50'
                                }`}
                        >
                            Kostnader uten eiendom
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('discontinued-properties'))}
                            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${activeTab === 'discontinued-properties'
                                ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40'
                                : 'text-muted hover:text-foreground hover:bg-muted/50'
                                }`}
                        >
                            Avviklet eiendom
                        </button>
                        <button
                            onClick={() => startTabTransition(() => setActiveTab('contracts-pivot'))}
                            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${activeTab === 'contracts-pivot'
                                ? 'bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40'
                                : 'text-muted hover:text-foreground hover:bg-muted/50'
                                }`}
                        >
                            Kontrakter (pivot)
                        </button>
                        {financeBudget2026HasData && (
                            <button
                                onClick={() => startTabTransition(() => setActiveTab('sammenligning-2026'))}
                                className={`px-3 py-1.5 rounded-md font-medium transition-colors shrink-0 ${activeTab === 'sammenligning-2026'
                                    ? 'bg-teal-500/20 text-teal-700 dark:text-teal-400 border border-teal-500/40'
                                    : 'text-muted hover:text-foreground hover:bg-muted/50'
                                    }`}
                            >
                                Sammenligning 2026
                            </button>
                        )}
                    </div>
                </div>

                {loading ? (
                    <div className="flex flex-col items-center justify-center p-20 gap-4">
                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-muted font-medium">Aggregerer regnskapsdata...</p>
                    </div>
                ) : (
                    <>
                        {/* Overview Tab */}
                        {activeTab === 'overview' && (
                            <div className="space-y-6">
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setOverviewViewMode('accordion')}
                                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${overviewViewMode === 'accordion' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'}`}
                                    >
                                        Regioner (accordion)
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setOverviewViewMode('pivot')}
                                        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${overviewViewMode === 'pivot' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'}`}
                                    >
                                        Pivot (region × kategori)
                                    </button>
                                </div>
                                {overviewViewMode === 'pivot' ? (
                                    <div className="overflow-x-auto rounded-xl border border-border bg-background">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-border bg-muted/30">
                                                    <th className="px-4 py-3 text-left font-bold text-muted-foreground">Region</th>
                                                    {okoRegn2025HasData && (
                                                        <th className="px-4 py-3 text-right font-bold text-primary">Regn. 2025 (Øk.)</th>
                                                    )}
                                                    {befsPred2026HasData && (
                                                        <th className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400">BEFS Pred. 2026</th>
                                                    )}
                                                    {financeBudget2026HasData && (
                                                        <th className="px-4 py-3 text-right font-bold text-teal-600 dark:text-teal-400">Budsj. 2026 (Øk.)</th>
                                                    )}
                                                    {kontant2026HasData && (
                                                        <th className="px-4 py-3 text-right font-bold text-cyan-600 dark:text-cyan-400">Faktisk 2026 YTD</th>
                                                    )}
                                                    {befsPred2026HasData && financeBudget2026HasData && (
                                                        <th className="px-4 py-3 text-right font-bold text-amber-600 dark:text-amber-400">Avvik</th>
                                                    )}
                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground">Eiendommer</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {regionalRows.map((reg) => {
                                                    const avvik26 = reg.befsPred2026 - reg.financeBudget2026;
                                                    const avvikPct26 = reg.financeBudget2026 > 0 ? (avvik26 / reg.financeBudget2026) * 100 : null;
                                                    const isNasjonal = reg.region === "Nasjonal";
                                                    return (
                                                    <tr key={reg.region} className={`border-b border-border/50 hover:bg-muted/20 ${isNasjonal ? "opacity-60 italic" : ""}`}>
                                                        <td className="px-4 py-3 font-medium">{reg.region}{isNasjonal && <span className="ml-1 text-xs font-normal not-italic text-muted-foreground">(sekkepost)</span>}{reg.region === "Bufdir" && <span className="ml-1 text-xs font-normal text-muted-foreground">(direktorat)</span>}</td>
                                                        {okoRegn2025HasData && (
                                                            <td className="px-4 py-3 text-right font-mono text-foreground">{reg.okoRegn2025 > 0 ? formatCurrency(reg.okoRegn2025) : '—'}</td>
                                                        )}
                                                        {befsPred2026HasData && (
                                                            <td className="px-4 py-3 text-right font-mono text-emerald-700 dark:text-emerald-300">{reg.befsPred2026 > 0 ? formatCurrency(reg.befsPred2026) : '—'}</td>
                                                        )}
                                                        {financeBudget2026HasData && (
                                                            <td className="px-4 py-3 text-right font-mono text-teal-700 dark:text-teal-300">{reg.financeBudget2026 > 0 ? formatCurrency(reg.financeBudget2026) : '—'}</td>
                                                        )}
                                                        {kontant2026HasData && (
                                                            <td className="px-4 py-3 text-right font-mono text-cyan-700 dark:text-cyan-300">{reg.kontant2026 > 0 ? formatCurrency(reg.kontant2026) : '—'}</td>
                                                        )}
                                                        {befsPred2026HasData && financeBudget2026HasData && (
                                                            <td className="px-4 py-3 text-right font-mono">
                                                                {reg.befsPred2026 > 0 && reg.financeBudget2026 > 0 ? (
                                                                    <span className={avvik26 > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}>
                                                                        {avvik26 > 0 ? "+" : ""}{formatCurrency(avvik26)}
                                                                        {avvikPct26 != null && <span className="text-[10px] ml-1">({avvikPct26 > 0 ? "+" : ""}{avvikPct26.toFixed(0)}%)</span>}
                                                                    </span>
                                                                ) : '—'}
                                                            </td>
                                                        )}
                                                        <td className="px-4 py-3 text-right">{reg.rows.length}</td>
                                                    </tr>
                                                    );
                                                })}
                                                <tr className="border-t-2 border-border bg-muted/40 font-semibold">
                                                    <td className="px-4 py-3">Totalt</td>
                                                    {okoRegn2025HasData && (
                                                        <td className="px-4 py-3 text-right font-mono">{formatCurrency(totalOkoRegn2025)}</td>
                                                    )}
                                                    {befsPred2026HasData && (
                                                        <td className="px-4 py-3 text-right font-mono text-emerald-700 dark:text-emerald-300">{formatCurrency(totalBefsPred2026)}</td>
                                                    )}
                                                    {financeBudget2026HasData && (
                                                        <td className="px-4 py-3 text-right font-mono text-teal-700 dark:text-teal-300">{formatCurrency(totalPortfolioFinanceBudget2026)}</td>
                                                    )}
                                                    {kontant2026HasData && (
                                                        <td className="px-4 py-3 text-right font-mono text-cyan-700 dark:text-cyan-300">{formatCurrency(totalKontant2026)}</td>
                                                    )}
                                                    {befsPred2026HasData && financeBudget2026HasData && (
                                                        <td className="px-4 py-3 text-right font-mono">
                                                            <span className={(totalBefsPred2026 - totalPortfolioFinanceBudget2026) > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}>
                                                                {(totalBefsPred2026 - totalPortfolioFinanceBudget2026) > 0 ? "+" : ""}{formatCurrency(totalBefsPred2026 - totalPortfolioFinanceBudget2026)}
                                                            </span>
                                                        </td>
                                                    )}
                                                    <td className="px-4 py-3 text-right">{regionalRows.reduce((s, r) => s + r.rows.length, 0)}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                            <div className="grid grid-cols-1 gap-8">
                                {regionalRows.map((regData) => (
                                    <div key={regData.region} className="bg-surface p-1 rounded-2xl border border-border shadow-sm">
                                        <Accordion
                                            title={`${regData.region}`}
                                            icon={<MapPin size={22} className="text-primary" />}
                                            defaultOpen={regData.rows.length > 0}
                                        >
                                            <div className="flex flex-wrap gap-6 mb-8 mt-2">
                                                {!budgetOnlyView && (
                                                    <>
                                                        <div className="flex items-center gap-3 bg-muted/10 p-4 rounded-xl border border-border">
                                                            <Wallet className="text-primary" size={24} />
                                                            <div>
                                                                <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Årlig Leie ({regData.region})</div>
                                                                <div className="text-xl font-bold text-foreground">{formatCurrency(regData.rent)}</div>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-3 bg-muted/10 p-4 rounded-xl border border-border">
                                                            <HardHat className="text-amber-500" size={24} />
                                                            <div>
                                                                <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Vedlikehold ({regData.region})</div>
                                                                <div className="text-xl font-bold text-foreground">{formatCurrency(regData.maintenance)}</div>
                                                            </div>
                                                        </div>
                                                    </>
                                                )}
                                                <div className="flex items-center gap-3 bg-muted/10 p-4 rounded-xl border border-border">
                                                    <BarChart3 className="text-emerald-500" size={24} />
                                                    <div>
                                                        <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Budsjett 2026 ({regData.region})</div>
                                                        <div className="text-xl font-bold text-foreground">{regData.budget > 0 ? formatCurrency(regData.budget) : "—"}</div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3 bg-muted/10 p-4 rounded-xl border border-border">
                                                    <Building2 className="text-blue-500" size={24} />
                                                    <div>
                                                        <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Antall Eiendommer</div>
                                                        <div className="text-xl font-bold text-foreground">{regData.rows.length}</div>
                                                    </div>
                                                </div>
                                                {!budgetOnlyView && (() => {
                                                    const last3 = getRegionalLast3YearsForbruk(regData.rows);
                                                    if (last3.length === 0) return null;
                                                    return (
                                                        <div key="forbruk" className="flex items-center gap-3 bg-muted/10 p-4 rounded-xl border border-border">
                                                            <History className="text-emerald-500" size={24} />
                                                            <div>
                                                                <DataTooltip content={FORBRUK_TOOLTIP}>
                                                                    <div className="text-[10px] text-muted font-bold uppercase tracking-wider">Forbruk siste 3 år</div>
                                                                </DataTooltip>
                                                                <div className="flex flex-wrap gap-3 mt-1">
                                                                    {last3.map(({ year, total_costs }) => (
                                                                        <span key={year} className="text-sm font-bold text-foreground">
                                                                            {year}: {formatCurrency(total_costs)}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })()}
                                            </div>

                                            {/* Property Breakdown Table */}
                                            <div className="overflow-hidden rounded-xl border border-border bg-background shadow-sm">
                                                <table className="w-full text-left text-sm">
                                                    <thead>
                                                        <tr className="border-b border-border bg-muted/30">
                                                            <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Eiendom</th>
                                                            {okoRegn2025HasData && (
                                                                <th className="px-6 py-4 text-right font-bold text-primary uppercase text-xs tracking-wider">Regn. 2025</th>
                                                            )}
                                                            {befsPred2026HasData && (
                                                                <th className="px-6 py-4 text-right font-bold text-emerald-600 dark:text-emerald-500 uppercase text-xs tracking-wider">BEFS Pred. 2026</th>
                                                            )}
                                                            <th className="px-6 py-4 text-right font-bold text-teal-600 dark:text-teal-400 uppercase text-xs tracking-wider">Budsj. 2026 Øk.</th>
                                                            {befsPred2026HasData && financeBudget2026HasData && (
                                                                <th className="px-6 py-4 text-right font-bold text-amber-600 dark:text-amber-400 uppercase text-xs tracking-wider">Avvik</th>
                                                            )}
                                                            <th className="px-6 py-4 w-10"></th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-border">
                                                        {regData.rows
                                                            .sort((a, b) => (b.financeBudget2026 ?? 0) - (a.financeBudget2026 ?? 0))
                                                            .map(row => {
                                                            const befs = row.befsPred2026 ?? 0;
                                                            const oko26 = row.financeBudget2026 ?? 0;
                                                            const avvik26 = befs - oko26;
                                                            const avvikPct = oko26 > 0 ? (avvik26 / oko26) * 100 : null;
                                                            const harBegge26 = befs > 0 && oko26 > 0;
                                                            return (
                                                                <tr key={row.property.property_id} className="hover:bg-muted/5 transition-colors group">
                                                                    <td className="px-6 py-4">
                                                                        <div className="flex items-center gap-2">
                                                                            <span className="font-bold text-foreground group-hover:text-primary transition-colors">{row.property.name}</span>
                                                                        </div>
                                                                        <div className="text-[11px] text-muted">{row.property.address}</div>
                                                                    </td>
                                                                    {okoRegn2025HasData && (
                                                                        <td className="px-6 py-4 text-right font-mono text-foreground">
                                                                            {row.okoRegn2025 != null && row.okoRegn2025 > 0 ? formatFullCurrency(row.okoRegn2025) : "—"}
                                                                        </td>
                                                                    )}
                                                                    {befsPred2026HasData && (
                                                                        <td className="px-6 py-4 text-right font-mono text-emerald-700 dark:text-emerald-400">
                                                                            {befs > 0 ? formatFullCurrency(befs) : "—"}
                                                                        </td>
                                                                    )}
                                                                    <td className="px-6 py-4 text-right font-mono text-teal-700 dark:text-teal-400">
                                                                        {oko26 > 0 ? formatFullCurrency(oko26) : "—"}
                                                                    </td>
                                                                    {befsPred2026HasData && financeBudget2026HasData && (
                                                                        <td className="px-6 py-4 text-right font-mono">
                                                                            {harBegge26 ? (
                                                                                <span className={avvik26 > 0 ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"}>
                                                                                    {avvik26 > 0 ? "+" : ""}{formatCurrency(avvik26)}
                                                                                    {avvikPct != null && (
                                                                                        <span className="text-[10px] ml-1">({avvikPct > 0 ? "+" : ""}{avvikPct.toFixed(0)}%)</span>
                                                                                    )}
                                                                                </span>
                                                                            ) : "—"}
                                                                        </td>
                                                                    )}
                                                                    <td className="px-6 py-4 text-right">
                                                                        <Link href={`/properties/${row.property.property_id}`} className="p-2 hover:bg-muted/10 rounded-lg inline-block transition-colors">
                                                                            <TrendingUp size={16} className="text-muted group-hover:text-primary" />
                                                                        </Link>
                                                                    </td>
                                                                </tr>
                                                            );
                                                        })}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </Accordion>
                                    </div>
                                ))}
                            </div>
                                )}
                            </div>
                        )}

                        {/* Suppliers Tab */}
                        {activeTab === 'suppliers' && (
                            <div className="space-y-6">
                                {supplierStats ? (
                                    <>
                                        <div className="glass-card p-6 border border-border rounded-xl">
                                            <div className="flex items-center gap-3 mb-4">
                                                <Users className="text-primary" size={24} />
                                                <h2 className="text-2xl font-bold">Leverandørstatistikk</h2>
                                            </div>
                                            <p className="text-sm text-muted mb-4">
                                                Utleier (leie): vi betaler leie for lokaler. Løpende utgift: strøm, fellesutgifter, vedlikehold m.m.
                                            </p>
                                            {/* Sum leietakere vs løpende utgifter + cakediagram */}
                                            {(() => {
                                                const leietakerSum = supplierStats.suppliers
                                                    .filter(s => getSupplierType(s.category) === "leietaker")
                                                    .reduce((sum, s) => sum + s.total_amount, 0);
                                                const løpendeSum = supplierStats.suppliers
                                                    .filter(s => getSupplierType(s.category) === "løpende")
                                                    .reduce((sum, s) => sum + s.total_amount, 0);
                                                const leietakerCount = supplierStats.suppliers.filter(s => getSupplierType(s.category) === "leietaker").length;
                                                const løpendeCount = supplierStats.suppliers.filter(s => getSupplierType(s.category) === "løpende").length;
                                                const pieData = [
                                                    { name: "Utleier (leie)", value: leietakerSum, fill: "hsl(var(--primary))" },
                                                    { name: "Løpende utgifter", value: løpendeSum, fill: "rgb(245, 158, 11)" },
                                                ].filter(d => d.value > 0);
                                                return (
                                                    <>
                                                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                                                            <div className="bg-primary/10 p-4 rounded-lg border border-primary/30">
                                                                <div className="text-xs text-muted font-bold uppercase tracking-wider mb-1">Leietakere (utleiere)</div>
                                                                <div className="text-lg font-bold text-primary">{formatCurrency(leietakerSum)}</div>
                                                                <div className="text-xs text-muted">{leietakerCount} leverandører</div>
                                                            </div>
                                                            <div className="bg-amber-500/10 p-4 rounded-lg border border-amber-500/30">
                                                                <div className="text-xs text-muted font-bold uppercase tracking-wider mb-1">Løpende utgifter</div>
                                                                <div className="text-lg font-bold text-amber-600 dark:text-amber-500">{formatCurrency(løpendeSum)}</div>
                                                                <div className="text-xs text-muted">{løpendeCount} leverandører</div>
                                                            </div>
                                                        </div>
                                                        {pieData.length > 0 && (
                                                            <div className="mb-6 w-full h-60">
                                                                <ResponsiveContainer width="100%" height={240}>
                                                                    <PieChart>
                                                                        <Pie
                                                                            data={pieData}
                                                                            dataKey="value"
                                                                            nameKey="name"
                                                                            cx="50%"
                                                                            cy="50%"
                                                                            outerRadius={80}
                                                                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                                                        >
                                                                            {pieData.map((entry, index) => (
                                                                                <Cell key={index} fill={entry.fill} />
                                                                            ))}
                                                                        </Pie>
                                                                        <Tooltip formatter={(value: number) => [formatFullCurrency(value), "Beløp"]} />
                                                                        <Legend />
                                                                    </PieChart>
                                                                </ResponsiveContainer>
                                                            </div>
                                                        )}
                                                    </>
                                                );
                                            })()}
                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4">
                                                <div className="bg-muted/10 p-4 rounded-lg border border-border">
                                                    <div className="text-xs text-muted font-bold uppercase tracking-wider mb-1">Total Porteføljekostnad</div>
                                                    <div className="text-xl font-bold">{formatCurrency(supplierStats.total_portfolio_cost)}</div>
                                                </div>
                                                <div className="bg-muted/10 p-4 rounded-lg border border-border">
                                                    <div className="text-xs text-muted font-bold uppercase tracking-wider mb-1">Antall Leverandører</div>
                                                    <div className="text-xl font-bold">{supplierStats.supplier_count}</div>
                                                </div>
                                                <div className="bg-muted/10 p-4 rounded-lg border border-border">
                                                    <div className="text-xs text-muted font-bold uppercase tracking-wider mb-1">Gjennomsnitt per Leverandør</div>
                                                    <div className="text-xl font-bold">{formatCurrency(supplierStats.total_portfolio_cost / supplierStats.supplier_count)}</div>
                                                </div>
                                            </div>
                                            {/* Filter: Alle / Leietakere / Løpende utgifter + Søk + Last ned CSV */}
                                            <div className="flex flex-wrap items-center gap-2 mb-4">
                                                <span className="text-sm text-muted self-center mr-2">Vis:</span>
                                                <button
                                                    onClick={() => setSupplierFilter('all')}
                                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${supplierFilter === 'all' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 text-muted hover:bg-muted'
                                                        }`}
                                                >
                                                    Alle
                                                </button>
                                                <button
                                                    onClick={() => setSupplierFilter('leietaker')}
                                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${supplierFilter === 'leietaker' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 text-muted hover:bg-muted'
                                                        }`}
                                                >
                                                    Leietakere (utleiere)
                                                </button>
                                                <button
                                                    onClick={() => setSupplierFilter('løpende')}
                                                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${supplierFilter === 'løpende' ? 'bg-amber-500 text-white' : 'bg-muted/50 text-muted hover:bg-muted'
                                                        }`}
                                                >
                                                    Løpende utgifter
                                                </button>
                                                <input
                                                    type="text"
                                                    value={supplierSearch}
                                                    onChange={(e) => setSupplierSearch(e.target.value)}
                                                    placeholder="Søk i leverandør eller kategori"
                                                    className="ml-2 px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-sm min-w-50"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        const searchFiltered = supplierSearch.trim()
                                                            ? supplierStats.suppliers.filter(s =>
                                                                (s.name && s.name.toLowerCase().includes(supplierSearch.toLowerCase())) ||
                                                                (s.category && s.category.toLowerCase().includes(supplierSearch.toLowerCase()))
                                                            )
                                                            : supplierStats.suppliers;
                                                        const filtered = supplierFilter === "all"
                                                            ? searchFiltered
                                                            : searchFiltered.filter(s => getSupplierType(s.category) === supplierFilter);
                                                        const headers = ["Leverandør", "Total Kostnad", "Antall Eiendommer", "Type", "Kategori"];
                                                        const rows = filtered.map(s => [
                                                            s.name ?? "",
                                                            String(s.total_amount ?? 0),
                                                            String(s.property_count ?? 0),
                                                            getSupplierType(s.category) === "leietaker" ? "Utleier (leie)" : "Løpende utgift",
                                                            s.category ?? "",
                                                        ]);
                                                        const csv = [headers.join(";"), ...rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(";"))].join("\n");
                                                        const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
                                                        const url = URL.createObjectURL(blob);
                                                        const a = document.createElement("a");
                                                        a.href = url;
                                                        a.download = "leverandorer.csv";
                                                        a.click();
                                                        URL.revokeObjectURL(url);
                                                    }}
                                                    className="px-3 py-1.5 rounded-lg text-sm font-medium bg-muted/50 text-muted hover:bg-muted border border-border"
                                                >
                                                    Last ned CSV
                                                </button>
                                            </div>
                                            {(() => {
                                                const searchFiltered = supplierSearch.trim()
                                                    ? supplierStats.suppliers.filter(s =>
                                                        (s.name && s.name.toLowerCase().includes(supplierSearch.toLowerCase())) ||
                                                        (s.category && s.category.toLowerCase().includes(supplierSearch.toLowerCase()))
                                                    )
                                                    : supplierStats.suppliers;
                                                const filtered = supplierFilter === 'all'
                                                    ? searchFiltered
                                                    : searchFiltered.filter(s => getSupplierType(s.category) === supplierFilter);
                                                const displayList = filtered.slice(0, statsVisibleCount);
                                                return (
                                                    <div className="overflow-hidden rounded-xl border border-border bg-background">
                                                        <table className="w-full text-left text-sm">
                                                            <thead>
                                                                <tr className="border-b border-border bg-muted/30">
                                                                    <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Leverandør</th>
                                                                    <th className="px-6 py-4 text-right font-bold text-primary uppercase text-xs tracking-wider">Total Kostnad</th>
                                                                    <th className="px-6 py-4 text-right font-bold text-primary uppercase text-xs tracking-wider">Antall Eiendommer</th>
                                                                    <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase text-xs tracking-wider">Type</th>
                                                                    <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase text-xs tracking-wider">Underkategori</th>
                                                                    <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase text-xs tracking-wider">Kategori</th>
                                                                    <th className="px-6 py-4 w-20"></th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-border">
                                                                {displayList.map((supplier, idx) => {
                                                                    const type = getSupplierType(supplier.category);
                                                                    return (
                                                                        <tr key={idx} className="hover:bg-muted/5 transition-colors">
                                                                            <td className="px-6 py-4 font-medium text-foreground">{supplier.name}</td>
                                                                            <td className="px-6 py-4 text-right font-mono text-foreground">{formatFullCurrency(supplier.total_amount)}</td>
                                                                            <td className="px-6 py-4 text-right text-foreground">{supplier.property_count}</td>
                                                                            <td className="px-6 py-4">
                                                                                <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${type === "leietaker"
                                                                                    ? "bg-primary/20 text-primary"
                                                                                    : "bg-amber-500/20 text-amber-600 dark:text-amber-400"
                                                                                    }`}>
                                                                                    {type === "leietaker" ? "Utleier (leie)" : "Løpende utgift"}
                                                                                </span>
                                                                            </td>
                                                                            <td className="px-6 py-4 text-muted">
                                                                                {type === "løpende" ? getLøpendeSubcategory(supplier.category) : "—"}
                                                                            </td>
                                                                            <td className="px-6 py-4 text-muted">{supplier.category}</td>
                                                                            <td className="px-6 py-4">
                                                                                <button
                                                                                    type="button"
                                                                                    onClick={() => setSupplierDetailsModal(supplier)}
                                                                                    className="text-xs text-primary hover:underline"
                                                                                >
                                                                                    Detaljer
                                                                                </button>
                                                                            </td>
                                                                        </tr>
                                                                    );
                                                                })}
                                                            </tbody>
                                                        </table>
                                                        {filtered.length > statsVisibleCount && (
                                                            <div className="px-6 py-4 bg-muted/20 text-center border-t border-border">
                                                                <button
                                                                    onClick={() => setStatsVisibleCount(prev => prev + 50)}
                                                                    className="px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-sm font-bold transition-colors"
                                                                >
                                                                    Vis neste 50... ({filtered.length - statsVisibleCount} gjenstår)
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })()}
                                            {/* Drill-down modal: leverandørdetaljer */}
                                            {supplierDetailsModal && (
                                                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setSupplierDetailsModal(null)}>
                                                    <div className="glass-card border border-border rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-xl" onClick={e => e.stopPropagation()}>
                                                        <div className="p-6 border-b border-border flex items-center justify-between">
                                                            <h3 className="text-xl font-bold">Leverandør: {supplierDetailsModal.name}</h3>
                                                            <button type="button" onClick={() => setSupplierDetailsModal(null)} className="p-2 rounded-lg hover:bg-muted text-muted hover:text-foreground">Lukk</button>
                                                        </div>
                                                        <div className="p-6 overflow-auto max-h-[60vh]">
                                                            <table className="w-full text-left text-sm">
                                                                <thead>
                                                                    <tr className="border-b border-border bg-muted/30">
                                                                        <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Eiendom</th>
                                                                        <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Beløp</th>
                                                                        <th className="px-4 py-3 text-left font-bold text-muted-foreground uppercase text-xs">Kategori</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody className="divide-y divide-border">
                                                                    {(supplierDetailsModal.details || []).map((d, i) => (
                                                                        <tr key={i}>
                                                                            <td className="px-4 py-3 font-medium text-foreground">{d.name}</td>
                                                                            <td className="px-4 py-3 text-right font-mono text-foreground">{formatFullCurrency(d.amount)}</td>
                                                                            <td className="px-4 py-3 text-muted">{d.category ?? "—"}</td>
                                                                        </tr>
                                                                    ))}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </>
                                ) : (
                                    <div className="flex flex-col items-center justify-center p-20 gap-4">
                                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-muted font-medium">Laster leverandørstatistikk...</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'catalog' && (
                            <div className="space-y-6">
                                <div className="glass-card p-6 border border-border rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <Layers className="text-primary" size={24} />
                                        <h2 className="text-2xl font-bold">Leverandørregister</h2>
                                    </div>
                                    <p className="text-sm text-muted mb-4">
                                        Komplett register over leverandører og deres tjenesteområder, sammenstilt fra interne dokumenter og systemdata.
                                    </p>
                                    {!catalogLoaded ? (
                                        <div className="flex flex-col items-center gap-4 py-16">
                                            <p className="text-muted-foreground text-sm">Klikk for å laste leverandørregisteret</p>
                                            <button
                                                onClick={async () => {
                                                    setCatalogLoading(true);
                                                    try {
                                                        const data = await financialAnalysisApi.getSupplierCatalog();
                                                        setSupplierCatalog(data);
                                                        setCatalogLoaded(true);
                                                    } catch (err) {
                                                        console.error("Failed to load catalog", err);
                                                    } finally {
                                                        setCatalogLoading(false);
                                                    }
                                                }}
                                                disabled={catalogLoading}
                                                className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold hover:bg-primary/90 transition-all disabled:opacity-60"
                                            >
                                                {catalogLoading ? 'Laster...' : 'Hent leverandørregister'}
                                            </button>
                                        </div>
                                    ) : (
                                        <>
                                    <div className="flex items-center gap-2 mb-4">
                                        <input
                                            type="text"
                                            value={supplierSearch}
                                            onChange={(e) => setSupplierSearch(e.target.value)}
                                            placeholder="Søk i registeret..."
                                            className="px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-sm flex-1"
                                        />
                                    </div>
                                    <div className="overflow-hidden rounded-xl border border-border bg-background">
                                        <table className="w-full text-left text-sm">
                                            <thead>
                                                <tr className="border-b border-border bg-muted/30">
                                                    <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Leverandør</th>
                                                    <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Tjenester / Artikler</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border">
                                                {(() => {
                                                    const filtered = supplierCatalog.filter(s =>
                                                        s.Leverandør.toLowerCase().includes(supplierSearch.toLowerCase()) ||
                                                        s.Tjenester.toLowerCase().includes(supplierSearch.toLowerCase())
                                                    );
                                                    return (
                                                        <>
                                                            {filtered.slice(0, catalogVisibleCount).map((s, idx) => (
                                                                <tr key={idx} className="hover:bg-muted/5 transition-colors">
                                                                    <td className="px-6 py-4 font-medium text-foreground">{s.Leverandør}</td>
                                                                    <td className="px-6 py-4 text-muted">{s.Tjenester}</td>
                                                                </tr>
                                                            ))}
                                                            {filtered.length > catalogVisibleCount && (
                                                                <tr>
                                                                    <td colSpan={2} className="px-6 py-8 text-center bg-muted/5">
                                                                        <button
                                                                            onClick={() => setCatalogVisibleCount(prev => prev + 50)}
                                                                            className="px-6 py-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-lg font-bold transition-all"
                                                                        >
                                                                            Vis neste 50... ({filtered.length - catalogVisibleCount} gjenstår)
                                                                        </button>
                                                                    </td>
                                                                </tr>
                                                            )}
                                                        </>
                                                    );
                                                })()}
                                            </tbody>
                                        </table>
                                    </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeTab === 'invoices' && (
                            <div className="space-y-4">
                                <div className="flex items-center gap-3 mb-2">
                                    <Users className="text-primary" size={24} />
                                    <h2 className="text-2xl font-bold">Fakturadetaljer per Leverandør</h2>
                                </div>
                                <p className="text-sm text-muted mb-6">
                                    Oversikt over totalsum per leverandør med mulighet for å se fakturaspesifikasjoner per eiendom.
                                </p>
                                {!invoicesLoaded ? (
                                    <div className="flex flex-col items-center gap-4 py-16">
                                        <p className="text-muted-foreground text-sm">Klikk for å laste fakturadetaljer</p>
                                        <button
                                            onClick={() => setInvoicesLoaded(true)}
                                            className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold hover:bg-primary/90 transition-all"
                                        >
                                            Hent fakturadetaljer
                                        </button>
                                    </div>
                                ) : supplierStats ? (
                                <div className="mb-4">
                                    <input
                                        type="text"
                                        value={supplierSearch}
                                        onChange={(e) => setSupplierSearch(e.target.value)}
                                        placeholder="Søk etter leverandør..."
                                        className="px-4 py-2 rounded-lg border border-border bg-background w-full max-w-md"
                                    />
                                </div>
                                ) : null}
                                {invoicesLoaded && supplierStats ? (
                                    <div className="space-y-3">
                                        {(() => {
                                            const filtered = supplierStats.suppliers.filter(s =>
                                                s.name.toLowerCase().includes(supplierSearch.toLowerCase())
                                            );
                                            return (
                                                <>
                                                    {filtered.slice(0, invoicesVisibleCount).map((supplier, idx) => (
                                                        <div key={idx} className="bg-surface p-1 rounded-xl border border-border shadow-sm">
                                                            <Accordion
                                                                title={`${supplier.name}`}
                                                                icon={
                                                                    <div className="flex items-center gap-4">
                                                                        <span className="font-bold text-lg">{formatFullCurrency(supplier.total_amount)}</span>
                                                                        <span className="text-xs text-muted">({supplier.property_count} eiendommer)</span>
                                                                    </div>
                                                                }
                                                            >
                                                                <div className="p-4 bg-muted/5 rounded-lg border border-border mt-2 overflow-x-auto">
                                                                    <table className="w-full text-left text-sm min-w-max">
                                                                        <thead>
                                                                            <tr className="border-b border-border text-muted-foreground uppercase text-[10px] font-bold">
                                                                                <th className="px-4 py-2">Eiendom</th>
                                                                                <th className="px-4 py-2 text-right">Beløp</th>
                                                                                <th className="px-4 py-2 text-left">Kategori</th>
                                                                                <th className="px-4 py-2 text-left">Dato</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody className="divide-y divide-border">
                                                                            {supplier.details.map((d, i) => (
                                                                                <tr key={i} className="hover:bg-muted/10">
                                                                                    <td className="px-4 py-2 font-medium">{d.name}</td>
                                                                                    <td className="px-4 py-2 text-right font-mono">{formatFullCurrency(d.amount)}</td>
                                                                                    <td className="px-4 py-2 text-muted">{d.category}</td>
                                                                                    <td className="px-4 py-2 text-muted italic">{d.date || "—"}</td>
                                                                                </tr>
                                                                            ))}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            </Accordion>
                                                        </div>
                                                    ))}
                                                    {filtered.length > invoicesVisibleCount && (
                                                        <div className="py-4 text-center">
                                                            <button
                                                                onClick={() => setInvoicesVisibleCount(prev => prev + 50)}
                                                                className="px-6 py-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-lg font-bold transition-all"
                                                            >
                                                                Last inn flere leverandører... ({filtered.length - invoicesVisibleCount} gjenstår)
                                                            </button>
                                                        </div>
                                                    )}
                                                </>
                                            );
                                        })()}
                                    </div>
                                ) : invoicesLoaded ? (
                                    <p className="p-10 text-center text-muted">Ingen fakturadata tilgjengelig.</p>
                                ) : null}
                            </div>
                        )}

                        {/* Patterns Tab - Accordion med alle kostnadsmønstre */}
                        {activeTab === 'patterns' && (
                            <div className="space-y-4">
                                {commonPatterns ? (
                                    <>
                                        <div className="mb-6">
                                            <h2 className="text-2xl font-bold flex items-center gap-3">
                                                <BarChart3 className="text-primary" size={28} />
                                                Kostnadsmønstre
                                            </h2>
                                            <p className="text-muted mt-1">
                                                {commonPatterns.total_properties} eiendommer analysert. Utvid seksjoner for å se detaljer.
                                            </p>
                                        </div>

                                        {/* Oversikt */}
                                        <Accordion title="Oversikt – Vanlige kategorier og leverandører" icon={<BarChart3 size={22} className="text-primary" />} defaultOpen={true}>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                <div>
                                                    <h3 className="text-sm font-semibold mb-3 text-foreground">Vanligste Kostnadskategorier</h3>
                                                    <div className="space-y-2">
                                                        {commonPatterns.common_categories.slice(0, 10).map((cat, idx) => (
                                                            <div key={idx} className="flex items-center justify-between p-3 bg-muted/10 rounded-lg border border-border">
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="font-medium text-foreground truncate">{cat.category}</div>
                                                                    <div className="text-xs text-muted">{cat.property_count} eiendommer ({cat.percentage.toFixed(1)}%)</div>
                                                                </div>
                                                                <div className="text-right ml-2">
                                                                    <div className="font-bold text-foreground">{formatCurrency(cat.avg_amount)}</div>
                                                                    <div className="text-xs text-muted">snitt</div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div>
                                                    <h3 className="text-sm font-semibold mb-3 text-foreground">Vanligste Leverandører</h3>
                                                    <div className="space-y-2">
                                                        {commonPatterns.common_providers.slice(0, 10).map((prov, idx) => (
                                                            <div key={idx} className="flex items-center justify-between p-3 bg-muted/10 rounded-lg border border-border">
                                                                <div className="font-medium text-foreground truncate">{prov.provider}</div>
                                                                <div className="text-sm text-muted ml-2">{prov.transaction_count} trans.</div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </Accordion>

                                        {/* Leie-gap analyse */}
                                        <Accordion title="Leie-gap analyse – Kontraktsfestet vs GL-bokført" icon={<TrendingDown size={22} className="text-amber-500" />}>
                                            {!rentGapLoaded ? (
                                                <div className="flex flex-col items-center gap-4 py-8">
                                                    <p className="text-muted text-sm">Sammenligner kontraktsfestet husleie med GL-bokført husleie per eiendom</p>
                                                    <button
                                                        onClick={async () => {
                                                            setRentGapLoading(true);
                                                            try {
                                                                const data = await financialAnalysisApi.getRentGap(selectedYear);
                                                                setRentGapData(data);
                                                                setRentGapLoaded(true);
                                                            } catch (e) { console.error(e); }
                                                            finally { setRentGapLoading(false); }
                                                        }}
                                                        disabled={rentGapLoading}
                                                        className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold hover:bg-primary/90 transition-all disabled:opacity-60"
                                                    >
                                                        {rentGapLoading ? 'Laster...' : 'Hent leie-gap analyse'}
                                                    </button>
                                                </div>
                                            ) : (
                                                <div>
                                                    {(() => {
                                                        const totalContracted = rentGapData.reduce((s, r) => s + r.contracted_rent, 0);
                                                        const totalGL = rentGapData.reduce((s, r) => s + r.gl_rent, 0);
                                                        const totalGap = totalContracted - totalGL;
                                                        return (
                                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4">
                                                                <div className="bg-primary/10 p-4 rounded-lg border border-primary/30 text-center">
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">Kontraktsfestet</div>
                                                                    <div className="text-xl font-bold text-primary">{formatCurrency(totalContracted)}</div>
                                                                </div>
                                                                <div className="bg-sky-500/10 p-4 rounded-lg border border-sky-500/30 text-center">
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">GL-bokført</div>
                                                                    <div className="text-xl font-bold text-sky-600">{formatCurrency(totalGL)}</div>
                                                                </div>
                                                                <div className="bg-amber-500/10 p-4 rounded-lg border border-amber-500/30 text-center">
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">Total gap</div>
                                                                    <div className="text-xl font-bold text-amber-600">{formatCurrency(totalGap)}</div>
                                                                </div>
                                                            </div>
                                                        );
                                                    })()}
                                                    <div className="overflow-hidden rounded-xl border border-border bg-background">
                                                        <table className="w-full text-left text-sm">
                                                            <thead>
                                                                <tr className="border-b border-border bg-muted/30">
                                                                    <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Eiendom</th>
                                                                    <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Region</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-primary uppercase text-xs">Kontraktsfestet</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-sky-600 uppercase text-xs">GL-bokført</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-amber-600 uppercase text-xs">Gap</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Gap %</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-border">
                                                                {rentGapData.slice(0, 30).map((r, i) => (
                                                                    <tr key={i} className="hover:bg-muted/5 transition-colors">
                                                                        <td className="px-4 py-3 font-medium text-foreground truncate max-w-48">{r.name}</td>
                                                                        <td className="px-4 py-3 text-muted text-xs">{r.region}</td>
                                                                        <td className="px-4 py-3 text-right font-mono">{formatFullCurrency(r.contracted_rent)}</td>
                                                                        <td className="px-4 py-3 text-right font-mono text-sky-700 dark:text-sky-400">{r.gl_rent > 0 ? formatFullCurrency(r.gl_rent) : '—'}</td>
                                                                        <td className={`px-4 py-3 text-right font-mono font-semibold ${r.gap > 500000 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                                                            {formatFullCurrency(r.gap)}
                                                                        </td>
                                                                        <td className="px-4 py-3 text-right text-muted text-xs">
                                                                            {r.gap_pct != null ? `${r.gap_pct}%` : '—'}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                    {rentGapData.length > 30 && (
                                                        <p className="text-center text-muted text-sm mt-2">Viser topp 30 av {rentGapData.length} eiendommer (sortert på størst gap)</p>
                                                    )}
                                                </div>
                                            )}
                                        </Accordion>

                                        {/* Husleieavstemming – grundig */}
                                        <Accordion title="Husleieavstemming – Kontonavn og gap" icon={<BarChart3 size={22} className="text-sky-500" />}>
                                            {!rentReconciliation ? (
                                                <div className="flex flex-col items-center gap-4 py-8">
                                                    <p className="text-muted text-sm">Vis alle GL-kontonavn, hvilke som regnes som husleie, og detaljert gap-analyse</p>
                                                    <button
                                                        onClick={async () => {
                                                            setRentReconciliationLoading(true);
                                                            try {
                                                                const data = await financialAnalysisApi.getRentReconciliation(selectedYear);
                                                                setRentReconciliation(data);
                                                            } catch (e) { console.error(e); }
                                                            finally { setRentReconciliationLoading(false); }
                                                        }}
                                                        disabled={rentReconciliationLoading}
                                                        className="px-6 py-2.5 bg-sky-600 text-white rounded-lg font-bold hover:bg-sky-700 transition-all disabled:opacity-60"
                                                    >
                                                        {rentReconciliationLoading ? 'Laster...' : 'Hent avstemming'}
                                                    </button>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                        <div className="bg-primary/10 p-3 rounded-lg border border-primary/30">
                                                            <div className="text-[10px] text-muted font-bold uppercase">Kontraktsfestet</div>
                                                            <div className="text-lg font-bold">{formatCurrency(rentReconciliation.contracted_rent_total)}</div>
                                                        </div>
                                                        <div className="bg-sky-500/10 p-3 rounded-lg border border-sky-500/30">
                                                            <div className="text-[10px] text-muted font-bold uppercase">GL husleie totalt</div>
                                                            <div className="text-lg font-bold text-sky-600">{formatCurrency(rentReconciliation.gl_lease_total)}</div>
                                                        </div>
                                                        <div className="bg-muted/30 p-3 rounded-lg border border-border">
                                                            <div className="text-[10px] text-muted font-bold uppercase">– med eiendom</div>
                                                            <div className="text-sm">{formatCurrency(rentReconciliation.gl_lease_with_property)}</div>
                                                        </div>
                                                        <div className="bg-muted/30 p-3 rounded-lg border border-border">
                                                            <div className="text-[10px] text-muted font-bold uppercase">– uten eiendom</div>
                                                            <div className="text-sm">{formatCurrency(rentReconciliation.gl_lease_orphan)}</div>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-4 items-center">
                                                        <span className="font-semibold text-amber-600">Gap: {formatCurrency(rentReconciliation.gap)}</span>
                                                        {rentReconciliation.gap_pct != null && (
                                                            <span className="text-muted text-sm">({rentReconciliation.gap_pct}%)</span>
                                                        )}
                                                    </div>
                                                    <div className="overflow-x-auto rounded-lg border border-border">
                                                        <table className="w-full text-sm">
                                                            <thead>
                                                                <tr className="bg-muted/30 border-b border-border">
                                                                    <th className="px-3 py-2 text-left font-bold">Kontonavn</th>
                                                                    <th className="px-3 py-2 text-right font-bold">Husleie?</th>
                                                                    <th className="px-3 py-2 text-right font-bold">Total</th>
                                                                    <th className="px-3 py-2 text-right font-bold">Med eiendom</th>
                                                                    <th className="px-3 py-2 text-right font-bold">Uten eiendom</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-border">
                                                                {rentReconciliation.accounts.slice(0, 25).map((a, i) => (
                                                                    <tr key={i} className={a.is_lease ? 'bg-sky-500/5' : ''}>
                                                                        <td className="px-3 py-2 truncate max-w-64">{a.account_name}</td>
                                                                        <td className="px-3 py-2 text-right">{a.is_lease ? '✓' : '—'}</td>
                                                                        <td className="px-3 py-2 text-right font-mono">{formatCurrency(a.total)}</td>
                                                                        <td className="px-3 py-2 text-right font-mono text-muted">{formatCurrency(a.with_property)}</td>
                                                                        <td className="px-3 py-2 text-right font-mono text-muted">{formatCurrency(a.orphan)}</td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                    <p className="text-xs text-muted">Kontonavn som starter med «Leie » eller er i listen regnes som husleie. Oppdatert kategorisering inkluderer «Leie av lager/naust/garsjer» og «Husleie».</p>
                                                </div>
                                            )}
                                        </Accordion>

                                        {/* Kostnadsvekst 2024→2025 */}
                                        <Accordion title="Kostnadsvekst 2024 → 2025" icon={<TrendingUp size={22} className="text-primary" />}>
                                            {!yoyLoaded ? (
                                                <div className="flex flex-col items-center gap-4 py-8">
                                                    <p className="text-muted text-sm">År-over-år endring per kostnadskateorii fra GL-data</p>
                                                    <button
                                                        onClick={async () => {
                                                            setYoyLoading(true);
                                                            try {
                                                                const data = await financialAnalysisApi.getYoyComparison();
                                                                setYoyData(data);
                                                                setYoyLoaded(true);
                                                            } catch (e) { console.error(e); }
                                                            finally { setYoyLoading(false); }
                                                        }}
                                                        disabled={yoyLoading}
                                                        className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold hover:bg-primary/90 transition-all disabled:opacity-60"
                                                    >
                                                        {yoyLoading ? 'Laster...' : 'Hent kostnadsvekst'}
                                                    </button>
                                                </div>
                                            ) : (
                                                <div>
                                                    {(() => {
                                                        const total24 = yoyData.reduce((s, r) => s + r.amount_2024, 0);
                                                        const total25 = yoyData.reduce((s, r) => s + r.amount_2025, 0);
                                                        const totalChange = total25 - total24;
                                                        const totalChangePct = total24 > 0 ? ((totalChange / total24) * 100).toFixed(1) : null;
                                                        return (
                                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-4">
                                                                <div className="bg-muted/10 p-4 rounded-lg border border-border text-center">
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">Total 2024</div>
                                                                    <div className="text-xl font-bold">{formatCurrency(total24)}</div>
                                                                </div>
                                                                <div className="bg-muted/10 p-4 rounded-lg border border-border text-center">
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">Total 2025</div>
                                                                    <div className="text-xl font-bold">{formatCurrency(total25)}</div>
                                                                </div>
                                                                <div className={`p-4 rounded-lg border text-center ${totalChange > 0 ? 'bg-amber-500/10 border-amber-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                                                                    <div className="text-xs text-muted font-bold uppercase mb-1">Endring</div>
                                                                    <div className={`text-xl font-bold ${totalChange > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                                                        {totalChange > 0 ? '+' : ''}{formatCurrency(totalChange)} ({totalChangePct != null ? `${totalChange > 0 ? '+' : ''}${totalChangePct}%` : '—'})
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        );
                                                    })()}
                                                    <div className="overflow-hidden rounded-xl border border-border bg-background">
                                                        <table className="w-full text-left text-sm">
                                                            <thead>
                                                                <tr className="border-b border-border bg-muted/30">
                                                                    <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Kategori</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">2024</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-primary uppercase text-xs">2025</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Endring</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">%</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-border">
                                                                {yoyData.map((r, i) => (
                                                                    <tr key={i} className="hover:bg-muted/5 transition-colors">
                                                                        <td className="px-4 py-3 font-medium text-foreground truncate max-w-64">{r.category}</td>
                                                                        <td className="px-4 py-3 text-right font-mono text-muted">{formatFullCurrency(r.amount_2024)}</td>
                                                                        <td className="px-4 py-3 text-right font-mono">{formatFullCurrency(r.amount_2025)}</td>
                                                                        <td className={`px-4 py-3 text-right font-mono font-semibold ${r.change_nok > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                                                            {r.change_nok > 0 ? '+' : ''}{formatFullCurrency(r.change_nok)}
                                                                        </td>
                                                                        <td className={`px-4 py-3 text-right text-sm font-semibold ${r.change_pct != null && r.change_pct > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                                                                            {r.change_pct != null ? `${r.change_pct > 0 ? '+' : ''}${r.change_pct}%` : '—'}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}
                                        </Accordion>

                                        {/* Budsjett vs faktisk – månedlig */}
                                        <Accordion title="Budsjett vs faktisk – månedlig (2025)" icon={<BadgePercent size={22} className="text-emerald-500" />}>
                                            {!monthlyLoaded ? (
                                                <div className="flex flex-col items-center gap-4 py-8">
                                                    <p className="text-muted text-sm">12 måneder 2025: budsjett (generert fra GL 2024 ×1.035) vs GL-faktisk</p>
                                                    <button
                                                        onClick={async () => {
                                                            setMonthlyLoading(true);
                                                            try {
                                                                const data = await financialAnalysisApi.getMonthlyBudgetActual(2025);
                                                                setMonthlyData(data);
                                                                setMonthlyLoaded(true);
                                                            } catch (e) { console.error(e); }
                                                            finally { setMonthlyLoading(false); }
                                                        }}
                                                        disabled={monthlyLoading}
                                                        className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg font-bold hover:bg-primary/90 transition-all disabled:opacity-60"
                                                    >
                                                        {monthlyLoading ? 'Laster...' : 'Hent månedlig budsjett vs faktisk'}
                                                    </button>
                                                </div>
                                            ) : (
                                                <div>
                                                    <div className="mb-6 h-72">
                                                        <ResponsiveContainer width="100%" height={280}>
                                                            <BarChart data={monthlyData} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
                                                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                                                                <XAxis dataKey="month_name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                                                                <YAxis tickFormatter={(v) => `${(v / 1000000).toFixed(0)}M`} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                                                                <Tooltip
                                                                    formatter={(value: number, name: string) => [formatFullCurrency(value), name === 'budget' ? 'Budsjett' : 'Faktisk']}
                                                                    contentStyle={{ backgroundColor: 'hsl(var(--surface))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: 12 }}
                                                                />
                                                                <Legend formatter={(v) => v === 'budget' ? 'Budsjett' : 'Faktisk'} />
                                                                <Bar dataKey="budget" fill="hsl(var(--primary))" opacity={0.4} radius={[4, 4, 0, 0]} name="budget" />
                                                                <Bar dataKey="actual" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} name="actual" />
                                                            </BarChart>
                                                        </ResponsiveContainer>
                                                    </div>
                                                    <div className="overflow-hidden rounded-xl border border-border bg-background">
                                                        <table className="w-full text-left text-sm">
                                                            <thead>
                                                                <tr className="border-b border-border bg-muted/30">
                                                                    <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">Måned</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Budsjett</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-primary uppercase text-xs">Faktisk</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Varians</th>
                                                                    <th className="px-4 py-3 text-right font-bold text-muted-foreground uppercase text-xs">Varians %</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-border">
                                                                {monthlyData.map((r, i) => (
                                                                    <tr key={i} className="hover:bg-muted/5 transition-colors">
                                                                        <td className="px-4 py-3 font-medium text-foreground">{r.month_name}</td>
                                                                        <td className="px-4 py-3 text-right font-mono text-muted">{r.budget > 0 ? formatFullCurrency(r.budget) : '—'}</td>
                                                                        <td className="px-4 py-3 text-right font-mono">{r.actual > 0 ? formatFullCurrency(r.actual) : '—'}</td>
                                                                        <td className={`px-4 py-3 text-right font-mono font-semibold ${r.variance >= 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
                                                                            {r.budget > 0 || r.actual > 0 ? `${r.variance >= 0 ? '+' : ''}${formatFullCurrency(r.variance)}` : '—'}
                                                                        </td>
                                                                        <td className={`px-4 py-3 text-right text-sm ${r.variance_pct != null && r.variance_pct >= 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
                                                                            {r.variance_pct != null ? `${r.variance_pct >= 0 ? '+' : ''}${r.variance_pct}%` : '—'}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}
                                        </Accordion>

                                    </>
                                ) : (
                                    <div className="flex flex-col items-center justify-center p-20 gap-4">
                                        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-muted font-medium">Laster kostnadsmønstre...</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'missing-costs' && (
                            <div className="space-y-6">
                                <div className="glass-card p-6 border border-border rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <AlertTriangle className="text-amber-500" size={24} />
                                        <h2 className="text-2xl font-bold">Eiendommer uten kostnadsdata</h2>
                                    </div>
                                    <p className="text-sm text-muted mb-4">
                                        Eiendommer som ikke har GL-regnskapsdata (property_id eller koststed) for {selectedYear}. Disse vises ikke i økonomioversikten.
                                        {missingCostsLoaded && (
                                            <>
                                                <span className="ml-2 font-semibold text-foreground">
                                                    {missingCostsData.length} eiendommer
                                                </span>
                                                {(() => {
                                                    const byType = missingCostsData.reduce<Record<string, number>>((acc, p) => {
                                                        const t = p.unit_short_type || "Ukjent";
                                                        acc[t] = (acc[t] || 0) + 1;
                                                        return acc;
                                                    }, {});
                                                    const entries = Object.entries(byType).sort((a, b) => b[1] - a[1]);
                                                    if (entries.length <= 1) return null;
                                                    return (
                                                        <span className="ml-3 text-muted">
                                                            ({entries.map(([k, v]) => `${k}: ${v}`).join(", ")})
                                                        </span>
                                                    );
                                                })()}
                                            </>
                                        )}
                                    </p>
                                    {missingCostsLoading ? (
                                        <div className="flex flex-col items-center justify-center py-16 gap-4">
                                            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                            <p className="text-muted text-sm">Henter liste...</p>
                                        </div>
                                    ) : (
                                        <div className="overflow-hidden rounded-xl border border-border bg-background">
                                            <table className="w-full text-left text-sm">
                                                <thead>
                                                    <tr className="border-b border-border bg-muted/30">
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Eiendom</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Adresse</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Region</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Type</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Koststed</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider"></th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-border">
                                                    {missingCostsData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={6} className="px-6 py-12 text-center text-muted">
                                                                Alle eiendommer har kostnadsdata for {selectedYear}.
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        missingCostsData.map((p) => (
                                                            <tr key={p.property_id} className="hover:bg-muted/5 transition-colors group">
<td className="px-6 py-4 font-medium text-foreground">{p.name}</td>
                                                            <td className="px-6 py-4 text-muted">{p.address}</td>
                                                            <td className="px-6 py-4 text-muted">{p.region || "—"}</td>
                                                            <td className="px-6 py-4 text-muted">{p.unit_short_type || "—"}</td>
                                                            <td className="px-6 py-4 text-muted font-mono text-xs">{p.unit_id_erp || "—"}</td>
                                                                <td className="px-6 py-4 text-right">
                                                                    <Link href={`/properties/${p.property_id}`} className="p-2 hover:bg-muted/10 rounded-lg inline-block transition-colors">
                                                                        <TrendingUp size={16} className="text-muted group-hover:text-primary" />
                                                                    </Link>
                                                                </td>
                                                            </tr>
                                                        ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeTab === 'costs-without-property' && (
                            <div className="space-y-6">
                                <div className="glass-card p-6 border border-border rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <Landmark className="text-amber-500" size={24} />
                                        <h2 className="text-2xl font-bold">Kostnader uten eiendom</h2>
                                    </div>
                                    <p className="text-sm text-muted mb-4">
                                        Koststeder (department_code) fra GL som har bokførte kostnader for {selectedYear}, men som ikke matcher noen eiendom (unit_id_erp).
                                        {costsWithoutPropertyLoaded && (
                                            <span className="ml-2 font-semibold text-foreground">
                                                {costsWithoutPropertyData.length} koststeder, totalt {formatCurrency(costsWithoutPropertyTotal)}
                                            </span>
                                        )}
                                    </p>
                                    <div className="flex gap-2 mb-4">
                                        <button
                                            type="button"
                                            onClick={() => setCostsWithoutPropertyViewMode('list')}
                                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${costsWithoutPropertyViewMode === 'list' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'}`}
                                        >
                                            Liste
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setCostsWithoutPropertyViewMode('pivot')}
                                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${costsWithoutPropertyViewMode === 'pivot' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'}`}
                                        >
                                            Pivot (region)
                                        </button>
                                    </div>
                                    {costsWithoutPropertyViewMode === 'pivot' ? (
                                        costsWithoutPropertyPivotLoading ? (
                                            <div className="flex flex-col items-center justify-center py-16 gap-4">
                                                <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                                <p className="text-muted text-sm">Henter pivot...</p>
                                            </div>
                                        ) : costsWithoutPropertyPivotData?.groups?.length ? (
                                            <div className="overflow-x-auto rounded-xl border border-border bg-background">
                                                {costsWithoutPropertyPivotData.groups.map((grp) => (
                                                    <div key={grp.group} className="mb-4">
                                                        <div className="px-4 py-2 bg-muted/50 font-semibold text-sm border-b border-border">{grp.group}</div>
                                                        {grp.categories.map((cat) => (
                                                            <div key={cat.key} className="p-2">
                                                                <table className="w-full text-sm">
                                                                    <thead>
                                                                        <tr className="border-b border-border bg-muted/30">
                                                                            <th className="text-left px-4 py-2 font-medium text-muted-foreground">Koststed</th>
                                                                            {costsWithoutPropertyPivotData.regions.map((r) => (
                                                                                <th key={r} className="text-right px-2 py-2 font-medium text-muted-foreground min-w-20">{r}</th>
                                                                            ))}
                                                                            <th className="text-right px-4 py-2 font-medium text-muted-foreground">Totalsum</th>
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {cat.rows.map((row, i) => (
                                                                            <tr
                                                                                key={i}
                                                                                className="border-b border-border/50 hover:bg-muted/20 cursor-pointer"
                                                                                onClick={async () => {
                                                                                    if (expandedOrphanDept === row.department_code) {
                                                                                        setExpandedOrphanDept(null);
                                                                                        return;
                                                                                    }
                                                                                    setExpandedOrphanDept(row.department_code);
                                                                                    setOrphanTxLoading(true);
                                                                                    const res = await getOrphanTransactions(row.department_code, selectedYear, 0, 200);
                                                                                    setOrphanTransactions(res?.transactions ?? []);
                                                                                    setOrphanTxLoading(false);
                                                                                }}
                                                                            >
                                                                                <td className="px-4 py-2 font-medium">{row.department_name}</td>
                                                                                {costsWithoutPropertyPivotData.regions.map((r) => (
                                                                                    <td key={r} className="text-right px-2 py-2 font-mono text-muted-foreground">
                                                                                        {row.by_region[r] ? row.by_region[r].toLocaleString('no-NO') : '—'}
                                                                                    </td>
                                                                                ))}
                                                                                <td className="text-right px-4 py-2 font-mono font-semibold">{row.total.toLocaleString('no-NO')}</td>
                                                                            </tr>
                                                                        ))}
                                                                        <tr className="border-t-2 border-border bg-muted/40 font-semibold">
                                                                            <td className="px-4 py-2">Sum {cat.label}</td>
                                                                            {costsWithoutPropertyPivotData.regions.map((r) => (
                                                                                <td key={r} className="text-right px-2 py-2 font-mono">{cat.totals_by_region[r]?.toLocaleString('no-NO') ?? '—'}</td>
                                                                            ))}
                                                                            <td className="text-right px-4 py-2 font-mono">{cat.grand_total.toLocaleString('no-NO')}</td>
                                                                        </tr>
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        ))}
                                                    </div>
                                                ))}
                                            </div>
                                                                        ) : (
                                            <p className="text-muted py-8 text-center">Ingen koststeder uten eiendom for {selectedYear}.</p>
                                        )
                                    ) : null}
                                    {costsWithoutPropertyViewMode === 'pivot' && expandedOrphanDept && (
                                        <div className="mt-4 p-4 rounded-xl border border-border bg-muted/10">
                                            <div className="text-xs text-muted mb-2">Enkelttransaksjoner for {expandedOrphanDept} (første 200)</div>
                                            {orphanTxLoading ? (
                                                <div className="py-4 flex gap-2">
                                                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                                                    <span>Laster...</span>
                                                </div>
                                            ) : orphanTransactions.length === 0 ? (
                                                <p className="text-muted py-2">Ingen transaksjoner.</p>
                                            ) : (
                                                <div className="overflow-x-auto max-h-64 overflow-y-auto rounded border border-border bg-background">
                                                    <table className="w-full text-xs">
                                                        <thead>
                                                            <tr className="border-b border-border bg-muted/30">
                                                                <th className="px-3 py-2 text-left">Periode</th>
                                                                <th className="px-3 py-2 text-left">Konto</th>
                                                                <th className="px-3 py-2 text-left">Leverandør</th>
                                                                <th className="px-3 py-2 text-left">Dim2</th>
                                                                <th className="px-3 py-2 text-right">Beløp</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {orphanTransactions.map((tx, i) => (
                                                                <tr key={tx.transaction_id || i} className="border-b border-border/50">
                                                                    <td className="px-3 py-2 font-mono">{tx.period}</td>
                                                                    <td className="px-3 py-2">{tx.account_name}</td>
                                                                    <td className="px-3 py-2">{tx.supplier_name}</td>
                                                                    <td className="px-3 py-2">{tx.dim2_name ?? ''}</td>
                                                                    <td className="px-3 py-2 text-right font-mono">{formatFullCurrency(tx.amount)}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {costsWithoutPropertyViewMode === 'list' && costsWithoutPropertyLoading ? (
                                        <div className="flex flex-col items-center justify-center py-16 gap-4">
                                            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                            <p className="text-muted text-sm">Henter liste...</p>
                                        </div>
                                    ) : (
                                        <div className="overflow-hidden rounded-xl border border-border bg-background">
                                            <table className="w-full text-left text-sm">
                                                <thead>
                                                    <tr className="border-b border-border bg-muted/30">
                                                        <th className="px-6 py-4 w-8"></th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Koststed</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Navn</th>
                                                        <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase text-xs tracking-wider">Beløp</th>
                                                        <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase text-xs tracking-wider">Antall poster</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-border">
                                                    {costsWithoutPropertyData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={5} className="px-6 py-12 text-center text-muted">
                                                                Alle koststeder er koblet til eiendommer.
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        costsWithoutPropertyData.map((c) => (
                                                            <React.Fragment key={c.department_code}>
                                                                <tr
                                                                    className="hover:bg-muted/5 transition-colors cursor-pointer"
                                                                    onClick={async () => {
                                                                        if (expandedOrphanDept === c.department_code) {
                                                                            setExpandedOrphanDept(null);
                                                                            return;
                                                                        }
                                                                        setExpandedOrphanDept(c.department_code);
                                                                        setOrphanTxLoading(true);
                                                                        const res = await getOrphanTransactions(c.department_code, selectedYear, 0, 200);
                                                                        setOrphanTransactions(res?.transactions ?? []);
                                                                        setOrphanTxLoading(false);
                                                                    }}
                                                                >
                                                                    <td className="px-2 py-4">
                                                                        {expandedOrphanDept === c.department_code ? (
                                                                            <ChevronDown size={18} className="text-muted" />
                                                                        ) : (
                                                                            <ChevronRight size={18} className="text-muted" />
                                                                        )}
                                                                    </td>
                                                                    <td className="px-6 py-4 font-mono font-medium text-foreground">{c.department_code}</td>
                                                                    <td className="px-6 py-4 text-muted">{c.department_name}</td>
                                                                    <td className="px-6 py-4 text-right font-mono text-amber-700 dark:text-amber-400">{formatFullCurrency(c.total)}</td>
                                                                    <td className="px-6 py-4 text-right text-muted">{c.transaction_count}</td>
                                                                </tr>
                                                                {expandedOrphanDept === c.department_code && (
                                                                    <tr>
                                                                        <td colSpan={5} className="px-6 py-4 bg-muted/10">
                                                                            <div className="text-xs text-muted mb-2">Enkelttransaksjoner (første 200)</div>
                                                                            {orphanTxLoading ? (
                                                                                <div className="py-4 flex items-center gap-2">
                                                                                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                                                                                    <span>Laster...</span>
                                                                                </div>
                                                                            ) : orphanTransactions.length === 0 ? (
                                                                                <p className="text-muted py-2">Ingen transaksjoner funnet.</p>
                                                                            ) : (
                                                                                <div className="overflow-x-auto max-h-64 overflow-y-auto rounded border border-border bg-background">
                                                                                    <table className="w-full text-xs">
                                                                                        <thead>
                                                                                            <tr className="border-b border-border bg-muted/30">
                                                                                                <th className="px-3 py-2 text-left">Periode</th>
                                                                                                <th className="px-3 py-2 text-left">Konto</th>
                                                                                                <th className="px-3 py-2 text-left">Leverandør</th>
                                                                                                <th className="px-3 py-2 text-left">Dim2/Adresse</th>
                                                                                                <th className="px-3 py-2 text-right">Beløp</th>
                                                                                                <th className="px-3 py-2 text-left">Faktura</th>
                                                                                            </tr>
                                                                                        </thead>
                                                                                        <tbody>
                                                                                            {orphanTransactions.map((tx, i) => (
                                                                                                <tr key={tx.transaction_id || i} className="border-b border-border/50">
                                                                                                    <td className="px-3 py-2 font-mono">{tx.period}</td>
                                                                                                    <td className="px-3 py-2">{tx.account_name}</td>
                                                                                                    <td className="px-3 py-2">{tx.supplier_name}</td>
                                                                                                    <td className="px-3 py-2">{tx.dim2_name ?? ""}</td>
                                                                                                    <td className="px-3 py-2 text-right font-mono">{formatFullCurrency(tx.amount)}</td>
                                                                                                    <td className="px-3 py-2">{tx.invoice_number}</td>
                                                                                                </tr>
                                                                                            ))}
                                                                                        </tbody>
                                                                                    </table>
                                                                                </div>
                                                                            )}
                                                                        </td>
                                                                    </tr>
                                                                )}
                                                            </React.Fragment>
                                                        ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeTab === 'discontinued-properties' && (
                            <div className="space-y-6">
                                <div className="glass-card p-6 border border-border rounded-xl">
                                    <div className="flex items-center gap-3 mb-4">
                                        <GitBranch className="text-amber-500" size={24} />
                                        <h2 className="text-2xl font-bold">Avviklet eiendom</h2>
                                    </div>
                                    <p className="text-sm text-muted mb-4">
                                        Eiendommer som ikke finnes i budsjettgrunnlaget for 2025 og som samtidig ikke har GL-kostnader i valgt år (uten aktivitet i året).
                                        {discontinuedPropertiesLoaded && (
                                            <span className="ml-2 font-semibold text-foreground">
                                                {discontinuedPropertiesData.length} eiendommer
                                            </span>
                                        )}
                                    </p>
                                    {!discontinuedBudgetAvailable && (
                                        <div className="mb-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
                                            Budsjettdata er ikke tilgjengelig nå. Listen kan være ufullstendig.
                                        </div>
                                    )}
                                    {discontinuedPropertiesLoading ? (
                                        <div className="flex flex-col items-center justify-center py-16 gap-4">
                                            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                            <p className="text-muted text-sm">Henter liste...</p>
                                        </div>
                                    ) : (
                                        <div className="overflow-hidden rounded-xl border border-border bg-background">
                                            <table className="w-full text-left text-sm">
                                                <thead>
                                                    <tr className="border-b border-border bg-muted/30">
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Eiendom</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Adresse</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Region</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Type</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">Koststed</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider">GL-kostnader {selectedYear}</th>
                                                        <th className="px-6 py-4 font-bold text-muted-foreground uppercase text-xs tracking-wider"></th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-border">
                                                    {discontinuedPropertiesData.length === 0 ? (
                                                        <tr>
                                                            <td colSpan={7} className="px-6 py-12 text-center text-muted">
                                                                Ingen avviklede eiendommer funnet med valgt regel (ikke i budsjett 2025 + ingen GL-kostnader i valgt år).
                                                            </td>
                                                        </tr>
                                                    ) : (
                                                        discontinuedPropertiesData.map((p) => (
                                                            <tr key={p.property_id} className="hover:bg-muted/5 transition-colors group">
                                                                <td className="px-6 py-4 font-medium text-foreground">{p.name}</td>
                                                                <td className="px-6 py-4 text-muted">{p.address || "—"}</td>
                                                                <td className="px-6 py-4 text-muted">{p.region || "—"}</td>
                                                                <td className="px-6 py-4 text-muted">{p.unit_short_type || "—"}</td>
                                                                <td className="px-6 py-4 text-muted font-mono text-xs">{p.unit_id_erp || "—"}</td>
                                                                <td className="px-6 py-4 text-muted">
                                                                    {p.has_costs_in_year ? formatCurrency(p.total_cost_in_year) : "Ingen"}
                                                                </td>
                                                                <td className="px-6 py-4 text-right">
                                                                    <Link href={`/properties/${p.property_id}`} className="p-2 hover:bg-muted/10 rounded-lg inline-block transition-colors">
                                                                        <TrendingUp size={16} className="text-muted group-hover:text-primary" />
                                                                    </Link>
                                                                </td>
                                                            </tr>
                                                        ))
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {activeTab === 'contracts-pivot' && (
                            <div className="space-y-6">
                                <div className="glass-card p-6 border border-border rounded-xl">
                                    <h3 className="text-lg font-bold text-foreground mb-2">Kontraktsoversikt (pivot)</h3>
                                    <p className="text-sm text-muted mb-4">
                                        Aktive kontrakter – velg rader og kolonner for å pivotere dynamisk. Kontraktsleie per år.
                                    </p>
                                    <ContractsPivotView />
                                </div>
                            </div>
                        )}

                        {activeTab === 'transactions' && (
                            <div className="space-y-6">
                                <TransactionExplorer />
                            </div>
                        )}

                        {activeTab === 'sammenligning-2026' && (
                            <Sammenligning2026
                                allRows={allPropertyRows}
                                financeBudget2026={financeBudget2026}
                            />
                        )}
                    </>
                )}
            </main>
        </div>
    );
}

function FinancialsGuard() {
    const { show_financials, loading } = useFeatureFlags();
    if (loading) return null;
    if (!show_financials) {
        return (
            <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4 text-center px-6">
                <div className="p-4 bg-amber-50 dark:bg-amber-950/30 rounded-full">
                    <svg className="w-10 h-10 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                </div>
                <h2 className="text-xl font-bold text-foreground">Økonomidata er ikke tilgjengelig</h2>
                <p className="text-muted-foreground text-sm max-w-sm">Tilgang til finansielle tall er midlertidig deaktivert av administrator.</p>
            </div>
        );
    }
    return (
        <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-muted">Laster økonomisk oversikt...</div>}>
            <FinancialsContent />
        </Suspense>
    );
}

export default function FinancialsPage() {
    return <FinancialsGuard />;
}
