"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api/client";

type SrsKategori = { kategori: string; ar: number; antall: number; total_belop: number };
type KoststedDekning = { totalt: number; koblet: number; ukoblet: number; prosent: number };
type KoststedUkobletRad = {
  koststed_kode: string;
  koststed_navn: string;
  region: string;
  eksempel_adresse: string;
  gl_antall_ar: number;
  gl_belop_ar: number;
  gl_antall_alle: number;
};
type KoststedUkoblet = { ar: number; antall: number; rader: KoststedUkobletRad[] };
type Leie = { konto: string; konto_navn: string; belop: number; antall: number; type: string };
type Anlegg = { totalt: number; aktive: number; total_bokfort: number; status: string };
type GlAr = Record<string, { antall: number; belop: number }>;
type Compliance = { kode: string; beskrivelse: string; status: string; detalj: string };

interface SrsRapport {
  ar: number;
  srs_kategorier: SrsKategori[];
  koststed_dekning: KoststedDekning;
  srs_13_leie: Leie[];
  srs_17_anlegg: Anlegg;
  gl_dette_ar: GlAr;
  compliance: Compliance[];
}

function fmtKr(n: number) {
  return new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);
}

function fmtN(n: number) {
  return new Intl.NumberFormat("nb-NO").format(n);
}

