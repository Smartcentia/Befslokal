"use client";

import React, { useEffect, useState } from "react";
import { fetchAPI } from "@/lib/api/client";
import Header from "@/app/components/ui/Header";
import { ClipboardList, Plus, Trash2, Radio, Globe } from "lucide-react";
import Link from "next/link";
import CreateTemplateDialog from "./CreateTemplateDialog";

interface ActivityTemplate {
    template_id: string;
    title: string;
    description?: string;
    category: string;
    priority: string;
    activity_type: string;
    scope?: string;
    adoption_count: number;
    created_by_user_id?: string;
}

type TabType = "explore" | "mine";

export default function ActivityHubPage() {
    const [templates, setTemplates] = useState<ActivityTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<TabType>("explore");
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [userSession, setUserSession] = useState<any>(null); // To store user info

    // Using client-side fetching for simplicity for now
    const fetchTemplates = async () => {
        setLoading(true);
        try {
            // "mine" tab -> scope=mine
            // "explore" tab -> scope=community (or default/system)
            // Ideally backend handles "default view" vs "my templates"

            // Backend logic: 
            // no scope param -> shows system + community + mine (The "Explore" view)
            // scope="mine" -> shows only mine

            const scopeParam = activeTab === "mine" ? "?scope=mine" : "";
            const data = await fetchAPI(`/hms/activities/templates${scopeParam}`);
            setTemplates(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error(error);
            setTemplates([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTemplates();
    }, [activeTab]);

    const handleSuccessCreate = (newTemplate: ActivityTemplate) => {
        // If we represent "mine", add it. If "explore", maybe add it if it fits.
        // Simplest: refresh
        fetchTemplates();
        setActiveTab("mine"); // Switch to mine to see it
    };

    const handlePublish = async (templateId: string) => {
        if (!confirm("Er du sikker på at du vil publisere denne malen til fellesskapet?")) return;
        try {
            await fetchAPI(`/hms/activities/templates/${templateId}/publish`, { method: "POST" });
            alert("Mal publisert!");
            fetchTemplates();
        } catch (e) {
            alert("Feil ved publisering");
        }
    };

    const handleDelete = async (templateId: string) => {
        if (!confirm("Er du sikker på at du vil slette denne malen?")) return;
        try {
            await fetchAPI(`/hms/activities/templates/${templateId}`, { method: "DELETE" });
            fetchTemplates();
        } catch (e) {
            alert("Feil ved sletting");
        }
    };

    return (
        <div className="min-h-screen font-sans text-foreground pb-20">
            <Header />
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-24">

                // ... existing imports

                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-linear-to-r from-blue-600 to-indigo-500">
                            Aktivitetshub
                        </h1>
                        <p className="text-muted mt-2">
                            Tilgjengelige aktivitetsmaler og bibliotek.
                        </p>
                    </div>
                    <button
                        onClick={() => setShowCreateDialog(true)}
                        className="bg-primary text-primary-foreground px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-primary/90 transition-colors shadow-lg"
                    >
                        <Plus size={18} />
                        Opprett ny mal
                    </button>
                </div>

                <div className="flex gap-4 mb-8 border-b border-border">
                    <button
                        onClick={() => setActiveTab("explore")}
                        className={`pb-3 px-4 text-sm font-medium transition-colors border-b-2 ${activeTab === "explore"
                            ? "border-primary text-primary"
                            : "border-transparent text-muted hover:text-foreground"
                            }`}
                    >
                        Utforsk
                    </button>
                    <button
                        onClick={() => setActiveTab("mine")}
                        className={`pb-3 px-4 text-sm font-medium transition-colors border-b-2 ${activeTab === "mine"
                            ? "border-primary text-primary"
                            : "border-transparent text-muted hover:text-foreground"
                            }`}
                    >
                        Mine maler
                    </button>
                </div>

                <CreateTemplateDialog
                    isOpen={showCreateDialog}
                    onClose={() => setShowCreateDialog(false)}
                    onSuccess={handleSuccessCreate}
                />

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-32 bg-muted/30 rounded-xl animate-pulse" />
                        ))}
                    </div>
                ) : templates.length === 0 ? (
                    <div className="p-12 rounded-xl border-2 border-dashed border-border text-center text-muted">
                        <ClipboardList size={48} className="mx-auto mb-4 opacity-50" />
                        <p>Ingen aktivitetsmaler funnet. Kjør seed_activity_templates for å fylle hub.</p>
                        <Link href="/checklists" className="mt-4 inline-block text-primary hover:underline">
                            Gå til sjekklister
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {templates.map((t) => (
                            <div
                                key={t.template_id}
                                className="glass-card p-6 flex flex-col"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted">
                                        {t.category}
                                    </span>
                                    <span
                                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${t.priority === "critical"
                                            ? "bg-red-500/20 text-red-500"
                                            : t.priority === "high"
                                                ? "bg-amber-500/20 text-amber-500"
                                                : "bg-slate-500/20 text-slate-400"
                                            }`}
                                    >
                                        {t.priority}
                                    </span>
                                </div>
                                <h3 className="font-bold text-foreground mb-2">{t.title}</h3>
                                <p className="text-sm text-muted grow line-clamp-2">
                                    {t.description || "Ingen beskrivelse"}
                                </p>
                                <div className="mt-4 flex items-center justify-between text-xs text-muted">
                                    <span className="flex items-center gap-1">
                                        {t.scope === "community" ? <Globe size={12} className="text-blue-500" /> :
                                            t.scope === "user" ? <Radio size={12} className="text-amber-500" /> : null}
                                        {t.activity_type}
                                    </span>
                                    {t.adoption_count > 0 && (
                                        <span>{t.adoption_count} eiendommer bruker denne</span>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    {activeTab === "mine" && (
                                        <>
                                            {t.scope !== "community" && (
                                                <button
                                                    onClick={() => handlePublish(t.template_id)}
                                                    className="mt-4 flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border border-blue-500/30 text-blue-500 hover:bg-blue-500/10 transition-colors text-sm font-medium"
                                                    title="Publiser til fellesskapet"
                                                >
                                                    <Globe size={16} />
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDelete(t.template_id)}
                                                className="mt-4 flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 transition-colors text-sm font-medium"
                                                title="Slett mal"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </>
                                    )}

                                    <Link
                                        href={`/checklists?adopt=${t.template_id}`}
                                        className="mt-4 flex-1 flex items-center justify-center gap-2 py-2 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors text-sm font-medium"
                                    >
                                        <Plus size={16} />
                                        {activeTab === "mine" ? "Bruk" : "Legg til"}
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <div className="mt-8">
                    <Link
                        href="/checklists"
                        className="text-primary hover:underline flex items-center gap-2"
                    >
                        Tilbake til sjekklister
                    </Link>
                </div>
            </main>
        </div>
    );
}
