"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { importFinanceBudget, importKontant2026, type FinanceBudgetImportReport, type Kontant2026ImportReport } from "@/lib/api/financeBudgetApi";

function fmt(n: number) {
  return (n / 1e6).toFixed(1) + " MNOK";
}

export default function BudsjettImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<FinanceBudgetImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Kontant 2026
  const [file2026, setFile2026] = useState<File | null>(null);
  const [loading2026, setLoading2026] = useState(false);
  const [report2026, setReport2026] = useState<Kontant2026ImportReport | null>(null);
  const [error2026, setError2026] = useState<string | null>(null);
  const inputRef2026 = useRef<HTMLInputElement>(null);

  async function handleImport() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await importFinanceBudget(file);
      setReport(res.report);
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleImport2026() {
    if (!file2026) return;
    setLoading2026(true);
    setError2026(null);
    setReport2026(null);
    try {
      const res = await importKontant2026(file2026);
      setReport2026(res);
    } catch (e: any) {
      setError2026(e?.message ?? String(e));
    } finally {
      setLoading2026(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-10 px-4 space-y-8">
      <div className="flex items-center gap-3">
        <Link href="/admin" className="text-muted-foreground hover:text-foreground text-sm">← Admin</Link>
        <span className="text-muted-foreground">/</span>
        <span className="text-sm font-medium">Import økonomi-budsjett</span>
      </div>

      <div>
        <h1 className="text-2xl font-bold mb-1">Import økonomi-budsjett 2025 og 2026</h1>
        <p className="text-muted-foreground text-sm">
          Laster opp Excel-uttrekk fra Bufdir Økonomi. Importerer automatisk begge år.
          Eksisterende økonomi-budsjettdata overskrives (idempotent) — prediksjoner og GL røres ikke.
        </p>
      </div>

      {/* Forklaringsboks */}
      <div className="rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-700 p-4 text-sm space-y-2">
        <div className="font-semibold text-amber-800 dark:text-amber-300">Om beløpskolonnene i kildefilen</div>
        <div className="text-amber-900 dark:text-amber-200 space-y-1">
          <p>
            <span className="font-medium">Beløp DA</span> (disponeringsvedtak) = vedtatt budsjett for hele kalenderåret.
            Dekker alle 12 måneder — dette er kilden systemet bruker.
          </p>
          <p>
            <span className="font-medium">Kontantbeløp</span> = kontantbasert beløp, kun fylt for måneder som er passert
            frem til uttrekksdato. For et uttrekk fra april 2026 vil mai–desember stå som 0 i denne kolonnen.
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400">
            Systemet bruker alltid Beløp DA som primærkilde slik at 2026-budsjettet dekker hele året (535 MNOK),
            ikke bare jan–apr (226 MNOK).
          </p>
        </div>
      </div>

      {/* Filvalg */}
      <div className="glass-card p-6 space-y-4">
        <div
          className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); }}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) setFile(f);
          }}
        >
          {file ? (
            <div className="space-y-1">
              <div className="text-2xl">📊</div>
              <div className="font-medium">{file.name}</div>
              <div className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</div>
            </div>
          ) : (
            <div className="space-y-2 text-muted-foreground">
              <div className="text-3xl">📁</div>
              <div>Dra Excel-fil hit eller klikk for å velge</div>
              <div className="text-xs">Forventet: «2026-04-30 Uttrekk til eiendom - regnskap 25_budsjett 25 og 26.xlsx»</div>
            </div>
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }}
        />
        <button
          onClick={handleImport}
          disabled={!file || loading}
          className="w-full py-3 rounded-lg bg-primary text-primary-foreground font-semibold disabled:opacity-40 hover:opacity-90 transition-opacity"
        >
          {loading ? "Importerer…" : "Importer budsjett"}
        </button>
      </div>

      {/* Feil */}
      {error && (
        <div className="glass-card p-4 border-l-4 border-red-500 text-red-700 dark:text-red-300">
          <strong>Feil:</strong> {error}
        </div>
      )}

      {/* Rapport */}
      {report && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Import-rapport</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="glass-card p-4 border-l-4 border-emerald-500">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Importert</div>
              <div className="text-2xl font-bold">{report.inserted.toLocaleString("no-NO")}</div>
              <div className="text-xs text-muted-foreground">rader</div>
            </div>
            <div className="glass-card p-4 border-l-4 border-teal-500">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Eiendommer</div>
              <div className="text-2xl font-bold">{report.matched_properties.toLocaleString("no-NO")}</div>
              <div className="text-xs text-muted-foreground">matchet</div>
            </div>
            <div className="glass-card p-4 border-l-4 border-sky-500">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Budsjett 2025</div>
              <div className="text-xl font-bold">{fmt(report.total_2025_nok)}</div>
            </div>
            <div className="glass-card p-4 border-l-4 border-violet-500">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Budsjett 2026</div>
              <div className="text-xl font-bold">{fmt(report.total_2026_nok)}</div>
            </div>
          </div>

          {/* Hoppet over */}
          <div className="glass-card p-4 text-sm space-y-1">
            <div className="font-semibold mb-2">Hoppet over</div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-muted-foreground">
              <span>Mangler periode:</span><span className="font-mono text-right">{report.skipped.no_periode}</span>
              <span>Feil år:</span><span className="font-mono text-right">{report.skipped.wrong_year}</span>
              <span>Nullbeløp:</span><span className="font-mono text-right">{report.skipped.zero_amount}</span>
              <span>Ukjent konto:</span><span className="font-mono text-right">{report.skipped.unknown_konto}</span>
              <span>Direktorat-rader:</span><span className="font-mono text-right">{report.direktorat_rows}</span>
            </div>
          </div>

          {/* Umatchede koststeder */}
          {report.unmatched_koststeder_count > 0 && (
            <div className="glass-card p-4 text-sm">
              <div className="font-semibold mb-2 text-amber-600 dark:text-amber-400">
                {report.unmatched_koststeder_count} koststeder uten eiendoms-match (lagret som direktorat-rader)
              </div>
              <div className="max-h-40 overflow-y-auto space-y-0.5 text-muted-foreground font-mono text-xs">
                {report.unmatched_koststeder.map((k) => (
                  <div key={k}>{k}</div>
                ))}
                {report.unmatched_koststeder_count > report.unmatched_koststeder.length && (
                  <div className="text-muted-foreground">…og {report.unmatched_koststeder_count - report.unmatched_koststeder.length} til</div>
                )}
              </div>
            </div>
          )}

          <div className="text-sm text-muted-foreground">
            Du kan nå gå til{" "}
            <Link href="/financials" className="underline hover:text-foreground">
              Økonomi & Finansielle Analyser
            </Link>{" "}
            og velge 2026-fanen for å se sammenstillingen.
          </div>
        </div>
      )}

      {/* ── Kontant 2026 ─────────────────────────────────────────────────── */}
      <hr className="border-border" />
      <div>
        <h2 className="text-xl font-bold mb-1">Import kontantregnskap 2026 (jan–apr)</h2>
        <p className="text-muted-foreground text-sm">
          Laster opp økonomi sitt kontantregnskap for 2026. Importerer til{" "}
          <code className="bg-muted px-1 rounded text-xs">finance_budget</code> som{" "}
          <code className="bg-muted px-1 rounded text-xs">data_source = kontant_2026</code>.
          Vises i YTD-visning og dashboard-kortet «Bokførte kostnader 2026».
        </p>
        <p className="text-xs text-muted-foreground mt-1">Forventet fane i Excel: «Kontant 2026» (eller «Kontant»)</p>
      </div>

      <div className="glass-card p-6 space-y-4">
        <div
          className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
          onClick={() => inputRef2026.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) setFile2026(f);
          }}
        >
          {file2026 ? (
            <div className="space-y-1">
              <div className="text-2xl">📊</div>
              <div className="font-medium">{file2026.name}</div>
              <div className="text-sm text-muted-foreground">{(file2026.size / 1024).toFixed(0)} KB</div>
            </div>
          ) : (
            <div className="space-y-2 text-muted-foreground">
              <div className="text-3xl">📁</div>
              <div>Dra kontant 2026-fil hit eller klikk for å velge</div>
            </div>
          )}
        </div>
        <input
          ref={inputRef2026}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile2026(f); }}
        />
        <button
          onClick={handleImport2026}
          disabled={!file2026 || loading2026}
          className="w-full py-3 rounded-lg bg-primary text-primary-foreground font-semibold disabled:opacity-40 hover:opacity-90 transition-opacity"
        >
          {loading2026 ? "Importerer…" : "Importer kontant 2026"}
        </button>
      </div>

      {error2026 && (
        <div className="glass-card p-4 border-l-4 border-red-500 text-red-700 dark:text-red-300">
          <strong>Feil:</strong> {error2026}
        </div>
      )}

      {report2026 && (
        <div className="glass-card p-4 space-y-3">
          <h3 className="font-semibold text-emerald-700 dark:text-emerald-400">✅ Kontant 2026 importert</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div className="rounded-lg bg-muted p-3">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Importert</div>
              <div className="text-xl font-bold">{report2026.inserted.toLocaleString("no-NO")}</div>
              <div className="text-xs text-muted-foreground">rader</div>
            </div>
            <div className="rounded-lg bg-muted p-3">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Sum 2026</div>
              <div className="text-xl font-bold">{fmt(report2026.total_2026_nok)}</div>
            </div>
            <div className="rounded-lg bg-muted p-3">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Nullbeløp</div>
              <div className="text-xl font-bold">{report2026.skipped_zero_amount}</div>
              <div className="text-xs text-muted-foreground">hoppet over</div>
            </div>
            <div className="rounded-lg bg-muted p-3">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Uten match</div>
              <div className="text-xl font-bold">{report2026.unmatched_koststeder}</div>
              <div className="text-xs text-muted-foreground">koststeder</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
