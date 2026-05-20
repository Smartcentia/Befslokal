"use client";

import React, { useMemo, useState, useEffect } from "react";
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import type { JsonStatRole } from "@/lib/ssb/jsonStatParse";

const COLORS = [
    "#2563eb",
    "#16a34a",
    "#dc2626",
    "#9333ea",
    "#ca8a04",
    "#0891b2",
    "#db2777",
    "#4f46e5",
];

const AUTO = "__auto__";
const MAX_SERIES = 8;
const MAX_X_POINTS = 48;

interface Props {
    rows: Array<Record<string, string | number | null>>;
    dimensionKeys: string[];
    valueKey: string;
    role?: JsonStatRole;
}

function pickTimeKey(keys: string[]): string | null {
    const lower = (k: string) => k.toLowerCase();
    const exact = keys.find((k) => lower(k) === "tid" || lower(k) === "time");
    if (exact) return exact;
    return (
        keys.find((k) => /tid|år|periode|uke|måned|kvartal|month|year|quarter/i.test(k)) ??
        null
    );
}

function looksLikeTimeKey(key: string): boolean {
    return pickTimeKey([key]) !== null || /tid|år|periode|uke|måned|kvartal/i.test(key);
}

/** Velg én dimensjon som seriekode (ikke tid, ikke verdi) med begrenset kardinalitet */
function pickSeriesKey(
    keys: string[],
    timeKey: string,
    valueKey: string,
    rows: Array<Record<string, string | number | null>>
): string | null {
    const candidates = keys.filter((k) => k !== timeKey && k !== valueKey);
    for (const c of candidates) {
        const uniq = new Set(rows.map((r) => String(r[c] ?? ""))).size;
        if (uniq >= 2 && uniq <= 12) return c;
    }
    for (const c of candidates) {
        const uniq = new Set(rows.map((r) => String(r[c] ?? ""))).size;
        if (uniq >= 2 && uniq <= 24) return c;
    }
    return null;
}

function uniqSorted(rows: Array<Record<string, string | number | null>>, key: string): string[] {
    return [...new Set(rows.map((r) => String(r[key] ?? "")))].filter(Boolean).sort((a, b) =>
        a.localeCompare(b, "nb")
    );
}

/** Velg standard «skive» per øvrig dimensjon (første sorterte verdi) for å redusere støy */
function defaultSliceFilters(
    rows: Array<Record<string, string | number | null>>,
    dimensionKeys: string[],
    valueKey: string,
    xKey: string,
    seriesKey: string
): Record<string, string> {
    const out: Record<string, string> = {};
    for (const d of dimensionKeys) {
        if (d === valueKey || d === xKey || d === seriesKey) continue;
        const vals = uniqSorted(rows, d);
        if (vals.length > 1 && vals[0] !== undefined) out[d] = vals[0];
    }
    return out;
}

function applySlice(
    rows: Array<Record<string, string | number | null>>,
    slice: Record<string, string>
): Array<Record<string, string | number | null>> {
    return rows.filter((r) =>
        Object.entries(slice).every(([k, v]) => String(r[k] ?? "") === v)
    );
}

