"use client";

import { useEffect, useState, useMemo } from "react";
import {
  ChevronDown,
  ChevronUp,
  Info,
  TrendingDown,
  TrendingUp,
  RefreshCw,
  Building2,
  BarChart3,
} from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

function fmt(n: number | null | undefined): string {
  if (n == null || n === 0) return "—";
  if (Math.abs(n) >= 1_000_000)
    return (n / 1_000_000).toLocaleString("nb-NO", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " MNOK";
  return n.toLocaleString("nb-NO", { maximumFractionDigits: 0 }) + " kr";
}

function pctStr(n: number | null | undefined): string {
  if (n == null) return "—";
  return (n > 0 ? "+" : "") + n.toFixed(1).replace(".", ",") + " %";
}

function changePct(actual: number, pred: number): number | null {
  if (!actual || actual < 200_000) return null;           // for liten base
  const pct = ((pred - actual) / actual) * 100;
  if (Math.abs(pct) > 300) return null;                  // meningsløs ekstremverdi
  return pct;
}

interface ChangeBadgeProps {
  pct: number | null | undefined;
  small?: boolean;
}
function ChangeBadge({ pct, small }: ChangeBadgeProps) {
  if (pct == null) return <span className="text-gray-400 text-xs">—</span>;
  const isDown = pct < 0;
  const isFlat = Math.abs(pct) <= 1;
  const cls = isFlat
    ? "bg-gray-100 text-gray-600"
    : isDown
    ? "bg-green-100 text-green-800"
    : Math.abs(pct) > 5
    ? "bg-red-100 text-red-800"
    : "bg-yellow-100 text-yellow-800";
  const Icon = isDown ? TrendingDown : TrendingUp;
  return (
    <span
      className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full font-medium ${small ? "text-[10px]" : "text-xs"} ${cls}`}
    >
      <Icon className={small ? "w-2.5 h-2.5" : "w-3 h-3"} />
      {pctStr(pct)}
    </span>
  );
}

interface CategoryRow {
  category: string;
  actual_2025: number;
  pred_2026: number;
  pred_2027: number;
  change_2526_pct?: number | null;
  change_2627_pct?: number | null;
}

interface PropertyRow {
  property_id: string;
  name: string;
  category: string;
  actual_2025: number;
  pred_2026: number;
  pred_2027: number;
  change_2526_pct?: number | null;
  change_2627_pct?: number | null;
  change_2527_pct?: number | null;
}

interface Totals {
  actual_2025: number;
  pred_2026: number;
  pred_2027: number;
  change_2526_pct?: number | null;
  change_2627_pct?: number | null;
  change_2527_pct?: number | null;
}

interface SammenligningData {
  scenario: string;
  generated_at: string;
  pred_2026_available?: boolean;
  pred_2027_available: boolean;
  totals: Totals;
  categories: CategoryRow[];
  properties: PropertyRow[];
}

const METODETEKST = [
  {
    tittel: "Algoritme: Holt-Winters dobbel eksponentiell glattning",
    tekst:
      "Modellen bruker Holt's Linear Exponential Smoothing med trenddemping (Gardner-McKenzie, φ = 0,85). Nyere regnskapsår vektes eksponentielt tyngre enn eldre år (α = 0,5 for nivå, β = 0,2 for trend). Trenddemping hindrer at kortvarige svingninger ekstrapoleres ukritisk langt frem i tid.",
  },
  {
    tittel: "Kategorier (Bufdir 2027-inndeling)",
    tekst:
      "Drift: løpende driftsutgifter (strøm, renovasjon, renhold, vakthold). Vedlikehold: vedlikehold og reparasjoner (konto 1268, 4960, 6630, 6632, 6662). Lokaler / Gjennomstrømning: husleie, fellesutgifter og omposteringer (konto 6300-serien + bilagsarter H1/H2/HB/RE). Annet: øvrige kostnader uten entydig kategori.",
  },
  {
    tittel: "Sikkerhetstiltak i modellen",
    tekst:
      "Inflasjonsfallback (3,5 % SSB KPI-prognose) brukes for eiendommer med kun ett år GL-historikk. Kald-start-begrensning: eiendommer med rask oppramp (siste år > 3 × historisk snitt) bruker inflasjonsfallback. Sikkerhetstak: prediksjon kappes til maks 5 × siste faktiske år uansett trendretning.",
  },
  {
    tittel: "Begrensninger",
    tekst:
      "Modellen tar ikke hensyn til nybygg, organisasjonsendringer, politiske vedtak etter 2025 eller endringer i leiekontrakter. Tallene er estimater – ikke godkjente budsjetttall. Faktisk 2026-regnskap vil overstyre prediksjonen etter årsavslutning.",
  },
];

function MetodePanel() {
  const [open, setOpen] = useState(false);
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <div className="border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3.5 bg-blue-50 hover:bg-blue-100 transition-colors text-left"
      >
        <span className="flex items-center gap-2 font-semibold text-blue-900 text-sm">
          <Info className="w-4 h-4 text-blue-600" />
          Metodebeskrivelse — slik beregnes prediksjonen
        </span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-blue-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-blue-600" />
        )}
      </button>

      {open && (
        <div className="divide-y bg-white">
          {METODETEKST.map((item, i) => (
            <div key={i}>
              <button
                onClick={() => setOpenIdx(openIdx === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50 transition-colors"
              >
                <span className="font-medium text-sm text-gray-800">{item.tittel}</span>
                {openIdx === i ? (
                  <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                )}
              </button>
              {openIdx === i && (
                <p className="px-5 pb-4 text-sm text-gray-600 leading-relaxed">
                  {item.tekst}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KategoriTabell({
  categories,
  totals,
}: {
  categories: CategoryRow[];
  totals: Totals;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b">
            <th className="px-4 py-3 text-left font-semibold text-gray-700">Kategori</th>
            <th className="px-4 py-3 text-right font-semibold text-gray-700">
              Faktisk 2025 (GL)
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-500 text-xs">
              25→26
            </th>
            <th className="px-4 py-3 text-right font-semibold text-indigo-900">
              Prediksjon 2026
            </th>
            <th className="px-4 py-3 text-center font-semibold text-gray-500 text-xs">
              26→27
            </th>
            <th className="px-4 py-3 text-right font-semibold text-blue-900">
              Prediksjon 2027
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {categories.map((row) => (
            <tr key={row.category} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3.5 font-medium text-gray-900">{row.category}</td>
              <td className="px-4 py-3.5 text-right tabular-nums text-gray-600">
                {fmt(row.actual_2025)}
              </td>
              <td className="px-4 py-3.5 text-center">
                <ChangeBadge pct={row.change_2526_pct ?? changePct(row.actual_2025, row.pred_2026)} />
              </td>
              <td className="px-4 py-3.5 text-right tabular-nums font-bold text-indigo-900">
                {fmt(row.pred_2026)}
              </td>
              <td className="px-4 py-3.5 text-center">
                <ChangeBadge pct={row.change_2627_pct ?? changePct(row.pred_2026, row.pred_2027)} />
              </td>
              <td className="px-4 py-3.5 text-right tabular-nums font-bold text-blue-900">
                {fmt(row.pred_2027)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="bg-gray-100 border-t-2 border-gray-300 font-bold">
            <td className="px-4 py-3 text-gray-900">Totalt</td>
            <td className="px-4 py-3 text-right tabular-nums text-gray-700">
              {fmt(totals.actual_2025)}
            </td>
            <td className="px-4 py-3 text-center">
              <ChangeBadge pct={totals.change_2526_pct ?? changePct(totals.actual_2025, totals.pred_2026)} />
            </td>
            <td className="px-4 py-3 text-right tabular-nums text-indigo-900">
              {fmt(totals.pred_2026)}
            </td>
            <td className="px-4 py-3 text-center">
              <ChangeBadge pct={totals.change_2627_pct ?? changePct(totals.pred_2026, totals.pred_2027)} />
            </td>
            <td className="px-4 py-3 text-right tabular-nums text-blue-900">
              {fmt(totals.pred_2027)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

type SortKey =
  | "name"
  | "category"
  | "actual_2025"
  | "pred_2026"
  | "pred_2027"
  | "change_2526_pct"
  | "change_2627_pct"
  | "change_2527_pct";

function EiendomTabell({ properties }: { properties: PropertyRow[] }) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("actual_2025");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [catFilter, setCatFilter] = useState<string>("alle");

  const categories = useMemo(
    () => Array.from(new Set(properties.map((p) => p.category))).sort(),
    [properties]
  );

  const withChange = useMemo(
    () =>
      properties.map((p) => ({
        ...p,
        change_2526_pct: p.change_2526_pct ?? changePct(p.actual_2025, p.pred_2026),
        change_2627_pct: p.change_2627_pct ?? changePct(p.pred_2026, p.pred_2027),
        change_2527_pct: p.change_2527_pct ?? changePct(p.actual_2025, p.pred_2027),
      })),
    [properties]
  );

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return withChange
      .filter(
        (p) =>
          (catFilter === "alle" || p.category === catFilter) &&
          (p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q))
      )
      .sort((a, b) => {
        const mult = sortDir === "desc" ? -1 : 1;
        if (sortKey === "name") return mult * a.name.localeCompare(b.name, "nb");
        if (sortKey === "category") return mult * a.category.localeCompare(b.category, "nb");
        const av = (a[sortKey] as number | null) ?? -Infinity;
        const bv = (b[sortKey] as number | null) ?? -Infinity;
        return mult * (av - bv);
      });
  }, [withChange, search, sortKey, sortDir, catFilter]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    else { setSortKey(key); setSortDir("desc"); }
  }

  function SortTh({ label, k }: { label: string; k: SortKey }) {
    const active = sortKey === k;
    return (
      <th
        className="px-3 py-3 text-right cursor-pointer select-none hover:text-blue-700 transition-colors whitespace-nowrap"
        onClick={() => toggleSort(k)}
      >
        <span className={`flex items-center justify-end gap-1 font-semibold ${active ? "text-blue-700" : "text-gray-600"}`}>
          {label}
          {active ? (
            sortDir === "desc" ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />
          ) : null}
        </span>
      </th>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="Søk eiendom…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-48 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={catFilter}
          onChange={(e) => setCatFilter(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="alle">Alle kategorier</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
      <p className="text-xs text-gray-500">{filtered.length} rader</p>

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th
                className="px-3 py-3 text-left cursor-pointer select-none hover:text-blue-700 transition-colors font-semibold text-gray-700"
                onClick={() => toggleSort("name")}
              >
                <span className="flex items-center gap-1">
                  Eiendom
                  {sortKey === "name" ? (sortDir === "desc" ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />) : null}
                </span>
              </th>
              <th
                className="px-3 py-3 text-left cursor-pointer select-none hover:text-blue-700 transition-colors font-semibold text-gray-600 text-xs"
                onClick={() => toggleSort("category")}
              >
                Kategori
              </th>
              <SortTh label="Faktisk 2025" k="actual_2025" />
              <th className="px-3 py-3 text-center font-semibold text-gray-400 text-xs">25→26</th>
              <SortTh label="Pred. 2026" k="pred_2026" />
              <th className="px-3 py-3 text-center font-semibold text-gray-400 text-xs">26→27</th>
              <SortTh label="Pred. 2027" k="pred_2027" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400 text-sm">
                  Ingen resultater
                </td>
              </tr>
            )}
            {filtered.map((row) => (
              <tr
                key={`${row.property_id}-${row.category}`}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-3 py-2.5 font-medium text-gray-900 max-w-[200px] truncate" title={row.name}>
                  {row.name}
                </td>
                <td className="px-3 py-2.5 text-xs text-gray-500 whitespace-nowrap">
                  {row.category}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-gray-600">
                  {fmt(row.actual_2025)}
                </td>
                <td className="px-3 py-2.5 text-center">
                  <ChangeBadge pct={row.change_2526_pct} small />
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums font-bold text-indigo-900">
                  {fmt(row.pred_2026)}
                </td>
                <td className="px-3 py-2.5 text-center">
                  <ChangeBadge pct={row.change_2627_pct} small />
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-blue-900 font-bold">
                  {fmt(row.pred_2027)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function PredSammenligningPage() {
  const [data, setData] = useState<SammenligningData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"kategori" | "eiendom">("kategori");
  const [scenario, setScenario] = useState<"xgb70" | "xgb50">("xgb70");

  async function load(sc = scenario) {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAPI<SammenligningData>(
        `/financials/prediksjon-sammenligning?scenario=${sc}`
      );
      setData(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(scenario); }, [scenario]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prediksjonssammenligning 2025 – 2026 – 2027</h1>
          <p className="text-sm text-gray-500 mt-1">Faktisk GL 2025 sammenlignet med prediksjon for både 2026 og 2027</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value as "xgb70" | "xgb50")}
            className="px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="xgb70">Scenario XGB-gulv 70 %</option>
            <option value="xgb50">Scenario XGB-gulv 50 %</option>
          </select>
          <button
            onClick={() => load(scenario)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Oppdater
          </button>
        </div>
      </div>

      {/* Leseveiledning */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-gray-500" />
            <span className="font-semibold text-sm text-gray-700">Faktisk 2025 (GL)</span>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">
            Regnskapsdata hentet direkte fra Agresso (GL-transaksjoner). Dette er <strong>reelle kostnader</strong> som allerede er påløpt og bokført. Brukes som startpunkt for prediksjonen.
          </p>
        </div>
        <div className="rounded-xl border border-blue-300 bg-blue-50 p-5">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-blue-800" />
            <span className="font-semibold text-sm text-blue-900">Prediksjon 2027</span>
          </div>
          <p className="text-sm text-blue-800 leading-relaxed">
            <strong>Budsjettet for 2027</strong> — to år frem i tid. Bygger på kostnadstrend 2021–2025 (Holt-Winters med trenddemping). Trenddemping begrenser ekstreme utslag.
          </p>
          <p className="text-xs text-blue-600 mt-2">
            ⚠️ Benyttes kun som teknisk grunnlag — faglig vurdering må legges til.
          </p>
        </div>
      </div>

      {/* Hvorfor kan 2027 være lavere enn 2025? */}
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div className="space-y-2">
            <p className="font-semibold text-amber-900 text-sm">
              Hvorfor kan prediksjonene være lavere enn faktisk 2025?
            </p>
            <p className="text-sm text-amber-800 leading-relaxed">
              Modellen analyserer kostnadshistorikken fra 2021 til 2025 og finner <strong>trenden</strong>. Dersom kostnadene har gått <em>ned</em> de siste årene — for eksempel fordi et stort vedlikeholdsprosjekt ble avsluttet, en eiendom ble avviklet, eller driftsrutiner ble effektivisert — vil modellen forutse at denne nedgangen fortsetter. Det er matematisk korrekt gitt historikken, men krever faglig vurdering: er nedgangen strukturell (vedvarer), eller var 2025 et unormalt lavt år?
            </p>
            <p className="text-sm text-amber-800 leading-relaxed">
              <strong>Per eiendom-fanen</strong> viser dette tydeligst: eiendommer med grønn badge (↓) er der modellen ser en nedgangstrend. Eiendommer med rød badge (↑) er der modellen forventer kostnadsvekst.
            </p>
          </div>
        </div>
      </div>

      {/* Metodepanel */}
      <MetodePanel />

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800">
          Feil: {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-2" />
          Laster data…
        </div>
      )}

      {/* Totalkort */}
      {data && !loading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: "Faktisk 2025 (GL)", value: data.totals.actual_2025, sub: "Regnskapstall fra Agresso", color: "text-gray-900", change: null as number | null },
              { label: "Prediksjon 2026", value: data.totals.pred_2026, sub: pctStr(data.totals.change_2526_pct ?? changePct(data.totals.actual_2025, data.totals.pred_2026)) + " fra 2025", color: "text-indigo-900", change: data.totals.change_2526_pct ?? changePct(data.totals.actual_2025, data.totals.pred_2026) },
              { label: "Prediksjon 2027", value: data.totals.pred_2027, sub: pctStr(data.totals.change_2627_pct ?? changePct(data.totals.pred_2026, data.totals.pred_2027)) + " fra 2026", color: "text-blue-900", change: data.totals.change_2627_pct ?? changePct(data.totals.pred_2026, data.totals.pred_2027) },
            ].map((card) => (
              <div key={card.label} className="border rounded-xl p-5 bg-white">
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{card.label}</p>
                <p className={`text-2xl font-bold mt-1 ${card.color}`}>{fmt(card.value)}</p>
                <div className="flex items-center gap-2 mt-1">
                  {card.change != null && <ChangeBadge pct={card.change} />}
                  <span className="text-xs text-gray-400">{card.sub}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setTab("kategori")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === "kategori" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-800"}`}
            >
              <BarChart3 className="w-4 h-4" />
              Totalt per kategori
            </button>
            <button
              onClick={() => setTab("eiendom")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === "eiendom" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-800"}`}
            >
              <Building2 className="w-4 h-4" />
              Per eiendom
              <span className="ml-1 text-xs text-gray-400">({data.properties.length})</span>
            </button>
          </div>

          {tab === "kategori" && (
            <KategoriTabell categories={data.categories} totals={data.totals} />
          )}
          {tab === "eiendom" && (
            <EiendomTabell properties={data.properties} />
          )}

          <p className="text-xs text-gray-400 text-right">
            Scenario: {data.scenario} · Oppdatert {new Date(data.generated_at).toLocaleString("nb-NO")}
          </p>
        </>
      )}
    </div>
  );
}
