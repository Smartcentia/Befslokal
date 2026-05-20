"use client";

import React, { useEffect, useState, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { fetchAPI } from "@/lib/api/client";
import DataTooltip from "@/app/components/ui/DataTooltip";
import { Building2, TrendingUp, Search, ChevronUp, ChevronDown, Calculator, ArrowRight } from "lucide-react";

interface Institution {
    property_id: string;
    name: string | null;
    address: string | null;
    region: string | null;
    approved_places: number | null;
    budgeted_places: number | null;
    affiliation: string | null;
    unit_type_derived: string | null;
    department_code: string | null;
    closed_at: string | null;
    unit_id_erp: string | null;
    annual_cost_2025: number | null;
    cost_per_place: number | null;
}

interface ByRegion {
    count: number;
    approved_places: number;
    budgeted_places: number;
}

interface InstitutionsResponse {
    institutions: Institution[];
    by_region: Record<string, ByRegion>;
    total_approved_places: number;
    total_budgeted_places: number;
    total_count: number;
}

type SortKey = "name" | "region" | "approved_places" | "budgeted_places" | "cost_per_place";

const formatNOK = (n: number | null) =>
    n == null ? "–" : new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

const REGION_ORDER = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir", "Ukjent"];

function InstitutionSortIcon({
    k,
    sortKey,
    sortAsc,
}: {
    k: SortKey;
    sortKey: SortKey;
    sortAsc: boolean;
}) {
    return sortKey === k ? (sortAsc ? <ChevronUp size={12} /> : <ChevronDown size={12} />) : null;
}

function InstitusjonsContent() {
    const searchParams = useSearchParams();
    const [data, setData] = useState<InstitutionsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [regionFilter, setRegionFilter] = useState<string>(
        searchParams.get("region") ?? "Alle"
    );
    const [showClosed, setShowClosed] = useState(false);
    const [sortKey, setSortKey] = useState<SortKey>("region");
    const [sortAsc, setSortAsc] = useState(true);

    useEffect(() => {
        fetchAPI<InstitutionsResponse>("/properties/institutions")
            .then((d) => setData(d))
            .catch(() => setData(null))
            .finally(() => setLoading(false));
    }, []);

    const regions = useMemo(() => {
        if (!data) return ["Alle"];
        const r = Array.from(new Set(data.institutions.map((i) => i.region || "Ukjent")));
        r.sort((a, b) => REGION_ORDER.indexOf(a) - REGION_ORDER.indexOf(b));
        return ["Alle", ...r];
    }, [data]);

    const filtered = useMemo(() => {
        if (!data) return [];
        let list = data.institutions;
        if (!showClosed) list = list.filter((i) => !i.closed_at);
        if (regionFilter !== "Alle") list = list.filter((i) => (i.region || "Ukjent") === regionFilter);
        if (search.trim()) {
            const q = search.toLowerCase();
            list = list.filter(
                (i) =>
                    (i.name || "").toLowerCase().includes(q) ||
                    (i.address || "").toLowerCase().includes(q) ||
                    (i.affiliation || "").toLowerCase().includes(q) ||
                    (i.department_code || "").toLowerCase().includes(q)
            );
        }
        // Sort
        list = [...list].sort((a, b) => {
            const av: string | number | null = a[sortKey] ?? null;
            const bv: string | number | null = b[sortKey] ?? null;
            if (av == null) return 1;
            if (bv == null) return -1;
            if (typeof av === "string" && typeof bv === "string") {
                return sortAsc ? av.localeCompare(bv, "nb") : bv.localeCompare(av, "nb");
            }
            return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
        });
        return list;
    }, [data, search, regionFilter, showClosed, sortKey, sortAsc]);

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) setSortAsc(!sortAsc);
        else { setSortKey(key); setSortAsc(true); }
    };

    if (loading) {
        return (
            <div className="p-8 space-y-4 animate-pulse">
                <div className="h-8 bg-muted rounded w-64" />
                <div className="grid grid-cols-4 gap-4">
                    {[1,2,3,4].map(i => <div key={i} className="h-20 bg-muted rounded" />)}
                </div>
                <div className="h-96 bg-muted rounded" />
            </div>
        );
    }

    if (!data) {
        return <div className="p-8 text-muted">Kunne ikke laste institusjonsdata.</div>;
    }

    const totalGK = filtered.reduce((s, i) => s + (i.approved_places || 0), 0);
    const totalBudj = filtered.reduce((s, i) => s + (i.budgeted_places || 0), 0);
    const avgCostPerPlace = (() => {
        const withData = filtered.filter((i) => i.cost_per_place != null && i.approved_places && i.approved_places > 0);
        if (!withData.length) return null;
        const sum = withData.reduce((s, i) => s + (i.cost_per_place || 0), 0);
        return Math.round(sum / withData.length);
    })();

    return (
        <div className="p-6 space-y-6 max-w-screen-xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                        <Building2 className="text-primary" size={24} />
                        Barnevernsinstitusjoner
                    </h1>
                    <p className="text-sm text-muted mt-1">
                        Kapasitetsoversikt – GK-plasser og budsjetterte plasser per institusjon
                    </p>
                </div>
                <Link
                    href="/barnevern"
                    className="flex items-center gap-1.5 text-sm bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors font-medium"
                >
                    <Calculator size={14} />
                    Kostnadssimulering
                </Link>
            </div>

            {/* KPI-kort */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4">
                    <DataTooltip content="Totalt antall barnevernsinstitusjoner (ekskl. nedlagte).">
                        <div className="text-xs text-muted font-medium mb-1">Institusjoner</div>
                    </DataTooltip>
                    <div className="text-2xl font-bold text-foreground">{filtered.length}</div>
                    <div className="text-xs text-muted">{data.total_count} totalt inkl. nedlagte</div>
                </div>
                <div className="glass-card p-4">
                    <DataTooltip content="Totalt antall godkjente/kvalitetssikrede institusjonsplasser (GK-plasser) for de filtrerte institusjonene.">
                        <div className="text-xs text-muted font-medium mb-1">GK-plasser</div>
                    </DataTooltip>
                    <div className="text-2xl font-bold text-sky-600 dark:text-sky-400">{totalGK}</div>
                    <div className="text-xs text-muted">{data.total_approved_places} totalt portefølje</div>
                </div>
                <div className="glass-card p-4">
                    <DataTooltip content="Totalt antall budsjetterte plasser for de filtrerte institusjonene.">
                        <div className="text-xs text-muted font-medium mb-1">Budj. plasser</div>
                    </DataTooltip>
                    <div className="text-2xl font-bold text-foreground">{totalBudj}</div>
                    <div className="text-xs text-muted">{data.total_budgeted_places} totalt portefølje</div>
                </div>
                <div className="glass-card p-4">
                    <DataTooltip content="Gjennomsnittlig GL-kostnad per GK-plass (2025). Basert på institusjoner med kjente kostnader.">
                        <div className="text-xs text-muted font-medium mb-1">Snitt kost/plass</div>
                    </DataTooltip>
                    <div className="text-2xl font-bold text-foreground">
                        {avgCostPerPlace ? formatNOK(avgCostPerPlace) : "–"}
                    </div>
                    <div className="text-xs text-muted">per GK-plass (2025)</div>
                </div>
            </div>

            {/* Regionsoversikt */}
            <div className="glass-card p-4">
                <h2 className="font-semibold text-sm text-foreground mb-3 flex items-center gap-2">
                    <TrendingUp size={14} className="text-primary" />
                    Per region
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                    {REGION_ORDER.filter((r) => data.by_region[r]).map((reg) => {
                        const rd = data.by_region[reg];
                        return (
                            <button
                                key={reg}
                                onClick={() => setRegionFilter(regionFilter === reg ? "Alle" : reg)}
                                className={`text-left p-2 rounded-lg border transition-all ${
                                    regionFilter === reg
                                        ? "border-primary bg-primary/10"
                                        : "border-border hover:border-primary/50 hover:bg-muted/30"
                                }`}
                            >
                                <div className="font-semibold text-foreground">{reg}</div>
                                <div className="text-muted">{rd.count} inst.</div>
                                <div className="font-bold text-sky-600 dark:text-sky-400">{rd.approved_places} GK</div>
                                <div className="text-muted">{rd.budgeted_places} budj.</div>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Mini simuleringssammendrag */}
            {data && (
                <div className="flex items-center justify-between bg-primary/5 border border-primary/20 rounded-xl px-4 py-3 text-sm">
                    <div className="flex items-center gap-2 text-foreground">
                        <Calculator size={14} className="text-primary flex-shrink-0" />
                        <span>
                            <span className="font-semibold">{data.total_approved_places} GK-plasser</span>
                            {" "}i porteføljen. Se hva ulike bruksgrader koster.
                        </span>
                    </div>
                    <Link
                        href="/barnevern"
                        className="text-primary font-medium hover:underline flex items-center gap-1 whitespace-nowrap ml-4"
                    >
                        Simuler kostnad <ArrowRight size={14} />
                    </Link>
                </div>
            )}

            {/* Filter-rad */}
            <div className="flex flex-wrap gap-3 items-center">
                <div className="relative flex-1 min-w-48">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Søk navn, adresse, tilhørighet..."
                        className="w-full pl-8 pr-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary text-foreground placeholder:text-muted"
                    />
                </div>
                <select
                    value={regionFilter}
                    onChange={(e) => setRegionFilter(e.target.value)}
                    className="text-sm bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                    {regions.map((r) => <option key={r}>{r}</option>)}
                </select>
                <label className="flex items-center gap-2 text-sm text-foreground cursor-pointer">
                    <input
                        type="checkbox"
                        checked={showClosed}
                        onChange={(e) => setShowClosed(e.target.checked)}
                        className="rounded"
                    />
                    Vis nedlagte
                </label>
                <span className="text-xs text-muted ml-auto">{filtered.length} institusjoner</span>
            </div>

            {/* Tabell */}
            <div className="glass-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-muted/30 border-b border-border">
                            <tr>
                                <th
                                    className="text-left px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider cursor-pointer hover:text-foreground"
                                    onClick={() => toggleSort("name")}
                                >
                                    <span className="flex items-center gap-1">Institusjon <InstitutionSortIcon k="name" sortKey={sortKey} sortAsc={sortAsc} /></span>
                                </th>
                                <th
                                    className="text-left px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider cursor-pointer hover:text-foreground hidden md:table-cell"
                                    onClick={() => toggleSort("region")}
                                >
                                    <span className="flex items-center gap-1">Region <InstitutionSortIcon k="region" sortKey={sortKey} sortAsc={sortAsc} /></span>
                                </th>
                                <th
                                    className="text-right px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider cursor-pointer hover:text-foreground"
                                    onClick={() => toggleSort("approved_places")}
                                >
                                    <DataTooltip content="Antall godkjente/kvalitetssikrede plasser (GK-plasser) per avdeling pr. 01.01. Kilde: BIRK.">
                                        <span className="flex items-center justify-end gap-1">GK-pl. <InstitutionSortIcon k="approved_places" sortKey={sortKey} sortAsc={sortAsc} /></span>
                                    </DataTooltip>
                                </th>
                                <th
                                    className="text-right px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider cursor-pointer hover:text-foreground hidden lg:table-cell"
                                    onClick={() => toggleSort("budgeted_places")}
                                >
                                    <DataTooltip content="Antall budsjetterte institusjonsplasser per avdeling. Kilde: BIRK.">
                                        <span className="flex items-center justify-end gap-1">Budj. pl. <InstitutionSortIcon k="budgeted_places" sortKey={sortKey} sortAsc={sortAsc} /></span>
                                    </DataTooltip>
                                </th>
                                <th
                                    className="text-right px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider cursor-pointer hover:text-foreground hidden xl:table-cell"
                                    onClick={() => toggleSort("cost_per_place")}
                                >
                                    <DataTooltip content="GL-kostnad 2025 delt på antall GK-plasser. Indikator for ressursbruk per plass.">
                                        <span className="flex items-center justify-end gap-1">Kost/plass <InstitutionSortIcon k="cost_per_place" sortKey={sortKey} sortAsc={sortAsc} /></span>
                                    </DataTooltip>
                                </th>
                                <th className="text-left px-4 py-3 text-xs font-semibold text-muted uppercase tracking-wider hidden xl:table-cell">
                                    Tilhørighet
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={6} className="px-4 py-8 text-center text-muted text-sm">
                                        Ingen institusjoner funnet.
                                    </td>
                                </tr>
                            )}
                            {filtered.map((inst) => (
                                <tr
                                    key={inst.property_id}
                                    className={`hover:bg-muted/20 transition-colors ${inst.closed_at ? "opacity-50" : ""}`}
                                >
                                    <td className="px-4 py-3">
                                        <Link
                                            href={`/properties/${inst.property_id}`}
                                            className="font-medium text-foreground hover:text-primary transition-colors block"
                                        >
                                            {inst.name || "Ukjent"}
                                            {inst.closed_at && (
                                                <span className="ml-2 text-[10px] bg-destructive/20 text-destructive px-1.5 py-0.5 rounded font-semibold">
                                                    NEDLAGT
                                                </span>
                                            )}
                                        </Link>
                                        <div className="text-xs text-muted mt-0.5">{inst.address}</div>
                                    </td>
                                    <td className="px-4 py-3 hidden md:table-cell">
                                        <span className="text-xs bg-muted/40 px-2 py-0.5 rounded font-medium text-foreground">
                                            {inst.region || "Ukjent"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                        {inst.approved_places != null && inst.approved_places > 0 ? (
                                            <span className="font-bold text-sky-600 dark:text-sky-400 text-base">
                                                {inst.approved_places}
                                            </span>
                                        ) : (
                                            <span className="text-muted">–</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right hidden lg:table-cell">
                                        {inst.budgeted_places != null && inst.budgeted_places > 0 ? (
                                            <span className="font-medium text-foreground">{inst.budgeted_places}</span>
                                        ) : (
                                            <span className="text-muted">–</span>
                                        )}
                                    </td>
                                    <td className="px-4 py-3 text-right hidden xl:table-cell">
                                        <span className="text-foreground font-mono text-xs">
                                            {inst.cost_per_place != null ? formatNOK(inst.cost_per_place) : "–"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 hidden xl:table-cell">
                                        <span className="text-xs text-muted">{inst.affiliation || "–"}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                        {filtered.length > 0 && (
                            <tfoot className="bg-muted/20 border-t-2 border-border font-semibold">
                                <tr>
                                    <td className="px-4 py-3 text-sm text-foreground">
                                        Totalt {filtered.length} institusjoner
                                    </td>
                                    <td className="hidden md:table-cell" />
                                    <td className="px-4 py-3 text-right text-sky-600 dark:text-sky-400 text-base font-bold">
                                        {totalGK}
                                    </td>
                                    <td className="px-4 py-3 text-right text-foreground hidden lg:table-cell">
                                        {totalBudj}
                                    </td>
                                    <td className="hidden xl:table-cell" />
                                    <td className="hidden xl:table-cell" />
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>
            </div>
        </div>
    );
}

export default function InstitusjonsPage() {
    return (
        <Suspense fallback={<div className="p-8 text-muted text-sm">Laster institusjoner…</div>}>
            <InstitusjonsContent />
        </Suspense>
    );
}
