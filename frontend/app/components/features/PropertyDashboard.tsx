"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { Building2, ArrowRight } from "lucide-react";
import { propertyService, type Property } from "@/lib/domains/core/propertyService";

export default function PropertyDashboard() {
    const { user } = useAuth();
    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProperties = async () => {
            if (!user) {
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                const all = await propertyService.getAll(0, 500);
                setProperties(Array.isArray(all) ? all : []);
            } catch (err) {
                console.error("Failed to fetch properties", err);
            } finally {
                setLoading(false);
            }
        };

        fetchProperties();
    }, [user]);

    if (loading) {
        return (
            <div className="p-8 text-center text-muted">
                Laster dine eiendommer...
            </div>
        );
    }

    if (properties.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] p-8 text-center">
                <div className="bg-surface p-8 rounded-xl border border-border max-w-md">
                    <h2 className="text-xl font-bold mb-2">Ingen eiendommer funnet</h2>
                    <p className="text-muted mb-6">
                        Du har ingen eiendommer knyttet til din bruker.
                        Kontakt administrator dersom dette er feil.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen text-foreground space-y-8 p-6">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">Mine Eiendommer</h1>
                    <p className="text-muted-foreground mt-1">
                        Oversikt over eiendommer du forvalter
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {properties.map((prop) => (
                    <div
                        key={prop.property_id}
                        className="group glass-card overflow-hidden hover:shadow-lg transition-all hover:-translate-y-1 flex flex-col h-full bg-surface/50 border border-border/50 hover:border-primary/50 rounded-xl"
                    >
                        <Link href={`/properties/${prop.property_id}`} className="block h-full p-6 flex flex-col">
                            <div className="flex items-start gap-3 mb-4">
                                {prop.bufdir_image_path ? (
                                    // eslint-disable-next-line @next/next/no-img-element
                                    <img
                                        src={prop.bufdir_image_path}
                                        alt=""
                                        className="w-16 h-16 rounded-lg object-cover border border-border shrink-0"
                                    />
                                ) : (
                                    <div className="p-3 bg-primary/10 text-primary rounded-xl group-hover:scale-110 transition-transform duration-300 shrink-0">
                                        <Building2 size={24} />
                                    </div>
                                )}
                                <div className="flex-1 min-w-0 flex flex-col items-end gap-1">
                                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                                        Aktiv forvaltning
                                    </span>
                                    {prop.region && (
                                        <span className="text-[10px] font-mono text-muted uppercase tracking-wide">
                                            {prop.region}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <h3 className="font-bold text-foreground text-lg mb-2 group-hover:text-primary transition-colors line-clamp-1">
                                {prop.name || prop.address}
                            </h3>

                            <div className="space-y-1 mb-4 flex-grow">
                                <p className="text-sm text-foreground truncate">
                                    {prop.address}
                                </p>
                                <p className="text-xs text-muted truncate">
                                    {prop.city} {prop.postal_code}
                                </p>
                                <div className="flex flex-wrap gap-2 pt-1">
                                    {prop.approved_places != null && prop.approved_places > 0 && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-medium">
                                            {prop.approved_places} plasser
                                        </span>
                                    )}
                                    {prop.usage && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-muted/30 text-muted-foreground border border-border font-medium line-clamp-1 max-w-full">
                                            {prop.usage}
                                        </span>
                                    )}
                                </div>
                                {prop.primary_lease_party_name && (
                                    <p className="text-[11px] text-muted-foreground line-clamp-2 pt-1" title={prop.primary_lease_party_name}>
                                        <span className="font-medium text-foreground/80">Leverandør: </span>
                                        {prop.primary_lease_party_name}
                                    </p>
                                )}
                            </div>

                            <div className="mt-auto pt-4 border-t border-border/50 flex items-center justify-between w-full">
                                <div className="flex items-center gap-2">
                                    <div className="w-6 h-6 rounded-full bg-primary/20 border-2 border-surface flex items-center justify-center text-[8px] font-bold text-primary">
                                        MEG
                                    </div>
                                    <span className="text-[10px] text-muted font-medium uppercase tracking-wider">
                                        Forvalter
                                    </span>
                                </div>
                                <span className="text-xs font-bold text-primary flex items-center gap-1 group-hover:gap-2 transition-all">
                                    Gå til eiendom <ArrowRight size={12} />
                                </span>
                            </div>
                        </Link>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 pb-12">
                <div className="glass-card p-6 rounded-xl border border-border bg-surface/30 hover:bg-surface/50 transition-colors">
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border/50 pb-2">Internkontroll</h3>
                    <div className="space-y-3">
                        <Link href="/internal-control" className="block text-sm hover:text-primary transition-colors flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                            Sjekkpunkter og avvik
                        </Link>
                        <Link href="/deviations" className="block text-sm hover:text-primary transition-colors flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                            Avviksbehandling
                        </Link>
                    </div>
                </div>

                <div className="glass-card p-6 rounded-xl border border-border bg-surface/30 hover:bg-surface/50 transition-colors">
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4 border-b border-border/50 pb-2">Økonomi</h3>
                    <div className="space-y-3">
                        <Link href="/budget" className="block text-sm hover:text-primary transition-colors flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                            Budsjettoversikt
                        </Link>
                        <Link href="/financials" className="block text-sm hover:text-primary transition-colors flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                            Regnskapstall
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
