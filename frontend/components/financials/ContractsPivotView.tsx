"use client";

import { useState, useEffect, useMemo } from "react";
import { getContractsPivotRaw, ContractsPivotRawRecord } from "@/lib/api/propertiesApi";
import { RotateCcw } from "lucide-react";

type PivotDimension = "region" | "utleier" | "eiendom";

const DIM_LABELS: Record<PivotDimension, string> = {
    region: "Region",
    utleier: "Utleier",
    eiendom: "Eiendom",
};

function buildPivot(
    records: ContractsPivotRawRecord[],
    rowDim: PivotDimension,
    colDim: PivotDimension
): {
    rows: string[];
    cols: string[];
    data: Record<string, Record<string, number>>;
    rowTotals: Record<string, number>;
    colTotals: Record<string, number>;
    grandTotal: number;
} {
    const rows = new Set<string>();
    const cols = new Set<string>();
    const data: Record<string, Record<string, number>> = {};
    const rowTotals: Record<string, number> = {};
    const colTotals: Record<string, number> = {};
    let grandTotal = 0;

    for (const r of records) {
        const rowVal = r[rowDim] || "(ukjent)";
        const colVal = r[colDim] || "(ukjent)";
        const amt = r.amount_per_year || 0;

        rows.add(rowVal);
        cols.add(colVal);
        if (!data[rowVal]) data[rowVal] = {};
        data[rowVal][colVal] = (data[rowVal][colVal] ?? 0) + amt;
        rowTotals[rowVal] = (rowTotals[rowVal] ?? 0) + amt;
        colTotals[colVal] = (colTotals[colVal] ?? 0) + amt;
        grandTotal += amt;
    }

    const rowOrder = [...rows].sort((a, b) => {
        const regionOrder = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir", "Øvrig"];
        if (rowDim === "region" && regionOrder.includes(a) && regionOrder.includes(b)) {
            return regionOrder.indexOf(a) - regionOrder.indexOf(b);
        }
        return a.localeCompare(b);
    });
    const colOrder = [...cols].sort((a, b) => a.localeCompare(b));

    return { rows: rowOrder, cols: colOrder, data, rowTotals, colTotals, grandTotal };
}

export default function ContractsPivotView() {
    const [records, setRecords] = useState<ContractsPivotRawRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [rowDim, setRowDim] = useState<PivotDimension>("region");
    const [colDim, setColDim] = useState<PivotDimension>("utleier");

    useEffect(() => {
        setLoading(true);
        getContractsPivotRaw()
            .then((res) => {
                if (res?.records) setRecords(res.records);
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, []);

    const pivot = useMemo(() => {
        if (!records.length) return null;
        return buildPivot(records, rowDim, colDim);
    }, [records, rowDim, colDim]);

    const otherDim: PivotDimension = useMemo(() => {
        const used = new Set([rowDim, colDim]);
        return (["region", "utleier", "eiendom"] as PivotDimension[]).find((d) => !used.has(d)) ?? "region";
    }, [rowDim, colDim]);

    const resetToDefault = () => {
        setRowDim("region");
        setColDim("utleier");
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
                <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-muted text-sm">Henter kontraktsdata...</p>
            </div>
        );
    }

    if (!records.length) {
        return <p className="text-muted py-8 text-center">Ingen aktive kontrakter funnet.</p>;
    }

    return (
        <div className="space-y-4">
            {/* Pivot-kontroller */}
            <div className="flex flex-wrap items-center gap-4 p-4 rounded-xl border border-border bg-muted/20">
                <span className="text-sm font-medium text-muted-foreground">Pivot:</span>
                <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">Rader</label>
                    <select
                        value={rowDim}
                        onChange={(e) => {
                            const v = e.target.value as PivotDimension;
                            setRowDim(v);
                            if (v === colDim) setColDim(otherDim);
                        }}
                        className="px-3 py-1.5 rounded-md border border-border bg-background text-foreground text-sm font-medium"
                    >
                        <option value="region">Region</option>
                        <option value="utleier">Utleier</option>
                        <option value="eiendom">Eiendom</option>
                    </select>
                </div>
                <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">Kolonner</label>
                    <select
                        value={colDim}
                        onChange={(e) => {
                            const v = e.target.value as PivotDimension;
                            setColDim(v);
                            if (v === rowDim) setRowDim(otherDim);
                        }}
                        className="px-3 py-1.5 rounded-md border border-border bg-background text-foreground text-sm font-medium"
                    >
                        <option value="region">Region</option>
                        <option value="utleier">Utleier</option>
                        <option value="eiendom">Eiendom</option>
                    </select>
                </div>
                <button
                    type="button"
                    onClick={resetToDefault}
                    className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    title="Tilbakestill til Region × Utleier"
                >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Standard
                </button>
                <span className="text-xs text-muted-foreground ml-auto">
                    {DIM_LABELS[rowDim]} × {DIM_LABELS[colDim]} · Sum årsleie
                </span>
            </div>

            {/* Dynamisk pivot-tabell */}
            {pivot && (
                <div className="overflow-x-auto rounded-xl border border-border bg-background">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border bg-muted/30">
                                <th className="px-4 py-3 text-left font-bold text-muted-foreground min-w-[140px]">
                                    {DIM_LABELS[rowDim]}
                                </th>
                                {pivot.cols.map((c) => (
                                    <th
                                        key={c}
                                        className="px-2 py-3 text-right font-bold text-muted-foreground min-w-24"
                                    >
                                        {c}
                                    </th>
                                ))}
                                <th className="px-4 py-3 text-right font-bold text-muted-foreground">Sum</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pivot.rows.map((row) => (
                                <tr key={row} className="border-b border-border/50">
                                    <td className="px-4 py-2 font-medium">{row}</td>
                                    {pivot.cols.map((col) => (
                                        <td
                                            key={col}
                                            className="px-2 py-2 text-right font-mono text-muted-foreground"
                                        >
                                            {pivot.data[row]?.[col]
                                                ? pivot.data[row][col].toLocaleString("no-NO")
                                                : "—"}
                                        </td>
                                    ))}
                                    <td className="px-4 py-2 text-right font-mono font-medium">
                                        {(pivot.rowTotals[row] ?? 0).toLocaleString("no-NO")}
                                    </td>
                                </tr>
                            ))}
                            <tr className="border-t-2 border-border bg-muted/20 font-semibold">
                                <td className="px-4 py-3">Sum</td>
                                {pivot.cols.map((col) => (
                                    <td key={col} className="px-2 py-3 text-right font-mono">
                                        {(pivot.colTotals[col] ?? 0).toLocaleString("no-NO")}
                                    </td>
                                ))}
                                <td className="px-4 py-3 text-right font-mono">
                                    {pivot.grandTotal.toLocaleString("no-NO")}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
