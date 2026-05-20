"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { financialAnalysisApi, type GlUtenEiendomResponse } from "@/lib/api/financialAnalysisApi";
import Header from "@/app/components/ui/Header";
import { Landmark, ArrowLeft } from "lucide-react";

function fmtKr(n: number) {
 return new Intl.NumberFormat("nb-NO", {
        style: "currency",
        currency: "NOK",
        maximumFractionDigits: 0,
    }).format(n);
}

function fmtN(n: number) {
    return new Intl.NumberFormat("nb-NO").format(n);
}

export default function SentralOkonomiPage() {
    const [ar, setAr] = useState(2025);
    const [data, setData] = useState<GlUtenEiendomResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            setError(null);
            try {
                const res = await financialAnalysisApi.getGlUtenEiendom(ar);
                if (!cancelled) setData(res);
            } catch (e: unknown) {
                if (!cancelled) {
                    setError(e instanceof Error ? e.message : "Kunne ikke hente data");
                    setData(null);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [ar]);

    const op = data?.oppsummering;

    return (
        <div className="min-h-screen bg-background">
            <Header />
            <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                    <Link
                        href="/financials"
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Økonomi
                    </Link>
                    <span aria-hidden>·</span>
                    <span className="inline-flex items-center gap-1.5">
                        <Landmark className="h-4 w-4" />
                        GL uten koblet eiendom
                    </span>
                </div>

                <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
                    <h1 className="text-xl font-semibold text-foreground">GL uten eiendomskobling</h1>
                    <p className="mt-2 text-sm text-muted-foreground max-w-3xl">
                        Viser aggregerte Agresso-poster der <code className="text-xs bg-muted px-1 rounded">property_id</code>{" "}
                        er tom — typisk Bufdir, regionskostnader og annet som ikke inngår i eiendoms-SRS.
                        Full bokføring ligger fortsatt i Agresso; dette er et analyseutsnitt i BEFS.
                    </p>
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                        <label className="text-sm font-medium text-foreground">År:</label>
                        <select
                            value={ar}
                            onChange={(e) => setAr(Number(e.target.value))}
                            className="border border-border rounded-md px-3 py-1.5 text-sm bg-background text-foreground"
                        >
                            {[2025, 2024, 2023, 2022, 2021].map((y) => (
                                <option key={y} value={y}>
                                    {y}
                                </option>
                            ))}
                        </select>
                        {loading && <span className="text-sm text-muted-foreground">Laster…</span>}
                    </div>
                </div>

                {error && (
                    <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                        {error}
                    </div>
                )}

                {op && !error && (
                    <div className="grid gap-4 sm:grid-cols-3">
                        <div className="rounded-lg border border-border bg-card p-4">
                            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Transaksjoner
                            </div>
                            <div className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
                                {fmtN(op.antall_transaksjoner)}
                            </div>
                        </div>
                        <div className="rounded-lg border border-border bg-card p-4">
                            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Sum beløp
                            </div>
                            <div className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
                                {fmtKr(op.sum_belop)}
                            </div>
                        </div>
                        <div className="rounded-lg border border-border bg-card p-4">
                            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                Koststad-grupper
                            </div>
                            <div className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
                                {fmtN(op.antall_koststed_grupper)}
                            </div>
                        </div>
                    </div>
                )}

                {data && !loading && !error && (
                    <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border bg-muted/50 text-left">
                                        <th className="px-4 py-3 font-medium text-foreground">Koststed</th>
                                        <th className="px-4 py-3 font-medium text-foreground">Navn</th>
                                        <th className="px-4 py-3 font-medium text-foreground">Region</th>
                                        <th className="px-4 py-3 font-medium text-foreground text-right">Antall</th>
                                        <th className="px-4 py-3 font-medium text-foreground text-right">Sum</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.rader.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                                                Ingen GL-rader uten eiendom for {ar}.
                                            </td>
                                        </tr>
                                    ) : (
                                        data.rader.map((r) => (
                                            <tr key={r.dim1_kode + r.region} className="border-b border-border/80 hover:bg-muted/30">
                                                <td className="px-4 py-2.5 font-mono text-xs text-foreground">{r.dim1_kode}</td>
                                                <td className="px-4 py-2.5 text-foreground max-w-md truncate" title={r.dim1_navn}>
                                                    {r.dim1_navn}
                                                </td>
                                                <td className="px-4 py-2.5 text-muted-foreground">{r.region || "—"}</td>
                                                <td className="px-4 py-2.5 text-right tabular-nums text-foreground">{fmtN(r.antall)}</td>
                                                <td className="px-4 py-2.5 text-right tabular-nums font-medium text-foreground">
                                                    {fmtKr(r.sum_belop)}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
