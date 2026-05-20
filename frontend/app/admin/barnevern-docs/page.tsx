"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getBufdirAnnualReports,
  getSsbBufdirShortlist,
  getStprpBufdir,
  type AnnualReportItem,
  listPredictionExcelFiles,
  type PredictionExcelFile,
  type SsbShortlistItem,
  type StprpItem,
} from "@/lib/api/barnevernDocsApi";

export default function BarnevernDocsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stprp, setStprp] = useState<StprpItem[]>([]);
  const [reports, setReports] = useState<AnnualReportItem[]>([]);
  const [ssb, setSsb] = useState<SsbShortlistItem[]>([]);
  const [excelFiles, setExcelFiles] = useState<PredictionExcelFile[]>([]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [a, b, c, d] = await Promise.all([
          getStprpBufdir(),
          getBufdirAnnualReports(),
          getSsbBufdirShortlist(),
          listPredictionExcelFiles(),
        ]);
        setStprp(a.items ?? []);
        setReports(b.items ?? []);
        setSsb(c.items ?? []);
        setExcelFiles(d.items ?? []);
      } catch (e: any) {
        setError(e?.message ?? "Kunne ikke hente data.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <main className="p-6 space-y-8">
      <h1 className="text-2xl font-semibold">Barnevern-dokumenter (Bufdir/SSB/Stortinget)</h1>

      <section className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-foreground space-y-3">
        <h2 className="font-semibold text-base">Kobling og analyse i BEFS</h2>
        <p className="text-muted-foreground leading-relaxed">
          Dette er samlet referansedata som kan knyttes til interne tall og styringsanalyse:{" "}
          <strong>St.prp./Prop</strong> gir politisk og budsjettkontekst,{" "}
          <strong>Bufdir årsrapport</strong> gir mål og resultatfortelling,{" "}
          <strong>SSB-tabeller</strong> gir nasjonale nøkkeltall, og{" "}
          <strong>prediksjon Excel</strong> knytter økonomi og prognoser i samme bilde som
          barnevern-simulering i appen.
        </p>
        <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
          <li>Bruk tabellene under som utgangspunkt når du tolker regionkostnader, institusjonsbruk og KI-rapporter.</li>
          <li>API: <code className="text-xs bg-muted px-1 rounded">/api/v1/barnevern-docs/stprp</code>,{" "}
            <code className="text-xs bg-muted px-1 rounded">…/annual-reports</code>,{" "}
            <code className="text-xs bg-muted px-1 rounded">…/ssb-shortlist</code> (autentisert).</li>
        </ul>
        <div className="flex flex-wrap gap-x-4 gap-y-2 pt-1 text-primary">
          <Link className="underline font-medium" href="/barnevern">
            Barnevern simulering (BEFS + SSB-referanse)
          </Link>
          <Link className="underline font-medium" href="/admin/bufdir-institutions">
            Bufdir institusjoner (full nasjonal liste)
          </Link>
          <Link className="underline font-medium" href="/ssb">
            SSB Statistikk (full tabell og analyse)
          </Link>
          <Link className="underline font-medium" href="/admin/barnevern-analysis">
            Syntese og risiko (generert analyse)
          </Link>
        </div>
      </section>

      {loading && <p className="text-muted-foreground">Laster data...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && (
        <>
          <section className="space-y-3">
            <h2 className="text-xl font-medium">Siste St.prp./Prop relevante for Bufdir</h2>
            <div className="overflow-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-muted/40">
                  <tr>
                    <th className="text-left p-2">Tittel</th>
                    <th className="text-left p-2">Referanse</th>
                    <th className="text-left p-2">Dato</th>
                    <th className="text-left p-2">Lenker</th>
                  </tr>
                </thead>
                <tbody>
                  {stprp.map((row) => (
                    <tr key={String(row.sak_id)} className="border-t">
                      <td className="p-2">{row.title ?? row.short_title ?? "-"}</td>
                      <td className="p-2">{row.reference ?? "-"}</td>
                      <td className="p-2">{row.updated_date ?? row.date ?? "-"}</td>
                      <td className="p-2 space-x-3">
                        {row.prop_url && (
                          <a className="underline" href={row.prop_url} target="_blank" rel="noreferrer">
                            Prop
                          </a>
                        )}
                        {row.storting_sak_url && (
                          <a className="underline" href={row.storting_sak_url} target="_blank" rel="noreferrer">
                            Sak
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-medium">Bufdir årsrapporter (10 år)</h2>
            <ul className="space-y-2">
              {reports.map((r) => (
                <li key={r.year} className="border rounded p-2">
                  <span className="font-medium mr-2">{r.year}</span>
                  <span className="mr-2">{r.title}</span>
                  {r.pdf_url ? (
                    <a className="underline" href={r.pdf_url} target="_blank" rel="noreferrer">
                      PDF
                    </a>
                  ) : (
                    <span className="text-muted-foreground">Ingen PDF funnet</span>
                  )}
                </li>
              ))}
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-medium">SSB tabell-kortliste (Bufetat/Bufdir-relevant)</h2>
            <div className="overflow-auto border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-muted/40">
                  <tr>
                    <th className="text-left p-2">Tabell</th>
                    <th className="text-left p-2">Periode</th>
                    <th className="text-left p-2">Lenker</th>
                  </tr>
                </thead>
                <tbody>
                  {ssb.map((t) => (
                    <tr key={t.id} className="border-t">
                      <td className="p-2">
                        <div className="font-medium">{t.id}</div>
                        <div>{t.label}</div>
                      </td>
                      <td className="p-2">
                        {t.firstPeriod ?? "-"} - {t.lastPeriod ?? "-"}
                      </td>
                      <td className="p-2 space-x-3">
                        {t.metadataUrl && (
                          <a className="underline" href={t.metadataUrl} target="_blank" rel="noreferrer">
                            Metadata
                          </a>
                        )}
                        {t.dataUrl && (
                          <a className="underline" href={t.dataUrl} target="_blank" rel="noreferrer">
                            Data
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-xl font-medium">Prediksjon Excel-filer</h2>
            <ul className="space-y-2">
              {excelFiles.map((f) => (
                <li key={f.filename} className="border rounded p-2 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{f.filename}</div>
                    <div className="text-xs text-muted-foreground">
                      Oppdatert: {new Date(f.updated_at).toLocaleString("nb-NO")} · {(f.size_bytes / 1024 / 1024).toFixed(1)} MB
                    </div>
                  </div>
                  <a className="underline" href={f.download_url}>
                    Last ned
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </main>
  );
}
