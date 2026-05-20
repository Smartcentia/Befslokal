import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

interface AIInsightsWidgetProps {
    property: any;
}

export default function AIInsightsWidget({ property }: AIInsightsWidgetProps) {
    const insights = property?.external_data?.ai_insights || {};
    const { parking, responsibility, costs, deadlines } = insights;

    // If no data found for either, hide widget (return empty fragment/div to keep tree stable)
    if ((!parking?.found) && (!responsibility?.found) && (!costs?.found) && (!deadlines?.found)) {
        return <div className="hidden" />;
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/5 to-purple-500/5 border border-border p-6 backdrop-blur-xl"
        >
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity">
                <svg className="w-24 h-24 text-primary" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" /></svg>
            </div>

            <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-xl shrink-0 border border-primary/20 shadow-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                        <path d="M8 21v-8a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v8" />
                        <path d="M16 3l3.5 3.5 1.5-1.5" />
                    </svg>
                </div>

                <div className="space-y-6 flex-1">
                    <div>
                        <h3 className="text-lg font-bold text-transparent bg-clip-text bg-linear-to-r from-primary to-purple-600 flex items-center gap-2">
                            AI-Assistert Analyse
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 uppercase tracking-widest">
                                BETA
                            </span>
                        </h3>
                        <p className="text-xs text-primary/60 uppercase tracking-wide font-bold mt-1">
                            Funnet i dokumentstruktur
                        </p>
                    </div>

                    {/* Parking Section */}
                    {parking?.found && (
                        <div className="bg-surface/50 rounded-xl p-4 border border-border space-y-3 shadow-sm">
                            <div className="flex justify-between items-start border-b border-border pb-3">
                                <div>
                                    <div className="text-label text-muted mb-1">Parkering</div>
                                    <div className="text-sm font-bold text-foreground">{parking.summary}</div>
                                </div>
                                <div className="text-right">
                                    <div className="text-label text-muted mb-1">Kostnad</div>
                                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{parking.cost}</div>
                                </div>
                            </div>

                            <div className="flex justify-between items-center text-xs">
                                <div className="flex items-center gap-1.5 text-muted">
                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span className="font-medium">Kilde:
                                        {parking.source_contract_id ? (
                                            <Link href={`/contracts/${parking.source_contract_id}`} className="text-primary italic hover:underline ml-1 font-bold">
                                                {parking.source_file}
                                            </Link>
                                        ) : (
                                            <span className="text-muted-foreground italic ml-1 font-bold">{parking.source_file}</span>
                                        )}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-muted/10 text-muted border border-border font-bold uppercase text-[10px]">
                                    <div className={`w-1.5 h-1.5 rounded-full ${parking.coverage === 'Inkludert' ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
                                    <span>{parking.coverage}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Responsibility Section */}
                    {responsibility?.found && (
                        <div className="bg-surface/50 rounded-xl p-4 border border-border space-y-3 relative overflow-hidden shadow-sm">
                            {/* Ambient background effect */}
                            <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 blur-3xl pointer-events-none"></div>

                            <div className="flex justify-between items-start border-b border-border pb-3">
                                <div className="flex-1">
                                    <div className="text-label text-muted mb-1 flex items-center gap-2">
                                        <svg className="w-3 h-3 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                        Ansvarsfordeling
                                    </div>
                                    <div className="text-sm font-bold text-foreground leading-relaxed mb-4">{responsibility.summary}</div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <span className="text-[10px] font-extrabold text-muted uppercase flex items-center gap-1 tracking-widest">
                                                <div className="w-1 h-1 bg-destructive rounded-full"></div> Leietaker
                                            </span>
                                            <ul className="text-xs space-y-1 text-muted-foreground">
                                                {responsibility.tenant?.map((item: string, i: number) => (
                                                    <li key={i} className="flex items-start gap-1.5 font-medium">
                                                        <span className="text-destructive/50 mt-0.5">•</span> {item}
                                                    </li>
                                                ))}
                                                {(!responsibility.tenant || responsibility.tenant.length === 0) && <li className="opacity-50">-</li>}
                                            </ul>
                                        </div>
                                        <div className="space-y-2">
                                            <span className="text-[10px] font-extrabold text-muted uppercase flex items-center gap-1 tracking-widest">
                                                <div className="w-1 h-1 bg-emerald-500 rounded-full"></div> Utleier
                                            </span>
                                            <ul className="text-xs space-y-1 text-muted-foreground">
                                                {responsibility.landlord?.map((item: string, i: number) => (
                                                    <li key={i} className="flex items-start gap-1.5 font-medium">
                                                        <span className="text-emerald-500/50 mt-0.5">•</span> {item}
                                                    </li>
                                                ))}
                                                {(!responsibility.landlord || responsibility.landlord.length === 0) && <li className="opacity-50">-</li>}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-between items-center text-xs mt-2">
                                <div className="flex items-center gap-1.5 text-muted">
                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span className="font-medium">Kilde:
                                        {responsibility.source_contract_id ? (
                                            <Link href={`/contracts/${responsibility.source_contract_id}`} className="text-primary italic hover:underline ml-1 font-bold">
                                                {responsibility.source_file}
                                            </Link>
                                        ) : (
                                            <span className="text-muted-foreground italic ml-1 font-bold">{responsibility.source_file}</span>
                                        )}
                                    </span>
                                </div>

                                {responsibility.snow && (
                                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-muted/10 text-muted border border-border font-bold uppercase text-[10px]">
                                        <span className="opacity-70">Snømåking:</span>
                                        <span className={`${responsibility.snow === 'Leietaker' ? 'text-destructive' : 'text-emerald-600 dark:text-emerald-400'}`}>{responsibility.snow}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    {/* Cost Section */}
                    {insights.costs?.found && (
                        <div className="bg-surface/50 rounded-xl p-4 border border-border space-y-3 relative overflow-hidden shadow-sm">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 blur-3xl pointer-events-none"></div>

                            <div className="flex justify-between items-start border-b border-border pb-3">
                                <div>
                                    <div className="text-label text-muted mb-1 flex items-center gap-2">
                                        <svg className="w-3 h-3 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        Kostnader & Energi
                                    </div>
                                    <div className="text-sm font-bold text-foreground max-w-md">{insights.costs.summary}</div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-xs">
                                <div className="bg-muted/10 p-2 rounded-lg border border-border">
                                    <span className="block text-[10px] text-muted uppercase font-extrabold mb-1">Strøm</span>
                                    <span className="font-bold text-foreground uppercase tracking-tight">{insights.costs.electricity}</span>
                                </div>
                                <div className="bg-muted/10 p-2 rounded-lg border border-border">
                                    <span className="block text-[10px] text-muted uppercase font-extrabold mb-1">Felleskost.</span>
                                    <span className="font-bold text-foreground uppercase tracking-tight">{insights.costs.common_costs}</span>
                                </div>
                                <div className="bg-muted/10 p-2 rounded-lg border border-border">
                                    <span className="block text-[10px] text-muted uppercase font-extrabold mb-1">Oppvarming</span>
                                    <span className="font-bold text-foreground uppercase tracking-tight">{insights.costs.heating}</span>
                                </div>
                                <div className="bg-muted/10 p-2 rounded-lg border border-border flex items-center">
                                    <span className="text-gray-400 italic font-bold text-[10px] uppercase">
                                        + {insights.costs.details?.length || 0} poster
                                    </span>
                                </div>
                            </div>

                            <div className="flex justify-end text-xs pt-2">
                                <div className="flex items-center gap-1.5 text-muted">
                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span className="font-medium">Kilde:
                                        {insights.costs.source_contract_id ? (
                                            <Link href={`/contracts/${insights.costs.source_contract_id}`} className="text-primary italic hover:underline ml-1 font-bold">
                                                {insights.costs.source_file}
                                            </Link>
                                        ) : (
                                            <span className="text-muted-foreground italic ml-1 font-bold">{insights.costs.source_file}</span>
                                        )}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                    {/* Deadline Section */}
                    {insights.deadlines?.found && (
                        <div className="bg-surface/50 rounded-xl p-4 border border-border space-y-3 relative overflow-hidden shadow-sm">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl pointer-events-none"></div>

                            <div className="flex justify-between items-start border-b border-border pb-3">
                                <div>
                                    <div className="text-label text-muted mb-1 flex items-center gap-2">
                                        <svg className="w-3 h-3 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                        Frister & Opsjoner
                                    </div>
                                    <div className="text-sm font-bold text-foreground max-w-md">{insights.deadlines.summary}</div>
                                </div>
                            </div>

                            <div className="flex flex-col gap-2 text-xs">
                                <div className="flex justify-between items-center bg-muted/10 p-2 rounded-lg border border-border">
                                    <span className="text-muted font-bold uppercase text-[10px]">Neste Regulering</span>
                                    <span className="font-bold text-foreground uppercase truncate ml-2">{insights.deadlines.next_regulation}</span>
                                </div>
                                <div className="flex justify-between items-center bg-muted/10 p-2 rounded-lg border border-border">
                                    <span className="text-muted font-bold uppercase text-[10px]">Oppsigelsestid</span>
                                    <span className="font-bold text-foreground uppercase truncate ml-2">{insights.deadlines.notice_period}</span>
                                </div>
                                <div className="flex justify-between items-center bg-blue-50/50 dark:bg-blue-500/10 p-2 rounded-lg border border-blue-200 dark:border-blue-500/20">
                                    <span className="text-blue-700 dark:text-slate-400 font-bold uppercase text-[10px]">Opsjonsfrist</span>
                                    <span className="font-extrabold text-blue-600 dark:text-blue-300 uppercase truncate ml-2">{insights.deadlines.option_deadline}</span>
                                </div>
                            </div>

                            <div className="flex justify-end text-xs pt-2">
                                <div className="flex items-center gap-1.5 text-muted font-medium">
                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    <span>Kilde:
                                        {insights.deadlines.source_contract_id ? (
                                            <Link href={`/contracts/${insights.deadlines.source_contract_id}`} className="text-primary italic hover:underline ml-1 font-bold">
                                                {insights.deadlines.source_file}
                                            </Link>
                                        ) : (
                                            <span className="text-muted-foreground italic ml-1 font-bold">{insights.deadlines.source_file}</span>
                                        )}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