export default function SSBJsonStatChart({
    rows,
    dimensionKeys,
    valueKey,
    role,
}: Props) {
    const autoTimeKey = useMemo(() => {
        const fromRole =
            role?.time?.[0] && dimensionKeys.includes(role.time[0]) ? role.time[0] : null;
        return fromRole || pickTimeKey(dimensionKeys);
    }, [dimensionKeys, role]);

    const [xAxisChoice, setXAxisChoice] = useState<string>(AUTO);
    const [seriesChoice, setSeriesChoice] = useState<string>(AUTO);
    const [chartKind, setChartKind] = useState<"line" | "bar">("line");
    const [sliceFilters, setSliceFilters] = useState<Record<string, string>>({});

    const effectiveXKey =
        xAxisChoice === AUTO ? autoTimeKey : xAxisChoice === "" ? null : xAxisChoice;

    const autoSeriesKey = useMemo(() => {
        if (!effectiveXKey) return null;
        const fromRole =
            role?.metric?.[0] && dimensionKeys.includes(role.metric[0])
                ? role.metric[0]
                : null;
        if (fromRole && fromRole !== effectiveXKey && fromRole !== valueKey) return fromRole;
        return pickSeriesKey(dimensionKeys, effectiveXKey, valueKey, rows);
    }, [effectiveXKey, dimensionKeys, role, rows, valueKey]);

    const effectiveSeriesKey =
        seriesChoice === AUTO
            ? autoSeriesKey
            : seriesChoice === ""
              ? null
              : seriesChoice;

    const candidateXKeys = useMemo(() => {
        return dimensionKeys.filter((k) => k !== valueKey);
    }, [dimensionKeys, valueKey]);

    const candidateSeriesKeys = useMemo(() => {
        if (!effectiveXKey) return dimensionKeys.filter((k) => k !== valueKey);
        return dimensionKeys.filter((k) => k !== valueKey && k !== effectiveXKey);
    }, [dimensionKeys, valueKey, effectiveXKey]);

    const sliceDimensions = useMemo(() => {
        if (!effectiveXKey || !effectiveSeriesKey) return [];
        return dimensionKeys.filter(
            (k) => k !== valueKey && k !== effectiveXKey && k !== effectiveSeriesKey
        );
    }, [dimensionKeys, effectiveXKey, effectiveSeriesKey, valueKey]);

    useEffect(() => {
        if (!effectiveXKey || !effectiveSeriesKey || rows.length === 0) return;
        setSliceFilters((prev) => {
            const next = defaultSliceFilters(rows, dimensionKeys, valueKey, effectiveXKey, effectiveSeriesKey);
            const merged = { ...next };
            for (const k of Object.keys(next)) {
                if (prev[k] !== undefined && uniqSorted(rows, k).includes(prev[k])) {
                    merged[k] = prev[k];
                }
            }
            return merged;
        });
    }, [effectiveXKey, effectiveSeriesKey, rows, dimensionKeys, valueKey]);

    const filteredRows = useMemo(() => {
        return applySlice(rows, sliceFilters);
    }, [rows, sliceFilters]);

    const chartModel = useMemo(() => {
        if (filteredRows.length < 1 || !effectiveXKey || !effectiveSeriesKey) return null;

        const xKeys = [...new Set(filteredRows.map((r) => String(r[effectiveXKey] ?? "")))]
            .filter(Boolean)
            .sort((a, b) => {
                if (looksLikeTimeKey(effectiveXKey)) {
                    return a.localeCompare(b, "nb", { numeric: true });
                }
                return a.localeCompare(b, "nb");
            })
            .slice(0, MAX_X_POINTS);

        const seriesNames = [
            ...new Set(filteredRows.map((r) => String(r[effectiveSeriesKey] ?? ""))),
        ]
            .filter(Boolean)
            .sort((a, b) => a.localeCompare(b, "nb"))
            .slice(0, MAX_SERIES);

        if (seriesNames.length < 1 || xKeys.length < 1) return null;

        const byX: Record<string, Record<string, number>> = {};
        for (const x of xKeys) {
            byX[x] = {};
            for (const s of seriesNames) {
                byX[x][s] = Number.NaN;
            }
        }

        for (const r of filteredRows) {
            const x = String(r[effectiveXKey] ?? "");
            const s = String(r[effectiveSeriesKey] ?? "");
            const v = r[valueKey];
            if (!xKeys.includes(x) || !seriesNames.includes(s)) continue;
            if (typeof v !== "number" || Number.isNaN(v)) continue;
            if (!byX[x]) byX[x] = {};
            byX[x][s] = v;
        }

        const points = xKeys.map((x) => {
            const row: Record<string, string | number> = { [effectiveXKey]: x };
            for (const s of seriesNames) {
                const n = byX[x]?.[s];
                row[s] = typeof n === "number" && !Number.isNaN(n) ? n : 0;
            }
            return row;
        });

        const isTimeX = looksLikeTimeKey(effectiveXKey);

        return {
            points,
            seriesNames,
            xLabel: effectiveXKey,
            seriesLabel: effectiveSeriesKey,
            isTimeX,
        };
    }, [filteredRows, effectiveXKey, effectiveSeriesKey, valueKey]);

    if (rows.length < 1) {
        return (
            <p className="text-sm text-muted-foreground border border-dashed border-border rounded-lg p-4">
                Ingen rader å visualisere.
            </p>
        );
    }

    if (!autoTimeKey && xAxisChoice === AUTO) {
        return (
            <p className="text-sm text-muted-foreground border border-dashed border-border rounded-lg p-4">
                Ingen åpenbar tidsdimensjon funnet. Velg <strong>X-akse</strong> manuelt under for å
                bygge et kategoridiagram (stolper).
            </p>
        );
    }

    if (!chartModel) {
        return (
            <div className="space-y-3">
                <ChartControls
                    candidateXKeys={candidateXKeys}
                    candidateSeriesKeys={candidateSeriesKeys}
                    xAxisChoice={xAxisChoice}
                    setXAxisChoice={setXAxisChoice}
                    seriesChoice={seriesChoice}
                    setSeriesChoice={setSeriesChoice}
                    chartKind={chartKind}
                    setChartKind={setChartKind}
                    sliceDimensions={sliceDimensions}
                    sliceFilters={sliceFilters}
                    setSliceFilters={setSliceFilters}
                    rows={rows}
                />
                <p className="text-sm text-muted-foreground border border-dashed border-border rounded-lg p-4">
                    Kombinasjonen av akser og filtre ga ingen gyldig serie. Juster valgene over eller
                    bruk tabellen under.
                </p>
            </div>
        );
    }

    const { points, seriesNames, xLabel, seriesLabel, isTimeX } = chartModel;
    const useBar = chartKind === "bar";
    const xAxisAngle = points.length > 10 ? -35 : 0;

    return (
        <div className="space-y-4">
            <ChartControls
                candidateXKeys={candidateXKeys}
                candidateSeriesKeys={candidateSeriesKeys}
                xAxisChoice={xAxisChoice}
                setXAxisChoice={setXAxisChoice}
                seriesChoice={seriesChoice}
                setSeriesChoice={setSeriesChoice}
                chartKind={chartKind}
                setChartKind={setChartKind}
                sliceDimensions={sliceDimensions}
                sliceFilters={sliceFilters}
                setSliceFilters={setSliceFilters}
                rows={rows}
            />

            <p className="text-xs text-muted-foreground">
                X-akse: <span className="font-medium text-foreground">{xLabel}</span> · Serier:{" "}
                <span className="font-medium text-foreground">{seriesLabel}</span> (maks. {MAX_SERIES}
                ) · {filteredRows.length} rader etter filter
                {!isTimeX && (
                    <span className="text-amber-700 dark:text-amber-300">
                        {" "}
                        · Kategorisk X-akse — stolpediagram anbefales ofte
                    </span>
                )}
            </p>

            <div className="h-80 w-full min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                    {useBar ? (
                        <BarChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                            <XAxis
                                dataKey={xLabel}
                                tick={{ fontSize: 10 }}
                                angle={xAxisAngle}
                                textAnchor={xAxisAngle ? "end" : "middle"}
                                height={xAxisAngle ? 56 : 32}
                                className="text-muted-foreground"
                            />
                            <YAxis
                                tick={{ fontSize: 11 }}
                                className="text-muted-foreground"
                                tickFormatter={(v) =>
                                    typeof v === "number"
                                        ? v.toLocaleString("nb-NO", { maximumFractionDigits: 0 })
                                        : String(v)
                                }
                            />
                            <Tooltip
                                formatter={(v: number) =>
                                    v !== undefined && v !== null
                                        ? v.toLocaleString("nb-NO", { maximumFractionDigits: 2 })
                                        : ""
                                }
                                contentStyle={{
                                    background: "var(--surface)",
                                    border: "1px solid var(--border)",
                                    borderRadius: 8,
                                }}
                            />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            {seriesNames.map((name, i) => (
                                <Bar
                                    key={name}
                                    dataKey={name}
                                    fill={COLORS[i % COLORS.length]}
                                    name={name.length > 36 ? `${name.slice(0, 33)}…` : name}
                                    radius={[4, 4, 0, 0]}
                                />
                            ))}
                        </BarChart>
                    ) : (
                        <LineChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                            <XAxis
                                dataKey={xLabel}
                                tick={{ fontSize: 11 }}
                                className="text-muted-foreground"
                            />
                            <YAxis
                                tick={{ fontSize: 11 }}
                                className="text-muted-foreground"
                                tickFormatter={(v) =>
                                    typeof v === "number"
                                        ? v.toLocaleString("nb-NO", { maximumFractionDigits: 0 })
                                        : String(v)
                                }
                            />
                            <Tooltip
                                formatter={(v: number) =>
                                    v !== undefined && v !== null
                                        ? v.toLocaleString("nb-NO", { maximumFractionDigits: 2 })
                                        : ""
                                }
                                labelFormatter={(l) => String(l)}
                                contentStyle={{
                                    background: "var(--surface)",
                                    border: "1px solid var(--border)",
                                    borderRadius: 8,
                                }}
                            />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            {seriesNames.map((name, i) => (
                                <Line
                                    key={name}
                                    type="monotone"
                                    dataKey={name}
                                    stroke={COLORS[i % COLORS.length]}
                                    dot={points.length <= 24}
                                    strokeWidth={2}
                                    name={name.length > 40 ? `${name.slice(0, 37)}…` : name}
                                />
                            ))}
                        </LineChart>
                    )}
                </ResponsiveContainer>
            </div>

            {points.length >= MAX_X_POINTS && (
                <p className="text-xs text-amber-800 dark:text-amber-200">
                    Viser maks. {MAX_X_POINTS} punkter på X-aksen — snevre inn med filtre eller last ned
                    CSV for full data.
                </p>
            )}
        </div>
    );
}

