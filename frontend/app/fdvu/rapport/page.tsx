"use client";

/**
 * /fdvu/rapport — Porteføljerapport for FDVU
 *
 * Tre nivåer:
 *  - Hele Bufetat (standard)
 *  - Region (filter)
 *  - Enkelt eiendom (klikk i tabellen → /fdvu/[id]/rapport)
 *
 * Brukeren kan:
 *  - Velge region eller "Alle Bufetat"
 *  - Se compliance-rate per eiendom
 *  - Klikke "Skriv ut rapport" → browser-print → PDF (print:hidden skjuler kontroller)
 *  - Klikke på eiendomsnavn → gå til detaljert tilsynsrapport
 */

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Printer, Download, ChevronRight, CheckCircle2, XCircle, AlertCircle, Building2, Filter, ArrowUp, ArrowDown } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const TOKEN = process.env.NEXT_PUBLIC_BACKEND_SECRET ?? "befs-super-secret-key-12345";
const hdrs = () => ({ Authorization: `Bearer ${TOKEN}` });

// ─────────────────────────────────────────────
// Typer
// ─────────────────────────────────────────────

interface Property {
  property_id: string; name: string; address?: string; region?: string;
  unit_type_derived?: string; approved_places?: number;
}

interface Summary {
  property_id: string; total_assignments: number; compliant: number;
  non_compliant: number; partial: number; not_assessed: number;
  not_applicable: number; overdue_reviews: number; compliance_rate: number;
}

interface Row extends Property { summary: Summary | null; }

// ─────────────────────────────────────────────
// Hjelpere
// ─────────────────────────────────────────────

function rateColor(rate: number): string {
  if (rate >= 0.9) return "text-emerald-500";
  if (rate >= 0.6) return "text-amber-500";
  return "text-red-500";
}

function rateBar(rate: number): string {
  if (rate >= 0.9) return "bg-emerald-500";
  if (rate >= 0.6) return "bg-amber-500";
  return "bg-red-500";
}

function statusLabel(rate: number, total: number): string {
  if (total === 0) return "Ikke startet";
  if (rate >= 0.9) return "God";
  if (rate >= 0.6) return "Delvis";
  return "Avvik";
}

// ─────────────────────────────────────────────
// Komponent
// ─────────────────────────────────────────────

