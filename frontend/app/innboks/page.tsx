"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/hooks/useAuth";
import { fetchAPI } from "@/lib/api";
import {
    Mail,
    Send,
    Inbox,
    Trash2,
    RefreshCw,
    PenSquare,
    X,
    ChevronLeft,
    Reply,
    Clock,
    User,
    AlertCircle,
    CheckCheck,
} from "lucide-react";

interface Melding {
    id: string;
    avsender_email: string;
    avsender_navn: string;
    mottaker_email: string;
    mottaker_navn: string;
    emne: string;
    innhold: string;
    lest: boolean;
    svar_til_id: string | null;
    sendt_dato: string;
    lest_dato: string | null;
}

interface Bruker {
    email: string;
    navn: string;
}

type Visning = "innboks" | "utboks";

function formatDato(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffDager = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDager === 0) {
        return d.toLocaleTimeString("nb-NO", { hour: "2-digit", minute: "2-digit" });
    }
    if (diffDager === 1) return "I går";
    if (diffDager < 7) return `${diffDager} dager siden`;
    return d.toLocaleDateString("nb-NO", { day: "numeric", month: "short" });
}

export default function InnboksPage() {
    const { user } = useAuth();
    const [visning, setVisning] = useState<Visning>("innboks");
    const [meldinger, setMeldinger] = useState<Melding[]>([]);
    const [loading, setLoading] = useState(true);
    const [valgt, setValgt] = useState<Melding | null>(null);
    const [komponer, setKomponer] = useState(false);
    const [svarModus, setSvarModus] = useState(false);

    // Komponer-form
    const [brukere, setBrukere] = useState<Bruker[]>([]);
    const [mottaker, setMottaker] = useState("");
    const [emne, setEmne] = useState("");
    const [innhold, setInnhold] = useState("");
    const [sender, setSender] = useState(false);
    const [sendFeil, setSendFeil] = useState("");

    const hentMeldinger = useCallback(async () => {
        setLoading(true);
        try {
            const endpoint = visning === "innboks" ? "/meldinger/innboks" : "/meldinger/utboks";
            const data = await fetchAPI<Melding[]>(endpoint);
            setMeldinger(data || []);
        } catch {
            setMeldinger([]);
        } finally {
            setLoading(false);
        }
    }, [visning]);

    useEffect(() => {
        hentMeldinger();
        setValgt(null);
    }, [hentMeldinger]);

    useEffect(() => {
        fetchAPI<Bruker[]>("/meldinger/brukere")
            .then((b) => setBrukere(b || []))
            .catch(() => {});
    }, []);

    const apneMelding = async (m: Melding) => {
        setValgt(m);
        if (!m.lest && visning === "innboks") {
            try {
                await fetchAPI(`/meldinger/${m.id}/les`, { method: "PATCH" });
                setMeldinger((prev) =>
                    prev.map((x) => (x.id === m.id ? { ...x, lest: true } : x))
                );
            } catch {}
        }
    };

    const arkiver = async (id: string) => {
        try {
            await fetchAPI(`/meldinger/${id}`, { method: "DELETE" });
            setMeldinger((prev) => prev.filter((m) => m.id !== id));
            if (valgt?.id === id) setValgt(null);
        } catch {}
    };

    const startSvar = (m: Melding) => {
        setMottaker(m.avsender_email);
        setEmne(m.emne.startsWith("Re: ") ? m.emne : `Re: ${m.emne}`);
        setInnhold(`\n\n--- Opprinnelig melding fra ${m.avsender_navn} ---\n${m.innhold}`);
        setSvarModus(true);
        setKomponer(true);
    };

    const sendMelding = async () => {
        if (!mottaker || !emne || !innhold.trim()) {
            setSendFeil("Fyll ut alle felt");
            return;
        }
        setSender(true);
        setSendFeil("");
        try {
            await fetchAPI("/meldinger", {
                method: "POST",
                body: JSON.stringify({ mottaker_email: mottaker, emne, innhold }),
            });
            setKomponer(false);
            setSvarModus(false);
            setMottaker("");
            setEmne("");
            setInnhold("");
            if (visning === "utboks") hentMeldinger();
        } catch (e: unknown) {
            setSendFeil(e instanceof Error ? e.message : "Sending feilet");
        } finally {
            setSender(false);
        }
    };

    const uleste = meldinger.filter((m) => !m.lest && visning === "innboks").length;

    return (
        <div className="flex h-[calc(100vh-8rem)] bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            {/* Sidebar */}
            <div className="w-56 border-r border-gray-200 bg-gray-50 flex flex-col flex-shrink-0">
                <div className="p-4 border-b border-gray-200">
                    <button
                        onClick={() => {
                            setKomponer(true);
                            setSvarModus(false);
                            setMottaker("");
                            setEmne("");
                            setInnhold("");
                        }}
                        className="w-full flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
                    >
                        <PenSquare size={16} />
                        Ny melding
                    </button>
                </div>

                <nav className="p-2 flex-1">
                    <button
                        onClick={() => setVisning("innboks")}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors mb-1 ${
                            visning === "innboks"
                                ? "bg-white shadow-sm text-blue-700 font-medium"
                                : "text-gray-600 hover:bg-white hover:shadow-sm"
                        }`}
                    >
                        <Inbox size={16} />
                        <span className="flex-1 text-left">Innboks</span>
                        {uleste > 0 && (
                            <span className="bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                                {uleste}
                            </span>
                        )}
                    </button>
                    <button
                        onClick={() => setVisning("utboks")}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                            visning === "utboks"
                                ? "bg-white shadow-sm text-blue-700 font-medium"
                                : "text-gray-600 hover:bg-white hover:shadow-sm"
                        }`}
                    >
                        <Send size={16} />
                        <span className="flex-1 text-left">Utboks</span>
                    </button>
                </nav>

                <div className="p-3 border-t border-gray-200">
                    <button
                        onClick={hentMeldinger}
                        className="w-full flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 px-2 py-1.5 rounded hover:bg-gray-100 transition-colors"
                    >
                        <RefreshCw size={12} />
                        Oppdater
                    </button>
                </div>
            </div>

            {/* Meldingliste */}
            <div className="w-80 border-r border-gray-200 flex flex-col flex-shrink-0 bg-white">
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                    <h2 className="text-sm font-semibold text-gray-700 capitalize">
                        {visning === "innboks" ? "Innboks" : "Utboks"}
                        {meldinger.length > 0 && (
                            <span className="ml-2 text-gray-400 font-normal text-xs">
                                ({meldinger.length})
                            </span>
                        )}
                    </h2>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {loading ? (
                        <div className="flex items-center justify-center h-32 text-gray-400">
                            <RefreshCw size={16} className="animate-spin mr-2" />
                            Laster...
                        </div>
                    ) : meldinger.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
                            <Mail size={32} className="opacity-40" />
                            <p className="text-sm">
                                {visning === "innboks" ? "Ingen meldinger" : "Ingen sendte meldinger"}
                            </p>
                        </div>
                    ) : (
                        meldinger.map((m) => (
                            <button
                                key={m.id}
                                onClick={() => apneMelding(m)}
                                className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-blue-50 transition-colors ${
                                    valgt?.id === m.id ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
                                } ${!m.lest && visning === "innboks" ? "bg-blue-50/50" : ""}`}
                            >
                                <div className="flex items-start justify-between gap-2">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-1.5 mb-0.5">
                                            {!m.lest && visning === "innboks" && (
                                                <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                                            )}
                                            <p className={`text-sm truncate ${!m.lest && visning === "innboks" ? "font-semibold text-gray-900" : "text-gray-700 font-medium"}`}>
                                                {visning === "innboks" ? m.avsender_navn : m.mottaker_navn}
                                            </p>
                                        </div>
                                        <p className="text-xs text-gray-600 truncate mb-1">{m.emne}</p>
                                        <p className="text-xs text-gray-400 truncate">{m.innhold.substring(0, 60)}</p>
                                    </div>
                                    <span className="text-xs text-gray-400 flex-shrink-0 mt-0.5">
                                        {formatDato(m.sendt_dato)}
                                    </span>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Melding-visning / Komponer */}
            <div className="flex-1 flex flex-col min-w-0">
                {komponer ? (
                    <div className="flex flex-col h-full">
                        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
                            <h3 className="font-semibold text-gray-800">
                                {svarModus ? "Svar på melding" : "Ny melding"}
                            </h3>
                            <button
                                onClick={() => { setKomponer(false); setSvarModus(false); }}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="max-w-2xl space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1.5">Til</label>
                                    {svarModus ? (
                                        <p className="text-sm text-gray-800 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                                            {mottaker}
                                        </p>
                                    ) : (
                                        <select
                                            value={mottaker}
                                            onChange={(e) => setMottaker(e.target.value)}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                                        >
                                            <option value="">Velg mottaker...</option>
                                            {brukere.map((b) => (
                                                <option key={b.email} value={b.email}>
                                                    {b.navn} ({b.email})
                                                </option>
                                            ))}
                                        </select>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1.5">Emne</label>
                                    <input
                                        type="text"
                                        value={emne}
                                        onChange={(e) => setEmne(e.target.value)}
                                        placeholder="Emne for meldingen"
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-medium text-gray-600 mb-1.5">Melding</label>
                                    <textarea
                                        value={innhold}
                                        onChange={(e) => setInnhold(e.target.value)}
                                        placeholder="Skriv din melding her..."
                                        rows={10}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    />
                                </div>

                                {sendFeil && (
                                    <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 px-3 py-2 rounded-lg">
                                        <AlertCircle size={14} />
                                        {sendFeil}
                                    </div>
                                )}

                                <div className="flex gap-3">
                                    <button
                                        onClick={sendMelding}
                                        disabled={sender}
                                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
                                    >
                                        <Send size={14} />
                                        {sender ? "Sender..." : "Send melding"}
                                    </button>
                                    <button
                                        onClick={() => { setKomponer(false); setSvarModus(false); }}
                                        className="px-4 py-2.5 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                    >
                                        Avbryt
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : valgt ? (
                    <div className="flex flex-col h-full">
                        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                            <div className="flex items-center justify-between mb-2">
                                <button
                                    onClick={() => setValgt(null)}
                                    className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                                >
                                    <ChevronLeft size={16} />
                                    Tilbake
                                </button>
                                <div className="flex items-center gap-2">
                                    {visning === "innboks" && (
                                        <button
                                            onClick={() => startSvar(valgt)}
                                            className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                                        >
                                            <Reply size={14} />
                                            Svar
                                        </button>
                                    )}
                                    <button
                                        onClick={() => arkiver(valgt.id)}
                                        className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
                                    >
                                        <Trash2 size={14} />
                                        Slett
                                    </button>
                                </div>
                            </div>
                            <h2 className="text-base font-semibold text-gray-900">{valgt.emne}</h2>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="max-w-2xl">
                                <div className="flex items-start gap-4 mb-6 pb-6 border-b border-gray-100">
                                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                        <User size={18} className="text-blue-600" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <div>
                                                <span className="font-medium text-gray-900 text-sm">
                                                    {valgt.avsender_navn}
                                                </span>
                                                <span className="text-xs text-gray-400 ml-2">
                                                    &lt;{valgt.avsender_email}&gt;
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-1 text-xs text-gray-400">
                                                <Clock size={11} />
                                                {new Date(valgt.sendt_dato).toLocaleString("nb-NO", {
                                                    day: "numeric",
                                                    month: "long",
                                                    year: "numeric",
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            Til: <span className="text-gray-700">{valgt.mottaker_navn}</span>
                                            {valgt.lest && valgt.lest_dato && visning === "utboks" && (
                                                <span className="ml-3 flex items-center gap-1 inline-flex text-green-500">
                                                    <CheckCheck size={11} />
                                                    Lest {formatDato(valgt.lest_dato)}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                                    {valgt.innhold}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-3">
                        <Mail size={48} className="opacity-30" />
                        <p className="text-base">Velg en melding for å lese den</p>
                        <p className="text-sm opacity-70">eller klikk «Ny melding» for å sende</p>
                    </div>
                )}
            </div>
        </div>
    );
}
