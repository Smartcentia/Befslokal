"use client";

import { Building2, Shield, BarChart3, FileText, MapPin, Users } from "lucide-react";
import Link from "next/link";

export default function WelcomePage() {
    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 z-40 bg-background/50 backdrop-blur-xl border-b border-border px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold text-xl shadow-lg shadow-primary/20">
                            B
                        </div>
                    </div>
                    <span className="text-xl font-semibold text-foreground tracking-tight">
                        BEFS <span className="opacity-50 font-normal">| Bufetat</span>
                    </span>
                    <Link
                        href="/login"
                        className="px-6 py-2.5 bg-primary hover:bg-primary/80 text-primary-foreground text-sm font-bold rounded-full transition-all hover:shadow-lg hover:shadow-primary/20"
                    >
                        Logg inn
                    </Link>
                </div>
            </header>

            {/* Hero Section */}
            <main className="flex-1 flex flex-col items-center justify-center px-6 pt-24 pb-12">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6 tracking-tight">
                        Eiendomsforvaltning
                        <span className="block text-primary">for Bufetat</span>
                    </h1>
                    <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
                        BEFS gir deg full oversikt over eiendommer, kontrakter, risiko og vedlikehold
                        - alt samlet i ett moderne verktøy.
                    </p>
                    <Link
                        href="/login"
                        className="inline-block px-8 py-4 bg-primary hover:bg-primary/90 text-primary-foreground text-lg font-bold rounded-full transition-all hover:shadow-xl hover:shadow-primary/30 hover:scale-105"
                    >
                        Logg inn
                    </Link>
                    <p className="text-sm text-muted-foreground mt-4">
                        Tilgang krever konto som administrator oppretter (ingen selvregistrering).
                    </p>
                </div>

                {/* Features Grid */}
                <div className="max-w-6xl mx-auto mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 px-4">
                    <FeatureCard
                        icon={<Building2 className="w-8 h-8" />}
                        title="Eiendomsoversikt"
                        description="Komplett oversikt over alle eiendommer med detaljert informasjon og historikk."
                    />
                    <FeatureCard
                        icon={<FileText className="w-8 h-8" />}
                        title="Kontrakthåndtering"
                        description="Administrer leiekontrakter, opsjoner og KPI-reguleringer enkelt."
                    />
                    <FeatureCard
                        icon={<Shield className="w-8 h-8" />}
                        title="Risikovurdering"
                        description="Automatisk risikoanalyse basert på NVE, Kartverket og andre datakilder."
                    />
                    <FeatureCard
                        icon={<BarChart3 className="w-8 h-8" />}
                        title="Analyse og rapporter"
                        description="Dashboards og rapporter for bedre beslutningsgrunnlag."
                    />
                    <FeatureCard
                        icon={<MapPin className="w-8 h-8" />}
                        title="Kartvisning"
                        description="Se alle eiendommer på kart med geografisk risikoinfo."
                    />
                    <FeatureCard
                        icon={<Users className="w-8 h-8" />}
                        title="HMS og avvik"
                        description="Registrer og følg opp avvik, brannbok og internkontroll."
                    />
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-border py-8 px-6">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-sm text-muted-foreground">
                        Bufetat Eiendomsforvaltningssystem (BEFS)
                    </p>
                    <p className="text-sm text-muted-foreground">
                        For support, kontakt IT-avdelingen
                    </p>
                </div>
            </footer>
        </div>
    );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
    return (
        <div className="glass-card p-6 hover:border-primary/50">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary mb-4">
                {icon}
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        </div>
    );
}