function ChartControls({
    candidateXKeys,
    candidateSeriesKeys,
    xAxisChoice,
    setXAxisChoice,
    seriesChoice,
    setSeriesChoice,
    chartKind,
    setChartKind,
    sliceDimensions,
    sliceFilters,
    setSliceFilters,
    rows,
}: {
    candidateXKeys: string[];
    candidateSeriesKeys: string[];
    xAxisChoice: string;
    setXAxisChoice: (v: string) => void;
    seriesChoice: string;
    setSeriesChoice: (v: string) => void;
    chartKind: "line" | "bar";
    setChartKind: (v: "line" | "bar") => void;
    sliceDimensions: string[];
    sliceFilters: Record<string, string>;
    setSliceFilters: React.Dispatch<React.SetStateAction<Record<string, string>>>;
    rows: Array<Record<string, string | number | null>>;
}) {
    return (
        <div className="rounded-xl border border-border bg-muted/10 p-4 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Tilpass diagram (forklaring til beslutningstakere)
            </div>
            <div className="flex flex-wrap gap-3 items-end">
                <label className="flex flex-col gap-1 text-xs min-w-[140px]">
                    <span className="text-muted-foreground">Diagramtype</span>
                    <select
                        value={chartKind}
                        onChange={(e) => setChartKind(e.target.value as "line" | "bar")}
                        className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                    >
                        <option value="line">Linje (trend)</option>
                        <option value="bar">Stolpe (sammenligning)</option>
                    </select>
                </label>
                <label className="flex flex-col gap-1 text-xs min-w-[160px]">
                    <span className="text-muted-foreground">X-akse</span>
                    <select
                        value={xAxisChoice}
                        onChange={(e) => setXAxisChoice(e.target.value)}
                        className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                    >
                        <option value={AUTO}>Auto (tid hvis funnet)</option>
                        {candidateXKeys.map((k) => (
                            <option key={k} value={k}>
                                {k}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="flex flex-col gap-1 text-xs min-w-[160px]">
                    <span className="text-muted-foreground">Serier (farge/legende)</span>
                    <select
                        value={seriesChoice}
                        onChange={(e) => setSeriesChoice(e.target.value)}
                        className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                    >
                        <option value={AUTO}>Auto</option>
                        {candidateSeriesKeys.map((k) => (
                            <option key={k} value={k}>
                                {k}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            {sliceDimensions.length > 0 && (
                <div className="flex flex-wrap gap-3 items-end pt-1 border-t border-border/60">
                    <span className="text-xs text-muted-foreground w-full sm:w-auto sm:mr-2">
                        Filtrer (én verdi per dimensjon — reduserer «støy» når tabellen har mange
                        kryss):
                    </span>
                    {sliceDimensions.map((dim) => {
                        const vals = uniqSorted(rows, dim);
                        if (vals.length < 2) return null;
                        return (
                            <label key={dim} className="flex flex-col gap-1 text-xs min-w-[140px]">
                                <span className="text-muted-foreground truncate" title={dim}>
                                    {dim}
                                </span>
                                <select
                                    value={sliceFilters[dim] ?? vals[0] ?? ""}
                                    onChange={(e) =>
                                        setSliceFilters((prev) => ({
                                            ...prev,
                                            [dim]: e.target.value,
                                        }))
                                    }
                                    className="rounded-lg border border-border bg-background px-2 py-1.5 text-sm text-foreground max-w-[220px]"
                                >
                                    {vals.map((v) => (
                                        <option key={v} value={v}>
                                            {v.length > 42 ? `${v.slice(0, 39)}…` : v}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
