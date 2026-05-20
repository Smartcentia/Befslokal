import { Deviation } from "@/lib/domains/fdv/deviationService";
import Link from "next/link";
import { AlertTriangle, Clock, MapPin } from "lucide-react";

// Inline helper components
function SeverityBadge({ severity }: { severity: string }) {
    const isHigh = severity?.toLowerCase() === 'high' || severity?.toLowerCase() === 'critical';
    const isMedium = severity?.toLowerCase() === 'medium';

    let label = 'Ukjent';
    if (isHigh) label = 'Høy';
    else if (isMedium) label = 'Middels';
    else if (severity?.toLowerCase() === 'low') label = 'Lav';

    return (
        <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${isHigh ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
            isMedium ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                'bg-blue-500/20 text-blue-400 border border-blue-500/30'
            }`}>
            {label}
        </span>
    );
}

function StatusBadge({ status }: { status: string }) {
    const isOpen = status?.toLowerCase() === 'open';
    return (
        <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${isOpen ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/30' :
            'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-400 border border-gray-200 dark:border-slate-600'
            }`}>
            {status === 'open' ? 'Åpen' : 'Lukket'}
        </span>
    );
}

export default function DeviationList({ deviations, onSelect }: { deviations: Deviation[]; onSelect: (d: Deviation) => void }) {
    if (!deviations || deviations.length === 0) {
        return (
            <div className="text-center p-8 bg-surface rounded-xl border border-dashed border-border">
                <p className="text-muted">Ingen avvik funnet.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 gap-4">
            {deviations.map((deviation) => (
                <div
                    key={deviation.id}
                    onClick={() => onSelect(deviation)}
                    className="group bg-surface p-5 rounded-xl border border-border shadow-sm hover:shadow-md transition-all hover:border-primary/50 hover:bg-muted/5 relative overflow-hidden cursor-pointer"
                >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-lg transition-colors ${deviation.id === 'new' ? 'bg-red-500/10 text-red-500 group-hover:bg-red-500 group-hover:text-white' : 'bg-muted/50 text-muted'
                                }`}>
                                <AlertTriangle size={24} />
                            </div>
                            <div>
                                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                    {deviation.property_name || "Ukjent Eiendom"}
                                </h3>
                                <p className="text-muted-foreground text-sm mt-0.5 line-clamp-2">
                                    {deviation.title || "Uten tittel"}
                                </p>
                                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-muted">
                                    <div className="flex items-center gap-1">
                                        <Clock size={12} />
                                        <span>
                                            {deviation.created_at ? new Date(deviation.created_at).toLocaleDateString('no-NO') : '-'}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <MapPin size={12} />
                                        <span>Lokasjon spesifisert</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                            <div className="flex gap-2">
                                <SeverityBadge severity={deviation.severity} />
                                <StatusBadge status={deviation.status} />
                            </div>
                            <span className="text-muted group-hover:translate-x-1 transition-transform">→</span>
                        </div>
                    </div>
                </div>
            ))
            }
        </div >
    );
}
