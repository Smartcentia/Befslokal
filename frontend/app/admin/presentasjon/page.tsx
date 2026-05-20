"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, TrendingDown, Minus, Building2, BarChart3,
  Printer, AlertCircle, CheckCircle2, ArrowRight
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "";

interface BudsjettSammenligningRow {
  region: string;
  regn_2025: number;
  befs_2026: number;
  budsjett_2026: number;
  antall_eiendommer: number;
}

interface EiendomRad {
  eiendom: string;
  region: string;
  regn_2025: number;
  befs_2026: number;
  budsjett_2026: number;
  merknad: string | null;
}

interface KpiCard {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "flat";
  color: string;
}

function fmt(n: number): string {
  if (Math.abs(n) >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)} mrd`;
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)} k`;
  return n.toFixed(0);
}

function fmtPst(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)} %`;
}

// Fargeklasser per region (konsistent)
const REGION_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-orange-500", "bg-purple-500",
  "bg-teal-500", "bg-pink-500", "bg-amber-500", "bg-indigo-500",
];

export default function PresentasjonPage() {
  const [regionData, setRegionData] = useState<BudsjettSammenligningRow[]>([]);
  const [eiendommer, setEiendommer] = useState<EiendomRad[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalRegn2025, setTotalRegn2025] = useState(0);
  const [totalBefs2026, setTotalBefs2026] = useState(0);
  const [totalBud2026, setTotalBud2026] = useState(0);
  const [totalEiendommer, setTotalEiendommer] = useState(0);
  const [sok, setSok] = useState("");
  const [filterRegion, setFilterRegion] = useState("Alle");
  const [visEiendommer, setVisEiendommer] = useState(true);

  useEffect(() => {
    const headers = {
      Authorization: `Bearer ${process.env.NEXT_PUBLIC_SHARED_SECRET || "befs-super-secret-key-12345"}`,
      "X-User-Email": "system@befs.no",
      "Content-Type": "application/json",
    };

    const safeJson = (r: Response) => (r.ok ? r.json() : Promise.resolve([]));

    Promise.all([
      fetch(`${API}/api/v1/financials/budsjett-sammenligning-regional`, { headers }).then(safeJson).catch(() => []),
      fetch(`${API}/api/v1/financials/budsjett-sammenligning-eiendommer`, { headers }).then(safeJson).catch(() => []),
    ]).then(([regional, alle]) => {
      const liste = (Array.isArray(regional) ? regional : [])
        .filter((r: BudsjettSammenligningRow) => r.region)
        .sort((a: BudsjettSammenligningRow, b: BudsjettSammenligningRow) => b.regn_2025 - a.regn_2025);

      setRegionData(liste);
      setTotalRegn2025(liste.reduce((s: number, r: BudsjettSammenligningRow) => s + r.regn_2025, 0));
      setTotalBefs2026(liste.reduce((s: number, r: BudsjettSammenligningRow) => s + r.befs_2026, 0));
      setTotalBud2026(liste.reduce((s: number, r: BudsjettSammenligningRow) => s + r.budsjett_2026, 0));
      setTotalEiendommer(liste.reduce((s: number, r: BudsjettSammenligningRow) => s + r.antall_eiendommer, 0));
      setEiendommer(Array.isArray(alle) ? alle : []);
      setLoading(false);
    });
  }, []);

  const vekstBudVsRegn = totalRegn2025 > 0 ? ((totalBud2026 - totalRegn2025) / totalRegn2025) * 100 : 0;
  const vekstBefsVsRegn = totalRegn2025 > 0 ? ((totalBefs2026 - totalRegn2025) / totalRegn2025) * 100 : 0;

  const kpiKort: KpiCard[] = [
    {
      label: "Kontantregnskap 2025 (Øk.)",
      value: fmt(totalRegn2025),
      sub: "Faktiske kostnader fra økonomiavdelingen",
      trend: "flat",
      color: "blue",
    },
    {
      label: "BEFS Prediksjon 2026",
      value: fmt(totalBefs2026),
      sub: `vs. regnskap 2025: ${fmtPst(vekstBefsVsRegn)}`,
      trend: vekstBefsVsRegn > 0 ? "up" : "down",
      color: "orange",
    },
    {
      label: "Budsjett 2026 (Økonomi)",
      value: fmt(totalBud2026),
      sub: `vs. regnskap 2025: ${fmtPst(vekstBudVsRegn)}`,
      trend: vekstBudVsRegn > 0 ? "up" : "down",
      color: "green",
    },
    {
      label: "Antall eiendommer",
      value: totalEiendommer > 0 ? `${totalEiendommer}` : "—",
      sub: "Eiendommer i øk. sammenligning",
      trend: "flat",
      color: "purple",
    },
  ];

  const maxBar = Math.max(...regionData.map((r) => Math.max(r.regn_2025, r.befs_2026, r.budsjett_2026)), 1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 print:bg-white print:from-white print:to-white text-white print:text-gray-900">
      {/* Kontroller (skjules ved print) */}
      <div className="fixed top-4 right-4 flex gap-2 z-50 print:hidden">
        <button
          onClick={() => window.print()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 rounded-lg text-sm"
        >
          <Printer size={14} /> Skriv ut / PDF
        </button>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-12 print:py-6 print:px-0">
        {/* Tittel */}
        <div className="mb-10 print:mb-6">
          <p className="text-xs font-bold tracking-widest text-blue-300 print:text-blue-600 uppercase mb-2">
            Bufetat Eiendomsforvaltning
          </p>
          <h1 className="text-4xl font-bold text-white print:text-gray-900 leading-tight">
            Økonomi, Regnskap og<br />Budsjett 2026
          </h1>
          <p className="text-blue-200 print:text-gray-500 mt-2 text-sm">
            Kontantregnskap 2025 (Øk.) · BEFS Prediksjon 2026 · Budsjett 2026 (Økonomi) · Regional fordeling
            · {new Date().toLocaleDateString("nb-NO", { year: "numeric", month: "long" })}
          </p>
        </div>

        {/* KPI-kort */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 print:gap-3 print:mb-6">
          {kpiKort.map((kpi) => (
            <div
              key={kpi.label}
              className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl p-5 print:p-4 backdrop-blur"
            >
              <p className="text-xs text-blue-200 print:text-gray-400 font-medium mb-1">{kpi.label}</p>
              <p className="text-2xl font-bold text-white print:text-gray-900 tracking-tight">
                {loading ? "…" : kpi.value}
              </p>
              {kpi.sub && (
                <p className="text-xs text-blue-300 print:text-gray-500 mt-1 flex items-center gap-1">
                  {kpi.trend === "up" ? <TrendingUp size={11} className="text-red-300 print:text-red-500" /> :
                   kpi.trend === "down" ? <TrendingDown size={11} className="text-green-300 print:text-green-500" /> :
                   <Minus size={11} />}
                  {kpi.sub}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Hoveddel: tabell + stolpediagram */}
        {loading ? (
          <div className="text-center text-blue-200 py-20">Laster regnskapsdata…</div>
        ) : (
          <>
            {/* Regional oversiktstabell */}
            <div className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl overflow-hidden mb-8 backdrop-blur">
              <div className="px-6 py-4 border-b border-white/10 print:border-gray-200">
                <h2 className="font-bold text-white print:text-gray-900 text-lg flex items-center gap-2">
                  <BarChart3 size={18} className="text-blue-300 print:text-blue-500" />
                  Regional fordeling — regnskap 2025 og budsjett 2026
                </h2>
                <p className="text-xs text-blue-300 print:text-gray-400 mt-1">
                  Kilde: Økonomiavdelingens autoriserte tall (budsjettt2026ver04)
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 print:border-gray-200">
                      <th className="text-left px-6 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Region</th>
                      <th className="text-right px-4 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Regn. 2025 (Øk.)</th>
                      <th className="text-right px-4 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">BEFS Pred. 2026</th>
                      <th className="text-right px-4 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Budsjett 2026 (Øk.)</th>
                      <th className="text-right px-4 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Avvik (BEFS−Øk.)</th>
                      <th className="text-center px-4 py-3 text-xs text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Eiendom.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 print:divide-gray-100">
                    {regionData.map((r, i) => {
                      const avvik = r.befs_2026 - r.budsjett_2026;
                      const avvikPst = r.budsjett_2026 > 0 ? (avvik / r.budsjett_2026) * 100 : 0;
                      const opp = avvik > 0;
                      return (
                        <tr key={r.region} className="hover:bg-white/5 print:hover:bg-gray-50 transition">
                          <td className="px-6 py-3 font-medium text-white print:text-gray-900 flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${REGION_COLORS[i % REGION_COLORS.length]}`} />
                            {r.region}
                          </td>
                          <td className="px-4 py-3 text-right text-blue-100 print:text-gray-700 font-medium">{fmt(r.regn_2025)}</td>
                          <td className="px-4 py-3 text-right text-orange-300 print:text-orange-700">{fmt(r.befs_2026)}</td>
                          <td className="px-4 py-3 text-right text-green-300 print:text-green-700 font-semibold">{fmt(r.budsjett_2026)}</td>
                          <td className="px-4 py-3 text-right">
                            <span className={`text-xs font-bold ${opp ? "text-red-300 print:text-red-600" : "text-green-300 print:text-green-600"}`}>
                              {avvik >= 0 ? "+" : ""}{fmt(avvik)} ({fmtPst(avvikPst)})
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center text-blue-200 print:text-gray-500 text-xs">{r.antall_eiendommer || "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-white/20 print:border-gray-300 bg-white/5 print:bg-gray-50">
                      <td className="px-6 py-3 font-bold text-white print:text-gray-900">Totalt Bufetat</td>
                      <td className="px-4 py-3 text-right font-bold text-blue-100 print:text-gray-700">{fmt(totalRegn2025)}</td>
                      <td className="px-4 py-3 text-right font-bold text-orange-300 print:text-orange-700">{fmt(totalBefs2026)}</td>
                      <td className="px-4 py-3 text-right font-bold text-green-300 print:text-green-700">{fmt(totalBud2026)}</td>
                      <td className="px-4 py-3 text-right">
                        {(() => {
                          const totAvvik = totalBefs2026 - totalBud2026;
                          const totAvvikPst = totalBud2026 > 0 ? (totAvvik / totalBud2026) * 100 : 0;
                          return (
                            <span className={`text-sm font-bold ${totAvvik > 0 ? "text-red-300 print:text-red-600" : "text-green-300 print:text-green-600"}`}>
                              {totAvvik >= 0 ? "+" : ""}{fmt(totAvvik)} ({fmtPst(totAvvikPst)})
                            </span>
                          );
                        })()}
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-blue-200 print:text-gray-600">{totalEiendommer > 0 ? totalEiendommer : "—"}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Stolpediagram */}
            <div className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl p-6 mb-8 backdrop-blur">
              <h2 className="font-bold text-white print:text-gray-900 mb-5 text-base">
                Kostnadsbilde per region — Regn. 2025 / BEFS pred. / Budsjett 2026
              </h2>
              <div className="space-y-4">
                {regionData.slice(0, 10).map((r, i) => {
                  const w25 = (r.regn_2025 / maxBar) * 100;
                  const wb = (r.befs_2026 / maxBar) * 100;
                  const w26 = (r.budsjett_2026 / maxBar) * 100;
                  return (
                    <div key={r.region}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-blue-100 print:text-gray-700 font-medium w-28 truncate">{r.region}</span>
                        <span className="text-xs text-blue-200 print:text-gray-400">{fmt(r.regn_2025)} → {fmt(r.budsjett_2026)}</span>
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-blue-300 print:text-gray-400 w-12">Regn.25</span>
                          <div className="flex-1 bg-white/10 print:bg-gray-100 rounded-full h-2.5">
                            <div className={`h-2.5 rounded-full ${REGION_COLORS[i % REGION_COLORS.length]} opacity-50`} style={{ width: `${w25}%` }} />
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-orange-300 print:text-orange-600 w-12">BEFS</span>
                          <div className="flex-1 bg-white/10 print:bg-gray-100 rounded-full h-2.5">
                            <div className="h-2.5 rounded-full bg-orange-400 opacity-70" style={{ width: `${wb}%` }} />
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-green-300 print:text-green-600 w-12">Bud.26</span>
                          <div className="flex-1 bg-white/10 print:bg-gray-100 rounded-full h-2.5">
                            <div className={`h-2.5 rounded-full ${REGION_COLORS[i % REGION_COLORS.length]}`} style={{ width: `${w26}%` }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center gap-6 mt-4 pt-4 border-t border-white/10 print:border-gray-200 text-xs text-blue-200 print:text-gray-400">
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-white/30 print:bg-gray-300 inline-block" /> Regn. 2025 (Øk.)</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-orange-400 inline-block" /> BEFS Prediksjon 2026</span>
                <span className="flex items-center gap-1"><span className="w-3 h-2 rounded bg-blue-400 inline-block" /> Budsjett 2026 (Øk.)</span>
              </div>
            </div>

            {/* Nøkkelpunkter */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8 print:grid-cols-2">
              <div className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl p-5 backdrop-blur">
                <h3 className="font-bold text-white print:text-gray-900 mb-3 flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-green-300 print:text-green-600" />
                  Hva viser tallene
                </h3>
                <ul className="space-y-2 text-sm text-blue-100 print:text-gray-700">
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-blue-300" />Regn. 2025 (Øk.) er økonomiavdelingens kontante regnskapsdata for 2025</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-blue-300" />BEFS Prediksjon 2026 er BEFS egne modellbaserte estimater (kontant 2025 × regional KPI)</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-blue-300" />Budsjett 2026 (Øk.) er økonomiavdelingens vedtatte budsjett for 2026</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-blue-300" />Avvik = BEFS prediksjon minus Øk. budsjett — viser presisjon i BEFS-modellen</li>
                </ul>
              </div>
              <div className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl p-5 backdrop-blur">
                <h3 className="font-bold text-white print:text-gray-900 mb-3 flex items-center gap-2">
                  <AlertCircle size={16} className="text-amber-300 print:text-amber-600" />
                  Viktige merknader
                </h3>
                <ul className="space-y-2 text-sm text-blue-100 print:text-gray-700">
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-amber-300" />Kilde for alle tall: budsjettt2026ver04 (autorisert av økonomiavdelingen)</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-amber-300" />Alle 211 eiendommer er inkludert, inkl. Nasjonal og Bufdir</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-amber-300" />FDVU-kostnader er underrapportert inntil vurderingsprosessen er fullført</li>
                  <li className="flex items-start gap-2"><ArrowRight size={14} className="mt-0.5 flex-shrink-0 text-amber-300" />Avviksoppfølging mot budsjett gjøres månedlig i BEFS</li>
                </ul>
              </div>
            </div>
          </>
        )}

        {/* Alle eiendommer — full tabell */}
        {!loading && eiendommer.length > 0 && (
          <div className="bg-white/10 print:bg-white border border-white/20 print:border-gray-200 rounded-2xl overflow-hidden mb-8 backdrop-blur">
            <div
              className="px-6 py-4 border-b border-white/10 print:border-gray-200 flex items-center justify-between cursor-pointer select-none"
              onClick={() => setVisEiendommer((v) => !v)}
            >
              <div>
                <h2 className="font-bold text-white print:text-gray-900 text-lg flex items-center gap-2">
                  <BarChart3 size={18} className="text-blue-300 print:text-blue-500" />
                  Alle eiendommer — økonomiavdelingens tall
                  <span className="text-xs font-normal text-blue-300 print:text-gray-400 ml-2">({eiendommer.length} stk)</span>
                </h2>
                <p className="text-xs text-blue-300 print:text-gray-400 mt-1">
                  Regn. 2025 (Øk.) · BEFS Prediksjon 2026 · Budsjett 2026 (Økonomi)
                </p>
              </div>
              <span className="text-blue-300 print:hidden text-sm">{visEiendommer ? "▲ Skjul" : "▼ Vis"}</span>
            </div>

            {visEiendommer && (
              <>
                {/* Søk og filter */}
                <div className="px-6 py-3 flex flex-wrap gap-3 border-b border-white/10 print:border-gray-200 print:hidden">
                  <input
                    type="text"
                    placeholder="Søk eiendom…"
                    value={sok}
                    onChange={(e) => setSok(e.target.value)}
                    className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white placeholder-blue-300 outline-none focus:border-blue-400 w-56"
                  />
                  <select
                    value={filterRegion}
                    onChange={(e) => setFilterRegion(e.target.value)}
                    className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white outline-none focus:border-blue-400"
                  >
                    <option value="Alle">Alle regioner</option>
                    {Array.from(new Set(eiendommer.map((e) => e.region))).sort().map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/10 print:border-gray-200 bg-white/5 print:bg-gray-50">
                        <th className="text-left px-4 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Eiendom</th>
                        <th className="text-left px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Region</th>
                        <th className="text-right px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Regn. 2025 (Øk.)</th>
                        <th className="text-right px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">BEFS Pred. 2026</th>
                        <th className="text-right px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Budsjett 2026 (Øk.)</th>
                        <th className="text-right px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider">Avvik</th>
                        <th className="text-left px-3 py-2.5 text-blue-200 print:text-gray-400 font-semibold uppercase tracking-wider print:hidden">Merknad</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 print:divide-gray-100">
                      {eiendommer
                        .filter((e) => {
                          const matchSok = !sok || e.eiendom.toLowerCase().includes(sok.toLowerCase());
                          const matchRegion = filterRegion === "Alle" || e.region === filterRegion;
                          return matchSok && matchRegion;
                        })
                        .map((e, i) => {
                          const avvik = e.befs_2026 - e.budsjett_2026;
                          return (
                            <tr key={i} className="hover:bg-white/5 print:hover:bg-gray-50 transition">
                              <td className="px-4 py-2 text-white print:text-gray-900 font-medium max-w-xs truncate">{e.eiendom}</td>
                              <td className="px-3 py-2 text-blue-300 print:text-gray-500">{e.region}</td>
                              <td className="px-3 py-2 text-right text-blue-100 print:text-gray-700">{e.regn_2025 > 0 ? fmt(e.regn_2025) : "—"}</td>
                              <td className="px-3 py-2 text-right text-orange-300 print:text-orange-700">{e.befs_2026 > 0 ? fmt(e.befs_2026) : "—"}</td>
                              <td className="px-3 py-2 text-right text-green-300 print:text-green-700 font-semibold">{e.budsjett_2026 > 0 ? fmt(e.budsjett_2026) : "—"}</td>
                              <td className="px-3 py-2 text-right">
                                {(e.befs_2026 > 0 || e.budsjett_2026 > 0) ? (
                                  <span className={`font-medium ${avvik > 0 ? "text-red-300 print:text-red-600" : "text-green-300 print:text-green-600"}`}>
                                    {avvik >= 0 ? "+" : ""}{fmt(avvik)}
                                  </span>
                                ) : "—"}
                              </td>
                              <td className="px-3 py-2 text-blue-200 print:text-gray-400 max-w-xs truncate print:hidden">{e.merknad || ""}</td>
                            </tr>
                          );
                        })}
                    </tbody>
                    <tfoot>
                      {(() => {
                        const filtrert = eiendommer.filter((e) => {
                          const matchSok = !sok || e.eiendom.toLowerCase().includes(sok.toLowerCase());
                          const matchRegion = filterRegion === "Alle" || e.region === filterRegion;
                          return matchSok && matchRegion;
                        });
                        const sumR = filtrert.reduce((s, e) => s + e.regn_2025, 0);
                        const sumB = filtrert.reduce((s, e) => s + e.befs_2026, 0);
                        const sumO = filtrert.reduce((s, e) => s + e.budsjett_2026, 0);
                        return (
                          <tr className="border-t-2 border-white/20 print:border-gray-300 bg-white/5 print:bg-gray-50">
                            <td className="px-4 py-2.5 font-bold text-white print:text-gray-900" colSpan={2}>
                              Totalt ({filtrert.length} eiendommer)
                            </td>
                            <td className="px-3 py-2.5 text-right font-bold text-blue-100 print:text-gray-700">{fmt(sumR)}</td>
                            <td className="px-3 py-2.5 text-right font-bold text-orange-300 print:text-orange-700">{fmt(sumB)}</td>
                            <td className="px-3 py-2.5 text-right font-bold text-green-300 print:text-green-700">{fmt(sumO)}</td>
                            <td className="px-3 py-2.5 text-right font-bold">
                              <span className={`${sumB - sumO > 0 ? "text-red-300 print:text-red-600" : "text-green-300 print:text-green-600"}`}>
                                {sumB - sumO >= 0 ? "+" : ""}{fmt(sumB - sumO)}
                              </span>
                            </td>
                            <td className="print:hidden" />
                          </tr>
                        );
                      })()}
                    </tfoot>
                  </table>
                </div>
              </>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-blue-300 print:text-gray-400 pt-4 border-t border-white/10 print:border-gray-200">
          Bufetat Eiendomsforvaltningssystem (BEFS) · Økonomi og regnskap · Konfidensielt
          · {new Date().toLocaleDateString("nb-NO")}
        </div>
      </div>
    </div>
  );
}
