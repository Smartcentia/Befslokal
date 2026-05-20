"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { fetchAPI } from "@/lib/api/client";

// ── Typer ────────────────────────────────────────────────────────────────────

interface Eiendom {
  property_id: string;
  navn: string;
  region: string;
  lokaler_gl: number;
  drift_gl: number;
  vedlikehold_gl: number;
  gjennomstromning_gl: number;
  sum_gl: number;
  lokaler_pred: number;
  drift_pred: number;
  vedlikehold_pred: number;
  sum_pred: number;
  endring_pst: number | null;
  har_prediksjon: boolean;
}

interface RegionRow {
  region: string;
  lokaler_gl: number;
  drift_gl: number;
  vedlikehold_gl: number;
  sum_gl: number;
  lokaler_pred: number;
  drift_pred: number;
  vedlikehold_pred: number;
  sum_pred: number;
  endring_pst: number | null;
}

interface Totaler {
  lokaler_gl: number;
  drift_gl: number;
  vedlikehold_gl: number;
  gjennomstromning_gl: number;
  sum_gl: number;
  lokaler_pred: number;
  drift_pred: number;
  vedlikehold_pred: number;
  sum_pred: number;
  endring_pst: number | null;
}

interface DashboardData {
  scenario: string;
  region_filter: string | null;
  antall_eiendommer_gl: number;
  antall_eiendommer_pred: number;
  totaler: Totaler;
  per_region: RegionRow[];
  per_eiendom: Eiendom[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtKr(n: number) {
  return new Intl.NumberFormat("no-NO", {
    style: "currency",
    currency: "NOK",
    maximumFractionDigits: 0,
  }).format(n);
}

function fmtMNOK(n: number) {
  return (n / 1_000_000).toLocaleString("no-NO", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " MNOK";
}

function EndringBadge({ pst }: { pst: number | null }) {
  if (pst === null) return <span className="text-gray-400 text-xs">—</span>;
  const pos = pst >= 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded ${
      pos ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"
    }`}>
      {pos ? "▲" : "▼"} {Math.abs(pst).toFixed(1)}%
    </span>
  );
}

function SortIcon({ col, sort }: { col: string; sort: { col: string; asc: boolean } }) {
  if (sort.col !== col) return <span className="text-gray-300 ml-1">⇅</span>;
  return <span className="ml-1">{sort.asc ? "▲" : "▼"}</span>;
}

// ── Kategorikort ─────────────────────────────────────────────────────────────

function KatKort({
  label,
  beskrivelse,
  gl,
  pred,
  color,
}: {
  label: string;
  beskrivelse: string;
  gl: number;
  pred: number;
  color: string;
}) {
  const endring = gl > 0 ? ((pred / gl - 1) * 100) : null;
  return (
    <div className={`bg-white rounded-xl border-l-4 ${color} border border-gray-200 shadow-sm p-5`}>
      <p className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-0.5">{label}</p>
      <p className="text-xs text-gray-400 mb-3">{beskrivelse}</p>
      <div className="flex justify-between items-end">
        <div>
          <p className="text-xs text-gray-400">GL 2025</p>
          <p className="text-lg font-bold text-gray-900">{fmtMNOK(gl)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Prediksjon 2027</p>
          <p className="text-lg font-bold text-gray-700">{pred > 0 ? fmtMNOK(pred) : "—"}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Endring</p>
          <EndringBadge pst={endring !== null ? Math.round(endring * 10) / 10 : null} />
        </div>
      </div>
    </div>
  );
}

// ── Hovedside ─────────────────────────────────────────────────────────────────

const ALLE_REGIONER = ["Bufdir", "Midt-Norge", "Nord", "Sør", "Vest", "Øst"];

export default function KostnadsinndeligDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<"xgb70" | "xgb50">("xgb70");
  const [region, setRegion] = useState("");
  const [søk, setSøk] = useState("");
  const [visning, setVisning] = useState<"region" | "eiendom">("region");
  const [sort, setSort] = useState<{ col: string; asc: boolean }>({ col: "sum_gl", asc: false });

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ scenario });
    if (region) params.set("region", region);
    fetchAPI<DashboardData>(`/financials/kostnadsinndeling-dashboard?${params}`)
      .then((d) => { if (!cancelled) { setData(d); setLoading(false); } })
      .catch((e) => { if (!cancelled) { setError(String(e)); setLoading(false); } });
    return () => { cancelled = true; };
  }, [scenario, region]);

  const filtrertEiendommer = useMemo(() => {
    if (!data) return [];
    let rows = data.per_eiendom;
    if (søk) {
      const q = søk.toLowerCase();
      rows = rows.filter((e) => e.navn.toLowerCase().includes(q) || e.region.toLowerCase().includes(q));
    }
    rows = [...rows].sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[sort.col];
      const bv = (b as unknown as Record<string, unknown>)[sort.col];
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      return sort.asc
        ? (av as number) < (bv as number) ? -1 : 1
        : (av as number) > (bv as number) ? -1 : 1;
    });
    return rows;
  }, [data, søk, sort]);

  function toggleSort(col: string) {
    setSort((s) => s.col === col ? { col, asc: !s.asc } : { col, asc: false });
  }

  const tot = data?.totaler;

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-8 space-y-6">
      {/* Topp */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-gray-400 mb-1">
            <Link href="/financials/prediksjon" className="hover:text-blue-600">Prediksjon 2027</Link>
            <span>›</span>
            <span className="text-gray-700 font-medium">Kostnadsinndeling</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Kostnadsinndeling 2027</h1>
          <p className="text-sm text-gray-500 mt-1">
            Bufdirs 3 offisielle kategorier — GL 2025 faktisk vs. Holt-Winters prediksjon 2027
          </p>
        </div>
        <Link
          href="/financials/prediksjon"
          className="text-sm text-blue-600 hover:underline"
        >
          ← Tilbake
        </Link>
      </div>

      {/* Kontrollpanel */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Scenario</label>
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {(["xgb70", "xgb50"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setScenario(s)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  scenario === s
                    ? "bg-blue-600 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {s === "xgb70" ? "XGB Gulv 70%" : "XGB Gulv 50%"}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Region</label>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Alle regioner</option>
            {ALLE_REGIONER.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Visning</label>
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {(["region", "eiendom"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setVisning(v)}
                className={`px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  visning === v
                    ? "bg-gray-800 text-white"
                    : "bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {v === "region" ? "Per region" : "Per eiendom"}
              </button>
            ))}
          </div>
        </div>
        {visning === "eiendom" && (
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-semibold text-gray-500 mb-1">Søk eiendom</label>
            <input
              value={søk}
              onChange={(e) => setSøk(e.target.value)}
              placeholder="Navn eller region…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        )}
      </div>

      {loading && (
        <div className="text-center py-16 text-gray-400 text-sm">Laster data…</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          Feil: {error}
        </div>
      )}

      {data && tot && (
        <>
          {/* Sammendragskort */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <KatKort
              label="Utgifter til lokaler"
              beskrivelse="Husleie, fellesutgifter, parkering"
              gl={tot.lokaler_gl}
              pred={tot.lokaler_pred}
              color="border-blue-500"
            />
            <KatKort
              label="Driftsutgifter"
              beskrivelse="Strøm, renhold, vakthold, renovasjon"
              gl={tot.drift_gl}
              pred={tot.drift_pred}
              color="border-green-500"
            />
            <KatKort
              label="Vedlikehold og utvikling"
              beskrivelse="Reparasjon, påkostning, oppgradering"
              gl={tot.vedlikehold_gl}
              pred={tot.vedlikehold_pred}
              color="border-yellow-500"
            />
          </div>

          {/* Totalkort */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Sum driftskostnader GL 2025</p>
              <p className="text-xl font-bold text-gray-900">{fmtMNOK(tot.sum_gl)}</p>
              <p className="text-xs text-gray-400">{data.antall_eiendommer_gl} eiendommer</p>
            </div>
            <div className="bg-white rounded-xl border border-blue-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-blue-600 uppercase mb-1">Prediksjon 2027 ({scenario.toUpperCase()})</p>
              <p className="text-xl font-bold text-blue-900">{fmtMNOK(tot.sum_pred)}</p>
              <p className="text-xs text-blue-400">{data.antall_eiendommer_pred} eiendommer</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Endring 2025→2027</p>
              <div className="mt-1"><EndringBadge pst={tot.endring_pst} /></div>
              <p className="text-xs text-gray-400 mt-1">{fmtKr((tot.sum_pred || 0) - (tot.sum_gl || 0))}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Gjennomstrømning GL 2025</p>
              <p className="text-xl font-bold text-gray-700">{fmtMNOK(tot.gjennomstromning_gl)}</p>
              <p className="text-xs text-gray-400">Omposteringer (ikke i sum)</p>
            </div>
          </div>

          {/* Per region */}
          {visning === "region" && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h2 className="text-sm font-bold text-gray-700">Per region</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500">
                      <th className="px-4 py-2.5 text-left">Region</th>
                      <th className="px-4 py-2.5 text-right">Lokaler GL 25</th>
                      <th className="px-4 py-2.5 text-right">Drift GL 25</th>
                      <th className="px-4 py-2.5 text-right">Vedlikehold GL 25</th>
                      <th className="px-4 py-2.5 text-right font-bold">Sum GL 25</th>
                      <th className="px-4 py-2.5 text-right text-blue-600">Lok pred 27</th>
                      <th className="px-4 py-2.5 text-right text-blue-600">Drift pred 27</th>
                      <th className="px-4 py-2.5 text-right text-blue-600">Ved pred 27</th>
                      <th className="px-4 py-2.5 text-right text-blue-600 font-bold">Sum pred 27</th>
                      <th className="px-4 py-2.5 text-right">Endring</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.per_region.map((r) => (
                      <tr key={r.region} className="hover:bg-gray-50">
                        <td className="px-4 py-2.5 font-medium text-gray-900">{r.region}</td>
                        <td className="px-4 py-2.5 text-right text-gray-600">{fmtMNOK(r.lokaler_gl)}</td>
                        <td className="px-4 py-2.5 text-right text-gray-600">{fmtMNOK(r.drift_gl)}</td>
                        <td className="px-4 py-2.5 text-right text-gray-600">{fmtMNOK(r.vedlikehold_gl)}</td>
                        <td className="px-4 py-2.5 text-right font-semibold text-gray-900">{fmtMNOK(r.sum_gl)}</td>
                        <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(r.lokaler_pred)}</td>
                        <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(r.drift_pred)}</td>
                        <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(r.vedlikehold_pred)}</td>
                        <td className="px-4 py-2.5 text-right font-semibold text-blue-900">{fmtMNOK(r.sum_pred)}</td>
                        <td className="px-4 py-2.5 text-right"><EndringBadge pst={r.endring_pst} /></td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 border-t-2 border-gray-300 font-bold">
                      <td className="px-4 py-2.5 text-gray-900">TOTALT</td>
                      <td className="px-4 py-2.5 text-right">{fmtMNOK(tot.lokaler_gl)}</td>
                      <td className="px-4 py-2.5 text-right">{fmtMNOK(tot.drift_gl)}</td>
                      <td className="px-4 py-2.5 text-right">{fmtMNOK(tot.vedlikehold_gl)}</td>
                      <td className="px-4 py-2.5 text-right text-gray-900">{fmtMNOK(tot.sum_gl)}</td>
                      <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(tot.lokaler_pred)}</td>
                      <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(tot.drift_pred)}</td>
                      <td className="px-4 py-2.5 text-right text-blue-700">{fmtMNOK(tot.vedlikehold_pred)}</td>
                      <td className="px-4 py-2.5 text-right text-blue-900">{fmtMNOK(tot.sum_pred)}</td>
                      <td className="px-4 py-2.5 text-right"><EndringBadge pst={tot.endring_pst} /></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          {/* Per eiendom */}
          {visning === "eiendom" && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-sm font-bold text-gray-700">
                  Per eiendom — {filtrertEiendommer.length} eiendommer
                </h2>
                <p className="text-xs text-gray-400">Klikk kolonneoverskrift for å sortere</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500">
                      <th className="px-4 py-2.5 text-left">Eiendom</th>
                      <th className="px-4 py-2.5 text-left">Region</th>
                      {[
                        ["lokaler_gl", "Lokaler GL"],
                        ["drift_gl", "Drift GL"],
                        ["vedlikehold_gl", "Vedlikehold GL"],
                        ["sum_gl", "Sum GL 25"],
                        ["lokaler_pred", "Lok pred 27"],
                        ["drift_pred", "Drift pred 27"],
                        ["vedlikehold_pred", "Ved pred 27"],
                        ["sum_pred", "Sum pred 27"],
                        ["endring_pst", "Endring"],
                      ].map(([col, label]) => (
                        <th
                          key={col}
                          className="px-4 py-2.5 text-right cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap"
                          onClick={() => toggleSort(col)}
                        >
                          {label}
                          <SortIcon col={col} sort={sort} />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filtrertEiendommer.map((e) => (
                      <tr key={e.property_id} className={`hover:bg-gray-50 ${!e.har_prediksjon ? "opacity-60" : ""}`}>
                        <td className="px-4 py-2 font-medium text-gray-900 max-w-[240px] truncate" title={e.navn}>{e.navn}</td>
                        <td className="px-4 py-2 text-gray-500 text-xs">{e.region}</td>
                        <td className="px-4 py-2 text-right text-gray-600">{e.lokaler_gl > 0 ? fmtMNOK(e.lokaler_gl) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right text-gray-600">{e.drift_gl > 0 ? fmtMNOK(e.drift_gl) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right text-gray-600">{e.vedlikehold_gl > 0 ? fmtMNOK(e.vedlikehold_gl) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right font-semibold text-gray-900">{fmtMNOK(e.sum_gl)}</td>
                        <td className="px-4 py-2 text-right text-blue-700">{e.lokaler_pred > 0 ? fmtMNOK(e.lokaler_pred) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right text-blue-700">{e.drift_pred > 0 ? fmtMNOK(e.drift_pred) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right text-blue-700">{e.vedlikehold_pred > 0 ? fmtMNOK(e.vedlikehold_pred) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right font-semibold text-blue-900">{e.sum_pred > 0 ? fmtMNOK(e.sum_pred) : <span className="text-gray-300">—</span>}</td>
                        <td className="px-4 py-2 text-right"><EndringBadge pst={e.endring_pst} /></td>
                      </tr>
                    ))}
                    {filtrertEiendommer.length === 0 && (
                      <tr>
                        <td colSpan={11} className="px-4 py-8 text-center text-gray-400">Ingen eiendommer funnet</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400">
            Kategorier jf. Bufdirs besluttede inndeling (e-post Øystein Møller Frich 22.04.2026).
            Predikasjon: Holt-Winters {scenario.toUpperCase()} · Inflasjon: 7% (2×3,5% SSB 2025→2027).
            Gjennomstrømning (omposteringer) inngår ikke i sum driftskostnader.
          </p>
        </>
      )}
    </div>
  );
}
