"use client";

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Users, AlertTriangle, TrendingUp } from 'lucide-react';
import { getTopTenants, Tenant } from '@/lib/api';
import { motion } from 'framer-motion';

interface TopTenantsPanelProps {
    limit?: number;
}

export default function TopTenantsPanel({ limit }: TopTenantsPanelProps) {
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const data = await getTopTenants();
                setTenants(data);
            } catch (err) {
                console.error("Failed to load top tenants", err);
                setError("Kunne ikke laste leietakere");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    if (loading) {
        return (
            <Card className="h-full border-border/40 shadow-sm bg-card/50 backdrop-blur-sm">
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg font-medium flex items-center gap-2 text-foreground/80">
                        <Users className="h-5 w-5 text-primary" />
                        {limit ? '5 største leietakere' : 'Største Leietakere (Omsetning)'}
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex items-center justify-center p-8">
                    <div className="animate-pulse flex flex-col items-center gap-2">
                        <div className="h-4 w-32 bg-muted rounded"></div>
                        <div className="h-4 w-24 bg-muted rounded"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="h-full border-red-200 dark:border-red-900/30 shadow-sm bg-red-50/10">
                <CardContent className="flex items-center justify-center p-8 text-red-500 gap-2">
                    <AlertTriangle size={18} />
                    <span className="text-sm font-medium">{error}</span>
                </CardContent>
            </Card>
        );
    }

    // Limit display (default: show all)
    const displayTenants = limit ? tenants.slice(0, limit) : tenants;

    // Calculate max revenue for progress bars (min 1 to avoid division by zero)
    const maxRevenue = Math.max(...displayTenants.map(t => t.revenue), 1);

    return (
        <Card className="h-full border-border/40 shadow-sm bg-card/50 backdrop-blur-sm overflow-hidden flex flex-col">
            <CardHeader className="pb-3 border-b border-border/30 bg-muted/20">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                        <Users className="h-4 w-4 text-primary" />
                        <span>{limit ? '5 største leietakere' : 'Topp 10 Leietakere'}</span>
                    </CardTitle>
                    <div className="text-xs font-medium text-muted-foreground bg-secondary/50 px-2 py-1 rounded-full flex items-center gap-1">
                        <TrendingUp size={12} />
                        Etter omsetning
                    </div>
                </div>
            </CardHeader>

            <CardContent className="p-0 overflow-y-auto custom-scrollbar flex-1">
                {displayTenants.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-40 text-muted-foreground p-4 text-center">
                        <Users size={32} className="mb-2 opacity-20" />
                        <p className="text-sm">Ingen leiedata tilgjengelig</p>
                    </div>
                ) : (
                    <div className="divide-y divide-border/30">
                        {displayTenants.map((tenant, index) => {
                            const percentage = (tenant.revenue / maxRevenue) * 100;

                            return (
                                <div key={tenant.tenant_id} className="p-4 hover:bg-muted/40 transition-colors group">
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center gap-3 overflow-hidden">
                                            <div className={`
                        flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold shrink-0
                        ${index < 3 ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-secondary text-secondary-foreground'}
                      `}>
                                                {index + 1}
                                            </div>
                                            <span className="font-medium text-sm truncate text-foreground group-hover:text-primary transition-colors" title={tenant.name}>
                                                {tenant.name}
                                            </span>
                                        </div>
                                        <div className="text-right shrink-0">
                                            <span className="block text-sm font-bold tracking-tight">
                                                {new Intl.NumberFormat('no-NO', {
                                                    style: 'currency',
                                                    currency: 'NOK',
                                                    maximumFractionDigits: 0,
                                                    notation: tenant.revenue > 1000000 ? 'compact' : 'standard'
                                                }).format(tenant.revenue)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        {/* Progress Bar Container */}
                                        <div className="h-1.5 w-full bg-secondary/50 rounded-full overflow-hidden">
                                            <motion.div
                                                className="h-full bg-linear-to-r from-primary to-primary/80 rounded-full transition-all duration-1000 ease-out group-hover:from-primary/90 group-hover:to-primary"
                                                initial={{ width: 0 }}
                                                animate={{ width: `${percentage}%` }}
                                            />
                                        </div>

                                        <div className="flex justify-between items-center text-xs text-muted-foreground px-0.5">
                                            <span>{tenant.contracts} kontrakt{tenant.contracts !== 1 ? 'er' : ''}</span>
                                            <span>{percentage.toFixed(0)}% av topp</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