/** Excel-vennlig CSV (UTF-8 med BOM), anførsel rundt felt med komma/linjeskift. */
function escapeCsvCell(value: string | number): string {
  const s = String(value ?? "");
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function downloadKoststedUkobletCsv(payload: KoststedUkoblet) {
  const ar = payload.ar;
  const header = [
    "koststed_kode",
    "koststed_navn",
    "region",
    "eksempel_adresse",
    `gl_antall_${ar}`,
    `gl_belop_${ar}`,
    "gl_antall_alle",
  ];
  const lines = [
    header.map(escapeCsvCell).join(","),
    ...payload.rader.map((r) =>
      [
        r.koststed_kode,
        r.koststed_navn,
        r.region,
        r.eksempel_adresse,
        r.gl_antall_ar,
        r.gl_belop_ar,
        r.gl_antall_alle,
      ]
        .map(escapeCsvCell)
        .join(","),
    ),
  ];
  const csv = "\uFEFF" + lines.join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `befs-koststed-ukoblet-${ar}.csv`;
  a.rel = "noopener";
  a.click();
  URL.revokeObjectURL(url);
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    ok:       { label: "OK", cls: "bg-green-100 text-green-800 border border-green-300" },
    delvis:   { label: "Delvis", cls: "bg-yellow-100 text-yellow-800 border border-yellow-300" },
    pending:  { label: "Planlagt", cls: "bg-blue-100 text-blue-800 border border-blue-300" },
    mangler:  { label: "Mangler", cls: "bg-red-100 text-red-800 border border-red-300" },
    ikke_befolket: { label: "Ikke startet", cls: "bg-gray-100 text-gray-600 border border-gray-300" },
  };
  const s = map[status] ?? { label: status, cls: "bg-gray-100 text-gray-600 border border-gray-300" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${s.cls}`}>
      {s.label}
    </span>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "ok")      return <span className="text-green-500 text-xl">✓</span>;
  if (status === "delvis")  return <span className="text-yellow-500 text-xl">◑</span>;
  if (status === "pending") return <span className="text-blue-500 text-xl">⏳</span>;
  return <span className="text-red-500 text-xl">✗</span>;
}

const KATEGORI_COLORS: Record<string, string> = {
  Drift:           "bg-blue-50 text-blue-900",
  Investering:     "bg-purple-50 text-purple-900",
  Gjennomstrømning:"bg-orange-50 text-orange-900",
  Ukjent:          "bg-gray-50 text-gray-600",
};

export default function SrsRapportPage() {
  const [ar, setAr] = useState(2025);
  const [data, setData] = useState<SrsRapport | null>(null);
  const [koststedUkoblet, setKoststedUkoblet] = useState<KoststedUkoblet | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function hent(valgtAr: number) {
    setLoading(true);
    setError(null);
    try {
      const [rapport, ukoblet] = await Promise.all([
        fetchAPI<SrsRapport>(`/financials/srs-rapport?ar=${valgtAr}`),
        fetchAPI<KoststedUkoblet>(`/financials/koststed-ukoblet?ar=${valgtAr}`),
      ]);
      setData(rapport);
      setKoststedUkoblet(ukoblet);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ukjent feil");
      setData(null);
      setKoststedUkoblet(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { hent(ar); }, [ar]);

  // Aggreger kategorier for valgt år
  const katDetteAr = data?.srs_kategorier.filter(k => k.ar === ar) ?? [];
  const totalBelop = katDetteAr.reduce((s, k) => s + k.total_belop, 0);
  const totalAntall = katDetteAr.reduce((s, k) => s + k.antall, 0);

  // Alle år tilgjengelig
  const alleAr = [...new Set(data?.srs_kategorier.map(k => k.ar) ?? [])].sort((a, b) => b - a);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4 print:mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">SRS-samsvarrapport</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Statlig Regnskapsstandard — dokumentasjon for regnskapsavdelingen
          </p>
        </div>
        <div className="flex items-center gap-3 print:hidden">
          <label className="text-sm font-medium text-gray-700">År:</label>
          <select
            value={ar}
            onChange={e => setAr(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white text-gray-900 shadow-sm"
          >
            {[2025, 2024, 2023, 2022, 2021].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button
            onClick={() => window.print()}
            className="px-4 py-1.5 text-sm bg-gray-800 text-white rounded-md hover:bg-gray-700"
          >
            Skriv ut / PDF
          </button>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">{error}</div>
      )}

      {data && !loading && (
        <div className="space-y-6">

          {/* ── 1. Compliance-sjekkliste ────────────────────────────────── */}
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">SRS-samsvarsstatus</h2>
              <p className="text-xs text-gray-500 mt-0.5">Oversikt over oppfylte og planlagte krav</p>
            </div>
            <div className="divide-y divide-gray-100">
              {data.compliance.map((c) => (
                <div key={c.kode} className="px-6 py-4 flex items-start gap-4">
                  <div className="mt-0.5 shrink-0">
                    <StatusIcon status={c.status} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-0.5">
                      <span className="font-semibold text-sm text-gray-900">{c.kode}</span>
                      <StatusBadge status={c.status} />
                    </div>
                    <p className="text-sm text-gray-600">{c.beskrivelse}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{c.detalj}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ── 2. SRS-kategorier for valgt år ─────────────────────────── */}
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">SRS-kategorisering {ar}</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                {fmtN(totalAntall)} transaksjoner — total: {fmtKr(totalBelop)}
              </p>
            </div>
            <div className="p-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {katDetteAr.map((k) => {
                const pst = totalBelop > 0 ? (k.total_belop / totalBelop * 100).toFixed(1) : "0";
                return (
                  <div key={k.kategori} className={`rounded-lg p-4 ${KATEGORI_COLORS[k.kategori] ?? "bg-gray-50"}`}>
                    <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{k.kategori}</p>
                    <p className="text-2xl font-bold mt-1">{fmtKr(k.total_belop)}</p>
                    <p className="text-sm opacity-70 mt-1">{fmtN(k.antall)} transaksjoner · {pst}%</p>
                  </div>
                );
              })}
              {katDetteAr.length === 0 && (
                <p className="text-sm text-gray-400 col-span-3">Ingen GL-data for {ar}</p>
              )}
            </div>

            {/* Historikk-tabell */}
            {alleAr.length > 1 && (
              <div className="border-t border-gray-100 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left">
                      <th className="px-4 py-2 font-semibold text-gray-600">År</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Kategori</th>
                      <th className="px-4 py-2 font-semibold text-gray-600 text-right">Antall</th>
                      <th className="px-4 py-2 font-semibold text-gray-600 text-right">Beløp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.srs_kategorier.map((k, i) => (
                      <tr key={i} className={k.ar === ar ? "bg-blue-50" : "hover:bg-gray-50"}>
                        <td className="px-4 py-2 text-gray-700 font-medium">{k.ar}</td>
                        <td className="px-4 py-2 text-gray-700">{k.kategori}</td>
                        <td className="px-4 py-2 text-right text-gray-600">{fmtN(k.antall)}</td>
                        <td className="px-4 py-2 text-right text-gray-800 font-medium">{fmtKr(k.total_belop)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* ── 3. Koststed-dekning ────────────────────────────────────── */}
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">Koststed-dekning (Dim1 → eiendom)</h2>
              <p className="text-xs text-gray-500 mt-0.5">Sporbarhet fra GL-transaksjoner til BEFS-eiendommer</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-3xl font-bold text-gray-900">{data.koststed_dekning.totalt}</p>
                  <p className="text-xs text-gray-500 mt-1">Totalt koststed</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">{data.koststed_dekning.koblet}</p>
                  <p className="text-xs text-gray-500 mt-1">Koblet til eiendom</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-orange-500">{data.koststed_dekning.ukoblet}</p>
                  <p className="text-xs text-gray-500 mt-1">Ikke koblet</p>
                </div>
              </div>
              {/* Progress bar */}
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all"
                  style={{ width: `${data.koststed_dekning.prosent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1.5 text-right">
                {data.koststed_dekning.prosent}% dekningsgrad
              </p>
            </div>
          </section>

          {/* ── 3b. Ukoblede koststed (detaljliste) ─────────────────────── */}
          {koststedUkoblet && koststedUkoblet.antall > 0 && (
            <section className="bg-white rounded-xl border border-amber-200 shadow-sm overflow-hidden print:break-inside-avoid">
              <div className="px-6 py-4 border-b border-amber-100 bg-amber-50/80 flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h2 className="text-base font-semibold text-gray-900">Ukoblede koststed (Dim1)</h2>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {fmtN(koststedUkoblet.antall)} rader i <code className="text-xs bg-white/80 px-1 rounded">koststed_mapping</code> uten{" "}
                    <code className="text-xs bg-white/80 px-1 rounded">property_id</code> — sortert etter GL-beløp for {koststedUkoblet.ar}.{" "}
                    Kjør script <code className="text-xs bg-white/80 px-1 rounded">backend/scripts/suggest_koststed_property_mapping.py</code> eller
                    admin <code className="text-xs bg-white/80 px-1 rounded">link-koststed-properties</code> for automatikk.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => downloadKoststedUkobletCsv(koststedUkoblet)}
                  className="shrink-0 px-3 py-1.5 text-sm font-medium rounded-md border border-amber-300 bg-white text-amber-900 hover:bg-amber-100 print:hidden"
                >
                  Last ned CSV
                </button>
              </div>
              <div className="overflow-x-auto max-h-[min(28rem,70vh)] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-50 z-10">
                    <tr className="text-left">
                      <th className="px-4 py-2 font-semibold text-gray-600">Kode</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Navn</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Region</th>
                      <th className="px-4 py-2 font-semibold text-gray-600">Eksempeladresse</th>
                      <th className="px-4 py-2 font-semibold text-gray-600 text-right">Antall GL {koststedUkoblet.ar}</th>
                      <th className="px-4 py-2 font-semibold text-gray-600 text-right">Beløp {koststedUkoblet.ar}</th>
                      <th className="px-4 py-2 font-semibold text-gray-600 text-right">Antall GL (alle år)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {koststedUkoblet.rader.map((row) => (
                      <tr key={row.koststed_kode} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-mono text-gray-800 whitespace-nowrap">{row.koststed_kode}</td>
                        <td className="px-4 py-2 text-gray-700 max-w-[14rem] sm:max-w-md truncate" title={row.koststed_navn}>
                          {row.koststed_navn || "—"}
                        </td>
                        <td className="px-4 py-2 text-gray-600 whitespace-nowrap">{row.region || "—"}</td>
                        <td className="px-4 py-2 text-gray-600 max-w-[16rem] sm:max-w-lg truncate" title={row.eksempel_adresse}>
                          {row.eksempel_adresse || "—"}
                        </td>
                        <td className="px-4 py-2 text-right text-gray-600">{fmtN(row.gl_antall_ar)}</td>
                        <td className="px-4 py-2 text-right font-medium text-gray-800">{fmtKr(row.gl_belop_ar)}</td>
                        <td className="px-4 py-2 text-right text-gray-500">{fmtN(row.gl_antall_alle)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {koststedUkoblet && koststedUkoblet.antall === 0 && (
            <section className="bg-white rounded-xl border border-green-200 shadow-sm px-6 py-4">
              <p className="text-sm text-green-800">
                Alle koststed-rader i <code className="text-xs bg-green-50 px-1 rounded">koststed_mapping</code> har{" "}
                <code className="text-xs bg-green-50 px-1 rounded">property_id</code> satt. Ingen poster i ukoblet-listen.
              </p>
            </section>
          )}

          {/* ── 4. SRS 13 – Leieavtaler ────────────────────────────────── */}
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">SRS 13 – Leieavtaler {ar}</h2>
              <p className="text-xs text-gray-500 mt-0.5">Konto 6300 (privat utleier) og 6310 (Statsbygg)</p>
            </div>
            {data.srs_13_leie.length === 0 ? (
              <p className="px-6 py-4 text-sm text-gray-400">Ingen leie-transaksjoner funnet for {ar}</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left">
                    <th className="px-4 py-2 font-semibold text-gray-600">Konto</th>
                    <th className="px-4 py-2 font-semibold text-gray-600">Beskrivelse</th>
                    <th className="px-4 py-2 font-semibold text-gray-600">Type</th>
                    <th className="px-4 py-2 font-semibold text-gray-600 text-right">Antall bilag</th>
                    <th className="px-4 py-2 font-semibold text-gray-600 text-right">Total beløp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.srs_13_leie.map((l) => (
                    <tr key={l.konto} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-700">{l.konto}</td>
                      <td className="px-4 py-3 text-gray-700">{l.konto_navn}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          l.type === "Statsbygg"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-gray-100 text-gray-700"
                        }`}>
                          {l.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">{fmtN(l.antall)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-800">{fmtKr(l.belop)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          {/* ── 5. SRS 17 – Anleggsmidler ──────────────────────────────── */}
          <section className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="text-base font-semibold text-gray-800">SRS 17 – Anleggsmidler</h2>
              <p className="text-xs text-gray-500 mt-0.5">Lineær avskrivning over MIN(levetid, gjenværende leieperiode)</p>
            </div>
            <div className="p-6">
              {data.srs_17_anlegg.status === "ikke_befolket" ? (
                <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <span className="text-blue-500 text-xl mt-0.5">⏳</span>
                  <div>
                    <p className="text-sm font-semibold text-blue-800">Anleggsregisteret er ikke befolket ennå</p>
                    <p className="text-xs text-blue-600 mt-1">
                      Fase 3 i SRS-implementasjonen vil populere dette fra GL-transaksjoner der konto ∈ {"{"}1268, 4960{"}"} og beløp ≥ 50 000 kr.
                      Avskrivningsmotor (SRS 17) og nøytralisering (SRS 10) implementeres samtidig.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-gray-900">{data.srs_17_anlegg.totalt}</p>
                    <p className="text-xs text-gray-500 mt-1">Totalt anleggsmidler</p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-green-600">{data.srs_17_anlegg.aktive}</p>
                    <p className="text-xs text-gray-500 mt-1">Aktive</p>
                  </div>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-purple-600">{fmtKr(data.srs_17_anlegg.total_bokfort)}</p>
                    <p className="text-xs text-gray-500 mt-1">Total balanseført verdi</p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Footer */}
          <p className="text-xs text-gray-400 text-center pb-4 print:block">
            Generert {new Date().toLocaleDateString("nb-NO")} — BEFS / Bufetat Eiendomsforvaltningssystem
          </p>
        </div>
      )}
    </div>
  );
}
