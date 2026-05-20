"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Header from "@/app/components/ui/Header";
import {
    getBarnevernPlaces,
    simulateBarnevernCost,
    type BarnevernPlacesResponse,
    type SimulationResult,
} from "@/lib/api/barnevernApi";
import { Baby, Building2, TrendingUp, SlidersHorizontal, Loader2, Info, HelpCircle, Landmark } from "lucide-react";
import {
    getStatsbudsjettetBfdYear,
    getGlNasjonalTotal,
    type StatsbudsjettetBfdYear,
    type GlNasjonalTotal,
} from "@/lib/api/barnevernDocsApi";

function Tooltip({ text }: { text: string }) {
    return (
        <span className="group relative inline-flex items-center ml-1 cursor-help">
            <HelpCircle size={13} className="text-muted/60 hover:text-muted transition-colors" />
            <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 rounded-lg bg-popover border border-border text-xs text-muted p-2.5 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-50 leading-relaxed">
                {text}
            </span>
        </span>
    );
}

const formatNOK = (n: number) =>
    new Intl.NumberFormat("nb-NO", {
        style: "currency",
        currency: "NOK",
        maximumFractionDigits: 0,
    }).format(n);

const REGION_ORDER = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir", "Ukjent"];

export default function BarnevernPage() {
    const [placesData, setPlacesData] = useState<BarnevernPlacesResponse | null>(null);
    const [simulation, setSimulation] = useState<SimulationResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [simLoading, setSimLoading] = useState(false);
    const [year, setYear] = useState(2026);
    const [usagePct, setUsagePct] = useState(0.85);
    const [bfdYear, setBfdYear] = useState<number>(2025);
    const [bfdData, setBfdData] = useState<StatsbudsjettetBfdYear | null>(null);
    const [bfdLoading, setBfdLoading] = useState(false);
    const [bfdError, setBfdError] = useState<string | null>(null);
    const [glTotal, setGlTotal] = useState<GlNasjonalTotal | null>(null);
    const [bfdSimMode, setBfdSimMode] = useState(false);
    const [foreslattValues, setForeslattValues] = useState<Record<string, number>>({});

    const loadPlaces = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getBarnevernPlaces();
            setPlacesData(data);
        } catch {
            setPlacesData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const runSim = useCallback(async () => {
        setSimLoading(true);
        try {
            const result = await simulateBarnevernCost({
                year,
                usage_pct: usagePct,
                include_ssb: true,
            });
            setSimulation(result);
        } catch {
            setSimulation(null);
        } finally {
            setSimLoading(false);
        }
    }, [year, usagePct]);

    const loadBfd = useCallback(async () => {
        setBfdLoading(true);
        setBfdError(null);
        try {
            const [data, gl] = await Promise.all([
                getStatsbudsjettetBfdYear(bfdYear),
                getGlNasjonalTotal(bfdYear).catch(() => null),
            ]);
            setBfdData(data);
            setGlTotal(gl);
        } catch {
            setBfdError("Kunne ikke laste bevilgningsdata.");
            setBfdData(null);
        } finally {
            setBfdLoading(false);
        }
    }, [bfdYear]);

    useEffect(() => {
        loadPlaces();
    }, [loadPlaces]);

    useEffect(() => {
        loadBfd();
    }, [loadBfd]);

    // Initialiser foreslåtte verdier når simulatormodus aktiveres
    useEffect(() => {
        if (bfdSimMode && bfdData) {
            const init: Record<string, number> = {};
            bfdData.kapitler.forEach(kap => {
                kap.poster.forEach(post => {
                    const key = `${kap.kap}-${post.post}`;
                    if (!(key in foreslattValues)) {
                        init[key] = post.bevilget;
                    }
                });
            });
            if (Object.keys(init).length > 0) {
                setForeslattValues(prev => ({ ...init, ...prev }));
            }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [bfdSimMode, bfdData]);

    useEffect(() => {
        if (!loading && placesData) runSim();
    }, [loading, placesData, runSim]);

    const regions = simulation?.by_region
        ? [...simulation.by_region].sort(
              (a, b) =>
                  REGION_ORDER.indexOf(a.region) - REGION_ORDER.indexOf(b.region)
          )
        : [];

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header />
            <main className="max-w-5xl mx-auto px-6 pt-24 pb-20">
                <div className="flex items-center gap-4 mb-8">
                    <div className="w-14 h-14 bg-primary/20 rounded-xl flex items-center justify-center text-primary border border-primary/20">
                        <Baby size={28} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">
                            Kostnadssimulering for brukte og ubrukte plasser
                        </h1>
                        <p className="text-muted text-sm mt-1">
                            Kombinerer BEFS institusjonsdata med statlig egenandel og valgfri bruksgrad.
                            Beregner kostnad for brukte og ubrukte plasser per region.
                            SSB KOSTRA brukes som nasjonal referanse.
                        </p>
                    </div>
                </div>

                <aside className="rounded-xl border border-border bg-muted/20 p-4 text-sm mb-8">
                    <div className="font-medium text-foreground mb-2">
                        St.prp., årsrapport og SSB som analysegrunnlag
                    </div>
                    <p className="text-muted-foreground leading-relaxed mb-3">
                        Bufdir/Storting og åpne statistikker kan kobles til denne simuleringen når du
                        skal forklare avvik, mål og budsjettkontekst. Samlet oversikt og nedlastinger
                        finner du under Barnevern-dokumenter; SSB kan du utforske direkte.
                    </p>
                    <div className="flex flex-wrap gap-x-4 gap-y-2">
                        <Link
                            href="/admin/barnevern-docs"
                            className="text-primary underline font-medium"
                        >
                            Barnevern-dokumenter (St.prp., årsrapport, SSB-kortliste)
                        </Link>
                        <Link
                            href="/admin/barnevern-analysis"
                            className="text-primary underline font-medium"
                        >
                            Barnevern-analyse (syntese)
                        </Link>
                        <Link
                            href="/admin/bufdir-institutions"
                            className="text-primary underline font-medium"
                        >
                            Bufdir institusjoner (nasjonal liste)
                        </Link>
                        <Link href="/ssb" className="text-primary underline font-medium">
                            SSB Statistikk
                        </Link>
                    </div>
                </aside>

                {loading ? (
                    <div className="flex items-center gap-2 text-muted py-12">
                        <Loader2 size={20} className="animate-spin" />
                        Laster plasser og institusjoner…
                    </div>
                ) : !placesData ? (
                    <div className="rounded-xl border border-border bg-muted/30 p-8 text-muted">
                        Kunne ikke laste barnevernsdata.
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Plasser-oversikt */}
                        <section className="rounded-xl border border-border bg-card p-6">
                            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                <Building2 size={18} />
                                Plasser og institusjoner (BEFS)
                            </h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                <div className="rounded-lg bg-muted/50 p-4">
                                    <div className="text-xs text-muted uppercase tracking-wider">
                                        Godkjente plasser
                                    </div>
                                    <div className="text-xl font-bold text-foreground mt-1">
                                        {placesData.total_approved_places.toLocaleString("nb-NO")}
                                    </div>
                                </div>
                                <div className="rounded-lg bg-muted/50 p-4">
                                    <div className="text-xs text-muted uppercase tracking-wider">
                                        Institusjoner
                                    </div>
                                    <div className="text-xl font-bold text-foreground mt-1">
                                        {placesData.total_count}
                                    </div>
                                </div>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-border">
                                            <th className="text-left py-2 font-medium">Region</th>
                                            <th className="text-right py-2 font-medium">Plasser</th>
                                            <th className="text-right py-2 font-medium">Kostnad 2025</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {REGION_ORDER.filter(
                                            (r) => placesData.by_region[r]
                                        ).map((reg) => {
                                            const agg = placesData.by_region[reg];
                                            return (
                                                <tr
                                                    key={reg}
                                                    className="border-b border-border/50"
                                                >
                                                    <td className="py-2">
                                                        <Link
                                                            href={`/institusjoner?region=${encodeURIComponent(reg)}`}
                                                            className="hover:text-primary transition-colors underline-offset-2 hover:underline"
                                                        >
                                                            {reg}
                                                        </Link>
                                                    </td>
                                                    <td className="text-right py-2">
                                                        {agg.approved_places.toLocaleString("nb-NO")}
                                                    </td>
                                                    <td className="text-right py-2">
                                                        {formatNOK(agg.annual_cost)}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </section>

                        {/* Bruksgrad-slider og simuleringsresultat */}
                        <section className="rounded-xl border border-border bg-card p-6">
                            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                <SlidersHorizontal size={18} />
                                Simulering
                            </h2>
                            <div className="flex flex-wrap gap-6 mb-6">
                                <div>
                                    <label className="block text-xs text-muted mb-1">År</label>
                                    <select
                                        value={year}
                                        onChange={(e) =>
                                            setYear(parseInt(e.target.value, 10))
                                        }
                                        className="rounded-lg border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        {[2024, 2025, 2026, 2027, 2028, 2029, 2030].map(
                                            (y) => (
                                                <option key={y} value={y}>
                                                    {y}
                                                </option>
                                            )
                                        )}
                                    </select>
                                </div>
                                <div className="flex-1 min-w-[200px]">
                                    <label className="block text-xs text-muted mb-1">
                                        Bruksgrad: {(usagePct * 100).toFixed(0)} %
                                    </label>
                                    <input
                                        type="range"
                                        min={0}
                                        max={100}
                                        value={usagePct * 100}
                                        onChange={(e) =>
                                            setUsagePct(
                                                parseInt(e.target.value, 10) / 100
                                            )
                                        }
                                        className="w-full h-2 rounded-lg appearance-none bg-muted accent-primary"
                                    />
                                </div>
                            </div>

                            {simLoading ? (
                                <div className="flex items-center gap-2 text-muted py-8">
                                    <Loader2 size={18} className="animate-spin" />
                                    Beregner…
                                </div>
                            ) : simulation ? (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <div className="rounded-lg bg-primary/10 p-4 border border-primary/20">
                                            <div className="text-xs text-muted uppercase">
                                                Brukte plasser
                                            </div>
                                            <div className="text-lg font-bold text-primary mt-1">
                                                {simulation.total_brukte.toLocaleString("nb-NO")}
                                            </div>
                                        </div>
                                        <div className="rounded-lg bg-muted/50 p-4">
                                            <div className="text-xs text-muted uppercase">
                                                Ubrukte plasser
                                            </div>
                                            <div className="text-lg font-bold mt-1">
                                                {simulation.total_ubrukte.toLocaleString("nb-NO")}
                                            </div>
                                        </div>
                                        <div className="rounded-lg bg-muted/50 p-4">
                                            <div className="text-xs text-muted uppercase">
                                                Kostnad brukte
                                            </div>
                                            <div className="text-lg font-bold mt-1">
                                                {formatNOK(simulation.total_kost_brukte)}
                                            </div>
                                        </div>
                                        <div className="rounded-lg bg-muted/50 p-4">
                                            <div className="text-xs text-muted uppercase">
                                                Kostnad ubrukte
                                            </div>
                                            <div className="text-lg font-bold mt-1">
                                                {formatNOK(simulation.total_kost_ubrukte)}
                                            </div>
                                        </div>
                                        <div className="rounded-lg bg-primary/10 p-4 border border-primary/20">
                                            <div className="text-xs text-muted uppercase">
                                                Total kostnad
                                            </div>
                                            <div className="text-lg font-bold text-primary mt-1">
                                                {formatNOK(simulation.total_kostnad)}
                                            </div>
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted">
                                        Egenandel {year}:{" "}
                                        {formatNOK(simulation.egenandel_maaned)}/mnd (
                                        {formatNOK(simulation.egenandel_aar)}/år)
                                    </p>
                                    <div>
                                        <h3 className="font-medium text-foreground mb-2">
                                            Per region
                                        </h3>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="border-b border-border">
                                                        <th className="text-left py-2 font-medium">Region</th>
                                                        <th className="text-right py-2 font-medium">Brukte pl.</th>
                                                        <th className="text-right py-2 font-medium">Ubrukte pl.</th>
                                                        <th className="text-right py-2 font-medium text-primary">
                                                            <span className="inline-flex items-center justify-end gap-0.5">
                                                                Kost brukte
                                                                <Tooltip text="Inntektspotensial: brukte plasser × statlig egenandel × 12. Viser hva staten mottar i kommunal betaling." />
                                                            </span>
                                                        </th>
                                                        <th className="text-right py-2 font-medium text-destructive">
                                                            <span className="inline-flex items-center justify-end gap-0.5">
                                                                Kost ubrukte
                                                                <Tooltip text="Kostnadsbyrde: tomme plasser × egenandel × 12. Kostnader Bufetat bærer uten inntektsdekning. Ikke direkte sammenlignbart med kost brukte." />
                                                            </span>
                                                        </th>
                                                        <th className="text-right py-2 font-medium">Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {regions.map((sim) => (
                                                        <tr
                                                            key={sim.region}
                                                            className="border-b border-border/50"
                                                        >
                                                            <td className="py-2">
                                                                <Link
                                                                    href={`/institusjoner?region=${encodeURIComponent(sim.region)}`}
                                                                    className="hover:text-primary transition-colors underline-offset-2 hover:underline"
                                                                >
                                                                    {sim.region}
                                                                </Link>
                                                            </td>
                                                            <td className="text-right py-2">{sim.brukte_plasser}</td>
                                                            <td className="text-right py-2">{sim.ubrukte_plasser}</td>
                                                            <td className="text-right py-2 text-primary font-medium">
                                                                {formatNOK(sim.kost_brukte)}
                                                            </td>
                                                            <td className="text-right py-2 text-destructive font-medium">
                                                                {formatNOK(sim.kost_ubrukte)}
                                                            </td>
                                                            <td className="text-right py-2 text-muted">
                                                                {formatNOK(sim.total_kostnad)}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                    {/* Totalrad ubrukte kostnader */}
                                    <div className="mt-3 rounded-lg border border-destructive/20 bg-destructive/5 p-4 flex flex-wrap gap-6 text-sm">
                                        <div>
                                            <span className="text-muted text-xs uppercase tracking-wider block mb-0.5">Totalt ubrukte plasser</span>
                                            <span className="font-bold text-foreground">{simulation.total_ubrukte.toLocaleString("nb-NO")} pl.</span>
                                        </div>
                                        <div>
                                            <span className="text-muted text-xs uppercase tracking-wider flex items-center gap-0.5 mb-0.5">
                                                Kostnad ubrukte (år)
                                                <Tooltip text="Estimert kostnadsbyrde for tomme plasser. Beregnes som ubrukte plasser × egenandel × 12. OBS: ikke direkte sammenlignbart med inntektspotensialet for brukte plasser." />
                                            </span>
                                            <span className="font-bold text-destructive">{formatNOK(simulation.total_kost_ubrukte)}</span>
                                        </div>
                                        <div>
                                            <span className="text-muted text-xs uppercase tracking-wider block mb-0.5">Andel av total</span>
                                            <span className="font-bold text-foreground">
                                                {simulation.total_kostnad > 0
                                                    ? ((simulation.total_kost_ubrukte / simulation.total_kostnad) * 100).toFixed(1)
                                                    : 0} %
                                            </span>
                                        </div>
                                    </div>

                                    {simulation.ssb_data && (
                                        <div className="mt-4 rounded-lg bg-muted/30 p-4 text-xs text-muted">
                                            <span className="font-medium text-foreground">
                                                SSB referanse
                                            </span>{" "}
                                            – KOSTRA barnevern (tabell 12279) for Landet er
                                            tilgjengelig som nasjonal sammenligning.
                                        </div>
                                    )}

                                    {/* Metodikk-forklaring */}
                                    <div className="mt-6 rounded-xl border border-border bg-muted/20 p-5">
                                        <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2 text-sm">
                                            <Info size={16} className="text-primary" />
                                            Slik fungerer simuleringen
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-muted leading-relaxed">
                                            <div className="space-y-3">
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        1. Godkjente plasser (BEFS)
                                                    </span>
                                                    Antall godkjente plasser hentes fra BEFS for alle barnevernsinstitusjoner og avdelinger.
                                                </div>
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        2. Bruksgrad (slider)
                                                    </span>
                                                    Du velger andelen plasser som er i bruk (0–100 %).
                                                    <span className="font-mono bg-muted/60 px-1 rounded text-foreground ml-1">
                                                        Brukte = godkjente × bruksgrad
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        3. Egenandel per plass (statlig)
                                                    </span>
                                                    Staten fastsetter en månedlig egenandel kommunene betaler per beboer.
                                                    Satsen prisjusteres årlig:
                                                    <ul className="mt-1 ml-2 space-y-0.5 font-mono text-foreground/70">
                                                        <li>2025 – 190 190 kr/mnd</li>
                                                        <li>2026 – 197 225 kr/mnd</li>
                                                        <li>2027 – 204 650 kr/mnd</li>
                                                    </ul>
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        4. Kostnad brukte plasser
                                                    </span>
                                                    <span className="font-mono bg-muted/60 px-1 rounded text-foreground">
                                                        brukte × egenandel × 12
                                                    </span>
                                                    {" "}– det staten mottar i kommunal betaling per år.
                                                </div>
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        5. Kostnad ubrukte plasser
                                                    </span>
                                                    Faktiske driftskostnader fra regnskapet (GL 2025) fordeles proporsjonalt på tomme plasser:
                                                    <span className="font-mono bg-muted/60 px-1 rounded text-foreground ml-1">
                                                        GL-kostnad × (ubrukte / godkjente)
                                                    </span>
                                                    . Dette er kostnader Bufetat bærer selv uten inntektsdekning.
                                                </div>
                                                <div>
                                                    <span className="font-medium text-foreground block mb-0.5">
                                                        6. SSB KOSTRA (nasjonal referanse)
                                                    </span>
                                                    SSB tabell 12279 hentes for "Landet" som en nasjonal sammenligningsverdi for barnevernstjenester.
                                                </div>
                                            </div>
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-border/50 text-xs text-muted">
                                            <span className="font-medium text-foreground">Merk:</span>{" "}
                                            Kostnader for brukte og ubrukte plasser er ikke direkte sammenlignbare –
                                            brukte plasser viser inntektspotensialet (egenandel), ubrukte plasser viser
                                            faktisk kostnadsbyrde for Bufetat.
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-muted py-8">
                                    Ingen simuleringsresultat.
                                </div>
                            )}
                        </section>

                        {/* BFD Bevilgninger – Statsbudsjettet */}
                        <section className="rounded-xl border border-border bg-card p-6">
                            <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
                                <h2 className="font-semibold text-foreground flex items-center gap-2">
                                    <Landmark size={18} />
                                    BFD Bevilgninger – Statsbudsjettet
                                    <Tooltip text="Bevilgninger fra Barne- og familiedepartementet (BFD) i statsbudsjettet (Prop. 1 S). Viser kapitler relevante for Bufetat: Kap. 855 Statlig barnevern, Kap. 841 Familievern og Kap. 854 Tiltak i barnevernet." />
                                </h2>
                                <button
                                    onClick={() => setBfdSimMode(v => !v)}
                                    className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border transition-colors ${bfdSimMode ? "bg-primary text-primary-foreground border-primary" : "border-input hover:bg-muted/30"}`}
                                >
                                    <SlidersHorizontal size={13} />
                                    {bfdSimMode ? "Avslutt simulering" : "Budsjett-simulering"}
                                </button>
                            </div>

                            <div className="mb-5">
                                <label className="block text-xs text-muted mb-1">Budsjettår</label>
                                <select
                                    value={bfdYear}
                                    onChange={(e) => setBfdYear(parseInt(e.target.value, 10))}
                                    className="rounded-lg border border-input bg-background px-3 py-2 text-sm"
                                >
                                    {[2022, 2023, 2024, 2025, 2026].map((y) => (
                                        <option key={y} value={y}>{y}</option>
                                    ))}
                                </select>
                            </div>

                            {bfdLoading ? (
                                <div className="flex items-center gap-2 text-muted py-8">
                                    <Loader2 size={18} className="animate-spin" />
                                    Laster bevilgningsdata…
                                </div>
                            ) : bfdError ? (
                                <div className="rounded-lg bg-muted/30 p-4 text-muted text-sm">{bfdError}</div>
                            ) : bfdData ? (
                                <div className="space-y-6">
                                    {bfdData.kapitler.map((kap) => {
                                        const totalBevilget = kap.poster.reduce((s, p) => s + p.bevilget, 0);
                                        return (
                                            <div key={kap.kap} className="rounded-lg border border-border overflow-hidden">
                                                <div className="bg-muted/30 px-4 py-2.5 flex items-center justify-between">
                                                    <span className="font-semibold text-sm text-foreground">
                                                        Kap. {kap.kap} – {kap.navn}
                                                    </span>
                                                    <span className="text-xs text-muted font-mono">
                                                        Totalt: {formatNOK(totalBevilget)}
                                                    </span>
                                                </div>
                                                <div className="overflow-x-auto">
                                                    <table className="w-full text-sm">
                                                        <thead>
                                                            <tr className="border-b border-border/50">
                                                                <th className="text-left px-4 py-2 font-medium text-muted text-xs uppercase tracking-wider w-16">Post</th>
                                                                <th className="text-left px-4 py-2 font-medium text-muted text-xs uppercase tracking-wider">Beskrivelse</th>
                                                                <th className="text-right px-4 py-2 font-medium text-muted text-xs uppercase tracking-wider">Bevilget (BFD)</th>
                                                                <th className="text-right px-4 py-2 font-medium text-muted text-xs uppercase tracking-wider">
                                                                    <span className="inline-flex items-center justify-end gap-0.5">
                                                                        Faktisk (BEFS)
                                                                        <Tooltip text="Kap. 855 Post 01: eiendoms-GL fra BEFS (deler av driftsbudsjettet). Post 22: kjøp av private tjenester fra Innkjøpsanalyse-rapporten (oransje = ekstern kilde). Kap. 841 Post 01: lokalkostnader for familievern-eiendommer i BEFS." />
                                                                    </span>
                                                                </th>
                                                                {bfdSimMode && (
                                                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-primary">
                                                                        Foreslått
                                                                    </th>
                                                                )}
                                                                {bfdSimMode && (
                                                                    <th className="text-right px-4 py-2 font-medium text-xs uppercase tracking-wider text-muted">
                                                                        Delta
                                                                    </th>
                                                                )}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {kap.poster.map((post) => {
                                                                const simKey = `${kap.kap}-${post.post}`;
                                                                const foreslatt = foreslattValues[simKey] ?? post.bevilget;
                                                                const simDelta = bfdSimMode ? foreslatt - post.bevilget : 0;
                                                                return (
                                                                <React.Fragment key={post.post}>
                                                                    <tr className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                                                                        <td className="px-4 py-2.5 font-mono text-xs text-muted">{post.post}</td>
                                                                        <td className="px-4 py-2.5 text-foreground">{post.navn}</td>
                                                                        <td className="px-4 py-2.5 text-right font-medium tabular-nums">
                                                                            {formatNOK(post.bevilget)}
                                                                        </td>
                                                                        <td className="px-4 py-2.5 text-right text-xs">
                                                                            {kap.kap === 855 && post.post === "01" && glTotal
                                                                                ? <span className="font-medium tabular-nums">{formatNOK(glTotal.eiendom_total_nok)}</span>
                                                                                : kap.kap === 855 && post.post === "22" && glTotal?.innkjop_har_data && (glTotal.kjoep_bv_tjenester_nok ?? 0) > 0
                                                                                ? <span className="font-medium tabular-nums text-amber-600">{formatNOK(glTotal.kjoep_bv_tjenester_nok!)}</span>
                                                                                : kap.kap === 841 && post.post === "01" && glTotal && glTotal.familievern_eiendom_nok > 0
                                                                                ? <span className="font-medium tabular-nums">{formatNOK(glTotal.familievern_eiendom_nok)}</span>
                                                                                : <span className="text-muted/50">—</span>
                                                                            }
                                                                        </td>
                                                                        {bfdSimMode && (
                                                                            <td className="px-4 py-2 text-right">
                                                                                <input
                                                                                    type="number"
                                                                                    value={foreslatt}
                                                                                    step={1000000}
                                                                                    onChange={(e) => {
                                                                                        const v = parseFloat(e.target.value);
                                                                                        setForeslattValues(prev => ({ ...prev, [simKey]: isNaN(v) ? post.bevilget : v }));
                                                                                    }}
                                                                                    className="w-36 text-right border rounded px-2 py-1 text-xs bg-background focus:ring-1 focus:ring-primary outline-none tabular-nums"
                                                                                />
                                                                            </td>
                                                                        )}
                                                                        {bfdSimMode && (
                                                                            <td className={`px-4 py-2 text-right tabular-nums text-xs ${simDelta > 0 ? "text-red-600" : simDelta < 0 ? "text-green-600" : "text-muted/50"}`}>
                                                                                {simDelta !== 0 ? (simDelta > 0 ? "+" : "") + formatNOK(simDelta) : "—"}
                                                                            </td>
                                                                        )}
                                                                    </tr>
                                                                    {/* Injiserte under-rader etter Post 01 i Kap. 855 */}
                                                                    {kap.kap === 855 && post.post === "01" && glTotal?.innkjop_har_data && (glTotal.lokaler_nok ?? 0) > 0 && (
                                                                        <tr className="border-b border-border/50 bg-muted/5">
                                                                            <td className="px-4 py-2 pl-8 font-mono text-xs text-muted/40">↳</td>
                                                                            <td className="px-4 py-2 text-muted text-xs italic">
                                                                                Herav lokaler og vedlikehold
                                                                                <Tooltip text="Nasjonal sum for lokalkostnader fra Innkjøpsanalyse-rapporten. Inkluderer leie, reparasjon og vedlikehold av alle Bufetat-enheter." />
                                                                            </td>
                                                                            <td className="px-4 py-2 text-right text-muted/40 text-xs">—</td>
                                                                            <td className="px-4 py-2 text-right text-xs font-medium tabular-nums text-amber-600">
                                                                                {formatNOK(glTotal.lokaler_nok!)}
                                                                            </td>
                                                                            {bfdSimMode && <td />}
                                                                            {bfdSimMode && <td />}
                                                                        </tr>
                                                                    )}
                                                                </React.Fragment>
                                                                );
                                                            })}
                                                            <tr className="bg-muted/20 font-semibold">
                                                                <td className="px-4 py-2.5 text-xs text-muted" colSpan={2}>Totalt kap. {kap.kap}</td>
                                                                <td className="px-4 py-2.5 text-right tabular-nums">{formatNOK(totalBevilget)}</td>
                                                                <td className="px-4 py-2.5" />
                                                                {bfdSimMode && (
                                                                    <td className="px-4 py-2.5 text-right tabular-nums text-primary font-bold">
                                                                        {formatNOK(kap.poster.reduce((s, p) => s + (foreslattValues[`${kap.kap}-${p.post}`] ?? p.bevilget), 0))}
                                                                    </td>
                                                                )}
                                                                {bfdSimMode && (() => {
                                                                    const totalForeslatt = kap.poster.reduce((s, p) => s + (foreslattValues[`${kap.kap}-${p.post}`] ?? p.bevilget), 0);
                                                                    const d = totalForeslatt - totalBevilget;
                                                                    return (
                                                                        <td className={`px-4 py-2.5 text-right tabular-nums text-xs ${d > 0 ? "text-red-600" : d < 0 ? "text-green-600" : "text-muted/50"}`}>
                                                                            {d !== 0 ? (d > 0 ? "+" : "") + formatNOK(d) : "—"}
                                                                        </td>
                                                                    );
                                                                })()}
                                                            </tr>
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        );
                                    })}

                                    {bfdSimMode && (() => {
                                        const totalBev = bfdData.kapitler.flatMap(kk => kk.poster).reduce((s, p) => s + p.bevilget, 0);
                                        const totalFor = bfdData.kapitler.reduce((s, kk) => s + kk.poster.reduce((s2, p) => s2 + (foreslattValues[`${kk.kap}-${p.post}`] ?? p.bevilget), 0), 0);
                                        const diff = totalFor - totalBev;
                                        return (
                                            <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 flex flex-wrap gap-6 text-sm">
                                                <div>
                                                    <div className="text-xs text-muted uppercase tracking-wide mb-0.5">BFD Bevilget (alle kap.)</div>
                                                    <div className="font-bold tabular-nums">{formatNOK(totalBev)}</div>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-muted uppercase tracking-wide mb-0.5">Foreslått total</div>
                                                    <div className="font-bold text-primary tabular-nums">{formatNOK(totalFor)}</div>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-muted uppercase tracking-wide mb-0.5">Delta</div>
                                                    <div className={`font-bold tabular-nums ${diff > 0 ? "text-red-600" : diff < 0 ? "text-green-600" : "text-muted"}`}>
                                                        {diff !== 0 ? (diff > 0 ? "+" : "") + formatNOK(diff) : "Ingen endring"}
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => setForeslattValues({})}
                                                    className="self-end px-3 py-1.5 text-xs border rounded hover:bg-muted/30 transition-colors"
                                                >
                                                    Nullstill
                                                </button>
                                            </div>
                                        );
                                    })()}

                                    <p className="text-xs text-muted">
                                        Kilde: {bfdData.kilde}. Sist oppdatert: {bfdData.sist_oppdatert}.
                                        Beløp er bevilget ramme i NOK (hele kroner) fra BFDs budsjettkapitler i Prop. 1 S.
                                    </p>
                                </div>
                            ) : null}
                        </section>
                    </div>
                )}
            </main>
        </div>
    );
}
