"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  AGRESSO_COLUMNS,
  getColumnExplanation,
} from "@/lib/domains/agresso/columnDefinitions";
import { summarizeByGroup } from "@/lib/domains/agresso/agressoCategories";
import {
  analyzeRows,
  computeBilagLocationCounts,
  DEFAULT_EVAL_PROMPT,
  parseBeløp,
  parseCsvText,
  rowToJsonForPrompt,
  type ParsedRow,
  type RowAnalysis,
} from "@/lib/domains/agresso/csvAnalysis";
import { AlertTriangle, BookOpen, Copy, FileSpreadsheet, Filter, Layers } from "lucide-react";

const PAGE_OPTIONS = [50, 100, 250, 500] as const;

const AUTO_LOAD_CSV =
  process.env.NEXT_PUBLIC_AUTO_LOAD_AGRESSO_CSV === "1" ||
  process.env.NEXT_PUBLIC_AUTO_LOAD_AGRESSO_CSV === "true";

function formatMoney(n: number): string {
  return new Intl.NumberFormat("nb-NO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

export function AgressoCsvLab() {
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<ParsedRow[]>([]);
  const [analysis, setAnalysis] = useState<RowAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [categoryGroup, setCategoryGroup] = useState<string>("all");
  const [pageSize, setPageSize] = useState<(typeof PAGE_OPTIONS)[number]>(100);
  const [page, setPage] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [evalPrompt, setEvalPrompt] = useState(DEFAULT_EVAL_PROMPT);

  const ingestCsvText = useCallback((text: string) => {
    try {
      const { headers: h, rows: r } = parseCsvText(text);
      if (h.length === 0) {
        setError("Fant ingen kolonner i filen.");
        setHeaders([]);
        setRows([]);
        setAnalysis([]);
        return;
      }
      setError(null);
      setHeaders(h);
      setRows(r);
      setAnalysis(analyzeRows(h, r));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kunne ikke tolke CSV.");
      setHeaders([]);
      setRows([]);
      setAnalysis([]);
    }
  }, []);

  const onFile = useCallback(
    async (file: File | null) => {
      if (!file) return;
      setLoading(true);
      setError(null);
      setSelectedIndex(null);
      setPage(0);
      try {
        const text = await file.text();
        ingestCsvText(text);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Kunne ikke lese filen.");
        setHeaders([]);
        setRows([]);
        setAnalysis([]);
      } finally {
        setLoading(false);
      }
    },
    [ingestCsvText],
  );

  useEffect(() => {
    if (!AUTO_LOAD_CSV) return;
    const w = window as Window & { __AGRESSO_CSV_AUTO_DONE__?: boolean };
    if (w.__AGRESSO_CSV_AUTO_DONE__) return;
    w.__AGRESSO_CSV_AUTO_DONE__ = true;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setSelectedIndex(null);
      setPage(0);
      try {
        const res = await fetch("/api/agresso-csv/local", { cache: "no-store" });
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({})) as { error?: string };
          if (!cancelled) {
            setError(
              typeof errBody.error === "string"
                ? errBody.error
                : `Kunne ikke hente fil (${res.status}).`,
            );
            setHeaders([]);
            setRows([]);
            setAnalysis([]);
          }
          return;
        }
        const text = await res.text();
        if (cancelled) return;
        ingestCsvText(text);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Nettverksfeil ved henting av CSV.");
          setHeaders([]);
          setRows([]);
          setAnalysis([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ingestCsvText]);

  const groupSummary = useMemo(() => {
    if (!analysis.length) return [];
    return summarizeByGroup(
      analysis.map((a) => a.category),
      analysis.map((a) => a.amount),
    );
  }, [analysis]);

  const flaggedSet = useMemo(() => {
    const s = new Set<number>();
    analysis.forEach((a) => {
      if (a.flags.length > 0) s.add(a.rowIndex);
    });
    return s;
  }, [analysis]);

  const bilagLocMax = useMemo(() => {
    if (!headers.length || !rows.length) return 0;
    const m = computeBilagLocationCounts(rows, headers);
    return Math.max(0, ...m.values());
  }, [headers, rows]);

  const filteredIndices = useMemo(() => {
    const q = query.trim().toLowerCase();
    const out: number[] = [];
    for (let i = 0; i < rows.length; i++) {
      if (categoryGroup !== "all" && analysis[i]?.category.groupKey !== categoryGroup) {
        continue;
      }
      if (flaggedOnly && !flaggedSet.has(i)) continue;
      if (q) {
        const blob = Object.values(rows[i]!).join(" ").toLowerCase();
        if (!blob.includes(q)) continue;
      }
      out.push(i);
    }
    return out;
  }, [rows, analysis, query, flaggedOnly, flaggedSet, categoryGroup]);

  const pageCount = Math.max(1, Math.ceil(filteredIndices.length / pageSize));
  const safePage = Math.min(page, pageCount - 1);
  const sliceStart = safePage * pageSize;
  const pageIndices = filteredIndices.slice(sliceStart, sliceStart + pageSize);

  const selectedRow =
    selectedIndex !== null && rows[selectedIndex] ? rows[selectedIndex] : null;
  const selectedAnalysis =
    selectedIndex !== null ? analysis[selectedIndex] : undefined;

  const beløpHeader = useMemo(() => {
    return headers.find((h) => {
      const t = h.trim().toLowerCase();
      return t === "beløp" || t === "belop" || t.includes("beløp");
    });
  }, [headers]);

  const fullPromptForCopy =
    selectedRow != null
      ? `${evalPrompt.trim()}\n\n${rowToJsonForPrompt(selectedRow, selectedAnalysis)}`
      : "";

  const copyPrompt = async () => {
    if (!fullPromptForCopy) return;
    try {
      await navigator.clipboard.writeText(fullPromptForCopy);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b border-border bg-surface/80 backdrop-blur-sm">
        <div className="mx-auto max-w-[1800px] px-4 py-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Agresso CSV-lab
              </h1>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                Last inn eksport av lokalkostnader. Alle kolonner vises med forklaring,
                og rader med mulige avvik flagges. Bruk prompten under til manuell eller
                ekstern KI-vurdering av valgt rad.
              </p>
              {AUTO_LOAD_CSV && (
                <p className="mt-2 max-w-2xl rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-muted-foreground">
                  <strong className="text-foreground">Auto-innlasting:</strong> ved besøk hentes CSV fra{" "}
                  <code className="text-foreground">AGRESSO_CSV_PATH</code> via{" "}
                  <code className="text-foreground">/api/agresso-csv/local</code> (kun{" "}
                  <code className="text-foreground">npm run dev</code>). Store filer (~30+ MB) kan bruke
                  noen sekunder. Endrer du <code className="text-foreground">.env.local</code>, start
                  dev-server på nytt.
                </p>
              )}
            </div>
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-background px-4 py-3 text-sm hover:bg-surface">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
              <span className="font-medium">
                {loading ? "Leser …" : "Velg CSV-fil"}
              </span>
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                disabled={loading}
                onChange={(e) => onFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>

          {error && (
            <p className="mt-4 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          {rows.length > 0 && (
            <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
              <span>
                <strong>{rows.length.toLocaleString("nb-NO")}</strong> rader,{" "}
                <strong>{flaggedSet.size.toLocaleString("nb-NO")}</strong> med flagg
              </span>
              <span className="text-muted-foreground">
                Maks Dim2-steder per bilag i utvalg:{" "}
                <strong>{bilagLocMax}</strong>
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto grid max-w-[1800px] gap-6 px-4 py-6 lg:grid-cols-[minmax(260px,320px)_1fr]">
        {/* Kolonneordbok */}
        <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
          <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
            <BookOpen className="h-4 w-4" />
            Kolonneforklaringer
          </div>
          <div className="max-h-[70vh] space-y-2 overflow-y-auto rounded-lg border border-border bg-surface/50 p-3 text-xs">
            {AGRESSO_COLUMNS.map((c) => (
              <details key={c.key} className="group border-b border-border/60 pb-2 last:border-0">
                <summary className="cursor-pointer font-medium text-foreground group-open:text-primary">
                  {c.label}
                </summary>
                <p className="mt-1 text-muted-foreground">{c.explanation}</p>
              </details>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Ekstra kolonner i filen får generisk forklaring i tabellens tooltip-rad.
          </p>
        </aside>

        <main className="min-w-0 space-y-4">
          {/* Verktøylinje */}
          <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface/40 p-4 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={flaggedOnly}
                  onChange={(e) => {
                    setFlaggedOnly(e.target.checked);
                    setPage(0);
                  }}
                  className="rounded border-border"
                />
                Kun rader med flagg
              </label>
            </div>
            <input
              type="search"
              placeholder="Søk i alle felt …"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(0);
              }}
              className="min-w-[200px] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              Regnskapsgruppe
              <select
                value={categoryGroup}
                onChange={(e) => {
                  setCategoryGroup(e.target.value);
                  setPage(0);
                }}
                className="max-w-[220px] rounded-md border border-border bg-background px-2 py-1"
                title="Filtrer på avledet kategori fra konto (se oppsummering under)"
              >
                <option value="all">Alle grupper</option>
                {groupSummary.map((g) => (
                  <option key={g.groupKey} value={g.groupKey}>
                    {g.groupLabel} ({g.rowCount.toLocaleString("nb-NO")})
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              Rader/side
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value) as (typeof PAGE_OPTIONS)[number]);
                  setPage(0);
                }}
                className="rounded-md border border-border bg-background px-2 py-1"
              >
                {PAGE_OPTIONS.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <span className="text-sm text-muted-foreground">
              Viser {filteredIndices.length.toLocaleString("nb-NO")} treff · side{" "}
              {safePage + 1}/{pageCount}
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={safePage <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Forrige
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={safePage >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Neste
              </Button>
            </div>
          </div>

          {rows.length === 0 && !loading && (
            <p className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
              Last opp CSV-filen for å starte.
            </p>
          )}

          {rows.length > 0 && groupSummary.length > 0 && (
            <div className="rounded-lg border border-border bg-surface/40 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                <Layers className="h-4 w-4" />
                Regnskapskategorier (avledet fra konto)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground">
                      <th className="py-2 pr-3 font-medium">Gruppe</th>
                      <th className="py-2 pr-3 font-medium text-right">Rader</th>
                      <th className="py-2 font-medium text-right">Sum beløp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groupSummary.map((g) => (
                      <tr key={g.groupKey} className="border-b border-border/50">
                        <td className="py-1.5 pr-3">{g.groupLabel}</td>
                        <td className="py-1.5 pr-3 text-right tabular-nums">
                          {g.rowCount.toLocaleString("nb-NO")}
                        </td>
                        <td className="py-1.5 text-right tabular-nums">
                          {formatMoney(g.sumAmount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {rows.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-max min-w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-surface">
                    <th className="sticky left-0 z-20 bg-surface px-2 py-2 font-medium">
                      #
                    </th>
                    <th className="px-2 py-2 font-medium">Flagg</th>
                    <th
                      className="max-w-[140px] px-2 py-2 font-medium"
                      title="Samlet gruppe basert på hovedbokskonto (lokalkost)"
                    >
                      Gruppe
                    </th>
                    <th
                      className="max-w-[180px] px-2 py-2 font-medium"
                      title="Kontonavn fra CSV"
                    >
                      Konto (detalj)
                    </th>
                    {headers.map((h) => (
                      <th
                        key={h}
                        className="max-w-[200px] whitespace-normal px-2 py-2 font-medium"
                        title={getColumnExplanation(h)}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageIndices.map((rowIdx) => {
                    const row = rows[rowIdx]!;
                    const ra = analysis[rowIdx]!;
                    const hasFlags = ra.flags.length > 0;
                    const isSel = selectedIndex === rowIdx;
                    return (
                      <tr
                        key={rowIdx}
                        onClick={() => setSelectedIndex(rowIdx)}
                        className={cn(
                          "cursor-pointer border-b border-border/60 hover:bg-surface/80",
                          hasFlags && "bg-amber-500/5",
                          isSel && "ring-1 ring-inset ring-primary",
                        )}
                      >
                        <td className="sticky left-0 z-10 bg-inherit px-2 py-1.5 text-muted-foreground">
                          {rowIdx + 1}
                        </td>
                        <td className="px-2 py-1.5">
                          {hasFlags ? (
                            <span title={ra.flagLabels.join("\n")}>
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                            </span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td
                          className="max-w-[140px] truncate px-2 py-1.5"
                          title={ra.category.groupLabel}
                        >
                          {ra.category.groupLabel}
                        </td>
                        <td
                          className="max-w-[180px] truncate px-2 py-1.5 text-muted-foreground"
                          title={ra.category.detailLabel}
                        >
                          {ra.category.detailLabel}
                        </td>
                        {headers.map((h) => (
                          <td
                            key={h}
                            className="max-w-[220px] truncate px-2 py-1.5"
                            title={`${getColumnExplanation(h)}\n\n${row[h] ?? ""}`}
                          >
                            {beløpHeader && h === beløpHeader
                              ? formatMoney(parseBeløp(row[h]))
                              : row[h] ?? ""}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Valgt rad + prompt */}
          {selectedRow && (
            <section className="space-y-3 rounded-lg border border-border bg-surface/40 p-4">
              <h2 className="text-sm font-semibold">Valgt rad #{selectedIndex! + 1}</h2>
              {selectedAnalysis && (
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">Kategori:</span>{" "}
                  {selectedAnalysis.category.groupLabel} — {selectedAnalysis.category.detailLabel}
                </p>
              )}
              {selectedAnalysis && selectedAnalysis.flags.length > 0 && (
                <ul className="list-inside list-disc space-y-1 text-sm text-amber-200/90">
                  {selectedAnalysis.flagLabels.map((l) => (
                    <li key={l}>{l}</li>
                  ))}
                </ul>
              )}
              {selectedAnalysis && selectedAnalysis.flags.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Ingen automatiske flagg på denne raden.
                </p>
              )}
              <div>
                <label className="mb-1 block text-xs font-medium text-muted-foreground">
                  Evalueringsprompt (rediger etter behov — kopier til KI eller notater)
                </label>
                <textarea
                  value={evalPrompt}
                  onChange={(e) => setEvalPrompt(e.target.value)}
                  rows={8}
                  className="w-full rounded-md border border-border bg-background font-mono text-xs leading-relaxed"
                />
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button type="button" size="sm" onClick={copyPrompt}>
                    <Copy className="mr-2 h-4 w-4" />
                    Kopier prompt + rad (JSON)
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setEvalPrompt(DEFAULT_EVAL_PROMPT)}
                  >
                    Tilbakestill prompt
                  </Button>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
