"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api/client";
import { MapPin, Plus, Pencil, Trash2, ChevronDown, ChevronRight, Check, X, Users } from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

interface EiendomSummary {
    property_id: string;
    name: string | null;
    address: string | null;
    region: string | null;
}

interface Lokasjon {
    lokasjon_id: string;
    navn: string;
    adresse: string | null;
    lokalisering_id: string | null;
    region: string | null;
    merknad: string | null;
    antall_eiendommer: number;
    eiendommer: EiendomSummary[];
}

// ── API helpers ───────────────────────────────────────────────────────────────

const api = {
    list: () => fetchAPI("/lokasjoner"),
    create: (body: object) => fetchAPI("/lokasjoner", { method: "POST", body: JSON.stringify(body) }),
    update: (id: string, body: object) => fetchAPI(`/lokasjoner/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => fetchAPI(`/lokasjoner/${id}`, { method: "DELETE" }),
    assign: (id: string, ids: string[]) =>
        fetchAPI(`/lokasjoner/${id}/eiendommer`, { method: "POST", body: JSON.stringify(ids) }),
    unassigned: () => fetchAPI("/lokasjoner/unassigned"),
};

// ── Edit form ─────────────────────────────────────────────────────────────────

interface FormState { navn: string; adresse: string; lokalisering_id: string; region: string; merknad: string }
const emptyForm: FormState = { navn: "", adresse: "", lokalisering_id: "", region: "", merknad: "" };

function LokasjonForm({
    initial,
    onSave,
    onCancel,
}: {
    initial?: Partial<FormState>;
    onSave: (f: FormState) => Promise<void>;
    onCancel: () => void;
}) {
    const [f, setF] = useState<FormState>({ ...emptyForm, ...initial });
    const [saving, setSaving] = useState(false);

    const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setF(prev => ({ ...prev, [k]: e.target.value }));

    const handleSubmit = async (ev: React.FormEvent) => {
        ev.preventDefault();
        setSaving(true);
        try { await onSave(f); } finally { setSaving(false); }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-3 p-4 bg-muted/30 rounded-lg border">
            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="text-xs text-muted-foreground">Navn *</label>
                    <input required value={f.navn} onChange={set("navn")}
                        className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background" />
                </div>
                <div>
                    <label className="text-xs text-muted-foreground">Lydia-ID (lokalisering_id)</label>
                    <input value={f.lokalisering_id} onChange={set("lokalisering_id")}
                        className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background" />
                </div>
                <div>
                    <label className="text-xs text-muted-foreground">Adresse</label>
                    <input value={f.adresse} onChange={set("adresse")}
                        className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background" />
                </div>
                <div>
                    <label className="text-xs text-muted-foreground">Region</label>
                    <input value={f.region} onChange={set("region")}
                        className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background" />
                </div>
                <div className="col-span-2">
                    <label className="text-xs text-muted-foreground">Merknad</label>
                    <input value={f.merknad} onChange={set("merknad")}
                        className="w-full mt-1 px-3 py-1.5 text-sm border rounded-lg bg-background" />
                </div>
            </div>
            <div className="flex gap-2 justify-end">
                <button type="button" onClick={onCancel}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-muted/50">
                    <X size={13} /> Avbryt
                </button>
                <button type="submit" disabled={saving}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50">
                    <Check size={13} /> {saving ? "Lagrer…" : "Lagre"}
                </button>
            </div>
        </form>
    );
}

// ── Assign panel ──────────────────────────────────────────────────────────────

function AssignPanel({
    lokasjon,
    allUnassigned,
    onDone,
}: {
    lokasjon: Lokasjon;
    allUnassigned: EiendomSummary[];
    onDone: (lok: Lokasjon) => void;
}) {
    const [selected, setSelected] = useState<Set<string>>(
        new Set(lokasjon.eiendommer.map(e => e.property_id))
    );
    const [saving, setSaving] = useState(false);
    const [search, setSearch] = useState("");

    // Pool = current eiendommer + unassigned
    const pool: EiendomSummary[] = [
        ...lokasjon.eiendommer,
        ...allUnassigned.filter(u => !lokasjon.eiendommer.some(e => e.property_id === u.property_id)),
    ];
    const filtered = pool.filter(e =>
        !search || (e.name ?? "").toLowerCase().includes(search.toLowerCase()) ||
        (e.address ?? "").toLowerCase().includes(search.toLowerCase())
    );

    const toggle = (id: string) => setSelected(prev => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id); else next.add(id);
        return next;
    });

    const save = async () => {
        setSaving(true);
        try {
            const updated = await api.assign(lokasjon.lokasjon_id, Array.from(selected));
            onDone(updated);
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="mt-2 p-3 bg-muted/20 rounded-lg border space-y-2">
            <p className="text-xs text-muted-foreground font-medium">Velg avdelinger som tilhører denne lokasjonen:</p>
            <input
                placeholder="Søk navn / adresse…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full px-3 py-1.5 text-sm border rounded-lg bg-background"
            />
            <div className="max-h-48 overflow-y-auto space-y-1">
                {filtered.map(e => (
                    <label key={e.property_id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/30 px-2 py-1 rounded">
                        <input type="checkbox" checked={selected.has(e.property_id)} onChange={() => toggle(e.property_id)} />
                        <span className="flex-1 truncate">{e.name ?? e.address ?? e.property_id}</span>
                        {e.address && <span className="text-xs text-muted-foreground truncate max-w-32">{e.address}</span>}
                    </label>
                ))}
                {filtered.length === 0 && <p className="text-xs text-muted-foreground px-2">Ingen treff</p>}
            </div>
            <div className="flex justify-end">
                <button onClick={save} disabled={saving}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50">
                    <Check size={13} /> {saving ? "Lagrer…" : `Lagre (${selected.size} valgt)`}
                </button>
            </div>
        </div>
    );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function LokasjonerAdminPage() {
    const [lokasjoner, setLokasjoner] = useState<Lokasjon[]>([]);
    const [unassigned, setUnassigned] = useState<EiendomSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState<Set<string>>(new Set());
    const [editing, setEditing] = useState<string | null>(null);   // lokasjon_id or "new"
    const [assigning, setAssigning] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        setLoading(true);
        try {
            const [loks, unass] = await Promise.all([api.list(), api.unassigned()]);
            setLokasjoner(loks);
            setUnassigned(unass);
        } catch {
            setError("Kunne ikke laste lokasjoner.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const toggleExpand = (id: string) => setExpanded(prev => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id); else next.add(id);
        return next;
    });

    const handleCreate = async (f: FormState) => {
        await api.create(f);
        setEditing(null);
        await load();
    };

    const handleUpdate = (id: string) => async (f: FormState) => {
        await api.update(id, f);
        setEditing(null);
        await load();
    };

    const handleDelete = async (id: string, navn: string) => {
        if (!confirm(`Slett «${navn}»? Eiendommene mister sin lokasjonskobling.`)) return;
        await api.delete(id);
        await load();
    };

    const handleAssignDone = (updated: Lokasjon) => {
        setLokasjoner(prev => prev.map(l => l.lokasjon_id === updated.lokasjon_id ? updated : l));
        setAssigning(null);
        load();
    };

    if (loading) return (
        <div className="p-6 animate-pulse space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-12 bg-muted rounded-lg" />)}
        </div>
    );

    return (
        <div className="p-6 max-w-4xl space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold flex items-center gap-2">
                        <MapPin size={20} className="text-primary" /> Lokasjoner
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        Grupper avdelinger under samme fysiske lokasjon. Navnene brukes i prediksjon og rapporter.
                    </p>
                </div>
                <button
                    onClick={() => setEditing("new")}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90"
                >
                    <Plus size={14} /> Ny lokasjon
                </button>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            {editing === "new" && (
                <LokasjonForm onSave={handleCreate} onCancel={() => setEditing(null)} />
            )}

            {unassigned.length > 0 && (
                <div className="text-xs text-muted-foreground bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
                    <span className="font-medium text-amber-700">{unassigned.length} avdelinger</span> er ikke tilknyttet noen lokasjon ennå.
                </div>
            )}

            <div className="space-y-2">
                {lokasjoner.map(lok => (
                    <div key={lok.lokasjon_id} className="border rounded-lg overflow-hidden">
                        {/* Header row */}
                        <div className="flex items-center gap-3 px-4 py-3 bg-card hover:bg-muted/20 transition-colors">
                            <button onClick={() => toggleExpand(lok.lokasjon_id)} className="text-muted-foreground">
                                {expanded.has(lok.lokasjon_id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            </button>
                            <div className="flex-1 min-w-0">
                                <div className="font-semibold truncate">{lok.navn}</div>
                                <div className="text-xs text-muted-foreground flex gap-3 mt-0.5">
                                    {lok.lokalisering_id && <span>ID: {lok.lokalisering_id}</span>}
                                    {lok.adresse && <span>{lok.adresse}</span>}
                                    {lok.region && <span>{lok.region}</span>}
                                </div>
                            </div>
                            <div className="flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded-full">
                                <Users size={11} /> {lok.antall_eiendommer}
                            </div>
                            <div className="flex items-center gap-1">
                                <button
                                    onClick={() => setAssigning(assigning === lok.lokasjon_id ? null : lok.lokasjon_id)}
                                    className="p-1.5 rounded hover:bg-muted/50 text-muted-foreground hover:text-primary"
                                    title="Tilknytt avdelinger"
                                >
                                    <Users size={14} />
                                </button>
                                <button
                                    onClick={() => setEditing(editing === lok.lokasjon_id ? null : lok.lokasjon_id)}
                                    className="p-1.5 rounded hover:bg-muted/50 text-muted-foreground hover:text-primary"
                                    title="Rediger"
                                >
                                    <Pencil size={14} />
                                </button>
                                <button
                                    onClick={() => handleDelete(lok.lokasjon_id, lok.navn)}
                                    className="p-1.5 rounded hover:bg-muted/50 text-muted-foreground hover:text-destructive"
                                    title="Slett"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </div>

                        {/* Edit form */}
                        {editing === lok.lokasjon_id && (
                            <div className="px-4 pb-3">
                                <LokasjonForm
                                    initial={{
                                        navn: lok.navn,
                                        adresse: lok.adresse ?? "",
                                        lokalisering_id: lok.lokalisering_id ?? "",
                                        region: lok.region ?? "",
                                        merknad: lok.merknad ?? "",
                                    }}
                                    onSave={handleUpdate(lok.lokasjon_id)}
                                    onCancel={() => setEditing(null)}
                                />
                            </div>
                        )}

                        {/* Assign panel */}
                        {assigning === lok.lokasjon_id && (
                            <div className="px-4 pb-3">
                                <AssignPanel
                                    lokasjon={lok}
                                    allUnassigned={unassigned}
                                    onDone={handleAssignDone}
                                />
                            </div>
                        )}

                        {/* Expanded eiendommer list */}
                        {expanded.has(lok.lokasjon_id) && lok.eiendommer.length > 0 && (
                            <div className="border-t bg-muted/10">
                                {lok.eiendommer.map(e => (
                                    <div key={e.property_id}
                                        className="flex items-center gap-3 px-6 py-2 text-sm border-b last:border-0">
                                        <span className="flex-1 truncate font-medium">{e.name ?? "—"}</span>
                                        <span className="text-xs text-muted-foreground truncate max-w-48">{e.address ?? ""}</span>
                                        <span className="text-xs text-muted-foreground">{e.region ?? ""}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}

                {lokasjoner.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-8">
                        Ingen lokasjoner opprettet ennå. Klikk «Ny lokasjon» for å starte.
                    </p>
                )}
            </div>
        </div>
    );
}
