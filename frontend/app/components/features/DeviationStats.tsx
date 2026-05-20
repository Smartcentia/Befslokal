import { Activity, AlertTriangle, CheckCircle, Clock } from "lucide-react";

interface DeviationStatsData {
    total: number;
    open: number;
    closed: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
}

interface DeviationStatsProps {
    stats: DeviationStatsData;
}

export default function DeviationStats({ stats }: DeviationStatsProps) {
    if (!stats) return null;

    const cards = [
        {
            title: "Totalt Antall",
            value: stats.total,
            subtext: "Registrerte avvik",
            icon: <Activity className="text-blue-600" size={24} />,
            bg: "bg-blue-50",
            border: "border-blue-200"
        },
        {
            title: "Åpne Avvik",
            value: stats.open,
            subtext: "Krever oppfølging",
            icon: <Clock className="text-orange-600" size={24} />,
            bg: "bg-orange-50",
            border: "border-orange-200"
        },
        {
            title: "Lukket",
            value: stats.closed,
            subtext: "Ferdigbehandlet",
            icon: <CheckCircle className="text-green-600" size={24} />,
            bg: "bg-green-50",
            border: "border-green-200"
        },
        {
            title: "Kritiske",
            value: stats.critical,
            subtext: "Høy prioritet",
            icon: <AlertTriangle className="text-red-600" size={24} />,
            bg: "bg-red-50",
            border: "border-red-200"
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {cards.map((card, idx) => (
                <div
                    key={idx}
                    className={`p-6 rounded-xl border bg-surface shadow-sm ${card.border}`}
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
    );
}
