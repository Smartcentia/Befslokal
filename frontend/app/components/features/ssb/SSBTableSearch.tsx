"use client";

import React, { useState, useCallback, useMemo, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Search, Loader2, Table2, Library } from "lucide-react";
import { searchTables, type SSBTable, type SsbTableSearchOpts } from "@/lib/api/ssbApi";
import Accordion from "@/app/components/ui/Accordion";

const BROWSE_PAGE_SIZE = 100;

export type BufetatCatalogMode = "off" | "all" | string;

interface Props {
    onSelectTable: (table: SSBTable) => void;
    /** Fra URL: off = hele SSB, all = kuratert uten filter, ellers kategorinøkkel (utdanning, utenforskap, …) */
    initialBufetat?: BufetatCatalogMode;
}

function curatedSearchOpts(mode: BufetatCatalogMode): SsbTableSearchOpts | undefined {
    if (mode === "off") return undefined;
    if (mode === "all") return { catalog: "curated" };
    return { category: mode };
}

/** Primæremne fra SSB paths (første ledd i første sti). */
function getPrimarySubjectLabel(table: SSBTable): string {
    const seg = table.paths?.[0]?.[0];
    if (seg && typeof seg === "object" && seg.label) {
        return seg.label;
    }
    if (table.subjectCode) {
        return `Fagområde (${table.subjectCode})`;
    }
    return "Andre";
}

function groupTablesBySubject(tables: SSBTable[]): [string, SSBTable[]][] {
    const map = new Map<string, SSBTable[]>();
    for (const t of tables) {
        const key = getPrimarySubjectLabel(t);
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(t);
    }
    for (const [, list] of map) {
        list.sort((a, b) => a.label.localeCompare(b.label, "nb"));
    }
    return [...map.entries()].sort((a, b) =>
        a[0].localeCompare(b[0], "nb")
    );
}

function TablePickRow({
    table,
    onSelect,
}: {
    table: SSBTable;
    onSelect: (t: SSBTable) => void;
}) {
    return (
        <button
            type="button"
            onClick={() => onSelect(table)}
            className="w-full text-left rounded-xl border border-border bg-card hover:bg-muted/30 p-4 transition-colors"
        >
            <div className="flex items-start gap-3">
                <Table2 size={16} className="text-primary mt-0.5 shrink-0" />
                <div>
                    <div className="font-medium text-foreground text-sm">
                        {table.label}
                    </div>
                    <div className="text-xs text-muted mt-0.5">
                        Tabell {table.id}
                        {table.firstPeriod
                            ? ` · ${table.firstPeriod}–${table.lastPeriod ?? ""}`
                            : ""}
                    </div>
                </div>
            </div>
        </button>
    );
}

