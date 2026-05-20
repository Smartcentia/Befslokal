import React, { useEffect, useState } from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, Activity } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { motion } from 'framer-motion';
import { fetchAPI } from '@/lib/api/client';

interface Lien {
    type: string;
    amount: number;
    currency: string;
    creditor?: string;
}

interface RiskProfile {
    score: number;
    level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN' | 'ERROR';
    red_flags: string[];
    actions: string[];
    liens?: Lien[]; // Optional list of mortgages
}

interface RiskIndicatorProps {
    orgNr: string;
}

export function RiskIndicator({ orgNr }: RiskIndicatorProps) {
    const [profile, setProfile] = useState<RiskProfile | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!orgNr) return;

        const fetchRisk = async () => {
            setLoading(true);
            try {
                const data = await fetchAPI<RiskProfile>(`/external/risk/${orgNr}`);
                setProfile(data);
            } catch (err) {
                console.error("Risk fetch failed", err);
            } finally {
                setLoading(false);
            }
        };

        fetchRisk();
    }, [orgNr]);

    if (loading) return <div className="text-sm text-gray-400 animate-pulse">Analyserer risiko...</div>;
    if (!profile) return null;

    // Determine styles based on level
    let color = "text-green-500";
    let bg = "bg-green-500/10";
    let Icon = ShieldCheck;
    let label = "Lav Risiko";

    if (profile.level === 'MEDIUM') {
        color = "text-yellow-500";
        bg = "bg-yellow-500/10";
        Icon = AlertTriangle;
        label = "Middels Risiko";
    } else if (profile.level === 'HIGH') {
        color = "text-orange-500";
        bg = "bg-orange-500/10";
        Icon = ShieldAlert;
        label = "Høy Risiko";
    } else if (profile.level === 'CRITICAL') {
        color = "text-red-600";
        bg = "bg-red-600/10";
        Icon = AlertOctagon;
        label = "KRITISK";
    }

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardHeader className="p-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Activity className="h-4 w-4" /> Risikovurdering (Sanntid)
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                <div className={`flex flex-col gap-4 p-4 rounded-lg border ${bg} border-${color.split('-')[1]}-200/20`}>
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-full bg-background ${color}`}>
                            <Icon className="h-8 w-8" />
                        </div>
                        <div>
                            <h3 className={`text-lg font-bold ${color}`}>{label} (Score: {profile.score})</h3>
                            {profile.red_flags.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Ingen negative anmerkninger funnet.</p>
                            ) : (
                                <div className="mt-2 space-y-1">
                                    {profile.red_flags.map((flag, i) => (
                                        <div key={i} className="text-sm font-medium text-red-500 flex items-center gap-1">
                                            • {flag}
                                        </div>
                                    ))}
                                    {profile.actions.map((act, i) => (
                                        <div key={`act-${i}`} className="text-xs font-bold text-red-700 bg-red-100 px-2 py-1 rounded inline-block mt-1">
                                            HANDLING: {act}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Liens / Mortgage Details Section */}
                    {profile.liens && profile.liens.length > 0 && (
                        <div className="mt-2 pt-4 border-t border-black/5 dark:border-white/5">
                            <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Registrerte Heftelser (Løsøreregisteret)</h4>
                            <div className="space-y-2">
                                {profile.liens.map((lien, i) => (
                                    <div key={i} className="flex justify-between items-center text-sm p-2 bg-background/50 rounded">
                                        <div className="flex flex-col">
                                            <span className="font-medium">{lien.type}</span>
                                            {lien.creditor && <span className="text-xs text-muted-foreground">{lien.creditor}</span>}
                                        </div>
                                        <span className="font-mono font-bold">
                                            {new Intl.NumberFormat('no-NO', { style: 'currency', currency: lien.currency }).format(lien.amount)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
