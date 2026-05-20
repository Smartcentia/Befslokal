"use client";
import React, { useState } from "react";
import { Loader2 } from "lucide-react";
import { combineSSBBefs, type SSBTable, type SSBCombineRequest } from "@/lib/api/ssbApi";

interface Props {
    selectedTable: SSBTable | null;
}

export default function SSBCombinePanel({ selectedTable }: Props) {
    const [befsDataset, setBefsDataset] = useState<SSBCombineRequest["befs_dataset"]>("region_costs");
    const [joinKey, setJoinKey] = useState<SSBCombineRequest["join_key"]>("region");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<unknown>(null);
    const [error, setError] = useState<string | null>(null);

    const handleCombine = async () => {
        if (!selectedTable) return;
        setLoading(true);
        setError(null);
        try {
            const res = await combineSSBBefs({
                table_id: selectedTable.id,
                befs_dataset: befsDataset,
                join_key: joinKey,
            });
            setResult(res);
        } catch {
            setError("Kunne ikke kombinere data.");
        } finally {
            setLoading(false);
        }
    };

    if (!selectedTable) {
        return <p className="text-muted">Velg en SSB-tabell fra søk-fanen først.</p>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h3 className="font-semibold text-foreground mb-1">{selectedTable.label}</h3>
                <p className="text-sm text-muted">Tabell {selectedTable.id}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs text-muted mb-1">BEFS datasett</label>
                    <select
                        value={befsDataset}
                        onChange={(e) => setBefsDataset(e.target.value as SSBCombineRequest["befs_dataset"])}
                        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                    >
                        <option value="region_costs">Regionkostnader</option>
                        <option value="properties">Eiendommer</option>
                        <option value="contracts">Kontrakter</option>
                    </select>
                </div>
                <div>
                    <label className="block text-xs text-muted mb-1">Koblingsnøkkel</label>
                    <select
                        value={joinKey}
                        onChange={(e) => setJoinKey(e.target.value as SSBCombineRequest["join_key"])}
                        className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                    >
                        <option value="region">Region</option>
                        <option value="kommune">Kommune</option>
                        <option value="year">År</option>
                    </select>
                </div>
            </div>

            <button
                type="button"
                onClick={handleCombine}
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 rounded-xl bg-primary text-primary-foreground font-medium hover:opacity-90 disabled:opacity-50"
            >
                {loading && <Loader2 size={16} className="animate-spin" />}
                Kombiner data
            </button>

            {error && <p className="text-sm text-destructive">{error}</p>}

            {result && (
                <div className="rounded-xl border border-border bg-muted/20 p-4 overflow-auto max-h-72">
                    <pre className="text-xs text-muted whitespace-pre-wrap break-all">
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
