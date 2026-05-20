"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, Building, ArrowRight } from 'lucide-react';

interface RiskDetailsTableProps {
    type: 'properties' | 'deviations';
    data: any[];
    loading: boolean;
    onClose: () => void;
}

export default function RiskDetailsTable({ type, data, loading, onClose }: RiskDetailsTableProps) {
    const router = useRouter();

    if (loading) return <div className="p-8 text-center text-slate-400 animate-pulse">Laster detaljer...</div>;

    const title = type === 'properties' ? 'Eiendommer med Høy Risiko' : 'Kritiske Avvik';
    const subtext = type === 'properties'
        ? 'Disse eiendommene har en risikoscore på 4 eller 5.'
        : 'Avvik som krever umiddelbar oppmerksomhet.';

    return (
        <div className="mt-8 bg-surface rounded-xl border border-border overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="p-6 border-b border-border flex justify-between items-start">
                <div>
                    <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                        {type === 'properties' ? <Building className="text-orange-500" /> : <AlertTriangle className="text-red-500" />}
                        {title}
                    </h2>
                    <p className="text-muted text-sm mt-1">{subtext}</p>
                </div>
                <button
                    onClick={onClose}
                    className="text-muted hover:text-foreground px-3 py-1 rounded hover:bg-muted/10 transition"
                >
                    Lukk
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-background text-muted text-sm uppercase tracking-wider">
                        <tr>
                            <th className="p-4 border-b border-border">Navn / Tittel</th>
                            {type === 'properties' ? (
                                <>
                                    <th className="p-4 border-b border-border">Adresse</th>
                                    <th className="p-4 border-b border-border">Bruk</th>
                                </>
                            ) : (
                                <>
                                    <th className="p-4 border-b border-border">Eiendom</th>
                                    <th className="p-4 border-b border-border">Frist</th>
                                </>
                            )}
                            <th className="p-4 border-b border-border">Status / Risiko</th>
                            <th className="p-4 border-b border-border">Handling</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border text-muted text-sm">
                        {data.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="p-8 text-center text-muted">
                                    Ingen data funnet.
                                </td>
                            </tr>
                        ) : (
                            data.map((item: any, idx: number) => (
                                <tr key={idx} className="hover:bg-muted/5 transition-colors">
                                    <td className="p-4 font-medium text-foreground">
                                        {type === 'properties' ? item.name || "Ukjent navn" : item.title}
                                    </td>

                                    {type === 'properties' ? (
                                        <>
                                            <td className="p-4 text-muted">{item.address}</td>
                                            <td className="p-4 text-muted">{item.usage?.toLowerCase() === 'barnevernsinstitusjon' ? 'Formålsbygg' : (item.usage || "-")}</td>
                                        </>
                                    ) : (
                                        <>
                                            <td className="p-4 text-muted">{item.property_id ? "Se detaljer..." : "Ukjent eiendom"}</td>
                                            <td className="p-4 text-muted">
                                                {item.due_date ? new Date(item.due_date).toLocaleDateString() : "-"}
                                            </td>
                                        </>
                                    )}

                                    <td className="p-4">
                                        {type === 'properties' ? (
                                            <span className="px-2 py-1 bg-orange-500/10 text-orange-400 rounded border border-orange-500/20 text-xs font-bold">
                                                HØY RISIKO
                                            </span>
                                        ) : (
                                            <span className="px-2 py-1 bg-red-500/10 text-red-400 rounded border border-red-500/20 text-xs font-bold">
                                                KRITISK
                                            </span>
                                        )}
                                    </td>

                                    <td className="p-4">
                                        <button
                                            onClick={() => {
                                                if (type === 'properties') router.push(`/properties/${item.property_id}`);
                                                else router.push(`/checklists?case_id=${item.case_id}`);
                                            }}
                                            className="text-blue-500 hover:text-blue-400 flex items-center gap-1 font-medium text-xs hover:underline"
                                        >
                                            Gå til {type === 'properties' ? 'eiendom' : 'sak'} <ArrowRight size={12} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {data.length > 5 && (
                <div className="p-4 bg-background text-center border-t border-border">
                    <button className="text-muted hover:text-foreground text-xs">Vis alle...</button>
                </div>
            )}
        </div>
    );
}
