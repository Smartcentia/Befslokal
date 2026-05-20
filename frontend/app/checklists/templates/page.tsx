"use client";

import React, { useEffect, useState } from "react";
import { internalControlService, ChecklistTemplate } from "@/lib/domains/hms/internalControlService";
import { propertyService } from "@/lib/domains/core/propertyService";
import Link from "next/link";
import Header from "@/app/components/ui/Header";
import {
    ClipboardList,
    Plus,
    Pencil,
    Trash2,
    FileCheck,
    ChevronDown,
} from "lucide-react";


export default function ChecklistTemplatesPage() {
    const [templates, setTemplates] = useState<ChecklistTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [properties, setProperties] = useState<{ property_id: string; address?: string; name?: string }[]>([]);

    const loadTemplates = () => {
        internalControlService
            .getChecklists("my")
            .then(setTemplates)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        loadTemplates();
        propertyService.getAll(0, 100).then(setProperties).catch(() => setProperties([]));
    }, []);

    return (
        <div className="min-h-screen font-sans text-foreground pb-20">
            <Header />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">
                <div className="mb-8 flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-linear-to-r from-blue-600 to-indigo-500">
                            Mine sjekklistemaler
                        </h1>
                        <p className="text-muted mt-2">
                            Opprett og administrer egne sjekklister. Bruk dem til å opprette internkontroll-saker for eiendommer.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link
                            href="/checklists"
                            className="px-4 py-2 text-sm font-medium text-muted hover:text-foreground transition-colors"
                        >
                            Tilbake til sjekklister
                        </Link>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium text-sm"
                        >
                            <Plus size={16} />
                            Ny mal
                        </button>
                    </div>
                </div>

                {showCreate && (
                    <CreateTemplateForm
                        onClose={() => setShowCreate(false)}
                        onSaved={() => {
                            setShowCreate(false);
                            loadTemplates();
                        }}
                    />
                )}

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-40 bg-muted/30 rounded-xl animate-pulse" />
                        ))}
                    </div>
                ) : templates.length === 0 ? (
                    <div className="p-12 rounded-xl border-2 border-dashed border-border text-center text-muted">
                        <ClipboardList size={48} className="mx-auto mb-4 opacity-50" />
                        <p className="font-medium">Ingen egne maler ennå</p>
                        <p className="text-sm mt-2">Opprett en mal for å bruke den til internkontroll-saker.</p>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium text-sm"
                        >
                            <Plus size={16} />
                            Opprett første mal
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {templates.map((t) => (
                            <TemplateCard
                                key={t.template_id}
                                template={t}
                                properties={properties}
                                isEditing={editingId === t.template_id}
                                onEdit={() => setEditingId(t.template_id)}
                                onCancelEdit={() => setEditingId(null)}
                                onSaved={() => {
                                    setEditingId(null);
                                    loadTemplates();
                                }}
                                onDeleted={() => loadTemplates()}
                            />
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

function CreateTemplateForm({
    onClose,
    onSaved,
}: {
    onClose: () => void;
    onSaved: () => void;
}) {
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [category, setCategory] = useState("brannvern");
    const [frequency, setFrequency] = useState("monthly");
    const [items, setItems] = useState<{ id: string; label: string }[]>([{ id: "1", label: "" }]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const addItem = () => {
        setItems((prev) => [...prev, { id: String(prev.length + 1), label: "" }]);
    };

    const updateItem = (index: number, label: string) => {
        setItems((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], label };
            return next;
        });
    };

    const removeItem = (index: number) => {
        setItems((prev) => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSaving(true);
        const validItems = items.filter((i) => i.label.trim());
        if (validItems.length === 0) {
            setError("Legg til minst ett sjekkpunkt.");
            setSaving(false);
            return;
        }
        if (!title.trim()) {
            setError("Tittel er påkrevd.");
            setSaving(false);
            return;
        }
        try {
            await internalControlService.createTemplate({
                title: title.trim(),
                description: description.trim() || undefined,
                items: validItems.map((i) => ({ id: i.id, label: i.label })),
                category,
                frequency,
            });
            onSaved();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Kunne ikke lagre mal.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="glass-card p-6 mb-8">
            <h2 className="text-xl font-bold mb-4">Ny sjekklistemal</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Tittel *</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        placeholder="F.eks. Månedlig brannsjekk"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">Beskrivelse</label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        rows={2}
                        placeholder="Valgfri beskrivelse"
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Kategori</label>
                        <select
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        >
                            <option value="brannvern">Brannvern</option>
                            <option value="el-sikkerhet">El-sikkerhet</option>
                            <option value="vedlikehold">Vedlikehold</option>
                            <option value="hms">HMS</option>
                            <option value="annet">Annet</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Frekvens</label>
                        <select
                            value={frequency}
                            onChange={(e) => setFrequency(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        >
                            <option value="weekly">Ukentlig</option>
                            <option value="monthly">Månedlig</option>
                            <option value="quarterly">Kvartalsvis</option>
                            <option value="yearly">Årlig</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2">Sjekkpunkter</label>
                    <div className="space-y-2">
                        {items.map((item, i) => (
                            <div key={i} className="flex gap-2">
                                <input
                                    type="text"
                                    value={item.label}
                                    onChange={(e) => updateItem(i, e.target.value)}
                                    className="flex-1 px-3 py-2 rounded-lg border border-border bg-background"
                                    placeholder={`Sjekkpunkt ${i + 1}`}
                                />
                                <button
                                    type="button"
                                    onClick={() => removeItem(i)}
                                    className="p-2 text-muted hover:text-destructive"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                        <button
                            type="button"
                            onClick={addItem}
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                            <Plus size={14} /> Legg til sjekkpunkt
                        </button>
                    </div>
                </div>
                {error && <p className="text-destructive text-sm">{error}</p>}
                <div className="flex gap-2">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg border border-border hover:bg-muted/50"
                    >
                        Avbryt
                    </button>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                        {saving ? "Lagrer..." : "Lagre mal"}
                    </button>
                </div>
            </form>
        </div>
    );
}

function TemplateCard({
    template,
    properties,
    isEditing,
    onEdit,
    onCancelEdit,
    onSaved,
    onDeleted,
}: {
    template: ChecklistTemplate;
    properties: { property_id: string; address?: string; name?: string }[];
    isEditing: boolean;
    onEdit: () => void;
    onCancelEdit: () => void;
    onSaved: () => void;
    onDeleted: () => void;
}) {
    const [showAdopt, setShowAdopt] = useState(false);
    const [adoptPropertyId, setAdoptPropertyId] = useState("");
    const [adopting, setAdopting] = useState(false);
    const [adoptError, setAdoptError] = useState<string | null>(null);

    const handleAdopt = async () => {
        if (!adoptPropertyId) return;
        setAdoptError(null);
        setAdopting(true);
        try {
            await internalControlService.createCaseFromTemplate(template.template_id, adoptPropertyId);
            setShowAdopt(false);
            setAdoptPropertyId("");
        } catch (e) {
            setAdoptError(e instanceof Error ? e.message : "Kunne ikke opprette sak.");
        } finally {
            setAdopting(false);
        }
    };

    if (isEditing) {
        return (
            <EditTemplateForm
                template={template}
                onCancel={onCancelEdit}
                onSaved={onSaved}
                onDeleted={onDeleted}
            />
        );
    }

    const itemCount = template.items?.length ?? 0;

    return (
        <div className="glass-card p-6 flex flex-col">
            <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted">
                    {template.category}
                </span>
                <div className="flex gap-1">
                    <button
                        onClick={onEdit}
                        className="p-1.5 text-muted hover:text-foreground rounded"
                        title="Rediger"
                    >
                        <Pencil size={14} />
                    </button>
                    <button
                        onClick={async () => {
                            if (confirm("Er du sikker på at du vil slette denne malen?")) {
                                await internalControlService.deleteTemplate(template.template_id);
                                onDeleted();
                            }
                        }}
                        className="p-1.5 text-muted hover:text-destructive rounded"
                        title="Slett"
                    >
                        <Trash2 size={14} />
                    </button>
                </div>
            </div>
            <h3 className="font-bold text-foreground mb-2">{template.title}</h3>
            <p className="text-sm text-muted grow line-clamp-2">
                {template.description || "Ingen beskrivelse"}
            </p>
            <p className="text-xs text-muted mt-2">{itemCount} sjekkpunkter</p>
            <div className="mt-4 relative">
                <button
                    onClick={() => setShowAdopt(!showAdopt)}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors text-sm font-medium"
                >
                    <FileCheck size={16} />
                    Opprett sak for eiendom
                    <ChevronDown size={14} className={showAdopt ? "rotate-180" : ""} />
                </button>
                {showAdopt && (
                    <div className="absolute top-full left-0 right-0 mt-2 p-3 bg-background border border-border rounded-lg shadow-lg z-10">
                        <label className="block text-xs font-medium mb-2">Velg eiendom</label>
                        <select
                            value={adoptPropertyId}
                            onChange={(e) => setAdoptPropertyId(e.target.value)}
                            className="w-full px-3 py-2 rounded border border-border bg-background text-sm mb-2"
                        >
                            <option value="">-- Velg eiendom --</option>
                            {properties.map((p) => (
                                <option key={p.property_id} value={p.property_id}>
                                    {p.address || p.name || p.property_id}
                                </option>
                            ))}
                        </select>
                        {adoptError && <p className="text-destructive text-xs mb-2">{adoptError}</p>}
                        <div className="flex gap-2">
                            <button
                                onClick={() => setShowAdopt(false)}
                                className="flex-1 py-1.5 text-sm border border-border rounded hover:bg-muted/50"
                            >
                                Avbryt
                            </button>
                            <button
                                onClick={handleAdopt}
                                disabled={!adoptPropertyId || adopting}
                                className="flex-1 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
                            >
                                {adopting ? "Oppretter..." : "Opprett"}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function EditTemplateForm({
    template,
    onCancel,
    onSaved,
    onDeleted,
}: {
    template: ChecklistTemplate;
    onCancel: () => void;
    onSaved: () => void;
    onDeleted: () => void;
}) {
    const [title, setTitle] = useState(template.title);
    const [description, setDescription] = useState(template.description ?? "");
    const [category, setCategory] = useState(template.category);
    const [frequency, setFrequency] = useState(template.frequency ?? "monthly");
    const [items, setItems] = useState<{ id: string; label: string }[]>(
        (template.items ?? []).map((i, idx) => ({
            id: String(idx + 1),
            label: (i as { label?: string; task?: string }).label ?? (i as { task?: string }).task ?? "",
        }))
    );
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const addItem = () => {
        setItems((prev) => [...prev, { id: String(prev.length + 1), label: "" }]);
    };

    const updateItem = (index: number, label: string) => {
        setItems((prev) => {
            const next = [...prev];
            next[index] = { ...next[index], label };
            return next;
        });
    };

    const removeItem = (index: number) => {
        setItems((prev) => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSaving(true);
        const validItems = items.filter((i) => i.label.trim());
        if (validItems.length === 0) {
            setError("Legg til minst ett sjekkpunkt.");
            setSaving(false);
            return;
        }
        try {
            await internalControlService.updateTemplate(template.template_id, {
                title: title.trim(),
                description: description.trim() || undefined,
                items: validItems.map((i) => ({ id: i.id, label: i.label })),
                category,
                frequency,
            });
            onSaved();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Kunne ikke lagre.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="glass-card p-6 col-span-full md:col-span-2 lg:col-span-3">
            <h2 className="text-xl font-bold mb-4">Rediger mal</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Tittel *</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">Beskrivelse</label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        rows={2}
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Kategori</label>
                        <select
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        >
                            <option value="brannvern">Brannvern</option>
                            <option value="el-sikkerhet">El-sikkerhet</option>
                            <option value="vedlikehold">Vedlikehold</option>
                            <option value="hms">HMS</option>
                            <option value="annet">Annet</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Frekvens</label>
                        <select
                            value={frequency}
                            onChange={(e) => setFrequency(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background"
                        >
                            <option value="weekly">Ukentlig</option>
                            <option value="monthly">Månedlig</option>
                            <option value="quarterly">Kvartalsvis</option>
                            <option value="yearly">Årlig</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2">Sjekkpunkter</label>
                    <div className="space-y-2">
                        {items.map((item, i) => (
                            <div key={i} className="flex gap-2">
                                <input
                                    type="text"
                                    value={item.label}
                                    onChange={(e) => updateItem(i, e.target.value)}
                                    className="flex-1 px-3 py-2 rounded-lg border border-border bg-background"
                                />
                                <button
                                    type="button"
                                    onClick={() => removeItem(i)}
                                    className="p-2 text-muted hover:text-destructive"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                        <button
                            type="button"
                            onClick={addItem}
                            className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                            <Plus size={14} /> Legg til sjekkpunkt
                        </button>
                    </div>
                </div>
                {error && <p className="text-destructive text-sm">{error}</p>}
                <div className="flex gap-2">
                    <button type="button" onClick={onCancel} className="px-4 py-2 rounded-lg border border-border hover:bg-muted/50">
                        Avbryt
                    </button>
                    <button
                        type="button"
                        onClick={async () => {
                            if (confirm("Er du sikker på at du vil slette denne malen?")) {
                                await internalControlService.deleteTemplate(template.template_id);
                                onDeleted();
                            }
                        }}
                        className="px-4 py-2 rounded-lg border border-destructive text-destructive hover:bg-destructive/10"
                    >
                        Slett
                    </button>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                        {saving ? "Lagrer..." : "Lagre"}
                    </button>
                </div>
            </form>
        </div>
    );
}
