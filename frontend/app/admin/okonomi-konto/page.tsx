"use client";

import { useState, useEffect, useMemo } from "react";
import { ChevronDown, ChevronRight, Search, Filter } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "";

const HEADERS = {
  Authorization: `Bearer ${process.env.NEXT_PUBLIC_SHARED_SECRET || "befs-super-secret-key-12345"}`,
  "X-User-Email": "system@befs.no",
  "Content-Type": "application/json",
};

interface KontoRad {
  eiendom: string;
  region: string;
  konto: string;
  konto_navn: string;
  belop: number;
}

interface EiendomGruppe {
  eiendom: string;
  region: string;
  total: number;
  kontoer: { konto: string; konto_navn: string; belop: number }[];
}

function fmt(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)} M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)} k`;
  return n.toFixed(0);
}

function fmtKr(n: number): string {
  return new Intl.NumberFormat("nb-NO", { maximumFractionDigits: 0 }).format(n) + " kr";
}

const REGION_COLORS: Record<string, string> = {
  "Øst": "bg-blue-500",
  "Sør": "bg-green-500",
  "Midt-Norge": "bg-orange-500",
  "Nord": "bg-purple-500",
  "Vest": "bg-teal-500",
  "Bufdir": "bg-pink-500",
  "Nasjonal": "bg-amber-500",
};

const KONTO_FARGER: Record<string, string> = {
  "6300": "text-red-400",
  "6310": "text-red-300",
  "6340": "text-yellow-400",
  "6360": "text-blue-400",
  "6395": "text-orange-400",
  "6396": "text-orange-300",
  "6398": "text-orange-200",
  "6630": "text-purple-400",
  "6390": "text-gray-400",
};

export default function OkonomiKontoPage() {
  const [data, setData] = useState<KontoRad[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(2025);
  const [sok, setSok] = useState("");
  const [filterRegion, setFilterRegion] = useState("Alle");
  const [filterKonto, setFilterKonto] = useState("Alle");
  const [apne, setApne] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/v1/financials/konto-fordeling-per-eiendom?year=${year}`, { headers: HEADERS })
      .then((r) => r.ok ? r.json() : Promise.resolve([]))
      .catch(() => [])
      .then((d) => { setData(Array.isArray(d) ? d : []); setLoading(false); });
  }, [year]);

  const regioner = useMemo(() => ["Alle", ...Array.from(new Set(data.map((r) => r.region))).sort()], [data]);
  const kontoer = useMemo(() => ["Alle", ...Array.from(new Set(data.map((r) => r.konto))).sort()], [data]);

  // Grupper per eiendom
  const grupper = useMemo<EiendomGruppe[]>(() => {
    const filtrert = data.filter((r) => {
      const mSok = !sok || r.eiendom.toLowerCase().includes(sok.toLowerCase());
      const mReg = filterRegion === "Alle" || r.region === filterRegion;
      const mKon = filterKonto === "Alle" || r.konto === filterKonto;
      return mSok && mReg && mKon;
    });

    const map = new Map<string, EiendomGruppe>();
    for (const r of filtrert) {
      if (!map.has(r.eiendom)) {
        map.set(r.eiendom, { eiendom: r.eiendom, region: r.region, total: 0, kontoer: [] });
      }
      const g = map.get(r.eiendom)!;
      g.total += r.belop;
      g.kontoer.push({ konto: r.konto, konto_navn: r.konto_navn, belop: r.belop });
    }

    return Array.from(map.values()).sort((a, b) => b.total - a.total);
  }, [data, sok, filterRegion, filterKonto]);

  // Konto-totaler på tvers av alle eiendommer (filtrert)
  const kontoTotaler = useMemo(() => {
    const map = new Map<string, { konto: string; konto_navn: string; belop: number }>();
    for (const g of grupper) {
      for (const k of g.kontoer) {
        if (!map.has(k.konto)) map.set(k.konto, { konto: k.konto, konto_navn: k.konto_navn, belop: 0 });
        map.get(k.konto)!.belop += k.belop;
      }
    }
    return Array.from(map.values()).sort((a, b) => b.belop - a.belop);
  }, [grupper]);

  const totalSum = grupper.reduce((s, g) => s + g.total, 0);

  const toggleApne = (navn: string) => {
    setApne((prev) => {
      const next = new Set(prev);
      if (next.has(navn)) next.delete(navn);
      else next.add(navn);
      return next;
    });
  };

  const apneAlle = () => setApne(new Set(grupper.map((g) => g.eiendom)));
  const lukkAlle = () => setApne(new Set());

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-foreground">Konto-fordeling per eiendom</h1>
          <p className="text-muted-foreground text-sm mt-1">
            GL-regnskap fra økonomiavdelingen · kun Bufetat-eiendommer i øk. sammenligning
          </p>
        </div>

        {/* Filtre */}
        <div className="glass-card p-4 mb-6 flex flex-wrap gap-3 items-center">
          <div className="flex items-center gap-2 border-r border-border pr-3">
            <span className="text-xs text-muted-foreground font-medium">År:</span>
            {[2024, 2025].map((y) => (
              <button
                key={y}
                onClick={() => setYear(y)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                  year === y ? "bg-primary text-primary-foreground" : "bg-secondary text-foreground hover:bg-secondary/80"
                }`}
              >
                {y}
              </button>
            ))}
          </div>
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Søk eiendom…"
              value={sok}
              onChange={(e) => setSok(e.target.value)}
              className="pl-8 pr-3 py-1.5 bg-secondary border border-border rounded-lg text-sm text-foreground placeholder-muted-foreground outline-none focus:border-primary w-52"
            />
          </div>
          <select
            value={filterRegion}
            onChange={(e) => setFilterRegion(e.target.value)}
            className="bg-secondary border border-border rounded-lg px-3 py-1.5 text-sm text-foreground outline-none focus:border-primary"
          >
            {regioner.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select
            value={filterKonto}
            onChange={(e) => setFilterKonto(e.target.value)}
            className="bg-secondary border border-border rounded-lg px-3 py-1.5 text-sm text-foreground outline-none focus:border-primary"
          >
            {kontoer.map((k) => (
              <option key={k} value={k}>
                {k === "Alle" ? "Alle kontoer" : `${k} – ${data.find((r) => r.konto === k)?.konto_navn || ""}`}
              </option>
            ))}
          </select>
          <div className="ml-auto flex gap-2">
            <button onClick={apneAlle} className="text-xs text-primary hover:underline">Åpne alle</button>
            <span className="text-muted-foreground">·</span>
            <button onClick={lukkAlle} className="text-xs text-primary hover:underline">Lukk alle</button>
          </div>
        </div>

        {/* Konto-totaler (sammendrag) */}
        <div className="glass-card p-4 mb-6">
          <h2 className="text-sm font-semibold text-foreground mb-3">
            Konto-fordeling totalt — {grupper.length} eiendommer · {fmt(totalSum)} kr
          </h2>
          <div className="flex flex-wrap gap-2">
            {kontoTotaler.map((k) => (
              <div
                key={k.konto}
                onClick={() => setFilterKonto(filterKonto === k.konto ? "Alle" : k.konto)}
                className={`cursor-pointer px-3 py-1.5 rounded-lg border text-xs transition ${
                  filterKonto === k.konto
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border bg-secondary text-foreground hover:border-primary/50"
                }`}
              >
                <span className={`font-mono font-bold ${KONTO_FARGER[k.konto] || "text-foreground"}`}>{k.konto}</span>
                <span className="text-muted-foreground mx-1.5">·</span>
                <span className="text-muted-foreground truncate max-w-[140px] inline-block align-bottom">{k.konto_navn}</span>
                <span className="ml-2 font-semibold">{fmt(k.belop)}</span>
                <span className="text-muted-foreground ml-1">({((k.belop / totalSum) * 100).toFixed(1)}%)</span>
              </div>
            ))}
          </div>
        </div>

        {/* Per eiendom */}
        {loading ? (
          <div className="text-center text-muted-foreground py-20">Laster kontodata…</div>
        ) : grupper.length === 0 ? (
          <div className="text-center text-muted-foreground py-20">Ingen data funnet</div>
        ) : (
          <div className="space-y-1">
            {grupper.map((g) => {
              const er_apne = apne.has(g.eiendom);
              const maxKonto = Math.max(...g.kontoer.map((k) => Math.abs(k.belop)), 1);
              return (
                <div key={g.eiendom} className="glass-card overflow-hidden">
                  {/* Rad-header */}
                  <div
                    className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-secondary/50 transition select-none"
                    onClick={() => toggleApne(g.eiendom)}
                  >
                    <span className="text-muted-foreground">
                      {er_apne ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </span>
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${REGION_COLORS[g.region] || "bg-gray-400"}`} />
                    <span className="text-sm font-medium text-foreground flex-1 truncate">{g.eiendom}</span>
                    <span className="text-xs text-muted-foreground w-24 text-right hidden sm:block">{g.region}</span>
                    <span className="text-sm font-bold text-foreground w-28 text-right">{fmtKr(g.total)}</span>
                    {/* Mini konto-bar */}
                    <div className="hidden md:flex items-center gap-0.5 w-32">
                      {g.kontoer.slice(0, 6).map((k, i) => (
                        <div
                          key={i}
                          className={`h-4 rounded-sm ${KONTO_FARGER[k.konto] ? "bg-current" : "bg-secondary"} opacity-70`}
                          style={{ width: `${(Math.abs(k.belop) / maxKonto) * 100}%`, minWidth: 3 }}
                          title={`${k.konto}: ${fmtKr(k.belop)}`}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Konto-detaljer */}
                  {er_apne && (
                    <div className="border-t border-border bg-secondary/20 px-4 py-3">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-muted-foreground border-b border-border">
                            <th className="text-left pb-1.5 font-medium">Konto</th>
                            <th className="text-left pb-1.5 font-medium">Navn</th>
                            <th className="text-right pb-1.5 font-medium">Beløp</th>
                            <th className="text-right pb-1.5 font-medium">Andel</th>
                            <th className="pb-1.5 w-32" />
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/50">
                          {g.kontoer.map((k, i) => {
                            const andel = g.total !== 0 ? (k.belop / g.total) * 100 : 0;
                            return (
                              <tr key={i} className="hover:bg-secondary/50 transition">
                                <td className={`py-1.5 font-mono font-bold ${KONTO_FARGER[k.konto] || "text-foreground"}`}>
                                  {k.konto}
                                </td>
                                <td className="py-1.5 text-foreground">{k.konto_navn}</td>
                                <td className="py-1.5 text-right font-medium text-foreground">{fmtKr(k.belop)}</td>
                                <td className="py-1.5 text-right text-muted-foreground">{andel.toFixed(1)} %</td>
                                <td className="py-1.5 pl-3">
                                  <div className="bg-secondary rounded-full h-1.5 w-32">
                                    <div
                                      className="h-1.5 rounded-full bg-primary opacity-70"
                                      style={{ width: `${Math.min(Math.abs(andel), 100)}%` }}
                                    />
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                        <tfoot>
                          <tr className="border-t border-border">
                            <td colSpan={2} className="pt-1.5 font-bold text-foreground">Totalt</td>
                            <td className="pt-1.5 text-right font-bold text-foreground">{fmtKr(g.total)}</td>
                            <td colSpan={2} />
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
