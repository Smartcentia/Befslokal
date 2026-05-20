"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api/client";
import Link from "next/link";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Cell,
} from "recharts";
import {
    Building2, ChevronRight, RefreshCw, Info, TrendingDown,
    Landmark, CheckCircle2, AlertTriangle, FileText,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface SRS14Finansiell {
    contract_id: string; property_name: string; region: string;
    party_name: string; end_date: string; months_remaining: number;
    total_months: number; amount_per_year: number;
    remaining_payments: number; arlig_avskrivning: number;
    konto_eiendel: string; konto_forpliktelse: string;
    konto_avskrivning: string; konto_noytralisering: string;
    has_option: boolean;
}

interface SRS14Operasjonell {
    contract_id: string; property_name: string; region: string;
    party_name: string; end_date: string; months_remaining: number;
    amount_per_year: number;
}

interface AvskrivningAr {
    ar: number; avskrivning: number; restverdi: number;
    srs10_noytralisering: number;
}

interface SRS14Data {
    as_of: string;
    finansielle_count: number; operasjonelle_count: number;
    total_rou_eiendel: number; total_forpliktelse: number;
    total_arlig_avskrivning: number;
    klassifisering_kriterier: Record<string, string>;
    finansielle: SRS14Finansiell[];
    operasjonelle_sample: SRS14Operasjonell[];
    avskrivningsplan: AvskrivningAr[];
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);
const fmtM = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 1, notation: "compact" }).format(n);

