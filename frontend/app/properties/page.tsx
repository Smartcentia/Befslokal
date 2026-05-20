"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { getProperties, getPropertyTypes, getPropertyUnitShortTypes, getPropertySuggestions, getAvdelinger } from "@/lib/api/propertiesApi";
import type { Property } from "@/lib/api";
import { getBudgetSummary } from "@/lib/api/budgetApi";
import PropertyList, { type BudgetByProperty, type SortColumn } from "@/app/components/features/PropertyList";
import SearchBar from "@/app/components/ui/SearchBar";

const LIMIT = 50;

export default function PropertiesPage() {
    const router = useRouter();
    const [properties, setProperties] = useState<Property[]>([]);
    const [availableTypes, setAvailableTypes] = useState<string[]>([]);
    const [availableUnitShortTypes, setAvailableUnitShortTypes] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [typeFilter, setTypeFilter] = useState<string>("");
    const [unitTypeFilter, setUnitTypeFilter] = useState<string>("");
    const [sortBy, setSortBy] = useState<SortColumn>("name");
    const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
    const [includeDiscontinued, setIncludeDiscontinued] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [filterResetKey, setFilterResetKey] = useState(0);
    const [budgetByProperty, setBudgetByProperty] = useState<BudgetByProperty | undefined>(undefined);
    const [avdelingerByParentErpId, setAvdelingerByParentErpId] = useState<Map<string, Property[]>>(new Map());

    // Track current skip in a ref for "load more" to avoid stale closure
    const skipRef = useRef(0);

    const loadPage = useCallback(async (currentSkip: number, append: boolean) => {
        try {
            if (append) {
                setLoadingMore(true);
            } else {
                setLoading(true);
            }
            setError(null);

            const data = await getProperties(currentSkip, LIMIT, {
                usage: typeFilter || undefined,
                search: searchTerm || undefined,
                unit_short_type: unitTypeFilter || undefined,
                include_discontinued: includeDiscontinued,
                order_by: sortBy,
                order_dir: sortDir,
            });

            if (append) {
                setProperties((prev) => [...prev, ...data]);
            } else {
                setProperties(data);
            }

            skipRef.current = currentSkip + LIMIT;
            setHasMore(data.length === LIMIT);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Feil ved lasting av eiendommer");
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, [typeFilter, unitTypeFilter, searchTerm, includeDiscontinued, sortBy, sortDir]);

    // Reload from page 0 whenever filters or sort changes
    useEffect(() => {
        skipRef.current = 0;
        loadPage(0, false);
    }, [loadPage]);

    // Fetch available types once
    useEffect(() => {
        getPropertyTypes().then(setAvailableTypes);
        getPropertyUnitShortTypes().then(setAvailableUnitShortTypes);
    }, []);

    // Budget summary once
    useEffect(() => {
        getBudgetSummary(2026)
            .then((res) => setBudgetByProperty(new Map(res.by_property.map((b) => [b.property_id, b.total_annual_budget]))))
            .catch(() => setBudgetByProperty(undefined));
    }, []);

    // Fetch all avdelinger once, group by parent ERP id
    useEffect(() => {
        getAvdelinger(includeDiscontinued).then((avd) => {
            const map = new Map<string, Property[]>();
            for (const a of avd) {
                if (a.parent_unit_id_erp) {
                    const list = map.get(a.parent_unit_id_erp) ?? [];
                    list.push(a);
                    map.set(a.parent_unit_id_erp, list);
                }
            }
            setAvdelingerByParentErpId(map);
        }).catch(() => {});
    }, [includeDiscontinued]);

    const handleSort = (column: SortColumn) => {
        if (sortBy === column) {
            setSortDir((d) => (d === "asc" ? "desc" : "asc"));
        } else {
            setSortBy(column);
            setSortDir("asc");
        }
    };

    const handleLoadMore = () => {
        if (!loadingMore && hasMore) {
            loadPage(skipRef.current, true);
        }
    };

    if (loading && properties.length === 0) {
        return <div className="p-8 text-center text-foreground">Laster eiendommer...</div>;
    }

    if (error && properties.length === 0) {
        return (
            <div className="p-8 text-danger">
                <p>Feil: {error}</p>
                <button type="button" onClick={() => loadPage(0, false)} className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded">Prøv igjen</button>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 px-4">
            <header className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-foreground tracking-tight">
                    Eiendommer
                </h1>
                <div className="text-muted text-sm font-semibold">
                    Viser {properties.length} eiendommer
                </div>
            </header>

            <div className="mb-6 flex flex-wrap items-end gap-4">
                <div className="flex-1 min-w-50 max-w-2xl">
                    <SearchBar
                        key={filterResetKey}
                        onSearch={setSearchTerm}
                        getSuggestions={getPropertySuggestions}
                        onSuggestionSelect={(id) => router.push(`/properties/${id}`)}
                        placeholder="Søk i navn eller adresse..."
                    />
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <label htmlFor="type-filter" className="text-sm font-medium text-foreground whitespace-nowrap">
                        Eiendomstype:
                    </label>
                    <div className="relative">
                        <select
                            id="type-filter"
                            value={typeFilter}
                            onChange={(e) => { setTypeFilter(e.target.value); if (e.target.value !== "" && e.target.value !== "Formålsbygg") setUnitTypeFilter(""); }}
                            className="enterprise-input min-w-45 py-2.5"
                        >
                            <option value="">Alle</option>
                            {availableTypes.map((t) => (
                                <option key={t} value={t}>{t === "Barnevernsinstitusjon" ? "Formålsbygg" : t}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                    <label htmlFor="status-filter" className="text-sm font-medium text-foreground whitespace-nowrap">
                        Status:
                    </label>
                    <div className="relative">
                        <select
                            id="status-filter"
                            value={includeDiscontinued ? "all" : "active"}
                            onChange={(e) => setIncludeDiscontinued(e.target.value === "all")}
                            className="enterprise-input min-w-44 py-2.5"
                        >
                            <option value="active">Aktive</option>
                            <option value="all">Vis også avviklede</option>
                        </select>
                    </div>
                </div>
                {(typeFilter === "" || typeFilter === "Formålsbygg") && (
                <div className="flex items-center gap-2 shrink-0">
                    <label htmlFor="unit-type-filter" className="text-sm font-medium text-foreground whitespace-nowrap">
                        Institusjonsnivå:
                    </label>
                    <div className="relative">
                        <select
                            id="unit-type-filter"
                            value={unitTypeFilter}
                            onChange={(e) => setUnitTypeFilter(e.target.value)}
                            className="enterprise-input min-w-52 py-2.5"
                        >
                            <option value="">Alle nivåer</option>
                            <option value="Barnevernsinstitusjon">Hele institusjonen</option>
                            <option value="Avdeling">Avdeling (underenhet)</option>
                        </select>
                    </div>
                </div>
                )}
                {(typeFilter || unitTypeFilter || searchTerm || includeDiscontinued) && (
                    <button
                        type="button"
                        onClick={() => { setTypeFilter(""); setUnitTypeFilter(""); setSearchTerm(""); setIncludeDiscontinued(false); setFilterResetKey((k) => k + 1); }}
                        className="shrink-0 text-xs text-muted hover:text-foreground border border-border rounded px-2.5 py-2 transition-colors flex items-center gap-1"
                    >
                        <span>×</span> Nullstill filter
                    </button>
                )}
            </div>

            <div className="mt-8">
                <div className="flex justify-between items-end mb-4">
                    <h2 className="text-xl font-semibold text-foreground">
                        Eiendomsliste
                    </h2>
                </div>

                <PropertyList
                    properties={properties}
                    budgetByProperty={budgetByProperty}
                    sortBy={sortBy}
                    sortDir={sortDir}
                    onSort={handleSort}
                    avdelingerByParentErpId={avdelingerByParentErpId}
                />

                {hasMore && (
                    <div className="mt-8 flex justify-center">
                        <button
                            type="button"
                            onClick={handleLoadMore}
                            disabled={loadingMore}
                            className={`px-8 py-3 rounded-lg font-semibold transition-all flex items-center gap-2 ${loadingMore
                                ? "bg-surface/50 text-muted cursor-not-allowed"
                                : "bg-primary hover:opacity-90 text-primary-foreground shadow-lg shadow-primary/20 active:scale-95"
                                }`}
                        >
                            {loadingMore ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Laster flere...
                                </>
                            ) : (
                                "Last inn flere eiendommer"
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
