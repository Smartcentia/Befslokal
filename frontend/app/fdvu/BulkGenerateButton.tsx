"use client";

import { useState } from "react";
import { Zap } from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

interface BulkResult {
    properties_processed: number;
    properties_with_new_assignments: number;
    total_created: number;
    total_skipped_existing: number;
    total_skipped_rule: number;
}

export default function BulkGenerateButton() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<BulkResult | null>(null);

    const handleClick = async () => {
        if (!confirm("Auto-tildel krav for alle aktive eiendommer? Eksisterende tildelinger beholdes.")) return;
        setLoading(true);
        setResult(null);
        try {
            const r = await fetchAPI<BulkResult>("/fdvu/assignments/auto-generate-all", { method: "POST" });
            setResult(r);
            setTimeout(() => window.location.reload(), 1500);
        } catch (e) {
            alert(e instanceof Error ? e.message : "Feil ved auto-tildeling");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center gap-3">
            <button
                onClick={handleClick}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
                <Zap size={14} />
                {loading ? "Tildeler …" : "Auto-tildel alle eiendommer"}
            </button>
            {result && (
                <span className="text-xs text-success">
                    ✓ {result.total_created} nye tildelinger for {result.properties_with_new_assignments} eiendommer
                </span>
            )}
        </div>
    );
}
