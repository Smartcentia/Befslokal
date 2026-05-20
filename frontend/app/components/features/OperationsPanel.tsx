"use client";

import { RecentActivityItem } from "@/lib/api";
import { AlertOctagon, FileCheck, Clock, Building2, Activity, PlayCircle } from "lucide-react";
import Link from "next/link";

// Map icon string names to components
const iconMap: Record<string, any> = {
    "AlertOctagon": AlertOctagon,
    "FileCheck": FileCheck,
    "Building2": Building2,
    "Clock": Clock,
    "Activity": Activity
};

interface OperationsPanelProps {
    recentActivity: RecentActivityItem[];
    loading?: boolean;
}

export default function OperationsPanel({ recentActivity, loading }: OperationsPanelProps) {
    return (
        <div className="space-y-6 h-full flex flex-col">
            {/* Header for the Panel */}
            <div className="flex items-center gap-2 pb-4 border-b border-border">
                <PlayCircle className="text-primary" size={20} />
                <h2 className="text-lg font-bold text-foreground tracking-tight">Drift & Oppgaver</h2>
            </div>

            {/* Quick Actions */}
            <div className="glass-card p-5">
                <h3 className="text-label mb-4">Snarveier</h3>
                <div className="space-y-2">
                    <Link href="/deviations" className="block w-full">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-surface hover:bg-muted/10 border border-border hover:border-primary transition-all text-left group cursor-pointer">
                            <span className="text-sm text-foreground font-bold">Nytt avvik</span>
                            <AlertOctagon size={16} className="text-amber-600 dark:text-amber-500 transition-transform group-hover:scale-110" />
                        </div>
                    </Link>
                    <Link href="/contracts" className="block w-full">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-surface hover:bg-muted/10 border border-border hover:border-primary transition-all text-left group cursor-pointer">
                            <span className="text-sm text-foreground font-bold">Ny kontrakt</span>
                            <FileCheck size={16} className="text-emerald-600 dark:text-emerald-500 transition-transform group-hover:scale-110" />
                        </div>
                    </Link>
                </div>
            </div>

            {/* Recent Activity / Log */}
            <div className="bg-surface border border-border rounded-xl flex-1 flex flex-col min-h-[300px] overflow-hidden">
                <div className="px-5 py-3 border-b border-border flex justify-between items-center bg-muted/5">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">Aktivitetslogg</h3>
                    <span className="text-[10px] font-bold text-muted uppercase tracking-wider">Siste 24t</span>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-32 text-slate-500 text-sm gap-2">
                            <Activity className="animate-spin" size={16} />
                            <span className="font-medium uppercase tracking-widest text-[10px]">Laster...</span>
                        </div>
                    ) : recentActivity.length === 0 ? (
                        <div className="p-8 text-center text-slate-500 text-sm">Ingen nylige hendelser.</div>
                    ) : (
                        <div className="divide-y divide-border/30">
                            {recentActivity.map((item, i) => {
                                const Icon = iconMap[item.icon] || Activity;
                                return (
                                    <div key={i} className="flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors group cursor-pointer">
                                        <div className={`p-1.5 rounded-md flex-shrink-0 ${item.type === 'deviation' ? 'bg-amber-500/10 text-amber-500' :
                                            item.type === 'contract' ? 'bg-blue-500/10 text-blue-500' :
                                                'bg-muted/10 text-muted'
                                            }`}>
                                            <Icon size={14} />
                                        </div>

                                        <div className="flex-1 min-w-0 flex justify-between items-center gap-4">
                                            <p className="text-sm text-foreground font-medium truncate">{item.text}</p>
                                            <span className="text-xs text-muted whitespace-nowrap font-mono">
                                                {new Date(item.time).toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
                <div className="p-2 border-t border-border bg-muted/5 text-center">
                    <Link href="/calendar" className="text-xs text-blue-400 hover:text-blue-300 font-bold uppercase tracking-wider transition-colors inline-flex items-center gap-1">
                        Se historikk <PlayCircle size={10} />
                    </Link>
                </div>
            </div>
        </div>
    );
}