export default function SSBTableSearch({
    onSelectTable,
    initialBufetat = "off",
}: Props) {
    const router = useRouter();
    const pathname = usePathname();
    const [bufetatCatalog, setBufetatCatalog] = useState<BufetatCatalogMode>(initialBufetat);
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SSBTable[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searched, setSearched] = useState(false);

    const [browseTables, setBrowseTables] = useState<SSBTable[]>([]);
    const [browseLoading, setBrowseLoading] = useState(false);
    const [browseError, setBrowseError] = useState<string | null>(null);
    const [browsePage, setBrowsePage] = useState(1);
    const [browseTotalPages, setBrowseTotalPages] = useState(1);
    const [browseTotalElements, setBrowseTotalElements] = useState(0);
    const [browseLoaded, setBrowseLoaded] = useState(false);

    const groupedBrowse = useMemo(
        () => groupTablesBySubject(browseTables),
        [browseTables]
    );

    const applyBufetatMode = useCallback(
        (mode: BufetatCatalogMode) => {
            setBufetatCatalog(mode);
            setSearched(false);
            setResults([]);
            if (mode === "off") {
                router.replace(pathname, { scroll: false });
                return;
            }
            if (mode === "all") {
                router.replace(`${pathname}?catalog=curated`, { scroll: false });
                return;
            }
            router.replace(`${pathname}?category=${encodeURIComponent(mode)}`, { scroll: false });
        },
        [pathname, router]
    );

    const runSearch = useCallback(
        async (q: string | undefined) => {
            setLoading(true);
            setError(null);
            setSearched(true);
            try {
                const opts = curatedSearchOpts(bufetatCatalog);
                const res = await searchTables(q || undefined, 1, 100, "no", opts);
                setResults(res.tables ?? []);
            } catch {
                setError("Kunne ikke søke i SSB-tabeller.");
                setResults([]);
            } finally {
                setLoading(false);
            }
        },
        [bufetatCatalog]
    );

    const handleSearch = useCallback(() => {
        void runSearch(query || undefined);
    }, [query, runSearch]);

    useEffect(() => {
        if (bufetatCatalog === "off") return;
        void runSearch(undefined);
    }, [bufetatCatalog, runSearch]);

    const loadBrowsePage = useCallback(async (page: number) => {
        setBrowseLoading(true);
        setBrowseError(null);
        try {
            const res = await searchTables(undefined, page, BROWSE_PAGE_SIZE, "no");
            setBrowseTables(res.tables ?? []);
            setBrowsePage(res.page?.pageNumber ?? page);
            setBrowseTotalPages(Math.max(1, res.page?.totalPages ?? 1));
            setBrowseTotalElements(res.page?.totalElements ?? 0);
            setBrowseLoaded(true);
        } catch {
            setBrowseError("Kunne ikke hente tabelllisten fra SSB.");
            setBrowseTables([]);
        } finally {
            setBrowseLoading(false);
        }
    }, []);

    const handleBrowseAccordionOpen = useCallback(
        (open: boolean) => {
            if (open && !browseLoaded && !browseLoading) {
                void loadBrowsePage(1);
            }
        },
        [browseLoaded, browseLoading, loadBrowsePage]
    );

    const catalogHintMap: Record<string, string> = {
        melding: "Barnevernsmeldinger – tabeller om bekymringsmeldinger og undersøkelser.",
        tiltak: "Barnevernstiltak – fosterhjem, plassering, omsorgsovertak.",
        institusjon: "Barnevernsinstitusjoner – opphold og kapasitet.",
        familievern: "Familievern – mekling, terapi og rådgivning.",
        kostra: "KOSTRA – kommunale kostnader og ressursbruk.",
        utdanning: "Utdanning – skole, barnehage og kompetanse.",
        utenforskap: "Utenforskap / NEET – unge utenfor arbeid og opplæring.",
    };
    const catalogHint =
        bufetatCatalog === "off"
            ? "Søk i hele Statistikkbanken (alle tabeller)."
            : bufetatCatalog === "all"
              ? "Viser kun Bufetat/Bufdir-kuraterte tabeller. Begrens søk til denne listen."
              : catalogHintMap[bufetatCatalog] ?? `Kuratert filter: ${bufetatCatalog}. Kombiner med fritekst under.`;

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide w-full sm:w-auto sm:mr-2 py-1.5">
                        Utvalg
                    </span>
                    {(
                        [
                            ["off", "Hele SSB"],
                            ["all", "Kuratert: alle"],
                            ["melding", "Barnevernsmeldinger"],
                            ["tiltak", "Barnevernstiltak"],
                            ["institusjon", "Institusjoner"],
                            ["familievern", "Familievern"],
                            ["kostra", "KOSTRA"],
                            ["utdanning", "Utdanning"],
                            ["utenforskap", "Utenforskap / NEET"],
                        ] as [string, string][]
                    ).map(([mode, label]) => (
                        <button
                            key={mode}
                            type="button"
                            onClick={() => applyBufetatMode(mode)}
                            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                                bufetatCatalog === mode
                                    ? "border-primary bg-primary/15 text-primary"
                                    : "border-border bg-card text-muted-foreground hover:bg-muted/40"
                            }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
                <p className="text-xs text-muted leading-relaxed">{catalogHint}</p>

                <div className="flex gap-2">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                        placeholder="Søk etter SSB-tabell (f.eks. barnevern, KOSTRA)…"
                        className="flex-1 rounded-xl border border-input bg-background px-4 py-2 text-sm"
                    />
                    <button
                        type="button"
                        onClick={handleSearch}
                        disabled={loading}
                        className="flex items-center gap-2 px-5 py-2 rounded-xl bg-primary text-primary-foreground font-medium hover:opacity-90 disabled:opacity-50"
                    >
                        {loading ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <Search size={16} />
                        )}
                        Søk
                    </button>
                </div>

                {error && (
                    <p className="text-sm text-destructive">{error}</p>
                )}

                {searched && !loading && results.length === 0 && !error && (
                    <p className="text-sm text-muted">Ingen tabeller funnet.</p>
                )}

                <div className="space-y-2">
                    {results.map((table) => (
                        <TablePickRow
                            key={table.id}
                            table={table}
                            onSelect={onSelectTable}
                        />
                    ))}
                </div>
            </div>

            <Accordion
                title="Utforsk alle SSB-tabeller"
                icon={<Library size={22} />}
                onOpenChange={handleBrowseAccordionOpen}
            >
                {bufetatCatalog !== "off" ? (
                    <p className="text-sm text-muted mb-4">
                        Utvidet bla-i-liste er kun tilgjengelig når «Hele SSB» er valgt over.
                    </p>
                ) : (
                    <>
                        <p className="text-sm text-muted mb-4">
                            Statistikkbanken har tusenvis av tabeller. Her vises{" "}
                            {BROWSE_PAGE_SIZE} om gangen, gruppert etter primæremne på
                            gjeldende side. Bruk sidetall for å bla — eller søk over for
                            å filtrere på tittel.
                        </p>

                        {browseLoading && (
                            <div className="flex items-center gap-2 text-muted text-sm py-6">
                                <Loader2 size={18} className="animate-spin" />
                                Henter tabeller fra SSB…
                            </div>
                        )}

                        {browseError && (
                            <p className="text-sm text-destructive">{browseError}</p>
                        )}

                        {browseLoaded && !browseLoading && (
                            <>
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4 text-sm text-muted">
                            <span>
                                Totalt{" "}
                                <strong className="text-foreground">
                                    {browseTotalElements.toLocaleString("nb-NO")}
                                </strong>{" "}
                                tabeller i SSB · side{" "}
                                <strong className="text-foreground">
                                    {browsePage}
                                </strong>{" "}
                                av{" "}
                                <strong className="text-foreground">
                                    {browseTotalPages}
                                </strong>
                            </span>
                            <div className="flex gap-2">
                                <button
                                    type="button"
                                    disabled={browsePage <= 1 || browseLoading}
                                    onClick={() => loadBrowsePage(browsePage - 1)}
                                    className="px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-sm hover:bg-muted/40 disabled:opacity-40"
                                >
                                    Forrige
                                </button>
                                <button
                                    type="button"
                                    disabled={
                                        browsePage >= browseTotalPages ||
                                        browseLoading
                                    }
                                    onClick={() => loadBrowsePage(browsePage + 1)}
                                    className="px-3 py-1.5 rounded-lg border border-border bg-background text-foreground text-sm hover:bg-muted/40 disabled:opacity-40"
                                >
                                    Neste
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2 max-h-[min(70vh,720px)] overflow-y-auto pr-1">
                            {groupedBrowse.map(([subject, tables]) => (
                                <details
                                    key={subject}
                                    className="rounded-xl border border-border bg-muted/5 open:bg-muted/10"
                                >
                                    <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground flex items-center gap-2 [&::-webkit-details-marker]:hidden">
                                        <span className="text-muted select-none">▸</span>
                                        <span>
                                            {subject}
                                            <span className="text-muted font-normal ml-2">
                                                ({tables.length})
                                            </span>
                                        </span>
                                    </summary>
                                    <div className="px-3 pb-3 space-y-2 border-t border-border/60 pt-2">
                                        {tables.map((t) => (
                                            <TablePickRow
                                                key={t.id}
                                                table={t}
                                                onSelect={onSelectTable}
                                            />
                                        ))}
                                    </div>
                                </details>
                            ))}
                        </div>
                            </>
                        )}
                    </>
                )}
            </Accordion>
        </div>
    );
}
