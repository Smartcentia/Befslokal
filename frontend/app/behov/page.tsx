"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchAPI } from "@/lib/api/client";
import { useAuth } from "@/hooks/useAuth";
import {
    MessageSquarePlus,
    Plus,
    ChevronDown,
    ChevronUp,
    Clock,
    CheckCircle2,
    Loader2,
    Trash2,
    AlertTriangle,
    Settings2,
    ArrowUpCircle,
    MinusCircle,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface Behovsmelding {
    id: string;
    tittel: string;
    beskrivelse: string | null;
    kategori: string | null;
    prioritet: string | null;
    status: string;
    opprettet_av: string;
    eiendom_navn: string | null;
    admin_kommentar: string | null;
    opprettet_dato: string | null;
    oppdatert_dato: string | null;
}

const KATEGORIER = ["Eiendom", "Kontrakt", "HMS", "Økonomi", "Rapport", "Kart", "Annet"];
const PRIORITETER = ["Lav", "Medium", "Høy", "Kritisk"];
const STATUSER = ["Ny", "Under behandling", "Implementert", "Avvist"];

// ── Style helpers ──────────────────────────────────────────────────────────

function statusStyle(status: string): string {
    switch (status) {
        case "Ny": return "bg-blue-100 text-blue-700";
        case "Under behandling": return "bg-yellow-100 text-yellow-700";
        case "Implementert": return "bg-green-100 text-green-700";
        case "Avvist": return "bg-red-100 text-red-700";
        default: return "bg-muted text-muted-foreground";
    }
}

function prioritetStyle(p: string | null): string {
    switch (p) {
        case "Kritisk": return "bg-red-100 text-red-700";
        case "Høy": return "bg-orange-100 text-orange-700";
        case "Medium": return "bg-yellow-100 text-yellow-700";
        case "Lav": return "bg-green-100 text-green-700";
        default: return "bg-muted text-muted-foreground";
    }
}

function PrioritIcon({ p }: { p: string | null }) {
    if (p === "Kritisk") return <AlertTriangle size={13} className="text-red-500" />;
    if (p === "Høy") return <ArrowUpCircle size={13} className="text-orange-500" />;
    if (p === "Medium") return <MinusCircle size={13} className="text-yellow-500" />;
    return <MinusCircle size={13} className="text-green-500" />;
}

function formatDate(iso: string | null) {
    if (!iso) return "–";
    return new Date(iso).toLocaleString("nb-NO", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function BehovPage() {
    const { email, role } = useAuth();
    const isAdmin = role === "ADMIN" || email === "frankvevle@gmail.com" || email === "admin@befs.no";

    const [behov, setBehov] = useState<Behovsmelding[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [submitting, setSubmitting] = useState(false);

    // Form state
    const [form, setForm] = useState({
        tittel: "",
        beskrivelse: "",
        kategori: "Annet",
        prioritet: "Medium",
        eiendom_navn: "",
    });

    // Admin update state
    const [adminEdit, setAdminEdit] = useState<{ id: string; status: string; kommentar: string } | null>(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchAPI<Behovsmelding[]>("/behov");
            setBehov(data);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Kunne ikke laste behovsmeldinger");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.tittel.trim()) return;
        setSubmitting(true);
        try {
            await fetchAPI("/behov", {
                method: "POST",
                body: JSON.stringify({
                    tittel: form.tittel,
                    beskrivelse: form.beskrivelse || null,
                    kategori: form.kategori,
                    prioritet: form.prioritet,
                    eiendom_navn: form.eiendom_navn || null,
                }),
            });
            setForm({ tittel: "", beskrivelse: "", kategori: "Annet", prioritet: "Medium", eiendom_navn: "" });
            setShowForm(false);
            await load();
        } catch (e) {
            alert("Feil ved innsending: " + (e instanceof Error ? e.message : "ukjent"));
        } finally {
            setSubmitting(false);
        }
    };

    const handleAdminSave = async () => {
        if (!adminEdit) return;
        try {
            await fetchAPI(`/behov/${adminEdit.id}`, {
                method: "PATCH",
                body: JSON.stringify({
                    status: adminEdit.status,
                    admin_kommentar: adminEdit.kommentar || null,
                }),
            });
            setAdminEdit(null);
            await load();
        } catch (e) {
            alert("Feil: " + (e instanceof Error ? e.message : "ukjent"));
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Arkiver denne behovsmeldingen?")) return;
        try {
            await fetchAPI(`/behov/${id}`, { method: "DELETE" });
            await load();
        } catch (e) {
            alert("Feil: " + (e instanceof Error ? e.message : "ukjent"));
        }
    };

    const filtered = statusFilter === "all" ? behov : behov.filter(b => b.status === statusFilter);

    // Stats
    const nyCount = behov.filter(b => b.status === "Ny").length;
    const underCount = behov.filter(b => b.status === "Under behandling").length;
    const implCount = behov.filter(b => b.status === "Implementert").length;

    return (
        <div className="min-h-screen bg-background">
            <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">

                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                            <MessageSquarePlus size={20} className="text-primary-foreground" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">Behovsmeldinger</h1>
                            <p className="text-sm text-muted-foreground">
                                Meld inn ønsker og behov for nye funksjoner i BEFS
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
                    >
                        <Plus size={16} />
                        Ny behovsmelding
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3 mb-6">
                    <div className="bg-card border rounded-xl p-4 text-center">
                        <div className="text-2xl font-bold text-blue-600">{nyCount}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">Nye</div>
                    </div>
                    <div className="bg-card border rounded-xl p-4 text-center">
                        <div className="text-2xl font-bold text-yellow-600">{underCount}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">Under behandling</div>
                    </div>
                    <div className="bg-card border rounded-xl p-4 text-center">
                        <div className="text-2xl font-bold text-green-600">{implCount}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">Implementert</div>
                    </div>
                </div>

                {/* New Need Form */}
                {showForm && (
                    <div className="bg-card border rounded-xl p-5 mb-6 shadow-sm">
                        <h2 className="text-base font-semibold text-foreground mb-4">Meld inn nytt behov</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1">Tittel *</label>
                                <input
                                    type="text"
                                    required
                                    value={form.tittel}
                                    onChange={e => setForm(f => ({ ...f, tittel: e.target.value }))}
                                    placeholder="Kort beskrivelse av behovet"
                                    className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-muted-foreground mb-1">Detaljert beskrivelse</label>
                                <textarea
                                    value={form.beskrivelse}
                                    onChange={e => setForm(f => ({ ...f, beskrivelse: e.target.value }))}
                                    placeholder="Beskriv behovet mer utdypende – hva skal løses, og hvem gjelder det?"
                                    rows={3}
                                    className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                                />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1">Kategori</label>
                                    <select
                                        value={form.kategori}
                                        onChange={e => setForm(f => ({ ...f, kategori: e.target.value }))}
                                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                                    >
                                        {KATEGORIER.map(k => <option key={k} value={k}>{k}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1">Prioritet</label>
                                    <select
                                        value={form.prioritet}
                                        onChange={e => setForm(f => ({ ...f, prioritet: e.target.value }))}
                                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                                    >
                                        {PRIORITETER.map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1">Eiendom (valgfritt)</label>
                                    <input
                                        type="text"
                                        value={form.eiendom_navn}
                                        onChange={e => setForm(f => ({ ...f, eiendom_navn: e.target.value }))}
                                        placeholder="F.eks. Ranheim Vestre"
                                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                                    />
                                </div>
                            </div>
                            <div className="flex gap-2 pt-1">
                                <button
                                    type="submit"
                                    disabled={submitting || !form.tittel.trim()}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
                                >
                                    {submitting ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                                    Send inn
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                    className="px-4 py-2 border rounded-lg text-sm hover:bg-muted transition-colors"
                                >
                                    Avbryt
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Filter tabs */}
                <div className="flex gap-1 border-b mb-4">
                    {["all", ...STATUSER].map(s => (
                        <button
                            key={s}
                            onClick={() => setStatusFilter(s)}
                            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                                statusFilter === s
                                    ? "border-primary text-primary"
                                    : "border-transparent text-muted-foreground hover:text-foreground"
                            }`}
                        >
                            {s === "all" ? "Alle" : s}
                        </button>
                    ))}
                </div>

                {/* Content */}
                {loading ? (
                    <div className="flex items-center justify-center py-16 text-muted-foreground">
                        <Loader2 size={24} className="animate-spin mr-2" />
                        Laster…
                    </div>
                ) : error ? (
                    <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm">
                        <AlertTriangle size={16} />
                        {error}
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center py-16 text-muted-foreground">
                        <MessageSquarePlus size={40} className="mx-auto mb-3 opacity-30" />
                        <p className="text-sm">
                            {behov.length === 0
                                ? "Ingen behovsmeldinger ennå. Vær den første!"
                                : "Ingen meldinger med valgt status."}
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filtered.map(item => (
                            <div key={item.id} className="bg-card border rounded-xl overflow-hidden">
                                {/* Row */}
                                <div
                                    className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-muted/30 transition-colors"
                                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                                >
                                    <PrioritIcon p={item.prioritet} />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-semibold text-sm text-foreground truncate">
                                                {item.tittel}
                                            </span>
                                            {item.kategori && (
                                                <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                                                    {item.kategori}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                                            <span className="flex items-center gap-1">
                                                <Clock size={11} /> {formatDate(item.opprettet_dato)}
                                            </span>
                                            {isAdmin && <span>{item.opprettet_av}</span>}
                                            {item.eiendom_navn && <span>📍 {item.eiendom_navn}</span>}
                                        </div>
                                    </div>

                                    {/* Status badge */}
                                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${statusStyle(item.status)}`}>
                                        {item.status}
                                    </span>

                                    {/* Priority badge */}
                                    {item.prioritet && (
                                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 hidden sm:inline ${prioritetStyle(item.prioritet)}`}>
                                            {item.prioritet}
                                        </span>
                                    )}

                                    {/* Delete */}
                                    <button
                                        onClick={e => { e.stopPropagation(); handleDelete(item.id); }}
                                        className="p-1 hover:bg-red-50 hover:text-red-500 rounded transition-colors shrink-0 text-muted-foreground"
                                        title="Arkiver"
                                    >
                                        <Trash2 size={14} />
                                    </button>

                                    {expandedId === item.id ? <ChevronUp size={16} className="text-muted-foreground shrink-0" /> : <ChevronDown size={16} className="text-muted-foreground shrink-0" />}
                                </div>

                                {/* Expanded */}
                                {expandedId === item.id && (
                                    <div className="px-4 pb-4 pt-2 border-t">
                                        {item.beskrivelse && (
                                            <p className="text-sm text-foreground mb-3 whitespace-pre-wrap">{item.beskrivelse}</p>
                                        )}

                                        {item.admin_kommentar && (
                                            <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-3">
                                                <div className="text-xs font-semibold text-blue-700 mb-0.5 flex items-center gap-1">
                                                    <Settings2 size={11} /> Admin-kommentar
                                                </div>
                                                <p className="text-sm text-blue-800">{item.admin_kommentar}</p>
                                            </div>
                                        )}

                                        {item.status === "Implementert" && (
                                            <div className="flex items-center gap-1.5 text-xs text-green-700 mb-3">
                                                <CheckCircle2 size={14} />
                                                Implementert {formatDate(item.oppdatert_dato)}
                                            </div>
                                        )}

                                        {/* Admin controls */}
                                        {isAdmin && (
                                            adminEdit?.id === item.id ? (
                                                <div className="space-y-2 mt-2">
                                                    <select
                                                        value={adminEdit.status}
                                                        onChange={e => setAdminEdit(a => a ? { ...a, status: e.target.value } : a)}
                                                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background"
                                                    >
                                                        {STATUSER.map(s => <option key={s} value={s}>{s}</option>)}
                                                    </select>
                                                    <textarea
                                                        value={adminEdit.kommentar}
                                                        onChange={e => setAdminEdit(a => a ? { ...a, kommentar: e.target.value } : a)}
                                                        placeholder="Admin-kommentar (valgfritt)"
                                                        rows={2}
                                                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background resize-none"
                                                    />
                                                    <div className="flex gap-2">
                                                        <button onClick={handleAdminSave} className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium">
                                                            Lagre
                                                        </button>
                                                        <button onClick={() => setAdminEdit(null)} className="px-3 py-1.5 border rounded-lg text-xs">
                                                            Avbryt
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => setAdminEdit({ id: item.id, status: item.status, kommentar: item.admin_kommentar || "" })}
                                                    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary transition-colors mt-1"
                                                >
                                                    <Settings2 size={13} /> Oppdater status
                                                </button>
                                            )
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}
