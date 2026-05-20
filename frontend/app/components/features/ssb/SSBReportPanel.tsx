"use client";

import React, { useMemo } from "react";
import { FileBarChart } from "lucide-react";
import {
    isJsonStatLike,
    flattenJsonStat2,
    summarizeNumericValues,
} from "@/lib/ssb/jsonStatParse";

interface Props {
    data: unknown;
    tableLabel?: string;
}

export default function SSBReportPanel({ data, tableLabel }: Props) {
    const brief = useMemo(() => {
        if (!data || !isJsonStatLike(data)) return null;
        try {
            const flat = flattenJsonStat2(data, { maxRows: 12000 });
            const stats = summarizeNumericValues(flat.rows, flat.valueKey);
            return { flat, stats };
        } catch {
            return null;
        }
    }, [data]);

    if (!data) {
        return (
            <p className="text-muted">
                Hent data fra «Hent data»-fanen for å lage rapport og analyse.
            </p>
        );
    }

    if (!brief) {
        return (
            <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                    Rapport krever json-stat2-data. Gå til «Hent data» og hent på nytt, eller
                    bruk rå visning under.
                </p>
                <div className="rounded-xl border border-border bg-muted/20 p-4 overflow-auto max-h-64">
                    <pre className="text-xs text-muted whitespace-pre-wrap break-all">
                        {typeof data === "string"
                            ? data
                            : JSON.stringify(data, null, 2)}
                    </pre>
                </div>
            </div>
        );
    }

    const { flat, stats } = brief;
    const mean =
        stats && stats.count > 0 ? stats.sum / stats.count : null;

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2">
                <FileBarChart size={18} className="text-primary" />
                <h3 className="font-semibold text-foreground">
                    Kort analyse: {tableLabel ?? flat.datasetLabel ?? "SSB-data"}
                </h3>
            </div>

            <ul className="list-disc pl-5 text-sm text-foreground space-y-1.5">
                <li>
                    <strong>{flat.rowCount}</strong> observasjoner i datasettet (etter
                    utfolding av dimensjoner).
                </li>
                <li>
                    Variabler:{" "}
                    <span className="font-medium">
                        {flat.dimensions.map((d) => d.label).join(" · ")}
                    </span>
                    .
                </li>
                {stats && (
                    <>
                        <li>
                            Tallverdi: min <strong>{stats.min.toLocaleString("nb-NO")}</strong>,
                            maks <strong>{stats.max.toLocaleString("nb-NO")}</strong>, gjennomsnitt{" "}
                            <strong>
                                {mean !== null
                                    ? mean.toLocaleString("nb-NO", { maximumFractionDigits: 2 })
                                    : "–"}
                            </strong>{" "}
                            (over {stats.count} numeriske celleverdier).
                        </li>
                    </>
                )}
                {flat.truncated && (
                    <li className="text-amber-800 dark:text-amber-200">
                        Store tabeller er avkortet til {flat.maxRows} rader i minnet – eksporter
                        CSV fra «Hent data» for full detalj.
                    </li>
                )}
            </ul>

            <p className="text-sm text-muted-foreground">
                Bruk fanen «Hent data» for tabell, diagram og CSV-eksport. Her er et tekstlig
                sammendrag egnet for utskrift eller videre notater.
            </p>
        </div>
    );
}
