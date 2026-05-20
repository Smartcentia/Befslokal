"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    Plus, Check, MessageSquare, ChevronUp, ChevronDown,
    Trash2, Clock, CheckCircle2, Circle, X, Save,
    Download, RotateCcw, GripVertical
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AgendaPunkt {
    id: string;
    tekst: string;
    varighet?: number;          // minutter
    ferdig: boolean;
    kommentar: string;
    visKommentar: boolean;
}

function uid() {
    return Math.random().toString(36).slice(2, 10);
}

const STORAGE_KEY = "knowme_agenda_v1";

function lagre(punkter: AgendaPunkt[], tittel: string) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ punkter, tittel }));
}

function last(): { punkter: AgendaPunkt[]; tittel: string } {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) return JSON.parse(raw);
    } catch {}
    return { punkter: [], tittel: "Møteagenda" };
}

// ── Komponent ─────────────────────────────────────────────────────────────────

export default function AgendaPage() {
    const [tittel, setTittel] = useState("Møteagenda");
    const [redigerTittel, setRedigerTittel] = useState(false);
    const [tittelInput, setTittelInput] = useState("Møteagenda");
    const [punkter, setPunkter] = useState<AgendaPunkt[]>([]);
    const [nyttPunkt, setNyttPunkt] = useState("");
    const [nyVarighet, setNyVarighet] = useState("");
    const [lagret, setLagret] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // Last fra localStorage ved oppstart
    useEffect(() => {
        const data = last();
        setPunkter(data.punkter);
        setTittel(data.tittel);
        setTittelInput(data.tittel);
    }, []);

    // Autosave ved endringer
    useEffect(() => {
        lagre(punkter, tittel);
        setLagret(true);
        const t = setTimeout(() => setLagret(false), 1500);
        return () => clearTimeout(t);
    }, [punkter, tittel]);

    const leggTil = () => {
        const txt = nyttPunkt.trim();
        if (!txt) return;
        const varighet = parseInt(nyVarighet) || undefined;
        setPunkter(p => [...p, {
            id: uid(),
            tekst: txt,
            varighet,
            ferdig: false,
            kommentar: "",
            visKommentar: false,
        }]);
        setNyttPunkt("");
        setNyVarighet("");
        inputRef.current?.focus();
    };

    const toggle = (id: string) =>
        setPunkter(p => p.map(x => x.id === id ? { ...x, ferdig: !x.ferdig } : x));

    const oppdaterKommentar = (id: string, kommentar: string) =>
        setPunkter(p => p.map(x => x.id === id ? { ...x, kommentar } : x));

    const toggleKommentar = (id: string) =>
        setPunkter(p => p.map(x => x.id === id ? { ...x, visKommentar: !x.visKommentar } : x));

    const slett = (id: string) =>
        setPunkter(p => p.filter(x => x.id !== id));

    const flytt = (id: string, retning: -1 | 1) => {
        setPunkter(prev => {
            const idx = prev.findIndex(x => x.id === id);
            if (idx < 0) return prev;
            const ny = [...prev];
            const target = idx + retning;
            if (target < 0 || target >= ny.length) return prev;
            [ny[idx], ny[target]] = [ny[target], ny[idx]];
            return ny;
        });
    };

    const nullstill = () => {
        if (!confirm("Nullstill hele agendaen?")) return;
        setPunkter([]);
        setTittel("Møteagenda");
        localStorage.removeItem(STORAGE_KEY);
    };

    const eksporter = () => {
        const linjer = [
            tittel,
            "=".repeat(tittel.length),
            "",
            ...punkter.map((p, i) => {
                const status = p.ferdig ? "✅" : "⬜";
                const tid = p.varighet ? ` (${p.varighet} min)` : "";
                const kommentar = p.kommentar ? `\n   💬 ${p.kommentar}` : "";
                return `${status} ${i + 1}. ${p.tekst}${tid}${kommentar}`;
            }),
        ];
        const blob = new Blob([linjer.join("\n")], { type: "text/plain" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${tittel.toLowerCase().replace(/\s+/g, "-")}.txt`;
        a.click();
    };

    const ferdig = punkter.filter(p => p.ferdig).length;
    const total = punkter.length;
    const totalMin = punkter.reduce((sum, p) => sum + (p.varighet || 0), 0);
    const progress = total > 0 ? Math.round((ferdig / total) * 100) : 0;

    return (
        <div className="text-foreground max-w-2xl mx-auto">

            {/* Tittel */}
            <div className="mb-6">
                {redigerTittel ? (
                    <div className="flex items-center gap-2">
                        <input
                            autoFocus
                            value={tittelInput}
                            onChange={e => setTittelInput(e.target.value)}
                            onKeyDown={e => {
                                if (e.key === "Enter") { setTittel(tittelInput); setRedigerTittel(false); }
                                if (e.key === "Escape") setRedigerTittel(false);
                            }}
                            className="text-2xl font-bold bg-transparent border-b-2 border-primary outline-none text-foreground w-full"
                        />
                        <button onClick={() => { setTittel(tittelInput); setRedigerTittel(false); }}
                            className="p-1.5 bg-primary text-primary-foreground rounded-lg">
                            <Check size={16} />
                        </button>
                    </div>
                ) : (
                    <div className="flex items-center justify-between">
                        <h1
                            className="text-2xl font-bold tracking-tight text-foreground cursor-pointer hover:text-primary transition-colors"
                            onClick={() => { setTittelInput(tittel); setRedigerTittel(true); }}
                            title="Klikk for å redigere"
                        >
                            {tittel}
                        </h1>
                        <div className="flex items-center gap-2">
                            {lagret && (
                                <span className="text-xs text-green-500 flex items-center gap-1 animate-fade">
                                    <Check size={11} /> Lagret
                                </span>
                            )}
                            <button onClick={eksporter} title="Eksporter som tekst"
                                className="p-2 rounded-lg border border-border hover:bg-border/40 text-muted-foreground transition-colors">
                                <Download size={15} />
                            </button>
                            <button onClick={nullstill} title="Nullstill agenda"
                                className="p-2 rounded-lg border border-border hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/20 text-muted-foreground transition-colors">
                                <RotateCcw size={15} />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Fremdrift */}
            {total > 0 && (
                <div className="bg-surface border border-border rounded-xl p-4 mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-foreground">
                            {ferdig} av {total} fullført
                        </span>
                        <div className="flex items-center gap-3">
                            {totalMin > 0 && (
                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                    <Clock size={12} /> {totalMin} min totalt
                                </span>
                            )}
                            <span className="text-sm font-bold text-primary">{progress}%</span>
                        </div>
                    </div>
                    <div className="w-full bg-border/40 rounded-full h-2.5 overflow-hidden">
                        <div
                            className="h-full bg-primary rounded-full transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Agendapunkter */}
            {punkter.length > 0 && (
                <div className="space-y-2 mb-6">
                    {punkter.map((p, i) => (
                        <div key={p.id}
                            className={`border rounded-xl transition-all ${p.ferdig
                                ? "bg-green-500/5 border-green-500/20"
                                : "bg-surface border-border"
                            }`}
                        >
                            {/* Hoved-rad */}
                            <div className="flex items-center gap-3 px-4 py-3">
                                {/* Rekkefølge-knapper */}
                                <div className="flex flex-col gap-0.5 opacity-30 hover:opacity-100 transition-opacity">
                                    <button onClick={() => flytt(p.id, -1)} disabled={i === 0}
                                        className="hover:text-primary disabled:opacity-20 transition-colors">
                                        <ChevronUp size={14} />
                                    </button>
                                    <button onClick={() => flytt(p.id, 1)} disabled={i === punkter.length - 1}
                                        className="hover:text-primary disabled:opacity-20 transition-colors">
                                        <ChevronDown size={14} />
                                    </button>
                                </div>

                                {/* Nummер */}
                                <span className="text-xs text-muted-foreground/50 w-5 text-right flex-shrink-0 font-mono">
                                    {i + 1}.
                                </span>

                                {/* Avkrysning */}
                                <button onClick={() => toggle(p.id)} className="flex-shrink-0">
                                    {p.ferdig
                                        ? <CheckCircle2 size={22} className="text-green-500" />
                                        : <Circle size={22} className="text-border hover:text-primary transition-colors" />
                                    }
                                </button>

                                {/* Tekst */}
                                <span className={`flex-1 text-sm font-medium ${p.ferdig ? "line-through text-muted-foreground" : "text-foreground"}`}>
                                    {p.tekst}
                                </span>

                                {/* Varighet */}
                                {p.varighet && (
                                    <span className="text-xs text-muted-foreground flex items-center gap-1 flex-shrink-0">
                                        <Clock size={11} /> {p.varighet} min
                                    </span>
                                )}

                                {/* Handlinger */}
                                <div className="flex items-center gap-1 flex-shrink-0">
                                    <button onClick={() => toggleKommentar(p.id)}
                                        title="Legg til kommentar"
                                        className={`p-1.5 rounded-lg transition-colors ${p.kommentar || p.visKommentar
                                            ? "text-primary bg-primary/10"
                                            : "text-muted-foreground/40 hover:text-muted-foreground hover:bg-border/40"
                                        }`}>
                                        <MessageSquare size={14} />
                                    </button>
                                    <button onClick={() => slett(p.id)}
                                        className="p-1.5 rounded-lg text-muted-foreground/40 hover:text-red-500 hover:bg-red-500/10 transition-colors">
                                        <Trash2 size={14} />
                                    </button>
                                </div>
                            </div>

                            {/* Kommentarfelt */}
                            {(p.visKommentar || p.kommentar) && (
                                <div className="px-4 pb-3 pt-0">
                                    <div className="ml-[72px] relative">
                                        <MessageSquare size={12} className="absolute left-3 top-2.5 text-muted-foreground/40" />
                                        <textarea
                                            value={p.kommentar}
                                            onChange={e => oppdaterKommentar(p.id, e.target.value)}
                                            placeholder="Skriv kommentar, notat eller beslutning her…"
                                            rows={2}
                                            className="w-full pl-8 pr-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Tomt state */}
            {punkter.length === 0 && (
                <div className="text-center py-16 text-muted-foreground">
                    <div className="text-4xl mb-3 opacity-20">📋</div>
                    <div className="text-sm">Ingen agendapunkter ennå</div>
                    <div className="text-xs mt-1 opacity-60">Legg til det første punktet nedenfor</div>
                </div>
            )}

            {/* Legg til nytt punkt */}
            <div className="bg-surface border border-border rounded-xl p-4 sticky bottom-6 shadow-lg">
                <div className="flex gap-2">
                    <input
                        ref={inputRef}
                        value={nyttPunkt}
                        onChange={e => setNyttPunkt(e.target.value)}
                        onKeyDown={e => { if (e.key === "Enter") leggTil(); }}
                        placeholder="Nytt agendapunkt…"
                        className="flex-1 px-3 py-2.5 border border-border rounded-lg text-sm text-foreground bg-background focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground"
                    />
                    <input
                        value={nyVarighet}
                        onChange={e => setNyVarighet(e.target.value)}
                        onKeyDown={e => { if (e.key === "Enter") leggTil(); }}
                        placeholder="min"
                        type="number"
                        min="1"
                        className="w-16 px-3 py-2.5 border border-border rounded-lg text-sm text-foreground bg-background focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground text-center"
                    />
                    <button
                        onClick={leggTil}
                        disabled={!nyttPunkt.trim()}
                        className="px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
                    >
                        <Plus size={17} /> Legg til
                    </button>
                </div>
                <p className="text-xs text-muted-foreground/50 mt-2 ml-1">
                    Enter for å legge til • Klikk sirkel for å krysse av • Boble-ikon for kommentar
                </p>
            </div>
        </div>
    );
}
