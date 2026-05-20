"use client";
/**
 * OmposteringModal
 *
 * Wizard for å ompostere en GL-transaksjon til nytt koststed.
 * Prinsipp: originalbilag røres aldri – oppretter to H1-linjer.
 *
 * Bruk:
 *   <OmposteringModal
 *     transaction={{ transaction_id, bilagsnr, belop, dim1_kode, dim1_navn, tekst, konto }}
 *     onClose={() => setOpen(false)}
 *     onSuccess={(result) => { refetch(); }}
 *   />
 */

import React, { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface GLTransactionMini {
  transaction_id: string;
  bilagsnr?: string | null;
  belop: number;
  dim1_kode?: string | null;
  dim1_navn?: string | null;
  tekst?: string | null;
  konto?: string | null;
  konto_navn?: string | null;
  leverandor_navn?: string | null;
}

interface OmposteringResult {
  status: string;
  original_transaction_id: string;
  gammelt_koststed: { kode: string; navn: string | null };
  nytt_koststed: { kode: string; navn: string | null };
  reversering_id: string;
  ny_postering_id: string;
  utfort_av: string;
  tidspunkt: string;
}

interface Props {
  transaction: GLTransactionMini;
  onClose: () => void;
  onSuccess?: (result: OmposteringResult) => void;
}

export default function OmposteringModal({ transaction, onClose, onSuccess }: Props) {
  const [nyDim1Kode, setNyDim1Kode] = useState("");
  const [nyDim1Navn, setNyDim1Navn] = useState("");
  const [kommentar, setKommentar] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<OmposteringResult | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/financials/ompostering`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_SHARED_SECRET || ""}`,
        },
        body: JSON.stringify({
          transaction_id: transaction.transaction_id,
          ny_dim1_kode: nyDim1Kode.trim(),
          ny_dim1_navn: nyDim1Navn.trim() || undefined,
          kommentar: kommentar.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Feil: ${res.status}`);
      setResult(data);
      onSuccess?.(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ukjent feil");
    } finally {
      setLoading(false);
    }
  }

  const fmt = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-background border border-border rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
          <div>
            <h2 className="font-bold text-base">Ompostering av transaksjon</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Originalbilag røres ikke — oppretter to H1-korrigeringslinjer
            </p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-xl leading-none">✕</button>
        </div>

        {result ? (
          /* ── Kvittering ─────────────────────────────────────────── */
          <div className="px-6 py-6 space-y-4">
            <div className="flex items-center gap-3 text-green-700 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
              <span className="text-xl">✓</span>
              <span className="font-semibold text-sm">Ompostering gjennomført</span>
            </div>
            <div className="text-sm space-y-2 bg-muted/40 rounded-xl px-4 py-3">
              <Row label="Fra koststed" value={`${result.gammelt_koststed.kode} – ${result.gammelt_koststed.navn ?? ""}`} />
              <Row label="Til koststed" value={`${result.nytt_koststed.kode} – ${result.nytt_koststed.navn ?? ""}`} />
              <Row label="Reversering-ID" value={result.reversering_id.slice(0, 8) + "…"} mono />
              <Row label="Ny postering-ID" value={result.ny_postering_id.slice(0, 8) + "…"} mono />
              <Row label="Utført av" value={result.utfort_av} />
            </div>
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition"
            >
              Lukk
            </button>
          </div>
        ) : (
          /* ── Skjema ─────────────────────────────────────────────── */
          <form onSubmit={submit} className="px-6 py-6 space-y-5">
            {/* Originalbilag info */}
            <div className="bg-muted/40 rounded-xl px-4 py-3 text-sm space-y-1.5">
              <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-2">Originalbilag</p>
              {transaction.bilagsnr && <Row label="Bilagsnr" value={transaction.bilagsnr} mono />}
              {transaction.konto && <Row label="Konto" value={`${transaction.konto}${transaction.konto_navn ? " – " + transaction.konto_navn : ""}`} />}
              {transaction.leverandor_navn && <Row label="Leverandør" value={transaction.leverandor_navn} />}
              <Row label="Beløp" value={fmt(transaction.belop)} mono />
              <Row label="Fra koststed" value={`${transaction.dim1_kode ?? "–"} ${transaction.dim1_navn ? "– " + transaction.dim1_navn : ""}`} />
              {transaction.tekst && <Row label="Tekst" value={transaction.tekst} />}
            </div>

            {/* Nytt koststed */}
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">
                Nytt koststed (Dim 1) <span className="text-red-500">*</span>
              </label>
              <input
                required
                type="text"
                value={nyDim1Kode}
                onChange={(e) => setNyDim1Kode(e.target.value)}
                placeholder="f.eks. 635703"
                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Koststed-navn <span className="text-muted-foreground text-xs">(valgfritt – hentes automatisk om tomt)</span></label>
              <input
                type="text"
                value={nyDim1Navn}
                onChange={(e) => setNyDim1Navn(e.target.value)}
                placeholder="f.eks. Enhet for spesialiserte fosterhjem"
                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-semibold">Begrunnelse <span className="text-muted-foreground text-xs">(valgfritt)</span></label>
              <textarea
                value={kommentar}
                onChange={(e) => setKommentar(e.target.value)}
                rows={2}
                placeholder="Hvorfor omposteres denne transaksjonen?"
                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
              />
            </div>

            {error && (
              <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2.5 rounded-xl border border-border text-sm font-semibold hover:bg-muted/50 transition"
              >
                Avbryt
              </button>
              <button
                type="submit"
                disabled={loading || !nyDim1Kode.trim()}
                className="flex-1 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition disabled:opacity-50"
              >
                {loading ? "Sender…" : "Gjennomfør ompostering"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-muted-foreground w-28 shrink-0">{label}:</span>
      <span className={mono ? "font-mono" : ""}>{value}</span>
    </div>
  );
}
