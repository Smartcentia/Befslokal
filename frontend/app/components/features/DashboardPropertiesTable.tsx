"use client";

import { useEffect, useState } from "react";
import { Building2, ArrowRight, User } from "lucide-react";
import { getProperties, Property } from "@/lib/api";
import Link from "next/link";

export default function DashboardPropertiesTable() {
    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProps = async () => {
            try {
                const data = await getProperties(0, 6); // Limit to 6 for the grid
                setProperties(data);
            } catch (err) {
                console.error("Failed to fetch properties", err);
            } finally {
                setLoading(false);
            }
        };
        fetchProps();
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-32 bg-surface border border-border rounded-xl animate-pulse shadow-sm" />
                ))}
            </div>
        );
    }

    return (
        <div className="mt-8">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-foreground">Mine Eiendommer</h3>
                <Link href="/properties" className="text-xs font-bold text-primary hover:opacity-80 uppercase tracking-wider transition-colors">
                    Se alle →
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {properties.length === 0 ? (
                    <div className="col-span-full p-12 text-center glass-card text-muted text-sm">
                        Ingen eiendommer funnet.
                    </div>
                ) : (
                    properties.map((prop) => (
                        <Link
                            key={prop.property_id}
                            href={`/properties/${prop.property_id}`}
                            className="group glass-card overflow-hidden hover:shadow-md transition-all hover:-translate-y-1 flex flex-col"
                        >
                            {/* Content section */}
                            <div className="p-4 flex-1 flex flex-col">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="p-2 bg-primary/10 text-primary rounded-lg group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                        <Building2 size={18} />
                                    </div>
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide bg-success/20 text-success`}>
                                        Aktiv
                                    </span>
                                </div>

                                <h4 className="font-bold text-foreground text-sm mb-1 group-hover:text-primary transition-colors truncate">
                                    {prop.name || prop.address}
                                </h4>
                                <p className="text-[11px] text-muted mb-4 truncate italic">
                                    {prop.address !== prop.name ? prop.address : prop.city}
                                </p>

                                <div className="flex justify-between items-center pt-3 border-t border-border mt-auto">
                                    <div className="flex items-center gap-1.5 flex-wrap">
                                        <div className="flex -space-x-1.5">
                                            {prop.managers && prop.managers.length > 0 ? (
                                                prop.managers.slice(0, 3).map((m, idx) => (
                                                    <div
                                                        key={m.user_id}
                                                        className="w-5 h-5 rounded-full bg-primary/10 border border-background flex items-center justify-center text-[8px] font-bold text-primary"
                                                        title={m.name}
                                                    >
                                                        {m.name?.charAt(0) || 'U'}
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="w-5 h-5 rounded-full bg-surface flex items-center justify-center text-[9px] text-muted">
                                                    <User size={10} />
                                                </div>
                                            )}
                                        </div>
                                        <span className="text-[10px] font-medium text-muted truncate max-w-25">
                                            {prop.usage?.toLowerCase() === 'barnevernsinstitusjon' ?
                                                'Formålsbygg' : (prop.usage || "Næring")}
                                        </span>
                                        <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-600 dark:text-amber-400 text-[9px] font-bold uppercase">
                                            Aktiv
                                        </span>
                                    </div>
                                    <span className="text-[10px] font-bold text-muted group-hover:text-primary flex items-center gap-1 transition-colors">
                                        Detaljer <ArrowRight size={10} />
                                    </span>
                                </div>
                            </div>
                        </Link>
                    ))
                )}
            </div>
        </div>
    );
}

