"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import Header from "@/app/components/ui/Header";
import { Users, Mail, Phone, ExternalLink, ShieldCheck, MapPin, AlertTriangle } from "lucide-react";
import { HealthScoreBadge, type HealthScore } from "@/app/components/features/HealthScoreBadge";
import { getTenantsWithProperty } from "@/lib/api";
import { motion } from "framer-motion";

const LIMIT = 50;

/** Data fra Brreg lagres i external_data.brreg_enhet (adresse, type, source, email, phone). */
interface PartyExternalData {
    source?: string;
    address?: string;
    email?: string;
    phone?: string;
    type?: string;
    orgForm?: string;
    brreg_enhet?: {
        source?: string;
        address?: string;
        email?: string;
        phone?: string;
        type?: string;
        [key: string]: unknown;
    };
    [key: string]: unknown;
}

interface Party {
    party_id: string;
    name: string;
    orgnr?: string;
    role?: string;
    is_company?: boolean;
    contact_email?: string;
    contact_phone?: string;
    external_data?: PartyExternalData | null;
    health_score?: {
        score?: number;
        label?: string;
        emoji?: string;
        category?: string;
        factors?: string[];
        confidence?: number;
        rationale?: string;
    } | null;
}

interface TenantWithProperty extends Party {
    property?: {
        latitude?: number;
        longitude?: number;
        address?: string;
        name?: string;
    };
}

function isBrregSource(ext?: PartyExternalData | null): boolean {
    const brreg = ext?.brreg_enhet;
    const source = ext?.source ?? brreg?.source;
    return Boolean(source && String(source).toUpperCase().includes("BRREG"));
}

function displayEmail(party: TenantWithProperty): string {
    const ext = party.external_data;
    const fromExt = ext?.email ?? ext?.brreg_enhet?.email;
    if (fromExt && fromExt !== "N/A") return fromExt;
    return party.contact_email || "Ingen e-post";
}

function displayPhone(party: TenantWithProperty): string {
    const ext = party.external_data;
    const fromExt = ext?.phone ?? ext?.brreg_enhet?.phone;
    if (fromExt && fromExt !== "N/A") return fromExt;
    return party.contact_phone || "Ingen telefon";
}

function displayAddress(party: TenantWithProperty): string | null {
    const ext = party.external_data;
    const fromExt = ext?.address ?? ext?.brreg_enhet?.address;
    if (fromExt && fromExt.trim() && !fromExt.startsWith(",")) return fromExt;
    return null;
}

type SortMode = "navn" | "risiko";

