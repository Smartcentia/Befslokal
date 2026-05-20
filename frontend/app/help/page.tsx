"use client";

import React, { useState } from "react";
import Link from "next/link";
import ChatWidget, { OPEN_KI_KOLLEGA_EVENT } from "@/app/components/features/ChatWidget";
import HelpCenter from "@/app/components/features/HelpCenter";
import HelpFaq from "./HelpFaq";
import KiKollegaHelpPanel from "./KiKollegaHelpPanel";
import { Accessibility, Shield } from "lucide-react";

export default function HelpPage() {
    const [activeTab, setActiveTab] = useState<"ki" | "docs" | "faq">("docs");

    const openKiAndSetTab = () => {
        setActiveTab("ki");
        window.dispatchEvent(new CustomEvent(OPEN_KI_KOLLEGA_EVENT));
    };

    return (
        <div className="min-h-screen p-8 bg-background text-foreground">
            <header className="mb-12 max-w-5xl mx-auto">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 rounded-lg border border-primary/25 bg-primary/10 shadow-sm">
                        <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold text-foreground tracking-tight">Brukerhjelp</h1>
                        <p className="text-muted-foreground mt-1">Komplett guide for alle funksjoner i eiendomsforvaltningssystemet</p>
                    </div>
                </div>
                <nav className="flex flex-wrap gap-2 mt-6 border-b border-border pb-4" aria-label="Hjelpefaner">
                    <button
                        type="button"
                        onClick={openKiAndSetTab}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "ki" ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground border border-transparent"}`}
                    >
                        Spør KI Kollega
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("docs")}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "docs" ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground border border-transparent"}`}
                    >
                        Dokumentasjon
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("faq")}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "faq" ? "bg-primary/15 text-primary border border-primary/30" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground border border-transparent"}`}
                    >
                        Ofte stilte spørsmål
                    </button>
                </nav>
            </header>

            {/* Offentlig informasjon – tilgjengelighet og personvern */}
            <div className="max-w-5xl mx-auto mb-10">
                <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3">Offentlig informasjon</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Link
                        href="/tilgjengelighet"
                        className="flex items-center gap-4 p-4 rounded-xl border border-border bg-surface/30 hover:border-primary/40 hover:bg-surface/50 transition-colors group"
                    >
                        <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20">
                            <Accessibility className="w-6 h-6" aria-hidden />
                        </div>
                        <div>
                            <span className="font-semibold text-foreground group-hover:text-primary transition-colors">Tilgjengelighet</span>
                            <p className="text-sm text-muted-foreground mt-0.5">Tilgjengelighetserklæring og universell utforming (UU)</p>
                        </div>
                    </Link>
                    <Link
                        href="/personvern"
                        className="flex items-center gap-4 p-4 rounded-xl border border-border bg-surface/30 hover:border-primary/40 hover:bg-surface/50 transition-colors group"
                    >
                        <div className="p-2 rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20">
                            <Shield className="w-6 h-6" aria-hidden />
                        </div>
                        <div>
                            <span className="font-semibold text-foreground group-hover:text-primary transition-colors">Personvern</span>
                            <p className="text-sm text-muted-foreground mt-0.5">Behandling av personopplysninger og informasjonskapsler</p>
                        </div>
                    </Link>
                </div>
            </div>

            <main className="max-w-5xl mx-auto">
                {activeTab === "ki" && (
                    <div className="space-y-6">
                        <KiKollegaHelpPanel />
                    </div>
                )}
                {activeTab === "docs" && <HelpCenter />}
                {activeTab === "faq" && <HelpFaq />}
            </main>

            <ChatWidget />
        </div>
    );
}