function KpiCard({ title, value, sub, icon: Icon, color = "blue" }: {
    title: string; value: string; sub?: string;
    icon: React.ElementType; color?: "blue" | "green" | "amber" | "purple" | "red";
}) {
    const colors = {
        blue: "text-blue-600 bg-blue-50 border-blue-100",
        green: "text-green-600 bg-green-50 border-green-100",
        amber: "text-amber-600 bg-amber-50 border-amber-100",
        purple: "text-purple-600 bg-purple-50 border-purple-100",
        red: "text-red-600 bg-red-50 border-red-100",
    };
    return (
        <div className="bg-card border border-border rounded-xl p-5 flex flex-col gap-2">
            <div className="flex items-center justify-between">
                <span className="text-xs text-muted uppercase tracking-wider font-medium">{title}</span>
                <span className={`p-1.5 rounded-lg border ${colors[color]}`}><Icon size={14} /></span>
            </div>
            <div className="text-2xl font-bold text-foreground">{value}</div>
            {sub && <div className="text-xs text-muted">{sub}</div>}
        </div>
    );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function SRS14Page() {
    const [data, setData] = useState<SRS14Data | null>(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState<"oversikt" | "finansielle" | "operasjonelle" | "plan">("oversikt");

    const load = async () => {
        setLoading(true);
        try {
            const d = await fetchAPI("/financials/srs14-analyse");
            setData(d as SRS14Data);
        } catch { /* ignore */ } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    if (loading) return (
        <div className="min-h-screen bg-background flex items-center justify-center">
            <RefreshCw size={24} className="animate-spin text-primary" />
        </div>
    );

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="bg-card border-b border-border px-6 py-4">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 text-xs text-muted mb-1">
                            <Link href="/financials" className="hover:text-primary">Økonomi</Link>
                            <ChevronRight size={10} />
                            <span>SRS 14 – Leieavtaler</span>
                        </div>
                        <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                            <FileText size={20} className="text-primary" />
                            SRS 14 – Bruksrettseiendel og leieforpliktelse
                        </h1>
                        <p className="text-xs text-muted mt-0.5">
                            Klassifisering av leieavtaler · Konto 1265/2765 · SRS 17 avskrivning · SRS 10 nøytralisering
                        </p>
                    </div>
                    <button onClick={load} className="p-2 rounded-lg border border-border hover:bg-muted/30 text-muted">
                        <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                    </button>
                </div>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">
                {/* Regulatory note */}
                <div className="flex items-start gap-3 bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm">
                    <Info size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="text-blue-800 space-y-1">
                        <div><strong>SRS 14 – forenklet statlig metode:</strong> Bruksrettseiendel = sum gjenstående leiebetalinger (ingen nåverdidiskontering for stat).</div>
                        <div><strong>SRS 17:</strong> Avskrivning lineær over MIN(levetid, gjenværende leieperiode). Konto 6830 → avskrivning, 1268 → akkumulert.</div>
                        <div><strong>SRS 10:</strong> All avskrivning nøytraliseres med motpost på konto 3390 – netto resultateffekt = 0 kr for statlig etat.</div>
                        <div className="text-xs text-blue-600 pt-1">Kriterier brukt her: Finansiell lease = varighet &gt; 36 mnd OG årsleie &gt; 200 000 kr</div>
                    </div>
                </div>

                {data && (
                    <>
                        {/* KPIs */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <KpiCard title="Bruksrettseiendel (1265)"
                                value={fmtM(data.total_rou_eiendel)}
                                sub="Sum gjenstående betalinger"
                                icon={Landmark} color="purple" />
                            <KpiCard title="Leieforpliktelse (2765)"
                                value={fmtM(data.total_forpliktelse)}
                                sub="= bruksrettseiendel"
                                icon={TrendingDown} color="red" />
                            <KpiCard title="Årl. avskrivning (6830)"
                                value={fmtM(data.total_arlig_avskrivning)}
                                sub="Nøytraliseres via 3390"
                                icon={TrendingDown} color="amber" />
                            <KpiCard title="Finansielle leieavtaler"
                                value={String(data.finansielle_count)}
                                sub={`${data.operasjonelle_count} operasjonelle`}
                                icon={Building2} color="blue" />
                        </div>

                        {/* Tabs */}
                        <div className="flex gap-1 border-b border-border">
                            {([
                                { key: "oversikt", label: "Oversikt" },
                                { key: "finansielle", label: `Finansielle (${data.finansielle_count})` },
                                { key: "operasjonelle", label: `Operasjonelle (${data.operasjonelle_count})` },
                                { key: "plan", label: "Avskrivningsplan" },
                            ] as { key: typeof tab; label: string }[]).map(t => (
                                <button key={t.key} onClick={() => setTab(t.key)}
                                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                                        tab === t.key
                                            ? "border-primary text-primary"
                                            : "border-transparent text-muted hover:text-foreground"
                                    }`}>{t.label}</button>
                            ))}
                        </div>

                        {/* ── Oversikt ─────────────────────────────────────────────── */}
                        {tab === "oversikt" && (
                            <div className="space-y-6">
                                {/* Balance sheet summary */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <h2 className="text-base font-semibold mb-4">Balanseeffekt (SRS 14)</h2>
                                    <div className="grid md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <div className="text-xs text-muted uppercase font-medium mb-2">EIENDELER</div>
                                            <div className="flex justify-between py-2 border-b border-border/50">
                                                <span className="text-sm">1265 Bruksrettseiendel</span>
                                                <span className="font-semibold">{fmt(data.total_rou_eiendel)}</span>
                                            </div>
                                            <div className="flex justify-between py-2 border-b border-border/50 text-muted text-sm">
                                                <span>1268 Akkumulert avskrivning</span>
                                                <span>– (løpende)</span>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="text-xs text-muted uppercase font-medium mb-2">FORPLIKTELSER</div>
                                            <div className="flex justify-between py-2 border-b border-border/50">
                                                <span className="text-sm">2765 Leieforpliktelse</span>
                                                <span className="font-semibold text-red-600">{fmt(data.total_forpliktelse)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="mt-4 pt-4 border-t border-border">
                                        <div className="text-xs text-muted uppercase font-medium mb-2">RESULTATPÅVIRKNING (SRS 10 nøytralisert)</div>
                                        <div className="flex items-center gap-4 flex-wrap">
                                            <div className="flex items-center gap-2 text-sm">
                                                <span className="text-muted">6830 Avskrivning:</span>
                                                <span className="font-medium text-amber-700">–{fmt(data.total_arlig_avskrivning)}</span>
                                            </div>
                                            <span className="text-muted">+</span>
                                            <div className="flex items-center gap-2 text-sm">
                                                <span className="text-muted">3390 Nøytralisering:</span>
                                                <span className="font-medium text-green-600">+{fmt(data.total_arlig_avskrivning)}</span>
                                            </div>
                                            <span className="text-muted">=</span>
                                            <div className="flex items-center gap-2 text-sm font-semibold">
                                                <span>Netto resultat:</span>
                                                <span className="text-green-600">0 kr</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Klassifisering */}
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <h2 className="text-base font-semibold mb-4">Klassifisering av leieavtaler</h2>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <div className="border border-amber-200 bg-amber-50 rounded-xl p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <AlertTriangle size={16} className="text-amber-600" />
                                                <span className="font-semibold text-amber-800">Finansielle leieavtaler</span>
                                            </div>
                                            <div className="text-sm text-amber-700 space-y-1">
                                                <div>Kriterium: varighet &gt; 36 mnd OG årsleie &gt; 200 000 kr</div>
                                                <div className="font-medium">{data.finansielle_count} kontrakt{data.finansielle_count !== 1 ? "er" : ""} → aktiveres som bruksrettseiendel</div>
                                                <div>Konto 1265 / 2765</div>
                                            </div>
                                        </div>
                                        <div className="border border-green-200 bg-green-50 rounded-xl p-4">
                                            <div className="flex items-center gap-2 mb-2">
                                                <CheckCircle2 size={16} className="text-green-600" />
                                                <span className="font-semibold text-green-800">Operasjonelle leieavtaler</span>
                                            </div>
                                            <div className="text-sm text-green-700 space-y-1">
                                                <div>Alle øvrige kontrakter</div>
                                                <div className="font-medium">{data.operasjonelle_count} kontrakt{data.operasjonelle_count !== 1 ? "er" : ""} → kostnadsføres på konto 4960/6300</div>
                                                <div>Ingen balanseeffekt</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── Finansielle ──────────────────────────────────────────── */}
                        {tab === "finansielle" && (
                            <div className="bg-card border border-border rounded-xl p-5">
                                <h2 className="text-base font-semibold mb-1">Finansielle leieavtaler</h2>
                                <p className="text-xs text-muted mb-4">Aktiveres som bruksrettseiendel (konto 1265) og leieforpliktelse (konto 2765)</p>
                                {data.finansielle.length === 0 ? (
                                    <div className="flex items-center gap-2 text-green-600 text-sm py-6 justify-center">
                                        <CheckCircle2 size={16} />
                                        Ingen finansielle leieavtaler identifisert
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-border text-xs text-muted uppercase">
                                                    <th className="text-left py-2 pr-4">Eiendom / Utleier</th>
                                                    <th className="text-left py-2 pr-4">Region</th>
                                                    <th className="text-right py-2 pr-4">Utløper</th>
                                                    <th className="text-right py-2 pr-4">Mnd igjen</th>
                                                    <th className="text-right py-2 pr-4">Årsleie</th>
                                                    <th className="text-right py-2 pr-4">Bruksrettseindel</th>
                                                    <th className="text-right py-2">Årl. avsrkivn.</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {data.finansielle.map((r, i) => (
                                                    <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                        <td className="py-2 pr-4">
                                                            <div className="font-medium">{r.property_name}</div>
                                                            <div className="text-xs text-muted">{r.party_name}</div>
                                                        </td>
                                                        <td className="py-2 pr-4 text-xs text-muted">{r.region}</td>
                                                        <td className="py-2 pr-4 text-right font-mono text-xs">{r.end_date}</td>
                                                        <td className="py-2 pr-4 text-right">{r.months_remaining}</td>
                                                        <td className="py-2 pr-4 text-right">{fmt(r.amount_per_year)}</td>
                                                        <td className="py-2 pr-4 text-right font-semibold text-purple-700">{fmt(r.remaining_payments)}</td>
                                                        <td className="py-2 text-right text-amber-700">{fmt(r.arlig_avskrivning)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot>
                                                <tr className="border-t-2 border-border font-semibold text-sm">
                                                    <td colSpan={5} className="py-2 pr-4">Sum</td>
                                                    <td className="py-2 pr-4 text-right text-purple-700">{fmt(data.total_rou_eiendel)}</td>
                                                    <td className="py-2 text-right text-amber-700">{fmt(data.total_arlig_avskrivning)}</td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ── Operasjonelle ────────────────────────────────────────── */}
                        {tab === "operasjonelle" && (
                            <div className="bg-card border border-border rounded-xl p-5">
                                <h2 className="text-base font-semibold mb-1">Operasjonelle leieavtaler (utvalg)</h2>
                                <p className="text-xs text-muted mb-4">Kostnadsføres løpende – ingen balanseeffekt. Viser topp 20 etter årsleie.</p>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border text-xs text-muted uppercase">
                                                <th className="text-left py-2 pr-4">Eiendom</th>
                                                <th className="text-left py-2 pr-4">Utleier</th>
                                                <th className="text-right py-2 pr-4">Utløper</th>
                                                <th className="text-right py-2 pr-4">Mnd igjen</th>
                                                <th className="text-right py-2">Årsleie</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.operasjonelle_sample.map((r, i) => (
                                                <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                    <td className="py-2 pr-4 font-medium">{r.property_name}</td>
                                                    <td className="py-2 pr-4 text-xs text-muted">{r.party_name}</td>
                                                    <td className="py-2 pr-4 text-right font-mono text-xs">{r.end_date}</td>
                                                    <td className="py-2 pr-4 text-right">{r.months_remaining}</td>
                                                    <td className="py-2 text-right">{fmt(r.amount_per_year)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* ── Avskrivningsplan ─────────────────────────────────────── */}
                        {tab === "plan" && (
                            <div className="space-y-6">
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <h2 className="text-base font-semibold mb-1">Avskrivningsplan 2025–2030</h2>
                                    <p className="text-xs text-muted mb-4">SRS 17 lineær avskrivning + SRS 10 nøytralisering (3390)</p>
                                    <ResponsiveContainer width="100%" height={240}>
                                        <BarChart data={data.avskrivningsplan}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                            <XAxis dataKey="ar" tick={{ fontSize: 11 }} />
                                            <YAxis tickFormatter={v => fmtM(v)} tick={{ fontSize: 11 }} width={70} />
                                            <Tooltip formatter={(v: number, n: string) => [fmt(v), n]} contentStyle={{ fontSize: 12 }} />
                                            <Bar dataKey="avskrivning" fill="#f59e0b" radius={[4,4,0,0]} name="Avskrivning (6830)" />
                                            <Bar dataKey="srs10_noytralisering" fill="#22c55e" radius={[4,4,0,0]} name="Nøytralisering (3390)" opacity={0.7} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="bg-card border border-border rounded-xl p-5">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-border text-xs text-muted uppercase">
                                                <th className="text-left py-2 pr-4">År</th>
                                                <th className="text-right py-2 pr-4">Avskrivning (6830)</th>
                                                <th className="text-right py-2 pr-4">Restverdi (1265)</th>
                                                <th className="text-right py-2">SRS 10 nøytralisering (3390)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.avskrivningsplan.map((r, i) => (
                                                <tr key={i} className="border-b border-border/50 hover:bg-muted/20">
                                                    <td className="py-2 pr-4 font-medium">{r.ar}</td>
                                                    <td className="py-2 pr-4 text-right text-amber-700">–{fmt(r.avskrivning)}</td>
                                                    <td className="py-2 pr-4 text-right">{fmt(r.restverdi)}</td>
                                                    <td className="py-2 text-right text-green-600">+{fmt(r.srs10_noytralisering)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