export default function TenantsPage() {
    const [tenants, setTenants] = useState<TenantWithProperty[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [sortMode, setSortMode] = useState<SortMode>("risiko");
    const skipRef = useRef(0);

    const loadTenants = useCallback(async (append: boolean) => {
        try {
            if (append) {
                setLoadingMore(true);
            } else {
                setLoading(true);
                skipRef.current = 0;
            }

            const data = await getTenantsWithProperty({
                skip: skipRef.current,
                limit: LIMIT,
            });

            const sorted = [...data].sort((a, b) => {
                const sa = a.health_score?.score ?? 1;
                const sb = b.health_score?.score ?? 1;
                if (sb !== sa) return sb - sa;
                return a.name.localeCompare(b.name, "nb");
            });

            if (append) {
                setTenants((prev) => [...prev, ...sorted]);
            } else {
                setTenants(sorted);
            }
            skipRef.current += data.length;
            setHasMore(data.length === LIMIT);
        } catch (e) {
            console.error("Failed to load tenants", e);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        loadTenants(false);
    }, [loadTenants]);

    return (
        <div className="min-h-screen font-sans pb-20 bg-background">
            <Header />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
                <div className="mb-8 flex justify-between items-end flex-wrap gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground tracking-tight">Leietakere</h1>
                        <p className="text-muted mt-2">Oversikt over alle parter og leietakere i systemet.</p>
                        {/* Risk summary */}
                        {!loading && tenants.length > 0 && (() => {
                            const counts = { 4: 0, 3: 0, 2: 0, 1: 0 };
                            tenants.forEach(t => { const s = t.health_score?.score ?? 1; counts[s as keyof typeof counts]++; });
                            return (
                                <div className="flex items-center gap-3 mt-3 flex-wrap">
                                    {counts[4] > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-700 dark:text-red-400 font-bold">🚨 {counts[4]} Kritisk</span>}
                                    {counts[3] > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-700 dark:text-orange-400 font-bold">🔶 {counts[3]} Oransje</span>}
                                    {counts[2] > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-700 dark:text-yellow-400 font-bold">⚠️ {counts[2]} Gul</span>}
                                    {counts[1] > 0 && <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 font-bold">✅ {counts[1]} Grønn</span>}
                                </div>
                            );
                        })()}
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex rounded-lg border border-border overflow-hidden text-xs font-medium">
                            <button onClick={() => setSortMode("risiko")} className={`px-3 py-1.5 transition-colors ${sortMode === "risiko" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted/50"}`}>Risiko</button>
                            <button onClick={() => setSortMode("navn")} className={`px-3 py-1.5 transition-colors ${sortMode === "navn" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted/50"}`}>Navn A–Å</button>
                        </div>
                        <button className="px-4 py-2 bg-primary text-primary-foreground font-bold rounded-lg text-sm hover:opacity-90 transition-colors shadow-lg shadow-primary/20">
                            + Ny Leietaker
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3, 4, 5, 6].map(i => (
                            <div key={i} className="h-40 glass-card animate-pulse" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {tenants.length === 0 ? (
                            <div className="col-span-full p-20 text-center glass-card text-muted">
                                <Users size={48} className="mx-auto mb-4 opacity-20" />
                                <p>Ingen leietakere funnet i systemet.</p>
                            </div>
                        ) : (
                            [...tenants]
                                .sort((a, b) => sortMode === "navn"
                                    ? a.name.localeCompare(b.name, "nb")
                                    : (b.health_score?.score ?? 1) - (a.health_score?.score ?? 1) || a.name.localeCompare(b.name, "nb")
                                )
                                .map((t, idx) => (
                                    <Link key={t.party_id} href={`/parties/${t.party_id}`} className="block" prefetch={false}>
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                            className="glass-card hover:shadow-md transition-all cursor-pointer group overflow-hidden flex flex-col"
                                        >
                                        {/* Content section */}
                                        <div className="p-6 flex-1 flex flex-col">
                                            <div className="flex items-start justify-between mb-4">
                                                <div className="p-3 bg-primary/10 text-primary rounded-xl group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                                    <Users size={24} />
                                                </div>
                                                <div className="flex items-center gap-2 flex-wrap justify-end">
                                                    <HealthScoreBadge score={t.health_score as HealthScore | null | undefined} />
                                                    {isBrregSource(t.external_data) && (
                                                        <span className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider flex items-center gap-1" title="Data fra Brønnøysundregistrene">
                                                            <ShieldCheck size={10} /> BRREG
                                                        </span>
                                                    )}
                                                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${t.orgnr ? 'bg-primary/20 text-primary' : 'bg-warning/20 text-warning'}`}>
                                                        {t.orgnr ? 'Bedrift' : 'Privat'}
                                                    </span>
                                                </div>
                                            </div>

                                            <h3 className="font-bold text-foreground text-lg mb-1 group-hover:text-primary transition-colors">{t.name}</h3>
                                            <div className="flex items-center gap-2 text-xs text-muted mb-2">
                                                <ShieldCheck size={12} />
                                                <span>Org.nr: {t.orgnr || "—"}</span>
                                            </div>

                                            {displayAddress(t) && (
                                                <div className="flex items-start gap-2 text-xs text-foreground mb-2">
                                                    <MapPin size={12} className="text-muted mt-0.5 shrink-0" />
                                                    <span className="line-clamp-2">{displayAddress(t)}</span>
                                                </div>
                                            )}

                                            {t.property?.address && (
                                                <div className="text-xs text-foreground mb-2">
                                                    <span className="font-semibold">Eiendom:</span> {t.property.address}
                                                </div>
                                            )}

                                            <div className="space-y-2 border-t border-border pt-4 mt-auto">
                                                <div className="flex items-center gap-2 text-xs text-foreground">
                                                    <Mail size={14} className="text-muted shrink-0" />
                                                    <span className="truncate">{displayEmail(t)}</span>
                                                </div>
                                                <div className="flex items-center gap-2 text-xs text-foreground">
                                                    <Phone size={14} className="text-muted shrink-0" />
                                                    <span className="truncate">{displayPhone(t)}</span>
                                                </div>
                                            </div>

                                            <div className="mt-4 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                                                <span className="text-xs font-bold text-primary flex items-center gap-1">
                                                    Se profil <ExternalLink size={12} />
                                                </span>
                                            </div>
                                        </div>
                                        </motion.div>
                                    </Link>
                                ))
                        )}
                    </div>
                )}
                {!loading && tenants.length > 0 && hasMore && (
                    <div className="mt-8 flex justify-center">
                        <button
                            onClick={() => loadTenants(true)}
                            disabled={loadingMore}
                            className="px-6 py-2 rounded-lg border border-border bg-muted/50 hover:bg-muted text-sm font-medium disabled:opacity-50"
                        >
                            {loadingMore ? "Laster..." : "Last flere"}
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
}
