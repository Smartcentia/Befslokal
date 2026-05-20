"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { ArrowLeft, Info } from "lucide-react";
import { API_BASE_URL } from "@/lib/api/client";

const BEARER = process.env.NEXT_PUBLIC_API_SECRET || "befs-super-secret-key-12345";

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtKr(n: number | null | undefined): string {
    if (n == null) return "—";
    return n.toLocaleString("nb-NO", { maximumFractionDigits: 0 }) + " kr";
}

function fmtMrd(n: number | null | undefined): string {
    if (n == null) return "—";
    const mrd = n / 1_000_000_000;
    if (Math.abs(mrd) >= 1) return mrd.toFixed(2).replace(".", ",") + " mrd kr";
    const mill = n / 1_000_000;
    return mill.toFixed(1).replace(".", ",") + " mill kr";
}

function fmtPst(n: number | null | undefined): string {
    if (n == null) return "—";
    return (n >= 0 ? "+" : "") + n.toFixed(1).replace(".", ",") + " %";
}

/** Viser "—" for ekstreme %-verdier eller for liten GL-base (under 200 000 kr). */
function fmtPstSafe(pct: number | null | undefined, glBase?: number): string {
    if (pct == null) return "—";
    if (glBase != null && glBase < 200_000) return "—";
    if (Math.abs(pct) > 300) return "—";
    return (pct >= 0 ? "+" : "") + pct.toFixed(1).replace(".", ",") + " %";
}

function deltaClass(n: number | null | undefined): string {
    if (n == null) return "text-gray-500";
    if (n > 0) return "text-red-600";
    return "text-green-600";
}

function changePct(actual: number, pred: number | null): number | null {
    if (!actual || pred == null) return null;
    return ((pred - actual) / actual) * 100;
}

async function apiFetch<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${path}`, {
        headers: { Authorization: `Bearer ${BEARER}` },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${path}`);
    return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface Antagelser {
    modell: string;
    alpha: number;
    beta: number;
    phi: number;
    history_from: number;
    history_to: number;
    passthrough_kategorier: string[];
    passthrough_forklaring: string;
    inflasjon_2026: number;
    inflasjon_2027: number;
    scenarioer: { navn: string; beskrivelse: string }[];
    generert: string;
}

interface SammenligningTotals {
    actual_2025: number;
    pred_2027: number;
    change_2527_pct: number | null;
    drift_actual_2025: number;
    drift_pred_2027: number;
    drift_change_pct: number | null;
    gjstrom_actual_2025: number;
    gjstrom_pred_2027: number;
    gjstrom_change_pct: number | null;
}

interface SammenligningCategory {
    category: string;
    is_gjennomstromning: boolean;
    metode: string;
    actual_2025: number;
    pred_2027: number;
    change_2527_pct: number | null;
}

interface SammenligningProperty {
    property_id: string;
    name: string;
    category: string;
    region: string;
    is_gjennomstromning: boolean;
    actual_2025: number;
    pred_2027: number;
    change_2527_pct: number | null;
}

interface SammenligningRegion {
    region: string;
    actual_2025: number;
    pred_2027: number;
    change_2527_pct: number | null;
}

interface Sammenligning {
    scenario: string;
    generated_at: string;
    pred_2027_available: boolean;
    totals: SammenligningTotals;
    categories: SammenligningCategory[];
    properties: SammenligningProperty[];
    regions: SammenligningRegion[];
}

interface Prediksjon2027 {
    ar: number;
    generert: boolean;
    antall_eiendommer: number;
    total_2027: number;
    total_2025_gl: number;
    endring_pst: number | null;
    lonn_2027: number;
    lonn_2025: number;
    lonn_generert: boolean;
    lonn_endring_pst: number | null;
}

interface HWStep {
    year: number;
    gl_raw: number | null;
    gl_cpi: number | null;
    L: number | null;
    T: number | null;
    prognose: number | null;
    avvik: number | null;
}

interface BeregningRow {
    property_id: string;
    name: string;
    region: string;
    category: string;
    category_display: string;
    is_gjennomstromning: boolean;
    gl_2021: number | null;
    gl_2022: number | null;
    gl_2023: number | null;
    gl_2024: number | null;
    gl_2025: number | null;
    n_years: number;
    cold_start: boolean;
    outlier_capped: boolean;
    outlier_capped_years: number[];
    alpha: number;
    beta: number;
    phi: number;
    horizon: number;
    L_init: number | null;
    T_init: number | null;
    L_final: number | null;
    T_final: number | null;
    phi_sum: number | null;
    hw_raw: number | null;
    method: string;
    constraint: string;
    pred_hw: number | null;
    pred_final: number | null;
    change_2527_pct: number | null;
    steps: HWStep[];
}

interface Beregning {
    scenario: string;
    modell_parametre: {
        alpha: number; beta: number; phi: number; horizon: number;
        phi_sum: number; max_annual_growth_pst: number;
        max_growth_factor: number; cold_start_ratio: number;
        inflation: number; history_from: number; history_to: number; target_year: number;
    };
    formel: {
        L_t: string; T_t: string; forecast: string; phi_sum_verdi: string;
    };
    antall_rader: number;
    rows: BeregningRow[];
}

// ── Tab bar ───────────────────────────────────────────────────────────────────

const TABS = [
    "Antagelser",
    "Sammendrag",
    "Per region",
    "Per kategori",
    "Lønn",
    "Alle eiendommer",
    "Outliers",
    "Backtesting",
    "Beregningsdetaljer",
    "Metodikk",
    "Begrepsoversikt",
] as const;

type Tab = (typeof TABS)[number];

