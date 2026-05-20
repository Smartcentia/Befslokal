"use client";

import { useEffect, useState, useCallback } from "react";
import {
    getTotalKostPerRegion,
    getGLAccountTotals,
    getGLTotalsByYear,
    type TotalKostPerRegion,
    type GLAccountTotals,
} from "@/lib/api/propertiesApi";
import { Layers, GitCompareArrows, AlertCircle, CalendarRange } from "lucide-react";

/** Alle år vi viser historikk for (GL i databasen + innkjøps-JSON der det finnes). */
export const COST_SOURCE_HISTORY_YEARS = [2020, 2021, 2022, 2023, 2024, 2025] as const;

function formatCurrency(n: number): string {
    return new Intl.NumberFormat("nb-NO", {
        style: "currency",
        currency: "NOK",
        maximumFractionDigits: 0,
    }).format(n);
}

function formatMnok(n: number): string {
    if (!Number.isFinite(n)) return "—";
    return `${(n / 1e6).toFixed(1)} MNOK`;
}

/** Summerer alle kategorier i Innkjøpsanalyse-JSON (sum per region per kategori). */
export function sumTotalKostInnkjøps(data: TotalKostPerRegion | null): number {
    if (!data?.by_category) return 0;
    let t = 0;
    for (const cat of Object.values(data.by_category)) {
        const br = cat.by_region_totals;
        if (!br || typeof br !== "object") continue;
        for (const v of Object.values(br)) {
            t += typeof v === "number" ? v : 0;
        }
    }
    return t;
}

/** Per kategori: total beløp (alle regioner). */
function innkjøpsCategoryTotals(data: TotalKostPerRegion | null): Record<string, number> {
    const m: Record<string, number> = {};
    if (!data?.by_category) return m;
    for (const [name, cat] of Object.entries(data.by_category)) {
        let s = 0;
        const br = cat.by_region_totals;
        if (br && typeof br === "object") {
            for (const v of Object.values(br)) {
                s += typeof v === "number" ? v : 0;
            }
        }
        m[name] = s;
    }
    return m;
}

function norm(s: string): string {
    return s.toLowerCase().replace(/\s+/g, " ").trim();
}

/** Finn nærmeste Innkjøpsanalyse-kategori til et GL-kontonavn. */
function matchInnkjøpsCategory(
    accountName: string,
    totals: Record<string, number>
): { key: string | null; amount: number } {
    const n = norm(accountName);
    if (!n) return { key: null, amount: 0 };

    for (const [key, val] of Object.entries(totals)) {
        const kn = norm(key);
        if (kn === n) return { key, amount: val };
    }
    for (const [key, val] of Object.entries(totals)) {
        const kn = norm(key);
        if (kn.includes(n) || n.includes(kn)) return { key, amount: val };
    }
    const words = new Set(n.split(/[^a-zæøå0-9]+/i).filter((w) => w.length > 3));
    let best: { key: string; score: number; amount: number } | null = null;
    for (const [key, val] of Object.entries(totals)) {
        const kn = norm(key);
        const kwords = kn.split(/[^a-zæøå0-9]+/i).filter((w) => w.length > 3);
        let score = 0;
        for (const kw of kwords) {
            if (words.has(kw)) score += 1;
        }
        if (score > 0 && (!best || score > best.score)) {
            best = { key, score, amount: val };
        }
    }
    if (best && best.score >= 2) return { key: best.key, amount: best.amount };
    return { key: null, amount: 0 };
}

interface Props {
    /** Startår for detaljvisning (GL-kontoer + treff mot innkjøp). */
    defaultDetailYear?: number;
    topN?: number;
    /** Kalles når bruker velger år (historikk/detalj) — synker GL-kolonne i eiendomstabellen. */
    onDetailYearChange?: (year: number) => void;
}

/**
 * Sammenligner aggregerte tall fra Innkjøpsanalyse-import (total_kost_per_region JSON)
 * med faktisk bokført GL (alle transaksjoner gruppert på kontonavn).
 * Viser oversikt per år 2020–2025 og detalj for valgt år.
 */
