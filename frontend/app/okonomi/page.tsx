"use client";

import React, { useEffect, useState, useMemo } from "react";
import Header from "@/app/components/ui/Header";
import {
    parsePivotDetailCsv,
    parseAggregertCsv,
    parseFlatCsv,
    nameSimilarity,
    pivotRegionLabel,
    PIVOT_CATEGORY_STROM,
    PIVOT_CATEGORY_ANNEN_LOKALER,
    type PivotRow,
    type AggregertRow,
    type FlatRow,
} from "@/lib/utils/parseInnkjopCsv";
import { getProperties } from "@/lib/api";
import { Building2, Layers, SlidersHorizontal, CheckCircle2, AlertCircle, XCircle, Loader2, Search, TriangleAlert, Info, ShieldAlert } from "lucide-react";
import Link from "next/link";

const formatNOK = (n: number) =>
    new Intl.NumberFormat("nb-NO", {
        style: "currency",
        currency: "NOK",
        maximumFractionDigits: 0,
    }).format(n);

const REGIONS = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir"] as const;
type Region = (typeof REGIONS)[number];

function regionVal(row: AggregertRow | PivotRow, r: Region): number {
    switch (r) {
        case "Midt-Norge": return row.midt;
        case "Nord": return row.nord;
        case "Sør": return row.sor;
        case "Vest": return row.vest;
        case "Øst": return row.ost;
        case "Bufdir": return row.bufdir;
    }
}

type Tab = "aggregert" | "detaljert" | "sammenligning" | "husleie-vs-aggregert" | "anomalier";

interface Anomaly {
    type: "allokering" | "negativ" | "ekstremverdi" | "dominans";
    alvorlighet: "kritisk" | "advarsel" | "info";
    institusjon: string;
    kategori: string;
    region: string;
    beløp: number;
    beskrivelse: string;
    kontekst: string;
}

interface CostData {
    aggregert: AggregertRow[];
    leie: PivotRow[];
    strom: FlatRow[];
    annen: FlatRow[];
}

/** metadata fra public/data/costs2025/manifest.json */
interface CostsManifest {
    schemaVersion: number;
    dataYear: number;
    lastUpdated: string;
    source?: string;
    erpGrandTotalNok: number;
    aggregertCsvTotalsumNok?: number;
    notes?: string;
}

async function fetchCsv(path: string): Promise<string> {
    const res = await fetch(path);
    const buf = await res.arrayBuffer();
    // Prøv ISO-8859-1 (Windows-1252) for norske tegn
    try {
        return new TextDecoder("windows-1252").decode(buf);
    } catch {
        return new TextDecoder("utf-8").decode(buf);
    }
}

const DISMISS_KEY = "befs_dismissed_anomalies";

