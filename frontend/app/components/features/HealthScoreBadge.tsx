"use client";

import React from "react";

export interface HealthScore {
    score: 1 | 2 | 3 | 4;
    label: "GRØNN" | "GUL" | "ORANSJE" | "RØD";
    emoji: string;
    category: string;
    factors: string[];
    data_sources: string[];
    data_quality: "høy" | "middels" | "lav" | "no_data";
}

const SCORE_STYLES: Record<number, { bg: string; border: string; text: string; ring: string; dot: string }> = {
    1: {
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        text: "text-emerald-700 dark:text-emerald-400",
        ring: "ring-emerald-500/20",
        dot: "bg-emerald-500",
    },
    2: {
        bg: "bg-yellow-500/10",
        border: "border-yellow-500/30",
        text: "text-yellow-700 dark:text-yellow-400",
        ring: "ring-yellow-500/20",
        dot: "bg-yellow-500",
    },
    3: {
        bg: "bg-orange-500/10",
        border: "border-orange-500/30",
        text: "text-orange-700 dark:text-orange-400",
        ring: "ring-orange-500/20",
        dot: "bg-orange-500",
    },
    4: {
        bg: "bg-red-500/10",
        border: "border-red-500/30",
        text: "text-red-700 dark:text-red-400",
        ring: "ring-red-500/20",
        dot: "bg-red-500",
    },
};

/** Compact inline badge – for use in cards and lists */
export function HealthScoreBadge({
    score,
    showLabel = true,
    showTooltip = true,
}: {
    score: HealthScore | null | undefined;
    showLabel?: boolean;
    showTooltip?: boolean;
}) {
    if (!score) return null;
    const s = SCORE_STYLES[score.score] ?? SCORE_STYLES[1];
    const tooltip = showTooltip && score.factors.length > 0
        ? score.factors.join(" · ")
        : undefined;

    return (
        <span
            title={tooltip}
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold border ${s.bg} ${s.border} ${s.text}`}
        >
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.dot}`} />
            {score.emoji}
            {showLabel && <span className="tracking-wider">{score.label}</span>}
        </span>
    );
}

/** Full card widget – for use on detail pages */
export function HealthScoreCard({ score }: { score: HealthScore | null | undefined }) {
    if (!score) return null;
    const s = SCORE_STYLES[score.score] ?? SCORE_STYLES[1];

    const sourceLabels: Record<string, string> = {
        konkurs_sjekk: "Konkursregisteret",
        brreg: "Brønnøysund",
        due_diligence: "Due Diligence",
        regnskap: "Årsregnskap",
    };

    return (
        <div className={`rounded-xl border p-5 ${s.bg} ${s.border}`}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${s.dot}`} />
                    <span className={`font-bold text-sm ${s.text}`}>
                        {score.emoji} Leverandør-score: {score.label}
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    {[1, 2, 3, 4].map((n) => (
                        <span
                            key={n}
                            className={`w-5 h-2 rounded-sm ${n <= score.score ? s.dot : "bg-muted-foreground/20"}`}
                        />
                    ))}
                </div>
            </div>

            <p className={`text-xs mb-3 ${s.text} opacity-80`}>{score.category}</p>

            {score.factors.length > 0 && (
                <ul className={`text-xs space-y-1 mb-3 ${s.text}`}>
                    {score.factors.map((f, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                            <span className="mt-0.5 opacity-60">•</span>
                            <span>{f}</span>
                        </li>
                    ))}
                </ul>
            )}

            {score.data_sources.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-current/10">
                    <span className="text-[10px] opacity-50 mr-1">Kilder:</span>
                    {score.data_sources.map((src) => (
                        <span
                            key={src}
                            className={`text-[10px] px-1.5 py-0.5 rounded border ${s.border} opacity-70`}
                        >
                            {sourceLabels[src] ?? src}
                        </span>
                    ))}
                    <span className={`ml-auto text-[10px] opacity-50`}>
                        Datakvalitet: {score.data_quality}
                    </span>
                </div>
            )}
        </div>
    );
}

/** Micro dot indicator – for compact table rows */
export function HealthScoreDot({ score }: { score: HealthScore | null | undefined }) {
    if (!score) return <span className="w-2 h-2 rounded-full bg-muted-foreground/20 inline-block" />;
    const s = SCORE_STYLES[score.score] ?? SCORE_STYLES[1];
    return (
        <span
            title={`${score.label}${score.factors.length > 0 ? ": " + score.factors[0] : ""}`}
            className={`w-2.5 h-2.5 rounded-full inline-block ring-2 ${s.dot} ${s.ring}`}
        />
    );
}
