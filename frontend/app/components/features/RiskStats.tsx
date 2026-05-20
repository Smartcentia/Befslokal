import { RiskStats } from "@/lib/api";
import { Activity, AlertTriangle, ShieldCheck, TrendingUp } from "lucide-react";
import Link from "next/link";

interface RiskStatsViewProps {
    stats: RiskStats;
    onFilterChange: (filter: string | null) => void;
    activeFilter: string | null;
}

export default function RiskStatsView({ stats, onFilterChange, activeFilter }: RiskStatsViewProps) {
    if (!stats) return null;

    const cards = [
        {
            key: 'avg_score',
            title: "Gjennomsnittlig Risiko",
            value: (stats.avg_score ?? 0).toFixed(1),
            subtext: "Skala 1-5",
            icon: <Activity className="text-blue-600" size={24} />,
            bg: "bg-blue-50",
            border: "border-blue-200"
        },
        {
            key: 'critical',
            title: "Kritiske Avvik",
            value: stats.count_critical_deviations ?? stats.count_critical ?? 0,
            subtext: "Krever umiddelbar tiltak",
            icon: <AlertTriangle className="text-red-600" size={24} />,
            bg: "bg-red-50",
            border: "border-red-200"
        },
        {
            key: 'total',
            title: "Total Vurderinger",
            value: stats.total_assessments,
            subtext: "Registrerte siste periode",
            icon: <ShieldCheck className="text-indigo-600" size={24} />,
            bg: "bg-indigo-50",
            border: "border-indigo-200"
        },
        {
            key: 'high_risk',
            title: "Høy Risiko",
            value: stats.count_high,
            subtext: "Eiendommer med høy risiko",
            icon: <TrendingUp className="text-orange-600" size={24} />,
            bg: "bg-orange-50",
            border: "border-orange-200"
        }
    ];

    return (
        <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold bg-linear-to-r from-primary to-accent bg-clip-text text-transparent">Risikoanalyse</h2>
                    <p className="text-muted text-sm">Sanntidsvurdering av risiko basert på NVE-data, kontraktsstatus og avvik.</p>
                </div>
                <Link href="/risk" className="text-sm font-medium text-primary hover:underline flex items-center gap-1">
                    Se hele risikobildet <TrendingUp size={14} />
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {cards.map((card, idx) => (
                    <div
                        key={idx}
                        onClick={() => onFilterChange(activeFilter === card.key ? null : card.key)}
                        className={`
                            p-6 rounded-xl border bg-surface shadow-sm transition-all duration-200
                            ${card.key !== 'avg_score' && card.key !== 'total' ? 'cursor-pointer hover:shadow-md hover:border-primary/50 hover:-translate-y-1' : ''}
                            ${activeFilter === card.key ? 'ring-2 ring-primary border-transparent shadow-lg shadow-primary/10' : 'border-border'}
                        `}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${card.bg.replace('50', '500/10')}`}>
                                {card.icon}
                            </div>
                            <span className="text-3xl font-bold text-foreground">{card.value}</span>
                        </div>
                        <h3 className="font-semibold text-foreground">{card.title}</h3>
                        <p className="text-sm text-muted mt-1">{card.subtext}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
