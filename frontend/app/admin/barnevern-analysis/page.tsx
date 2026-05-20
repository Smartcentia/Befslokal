"use client";

import { useEffect, useState } from "react";
import {
  getBarnevernReportsAnalysis,
  regenerateBarnevernReportsAnalysis,
  type BarnevernReportsAnalysis,
} from "@/lib/api/barnevernDocsApi";

export default function BarnevernAnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<BarnevernReportsAnalysis | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getBarnevernReportsAnalysis();
        setAnalysis(data);
      } catch (e: any) {
        setError(e?.message ?? "Kunne ikke hente analyse.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <main className="p-6">Laster analyse...</main>;
  if (error) return <main className="p-6 text-red-500">{error}</main>;
  if (!analysis) return <main className="p-6">Ingen analyse tilgjengelig.</main>;

  async function regenerate() {
    setRegenerating(true);
    setError(null);
    try {
      const res = await regenerateBarnevernReportsAnalysis();
      setAnalysis(res.analysis);
    } catch (e: any) {
      setError(e?.message ?? "Kunne ikke regenerere analyse.");
    } finally {
      setRegenerating(false);
    }
  }

  return (
    <main className="p-6 space-y-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Analysepresentasjon: Bufdir/Bufetat-rapporter</h1>
        <button
          type="button"
          onClick={regenerate}
          disabled={regenerating}
          className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-60 text-white text-sm font-medium"
        >
          {regenerating ? "Regenererer..." : "Regenerer analyse"}
        </button>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border rounded-lg p-4">
          <div className="text-xs text-muted-foreground">St.prp./Prop</div>
          <div className="text-2xl font-bold">{analysis.summary.stprp_count}</div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-xs text-muted-foreground">Årsrapporter (totalt)</div>
          <div className="text-2xl font-bold">{analysis.summary.annual_report_total}</div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-xs text-muted-foreground">Årsrapporter med PDF</div>
          <div className="text-2xl font-bold">{analysis.summary.annual_report_pdf_count}</div>
        </div>
        <div className="border rounded-lg p-4">
          <div className="text-xs text-muted-foreground">SSB tabeller</div>
          <div className="text-2xl font-bold">{analysis.summary.ssb_table_count}</div>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Hovedfunn</h2>
        <ul className="list-disc pl-6 space-y-2">
          {analysis.highlights.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Risiko og gap</h2>
        <ul className="list-disc pl-6 space-y-2">
          {analysis.risks.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Anbefalte tiltak</h2>
        <ul className="list-disc pl-6 space-y-2">
          {analysis.recommended_actions.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