export default function CostSourceAnalysisSection({
    defaultDetailYear = 2025,
    topN = 12,
    onDetailYearChange,
}: Props) {
    const [detailYear, setDetailYear] = useState(defaultDetailYear);

    const [glByYear, setGlByYear] = useState<Record<string, number>>({});
    const [innkjøpsSumByYear, setInnkjøpsSumByYear] = useState<Record<number, number>>({});
    const [historyLoading, setHistoryLoading] = useState(true);
    const [historyError, setHistoryError] = useState<string | null>(null);

    const [innkjøps, setInnkjøps] = useState<TotalKostPerRegion | null>(null);
    const [gl, setGl] = useState<GLAccountTotals | null>(null);
    const [detailLoading, setDetailLoading] = useState(true);
    const [detailError, setDetailError] = useState<string | null>(null);

    /** Historikk: GL per år + innkjøpssum per år (parallell lasting). */
    useEffect(() => {
        let cancelled = false;
        (async () => {
            setHistoryLoading(true);
            setHistoryError(null);
            try {
                const results = await Promise.all([
                    getGLTotalsByYear(),
                    ...COST_SOURCE_HISTORY_YEARS.map((y) => getTotalKostPerRegion(y)),
                ]);
                if (cancelled) return;
                const glRes = results[0];
                setGlByYear(glRes?.by_year ?? {});
                const sums: Record<number, number> = {};
                COST_SOURCE_HISTORY_YEARS.forEach((y, i) => {
                    sums[y] = sumTotalKostInnkjøps(results[i + 1] as TotalKostPerRegion | null);
                });
                setInnkjøpsSumByYear(sums);
            } catch (e) {
                if (!cancelled) setHistoryError(e instanceof Error ? e.message : "Kunne ikke laste historikk");
            } finally {
                if (!cancelled) setHistoryLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, []);

    /** Detalj for valgt år. */
    useEffect(() => {
        let cancelled = false;
        (async () => {
            setDetailLoading(true);
            setDetailError(null);
            try {
                const [a, b] = await Promise.all([
                    getTotalKostPerRegion(detailYear),
                    getGLAccountTotals(detailYear, 40),
                ]);
                if (!cancelled) {
                    setInnkjøps(a);
                    setGl(b);
                }
            } catch (e) {
                if (!cancelled) setDetailError(e instanceof Error ? e.message : "Kunne ikke laste detaljer");
            } finally {
                if (!cancelled) setDetailLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [detailYear]);

    const onSelectYear = useCallback(
        (y: number) => {
            setDetailYear(y);
            onDetailYearChange?.(y);
        },
        [onDetailYearChange]
    );

    const innkjøpsSum = sumTotalKostInnkjøps(innkjøps);
    const catTotals = innkjøpsCategoryTotals(innkjøps);
    const glTotal = gl?.total_amount ?? 0;
    const diff = glTotal - innkjøpsSum;
    const hasInnkjøpsData = innkjøps && Object.keys(innkjøps.by_category || {}).length > 0;
    const topAccounts = (gl?.top_accounts ?? []).slice(0, topN);
    const barDen = glTotal > 0 ? glTotal : 1;

    if (historyError) {
        return (
            <div className="rounded-2xl border border-destructive/40 bg-destructive/5 p-6 text-sm text-destructive flex items-start gap-2">
                <AlertCircle className="shrink-0 mt-0.5" size={18} />
                {historyError}
            </div>
        );
    }

    return (
        <section className="rounded-2xl border border-border bg-surface shadow-sm overflow-hidden">
            <div className="p-6 border-b border-border bg-muted/20">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="flex items-start gap-3 min-w-0">
                        <GitCompareArrows className="text-primary shrink-0 mt-1" size={28} />
                        <div>
                            <h2 className="text-xl font-bold text-foreground">Kostnadskilde: Innkjøpsanalyse vs GL</h2>
                            <p className="text-sm text-muted mt-1 max-w-3xl">
                                <strong>Innkjøpsanalyse</strong> viser importert «Total kost» per kategori og region (
                                <code className="text-xs bg-muted px-1 rounded">total_kost_per_region_ÅR.json</code>
                                ). <strong>GL</strong> er sum av alle bokførte transaksjoner i året. Tabellen under viser{" "}
                                <strong>2020–2025</strong> (historikk); for år uten import-fil vises kun GL.
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                        <label htmlFor="cost-source-detail-year" className="text-xs font-semibold text-muted uppercase tracking-wider">
                            Detaljvisning
                        </label>
                        <select
                            id="cost-source-detail-year"
                            className="rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground"
                            value={detailYear}
                            onChange={(e) => onSelectYear(Number(e.target.value))}
                        >
                            {COST_SOURCE_HISTORY_YEARS.map((y) => (
                                <option key={y} value={y}>
                                    {y}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Historikk 2020–2025 */}
            <div className="px-6 pt-6">
                <div className="flex items-center gap-2 mb-3">
                    <CalendarRange className="text-muted" size={18} />
                    <h3 className="text-sm font-bold text-foreground">GL og innkjøpsanalyse per år (2020–2025)</h3>
                </div>
                <div className="overflow-x-auto rounded-xl border border-border bg-background">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border bg-muted/30 text-left">
                                <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs">År</th>
                                <th className="px-4 py-3 font-bold text-primary uppercase text-xs text-right">GL totalt</th>
                                <th className="px-4 py-3 font-bold text-foreground uppercase text-xs text-right">Innkjøpsanalyse</th>
                                <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs text-right">Differanse</th>
                                <th className="px-4 py-3 font-bold text-muted-foreground uppercase text-xs w-24"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {historyLoading ? (
                                <tr>
                                    <td colSpan={5} className="px-4 py-8 text-center text-muted">
                                        Laster historikk…
                                    </td>
                                </tr>
                            ) : (
                                COST_SOURCE_HISTORY_YEARS.map((y) => {
                                    const glVal = glByYear[String(y)];
                                    const innVal = innkjøpsSumByYear[y] ?? 0;
                                    const hasGl = glVal != null && Number.isFinite(glVal);
                                    const hasInn = innVal > 0;
                                    const d = (hasGl ? (glVal as number) : 0) - innVal;
                                    const active = y === detailYear;
                                    return (
                                        <tr
                                            key={y}
                                            className={`${active ? "bg-primary/5" : "hover:bg-muted/20"} cursor-pointer transition-colors`}
                                            onClick={() => onSelectYear(y)}
                                        >
                                            <td className="px-4 py-2.5 font-medium">{y}</td>
                                            <td className="px-4 py-2.5 text-right font-mono tabular-nums">
                                                {hasGl ? formatCurrency(glVal!) : "—"}
                                            </td>
                                            <td className="px-4 py-2.5 text-right font-mono tabular-nums text-muted">
                                                {hasInn ? formatCurrency(innVal) : "—"}
                                            </td>
                                            <td className="px-4 py-2.5 text-right font-mono tabular-nums text-muted">
                                                {hasGl && hasInn ? formatCurrency(d) : "—"}
                                            </td>
                                            <td className="px-4 py-2.5 text-right text-xs text-primary font-medium">
                                                {active ? "Valgt" : "Vis detalj →"}
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
                <p className="text-[11px] text-muted mt-2 mb-4">
                    GL-tall kommer fra databasen (alle transaksjoner). Innkjøpsanalyse krever importfil for året. Klikk en rad for å
                    oppdatere detaljvisningen under.
                </p>
            </div>

            {detailError && (
                <div className="mx-6 mb-4 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive flex items-start gap-2">
                    <AlertCircle className="shrink-0 mt-0.5" size={18} />
                    {detailError}
                </div>
            )}

            {detailLoading ? (
                <div className="px-6 pb-8 flex items-center gap-3 text-muted">
                    <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    Laster detaljer for {detailYear}…
                </div>
            ) : (
                <>
                    <div className="p-6 grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-border">
                        <div className="rounded-xl border border-border bg-background p-4">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-muted mb-1 flex items-center gap-2">
                                <Layers size={14} /> Innkjøpsanalyse (sum) {detailYear}
                            </div>
                            <div className="text-2xl font-bold text-foreground">{formatCurrency(innkjøpsSum)}</div>
                            <div className="text-xs text-muted mt-1">{formatMnok(innkjøpsSum)}</div>
                            {!hasInnkjøpsData && (
                                <p className="text-xs text-amber-600 dark:text-amber-500 mt-2">Ingen import-fil for dette året.</p>
                            )}
                        </div>
                        <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-muted mb-1">GL totalt ({detailYear})</div>
                            <div className="text-2xl font-bold text-primary">{formatCurrency(glTotal)}</div>
                            <div className="text-xs text-muted mt-1">{formatMnok(glTotal)}</div>
                            <div className="text-xs text-muted mt-2">
                                Herav husleie (kontomønster):{" "}
                                <span className="font-medium text-foreground">{formatMnok(gl?.total_faktisk_husleie ?? 0)}</span>
                            </div>
                        </div>
                        <div className="rounded-xl border border-border bg-background p-4">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-muted mb-1">Differanse (GL − Innkjøps)</div>
                            <div
                                className={`text-2xl font-bold ${
                                    !hasInnkjøpsData
                                        ? "text-muted"
                                        : Math.abs(diff) < 1e7
                                          ? "text-emerald-600 dark:text-emerald-400"
                                          : "text-amber-600 dark:text-amber-400"
                                }`}
                            >
                                {hasInnkjøpsData ? formatCurrency(diff) : "—"}
                            </div>
                            <div className="text-xs text-muted mt-1">{hasInnkjøpsData ? formatMnok(diff) : ""}</div>
                            <p className="text-[11px] text-muted mt-2 leading-snug">
                                Avvik forventes (andre kostnader, periodisering, kostnader uten eiendom). Bruk tabellen under for å se
                                største GL-kontoer.
                            </p>
                        </div>
                    </div>

                    <div className="px-6 pb-6">
                        <h3 className="text-sm font-bold text-foreground mb-3">
                            Topp {topN} GL-kontoer i {detailYear} (andel av GL-total)
                        </h3>
                        <div className="space-y-2">
                            {topAccounts.map((row, idx) => {
                                const pct = (row.amount / barDen) * 100;
                                const match = matchInnkjøpsCategory(row.account_name, catTotals);
                                const hasMatch = match.key != null && match.amount > 0;
                                return (
                                    <div
                                        key={`${row.account_name}-${idx}`}
                                        className="rounded-lg border border-border/80 overflow-hidden bg-background"
                                    >
                                        <div className="flex items-center justify-between gap-2 px-3 py-2 text-xs">
                                            <span className="font-medium truncate flex-1" title={row.account_name}>
                                                {row.account_name}
                                                {row.is_lease && (
                                                    <span className="ml-2 text-[10px] uppercase text-primary font-bold">Leie</span>
                                                )}
                                            </span>
                                            <span className="font-mono text-muted shrink-0">{formatCurrency(row.amount)}</span>
                                            <span className="font-mono text-muted w-12 text-right shrink-0">{pct.toFixed(1)}%</span>
                                        </div>
                                        <div className="h-2 bg-muted/30 relative">
                                            <div
                                                className="absolute left-0 top-0 h-full bg-primary/70 rounded-r"
                                                style={{ width: `${Math.min(100, pct)}%` }}
                                            />
                                        </div>
                                        <div className="px-3 py-1.5 text-[11px] text-muted border-t border-border/50 flex flex-wrap gap-x-3 gap-y-1">
                                            {hasMatch ? (
                                                <>
                                                    <span className="text-emerald-600 dark:text-emerald-400">
                                                        Treff i innkjøp: {match.key}
                                                    </span>
                                                    <span>≈ {formatCurrency(match.amount)} i innkjøpsanalyse</span>
                                                </>
                                            ) : (
                                                <span className="text-muted">
                                                    Ingen direkte treff i innkjøpskategorier — sjekk kontonavn/oppdeling.
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        {gl && gl.account_count > topN && (
                            <p className="text-xs text-muted mt-4">
                                Totalt {gl.account_count} ulike kontonavn i GL for {detailYear}. Topp {topN} vises.
                            </p>
                        )}
                    </div>
                </>
            )}
        </section>
    );
}
