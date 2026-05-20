"use client";

import React, { useState, useCallback, Suspense, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Database, Search, Link2, FileBarChart, Loader2, BookOpen } from "lucide-react";
import SSBTableSearch, {
    type BufetatCatalogMode,
} from "@/app/components/features/ssb/SSBTableSearch";
import SSBDataViewer from "@/app/components/features/ssb/SSBDataViewer";
import SSBCombinePanel from "@/app/components/features/ssb/SSBCombinePanel";
import SSBReportPanel from "@/app/components/features/ssb/SSBReportPanel";
import { getTableData, type SSBTable } from "@/lib/api/ssbApi";

type TabId = "search" | "data" | "combine" | "report";

type TidPreset = "all" | "tid_last10";

const CURATED_CATEGORY_KEYS = new Set([
    "utdanning",
    "utenforskap",
    "kostra",
    "melding",
    "tiltak",
    "institusjon",
    "familievern",
    "annet",
]);

function deriveBufetatFromSearchParams(sp: URLSearchParams): BufetatCatalogMode {
    const c = sp.get("category");
    if (c && CURATED_CATEGORY_KEYS.has(c)) return c;
    if (sp.get("catalog") === "curated") return "all";
    return "off";
}

function SSBPageInner() {
    const searchParams = useSearchParams();
    const catalogKey = searchParams.toString();
    const initialBufetat = useMemo(
        () => deriveBufetatFromSearchParams(searchParams),
        [searchParams]
    );
    const [activeTab, setActiveTab] = useState<TabId>("search");
    const [selectedTable, setSelectedTable] = useState<SSBTable | null>(null);
    const [tableData, setTableData] = useState<unknown>(null);
    const [dataLoading, setDataLoading] = useState(false);
    const [dataError, setDataError] = useState<string | null>(null);
    /** Tid=top(10) feiler på enkelte tabeller (påkrevde dimensjoner). Standard = fullt uttrekk. */
    const [tidPreset, setTidPreset] = useState<TidPreset>("all");

    const handleSelectTable = useCallback((table: SSBTable) => {
        setSelectedTable(table);
        setTableData(null);
        setDataError(null);
        setActiveTab("data");
    }, []);

    const handleFetchData = useCallback(async () => {
        if (!selectedTable) return;
        setDataLoading(true);
        setDataError(null);
        try {
            const valueCodes =
                tidPreset === "tid_last10" ? { Tid: "top(10)" } : undefined;
            const data = await getTableData(selectedTable.id, { valueCodes });
            setTableData(data);
        } catch (err) {
            console.error("Fetch data failed", err);
            setDataError(
                "Kunne ikke hente data fra SSB. Prøv «Alle perioder» hvis tabellen ikke har variabelen Tid, eller prøv igjen senere."
            );
        } finally {
            setDataLoading(false);
        }
    }, [selectedTable, tidPreset]);

    const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
        { id: "search", label: "Søk tabeller", icon: <Search size={18} /> },
        { id: "data", label: "Hent data", icon: <Database size={18} /> },
        { id: "combine", label: "Kombiner med BEFS", icon: <Link2 size={18} /> },
        { id: "report", label: "Analyser og rapporter", icon: <FileBarChart size={18} /> },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground">
            <div className="max-w-5xl mx-auto px-6 pt-32 pb-20">
                {/* Header */}
                <div className="flex items-center gap-4 mb-12">
                    <div className="w-16 h-16 bg-primary/20 rounded-2xl flex items-center justify-center text-primary border border-primary/20 shadow-lg shadow-primary/10">
                        <Database size={32} />
                    </div>
                    <div>
                        <h1 className="text-4xl font-bold text-foreground tracking-tight">
                            SSB Statistikk
                        </h1>
                        <p className="text-muted mt-2 text-lg">
                            Søk, hent og kombiner data fra Statistisk sentralbyrå med BEFS-data.
                            Lag analyser og rapporter.
                        </p>
                        <p className="mt-4">
                            <Link
                                href="/ssb/utdanning-metode"
                                className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                            >
                                <BookOpen size={18} />
                                Utdanning og gjennomføring: kilder, metode og tabellskisse
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-8 border-b border-border">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-4 py-3 font-medium border-b-2 -mb-px transition-colors ${
                                activeTab === tab.id
                                    ? "border-primary text-primary"
                                    : "border-transparent text-muted hover:text-foreground"
                            }`}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab content */}
                <div className="rounded-2xl border border-border bg-surface/50 p-6">
                    {activeTab === "search" && (
                        <SSBTableSearch
                            key={catalogKey}
                            initialBufetat={initialBufetat}
                            onSelectTable={handleSelectTable}
                        />
                    )}

                    {activeTab === "data" && (
                        <div className="space-y-6">
                            {selectedTable ? (
                                <>
                                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                                        <div>
                                            <h3 className="font-semibold text-foreground">
                                                {selectedTable.label}
                                            </h3>
                                            <p className="text-sm text-muted">
                                                Tabell {selectedTable.id}
                                            </p>
                                        </div>
                                        <div className="flex flex-col items-stretch sm:items-end gap-3">
                                            <label className="flex flex-col gap-1 text-sm text-muted">
                                                <span>Omfang</span>
                                                <select
                                                    value={tidPreset}
                                                    onChange={(e) =>
                                                        setTidPreset(e.target.value as TidPreset)
                                                    }
                                                    className="rounded-lg border border-border bg-background px-3 py-2 text-foreground text-sm min-w-[260px]"
                                                >
                                                    <option value="all">
                                                        Alle data (standard)
                                                    </option>
                                                    <option value="tid_last10">
                                                        Kun siste 10 tidsperioder (Tid=top(10)) – ikke alle
                                                        tabeller støtter dette
                                                    </option>
                                                </select>
                                            </label>
                                            <button
                                                type="button"
                                                onClick={handleFetchData}
                                                disabled={dataLoading}
                                                className="flex items-center justify-center gap-2 px-6 py-2 rounded-xl bg-primary text-primary-foreground font-medium hover:opacity-90 disabled:opacity-50"
                                            >
                                                {dataLoading ? (
                                                    <Loader2 className="animate-spin" size={18} />
                                                ) : (
                                                    "Hent data"
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                    {dataError && (
                                        <div className="p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger">
                                            {dataError}
                                        </div>
                                    )}
                                    {tableData && (
                                        <SSBDataViewer
                                            data={tableData}
                                            tableLabel={selectedTable.label}
                                            fetchMeta={{
                                                tidPreset,
                                                tableId: selectedTable.id,
                                            }}
                                        />
                                    )}
                                </>
                            ) : (
                                <p className="text-muted">
                                    Velg en tabell fra søket for å hente data.
                                </p>
                            )}
                        </div>
                    )}

                    {activeTab === "combine" && (
                        <SSBCombinePanel selectedTable={selectedTable} />
                    )}

                    {activeTab === "report" && (
                        <SSBReportPanel
                            data={tableData}
                            tableLabel={selectedTable?.label}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

export default function SSBPage() {
    return (
        <Suspense fallback={null}>
            <SSBPageInner />
        </Suspense>
    );
}
