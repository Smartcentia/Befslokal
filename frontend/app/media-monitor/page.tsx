"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/app/components/ui/Header";
import { fetchAPI } from "@/lib/api/client";
import { useAuth } from "@/hooks/useAuth";
import {
    Newspaper,
    RefreshCw,
    AlertTriangle,
    CheckCircle,
    TrendingDown,
    TrendingUp,
    Minus,
    ChevronDown,
    ChevronUp,
    ExternalLink,
    Clock,
    Building2,
    PlayCircle,
    Activity,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface TenantSentiment {
    party_id: string;
    name: string;
    orgnr: string | null;
    active_contracts: number;
    sentiment_score: number;
    sentiment_label: "Negativt" | "Nøytralt" | "Positivt";
    summary: string;
    red_flags: string[];
    positive_news: string[];
    sources_checked: number;
    last_updated: string | null;
}

interface RunAllResult {
    status: string;
    total?: number;
    updated?: number;
    errors?: number;
    message?: string;
}

interface MonitorStatus {
    job_running: boolean;
    last_run_started?: string;
    total_monitored?: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function scoreColor(score: number): string {
    if (score <= 3) return "text-red-600";
    if (score <= 5) return "text-orange-500";
    if (score <= 7) return "text-yellow-500";
    return "text-green-600";
}

function scoreBg(score: number): string {
    if (score <= 3) return "bg-red-50 border-red-200";
    if (score <= 5) return "bg-orange-50 border-orange-200";
    if (score <= 7) return "bg-yellow-50 border-yellow-200";
    return "bg-green-50 border-green-200";
}

function scoreBadgeBg(score: number): string {
    if (score <= 3) return "bg-red-100 text-red-700";
    if (score <= 5) return "bg-orange-100 text-orange-700";
    if (score <= 7) return "bg-yellow-100 text-yellow-700";
    return "bg-green-100 text-green-700";
}

function SentimentIcon({ score }: { score: number }) {
    if (score <= 3) return <TrendingDown size={16} className="text-red-500" />;
    if (score <= 5) return <Minus size={16} className="text-orange-500" />;
    return <TrendingUp size={16} className="text-green-500" />;
}

function ScoreBar({ score }: { score: number }) {
    const pct = ((score - 1) / 9) * 100;
    const barColor =
        score <= 3 ? "bg-red-500" :
        score <= 5 ? "bg-orange-400" :
        score <= 7 ? "bg-yellow-400" :
        "bg-green-500";
    return (
        <div className="flex items-center gap-2 w-full">
            <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className={`text-xs font-bold w-6 text-right ${scoreColor(score)}`}>
                {score.toFixed(1)}
            </span>
        </div>
    );
}

function formatDate(iso: string | null): string {
    if (!iso) return "Aldri";
    const d = new Date(iso);
    return d.toLocaleString("nb-NO", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}

// ── Row Component ──────────────────────────────────────────────────────────

function TenantRow({ item, rank, onRefresh }: {
    item: TenantSentiment;
    rank: number;
    onRefresh: (partyId: string) => Promise<void>;
}) {
    const [expanded, setExpanded] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    const handleRefresh = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setRefreshing(true);
        await onRefresh(item.party_id);
        setRefreshing(false);
    };

    return (
        <div className={`border rounded-xl mb-3 transition-all duration-200 ${scoreBg(item.sentiment_score)}`}>
            {/* Main row */}
            <div
                className="flex items-center gap-3 px-4 py-3 cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                {/* Rank */}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${scoreBadgeBg(item.sentiment_score)}`}>
                    {rank}
                </div>

                {/* Icon */}
                <SentimentIcon score={item.sentiment_score} />

                {/* Name + orgnr */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground truncate">
                            {item.name}
                        </span>
                        {item.orgnr && (
                            <span className="text-xs text-muted-foreground hidden sm:inline">
                                {item.orgnr}
                            </span>
                        )}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-0.5">
                        {item.summary || "Ingen oppsummering"}
                    </div>
                </div>

                {/* Score bar */}
                <div className="w-32 hidden md:block">
                    <ScoreBar score={item.sentiment_score} />
                </div>

                {/* Label badge */}
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${scoreBadgeBg(item.sentiment_score)}`}>
                    {item.sentiment_label}
                </span>

                {/* Active contracts */}
                <div className="text-xs text-muted-foreground shrink-0 hidden lg:flex items-center gap-1">
                    <Building2 size={12} />
                    {item.active_contracts}
                </div>

                {/* Refresh */}
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    title="Oppdater nå"
                    className="p-1 hover:bg-white/60 rounded-lg transition-colors shrink-0"
                >
                    <RefreshCw size={14} className={`text-muted-foreground ${refreshing ? "animate-spin" : ""}`} />
                </button>

                {/* Expand */}
                <div className="shrink-0 text-muted-foreground">
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
            </div>

            {/* Expanded details */}
            {expanded && (
                <div className="px-4 pb-4 pt-0 border-t border-current/10 mt-1">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
                        {/* Red flags */}
                        {item.red_flags.length > 0 && (
                            <div>
                                <div className="flex items-center gap-1.5 mb-2">
                                    <AlertTriangle size={14} className="text-red-500" />
                                    <span className="text-xs font-semibold text-red-700 uppercase tracking-wide">
                                        Røde flagg ({item.red_flags.length})
                                    </span>
                                </div>
                                <ul className="space-y-1">
                                    {item.red_flags.map((flag, i) => (
                                        <li key={i} className="flex items-start gap-1.5 text-xs text-red-800">
                                            <span className="mt-0.5 shrink-0">•</span>
                                            {flag}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Positive news */}
                        {item.positive_news.length > 0 && (
                            <div>
                                <div className="flex items-center gap-1.5 mb-2">
                                    <CheckCircle size={14} className="text-green-500" />
                                    <span className="text-xs font-semibold text-green-700 uppercase tracking-wide">
                                        Positivt ({item.positive_news.length})
                                    </span>
                                </div>
                                <ul className="space-y-1">
                                    {item.positive_news.map((n, i) => (
                                        <li key={i} className="flex items-start gap-1.5 text-xs text-green-800">
                                            <span className="mt-0.5 shrink-0">•</span>
                                            {n}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* No flags or news */}
                        {item.red_flags.length === 0 && item.positive_news.length === 0 && (
                            <div className="text-xs text-muted-foreground col-span-2">
                                Ingen spesifikke funn registrert.
                            </div>
                        )}
                    </div>

                    {/* Footer meta */}
                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-current/10">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                                <Clock size={11} />
                                {formatDate(item.last_updated)}
                            </span>
                            <span>{item.sources_checked} kilder sjekket</span>
                        </div>
                        <Link
                            href={`/parties/${item.party_id}`}
                            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                            onClick={(e) => e.stopPropagation()}
                        >
                            Se leietaker
                            <ExternalLink size={11} />
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Main Page ──────────────────────────────────────────────────────────────

interface AuthUser {
    email?: string | null;
    roles?: string[];
    role?: string;
    isAdmin?: boolean;
}

export default function MediaMonitorPage() {
    const { user: authUser } = useAuth();
    const router = useRouter();
    const user = authUser as AuthUser | undefined;

    // Admin-only page
    const isAdmin =
        user?.email === "admin@befs.no" ||
        user?.email === "frankvevle@gmail.com" ||
        user?.roles?.includes("ADMIN") ||
        user?.role === "ADMIN" ||
        user?.isAdmin === true;

    const [ranking, setRanking] = useState<TenantSentiment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [runAllLoading, setRunAllLoading] = useState(false);
    const [runAllResult, setRunAllResult] = useState<RunAllResult | null>(null);
    const [status, setStatus] = useState<MonitorStatus | null>(null);
    const [filter, setFilter] = useState<"all" | "negative" | "positive">("all");
    const [searchQuery, setSearchQuery] = useState("");

    // Redirect non-admins
    useEffect(() => {
        if (authUser !== undefined && !isAdmin) {
            router.replace("/dashboard");
        }
    }, [authUser, isAdmin, router]);

    const loadRanking = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchAPI<TenantSentiment[]>("/media-monitor/ranking");
            setRanking(data);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Kunne ikke laste data");
        } finally {
            setLoading(false);
        }
    }, []);

    const loadStatus = useCallback(async () => {
        try {
            const s = await fetchAPI<MonitorStatus>("/media-monitor/status");
            setStatus(s);
        } catch {
            // ignore
        }
    }, []);

    useEffect(() => {
        loadRanking();
        loadStatus();
    }, [loadRanking, loadStatus]);

    const handleRunAll = async () => {
        setRunAllLoading(true);
        setRunAllResult(null);
        try {
            const result = await fetchAPI<RunAllResult>("/media-monitor/run-all", {
                method: "POST",
            });
            setRunAllResult(result);
            // Refresh ranking after a short delay
            setTimeout(loadRanking, 3000);
        } catch (e) {
            setRunAllResult({
                status: "error",
                message: e instanceof Error ? e.message : "Ukjent feil",
            });
        } finally {
            setRunAllLoading(false);
        }
    };

    const handleRefreshOne = async (partyId: string) => {
        try {
            await fetchAPI(`/media-monitor/run/${partyId}`, { method: "POST" });
            await loadRanking();
        } catch (e) {
            console.error("Refresh failed", e);
        }
    };

    // Filter + search
    const filtered = ranking.filter((item) => {
        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            if (!item.name.toLowerCase().includes(q) && !(item.orgnr || "").includes(q)) {
                return false;
            }
        }
        if (filter === "negative") return item.sentiment_score <= 4;
        if (filter === "positive") return item.sentiment_score >= 7;
        return true;
    });

    // Summary stats
    const negCount = ranking.filter(r => r.sentiment_score <= 4).length;
    const posCount = ranking.filter(r => r.sentiment_score >= 7).length;
    const neutralCount = ranking.length - negCount - posCount;
    const avgScore = ranking.length
        ? (ranking.reduce((s, r) => s + r.sentiment_score, 0) / ranking.length).toFixed(1)
        : "–";

    return (
        <div className="flex flex-col min-h-screen bg-background">
            <Header />
            <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-5xl mx-auto w-full">

                {/* Page header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                            <Newspaper size={20} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">Media Overvåkning</h1>
                            <p className="text-sm text-muted-foreground">
                                Sentimentanalyse av leietakere – oppdatert nattlig kl. 02:30
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={loadRanking}
                            disabled={loading}
                            className="flex items-center gap-1.5 px-3 py-2 text-sm border rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
                        >
                            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                            Oppdater
                        </button>
                        <button
                            onClick={handleRunAll}
                            disabled={runAllLoading || status?.job_running}
                            className="flex items-center gap-1.5 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                        >
                            {runAllLoading ? (
                                <RefreshCw size={14} className="animate-spin" />
                            ) : (
                                <PlayCircle size={14} />
                            )}
                            Kjør nå
                        </button>
                    </div>
                </div>

                {/* Status banner */}
                {status?.job_running && (
                    <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 text-blue-800 text-sm px-4 py-2.5 rounded-xl mb-4">
                        <Activity size={16} className="animate-pulse" />
                        Overvåkningsjobb kjører nå i bakgrunnen…
                    </div>
                )}

                {/* Run all result */}
                {runAllResult && (
                    <div className={`flex items-start gap-2 text-sm px-4 py-3 rounded-xl mb-4 border ${
                        runAllResult.status === "ok" || runAllResult.status === "started"
                            ? "bg-green-50 border-green-200 text-green-800"
                            : runAllResult.status === "already_running"
                            ? "bg-yellow-50 border-yellow-200 text-yellow-800"
                            : "bg-red-50 border-red-200 text-red-800"
                    }`}>
                        {runAllResult.status === "ok" || runAllResult.status === "started" ? (
                            <>
                                <CheckCircle size={16} className="mt-0.5 shrink-0" />
                                <span>
                                    {runAllResult.status === "started"
                                        ? "Analyse startet i bakgrunnen. Rangeringen oppdateres om et par minutter."
                                        : `Kjørt: ${runAllResult.total} leietakere analysert – ${runAllResult.updated} oppdatert, ${runAllResult.errors} feil.`
                                    }
                                </span>
                            </>
                        ) : runAllResult.status === "already_running" ? (
                            <>
                                <Activity size={16} className="mt-0.5 shrink-0" />
                                <span>En jobb kjører allerede. Prøv igjen om litt.</span>
                            </>
                        ) : (
                            <>
                                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                                <span>{runAllResult.message || "Feil under kjøring."}</span>
                            </>
                        )}
                    </div>
                )}

                {/* Summary cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                    <div className="bg-card border rounded-xl p-4">
                        <div className="text-2xl font-bold text-foreground">{ranking.length}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">Leietakere analysert</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                        <div className="text-2xl font-bold text-red-600">{negCount}</div>
                        <div className="text-xs text-red-700 mt-0.5">Negative (≤ 4)</div>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                        <div className="text-2xl font-bold text-yellow-600">{neutralCount}</div>
                        <div className="text-xs text-yellow-700 mt-0.5">Nøytrale (5–6)</div>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                        <div className="text-2xl font-bold text-green-600">{posCount}</div>
                        <div className="text-xs text-green-700 mt-0.5">Positive (≥ 7)</div>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-3 mb-4">
                    <input
                        type="text"
                        placeholder="Søk leietaker eller orgnr…"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex border rounded-lg overflow-hidden text-sm shrink-0">
                        {(["all", "negative", "positive"] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-3 py-2 transition-colors ${
                                    filter === f
                                        ? "bg-blue-600 text-white"
                                        : "bg-background hover:bg-muted text-foreground"
                                }`}
                            >
                                {f === "all" ? "Alle" : f === "negative" ? "🔴 Negative" : "🟢 Positive"}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Score average */}
                {ranking.length > 0 && (
                    <div className="text-xs text-muted-foreground mb-4">
                        Viser {filtered.length} av {ranking.length} leietakere · Gjennomsnittlig score: {avgScore} / 10
                    </div>
                )}

                {/* Content */}
                {loading ? (
                    <div className="space-y-3">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="h-16 bg-muted animate-pulse rounded-xl" />
                        ))}
                    </div>
                ) : error ? (
                    <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm">
                        <AlertTriangle size={16} />
                        {error}
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center py-16 text-muted-foreground">
                        <Newspaper size={40} className="mx-auto mb-3 opacity-30" />
                        <p className="text-sm">
                            {ranking.length === 0
                                ? 'Ingen data ennå. Trykk "Kjør nå" for å starte analyse.'
                                : "Ingen leietakere matcher søket."}
                        </p>
                    </div>
                ) : (
                    <div>
                        {filtered.map((item, idx) => (
                            <TenantRow
                                key={item.party_id}
                                item={item}
                                rank={idx + 1}
                                onRefresh={handleRefreshOne}
                            />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