function TabBar({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
    return (
        <div className="overflow-x-auto border-b border-gray-200 mb-6">
            <div className="flex gap-0 min-w-max">
                {TABS.map((t) => (
                    <button
                        key={t}
                        onClick={() => onChange(t)}
                        className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
                            active === t
                                ? "border-teal-600 text-teal-700 bg-teal-50/50"
                                : "border-transparent text-gray-600 hover:text-teal-700 hover:border-teal-300"
                        }`}
                    >
                        {t}
                    </button>
                ))}
            </div>
        </div>
    );
}

function Section({ title, children }: { title?: string; children: React.ReactNode }) {
    return (
        <section className="space-y-4">
            {title && <h2 className="text-base font-semibold text-gray-900">{title}</h2>}
            {children}
        </section>
    );
}

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
    return (
        <th className={`px-4 py-2 text-xs font-semibold text-gray-600 uppercase tracking-wide ${right ? "text-right" : "text-left"}`}>
            {children}
        </th>
    );
}

function Td({ children, right, bold, className }: { children: React.ReactNode; right?: boolean; bold?: boolean; className?: string }) {
    return (
        <td className={`px-4 py-2 text-sm ${right ? "text-right tabular-nums" : ""} ${bold ? "font-semibold" : ""} ${className ?? ""}`}>
            {children}
        </td>
    );
}

// ── Metode-badge ──────────────────────────────────────────────────────────────

function MetodeBadge({ isGjennomstromning }: { isGjennomstromning: boolean }) {
    if (isGjennomstromning) {
        return (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800 ml-1" title="Bruker inflasjonsfallback — ikke Holt-Winters trendmodell">
                Inflasjon
            </span>
        );
    }
    return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-teal-100 text-teal-800 ml-1" title="Holt-Winters dempet trendmodell">
            HW
        </span>
    );
}

// ── Tab 1: Antagelser ─────────────────────────────────────────────────────────

function TabAntagelser({ data }: { data: Antagelser }) {
    return (
        <Section title="Modellparametre og antagelser">
            <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full">
                    <thead className="bg-gray-50">
                        <tr>
                            <Th>Parameter</Th>
                            <Th>Verdi</Th>
                            <Th>Beskrivelse</Th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        <tr><Td bold>Modell</Td><Td>{data.modell}</Td><Td className="text-gray-500">Prediksjonsmotoren</Td></tr>
                        <tr><Td bold>Alpha (α)</Td><Td>{data.alpha}</Td><Td className="text-gray-500">Nivå-glattning — høyere vekter nyere data</Td></tr>
                        <tr><Td bold>Beta (β)</Td><Td>{data.beta}</Td><Td className="text-gray-500">Trend-glattning</Td></tr>
                        <tr><Td bold>Phi (φ)</Td><Td>{data.phi}</Td><Td className="text-gray-500">Dempingsfaktor for trend</Td></tr>
                        <tr><Td bold>Historikk</Td><Td>{data.history_from}–{data.history_to}</Td><Td className="text-gray-500">År med GL-data brukt som grunnlag</Td></tr>
                        <tr><Td bold>Inflasjon 2027</Td><Td>{(data.inflasjon_2027 * 100).toFixed(1).replace(".", ",")} %</Td><Td className="text-gray-500">KPI-fallback (SSB) for Gjennomstrømning og kaldt-start eiendommer</Td></tr>
                        <tr><Td bold>Passthrough</Td><Td>{data.passthrough_kategorier.join(", ")}</Td><Td className="text-gray-500">{data.passthrough_forklaring}</Td></tr>
                    </tbody>
                </table>
            </div>

            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                <strong>Metodebadger i tabellene:</strong>{" "}
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-teal-100 text-teal-800 mx-1">HW</span>
                = Holt-Winters dempet trendmodell (α=0,5 β=0,2 φ=0,85).{" "}
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800 mx-1">Inflasjon</span>
                = Siste faktiske beløp × SSB KPI (3,5 %). Brukes for Gjennomstrømning/omposteringer og eiendommer med {"<"} 3 år historikk.
            </div>

            <div className="mt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Scenarioer</h3>
                <div className="flex flex-col gap-2">
                    {data.scenarioer.map((s) => (
                        <div key={s.navn} className="flex items-start gap-3 p-3 rounded-lg bg-teal-50 border border-teal-100">
                            <span className="font-mono text-xs font-bold text-teal-700 mt-0.5">{s.navn}</span>
                            <span className="text-sm text-gray-700">{s.beskrivelse}</span>
                        </div>
                    ))}
                </div>
            </div>

            <p className="text-xs text-gray-500 mt-2">Generert: {data.generert}</p>
        </Section>
    );
}

// ── Tab 2: Sammendrag ─────────────────────────────────────────────────────────

function TabSammendrag({ data }: { data: Sammenligning }) {
    const { totals, categories } = data;

    return (
        <Section>
            {/* Info-boks om Gjennomstrømning */}
            <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                <Info className="w-4 h-4 mt-0.5 shrink-0 text-blue-600" />
                <div>
                    <strong>Gjennomstrømning er skilt ut</strong> — omposteringer (husleieoverføringer, internfakturering)
                    varierer erratisk år til år og er ikke egnet for trendmodellering. De bruker inflasjonsfallback (3,5 %)
                    og er vist separat under for transparens. Driftskostnader = Drift + Vedlikehold.
                </div>
            </div>

            {/* KPI-kort: Driftskostnader (Drift + Vedlikehold) */}
            <h3 className="text-sm font-semibold text-gray-700 mt-2">Driftskostnader (Drift + Vedlikehold)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-xl border border-gray-200 bg-white p-5">
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">2025 faktisk (GL)</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{fmtMrd(totals.drift_actual_2025)}</p>
                    <p className="text-xs text-gray-400 mt-1">Regnskapsdata fra Agresso</p>
                </div>
                <div className="rounded-xl border border-teal-300 bg-teal-50 p-5">
                    <p className="text-xs uppercase tracking-wide text-teal-700 font-medium">2027 prediksjon</p>
                    <p className="text-3xl font-bold text-teal-800 mt-2">{fmtMrd(totals.drift_pred_2027)}</p>
                    {totals.drift_change_pct != null && (
                        <p className={`text-sm mt-1 font-medium ${deltaClass(totals.drift_change_pct)}`}>
                            {fmtPst(totals.drift_change_pct)} vs 2025
                        </p>
                    )}
                    <p className="text-xs text-teal-600 mt-1">Holt-Winters dempet trend</p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-white p-5">
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">Endring 2025 → 2027</p>
                    <p className={`text-3xl font-bold mt-2 ${deltaClass(totals.drift_change_pct)}`}>
                        {fmtPst(totals.drift_change_pct)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Inkl. inflasjon og trenddemping</p>
                </div>
            </div>

            {/* KPI-kort: Gjennomstrømning */}
            <h3 className="text-sm font-semibold text-amber-700 mt-4">Gjennomstrømning / Lokaler (omposteringer)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                    <p className="text-xs uppercase tracking-wide text-amber-600 font-medium">2025 faktisk (GL)</p>
                    <p className="text-3xl font-bold text-amber-800 mt-2">{fmtMrd(totals.gjstrom_actual_2025)}</p>
                </div>
                <div className="rounded-xl border border-amber-300 bg-amber-50 p-5">
                    <p className="text-xs uppercase tracking-wide text-amber-700 font-medium">2027 prediksjon</p>
                    <p className="text-3xl font-bold text-amber-800 mt-2">{fmtMrd(totals.gjstrom_pred_2027)}</p>
                    <p className="text-xs text-amber-600 mt-1">Inflasjonsfallback (3,5 % SSB)</p>
                </div>
                <div className="rounded-xl border border-amber-200 bg-white p-5">
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">Endring 2025 → 2027</p>
                    <p className={`text-3xl font-bold mt-2 ${deltaClass(totals.gjstrom_change_pct)}`}>
                        {fmtPst(totals.gjstrom_change_pct)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Kun KPI-justert, ingen trend</p>
                </div>
            </div>

            {/* Totalt */}
            <div className="rounded-xl border border-gray-300 bg-gray-50 p-4 flex items-center justify-between">
                <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">Totalt alle kategorier 2027</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{fmtMrd(totals.pred_2027)}</p>
                </div>
                <div className="text-right">
                    <p className="text-xs text-gray-500">vs faktisk 2025 ({fmtMrd(totals.actual_2025)})</p>
                    <p className={`text-lg font-bold ${deltaClass(totals.change_2527_pct)}`}>
                        {fmtPst(totals.change_2527_pct)}
                    </p>
                </div>
            </div>

            {/* Kategoritabell */}
            <h2 className="text-base font-semibold text-gray-900 mt-4 mb-2">Per kategori</h2>
            <CategoryTable categories={categories} />
        </Section>
    );
}

function CategoryTable({ categories }: { categories: SammenligningCategory[] }) {
    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full">
                <thead className="bg-gray-50">
                    <tr>
                        <Th>Kategori</Th>
                        <Th>Metode</Th>
                        <Th right>2025 faktisk (GL)</Th>
                        <Th right>2027 prediksjon</Th>
                        <Th right>Δ 25→27 %</Th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {categories.map((c) => (
                        <tr key={c.category} className={`hover:bg-gray-50 ${c.is_gjennomstromning ? "bg-amber-50/30" : ""}`}>
                            <Td bold>{c.category}</Td>
                            <Td>
                                <MetodeBadge isGjennomstromning={c.is_gjennomstromning} />
                            </Td>
                            <Td right>{fmtKr(c.actual_2025)}</Td>
                            <Td right bold>{fmtKr(c.pred_2027)}</Td>
                            <Td right className={deltaClass(c.change_2527_pct)}>
                                {fmtPstSafe(c.change_2527_pct, c.actual_2025)}
                            </Td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// ── Tab 3: Per region ─────────────────────────────────────────────────────────

function RegionTable({ regions }: { regions: SammenligningRegion[] }) {
    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full">
                <thead className="bg-gray-50">
                    <tr>
                        <Th>Region</Th>
                        <Th right>2025 faktisk (GL)</Th>
                        <Th right>2027 prediksjon</Th>
                        <Th right>Δ 25→27 %</Th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {regions.map((r) => (
                        <tr key={r.region} className="hover:bg-gray-50">
                            <Td bold>{r.region}</Td>
                            <Td right>{fmtKr(r.actual_2025)}</Td>
                            <Td right bold>{fmtKr(r.pred_2027)}</Td>
                            <Td right className={deltaClass(r.change_2527_pct)}>
                                {fmtPstSafe(r.change_2527_pct, r.actual_2025)}
                            </Td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function TabPerRegion({ data }: { data: Sammenligning }) {
    return (
        <Section title="Regionale aggregater — 2025 faktisk vs 2027 prediksjon">
            <RegionTable regions={data.regions} />
            <p className="text-xs text-gray-500 mt-2">
                Alle kategorier inkludert (Drift + Vedlikehold + Gjennomstrømning). Δ % vises ikke der
                regionen har for liten base (&lt; 200 000 kr). Sortert etter 2027-prediksjon.
            </p>
        </Section>
    );
}

// ── Tab 4: Per kategori ───────────────────────────────────────────────────────

function TabPerKategori({ data }: { data: Sammenligning }) {
    const cats = data.categories;
    const max2027 = Math.max(...cats.map((c) => c.pred_2027 ?? c.actual_2025));

    return (
        <Section title="Kostnadskategorier — fordeling og utvikling">
            <CategoryTable categories={cats} />

            <h3 className="text-sm font-semibold text-gray-700 mt-6 mb-3">
                Relativ størrelse per kategori — 2027 prediksjon
            </h3>
            <div className="space-y-2">
                {cats.map((c) => {
                    const val = c.pred_2027 ?? c.actual_2025;
                    const pct = max2027 > 0 ? (val / max2027) * 100 : 0;
                    return (
                        <div key={c.category} className="flex items-center gap-3">
                            <span className="text-sm text-gray-700 w-48 shrink-0 truncate" title={c.category}>
                                {c.category}
                            </span>
                            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                                <div
                                    className={`h-5 rounded-full transition-all ${c.is_gjennomstromning ? "bg-amber-400" : "bg-teal-500"}`}
                                    style={{ width: `${pct.toFixed(1)}%` }}
                                />
                            </div>
                            <span className="text-sm tabular-nums text-gray-600 w-32 text-right">{fmtKr(val)}</span>
                            <MetodeBadge isGjennomstromning={c.is_gjennomstromning} />
                        </div>
                    );
                })}
            </div>
        </Section>
    );
}

// ── Tab 5: Lønn ───────────────────────────────────────────────────────────────

function TabLonn({ data }: { data: Prediksjon2027 }) {
    return (
        <Section title="Lønnskostnader — prediksjon 2027">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-5">
                    <p className="text-xs uppercase tracking-wide text-rose-600 font-medium">Lønn 2025 (faktisk)</p>
                    <p className="text-3xl font-bold text-rose-700 mt-2">
                        {data.lonn_2025 > 0 ? fmtMrd(data.lonn_2025) : "—"}
                    </p>
                </div>
                <div className="rounded-xl border border-rose-300 bg-rose-100 p-5">
                    <p className="text-xs uppercase tracking-wide text-rose-700 font-medium">Lønn 2027 (prediksjon)</p>
                    <p className="text-3xl font-bold text-rose-800 mt-2">
                        {data.lonn_generert ? fmtMrd(data.lonn_2027) : "Ikke generert"}
                    </p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-white p-5">
                    <p className="text-xs uppercase tracking-wide text-gray-500 font-medium">Endring 2025 → 2027</p>
                    <p className={`text-3xl font-bold mt-2 ${deltaClass(data.lonn_endring_pst)}`}>
                        {fmtPst(data.lonn_endring_pst)}
                    </p>
                </div>
            </div>

            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                <strong>Merk:</strong> Detaljerte lønnsdata per eiendom finnes i Excel-eksporten.
            </div>
        </Section>
    );
}

// ── Tab 6: Alle eiendommer ────────────────────────────────────────────────────

function TabAlleEiendommer({ properties }: { properties: SammenligningProperty[] }) {
    const [search, setSearch] = useState("");
    const [regionFilter, setRegionFilter] = useState("");
    const [skjulGjennomstromning, setSkjulGjennomstromning] = useState(false);
    const [visibleCount, setVisibleCount] = useState(100);

    const regions = useMemo(() => {
        const s = new Set(properties.map((p) => p.region));
        return Array.from(s).sort();
    }, [properties]);

    const filtered = useMemo(() => {
        let list = properties;
        if (skjulGjennomstromning) {
            list = list.filter((p) => !p.is_gjennomstromning);
        }
        if (search.trim()) {
            const q = search.toLowerCase();
            list = list.filter((p) => p.name.toLowerCase().includes(q));
        }
        if (regionFilter) {
            list = list.filter((p) => p.region === regionFilter);
        }
        return list;
    }, [properties, search, regionFilter, skjulGjennomstromning]);

    const visible = filtered.slice(0, visibleCount);

    return (
        <Section title="Alle eiendommer">
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 mb-3">
                <strong>Δ 25→27 %</strong> sammenligner Prediksjon 2027 direkte med GL 2025.
                Vises som «—» der GL 2025 er under 200 000 kr (for liten base) eller endringen er over 300 %
                (typisk omposteringer med erratisk historikk).
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-teal-100 text-teal-800 mx-1">HW</span>= Holt-Winters.
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 text-amber-800 mx-1">Inflasjon</span>= KPI-fallback.
            </div>
            <div className="flex flex-col sm:flex-row gap-3 mb-4 flex-wrap">
                <input
                    type="text"
                    placeholder="Søk på eiendomsnavn…"
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setVisibleCount(100); }}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm flex-1 min-w-48 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <select
                    value={regionFilter}
                    onChange={(e) => { setRegionFilter(e.target.value); setVisibleCount(100); }}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                    <option value="">Alle regioner</option>
                    {regions.map((r) => (
                        <option key={r} value={r}>{r}</option>
                    ))}
                </select>
                <button
                    onClick={() => { setSkjulGjennomstromning((v) => !v); setVisibleCount(100); }}
                    className={`px-3 py-2 rounded-lg text-sm border transition-colors whitespace-nowrap ${
                        skjulGjennomstromning
                            ? "bg-teal-600 text-white border-teal-600"
                            : "bg-white text-gray-700 border-gray-300 hover:border-teal-400"
                    }`}
                >
                    {skjulGjennomstromning ? "✓ Viser kun Drift + Vedlikehold" : "Skjul Gjennomstrømning"}
                </button>
            </div>
            <p className="text-xs text-gray-500 mb-2">
                Viser {Math.min(visibleCount, filtered.length)} av {filtered.length} rader
                {filtered.length !== properties.length && ` (${properties.length} totalt)`}
            </p>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full">
                    <thead className="bg-gray-50">
                        <tr>
                            <Th>Eiendom</Th>
                            <Th>Region</Th>
                            <Th>Kategori</Th>
                            <Th>Metode</Th>
                            <Th right>2025 faktisk (GL)</Th>
                            <Th right>2027 prediksjon</Th>
                            <Th right>Δ 25→27 %</Th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {visible.map((p) => (
                            <tr
                                key={`${p.property_id}-${p.category}`}
                                className={`hover:bg-gray-50 ${p.is_gjennomstromning ? "bg-amber-50/20" : ""}`}
                            >
                                <Td className="max-w-xs truncate font-medium" bold>
                                    <span title={p.name}>{p.name}</span>
                                </Td>
                                <Td className="text-gray-500">{p.region}</Td>
                                <Td className="text-gray-500">{p.category}</Td>
                                <Td>
                                    <MetodeBadge isGjennomstromning={p.is_gjennomstromning} />
                                </Td>
                                <Td right>{fmtKr(p.actual_2025)}</Td>
                                <Td right bold>{fmtKr(p.pred_2027)}</Td>
                                <Td right className={deltaClass(p.change_2527_pct)}>
                                    {fmtPstSafe(p.change_2527_pct, p.actual_2025)}
                                </Td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {filtered.length > visibleCount && (
                <button
                    onClick={() => setVisibleCount((v) => v + 100)}
                    className="mt-3 px-4 py-2 text-sm border border-teal-600 text-teal-700 rounded-lg hover:bg-teal-50 transition-colors"
                >
                    Vis flere ({filtered.length - visibleCount} gjenstår)
                </button>
            )}
        </Section>
    );
}

// ── Tab 7: Outliers ───────────────────────────────────────────────────────────

function TabOutliers({ properties }: { properties: SammenligningProperty[] }) {
    const outliers = useMemo(() => {
        return properties
            .filter((p) => {
                if (p.is_gjennomstromning) return false;          // omposteringer ekskludert
                if (p.actual_2025 < 200_000) return false;        // for liten base
                const pct = p.change_2527_pct ?? 0;
                return Math.abs(pct) > 15 && Math.abs(pct) <= 300;
            })
            .sort((a, b) => Math.abs(b.change_2527_pct ?? 0) - Math.abs(a.change_2527_pct ?? 0));
    }, [properties]);

    return (
        <Section title="Outliers — eiendommer med stor endring 2025 → 2027">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-4">
                <strong>Hva er outliers?</strong> Eiendommer der Holt-Winters prediksjon 2027 avviker mer enn 15 %
                fra faktisk GL 2025, med GL-base over 200 000 kr. Gjennomstrømning er ekskludert (omposteringer
                er ikke trendmodellert). Disse bør kontrolleres manuelt — mulige årsaker: lav historikk,
                engangsutgifter i 2025, eller manglende koststedskoblinger.
            </div>
            <p className="text-xs text-gray-500 mb-2">{outliers.length} eiendommer med reell endring &gt; 15 %</p>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full">
                    <thead className="bg-gray-50">
                        <tr>
                            <Th>Eiendom</Th>
                            <Th>Region</Th>
                            <Th>Kategori</Th>
                            <Th right>2025 faktisk</Th>
                            <Th right>2027 pred.</Th>
                            <Th right>Δ 25→27 %</Th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {outliers.map((p) => (
                            <tr key={`${p.property_id}-${p.category}`} className="hover:bg-gray-50">
                                <Td bold className="max-w-xs truncate">
                                    <span title={p.name}>{p.name}</span>
                                </Td>
                                <Td className="text-gray-500">{p.region}</Td>
                                <Td className="text-gray-500">{p.category}</Td>
                                <Td right>{fmtKr(p.actual_2025)}</Td>
                                <Td right bold>{fmtKr(p.pred_2027)}</Td>
                                <Td right className={deltaClass(p.change_2527_pct)}>
                                    {fmtPst(p.change_2527_pct)}
                                </Td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Section>
    );
}

// ── Tab 8: Backtesting ────────────────────────────────────────────────────────

function TabBacktesting({ apiBase }: { apiBase: string }) {
    return (
        <Section title="Backtesting og validering">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800 mb-4">
                MAPE-validering er beregnet i Excel-eksporten. Last ned Excel for fullstendige backtesting-resultater.
            </div>

            <div className="overflow-x-auto rounded-lg border border-gray-200 mb-4">
                <table className="w-full">
                    <thead className="bg-gray-50">
                        <tr>
                            <Th>Begrep</Th>
                            <Th>Definisjon</Th>
                            <Th>Tolkning</Th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        <tr className="hover:bg-gray-50"><Td bold>MAPE</Td><Td>Mean Absolute Percentage Error</Td><Td className="text-gray-500">Gjennomsnittlig absolutt prosentvis feil</Td></tr>
                        <tr className="hover:bg-gray-50"><Td bold>{"< 10 %"}</Td><Td>Svært god prediksjon</Td><Td className="text-gray-500">Akseptabelt for budsjettering</Td></tr>
                        <tr className="hover:bg-gray-50"><Td bold>10–20 %</Td><Td>God prediksjon</Td><Td className="text-gray-500">Bør varsles i rapport</Td></tr>
                        <tr className="hover:bg-gray-50"><Td bold>{"> 20 %"}</Td><Td>Usikker prediksjon</Td><Td className="text-gray-500">Manuell gjennomgang anbefalt</Td></tr>
                        <tr className="hover:bg-gray-50"><Td bold>Holdout-periode</Td><Td>2024 (tilbakeholdt fra trening)</Td><Td className="text-gray-500">Modellen er trent på 2021–2023</Td></tr>
                    </tbody>
                </table>
            </div>

            <a
                href={`${apiBase}/api/v1/financials/prediksjon/export.xlsx?scenario=xgb70`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700 transition-colors"
            >
                Last ned Excel med backtesting-resultater
            </a>
        </Section>
    );
}

// ── Tab 9: Metodikk ───────────────────────────────────────────────────────────

function TabMetodikk() {
    return (
        <Section title="Metodikk og analyse">
            <div className="prose prose-sm max-w-none space-y-4 text-gray-700">
                <div className="p-5 bg-teal-50 border border-teal-200 rounded-lg">
                    <h3 className="font-semibold text-teal-800 mb-2">Hensikt</h3>
                    <p>
                        Rapporten gir grunnlag for budsjett­prediksjon for 2027 for Bufetat Eiendoms­forvaltning.
                        Prediksjonen benyttes som teknisk støtte ved utarbeidelse av drifts­budsjett,
                        og er ikke et godkjent budsjetttall. Endelig budsjett fastsettes av eiendomsseksjonen.
                    </p>
                </div>

                <div className="p-5 bg-white border border-gray-200 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-2">Modell: Holt-Winters dobbel eksponentiell utjevning</h3>
                    <p>
                        Brukes for <strong>Drift</strong> og <strong>Vedlikehold</strong> med ≥ 3 år GL-historikk:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-gray-600">
                        <li><strong>α = 0,5</strong> — balansert vekting av historikk og nyere data</li>
                        <li><strong>β = 0,2</strong> — moderat trend-glattning</li>
                        <li><strong>φ = 0,85</strong> — dempingsfaktor for å unngå eksplosiv trendekstrapolasjon</li>
                        <li>Maks vekst per år: 8 % (sikkerhetstak)</li>
                        <li>Maks prediksjon: 5 × siste faktiske år</li>
                    </ul>
                </div>

                <div className="p-5 bg-amber-50 border border-amber-200 rounded-lg">
                    <h3 className="font-semibold text-amber-800 mb-2">Gjennomstrømning / Omposteringer — inflasjonsfallback</h3>
                    <p className="text-amber-800">
                        Kategorien <strong>Lokaler / Gjennomstrømning</strong> (<em>srs_kategori = Gjennomstrømning/Lokaler</em>)
                        behandles med inflasjonsfallback, <strong>ikke</strong> Holt-Winters trendmodell. Årsak:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-amber-700">
                        <li>Omposteringer er interne regnskapskorrigeringer — ikke operativ kostnad</li>
                        <li>Husleieoverføringer mellom regioner nulles ut på organisasjonsnivå</li>
                        <li>Varierer erratisk år til år — ingen meningsfull trend å ekstrapolere</li>
                    </ul>
                    <p className="mt-2 text-amber-800">
                        <strong>Metode:</strong> siste faktiske GL-beløp × SSB KPI (3,5 %). Gjennomstrømning er
                        vist separat i Sammendrag for transparens.
                    </p>
                </div>

                <div className="p-5 bg-white border border-gray-200 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-2">Inflasjonsfallback (øvrige tilfeller)</h3>
                    <p>
                        Brukes også for Drift/Vedlikehold der:
                    </p>
                    <ul className="list-disc list-inside mt-2 space-y-1 text-gray-600">
                        <li>Eiendom har {"<"} 3 år GL-historikk</li>
                        <li>Kald-start: siste år {">"} 1,5 × historisk snitt (rask oppramp)</li>
                        <li>Negativ trend som vil gi implausibel lav prediksjon</li>
                    </ul>
                </div>

                <div className="p-5 bg-white border border-gray-200 rounded-lg">
                    <h3 className="font-semibold text-gray-800 mb-2">Endring-% tolkning</h3>
                    <p>
                        Alle %-endringer i denne rapporten sammenligner <strong>Prediksjon 2027 vs faktisk GL 2025</strong>
                        (25→27). Det er to år — noe vekst er forventet selv uten reell endring.
                        «—» vises der GL 2025 {"<"} 200 000 kr (for liten base) eller endring {">"} 300 % (støy).
                    </p>
                </div>

                <div className="p-5 bg-amber-50 border border-amber-200 rounded-lg">
                    <h3 className="font-semibold text-amber-800 mb-2">Begrensninger</h3>
                    <ul className="list-disc list-inside space-y-1 text-amber-700">
                        <li>Modellen tar ikke hensyn til nybygg eller avvikling av eiendommer etter 2025</li>
                        <li>Vesentlige strukturendringer (oppussing, kapasitetsøkning) reflekteres ikke</li>
                        <li>Politiske vedtak etter april 2026 er ikke innarbeidet</li>
                        <li>Lønnskostnader er separat modellert og ikke inkludert i driftsbudsjettet</li>
                        <li>Tallene er maskinelle estimater — ikke revisorgodkjente budsjetttall</li>
                    </ul>
                </div>
            </div>
        </Section>
    );
}

// ── Tab 10: Beregningsdetaljer ────────────────────────────────────────────────

/** Formateringshjelpere for store tall (kortformat) */
function fmtShort(n: number | null | undefined): string {
    if (n == null) return "—";
    const abs = Math.abs(n);
    if (abs >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(".", ",") + " M";
    if (abs >= 1_000) return (n / 1_000).toFixed(0) + " k";
    return n.toFixed(0);
}

const METHOD_LABELS: Record<string, string> = {
    "holt_linear_damped":              "HW (dempet trend)",
    "holt_linear_damped_outlier_capped": "HW (dempet + outlier-kap)",
    "negative_trend_floor":            "HW → negativ gulv",
    "output_ratio_fallback":           "HW → output-ratio fallback",
    "annual_growth_capped":            "HW → vekstkap 8%/år",
    "inflation_passthrough":           "Inflasjon (passthrough)",
    "inflation_coldstart":             "Inflasjon (kald start)",
    "inflation_fallback":              "Inflasjon (fallback)",
};

function MethodPill({ method }: { method: string }) {
    const isHW = method.startsWith("holt_linear");
    return (
        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            isHW
                ? "bg-teal-100 text-teal-800"
                : "bg-amber-100 text-amber-800"
        }`}>
            {METHOD_LABELS[method] ?? method}
        </span>
    );
}

/** Én-rad-per-år steg-tabell som expanderes under eiendomsraden */
function StepTable({ steps, outlierYears, phi_sum }: {
    steps: HWStep[];
    outlierYears: number[];
    phi_sum: number | null;
}) {
    const TARGET = 2027;
    return (
        <table className="w-full text-xs border-collapse">
            <thead>
                <tr className="bg-gray-100">
                    <th className="px-3 py-1.5 text-left font-semibold text-gray-600">År</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-gray-600">GL faktisk</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-gray-600">GL CPI-just.</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-teal-700">Level (L)</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-teal-700">Trend (T)</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-blue-700">Prognose (t+1)</th>
                    <th className="px-3 py-1.5 text-right font-semibold text-gray-600">Avvik</th>
                </tr>
            </thead>
            <tbody>
                {steps.map((s, i) => {
                    const isPred    = s.year === TARGET;
                    const isOutlier = outlierYears.includes(s.year);
                    const isInit    = i === 0 && !isPred;
                    const rowCls = isPred
                        ? "bg-green-50 border-t-2 border-green-300"
                        : isOutlier
                        ? "bg-orange-50"
                        : isInit
                        ? "bg-blue-50"
                        : "hover:bg-gray-50";
                    return (
                        <tr key={s.year} className={rowCls}>
                            <td className={`px-3 py-1.5 font-mono ${isPred ? "font-bold text-green-800" : isInit ? "text-blue-700" : "text-gray-700"}`}>
                                {isPred ? "→ 2027" : s.year}
                                {isInit && <span className="ml-1 text-blue-400 text-xs">init</span>}
                                {isOutlier && <span className="ml-1 text-orange-500 text-xs">⊕winsor</span>}
                            </td>
                            <td className="px-3 py-1.5 text-right tabular-nums text-gray-600">{fmtKr(s.gl_raw)}</td>
                            <td className="px-3 py-1.5 text-right tabular-nums text-gray-500">{fmtKr(s.gl_cpi)}</td>
                            <td className={`px-3 py-1.5 text-right tabular-nums font-mono ${s.L != null ? "text-teal-700" : "text-gray-300"}`}>{fmtKr(s.L)}</td>
                            <td className={`px-3 py-1.5 text-right tabular-nums font-mono ${s.T != null ? "text-teal-700" : "text-gray-300"}`}>{fmtKr(s.T)}</td>
                            <td className={`px-3 py-1.5 text-right tabular-nums font-mono ${isPred ? "font-bold text-green-700" : s.prognose != null ? "text-blue-600" : "text-gray-300"}`}>
                                {isPred && phi_sum != null && s.prognose != null
                                    ? `L + ${phi_sum}×T = ${fmtKr(s.prognose)}`
                                    : fmtKr(s.prognose)}
                            </td>
                            <td className={`px-3 py-1.5 text-right tabular-nums ${s.avvik != null ? (s.avvik >= 0 ? "text-green-600" : "text-red-500") : "text-gray-300"}`}>
                                {s.avvik != null ? (s.avvik >= 0 ? "+" : "") + fmtKr(s.avvik) : "—"}
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    );
}

function TabBeregning({
    data,
    loading,
}: {
    data: Beregning | null;
    loading: boolean;
}) {
    const [search, setSearch] = useState("");
    const [catFilter, setCatFilter] = useState<string>("alle");
    const [showGjstrom, setShowGjstrom] = useState(false);
    const [showFormulas, setShowFormulas] = useState(false);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const toggleExpand = (key: string) =>
        setExpanded((prev) => {
            const next = new Set(prev);
            next.has(key) ? next.delete(key) : next.add(key);
            return next;
        });

    const filtered = useMemo(() => {
        if (!data) return [];
        return data.rows.filter((r) => {
            if (!showGjstrom && r.is_gjennomstromning) return false;
            if (catFilter !== "alle" && r.category !== catFilter) return false;
            if (search) {
                const q = search.toLowerCase();
                if (!r.name.toLowerCase().includes(q) && !r.property_id.toLowerCase().includes(q) && !r.region.toLowerCase().includes(q)) return false;
            }
            return true;
        });
    }, [data, search, catFilter, showGjstrom]);

    if (loading) {
        return (
            <div className="flex items-center gap-3 py-12 justify-center">
                <div className="w-6 h-6 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-gray-500">Laster beregningsdetaljer…</span>
            </div>
        );
    }
    if (!data) return <p className="text-sm text-gray-500 py-6">Ingen data</p>;

    const mp = data.modell_parametre;

    return (
        <Section title="Beregningsdetaljer — HW steg-for-steg per eiendom">
            {/* Formel-boks */}
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg text-sm">
                <button
                    onClick={() => setShowFormulas((v) => !v)}
                    className="font-semibold text-teal-800 flex items-center gap-2"
                >
                    <span>{showFormulas ? "▼" : "▶"}</span> Holt-Winters formler og parametre
                </button>
                {showFormulas && (
                    <div className="mt-3 space-y-3 text-teal-900">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <p className="font-medium mb-1">Modell-parametre</p>
                                <table className="text-xs w-full">
                                    <tbody>
                                        <tr><td className="pr-4 text-gray-600">α (alpha)</td><td className="font-mono font-semibold">{mp.alpha}</td><td className="text-gray-500 pl-2">nivå-glattning</td></tr>
                                        <tr><td className="pr-4 text-gray-600">β (beta)</td><td className="font-mono font-semibold">{mp.beta}</td><td className="text-gray-500 pl-2">trend-glattning</td></tr>
                                        <tr><td className="pr-4 text-gray-600">φ (phi)</td><td className="font-mono font-semibold">{mp.phi}</td><td className="text-gray-500 pl-2">dempingsfaktor</td></tr>
                                        <tr><td className="pr-4 text-gray-600">h (horizon)</td><td className="font-mono font-semibold">{mp.horizon}</td><td className="text-gray-500 pl-2">år fremover</td></tr>
                                        <tr><td className="pr-4 text-gray-600">φ_sum</td><td className="font-mono font-semibold">{mp.phi_sum}</td><td className="text-gray-500 pl-2">φ¹ + φ²</td></tr>
                                        <tr><td className="pr-4 text-gray-600">Maks vekst/år</td><td className="font-mono font-semibold">{mp.max_annual_growth_pst} %</td><td className="text-gray-500 pl-2">sikkerhetstak</td></tr>
                                        <tr><td className="pr-4 text-gray-600">Historikk</td><td className="font-mono font-semibold">{mp.history_from}–{mp.history_to}</td><td className="text-gray-500 pl-2">treningsperiode</td></tr>
                                    </tbody>
                                </table>
                            </div>
                            <div>
                                <p className="font-medium mb-1">Formelsteg</p>
                                <div className="font-mono text-xs space-y-1 bg-teal-100 p-3 rounded">
                                    <p className="text-gray-500">{"Init: L₀ = y₁,  T₀ = (yₙ − y₁) / (n−1)"}</p>
                                    <p className="text-teal-900">{"L_t  = α·y_t + (1−α)·(L_(t−1) + φ·T_(t−1))"}</p>
                                    <p className="text-teal-900">{"T_t  = β·(L_t − L_(t−1)) + (1−β)·φ·T_(t−1)"}</p>
                                    <p className="text-teal-900 font-bold">{"Pred = L_n + φ_sum·T_n"}</p>
                                    <p className="text-teal-800 mt-1">{`     = L_n + ${mp.phi_sum}·T_n`}</p>
                                </div>
                                <p className="text-xs text-gray-500 mt-2">CPI-justert til {mp.history_to}-NOK (SSB KPI 2015=100). Siste år aldri winsorisert.</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Filtre */}
            <div className="flex flex-wrap gap-3 items-center">
                <input
                    type="text"
                    placeholder="Søk eiendom, region…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-teal-400"
                />
                <select
                    value={catFilter}
                    onChange={(e) => setCatFilter(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
                >
                    <option value="alle">Alle kategorier</option>
                    <option value="operations">Drift</option>
                    <option value="investment">Vedlikehold</option>
                    <option value="property">Lokaler / Gjennomstrømning</option>
                    <option value="other">Annet</option>
                </select>
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                    <input type="checkbox" checked={showGjstrom} onChange={(e) => setShowGjstrom(e.target.checked)} className="accent-amber-600" />
                    Vis Gjennomstrømning
                </label>
                <span className="ml-auto text-xs text-gray-500">{filtered.length} av {data.antall_rader} rader · klikk rad for å se år-for-år steg</span>
            </div>

            {/* Eiendom-kort med ekspanderbare steg */}
            <div className="space-y-2">
                {filtered.map((r) => {
                    const key = `${r.property_id}-${r.category}`;
                    const isOpen = expanded.has(key);
                    const isHW = r.method.startsWith("holt_linear");
                    return (
                        <div key={key} className={`rounded-lg border overflow-hidden ${r.is_gjennomstromning ? "border-amber-200" : "border-gray-200"}`}>
                            {/* Sammendragsrad — klikk for å ekspandere */}
                            <button
                                onClick={() => toggleExpand(key)}
                                className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                                    r.is_gjennomstromning ? "bg-amber-50 hover:bg-amber-100" : isHW ? "bg-teal-50/60 hover:bg-teal-100/60" : "bg-gray-50 hover:bg-gray-100"
                                }`}
                            >
                                <span className="text-gray-400 text-xs w-4">{isOpen ? "▼" : "▶"}</span>
                                <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-0.5">
                                    <span className="font-semibold text-sm text-gray-900 col-span-2 sm:col-span-1">{r.name}</span>
                                    <span className="text-xs text-gray-500">{r.region}</span>
                                    <span className="text-xs text-gray-500">{r.category_display}</span>
                                    <span><MethodPill method={r.method} /></span>
                                </div>
                                <div className="shrink-0 flex items-center gap-4 text-right">
                                    <div>
                                        <p className="text-xs text-gray-400">GL 2025</p>
                                        <p className="text-sm font-mono font-semibold text-gray-700">{fmtShort(r.gl_2025)}</p>
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-400">Pred 2027</p>
                                        <p className="text-sm font-mono font-semibold text-teal-700">{fmtShort(r.pred_final)}</p>
                                    </div>
                                    <div className="w-16">
                                        <p className="text-xs text-gray-400">Δ 25→27</p>
                                        <p className={`text-sm font-semibold ${deltaClass(r.change_2527_pct)}`}>{fmtPstSafe(r.change_2527_pct)}</p>
                                    </div>
                                </div>
                            </button>

                            {/* Ekspandert: år-for-år steg */}
                            {isOpen && (
                                <div className="border-t border-gray-200 overflow-x-auto">
                                    <StepTable
                                        steps={r.steps}
                                        outlierYears={r.outlier_capped_years}
                                        phi_sum={r.phi_sum}
                                    />
                                </div>
                            )}
                        </div>
                    );
                })}
                {filtered.length === 0 && (
                    <p className="text-center py-8 text-sm text-gray-400">Ingen rader matcher søket</p>
                )}
            </div>

            {/* Forklaring */}
            <div className="flex flex-wrap gap-4 text-xs text-gray-500 pt-2">
                <span><span className="inline-block w-3 h-3 rounded bg-blue-100 mr-1" />Initialisering</span>
                <span><span className="inline-block w-3 h-3 rounded bg-gray-100 mr-1" />Treningsår</span>
                <span><span className="inline-block w-3 h-3 rounded bg-orange-100 mr-1" />⊕ Winsorisert</span>
                <span><span className="inline-block w-3 h-3 rounded bg-green-100 mr-1" />2027-prediksjon</span>
                <span className="ml-auto">Avvik = GL CPI-justert − fremskutt prognose for det året</span>
            </div>
        </Section>
    );
}

// ── Tab 11: Begrepsoversikt ───────────────────────────────────────────────────

interface GlossaryEntry {
    term: string;
    short: string;
    long: string;
    example?: string;
    category: "modell" | "data" | "begrensning" | "scenario" | "generelt";
}

const GLOSSARY: GlossaryEntry[] = [
    // ── Datakilder ──────────────────────────────────────────────────────────
    {
        term: "GL (General Ledger)",
        short: "Bokført regnskapstransaksjon i Agresso/SRS",
        long: "GL-transaksjoner er de faktiske, bokførte kostnadene fra regnskapssystemet (Agresso/SRS). De er grunnlaget for historikken modellen trenes på. Kun netto-positive beløp per eiendom+kategori+år tas med — slik at reverseringer og feilfaktureringer nulles ut.",
        example: "GL 2025 for eiendom X, kategori Drift = sum av alle bokførte driftskostnader i 2025",
        category: "data",
    },
    {
        term: "SRS-kategori",
        short: "Kostnadskategori fra Bufdirs klassifisering",
        long: "Bufdir har definert fire kosnadskategorier som alle GL-transaksjoner mappes til: Lokaler (husleie, parkering), Drift (strøm, renhold, vakthold), Vedlikehold (reparasjon, inventar) og Gjennomstrømning (omposteringer). Kategorien styrer hvilken prediksjonsstrategi som brukes.",
        category: "data",
    },
    {
        term: "Gjennomstrømning / Omposteringer",
        short: "Interne regnskapskorrigeringer — ikke operativ kostnad",
        long: "Gjennomstrømning-kategorien (srs_kategori=Gjennomstrømning eller Lokaler) dekker omposteringer: beløp som flyttes mellom eiendommer eller regioner i regnskapet. De varierer erratisk fra år til år og representerer ikke reelle driftsutgifter. Modellen bruker derfor inflasjonsfallback for denne kategorien fremfor Holt-Winters trendmodell.",
        example: "En eiendom kan ha 0 kr et år og 5 M kr neste år i gjennomstrømning — avhengig av hvilke interne omposterte husleier som ble bokført",
        category: "data",
    },
    {
        term: "CPI-justering (KPI-deflasjon)",
        short: "Prisjusterer historiske beløp til 2025-NOK",
        long: "For å gjøre historiske GL-tall sammenlignbare justeres alle beløp til 2025-NOK ved hjelp av SSB KPI-indeksen (2015=100). En krone i 2021 hadde høyere kjøpekraft enn i 2025, så 2021-beløp skaleres opp med faktoren 140/112 ≈ 1,25. Siste faktiske år (2025) endres aldri.",
        example: "GL 2021 = 1 000 000 kr → CPI-justert til 2025-NOK: 1 000 000 × (140/112) = 1 250 000 kr",
        category: "data",
    },

    // ── Modell ───────────────────────────────────────────────────────────────
    {
        term: "Holt-Winters / Holts linære metode",
        short: "Dobbel eksponentiell utjevning med dempet trend",
        long: "Holt-Winters (her: Holts linære variant uten sesongkomponent) er en tidsrekke-metode som oppdaterer to tilstandsvariabler: nivå (L) og trend (T). Nyere observasjoner vektes eksponentielt mer. Modellen brukes for Drift og Vedlikehold med ≥ 3 år historikk. Merk: noen kilder kaller full sesongmodell «Holt-Winters» — her brukes kun todimensjonal versjon uten sesong.",
        category: "modell",
    },
    {
        term: "α (alpha) — nivåglattingsfaktor",
        short: "Vekter nyere observasjoner vs. glatt historikk",
        long: "α ∈ [0, 1] styrer hvor raskt nivåestimatet L reagerer på nye observasjoner. α=1 betyr at kun siste observasjon teller. α=0 betyr at historikken aldri oppdateres. Modellen bruker α=0,5 — en balansert vekting som gir stabil reaksjon uten å overreagere på enkeltår.",
        example: "L_t = 0,5 × y_t + 0,5 × (L_{t−1} + φ×T_{t−1})",
        category: "modell",
    },
    {
        term: "β (beta) — trendglattingsfaktor",
        short: "Vekter ny trendinformasjon vs. glatt historisk trend",
        long: "β ∈ [0, 1] styrer hvor raskt trendestimatet T oppdateres. Modellen bruker β=0,2 — forsiktig trendoppdatering som unngår å overekstrapolere et enkeltårs kostnadshopp.",
        example: "T_t = 0,2 × (L_t − L_{t−1}) + 0,8 × φ×T_{t−1}",
        category: "modell",
    },
    {
        term: "φ (phi) — dempingsfaktor",
        short: "Demper trenden slik at den ikke vokser ubegrenset",
        long: "φ ∈ [0, 1] implementerer Gardner-McKenzie (1985) dempet trend. uten demping (φ=1) ville trenden summere seg lineært, noe som gir urealistisk eksponentiell vekst over lange horisonter. φ=0,85 gir φ_sum = 0,85¹ + 0,85² = 1,5725 over 2 år — trenden bidrar med 1,57 ganger stigningstallet, ikke 2,0.",
        example: "φ=0,85, h=2: φ_sum = 0,85 + 0,7225 = 1,5725",
        category: "modell",
    },
    {
        term: "φ_sum (dempet horisont-multiplier)",
        short: "Effektiv vekting av stigningstallet over h år",
        long: "φ_sum = φ¹ + φ² + … + φʰ. For h=2 og φ=0,85: φ_sum = 1,5725. Denne verdien multipliseres med T_n for å gi bidraget fra trenden i prediksjonen. Uten demping ville bidraget vært h=2 (dobbelt stigningstallet).",
        example: "Prediksjon = L_n + 1,5725 × T_n",
        category: "modell",
    },
    {
        term: "L_init / L₀ (initiell nivå)",
        short: "Startverdi for nivåestimatet",
        long: "L initialiseres til den første (eldste) CPI-justerte GL-observasjonen i treningsserien. Eksempel: hvis treningsserien starter i 2021, er L₀ = CPI-justert GL 2021.",
        category: "modell",
    },
    {
        term: "T_init / T₀ (initiell trend)",
        short: "Gjennomsnittlig stigningstall over hele treningsserien",
        long: "T₀ beregnes som gjennomsnitts-stigningen over hele serien: (siste verdi − første verdi) / (n − 1). Dette er mer stabilt enn å bruke kun første steg, og gir en meningsfull starttrend selv for serier med støy.",
        example: "GL 2021=1M, GL 2025=1,4M: T₀ = (1,4M − 1M) / 4 = 100 000 kr/år",
        category: "modell",
    },
    {
        term: "L_final / T_final",
        short: "Nivå og trend etter siste treningsiterasjon (2025)",
        long: "Etter at HW-algoritmen har iterert gjennom alle år i treningsserien, er L_final og T_final nivå- og trendestimatet for siste observerte år (2025). Disse er inngangsverdiene til prediksjonsformelen.",
        category: "modell",
    },
    {
        term: "Initialiserings­år",
        short: "Første år i treningsserien — L₀ og T₀ settes her",
        long: "Det første året i GL-historikken initialiserer modellen: nivå L₀ = y₁ (CPI-justert GL for det første tilgjengelige året), trend T₀ = (yₙ − y₁)/(n−1) (gjennomsnittlig stigning over hele serien). Det finnes ingen fremskutt prognose for initialiseringsåret. I tabellen vises dette som en blå rad merket «init».",
        example: "GL 2021 (CPI-justert)=1 500 000, GL 2025=2 100 000: T₀ = (2 100 000 − 1 500 000) / 4 = 150 000 kr/år",
        category: "modell",
    },
    {
        term: "Prognose (t+1) — fremskutt prognose",
        short: "Modellens anslag for neste år, beregnet FØR det observeres",
        long: "For hvert treningsår t (unntatt initialiseringsåret) beregnes en «ett-steg-fremskutt prognose» basert på forrige periodes nivå og trend: Prognose_t = L_{t−1} + φ × T_{t−1}. Denne prognosetallet genereres FØR årets faktiske GL sees, og viser derfor hvor godt modellen hadde tippet på forhånd. Merk: dette er h=1 prognose (ett år frem), ikke den endelige 2027-prediksjonen (h=2).",
        example: "L 2024=1 800 000, T 2024=60 000, φ=0,85 → Prognose 2025 = 1 800 000 + 0,85×60 000 = 1 851 000 kr",
        category: "modell",
    },
    {
        term: "Avvik (faktisk − prognose)",
        short: "Forskjellen mellom faktisk GL og fremskutt prognose for det året",
        long: "Avvik_t = GL_t (CPI-justert) − Prognose_t. Et positivt avvik betyr at kostnadene ble høyere enn modellen forventet; negativt betyr de ble lavere. Store, systematiske avvik over flere år tyder på at trenden er feil kalibrert. Avviket brukes ikke i selve prediksjonen — det er et rent diagnose­verktøy for å vurdere modellkvaliteten.",
        example: "GL 2025 (CPI-just.)=2 100 000, Prognose 2025=1 851 000 → Avvik = +249 000 kr (+13,4 %)",
        category: "modell",
    },
    {
        term: "Rå HW-prediksjon",
        short: "H=2 prediksjon før sikkerhetskapper — ikke det samme som Prognose (t+1)",
        long: "Rå HW = L_final + φ_sum × T_final, der φ_sum = φ¹ + φ² = 1,5725 (to år frem). Dette er det endelige modellestimatet for 2027, beregnet etter at alle treningsår er prosessert. Merk forskjellen fra Prognose (t+1): den fremskutte prognosetabellen viser h=1 anslag for hvert enkelt treningsår, mens Rå HW er h=2 anslaget for 2027. Sikkerhetskappene justerer Rå HW etterpå.",
        example: "L_final=1 900 000, T_final=55 000, φ_sum=1,5725 → Rå HW = 1 900 000 + 1,5725×55 000 = 1 986 488 kr",
        category: "modell",
    },
    {
        term: "Winsorisering (outlier-kapping)",
        short: "Begrenser ekstreme historiske verdier før fitting",
        long: "Outlier-år med unormalt høye eller lave kostnader (utenfor Tukey IQR-gjerdene: Q3 + 1,5×IQR og Q1 − 1,5×IQR) cappes før HW-fitting. Siste faktiske år (2025) winsoriseres aldri — det er ankerverdien for vekstkapper. Krever ≥ 4 datapunkter for å aktiveres. I steg-tabellen markeres winsoriserte år med «⊕winsor» og oransje bakgrunn.",
        example: "Serie [122M, 194M, 160M, 142M, 150M]: Q1=142M, Q3=160M, IQR=18M → øvre grense=187M → 194M cappes til 187M",
        category: "modell",
    },

    // ── Begrensninger ────────────────────────────────────────────────────────
    {
        term: "Kald start (cold start)",
        short: "Rask opptrapping — inflasjonsfallback brukes",
        long: "En eiendom er «kald start» hvis siste faktiske år (2025) er > 1,5 × historisk snitt. Dette skjer for eiendommer som nettopp ble aktive og har lave historiske verdier. Holt-Winters vil da ekstrapolere en urealistisk eksplosiv trend. Fallback: siste faktiske × (1 + 3,5 % × horizon).",
        example: "[0, 0, 100k, 3M, 5,5M]: snitt=1,72M, siste=5,5M → ratio=3,2 > 1,5 → kald start",
        category: "begrensning",
    },
    {
        term: "Negativ trend-gulv",
        short: "Prediksjon aldri lavere enn inflasjonsvekst",
        long: "Hvis HW-prediksjonen er lavere enn siste faktiske × (1 + inflasjon × horizon), settes prediksjonen til dette gulvet. En strukturell kostnadsnedgang ville kreve eksplisitt begrunnelse — modellen antar at kostnader minst vokser med inflasjon.",
        example: "GL 2025=2M, inflasjon=3,5%, h=2 → gulv=2M × 1,071=2,14M. HW gir 1,9M → justeres til 2,14M",
        category: "begrensning",
    },
    {
        term: "Output-ratio fallback",
        short: "HW-output > 1,5× siste faktiske → inflasjonsfallback",
        long: "Selv om input-serien passerte kald-start-sjekken, kan HW produsere urealistisk høye tall (f.eks. hvis 2024 var et ekstremår som drev opp snittet). Hvis rå HW > 1,5 × GL 2025, brukes inflasjonsfallback i stedet.",
        category: "begrensning",
    },
    {
        term: "Vekstkap (annual_growth_capped)",
        short: "Maks 8 % vekst per år (16,6 % over 2 år)",
        long: "For å forhindre at krise-år-trender ekstrapoleres, begrenses prediksjonen til GL 2025 × (1,08)². Dette er det vanligste tiltaket som aktiveres for eiendommer med høy kostnadsvekst i perioden 2021–2025.",
        example: "GL 2025=3M, cap=3M × 1,1664=3,5M. HW gir 4,2M → justeres til 3,5M",
        category: "begrensning",
    },
    {
        term: "Hard cap (max vekstfaktor)",
        short: "Absolutt tak: aldri mer enn 5× siste faktiske",
        long: "Siste sikkerhetsnett: prediksjonen kan aldri overstige GL 2025 × 5. Dette fanger opp tilfeller der alle andre begrensninger er for leke.",
        category: "begrensning",
    },
    {
        term: "Inflasjonsfallback",
        short: "Enkelt anslag: siste faktiske × (1 + 3,5 %×h)",
        long: "Brukes i tre situasjoner: (1) kategorien er Gjennomstrømning/Lokaler (passthrough), (2) eiendom har < 3 år historikk, (3) kald start eller output-ratio fallback aktiveres. Beløpet lagres i 2025-NOK og inflasjonsjusteres uniformt av Excel-arket.",
        category: "begrensning",
    },

    // ── Scenarioer ───────────────────────────────────────────────────────────
    {
        term: "XGBoost-gulv",
        short: "Nedre grense basert på ML-prediksjon på tvers av porteføljen",
        long: "XGBoost er en gradientboosting-modell trent på alle eiendommer samlet. Den gir en porteføljenivå-prediksjon. For eiendommer der HW-prediksjonen er under en viss andel av XGBoost-prediksjonen, heves prediksjonen til dette gulvet. Scenariovariabelen styrer gulv-andelen.",
        category: "scenario",
    },
    {
        term: "Scenario xgb70 (standard)",
        short: "XGBoost-gulv = 70 % av ML-prediksjon",
        long: "Anbefalt scenario for budsjettplanlegging. XGBoost-gulvet aktiveres der Holt-Winters gir et anslag som er lavere enn 70 % av hva XGBoost forventer basert på tverreiendomsmønster. Konservativt: gulvet gir et minimumsnivå å planlegge rundt.",
        category: "scenario",
    },
    {
        term: "Scenario xgb50 (optimistisk)",
        short: "XGBoost-gulv = 50 % av ML-prediksjon",
        long: "Lavere gulv enn xgb70 — gulvet aktiveres sjeldnere og HW-prediksjonen faller mer gjennom. Gir lavere totaltall enn xgb70. Brukes som nedre estimat i sensitivitetsanalyser.",
        category: "scenario",
    },

    // ── Generelt ─────────────────────────────────────────────────────────────
    {
        term: "Endring % (25→27)",
        short: "Prosentvis endring fra GL 2025 til prediksjon 2027",
        long: "Alle prosentendringer i rapporten sammenlignes direkte mellom faktisk GL 2025 og prediksjon 2027 (to år). «—» vises der GL 2025 < 200 000 kr (for liten base gir villedende tall) eller der endringen er > 300 % i absoluttverdi (tyder på støy/omposteringer, ikke reell kostnadsvekst).",
        example: "GL 2025=2M, Pred 2027=2,2M → endring = (2,2M − 2M)/2M × 100 = +10,0 %",
        category: "generelt",
    },
    {
        term: "Minimumsgrense for %-visning",
        short: "GL 2025 < 200 000 kr → «—»",
        long: "Eiendommer med svært lite aktivitet i 2025 vil gi ekstreme prosentendringer selv for moderate absolutte endringer. For å unngå villedende tall vises «—» der GL 2025-basen er under 200 000 kr.",
        example: "GL 2025=3 131 kr, Pred 2027=3 M kr → +95 870 % — vises som «—»",
        category: "generelt",
    },
    {
        term: "Pred HW vs Pred 2027 (final)",
        short: "Pred HW er etter sikkerhetskapper; Pred 2027 er etter XGBoost-gulv",
        long: "«Pred HW» er Holt-Winters sitt h=2 anslag etter at alle sikkerhetskapper er applisert (negativ-trend-gulv, output-ratio, vekstkap, hardkap), men før XGBoost-gulvet. «Pred 2027 (final)» er verdien lagret i budget-tabellen etter at XGBoost-gulvet eventuelt har løftet estimatet. I steg-tabellen vises Pred HW som prognose-feltet på 2027-raden (grønn bakgrunn), formulert som «L + 1,5725×T = X kr».",
        category: "generelt",
    },
    {
        term: "Treningsperiode",
        short: "GL-historikk 2020–2025 brukt til å trene modellen",
        long: "Modellen bruker GL-data fra 2020 til og med 2025 (siste tilgjengelige). Eiendommer uten GL-aktivitet i 2025 regnes som inaktive og predikeres ikke. Eiendommer med < 3 år historikk i treningsperioden faller tilbake til inflasjonsfallback.",
        category: "data",
    },
    {
        term: "Backtesting",
        short: "Validering av modellens historiske nøyaktighet",
        long: "For å vurdere modellens kvalitet kjøres den på historiske data der svaret er kjent: modellen trenes på f.eks. 2021–2023 og predikerer 2024–2025. Avviket mellom modellens prediksjoner og de faktiske GL-tallene måles (MAPE = Mean Absolute Percentage Error). Lav MAPE = god modell.",
        category: "generelt",
    },
];

const CAT_LABELS: Record<GlossaryEntry["category"], string> = {
    data:       "Datakilder og input",
    modell:     "Modell og algoritme",
    begrensning:"Sikkerhetskapper og fallbacks",
    scenario:   "Scenarioer og XGBoost",
    generelt:   "Generelt og tolkning",
};

const CAT_COLORS: Record<GlossaryEntry["category"], string> = {
    data:        "bg-blue-50 border-blue-200 text-blue-800",
    modell:      "bg-teal-50 border-teal-200 text-teal-800",
    begrensning: "bg-orange-50 border-orange-200 text-orange-800",
    scenario:    "bg-purple-50 border-purple-200 text-purple-800",
    generelt:    "bg-gray-50 border-gray-200 text-gray-800",
};

const CAT_BADGE: Record<GlossaryEntry["category"], string> = {
    data:        "bg-blue-100 text-blue-700",
    modell:      "bg-teal-100 text-teal-700",
    begrensning: "bg-orange-100 text-orange-700",
    scenario:    "bg-purple-100 text-purple-700",
    generelt:    "bg-gray-100 text-gray-700",
};

function TabBegrepsoversikt() {
    const [search, setSearch] = useState("");
    const [catFilter, setCatFilter] = useState<string>("alle");

    const filtered = useMemo(() => {
        return GLOSSARY.filter((e) => {
            if (catFilter !== "alle" && e.category !== catFilter) return false;
            if (search) {
                const q = search.toLowerCase();
                return (
                    e.term.toLowerCase().includes(q) ||
                    e.short.toLowerCase().includes(q) ||
                    e.long.toLowerCase().includes(q)
                );
            }
            return true;
        });
    }, [search, catFilter]);

    // Group by category in display order
    const ORDER: GlossaryEntry["category"][] = ["data", "modell", "begrensning", "scenario", "generelt"];
    const grouped = ORDER.map((cat) => ({
        cat,
        entries: filtered.filter((e) => e.category === cat),
    })).filter((g) => g.entries.length > 0);

    return (
        <Section title="Begrepsoversikt — prediksjon 2027">
            {/* Intro */}
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg text-sm text-teal-900">
                Forklaring av alle faglige begreper, parametre og modellvalg som brukes i rapporten.
                Beregnet for økonomi, regnskap og ledelse som ønsker å forstå — og ettergå — prediksjonsmetodikken.
            </div>

            {/* Filter-bar */}
            <div className="flex flex-wrap gap-3 items-center">
                <input
                    type="text"
                    placeholder="Søk begrep…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="border border-gray-300 rounded px-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-teal-400"
                />
                <div className="flex gap-2 flex-wrap">
                    {(["alle", ...ORDER] as const).map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setCatFilter(cat)}
                            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                                catFilter === cat
                                    ? "bg-teal-600 text-white border-teal-600"
                                    : "bg-white text-gray-600 border-gray-300 hover:border-teal-400"
                            }`}
                        >
                            {cat === "alle" ? "Alle" : CAT_LABELS[cat]}
                        </button>
                    ))}
                </div>
                <span className="ml-auto text-xs text-gray-400">{filtered.length} begreper</span>
            </div>

            {/* Groups */}
            {grouped.map(({ cat, entries }) => (
                <div key={cat} className="space-y-3">
                    <h3 className={`text-sm font-semibold px-3 py-1.5 rounded-md border inline-block ${CAT_COLORS[cat]}`}>
                        {CAT_LABELS[cat]}
                    </h3>
                    <div className="grid gap-3 sm:grid-cols-1">
                        {entries.map((entry) => (
                            <div key={entry.term} className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                                <div className="flex items-start gap-3 px-4 py-3 bg-gray-50 border-b border-gray-200">
                                    <span className={`shrink-0 mt-0.5 px-2 py-0.5 rounded text-xs font-semibold ${CAT_BADGE[cat]}`}>
                                        {cat === "modell" ? "Modell" : cat === "data" ? "Data" : cat === "begrensning" ? "Begrensning" : cat === "scenario" ? "Scenario" : "Generelt"}
                                    </span>
                                    <div>
                                        <p className="font-semibold text-gray-900 text-sm">{entry.term}</p>
                                        <p className="text-xs text-gray-500 mt-0.5">{entry.short}</p>
                                    </div>
                                </div>
                                <div className="px-4 py-3 space-y-2">
                                    <p className="text-sm text-gray-700 leading-relaxed">{entry.long}</p>
                                    {entry.example && (
                                        <div className="flex gap-2 items-start mt-1">
                                            <span className="shrink-0 text-xs font-medium text-gray-400 mt-0.5">Eks:</span>
                                            <p className="text-xs text-gray-600 italic">{entry.example}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}

            {filtered.length === 0 && (
                <p className="text-sm text-gray-400 py-6 text-center">Ingen begreper matcher søket</p>
            )}
        </Section>
    );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function PredRapportPage() {
    const [activeTab, setActiveTab] = useState<Tab>("Sammendrag");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [antagelser, setAntagelser] = useState<Antagelser | null>(null);
    const [sammenligning, setSammenligning] = useState<Sammenligning | null>(null);
    const [pred2027, setPred2027] = useState<Prediksjon2027 | null>(null);

    // Beregningsdetaljer — lastes lazy (store data, bare ved behov)
    const [beregning, setBeregning] = useState<Beregning | null>(null);
    const [beregningLoading, setBeregningLoading] = useState(false);

    useEffect(() => {
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const [ant, samm, pred] = await Promise.all([
                    apiFetch<Antagelser>("/financials/prediksjon/antagelser"),
                    apiFetch<Sammenligning>("/financials/prediksjon-sammenligning?scenario=xgb70"),
                    apiFetch<Prediksjon2027>("/financials/prediksjon-2027"),
                ]);
                setAntagelser(ant);
                setSammenligning(samm);
                setPred2027(pred);
            } catch (e: unknown) {
                setError(e instanceof Error ? e.message : String(e));
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    // Lazy-last beregningsdetaljer når fanen åpnes
    useEffect(() => {
        if (activeTab !== "Beregningsdetaljer" || beregning !== null || beregningLoading) return;
        async function loadBeregning() {
            setBeregningLoading(true);
            try {
                const data = await apiFetch<Beregning>("/financials/prediksjon-beregning?scenario=xgb70");
                setBeregning(data);
            } catch (e) {
                console.error("Feil ved lasting av beregningsdetaljer:", e);
            } finally {
                setBeregningLoading(false);
            }
        }
        loadBeregning();
    }, [activeTab, beregning, beregningLoading]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-3">
                <div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-gray-500">Laster prediksjonrapport…</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 max-w-2xl mx-auto">
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                    <strong>Feil ved lasting:</strong> {error}
                </div>
            </div>
        );
    }

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "";

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-2">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
                <div>
                    <Link
                        href="/financials/prediksjon"
                        className="inline-flex items-center gap-1 text-sm text-teal-600 hover:text-teal-700 mb-2"
                    >
                        <ArrowLeft size={14} /> Tilbake til prediksjon
                    </Link>
                    <h1 className="text-2xl font-bold text-gray-900">
                        Prediksjon 2027 — fullstendig rapport
                    </h1>
                    <p className="text-sm text-gray-500 mt-1">
                        Bufetat Eiendomsforvaltning · Holt-Winters (α=0,5 β=0,2 φ=0,85) + Inflasjonsfallback for Gjennomstrømning
                    </p>
                </div>
                <a
                    href={`${apiBase}/api/v1/financials/prediksjon/export.xlsx?scenario=xgb70`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700 transition-colors"
                >
                    Last ned Excel
                </a>
            </div>

            {/* Tab bar */}
            <TabBar active={activeTab} onChange={setActiveTab} />

            {/* Tab content */}
            {activeTab === "Antagelser" && antagelser && <TabAntagelser data={antagelser} />}
            {activeTab === "Sammendrag" && sammenligning && <TabSammendrag data={sammenligning} />}
            {activeTab === "Per region" && sammenligning && <TabPerRegion data={sammenligning} />}
            {activeTab === "Per kategori" && sammenligning && <TabPerKategori data={sammenligning} />}
            {activeTab === "Lønn" && pred2027 && <TabLonn data={pred2027} />}
            {activeTab === "Alle eiendommer" && sammenligning && (
                <TabAlleEiendommer properties={sammenligning.properties} />
            )}
            {activeTab === "Outliers" && sammenligning && (
                <TabOutliers properties={sammenligning.properties} />
            )}
            {activeTab === "Backtesting" && <TabBacktesting apiBase={apiBase} />}
            {activeTab === "Beregningsdetaljer" && (
                <TabBeregning data={beregning} loading={beregningLoading} />
            )}
            {activeTab === "Metodikk" && <TabMetodikk />}
            {activeTab === "Begrepsoversikt" && <TabBegrepsoversikt />}
        </div>
    );
}
