"use client";

import React, { useState, useEffect, useCallback } from "react";
import { fetchAPI } from "@/lib/api/client";

interface ForslagEiendom {
  property_id: string;
  name: string;
  address: string;
  region: string;
  score: number;     // 0.0–1.0
  grunn: string;     // forklaringstekst fra backend
}

interface UkobletKoststed {
  koststed_kode: string;
  koststed_navn: string;
  region: string;
  belop_2025: number;
  belop_2024: number;
  belop_totalt: number;
  antall_tx: number;
  eksempel_tekst: string;
  kontonavn_topp: string;
  foreslåtte_eiendommer: ForslagEiendom[];
}

interface Eiendom {
  property_id: string;
  name: string;
  address: string;
  region: string;
}

interface KoststedData {
  ukoblet_koststed: UkobletKoststed[];
  totalt_ukoblet: number;
  eiendommer: Eiendom[];
}

function fmtKr(n: number) {
  return new Intl.NumberFormat("no-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);
}

export default function KoststedMappingPage() {
  const [data, setData] = useState<KoststedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [minBelop, setMinBelop] = useState(100000);
  const [søk, setSøk] = useState("");
  const [valg, setValg] = useState<Record<string, string>>({});  // kode → property_id
  const [lagrer, setLagrer] = useState<Record<string, boolean>>({});
  const [lagretOk, setLagretOk] = useState<Record<string, boolean>>({});
  const [backfillResultat, setBackfillResultat] = useState<string | null>(null);
  const [backfillLaster, setBackfillLaster] = useState(false);

  const last = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchAPI<KoststedData>(
        `/admin/gl-import/koststed-mapping/ukoblet?min_belop=${minBelop}`
      );
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [minBelop]);

  useEffect(() => { last(); }, [last]);

  async function lagreKobling(kode: string) {
    const pid = valg[kode];
    if (!pid && pid !== "") return;
    setLagrer(p => ({ ...p, [kode]: true }));
    try {
      const url = `/admin/gl-import/koststed-mapping/${encodeURIComponent(kode)}` +
        (pid ? `?property_id=${encodeURIComponent(pid)}` : "");
      await fetchAPI(url, { method: "PATCH" });
      setLagretOk(p => ({ ...p, [kode]: true }));
      setTimeout(() => {
        setLagretOk(p => ({ ...p, [kode]: false }));
        last();
      }, 2000);
    } catch (e) {
      alert(`Feil ved lagring av ${kode}: ${e}`);
    } finally {
      setLagrer(p => ({ ...p, [kode]: false }));
    }
  }

  async function kjørBackfill() {
    setBackfillLaster(true);
    setBackfillResultat(null);
    try {
      const res = await fetchAPI<{
        gl_transactions_backfilled: number;
        total_koblet: number;
        total_gl: number;
        koblet_pst: number;
      }>("/admin/gl-import/gl-backfill-property-ids", { method: "POST" });
      setBackfillResultat(
        `✅ Backfill fullført: ${res.gl_transactions_backfilled} transaksjoner koblet. ` +
        `Totalt ${res.total_koblet.toLocaleString("no-NO")} av ${res.total_gl.toLocaleString("no-NO")} (${res.koblet_pst}%) har property_id.`
      );
      last();
    } catch (e) {
      setBackfillResultat(`❌ Feil: ${e}`);
    } finally {
      setBackfillLaster(false);
    }
  }

  const filtrert = (data?.ukoblet_koststed ?? []).filter(k =>
    søk === "" ||
    k.koststed_kode.includes(søk) ||
    k.koststed_navn.toLowerCase().includes(søk.toLowerCase()) ||
    k.eksempel_tekst.toLowerCase().includes(søk.toLowerCase())
  );

  const sumBelop2025 = filtrert.reduce((s, k) => s + k.belop_2025, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Toppseksjon */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Koststed-kobling (dim1_kode → eiendom)</h1>
        <p className="text-sm text-gray-600 mt-1">
          Koble GL-koststedskoder til BEFS-eiendommer. Koblingen brukes automatisk ved neste GL-import
          og backfiller eksisterende transaksjoner.
        </p>
      </div>

      {/* Kontrollpanel */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Min. beløp 2025 (NOK)</label>
          <select
            value={minBelop}
            onChange={e => setMinBelop(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value={0}>Alle</option>
            <option value={100000}>≥ 100 000</option>
            <option value={500000}>≥ 500 000</option>
            <option value={1000000}>≥ 1 000 000</option>
          </select>
        </div>
        <div className="flex-1 min-w-[200px]">
          <label className="block text-xs font-semibold text-gray-600 mb-1">Søk</label>
          <input
            value={søk}
            onChange={e => setSøk(e.target.value)}
            placeholder="Kode, navn eller tekst…"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={last}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            🔄 Oppdater
          </button>
          <button
            onClick={kjørBackfill}
            disabled={backfillLaster}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {backfillLaster ? "Kjører…" : "⚡ Kjør full backfill"}
          </button>
        </div>
      </div>

      {/* Backfill-resultat */}
      {backfillResultat && (
        <div className={`rounded-lg p-4 text-sm font-medium ${backfillResultat.startsWith("✅") ? "bg-green-50 text-green-800 border border-green-200" : "bg-red-50 text-red-800 border border-red-200"}`}>
          {backfillResultat}
        </div>
      )}

      {/* Statistikk */}
      {data && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-bold uppercase text-gray-500 mb-1">Ukoblede koststedskoder</p>
            <p className="text-2xl font-bold text-gray-900">{filtrert.length}</p>
            <p className="text-xs text-gray-500">av {data.totalt_ukoblet} totalt</p>
          </div>
          <div className="bg-white rounded-xl border border-orange-200 p-4">
            <p className="text-xs font-bold uppercase text-orange-600 mb-1">GL 2025 (ukoblet)</p>
            <p className="text-2xl font-bold text-orange-700">{fmtKr(sumBelop2025)}</p>
            <p className="text-xs text-orange-500">sekkepost som kan kobles</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-bold uppercase text-gray-500 mb-1">Eiendommer tilgjengelig</p>
            <p className="text-2xl font-bold text-gray-900">{data.eiendommer.length}</p>
            <p className="text-xs text-gray-500">å koble til</p>
          </div>
        </div>
      )}

      {/* Tabell */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Laster…</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 w-28">Kode</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Koststed-navn</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 w-24">Region</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-600 w-32">GL 2025</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Eksempel tekst / kontoer</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 w-96">Fuzzy-forslag + manuelt valg</th>
                  <th className="px-4 py-3 w-24"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtrert.map(k => {
                  const forslag = k.foreslåtte_eiendommer ?? [];
                  const scoreColor = (s: number) =>
                    s >= 0.6 ? "bg-green-100 text-green-800 border-green-300" :
                    s >= 0.35 ? "bg-yellow-100 text-yellow-800 border-yellow-300" :
                    "bg-gray-100 text-gray-600 border-gray-300";
                  return (
                  <tr key={k.koststed_kode} className="hover:bg-gray-50 align-top">
                    <td className="px-4 py-3 font-mono text-xs font-bold text-gray-900">{k.koststed_kode}</td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">{k.koststed_navn}</p>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{k.region}</td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">
                      {k.belop_2025 > 0 ? fmtKr(k.belop_2025) : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-xs text-gray-500 truncate max-w-xs" title={k.eksempel_tekst}>{k.eksempel_tekst}</p>
                      <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs" title={k.kontonavn_topp}>{k.kontonavn_topp}</p>
                    </td>
                    <td className="px-4 py-3 space-y-2">
                      {/* Fuzzy-forslag som hurtigknapper */}
                      {forslag.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">🔍 Forslag</p>
                          {forslag.map(f => (
                            <button
                              key={f.property_id}
                              onClick={() => setValg(p => ({ ...p, [k.koststed_kode]: f.property_id }))}
                              title={f.grunn}
                              className={`w-full text-left px-2 py-1 rounded border text-xs transition-colors hover:opacity-80 ${
                                valg[k.koststed_kode] === f.property_id
                                  ? "bg-blue-100 text-blue-900 border-blue-400 font-semibold"
                                  : scoreColor(f.score)
                              }`}
                            >
                              <span className="font-mono font-bold mr-1">{Math.round(f.score * 100)}%</span>
                              {f.name}
                              {f.address ? <span className="opacity-60"> · {f.address.slice(0, 30)}</span> : null}
                              <span className="block text-xs opacity-50 mt-0.5">{f.grunn}</span>
                            </button>
                          ))}
                        </div>
                      )}
                      {/* Full dropdown */}
                      <select
                        value={valg[k.koststed_kode] ?? ""}
                        onChange={e => setValg(p => ({ ...p, [k.koststed_kode]: e.target.value }))}
                        className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs"
                      >
                        <option value="">— Velg eiendom manuelt —</option>
                        {(data?.eiendommer ?? []).map(e => (
                          <option key={e.property_id} value={e.property_id}>
                            [{e.region}] {e.name}{e.address ? ` — ${e.address}` : ""}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      {lagretOk[k.koststed_kode] ? (
                        <span className="text-green-600 font-bold text-xs">✅ Lagret</span>
                      ) : (
                        <button
                          onClick={() => lagreKobling(k.koststed_kode)}
                          disabled={!valg[k.koststed_kode] || lagrer[k.koststed_kode]}
                          className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:opacity-40 transition-colors"
                        >
                          {lagrer[k.koststed_kode] ? "…" : "Koble"}
                        </button>
                      )}
                    </td>
                  </tr>
                  );
                })}
                {filtrert.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                      Ingen ukoblede koststedskoder med beløp ≥ {fmtKr(minBelop)} 🎉
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-400">
        Kobling lagres i koststed_mapping-tabellen og backfiller automatisk gl_transactions.
        Neste GL-import vil bruke den nye mappingen.
      </p>
    </div>
  );
}