export default function OkonomiPage() {
    const [tab, setTab] = useState<Tab>("aggregert");
    const [data, setData] = useState<CostData | null>(null);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [regionFilter, setRegionFilter] = useState<string>("Alle");
    const [categoryFilter, setCategoryFilter] = useState<string>("Alle");
    const [befs, setBefs] = useState<{ name: string; region: string }[]>([]);
    const [dismissed, setDismissed] = useState<Set<string>>(new Set());
    const [showDismissed, setShowDismissed] = useState(false);
    const [costsMeta, setCostsMeta] = useState<CostsManifest | null>(null);

    // Load dismissed anomalies from localStorage
    useEffect(() => {
        try {
            const stored = localStorage.getItem(DISMISS_KEY);
            if (stored) setDismissed(new Set(JSON.parse(stored) as string[]));
        } catch { /* ignore */ }
    }, []);

    const dismissAnomaly = (key: string) => {
        setDismissed(prev => {
            const next = new Set(prev);
            next.add(key);
            try { localStorage.setItem(DISMISS_KEY, JSON.stringify([...next])); } catch { /* ignore */ }
            return next;
        });
    };

    const restoreAnomaly = (key: string) => {
        setDismissed(prev => {
            const next = new Set(prev);
            next.delete(key);
            try { localStorage.setItem(DISMISS_KEY, JSON.stringify([...next])); } catch { /* ignore */ }
            return next;
        });
    };

    const anomalyKey = (a: Anomaly) => `${a.type}|${a.institusjon}|${a.kategori}`;

    useEffect(() => {
        async function load() {
            const [metaRes, aggText, leieText, stromText, annenText] = await Promise.all([
                fetch("/data/costs2025/manifest.json"),
                fetchCsv("/data/costs2025/aggregert.csv"),
                fetchCsv("/data/costs2025/leie_av_lokaler.csv"),
                fetchCsv("/data/costs2025/strom_oppvarming.csv"),
                fetchCsv("/data/costs2025/annen_kostnad.csv"),
            ]);
            try {
                if (metaRes.ok) {
                    const m = (await metaRes.json()) as CostsManifest;
                    if (typeof m.erpGrandTotalNok === "number") setCostsMeta(m);
                }
            } catch {
                /* manifest valgfri */
            }
            setData({
                aggregert: parseAggregertCsv(aggText),
                leie: parsePivotDetailCsv(leieText),
                strom: parseFlatCsv(stromText, "Strøm og oppvarming"),
                annen: parseFlatCsv(annenText, "Annen kostnad lokaler"),
            });
            setLoading(false);
        }
        load();
        getProperties().then((props) =>
            setBefs(props.map((p) => ({ name: p.name ?? "", region: p.region ?? "" })))
        ).catch(() => {});
    }, []);

    // Alle unike institusjoner fra detalj-filene
    const allInstitutions = useMemo<string[]>(() => {
        if (!data) return [];
        const set = new Set<string>();
        data.leie.forEach((r) => set.add(r.institution));
        data.strom.forEach((r) => set.add(r.institution));
        data.annen.forEach((r) => set.add(r.institution));
        return [...set].sort();
    }, [data]);

    /** Bekreftet ERP-total (manifest), fallback hvis manifest mangler */
    const erpGrandTotal = costsMeta?.erpGrandTotalNok ?? 504_079_834;

    /**
     * Detaljert total: kun pivot-filen (full eksport med alle seksjoner).
     * Flat-filene strom/annen er samme poster og skal ikke legges til (unngår dobbelttelling).
     */
    const detailTotal = useMemo(() => {
        if (!data) return 0;
        return data.leie.reduce((a, r) => a + r.total, 0);
    }, [data]);

    const aggregertTotal = useMemo(() => {
        if (!data) return 0;
        const totalRow = data.aggregert.find((r) => r.category.startsWith("Totalsum"));
        return totalRow?.total ?? data.aggregert.reduce((a, r) => a + r.total, 0);
    }, [data]);

    // Per-kategori detaljert sum (for sammenligning mot aggregert) — kun pivot
    const detailByCategory = useMemo(() => {
        if (!data) return new Map<string, number>();
        const map = new Map<string, number>();
        for (const r of data.leie) {
            map.set(r.category, (map.get(r.category) ?? 0) + r.total);
        }
        return map;
    }, [data]);

    // Per institusjon: pivot splittet i «øvrige lokalkostnader» / strøm / annen (ingen dobbelttelling)
    const detailRows = useMemo(() => {
        if (!data) return [];
        const map = new Map<string, { institution: string; region: string; leie: number; strom: number; annen: number }>();

        data.leie.forEach((r) => {
            const key = r.institution;
            const existing = map.get(key) ?? { institution: r.institution, region: "", leie: 0, strom: 0, annen: 0 };
            const rl = pivotRegionLabel(r);
            if (!existing.region && rl) existing.region = rl;
            if (r.category === PIVOT_CATEGORY_STROM) {
                existing.strom += r.total;
            } else if (r.category === PIVOT_CATEGORY_ANNEN_LOKALER) {
                existing.annen += r.total;
            } else {
                existing.leie += r.total;
            }
            map.set(key, existing);
        });
        // Utfyll region fra flat-filer hvis pivot ikke ga region (sjeldent)
        data.strom.forEach((r) => {
            const existing = map.get(r.institution);
            if (existing && !existing.region && r.region) existing.region = r.region;
        });
        data.annen.forEach((r) => {
            const existing = map.get(r.institution);
            if (existing && !existing.region && r.region) existing.region = r.region;
        });

        return [...map.values()].sort((a, b) => (b.leie + b.strom + b.annen) - (a.leie + a.strom + a.annen));
    }, [data]);

    const filteredDetail = useMemo(() => {
        return detailRows.filter((r) => {
            const matchSearch = !search || r.institution.toLowerCase().includes(search.toLowerCase());
            const matchRegion = regionFilter === "Alle" || r.region.includes(regionFilter);
            return matchSearch && matchRegion;
        });
    }, [detailRows, search, regionFilter]);

    // Kostnad per institusjon for sammenligning
    const costByInstitution = useMemo(() => {
        const map = new Map<string, number>();
        detailRows.forEach((r) => map.set(r.institution, r.leie + r.strom + r.annen));
        return map;
    }, [detailRows]);

    // Sammenligning: ERP-institusjoner vs BEFS-eiendommer
    const matchResults = useMemo(() => {
        const results = allInstitutions.map((inst) => {
            const best = befs.reduce<{ name: string; region: string; score: number }>(
                (acc, b) => {
                    const score = nameSimilarity(inst, b.name);
                    return score > acc.score ? { name: b.name, region: b.region, score } : acc;
                },
                { name: "", region: "", score: 0 }
            );
            const status: "match" | "usikker" | "ingen" = best.score >= 0.7 ? "match" : best.score >= 0.4 ? "usikker" : "ingen";
            const cost = costByInstitution.get(inst) ?? 0;
            return { institution: inst, match: best, status, cost };
        });
        // Sort: ikkematchet med høy kostnad øverst (risikorangering), deretter usikre, til slutt matchede
        return results.sort((a, b) => {
            const order: Record<string, number> = { ingen: 0, usikker: 1, match: 2 };
            if (order[a.status] !== order[b.status]) return order[a.status] - order[b.status];
            return b.cost - a.cost;
        });
    }, [allInstitutions, befs, costByInstitution]);

    // ── Anomali-deteksjon ──────────────────────────────────────────────────────
    const anomalier = useMemo<Anomaly[]>(() => {
        if (!data) return [];
        const found: Anomaly[] = [];

        // Hjelpefunksjoner
        const stddev = (vals: number[]) => {
            const m = vals.reduce((a, b) => a + b, 0) / vals.length;
            return { mean: m, sd: Math.sqrt(vals.map(v => (v - m) ** 2).reduce((a, b) => a + b, 0) / vals.length) };
        };

        // ── 1. NEGATIVE BELØP (refusjoner / kreditnoter) ──────────────────────
        [...data.strom, ...data.annen].forEach((r) => {
            if (r.amount < 0) {
                found.push({
                    type: "negativ",
                    alvorlighet: "advarsel",
                    institusjon: r.institution,
                    kategori: r.category,
                    region: r.region,
                    beløp: r.amount,
                    beskrivelse: "Negativt beløp i ERP-eksport",
                    kontekst: "Kan være en refusjon, kreditnota eller reverseringsbilag. Bør verifiseres mot leverandørreskontro.",
                });
            }
        });
        data.leie.forEach((r) => {
            if (r.total < 0) {
                found.push({
                    type: "negativ",
                    alvorlighet: "advarsel",
                    institusjon: r.institution,
                    kategori: r.category,
                    region: "",
                    beløp: r.total,
                    beskrivelse: "Negativt leiebeløp i ERP-eksport",
                    kontekst: "Kan være en reversering eller kreditnota. Sjekk bilagsnummer i Agresso.",
                });
            }
        });

        // ── 2. ALLOKERINGSPOSTER (Regionkontor, Kontorfaglig enhet, Bufdir-sentralt) ─
        const ALLOC_KEYWORDS = ["Regionkontor", "Kontorfaglig enhet", "Bufdir"];
        const ALLOC_THRESHOLD = 5_000_000; // > 5M = kritisk
        detailRows.forEach((r) => {
            const total = r.leie + r.strom + r.annen;
            const isAlloc = ALLOC_KEYWORDS.some(kw => r.institution.startsWith(kw));
            if (isAlloc && total > ALLOC_THRESHOLD) {
                const isRegionkontor = r.institution.startsWith("Regionkontor");
                found.push({
                    type: "allokering",
                    alvorlighet: total > 50_000_000 ? "kritisk" : "advarsel",
                    institusjon: r.institution,
                    kategori: "Alle kategorier",
                    region: r.region || "—",
                    beløp: total,
                    beskrivelse: isRegionkontor
                        ? "Regionkontor med svært høye samlede kostnader"
                        : "Støtteenhet / sentralt allokert kostnad",
                    kontekst: isRegionkontor
                        ? "Regionkontorer samler ofte kostnader som ikke er fordelt på enkeltinstitusjoner i ERP. Total leie+strøm+annen kost tyder på at dette er en aggregert post, ikke ett bygg. Bør verifiseres mot Agresso koststedshierarki."
                        : "Sentralt koststed som trolig aggregerer kostnader fra flere enheter. Sjekk om dette bør splittes på underliggende kosteder.",
                });
            }
        });

        // ── 3. EKSTREMVERDIER (> gj.snitt + 2×SD innen kategori) ─────────────
        // Strøm per institusjon
        if (data.strom.length > 3) {
            const vals = data.strom.filter(r => r.amount > 0).map(r => r.amount);
            const { mean, sd } = stddev(vals);
            const thresh = mean + 2 * sd;
            data.strom.filter(r => r.amount > thresh).forEach((r) => {
                found.push({
                    type: "ekstremverdi",
                    alvorlighet: r.amount > mean + 3 * sd ? "kritisk" : "advarsel",
                    institusjon: r.institution,
                    kategori: "Strøm og oppvarming",
                    region: r.region,
                    beløp: r.amount,
                    beskrivelse: `Strøm/varme ${(r.amount / mean).toFixed(1)}× over gjennomsnittet`,
                    kontekst: `Gjennomsnitt: ${formatNOK(Math.round(mean))} / Terskel (+2SD): ${formatNOK(Math.round(thresh))}. Kan skyldes at posten samler kostnader for hele regionen (allokering) eller at det er feilkontering.`,
                });
            });
        }

        // Annen kostnad per institusjon
        if (data.annen.length > 3) {
            const vals = data.annen.filter(r => r.amount > 0).map(r => r.amount);
            const { mean, sd } = stddev(vals);
            const thresh = mean + 2 * sd;
            data.annen.filter(r => r.amount > thresh).forEach((r) => {
                found.push({
                    type: "ekstremverdi",
                    alvorlighet: r.amount > mean + 3 * sd ? "kritisk" : "advarsel",
                    institusjon: r.institution,
                    kategori: "Annen kostnad lokaler",
                    region: r.region,
                    beløp: r.amount,
                    beskrivelse: `Annen kostnad ${(r.amount / mean).toFixed(1)}× over gjennomsnittet`,
                    kontekst: `Gjennomsnitt: ${formatNOK(Math.round(mean))} / Terskel (+2SD): ${formatNOK(Math.round(thresh))}.`,
                });
            });
        }

        // Leie per institusjon (bruker total på tvers av leietyper)
        if (detailRows.length > 3) {
            const leieVals = detailRows.filter(r => r.leie > 0).map(r => r.leie);
            if (leieVals.length > 3) {
                const { mean, sd } = stddev(leieVals);
                const thresh = mean + 2 * sd;
                detailRows.filter(r => r.leie > thresh).forEach((r) => {
                    // Unngå duplikat med allokerings-funn
                    const alreadyFound = found.some(a => a.institusjon === r.institution && a.type === "allokering");
                    if (!alreadyFound) {
                        found.push({
                            type: "ekstremverdi",
                            alvorlighet: r.leie > mean + 3 * sd ? "kritisk" : "advarsel",
                            institusjon: r.institution,
                            kategori: "Leie lokaler (alle typer)",
                            region: r.region || "—",
                            beløp: r.leie,
                            beskrivelse: `Leiekostnad ${(r.leie / mean).toFixed(1)}× over gjennomsnittet`,
                            kontekst: `Gjennomsnitt: ${formatNOK(Math.round(mean))} / Terskel (+2SD): ${formatNOK(Math.round(thresh))}. Kan være en samlekonto for region.`,
                        });
                    }
                });
            }
        }

        // ── 4. DOMINANS — én enhet > 80% av regionens kategoritotal ──────────
        const regionGroups: Record<string, number[]> = {};
        data.strom.forEach(r => {
            if (!regionGroups[r.region]) regionGroups[r.region] = [];
            regionGroups[r.region].push(r.amount);
        });
        Object.entries(regionGroups).forEach(([region, amounts]) => {
            const regionTotal = amounts.reduce((a, b) => a + b, 0);
            data.strom.filter(r => r.region === region).forEach((r) => {
                const pct = regionTotal > 0 ? r.amount / regionTotal : 0;
                if (pct > 0.8 && amounts.length > 1 && r.amount > 500_000) {
                    const alreadyFound = found.some(a => a.institusjon === r.institution && a.kategori === "Strøm og oppvarming");
                    if (!alreadyFound) {
                        found.push({
                            type: "dominans",
                            alvorlighet: "advarsel",
                            institusjon: r.institution,
                            kategori: "Strøm og oppvarming",
                            region,
                            beløp: r.amount,
                            beskrivelse: `${(pct * 100).toFixed(0)}% av ${region}s strøm/varme-total`,
                            kontekst: `Én enhet dominerer hele regionens strøm og oppvarmingskostnad (${formatNOK(regionTotal)} totalt for regionen). Tyder på at øvrige enheter ikke har ført strøm per koststed, eller at dette er en allokert samlepost.`,
                        });
                    }
                }
            });
        });

        // Sorter: kritisk øverst, deretter etter beløp
        return found.sort((a, b) => {
            const order = { kritisk: 0, advarsel: 1, info: 2 };
            if (order[a.alvorlighet] !== order[b.alvorlighet]) return order[a.alvorlighet] - order[b.alvorlighet];
            return Math.abs(b.beløp) - Math.abs(a.beløp);
        });
    }, [data, detailRows]);

    const tabBtn = (t: Tab, label: string) => (
        <button
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                tab === t
                    ? "bg-primary text-primary-foreground"
                    : "text-muted hover:text-foreground hover:bg-muted/50"
            }`}
        >
            {label}
        </button>
    );

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Header />
            <main className="max-w-6xl mx-auto px-6 pt-24 pb-20">
                <div className="flex items-center gap-4 mb-6">
                    <div className="w-14 h-14 bg-primary/20 rounded-xl flex items-center justify-center text-primary border border-primary/20">
                        <Building2 size={28} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold">Eiendomskostnader 2025 — ERP-eksport</h1>
                        <p className="text-muted text-sm mt-1">
                            Faktiske kostnader fra regnskapssystemet. Aggregert og detaljert per institusjon/koststed.
                            Brukes til å verifisere at kostnader er plassert på riktig eiendom i BEFS.
                        </p>
                        {costsMeta?.lastUpdated && (
                            <p className="text-xs text-muted mt-2">
                                Datasett sist oppdatert i BEFS: {costsMeta.lastUpdated}
                                {costsMeta.source ? ` · Kilde: ${costsMeta.source}` : ""}
                            </p>
                        )}
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center gap-2 text-muted py-16">
                        <Loader2 size={20} className="animate-spin" />
                        Laster kostnadsdata…
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Sammendrag-kort */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
                                <div className="text-xs text-muted mb-1">Ekte ERP-total 2025</div>
                                <div className="text-2xl font-bold font-mono text-primary">{formatNOK(erpGrandTotal)}</div>
                                <div className="text-xs text-muted mt-1">Alle kategorier bekreftet fra Agresso</div>
                            </div>
                            <div className="rounded-xl border border-sky-500/30 bg-sky-500/5 p-4">
                                <div className="text-xs text-muted mb-1">Hva vi har detaljert</div>
                                <div className="text-2xl font-bold font-mono text-sky-500">{formatNOK(detailTotal)}</div>
                                <div className="text-xs text-muted mt-1">
                                    {((detailTotal / erpGrandTotal) * 100).toFixed(1)} % av ERP — full pivot-eksport (alle kategorier i én fil)
                                </div>
                            </div>
                            <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-4">
                                <div className="text-xs text-muted mb-1">Uten detaljfil</div>
                                <div className="text-2xl font-bold font-mono text-orange-500">{formatNOK(erpGrandTotal - detailTotal)}</div>
                                <div className="text-xs text-muted mt-1">
                                    {(((erpGrandTotal - detailTotal) / erpGrandTotal) * 100).toFixed(1)} % — differanse mot bekreftet ERP (skal være ~0 %)
                                </div>
                            </div>
                        </div>
                        {/* Dekningsbar */}
                        {data && (
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs text-muted">
                                    <span>Detaljdekningsgrad</span>
                                    <span>{((detailTotal / erpGrandTotal) * 100).toFixed(1)} %</span>
                                </div>
                                <div className="h-2 rounded-full bg-muted/30 overflow-hidden">
                                    <div
                                        className="h-full rounded-full bg-sky-500 transition-all"
                                        style={{ width: `${Math.min(100, (detailTotal / erpGrandTotal) * 100)}%` }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Tab-navigasjon */}
                        <div className="flex flex-wrap gap-2 border-b border-border pb-3">
                            {tabBtn("aggregert", "Aggregert oversikt")}
                            {tabBtn("husleie-vs-aggregert", "Husleie detaljert vs. aggregert")}
                            {tabBtn("detaljert", "Detaljert per institusjon")}
                            {tabBtn("sammenligning", "Sammenligning med BEFS")}
                            <button
                                onClick={() => setTab("anomalier")}
                                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                                    tab === "anomalier"
                                        ? "bg-amber-500 text-white"
                                        : "text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 border border-amber-500/30"
                                }`}
                            >
                                <TriangleAlert size={14} />
                                Anomalier {anomalier.length > 0 && (
                                    <span className={`ml-0.5 rounded-full px-1.5 py-0.5 text-xs font-bold ${tab === "anomalier" ? "bg-white/20" : "bg-amber-500/20"}`}>
                                        {anomalier.filter(a => a.alvorlighet === "kritisk").length > 0
                                            ? `${anomalier.filter(a => a.alvorlighet === "kritisk").length}🔴 ${anomalier.filter(a => a.alvorlighet !== "kritisk").length}🟡`
                                            : anomalier.length}
                                    </span>
                                )}
                            </button>
                        </div>

                        {/* ── Tab 1: Aggregert ── */}
                        {tab === "aggregert" && data && (
                            <section className="rounded-xl border border-border bg-card p-6">
                                <h2 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                                    <Layers size={18} />
                                    Kostnadskategorier × Region — 2025
                                </h2>
                                <p className="text-xs text-muted mb-4">
                                    Alle beløp i NOK. Kilde: Agresso/Cognos ERP-eksport.
                                </p>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border">
                                                <th className="text-left py-2 font-medium pr-4">Kostnadskategori</th>
                                                {REGIONS.map((r) => (
                                                    <th key={r} className="text-right py-2 font-medium px-2 whitespace-nowrap">{r}</th>
                                                ))}
                                                <th className="text-right py-2 font-medium pl-4 text-primary">Total (aggregert)</th>
                                                <th className="text-right py-2 font-medium pl-4 text-sky-500">Detaljert fil</th>
                                                <th className="text-right py-2 font-medium pl-4 text-muted">Avvik</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.aggregert.map((row) => {
                                                const isTotal = row.category.startsWith("Totalsum");
                                                const detFil = detailByCategory.get(row.category);
                                                const avvik = detFil !== undefined ? row.total - detFil : null;
                                                return (
                                                    <tr
                                                        key={row.category}
                                                        className={`border-b border-border/50 ${isTotal ? "font-bold bg-muted/30" : "hover:bg-muted/20"}`}
                                                    >
                                                        <td className={`py-2 pr-4 ${isTotal ? "text-foreground" : "text-foreground/90"}`}>
                                                            {row.category}
                                                        </td>
                                                        {REGIONS.map((r) => {
                                                            const val = regionVal(row, r);
                                                            return (
                                                                <td key={r} className="text-right py-2 px-2 font-mono text-xs">
                                                                    {val ? formatNOK(val) : <span className="text-muted/40">—</span>}
                                                                </td>
                                                            );
                                                        })}
                                                        <td className={`text-right py-2 pl-4 font-mono text-xs font-semibold ${isTotal ? "text-primary" : ""}`}>
                                                            {formatNOK(row.total)}
                                                        </td>
                                                        <td className="text-right py-2 pl-4 font-mono text-xs text-sky-500">
                                                            {detFil !== undefined ? formatNOK(detFil) : <span className="text-muted/40">—</span>}
                                                        </td>
                                                        <td className={`text-right py-2 pl-4 font-mono text-xs ${avvik === null ? "" : avvik === 0 ? "text-primary" : "text-yellow-500"}`}>
                                                            {avvik === null ? <span className="text-muted/40">—</span> : avvik === 0 ? "✓" : formatNOK(avvik)}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                                <p className="text-xs text-muted mt-4">
                                    «Detaljert fil» kommer fra pivot-eksport (samme omfang som total i kortet over). Strøm og annen kostnad er med i pivot;
                                    flat-filene brukes ikke i summer (unngår dobbelttelling).
                                </p>
                            </section>
                        )}

                        {/* ── Tab 2: Detaljert vs. aggregert ── */}
                        {tab === "husleie-vs-aggregert" && data && (
                            <section className="rounded-xl border border-border bg-card p-6 space-y-4">
                                <div>
                                    <h2 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                                        <Layers size={18} />
                                        Alle kategorier — detaljert vs. aggregert 2025
                                    </h2>
                                    <p className="text-xs text-muted">
                                        Grønn = vi har institusjonsnivå-data som stemmer med aggregert.
                                        Oransje = mangler detaljfil, kun aggregert totalsum tilgjengelig.
                                        Gul = avvik mellom detaljfil og aggregert (datavalideringsfunn).
                                    </p>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border text-xs">
                                                <th className="text-left py-2 font-medium w-6"></th>
                                                <th className="text-left py-2 font-medium">Kostnadskategori</th>
                                                <th className="text-right py-2 font-medium text-primary px-3">Aggregert (ERP)</th>
                                                <th className="text-right py-2 font-medium text-sky-500 px-3">Detaljert fil</th>
                                                <th className="text-right py-2 font-medium px-3">Avvik</th>
                                                <th className="text-right py-2 font-medium px-3">Avvik %</th>
                                                <th className="text-right py-2 font-medium px-3">% av ERP-total</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(() => {
                                                // Alle kategorier fra aggregert.csv (ekskl. Totalsum-rad)
                                                const aggCats = data.aggregert.filter(r => !r.category.startsWith("Totalsum"));
                                                let aggColSum = 0, detColSum = 0;
                                                return (
                                                    <>
                                                        {aggCats.map((aggRow) => {
                                                            const aggVal = aggRow.total;
                                                            const detVal = detailByCategory.get(aggRow.category);
                                                            const hasDetail = detVal !== undefined;
                                                            const avvik = hasDetail ? aggVal - detVal! : null;
                                                            const avvikPct = hasDetail && aggVal > 0 ? (avvik! / aggVal) * 100 : null;
                                                            const pctOfTotal = (aggVal / erpGrandTotal) * 100;
                                                            aggColSum += aggVal;
                                                            if (hasDetail) detColSum += detVal!;

                                                            // Fargekoding
                                                            const isOk = hasDetail && Math.abs(avvik!) < 10_000;
                                                            const isAvvik = hasDetail && Math.abs(avvik!) >= 10_000;
                                                            const isMissing = !hasDetail;

                                                            return (
                                                                <tr key={aggRow.category} className={`border-b border-border/40 hover:bg-muted/20 ${isMissing ? "opacity-70" : ""}`}>
                                                                    <td className="py-2 pl-1">
                                                                        {isOk && <span className="inline-block w-2 h-2 rounded-full bg-primary" title="Stemmer" />}
                                                                        {isAvvik && <span className="inline-block w-2 h-2 rounded-full bg-yellow-500" title="Avvik" />}
                                                                        {isMissing && <span className="inline-block w-2 h-2 rounded-full bg-orange-500" title="Mangler detaljfil" />}
                                                                    </td>
                                                                    <td className="py-2 text-foreground/90 pr-2">{aggRow.category}</td>
                                                                    <td className="text-right py-2 font-mono text-xs text-primary px-3">{formatNOK(aggVal)}</td>
                                                                    <td className="text-right py-2 font-mono text-xs text-sky-500 px-3">
                                                                        {hasDetail ? formatNOK(detVal!) : <span className="text-orange-500/70 text-xs italic">mangler detaljfil</span>}
                                                                    </td>
                                                                    <td className={`text-right py-2 font-mono text-xs px-3 ${isOk ? "text-primary" : isAvvik ? "text-yellow-500" : "text-muted/40"}`}>
                                                                        {avvik !== null ? (Math.abs(avvik) < 10_000 ? "✓" : formatNOK(avvik)) : "—"}
                                                                    </td>
                                                                    <td className={`text-right py-2 font-mono text-xs px-3 ${avvikPct !== null && Math.abs(avvikPct) < 1 ? "text-primary" : avvikPct !== null ? "text-yellow-500" : "text-muted/40"}`}>
                                                                        {avvikPct !== null ? `${avvikPct > 0 ? "+" : ""}${avvikPct.toFixed(1)} %` : "—"}
                                                                    </td>
                                                                    <td className="text-right py-2 font-mono text-xs text-muted px-3">
                                                                        {pctOfTotal.toFixed(1)} %
                                                                    </td>
                                                                </tr>
                                                            );
                                                        })}
                                                        {/* Sum-rad */}
                                                        <tr className="border-t-2 border-border bg-muted/20 font-bold text-sm">
                                                            <td></td>
                                                            <td className="py-3">Sum (vår CSV-fil)</td>
                                                            <td className="text-right py-3 font-mono text-xs text-primary px-3">{formatNOK(aggColSum)}</td>
                                                            <td className="text-right py-3 font-mono text-xs text-sky-500 px-3">{formatNOK(detColSum)}</td>
                                                            <td className={`text-right py-3 font-mono text-xs px-3 ${Math.abs(aggColSum - detColSum) < 10_000 ? "text-primary" : "text-yellow-500"}`}>
                                                                {formatNOK(aggColSum - detColSum)}
                                                            </td>
                                                            <td className="text-right py-3 font-mono text-xs px-3 text-muted">
                                                                {aggColSum > 0 ? `${(((aggColSum - detColSum) / aggColSum) * 100).toFixed(1)} %` : "—"}
                                                            </td>
                                                            <td className="text-right py-3 font-mono text-xs text-muted px-3">100 %</td>
                                                        </tr>
                                                        {/* Ekte ERP-total (inkl. kategorier som mangler i vår CSV) */}
                                                        <tr className="border-t border-dashed border-orange-500/40 bg-orange-500/5">
                                                            <td><span className="inline-block w-2 h-2 rounded-full bg-orange-500 ml-1" /></td>
                                                            <td className="py-2 text-orange-700 dark:text-orange-400 font-semibold text-xs">
                                                                Kategorier ikke i vår CSV-fil
                                                                <span className="ml-2 font-normal text-muted">(Fast bygningsinventar, Fellesutg. Statsbygg indre vedl. m.fl.)</span>
                                                            </td>
                                                            <td className="text-right py-2 font-mono text-xs text-orange-500 px-3">{formatNOK(erpGrandTotal - aggColSum)}</td>
                                                            <td colSpan={3} className="text-right py-2 text-xs text-muted px-3 italic">Bekreftet fra Agresso — ikke i aggregert.csv</td>
                                                            <td className="text-right py-2 font-mono text-xs text-orange-500 px-3">
                                                                {((erpGrandTotal - aggColSum) / erpGrandTotal * 100).toFixed(1)} %
                                                            </td>
                                                        </tr>
                                                        {/* Endelig ERP-total */}
                                                        <tr className="bg-primary/5 border-t-2 border-primary/30 font-bold">
                                                            <td></td>
                                                            <td className="py-3 text-primary">Ekte ERP-total (Agresso bekreftet)</td>
                                                            <td className="text-right py-3 font-mono text-xs text-primary px-3">{formatNOK(erpGrandTotal)}</td>
                                                            <td className="text-right py-3 font-mono text-xs text-sky-500 px-3">{formatNOK(detColSum)}</td>
                                                            <td className="text-right py-3 font-mono text-xs text-orange-500 px-3">{formatNOK(erpGrandTotal - detColSum)}</td>
                                                            <td className="text-right py-3 font-mono text-xs text-orange-500 px-3">
                                                                {`+${((erpGrandTotal - detColSum) / erpGrandTotal * 100).toFixed(1)} %`}
                                                            </td>
                                                            <td className="text-right py-3 font-mono text-xs text-primary px-3">100 %</td>
                                                        </tr>
                                                    </>
                                                );
                                            })()}
                                        </tbody>
                                    </table>
                                </div>
                                <div className="flex flex-wrap gap-4 pt-2 border-t border-border text-xs text-muted">
                                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-2 rounded-full bg-primary" /> Stemmer (&lt;10 000 kr avvik)</span>
                                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-2 rounded-full bg-yellow-500" /> Avvik (detaljfil ≠ aggregert)</span>
                                    <span className="flex items-center gap-1.5"><span className="inline-block w-2 h-2 rounded-full bg-orange-500" /> Mangler detaljfil — kun aggregert totalsum</span>
                                </div>
                            </section>
                        )}

                        {/* ── Tab 3: Detaljert ── */}
                        {tab === "detaljert" && (
                            <section className="rounded-xl border border-border bg-card p-6">
                                <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                                    <SlidersHorizontal size={18} />
                                    Kostnader per institusjon — 2025
                                </h2>
                                <div className="flex flex-wrap gap-3 mb-5">
                                    <div className="relative flex-1 min-w-[200px]">
                                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                                        <input
                                            type="text"
                                            placeholder="Søk institusjon…"
                                            value={search}
                                            onChange={(e) => setSearch(e.target.value)}
                                            className="w-full pl-8 pr-3 py-2 rounded-lg border border-input bg-background text-sm"
                                        />
                                    </div>
                                    <select
                                        value={regionFilter}
                                        onChange={(e) => setRegionFilter(e.target.value)}
                                        className="rounded-lg border border-input bg-background px-3 py-2 text-sm"
                                    >
                                        <option value="Alle">Alle regioner</option>
                                        {REGIONS.filter((r) => r !== "Bufdir").map((r) => (
                                            <option key={r} value={r}>{r}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border">
                                                <th className="text-left py-2 font-medium">Institusjon / Koststed</th>
                                                <th className="text-right py-2 font-medium">Region</th>
                                                <th className="text-right py-2 font-medium text-primary">Leie lokaler</th>
                                                <th className="text-right py-2 font-medium">Strøm/varme</th>
                                                <th className="text-right py-2 font-medium">Annen kost.</th>
                                                <th className="text-right py-2 font-medium font-semibold">Sum</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredDetail.map((r) => (
                                                <tr key={r.institution} className="border-b border-border/50 hover:bg-muted/20">
                                                    <td className="py-2 max-w-xs truncate" title={r.institution}>{r.institution}</td>
                                                    <td className="text-right py-2 text-muted text-xs">{r.region || "—"}</td>
                                                    <td className="text-right py-2 text-primary font-mono text-xs">{r.leie ? formatNOK(r.leie) : <span className="text-muted/40">—</span>}</td>
                                                    <td className="text-right py-2 font-mono text-xs">{r.strom ? formatNOK(r.strom) : <span className="text-muted/40">—</span>}</td>
                                                    <td className="text-right py-2 font-mono text-xs">{r.annen ? formatNOK(r.annen) : <span className="text-muted/40">—</span>}</td>
                                                    <td className="text-right py-2 font-mono text-xs font-semibold">
                                                        {formatNOK(r.leie + r.strom + r.annen)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <p className="text-xs text-muted mt-3">
                                    {filteredDetail.length} av {detailRows.length} institusjoner vist.
                                    Første kolonne er alle lokalkostnader fra pivot unntatt strøm og «annen kostnad lokaler» (disse har egne kolonner).
                                </p>
                            </section>
                        )}

                        {/* ── Tab 5: Anomalier ── */}
                        {tab === "anomalier" && (
                            <section className="space-y-4">
                                <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
                                    <h2 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                                        <ShieldAlert size={18} className="text-amber-500" />
                                        Automatisk anomalideteksjon — ERP-data 2025
                                    </h2>
                                    <p className="text-xs text-muted">
                                        Identifiserer statisktiske uteliggere, negative beløp, allokeringsposter og dominanseffekter.
                                        Hvert funn bør verifiseres manuelt mot Agresso/koststedshierarki.
                                    </p>
                                    <div className="flex flex-wrap items-center justify-between gap-3 mt-3">
                                        <div className="flex gap-4 text-xs">
                                            <span className="flex items-center gap-1 font-medium text-red-600 dark:text-red-400">
                                                <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Kritisk ({anomalier.filter(a => a.alvorlighet === "kritisk").length})
                                            </span>
                                            <span className="flex items-center gap-1 font-medium text-amber-600 dark:text-amber-400">
                                                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Advarsel ({anomalier.filter(a => a.alvorlighet === "advarsel").length})
                                            </span>
                                            <span className="flex items-center gap-1 font-medium text-sky-600 dark:text-sky-400">
                                                <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" /> Info ({anomalier.filter(a => a.alvorlighet === "info").length})
                                            </span>
                                        </div>
                                        {dismissed.size > 0 && (
                                            <button
                                                onClick={() => setShowDismissed(p => !p)}
                                                className="text-xs text-muted hover:text-foreground border border-border rounded-lg px-3 py-1.5 transition-colors"
                                            >
                                                {showDismissed ? "Skjul gjennomgåtte" : `Vis gjennomgåtte (${dismissed.size})`}
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {(() => {
                                    const visibleAnomalier = anomalier.filter(a => !dismissed.has(anomalyKey(a)));
                                    const dismissedAnomalier = anomalier.filter(a => dismissed.has(anomalyKey(a)));
                                    const renderCard = (a: Anomaly, i: number, isDismissed = false) => {
                                        const key = anomalyKey(a);
                                        const colors = {
                                            kritisk: { border: "border-red-500/40", bg: "bg-red-500/5", icon: "text-red-500", badge: "bg-red-500/10 text-red-600 dark:text-red-400" },
                                            advarsel: { border: "border-amber-500/40", bg: "bg-amber-500/5", icon: "text-amber-500", badge: "bg-amber-500/10 text-amber-600 dark:text-amber-400" },
                                            info:     { border: "border-sky-500/40",   bg: "bg-sky-500/5",   icon: "text-sky-500",   badge: "bg-sky-500/10 text-sky-600 dark:text-sky-400" },
                                        }[a.alvorlighet];
                                        const typeLabel = { allokering: "Allokering", negativ: "Negativt beløp", ekstremverdi: "Ekstremverdi", dominans: "Dominanseffekt" }[a.type];
                                        const TypeIcon = { allokering: ShieldAlert, negativ: TriangleAlert, ekstremverdi: AlertCircle, dominans: Info }[a.type];
                                        return (
                                            <div key={`${isDismissed ? "d" : "v"}-${i}`} className={`rounded-xl border ${colors.border} ${colors.bg} p-5 ${isDismissed ? "opacity-50" : ""}`}>
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="flex items-start gap-3 flex-1">
                                                        <TypeIcon size={20} className={`mt-0.5 shrink-0 ${colors.icon}`} />
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex flex-wrap items-center gap-2 mb-1">
                                                                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${colors.badge}`}>
                                                                    {a.alvorlighet.toUpperCase()} · {typeLabel}
                                                                </span>
                                                                {a.region && a.region !== "—" && (
                                                                    <span className="text-[10px] text-muted bg-muted/30 px-2 py-0.5 rounded-full">{a.region}</span>
                                                                )}
                                                                <span className="text-[10px] text-muted bg-muted/30 px-2 py-0.5 rounded-full">{a.kategori}</span>
                                                                {isDismissed && (
                                                                    <span className="text-[10px] text-primary bg-primary/10 px-2 py-0.5 rounded-full">✓ Gjennomgått</span>
                                                                )}
                                                            </div>
                                                            <div className="font-semibold text-foreground text-sm">{a.institusjon}</div>
                                                            <div className="text-xs text-foreground/80 mt-0.5">{a.beskrivelse}</div>
                                                            <div className="text-xs text-muted mt-2 leading-relaxed">{a.kontekst}</div>
                                                        </div>
                                                    </div>
                                                    <div className="text-right shrink-0 flex flex-col items-end gap-2">
                                                        <div className={`text-xl font-bold font-mono ${a.beløp < 0 ? "text-red-500" : colors.icon}`}>
                                                            {formatNOK(a.beløp)}
                                                        </div>
                                                        <div className="text-[10px] text-muted">
                                                            {((Math.abs(a.beløp) / erpGrandTotal) * 100).toFixed(2)}% av ERP-total
                                                        </div>
                                                        {isDismissed ? (
                                                            <button
                                                                onClick={() => restoreAnomaly(key)}
                                                                className="text-[10px] text-muted hover:text-foreground border border-border/50 rounded px-2 py-0.5 transition-colors"
                                                            >
                                                                Gjenopprett
                                                            </button>
                                                        ) : (
                                                            <button
                                                                onClick={() => dismissAnomaly(key)}
                                                                className="text-[10px] text-muted hover:text-primary border border-border/50 rounded px-2 py-0.5 transition-colors"
                                                            >
                                                                Merk gjennomgått
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    };

                                    return (
                                        <>
                                            {visibleAnomalier.length === 0 && (
                                                <div className="rounded-xl border border-border bg-card p-8 text-center text-muted text-sm">
                                                    <CheckCircle2 size={32} className="mx-auto mb-2 text-primary" />
                                                    {dismissed.size > 0 ? `Alle ${dismissed.size} anomalier er merket som gjennomgått` : "Ingen anomalier oppdaget"}
                                                </div>
                                            )}
                                            {visibleAnomalier.map((a, i) => renderCard(a, i, false))}
                                            {showDismissed && dismissedAnomalier.length > 0 && (
                                                <>
                                                    <div className="flex items-center gap-2 text-xs text-muted pt-2">
                                                        <div className="flex-1 border-t border-dashed border-border" />
                                                        Gjennomgåtte anomalier ({dismissedAnomalier.length})
                                                        <div className="flex-1 border-t border-dashed border-border" />
                                                    </div>
                                                    {dismissedAnomalier.map((a, i) => renderCard(a, i, true))}
                                                </>
                                            )}
                                        </>
                                    );
                                })()}

                                <div className="rounded-xl border border-border bg-card p-4 text-xs text-muted">
                                    <strong className="text-foreground">Metode:</strong> Negative beløp detekteres direkte. Ekstremverdier beregnes som gjennomsnitt + 2×standardavvik innen hver kostnadskategori.
                                    Allokeringsposter identifiseres ved navn («Regionkontor», «Kontorfaglig enhet», «Bufdir»). Dominans flagges når én enhet &gt;80% av regionsummen for en kategori.
                                </div>
                            </section>
                        )}

                        {/* ── Tab 4: Sammenligning ── */}
                        {tab === "sammenligning" && (
                            <section className="rounded-xl border border-border bg-card p-6">
                                <h2 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                                    <Building2 size={18} />
                                    ERP-institusjon vs. BEFS-eiendom
                                </h2>
                                <p className="text-xs text-muted mb-4">
                                    Sjekker om koststedsnavnet fra ERP matcher en eiendom i BEFS.
                                    Brukes til å verifisere at kostnader er plassert korrekt.
                                </p>
                                <div className="flex gap-4 mb-4 text-xs">
                                    <span className="flex items-center gap-1 text-primary"><CheckCircle2 size={13} /> Matchet (≥70%)</span>
                                    <span className="flex items-center gap-1 text-yellow-500"><AlertCircle size={13} /> Usikker (40–70%)</span>
                                    <span className="flex items-center gap-1 text-destructive"><XCircle size={13} /> Ikke matchet (&lt;40%)</span>
                                </div>
                                {befs.length === 0 && (
                                    <div className="text-muted text-xs mb-4 italic">BEFS-eiendommer ikke lastet — sammenligning basert på navn alene.</div>
                                )}
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border">
                                                <th className="text-left py-2 font-medium w-6"></th>
                                                <th className="text-left py-2 font-medium">ERP-institusjon</th>
                                                <th className="text-left py-2 font-medium">BEFS-match</th>
                                                <th className="text-right py-2 font-medium">Score</th>
                                                <th className="text-right py-2 font-medium text-primary">ERP-kostnad</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {matchResults.map((r) => (
                                                <tr key={r.institution} className={`border-b border-border/50 hover:bg-muted/20 ${r.status === "ingen" && r.cost > 5_000_000 ? "bg-red-500/5" : ""}`}>
                                                    <td className="py-1.5">
                                                        {r.status === "match" && <CheckCircle2 size={14} className="text-primary" />}
                                                        {r.status === "usikker" && <AlertCircle size={14} className="text-yellow-500" />}
                                                        {r.status === "ingen" && <XCircle size={14} className="text-destructive" />}
                                                    </td>
                                                    <td className="py-1.5 text-foreground/90">{r.institution}</td>
                                                    <td className="py-1.5 text-muted text-xs">
                                                        {r.match.name ? (
                                                            <Link href={`/institusjoner`} className="hover:text-primary hover:underline underline-offset-2 transition-colors">
                                                                {r.match.name}
                                                            </Link>
                                                        ) : <span className="text-destructive/60 italic text-[11px]">ingen match i BEFS</span>}
                                                    </td>
                                                    <td className="text-right py-1.5 font-mono text-xs text-muted">
                                                        {r.match.score > 0 ? `${(r.match.score * 100).toFixed(0)} %` : "—"}
                                                    </td>
                                                    <td className={`text-right py-1.5 font-mono text-xs ${r.cost > 5_000_000 ? "text-primary font-semibold" : "text-muted"}`}>
                                                        {r.cost > 0 ? formatNOK(r.cost) : <span className="text-muted/40">—</span>}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                                    {(["match", "usikker", "ingen"] as const).map((s) => {
                                        const count = matchResults.filter((r) => r.status === s).length;
                                        const label = s === "match" ? "Matchet" : s === "usikker" ? "Usikker" : "Ikke matchet";
                                        const color = s === "match" ? "text-primary" : s === "usikker" ? "text-yellow-500" : "text-destructive";
                                        return (
                                            <div key={s} className="rounded-lg bg-muted/40 p-3 text-center">
                                                <div className={`text-2xl font-bold ${color}`}>{count}</div>
                                                <div className="text-muted mt-0.5">{label}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </section>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
