"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Download, ChevronDown, ChevronRight, Table2, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
    flattenJsonStat2,
    isJsonStatLike,
    rowsToCsv,
    summarizeNumericValues,
    resolveTimeDimensionKey,
    computeRowAnalytics,
    type FlattenedJsonStat,
} from "@/lib/ssb/jsonStatParse";
import SSBJsonStatChart from "./SSBJsonStatChart";

export interface SSBDataViewerFetchMeta {
    tidPreset: "all" | "tid_last10";
    tableId: string;
}

interface Props {
    data: unknown;
    tableLabel?: string;
    /** Kontekst for antakelsesboks (valg ved henting) */
    fetchMeta?: SSBDataViewerFetchMeta;
}

function formatCell(v: string | number | null): string {
    if (v === null || v === undefined) return "–";
    if (typeof v === "number") {
        if (Number.isNaN(v)) return "–";
        return v.toLocaleString("nb-NO", { maximumFractionDigits: 4 });
    }
    return String(v);
}

function formatPct(v: number | null): string {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    return `${v.toLocaleString("nb-NO", { maximumFractionDigits: 2 })} %`;
}

function formatIndex(v: number | null): string {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    return v.toLocaleString("nb-NO", { maximumFractionDigits: 2 });
}

export default function SSBDataViewer({ data, tableLabel, fetchMeta }: Props) {
    const [showRaw, setShowRaw] = useState(false);
    const [showAllRows, setShowAllRows] = useState(false);
    const [analyticsEnabled, setAnalyticsEnabled] = useState(true);

    const parsed: FlattenedJsonStat | null = useMemo(() => {
        if (!data || !isJsonStatLike(data)) return null;
        try {
            return flattenJsonStat2(data, { maxRows: 12000 });
        } catch {
            return null;
        }
    }, [data]);

    const datasetMeta = useMemo(() => {
        if (!data || typeof data !== "object") return { updated: null as string | null, source: null as string | null };
        const o = data as Record<string, unknown>;
        return {
            updated: typeof o.updated === "string" ? o.updated : null,
            source: typeof o.source === "string" ? o.source : null,
        };
    }, [data]);

    const datasetNotes = useMemo(() => {
        if (!data || typeof data !== "object") return [];
        const n = (data as { note?: unknown }).note;
        if (!Array.isArray(n)) return [];
        return n.filter((x): x is string => typeof x === "string" && x.length > 0);
    }, [data]);

    const timeKey = useMemo(() => (parsed ? resolveTimeDimensionKey(parsed) : null), [parsed]);

    const rowAnalytics = useMemo(() => {
        if (!parsed || !timeKey) return null;
        return computeRowAnalytics(parsed.rows, parsed.dimensionKeys, parsed.valueKey, timeKey);
    }, [parsed, timeKey]);

    const previewLimit = 400;
    const displayRows = useMemo(() => {
        if (!parsed) return [];
        if (showAllRows) return parsed.rows;
        return parsed.rows.slice(0, previewLimit);
    }, [parsed, showAllRows]);

    const displayAnalytics = useMemo(() => {
        if (!rowAnalytics) return null;
        if (showAllRows) return rowAnalytics;
        return rowAnalytics.slice(0, previewLimit);
    }, [rowAnalytics, showAllRows, previewLimit]);

    const baseColumns = useMemo(() => {
        if (!parsed) return [];
        return [...parsed.dimensionKeys, parsed.valueKey];
    }, [parsed]);

    const analyseColumns = useMemo(() => {
        if (!analyticsEnabled || !timeKey) return baseColumns;
        return [...baseColumns, "Δ % (siste periode)", "Indeks (basis første)", "Avvik (IQR)"];
    }, [baseColumns, analyticsEnabled, timeKey]);

    const stats = useMemo(() => {
        if (!parsed) return null;
        return summarizeNumericValues(parsed.rows, parsed.valueKey);
    }, [parsed]);

    const downloadCsv = useCallback(() => {
        if (!parsed) return;
        const cols = baseColumns;
        const csv = rowsToCsv(parsed.rows, cols);
        const blob = new Blob(["\ufeff", csv], {
            type: "text/csv;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ssb-data-${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }, [parsed, baseColumns]);

    const downloadAnalyseCsv = useCallback(() => {
        if (!parsed || !rowAnalytics || !timeKey) return;
        const extra = ["delta_pct", "indeks_100", "avvik_iqr"];
        const cols = [...baseColumns, ...extra];
        const rows = parsed.rows.map((r, i) => {
            const a = rowAnalytics[i];
            return {
                ...r,
                delta_pct: a?.yoyPct ?? "",
                indeks_100: a?.index100 ?? "",
                avvik_iqr: a?.outlier ?? "",
            };
        });
        const csv = rowsToCsv(rows, cols);
        const blob = new Blob(["\ufeff", csv], {
            type: "text/csv;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `ssb-analyse-${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }, [parsed, rowAnalytics, timeKey, baseColumns]);

    if (!data) return null;

    if (!parsed) {
        return (
            <div className="space-y-4">
                {tableLabel && (
                    <h3 className="font-semibold text-foreground">{tableLabel}</h3>
                )}
                <p className="text-sm text-muted-foreground">
                    Dataene er ikke på json-stat2-format. Viser rå innhold (ofte CSV/HTML
                    eller annet) – kontakt admin hvis du forventet tabell.
                </p>
                <div className="rounded-xl border border-border bg-muted/20 p-4 overflow-auto max-h-96">
                    <pre className="text-xs text-muted-foreground whitespace-pre-wrap break-all">
                        {typeof data === "string"
                            ? data
                            : JSON.stringify(data, null, 2)}
                    </pre>
                </div>
            </div>
        );
    }

    const title = parsed.datasetLabel || tableLabel;

    return (
        <div className="space-y-6">
            {fetchMeta && (
                <div className="rounded-lg border border-primary/25 bg-primary/5 px-4 py-3 text-sm">
                    <div className="flex items-start gap-2">
                        <Info size={18} className="text-primary shrink-0 mt-0.5" />
                        <div className="space-y-2 text-foreground">
                            <div className="font-medium">Antakelser ved denne visningen</div>
                            <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                                <li>
                                    Kilde: Statistisk sentralbyrå (PxWebApi), format json-stat2.
                                    {datasetMeta.source && ` Oppgitt kilde: ${datasetMeta.source}.`}
                                </li>
                                <li>
                                    Tabell-ID: <span className="font-mono">{fetchMeta.tableId}</span>
                                    .
                                </li>
                                <li>
                                    Hentet omfang:{" "}
                                    {fetchMeta.tidPreset === "tid_last10"
                                        ? "API-filter Tid=top(10) (siste 10 tidsperioder – feiler på noen tabeller)."
                                        : "Alle rader/perioder som API returnerte (ingen Tid-filter)."}
                                </li>
                                {datasetMeta.updated && (
                                    <li>
                                        SSB oppdatert:{" "}
                                        {new Date(datasetMeta.updated).toLocaleString("nb-NO")}
                                    </li>
                                )}
                                <li>
                                    Analysekolonner forutsetter en tidsdimensjon (typisk «Tid» eller
                                    «år»). Gruppe = samme kombinasjon av øvrige dimensjoner. Δ % =
                                    endring mot forrige sorterte periode i gruppen. Indeks = 100 i
                                    første periode med tall i gruppen. Avvik = Tukey IQR (krever min.
                                    4 tall i gruppen).
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {datasetNotes.length > 0 && (
                <div className="rounded-lg border border-border bg-muted/20 px-4 py-3 text-sm text-foreground space-y-2">
                    <div className="font-medium text-xs uppercase tracking-wide text-muted-foreground">
                        Fotnoter fra SSB
                    </div>
                    <ul className="list-disc pl-4 space-y-1">
                        {datasetNotes.map((note, i) => (
                            <li key={i} className="text-muted-foreground">
                                {note}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {title && (
                <div>
                    <h3 className="font-semibold text-foreground flex items-center gap-2">
                        <Table2 size={18} className="text-primary" />
                        {title}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        {parsed.dimensionKeys.length} dimensjon
                        {parsed.dimensionKeys.length !== 1 ? "er" : ""}:{" "}
                        {parsed.dimensions.map((d) => d.label).join(" · ")}
                        {timeKey && (
                            <>
                                {" "}
                                · Tidsnøkkel for analyse: <span className="font-mono">{timeKey}</span>
                            </>
                        )}
                    </p>
                </div>
            )}

            {parsed.sizeMismatchWarning && (
                <div className="text-sm rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-100 px-3 py-2">
                    {parsed.sizeMismatchWarning}
                </div>
            )}

            {stats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    <div className="rounded-xl border border-border bg-surface/80 p-3">
                        <div className="text-muted-foreground text-xs">Datapunkter</div>
                        <div className="font-semibold tabular-nums">{stats.count}</div>
                    </div>
                    <div className="rounded-xl border border-border bg-surface/80 p-3">
                        <div className="text-muted-foreground text-xs">Min</div>
                        <div className="font-semibold tabular-nums">
                            {formatCell(stats.min)}
                        </div>
                    </div>
                    <div className="rounded-xl border border-border bg-surface/80 p-3">
                        <div className="text-muted-foreground text-xs">Maks</div>
                        <div className="font-semibold tabular-nums">
                            {formatCell(stats.max)}
                        </div>
                    </div>
                    <div className="rounded-xl border border-border bg-surface/80 p-3">
                        <div className="text-muted-foreground text-xs">Sum</div>
                        <div className="font-semibold tabular-nums">
                            {formatCell(stats.sum)}
                        </div>
                    </div>
                </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                        type="checkbox"
                        checked={analyticsEnabled && !!timeKey}
                        disabled={!timeKey}
                        onChange={(e) => setAnalyticsEnabled(e.target.checked)}
                        className="rounded border-border"
                    />
                    <span className={!timeKey ? "text-muted-foreground" : ""}>
                        Vis Δ %, indeks og avvik (krever tidsdimensjon)
                    </span>
                </label>
                {!timeKey && (
                    <span className="text-xs text-muted-foreground">
                        Ingen tidsdimensjon funnet – analysekolonner er deaktivert.
                    </span>
                )}
            </div>

            <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground">
                    Diagram (linje eller stolpe)
                </h4>
                <p className="text-xs text-muted-foreground">
                    Velg akser og filtre for å forklare ett utsnitt om gangen — nyttig når tabellen har
                    mange dimensjoner (f.eks. region, alder, NEET-status).
                </p>
                <SSBJsonStatChart
                    rows={parsed.rows}
                    dimensionKeys={parsed.dimensionKeys}
                    valueKey={parsed.valueKey}
                    role={parsed.role}
                />
            </div>

            <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="outline" size="sm" onClick={downloadCsv}>
                    <Download size={16} className="mr-2" />
                    Last ned CSV (data)
                </Button>
                {rowAnalytics && timeKey && (
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={downloadAnalyseCsv}
                    >
                        <Download size={16} className="mr-2" />
                        Last ned CSV (med analysekolonner)
                    </Button>
                )}
                {parsed.rows.length > previewLimit && (
                    <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowAllRows((v) => !v)}
                    >
                        {showAllRows
                            ? `Vis kun første ${previewLimit} rader`
                            : `Vis alle ${parsed.rows.length} rader (kan være tungt)`}
                    </Button>
                )}
            </div>

            <div className="rounded-xl border border-border overflow-hidden">
                <div className="max-h-[min(70vh,560px)] overflow-auto">
                    <Table>
                        <TableHeader className="sticky top-0 z-10 bg-surface shadow-sm">
                            <TableRow>
                                {analyseColumns.map((col) => (
                                    <TableHead
                                        key={col}
                                        className="whitespace-nowrap bg-surface text-xs sm:text-sm"
                                    >
                                        {col}
                                    </TableHead>
                                ))}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {displayRows.map((row, i) => {
                                const a = displayAnalytics?.[i];
                                const out = a?.outlier;
                                return (
                                    <TableRow
                                        key={i}
                                        className={cn(
                                            out === "lav" &&
                                                "bg-sky-500/10 border-l-4 border-l-sky-600",
                                            out === "høy" &&
                                                "bg-amber-500/10 border-l-4 border-l-amber-600"
                                        )}
                                    >
                                        {baseColumns.map((col) => (
                                            <TableCell
                                                key={col}
                                                className="whitespace-nowrap max-w-[min(28vw,240px)] truncate text-xs sm:text-sm"
                                                title={formatCell(row[col] ?? null)}
                                            >
                                                {formatCell(row[col] ?? null)}
                                            </TableCell>
                                        ))}
                                        {analyticsEnabled && timeKey && (
                                            <>
                                                <TableCell className="tabular-nums text-xs sm:text-sm">
                                                    {formatPct(a?.yoyPct ?? null)}
                                                </TableCell>
                                                <TableCell className="tabular-nums text-xs sm:text-sm">
                                                    {formatIndex(a?.index100 ?? null)}
                                                </TableCell>
                                                <TableCell className="text-xs sm:text-sm">
                                                    {a?.outlier === "lav" && (
                                                        <span className="text-sky-700 dark:text-sky-300">
                                                            Lav
                                                        </span>
                                                    )}
                                                    {a?.outlier === "høy" && (
                                                        <span className="text-amber-800 dark:text-amber-200">
                                                            Høy
                                                        </span>
                                                    )}
                                                    {!a?.outlier && "–"}
                                                </TableCell>
                                            </>
                                        )}
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </div>
            </div>

            {analyticsEnabled && timeKey && displayRows.length > 0 ? (
                <p className="text-xs text-muted-foreground">
                    Radmarkering: blå kant = verdi under nedre IQR-grense, oransje = over øvre.
                    Tom Δ % der det ikke finnes forrige periode i gruppen.
                </p>
            ) : null}

            <p className="text-xs text-muted-foreground">
                {parsed.truncated && (
                    <>
                        Visningen er begrenset til {parsed.maxRows} rader av hensyn til
                        ytelse. Last ned CSV for å få alle flatede rader som ble generert.{" "}
                    </>
                )}
                {!parsed.truncated && parsed.rows.length > previewLimit && !showAllRows && (
                    <>
                        Tabellen viser de første {previewLimit} radene. Bruk knappen over for
                        full liste.{" "}
                    </>
                )}
                Tall er formatert med norsk locale (mellomrom som tusenskille der det passer).
            </p>

            <div className="border border-border rounded-xl overflow-hidden">
                <button
                    type="button"
                    onClick={() => setShowRaw((s) => !s)}
                    className="flex items-center gap-2 w-full px-4 py-3 text-left text-sm font-medium bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                    {showRaw ? (
                        <ChevronDown size={18} />
                    ) : (
                        <ChevronRight size={18} />
                    )}
                    Teknisk JSON (feilsøking)
                </button>
                {showRaw && (
                    <div className="p-4 max-h-64 overflow-auto border-t border-border bg-muted/10">
                        <pre className="text-xs text-muted-foreground whitespace-pre-wrap break-all">
                            {JSON.stringify(data, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </div>
    );
}