export default function PortfolioRapportPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [summaries, setSummaries] = useState<Record<string, Summary>>({});
  const [loading, setLoading] = useState(true);
  const [region, setRegion] = useState<string>("alle");
  const [sortBy, setSortBy] = useState<"name" | "rate" | "avvik">("rate");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const today = new Date().toLocaleDateString("no-NO", { day: "2-digit", month: "long", year: "numeric" });

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/v1/properties?limit=700`, { headers: hdrs() })
      .then(r => r.ok ? r.json() : { items: [] })
      .then(async d => {
        const props: Property[] = Array.isArray(d?.items) ? d.items : Array.isArray(d) ? d : [];
        setProperties(props);
        // Fetch summaries in parallel (cap at 100 to avoid overload)
        const batch = props.slice(0, 100);
        const results = await Promise.allSettled(
          batch.map(p =>
            fetch(`${API}/api/v1/fdvu/compliance/summary/${p.property_id}`, { headers: hdrs() })
              .then(r => r.ok ? r.json() as Promise<Summary> : null)
              .catch(() => null)
          )
        );
        const map: Record<string, Summary> = {};
        for (let i = 0; i < batch.length; i++) {
          const r = results[i];
          if (r.status === "fulfilled" && r.value) map[batch[i].property_id] = r.value;
        }
        setSummaries(map);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const regions = useMemo(() => {
    const s = new Set(properties.map(p => p.region ?? "Ukjent"));
    return ["alle", ...Array.from(s).sort()];
  }, [properties]);

  const rows: Row[] = useMemo(() => {
    let filtered = properties.map(p => ({ ...p, summary: summaries[p.property_id] ?? null }));
    if (region !== "alle") filtered = filtered.filter(r => r.region === region);
    filtered.sort((a, b) => {
      let diff = 0;
      if (sortBy === "name") diff = (a.name ?? "").localeCompare(b.name ?? "");
      else if (sortBy === "rate") diff = ((a.summary?.compliance_rate ?? -1) - (b.summary?.compliance_rate ?? -1));
      else if (sortBy === "avvik") diff = ((a.summary?.non_compliant ?? 0) - (b.summary?.non_compliant ?? 0));
      return sortDir === "asc" ? diff : -diff;
    });
    return filtered;
  }, [properties, summaries, region, sortBy, sortDir]);

  // Portfolio-KPIer
  const kpi = useMemo(() => {
    const all = Object.values(summaries);
    const total_assignments = all.reduce((s, x) => s + x.total_assignments, 0);
    const compliant = all.reduce((s, x) => s + x.compliant, 0);
    const non_compliant = all.reduce((s, x) => s + x.non_compliant, 0);
    const partial = all.reduce((s, x) => s + x.partial, 0);
    const not_assessed = all.reduce((s, x) => s + x.not_assessed, 0);
    const overdue = all.reduce((s, x) => s + x.overdue_reviews, 0);
    const denom = total_assignments - all.reduce((s, x) => s + x.not_applicable, 0) - not_assessed;
    const rate = denom > 0 ? compliant / denom : 0;
    return { total_assignments, compliant, non_compliant, partial, not_assessed, overdue, rate };
  }, [summaries]);

  const toggleSort = (col: "name" | "rate" | "avvik") => {
    if (sortBy === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortBy(col); setSortDir("asc"); }
  };

  const SortIcon = ({ col }: { col: "name" | "rate" | "avvik" }) => {
    if (sortBy !== col) return null;
    return sortDir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />;
  };

  const filteredRegion = region === "alle" ? "Hele Bufetat" : region;
  const propCount = rows.length;
  const assessedCount = rows.filter(r => r.summary && r.summary.total_assignments > 0).length;

  return (
    <div className="min-h-screen bg-background text-foreground">

      {/* Kontroller (skjules ved print) */}
      <div className="print:hidden border-b border-border bg-card/50 px-6 py-5">
        <div className="max-w-6xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Building2 size={20} className="text-primary" />
              FDVU Porteføljerapport
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {filteredRegion} · {propCount} eiendommer · Generert {today}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Region-filter */}
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-muted-foreground" />
              <select
                value={region}
                onChange={e => setRegion(e.target.value)}
                className="text-sm bg-background border border-border rounded-lg px-3 py-1.5 outline-none focus:border-primary/50"
              >
                {regions.map(r => (
                  <option key={r} value={r}>{r === "alle" ? "Alle Bufetat" : r}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <Printer size={14} />
              Skriv ut / Lagre PDF
            </button>
            <Link href="/fdvu/bulk-vurdering" className="flex items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors font-medium">
              Bulk-vurdering →
            </Link>
            <Link href="/fdvu" className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
              <ChevronRight size={14} className="rotate-180" /> Tilbake
            </Link>
          </div>
        </div>
      </div>

      {/* Rapport-innhold */}
      <div className="max-w-6xl mx-auto px-6 py-6 space-y-6 print:px-0 print:py-0">

        {/* Rapport-header (kun print) */}
        <div className="hidden print:block mb-6">
          <div className="flex items-center justify-between border-b border-gray-300 pb-4 mb-4">
            <div>
              <h1 className="text-2xl font-bold">FDVU Porteføljerapport — {filteredRegion}</h1>
              <p className="text-gray-600 text-sm mt-1">Bufetat Eiendom · Generert {today}</p>
            </div>
            <div className="text-right text-sm text-gray-500">
              <div>Konfidensielt</div>
              <div>Side 1 av 1</div>
            </div>
          </div>
        </div>

        {/* KPI-kort */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 print:grid-cols-6">
          {[
            { label: "Eiendommer", value: propCount, sub: `${assessedCount} med vurderinger` },
            { label: "Compliance-rate", value: `${Math.round(kpi.rate * 100)}%`, sub: "av vurderte krav", highlight: true },
            { label: "Oppfylt", value: kpi.compliant, sub: "krav", cls: "text-emerald-500" },
            { label: "Avvik", value: kpi.non_compliant, sub: "krav", cls: "text-red-500" },
            { label: "Delvis", value: kpi.partial, sub: "krav", cls: "text-amber-500" },
            { label: "Forfalt", value: kpi.overdue, sub: "revisjoner", cls: "text-orange-500" },
          ].map(k => (
            <div key={k.label} className="bg-card border border-border rounded-xl p-3 print:border-gray-200">
              <div className="text-xs text-muted-foreground">{k.label}</div>
              <div className={`text-2xl font-bold mt-1 ${k.cls ?? ""}`}>{k.value}</div>
              <div className="text-xs text-muted-foreground">{k.sub}</div>
            </div>
          ))}
        </div>

        {/* Compliance-bar */}
        <div className="bg-card border border-border rounded-xl p-4 print:border-gray-200">
          <div className="flex items-center justify-between mb-2 text-sm">
            <span className="font-medium">Portefølje compliance-rate</span>
            <span className={`font-bold ${rateColor(kpi.rate)}`}>{Math.round(kpi.rate * 100)}%</span>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden">
            <div className={`h-full ${rateBar(kpi.rate)} transition-all`} style={{ width: `${Math.round(kpi.rate * 100)}%` }} />
          </div>
          <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
            <span className="text-emerald-500">■ Oppfylt: {kpi.compliant}</span>
            <span className="text-red-500">■ Avvik: {kpi.non_compliant}</span>
            <span className="text-amber-500">■ Delvis: {kpi.partial}</span>
            <span>■ Ikke vurdert: {kpi.not_assessed}</span>
          </div>
        </div>

        {/* Eiendomstabell */}
        <div className="bg-card border border-border rounded-xl overflow-hidden print:border-gray-200">
          <div className="flex items-center gap-3 px-5 py-3 border-b border-border print:border-gray-200 bg-muted/30">
            <span className="text-sm font-semibold">{filteredRegion} — {propCount} eiendommer</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">Laster…</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border print:border-gray-200 text-muted-foreground text-xs uppercase tracking-wide">
                    <th className="text-left px-5 py-3 font-medium">
                      <button onClick={() => toggleSort("name")} className="flex items-center gap-1 hover:text-foreground">
                        Eiendom <SortIcon col="name" />
                      </button>
                    </th>
                    <th className="text-left px-3 py-3 font-medium">Region</th>
                    <th className="text-left px-3 py-3 font-medium">Type</th>
                    <th className="text-center px-3 py-3 font-medium">
                      <button onClick={() => toggleSort("rate")} className="flex items-center gap-1 hover:text-foreground mx-auto">
                        Rate <SortIcon col="rate" />
                      </button>
                    </th>
                    <th className="text-center px-3 py-3 font-medium">Oppfylt</th>
                    <th className="text-center px-3 py-3 font-medium">
                      <button onClick={() => toggleSort("avvik")} className="flex items-center gap-1 hover:text-foreground mx-auto">
                        Avvik <SortIcon col="avvik" />
                      </button>
                    </th>
                    <th className="text-center px-3 py-3 font-medium">Delvis</th>
                    <th className="text-center px-3 py-3 font-medium">Forfalt</th>
                    <th className="text-center px-3 py-3 font-medium print:hidden">Status</th>
                    <th className="text-right px-5 py-3 font-medium print:hidden">Rapport</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {rows.map(row => {
                    const s = row.summary;
                    const rate = s ? s.compliance_rate : 0;
                    const hasData = s && s.total_assignments > 0;
                    return (
                      <tr key={row.property_id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-5 py-3">
                          <Link href={`/fdvu/${row.property_id}`} className="font-medium hover:text-primary transition-colors">
                            {row.name}
                          </Link>
                          {row.address && <div className="text-xs text-muted-foreground">{row.address}</div>}
                        </td>
                        <td className="px-3 py-3 text-muted-foreground text-xs">{row.region ?? "—"}</td>
                        <td className="px-3 py-3 text-muted-foreground text-xs">{row.unit_type_derived ?? "—"}</td>

                        {/* Rate */}
                        <td className="px-3 py-3 text-center">
                          {hasData ? (
                            <div className="flex flex-col items-center gap-1">
                              <span className={`font-bold text-sm ${rateColor(rate)}`}>{Math.round(rate * 100)}%</span>
                              <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                <div className={`h-full ${rateBar(rate)}`} style={{ width: `${Math.round(rate * 100)}%` }} />
                              </div>
                            </div>
                          ) : <span className="text-muted-foreground">—</span>}
                        </td>

                        <td className="px-3 py-3 text-center">
                          {s ? <span className="text-emerald-500 font-medium">{s.compliant}</span> : <span className="text-muted-foreground">—</span>}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {s && s.non_compliant > 0
                            ? <span className="text-red-500 font-bold">{s.non_compliant}</span>
                            : <span className="text-muted-foreground">{s ? "0" : "—"}</span>}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {s ? <span className="text-amber-500">{s.partial}</span> : <span className="text-muted-foreground">—</span>}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {s && s.overdue_reviews > 0
                            ? <span className="text-orange-500 font-medium">{s.overdue_reviews}</span>
                            : <span className="text-muted-foreground">{s ? "0" : "—"}</span>}
                        </td>

                        {/* Status badge */}
                        <td className="px-3 py-3 text-center print:hidden">
                          {hasData ? (
                            <span className={`text-xs px-2 py-0.5 rounded border font-medium
                              ${rate >= 0.9 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : rate >= 0.6 ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-red-500/10 text-red-400 border-red-500/30"}`}>
                              {statusLabel(rate, s?.total_assignments ?? 0)}
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">Ikke startet</span>
                          )}
                        </td>

                        {/* Link til detaljrapport */}
                        <td className="px-5 py-3 text-right print:hidden">
                          <Link href={`/fdvu/${row.property_id}/rapport`}
                            className="text-xs text-primary hover:underline flex items-center gap-1 justify-end">
                            Rapport <ChevronRight size={12} />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Fotnote */}
        <div className="text-xs text-muted-foreground text-center print:text-gray-500 print:mt-8">
          FDVU Compliance-rapport · Bufetat Eiendom · {today} · Konfidensielt dokument
        </div>
      </div>
    </div>
  );
}
