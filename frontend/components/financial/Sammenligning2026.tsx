"use client";

import { useState, useEffect, useMemo } from "react";
import { AlertTriangle, Info } from "lucide-react";
import { getFinanceBudgetSummary, type FinanceBudgetSummary } from "@/lib/api/financeBudgetApi";

// ─── Typer ───────────────────────────────────────────────────────────────────

interface PropertyRow {
  property: { property_id: string; name?: string; region?: string };
  budget?: number;
  financeBudget2026?: number;
}

interface Sammenligning2026Props {
  allRows: PropertyRow[];
  financeBudget2026: FinanceBudgetSummary | null;
}

type Visning = "fullår" | "ytd";

const REGIONS = ["Bufdir", "Midt-Norge", "Nord", "Sør", "Vest", "Øst"];
const NASJONAL_REGION = "Nasjonal";
const YTD_MONTH = 4;
const YTD_LABEL = "jan–apr";

// ─── Hjelpefunksjoner ─────────────────────────────────────────────────────────

function fmtNOK(n: number): string {
  if (Math.abs(n) >= 1_000_000_000)
    return (n / 1_000_000_000).toFixed(2).replace(".", ",") + " mrd";
  if (Math.abs(n) >= 1_000_000)
    return (n / 1_000_000).toFixed(1).replace(".", ",") + " M";
  return Math.round(n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function fmtPst(n: number): string {
  return (n > 0 ? "+" : "") + n.toFixed(1).replace(".", ",") + " %";
}

function avvikColor(pct: number): string {
  const abs = Math.abs(pct);
  if (abs > 20) return "text-red-600 dark:text-red-400";
  if (abs > 10) return "text-yellow-600 dark:text-yellow-400";
  return "text-emerald-600 dark:text-emerald-400";
}

function avvikRowBg(befs: number, oko: number): string {
  if (befs <= 0 || oko <= 0) return "";
  return befs > oko
    ? "bg-red-50/40 dark:bg-red-950/20"
    : "bg-emerald-50/40 dark:bg-emerald-950/20";
}

// ─── Komponent ────────────────────────────────────────────────────────────────

export default function Sammenligning2026({ allRows, financeBudget2026 }: Sammenligning2026Props) {
  const [visning, setVisning] = useState<Visning>("fullår");
  const [ytdOko, setYtdOko] = useState<FinanceBudgetSummary | null>(null);
  const [ytdLoading, setYtdLoading] = useState(false);

  // Lazy-last YTD-data ved første gang brukeren bytter til YTD
  useEffect(() => {
    if (visning !== "ytd" || ytdOko !== null) return;
    setYtdLoading(true);
    getFinanceBudgetSummary(2026, 'kontant_2026', YTD_MONTH)
      .then(setYtdOko)
      .finally(() => setYtdLoading(false));
  }, [visning, ytdOko]);

  // ── Fulltår-data ──────────────────────────────────────────────────────────

  const fulltårRows = useMemo(
    () =>
      allRows
        .map((r) => ({
          name: r.property.name ?? r.property.property_id,
          region: r.property.region ?? NASJONAL_REGION,
          befs: r.budget ?? 0,
          oko: r.financeBudget2026 ?? 0,
        }))
        .filter((r) => r.befs > 0 || r.oko > 0),
    [allRows],
  );

  const fulltårRegional = useMemo(() => {
    const map: Record<string, { befs: number; oko: number }> = {};
    for (const r of fulltårRows) {
      if (!map[r.region]) map[r.region] = { befs: 0, oko: 0 };
      map[r.region].befs += r.befs;
      map[r.region].oko += r.oko;
    }
    return map;
  }, [fulltårRows]);

  // ── YTD-data ──────────────────────────────────────────────────────────────

  const ytdOkoByProp = useMemo(() => {
    if (!ytdOko) return new Map<string, number>();
    return new Map(ytdOko.by_property.map((p) => [p.property_id, p.total]));
  }, [ytdOko]);

  const ytdRows = useMemo(
    () =>
      allRows
        .map((r) => ({
          name: r.property.name ?? r.property.property_id,
          region: r.property.region ?? NASJONAL_REGION,
          // Proporsjonal YTD-approksimering for modellen (4/12 av fulltår)
          befs: ((r.budget ?? 0) * YTD_MONTH) / 12,
          oko: ytdOkoByProp.get(r.property.property_id) ?? 0,
        }))
        .filter((r) => r.befs > 0 || r.oko > 0),
    [allRows, ytdOkoByProp],
  );

  const ytdRegional = useMemo(() => {
    const map: Record<string, { befs: number; oko: number }> = {};
    for (const r of ytdRows) {
      if (!map[r.region]) map[r.region] = { befs: 0, oko: 0 };
      map[r.region].befs += r.befs;
      map[r.region].oko += r.oko;
    }
    return map;
  }, [ytdRows]);

  // Aktive datasett
  const activeRows = visning === "fullår" ? fulltårRows : ytdRows;
  const activeRegional = visning === "fullår" ? fulltårRegional : ytdRegional;

  const totBefs = activeRows.reduce((s, r) => s + r.befs, 0);
  const totOko = activeRows.reduce((s, r) => s + r.oko, 0);
  const totAvvik = totBefs - totOko;

  // Topp-10 avvik (absolutt differanse)
  const topp10 = useMemo(
    () =>
      [...activeRows]
        .filter((r) => r.befs > 0 && r.oko > 0)
        .sort((a, b) => Math.abs(b.befs - b.oko) - Math.abs(a.befs - a.oko))
        .slice(0, 10),
    [activeRows],
  );

  const ytdSuffix = visning === "ytd" ? ` (${YTD_LABEL})` : "";

  return (
    <div className="space-y-5">
      {/* ── Toppsummering ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: `BEFS-estimat 2026${ytdSuffix}`, val: totBefs, color: "border-violet-500" },
          { label: `Vedtatt budsjett (Økonomi)${ytdSuffix}`, val: totOko, color: "border-teal-500" },
          {
            label: "Avvik (estimat − budsjett)",
            val: totAvvik,
            color: totAvvik > 0 ? "border-red-400" : "border-emerald-500",
          },
        ].map((c) => (
          <div key={c.label} className={`glass-card p-4 border-l-4 ${c.color}`}>
            <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">{c.label}</div>
            <div
              className={`text-xl font-bold tabular-nums ${
                c.label.startsWith("Avvik")
                  ? totAvvik > 0
                    ? "text-red-600 dark:text-red-400"
                    : "text-emerald-600 dark:text-emerald-400"
                  : ""
              }`}
            >
              {totAvvik > 0 && c.label.startsWith("Avvik") ? "+" : ""}
              {fmtNOK(c.val)}
            </div>
          </div>
        ))}
      </div>

      {/* ── Visning-toggle ──────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Visning:</span>
        {(["fullår", "ytd"] as Visning[]).map((v) => (
          <button
            key={v}
            onClick={() => setVisning(v)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              visning === v
                ? "bg-primary text-primary-foreground"
                : "bg-muted/50 text-muted-foreground hover:bg-muted"
            }`}
          >
            {v === "fullår" ? "Fulltår" : `YTD ${YTD_LABEL}`}
          </button>
        ))}
        {visning === "ytd" && ytdLoading && (
          <span className="text-xs text-muted-foreground animate-pulse">Laster YTD-data…</span>
        )}
      </div>

      {/* ── Kildeforklaring ─────────────────────────────────────────────────── */}
      <div className="flex gap-2 items-start rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20 p-3 text-xs text-blue-800 dark:text-blue-300">
        <Info className="h-3.5 w-3.5 mt-0.5 shrink-0" />
        <div className="space-y-1">
          <p>
            <strong>Økonomi-budsjett</strong> = <em>Beløp DA</em> (vedtatt fulltårsramme fra Agresso) —{" "}
            <strong>ikke</strong> Kontantbeløp (faktisk kassabevegelse per periode).
          </p>
          {visning === "ytd" && (
            <p>
              <strong>BEFS-estimat YTD</strong> er en proporsjonal approksimering: fulltårsmodell × 4/12.
              Økonomi-YTD er faktisk Beløp DA for månedene 1–{YTD_MONTH}.
            </p>
          )}
          <p>
            BEFS-estimat = GL 2025 husleie + 4,7 % og GL 2025 drift + 10,0 % inflasjonsjustering (to separate kilder summert, ≈ 604 M kr totalt).
          </p>
        </div>
      </div>

      {/* ── Regional sammendragstabell ───────────────────────────────────────── */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border/50">
          <h3 className="text-sm font-semibold">Regional oversikt{ytdSuffix}</h3>
        </div>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-muted/30 text-left">
              {["Region", "BEFS-estimat", "Vedtatt budsjett (Øk.)", "Avvik (NOK)", "Avvik (%)"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 font-semibold text-xs uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {REGIONS.map((reg) => {
              const d = activeRegional[reg] ?? { befs: 0, oko: 0 };
              if (d.befs === 0 && d.oko === 0) return null;
              const avvik = d.befs - d.oko;
              const pct = d.oko > 0 ? (avvik / d.oko) * 100 : null;
              return (
                <tr key={reg} className="border-t border-border/50 hover:bg-muted/20">
                  <td className="px-4 py-2.5 font-medium">{reg}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-violet-700 dark:text-violet-300">
                    {d.befs > 0 ? fmtNOK(d.befs) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-teal-700 dark:text-teal-300">
                    {d.oko > 0 ? fmtNOK(d.oko) : "—"}
                  </td>
                  <td
                    className={`px-4 py-2.5 text-right tabular-nums font-medium ${
                      pct !== null ? avvikColor(pct) : "text-muted-foreground"
                    }`}
                  >
                    {pct !== null ? `${avvik > 0 ? "+" : ""}${fmtNOK(avvik)}` : "—"}
                  </td>
                  <td
                    className={`px-4 py-2.5 text-right tabular-nums font-semibold ${
                      pct !== null ? avvikColor(pct) : "text-muted-foreground"
                    }`}
                  >
                    {pct !== null ? fmtPst(pct) : "—"}
                  </td>
                </tr>
              );
            })}
            {/* Nasjonale sekkepost-eiendommer (region=null i DB) */}
            {(() => {
              const d = activeRegional[NASJONAL_REGION];
              if (!d || (d.befs === 0 && d.oko === 0)) return null;
              return (
                <tr key="Nasjonal" className="border-t border-border/50 bg-muted/10 opacity-60 italic hover:bg-muted/20">
                  <td className="px-4 py-2.5 font-medium text-muted-foreground">
                    Nasjonal <span className="text-xs font-normal">(sekkepost)</span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                    {d.befs > 0 ? fmtNOK(d.befs) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">
                    {d.oko > 0 ? fmtNOK(d.oko) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">—</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-muted-foreground">—</td>
                </tr>
              );
            })()}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/20 font-bold">
              <td className="px-4 py-3">TOTAL</td>
              <td className="px-4 py-3 text-right tabular-nums text-violet-700 dark:text-violet-300">
                {fmtNOK(totBefs)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-teal-700 dark:text-teal-300">
                {fmtNOK(totOko)}
              </td>
              <td
                className={`px-4 py-3 text-right tabular-nums ${
                  totAvvik > 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {totAvvik > 0 ? "+" : ""}
                {fmtNOK(totAvvik)}
              </td>
              <td
                className={`px-4 py-3 text-right tabular-nums ${
                  totAvvik > 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {totOko > 0 ? fmtPst((totAvvik / totOko) * 100) : "—"}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* ── Topp-10 avvik ───────────────────────────────────────────────────── */}
      {topp10.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="px-4 py-3 border-b border-border/50">
            <h3 className="text-sm font-semibold">Topp 10 eiendomsavvik{ytdSuffix}</h3>
          </div>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-muted/30 text-left">
                {["Eiendom", "Region", "BEFS-estimat", "Vedtatt budsjett (Øk.)", "Avvik (NOK)", "Avvik (%)"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 font-semibold text-xs uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {topp10.map((r, i) => {
                const avvik = r.befs - r.oko;
                const pct = r.oko > 0 ? (avvik / r.oko) * 100 : null;
                const isStatlig = r.name.toLowerCase().includes("statlig");
                return (
                  <tr key={i} className={`border-t border-border/50 hover:bg-muted/20 ${avvikRowBg(r.befs, r.oko)}`}>
                    <td className="px-4 py-2.5 font-medium">
                      {r.name}
                      {isStatlig && (
                        <span
                          className="ml-1.5 inline-flex items-center gap-0.5 text-amber-600 dark:text-amber-400"
                          title="Statlig = nasjonal sekkepost-eiendom, ikke geografisk objekt"
                        >
                          <AlertTriangle className="h-3 w-3" />
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">{r.region}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-violet-700 dark:text-violet-300">
                      {fmtNOK(r.befs)}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-teal-700 dark:text-teal-300">
                      {fmtNOK(r.oko)}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right tabular-nums font-medium ${
                        pct !== null ? avvikColor(pct) : "text-muted-foreground"
                      }`}
                    >
                      {pct !== null ? `${avvik > 0 ? "+" : ""}${fmtNOK(avvik)}` : "—"}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right tabular-nums ${
                        pct !== null ? avvikColor(pct) : "text-muted-foreground"
                      }`}
                    >
                      {pct !== null ? fmtPst(pct) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Eiendomstabell (full liste) ──────────────────────────────────────── */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Alle eiendommer{ytdSuffix}</h3>
          <div className="flex gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-red-200 dark:bg-red-900/40" />
              Estimat over budsjett
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-2.5 h-2.5 rounded-sm bg-emerald-200 dark:bg-emerald-900/40" />
              Estimat under budsjett
            </span>
          </div>
        </div>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-muted/30 text-left">
              {["Eiendom", "Region", "BEFS-estimat", "Vedtatt budsjett (Øk.)", "Avvik (NOK)", "Avvik (%)"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-4 py-3 font-semibold text-xs uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                  >
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {activeRows
              .slice()
              .sort((a, b) => (b.befs || b.oko) - (a.befs || a.oko))
              .map((r, i) => {
                const avvik = r.befs - r.oko;
                const pct = r.oko > 0 ? (avvik / r.oko) * 100 : null;
                const harBegge = r.befs > 0 && r.oko > 0;
                return (
                  <tr
                    key={i}
                    className={`border-t border-border/50 hover:bg-muted/20 transition-colors ${
                      harBegge ? avvikRowBg(r.befs, r.oko) : ""
                    }`}
                  >
                    <td className="px-4 py-2.5 font-medium">{r.name}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{r.region}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-violet-700 dark:text-violet-300">
                      {r.befs > 0 ? fmtNOK(r.befs) : "—"}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-teal-700 dark:text-teal-300">
                      {r.oko > 0 ? fmtNOK(r.oko) : "—"}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right tabular-nums font-medium ${
                        !harBegge
                          ? "text-muted-foreground"
                          : pct !== null
                            ? avvikColor(pct)
                            : "text-muted-foreground"
                      }`}
                    >
                      {harBegge ? `${avvik > 0 ? "+" : ""}${fmtNOK(avvik)}` : "—"}
                    </td>
                    <td
                      className={`px-4 py-2.5 text-right tabular-nums ${
                        !harBegge
                          ? "text-muted-foreground"
                          : pct !== null
                            ? avvikColor(pct)
                            : "text-muted-foreground"
                      }`}
                    >
                      {pct !== null ? fmtPst(pct) : "—"}
                    </td>
                  </tr>
                );
              })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/20 font-bold">
              <td className="px-4 py-3">TOTAL</td>
              <td />
              <td className="px-4 py-3 text-right tabular-nums text-violet-700 dark:text-violet-300">
                {fmtNOK(totBefs)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-teal-700 dark:text-teal-300">
                {fmtNOK(totOko)}
              </td>
              <td
                className={`px-4 py-3 text-right tabular-nums ${
                  totAvvik > 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {totAvvik > 0 ? "+" : ""}
                {fmtNOK(totAvvik)}
              </td>
              <td
                className={`px-4 py-3 text-right tabular-nums ${
                  totAvvik > 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {totOko > 0 ? fmtPst((totAvvik / totOko) * 100) : "—"}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        <strong>BEFS-estimat:</strong> Kontant 2025 (faktisk regnskap) per eiendom × regional vekstrate.
        Vekstratene er reverse-engineered fra økonomiavdelingens vedtatte budsjett 2026 vs. regnskap 2025:
        Øst +17 %, Sør −11 %, Nord +27 %, Vest −15 %, Midt +2 %, Bufdir +14 %.
        Eiendommer uten regionkobling bruker +3,5 % flat rate.
        Kilde: budget-tabellen, data_source=&apos;okonomi_regional_2026&apos;.{" "}
        <strong>Vedtatt budsjett:</strong> Økonomiavdelingens budsjett lastet opp via{" "}
        <a href="/admin/budsjett-import" className="underline hover:text-foreground">
          budsjett-import
        </a>
        .
      </p>
    </div>
  );
}
