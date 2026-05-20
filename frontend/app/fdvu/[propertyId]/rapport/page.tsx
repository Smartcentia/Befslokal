"use client";

/**
 * /fdvu/[propertyId]/rapport — Tilsynsrapport for én eiendom
 *
 * Forhåndsutfylt fra database:
 *  - Eiendomsinfo (navn, adresse, type, godkjente plasser)
 *  - Compliance-vurderinger → avkrysning per krav, gruppert per regelverk
 *  - Tilstandsgrader (TG0-TG3) fra bygningskomponenter
 *  - FDV-dokumentstatus
 *
 * Brukeren kan:
 *  - Redigere status og notater direkte i skjema → lagre til backend
 *  - Skrive inn tilleggstekst i frie felt (inspektør, dato, konklusjon)
 *  - Klikke "Skriv ut" → browser-print → PDF
 *    (print:hidden skjuler alle kontroller og skjemaknapper)
 */

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { ChevronLeft, Printer, Save, Loader2, CheckCircle2, XCircle, AlertCircle, MinusCircle, HelpCircle } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const TOKEN = process.env.NEXT_PUBLIC_BACKEND_SECRET ?? "befs-super-secret-key-12345";
const hdrs = () => ({ Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" });

// ─────────────────────────────────────────────
// Typer
// ─────────────────────────────────────────────

interface RapportProperty { property_id: string; name: string; address?: string; city?: string; region?: string; unit_type_derived?: string; approved_places?: number; }
interface ComplianceDetail { assignment_id: string; code: string; title: string; regulation_set: string; severity?: string | null; status: string; assessed_at?: string | null; next_review_date?: string | null; evidence_notes?: string | null; }
interface ComplianceSummary { total_assignments: number; compliant: number; non_compliant: number; partial: number; not_assessed: number; not_applicable: number; overdue_reviews: number; compliance_rate: number; }
interface Component { component_id: string; name: string; type?: string; ns3451_code?: string; condition_grade?: string; criticality_level?: string; replacement_year?: number; }
interface FdvDocument { document_id: string; title: string; document_type: string; document_date?: string | null; valid_until?: string | null; status: string; }

interface Rapport {
  generated_at: string;
  property: RapportProperty;
  compliance_summary: ComplianceSummary;
  compliance_details: ComplianceDetail[];
  components: Component[];
  fdv_documents: FdvDocument[];
}

// ─────────────────────────────────────────────
// Konstanter
// ─────────────────────────────────────────────

const STATUS_OPTIONS = [
  { value: "compliant",      label: "Oppfylt",        icon: CheckCircle2, cls: "text-emerald-600 print:text-black" },
  { value: "partial",        label: "Delvis oppfylt", icon: AlertCircle,  cls: "text-amber-600 print:text-black" },
  { value: "non_compliant",  label: "Avvik",          icon: XCircle,      cls: "text-red-600 print:text-black" },
  { value: "not_applicable", label: "Ikke aktuelt",   icon: MinusCircle,  cls: "text-gray-400 print:text-black" },
  { value: "not_assessed",   label: "Ikke vurdert",   icon: HelpCircle,   cls: "text-gray-400 print:text-black" },
];

const STATUS_PRINT_SYMBOL: Record<string, string> = {
  compliant: "☑ Oppfylt",
  partial: "△ Delvis",
  non_compliant: "✗ Avvik",
  not_applicable: "— N/A",
  not_assessed: "○ Ikke vurdert",
};

const REG_LABELS: Record<string, string> = {
  RKL6: "Risikoklasse 6 – Brannsikkerhet",
  BVL: "Barnevernloven",
  KVALITETSFORSKRIFTEN: "Kvalitetsforskriften",
  TEK17: "TEK17 – Teknisk forskrift",
  HMS: "HMS / Arbeidsmiljøloven",
  INTERN: "Interne krav",
  DRIFTSLEDELSE: "Driftsledelse",
  ENOK: "Energieffektivisering (ENOK)",
  UU: "Universell utforming",
  SIKKERHET: "Sikkerhet og personvern",
  MILJØ: "Miljø og farlige stoffer",
  BYGG: "Bygg – NS3451 tilstandsanalyse",
};

const TG_LABELS: Record<string, string> = {
  TG0: "TG0 – Ingen symptomer",
  TG1: "TG1 – Svake symptomer",
  TG2: "TG2 – Middels alvorlig",
  TG3: "TG3 – Kraftige avvik",
};

// ─────────────────────────────────────────────
// Lokal state for redigerbare felt
// ─────────────────────────────────────────────

interface LocalRow { status: string; evidence_notes: string; dirty: boolean; }

function initLocal(details: ComplianceDetail[]): Record<string, LocalRow> {
  const m: Record<string, LocalRow> = {};
  for (const d of details) {
    m[d.assignment_id] = { status: d.status, evidence_notes: d.evidence_notes ?? "", dirty: false };
  }
  return m;
}

// ─────────────────────────────────────────────
// Komponent
// ─────────────────────────────────────────────

export default function TilsynsrapportPage({ params }: { params: Promise<{ propertyId: string }> }) {
  const { propertyId } = use(params);
  const [rapport, setRapport] = useState<Rapport | null>(null);
  const [local, setLocal] = useState<Record<string, LocalRow>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState("");
  // Frie felt for rapporten
  const [inspectørNavn, setInspektørNavn] = useState("");
  const [tilsynsDato, setTilsynsDato] = useState(new Date().toISOString().split("T")[0]);
  const [konklusjon, setKonklusjon] = useState("");
  const [tiltak, setTiltak] = useState("");

  const today = new Date().toLocaleDateString("no-NO", { day: "2-digit", month: "long", year: "numeric" });

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/v1/fdvu/rapport/${propertyId}`, { headers: hdrs() })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d) { setRapport(d); setLocal(initLocal(d.compliance_details ?? [])); }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [propertyId]);

  const setField = (id: string, field: "status" | "evidence_notes", val: string) => {
    setLocal(prev => ({ ...prev, [id]: { ...prev[id], [field]: val, dirty: true } }));
  };

  const saveAll = async () => {
    const dirty = Object.values(local).filter(l => l.dirty);
    if (!dirty.length) return;
    setSaving(true);
    try {
      // Batch-lagre status via bulk-assess per status-gruppe
      const byStatus: Record<string, string[]> = {};
      for (const [assignment_id, l] of Object.entries(local)) {
        if (l.dirty) (byStatus[l.status] ??= []).push(assignment_id);
      }
      for (const [status, ids] of Object.entries(byStatus)) {
        await fetch(`${API}/api/v1/fdvu/compliance/bulk-assess`, {
          method: "POST", headers: hdrs(),
          body: JSON.stringify({ assignment_ids: ids, status }),
        });
      }
      // Individuelle notater via upsert
      for (const [assignment_id, l] of Object.entries(local)) {
        if (l.dirty) {
          await fetch(`${API}/api/v1/fdvu/compliance/assess`, {
            method: "PUT", headers: hdrs(),
            body: JSON.stringify({ assignment_id, status: l.status, evidence_notes: l.evidence_notes || undefined }),
          });
        }
      }
      setSavedMsg(`Lagret ${dirty.length} vurderinger`);
      setLocal(prev => {
        const next = { ...prev };
        for (const [k] of Object.entries(prev)) next[k] = { ...next[k], dirty: false };
        return next;
      });
      setTimeout(() => setSavedMsg(""), 4000);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen text-muted-foreground text-sm">Laster rapport…</div>;
  if (!rapport) return <div className="flex items-center justify-center min-h-screen text-red-500 text-sm">Kunne ikke laste rapport. Sjekk at backend er oppe.</div>;

  const prop = rapport.property;
  const cs = rapport.compliance_summary;
  const details = rapport.compliance_details ?? [];
  const components = rapport.components ?? [];
  const docs = rapport.fdv_documents ?? [];
  const rate = Math.round(cs.compliance_rate * 100);

  // Grupper details per regulation_set
  const grouped: Record<string, ComplianceDetail[]> = {};
  for (const d of details) {
    (grouped[d.regulation_set] ??= []).push(d);
  }

  // TG-oppsummering
  const tgCounts: Record<string, number> = {};
  for (const c of components) {
    if (c.condition_grade) tgCounts[c.condition_grade] = (tgCounts[c.condition_grade] ?? 0) + 1;
  }

  const dirtyCount = Object.values(local).filter(l => l.dirty).length;

  return (
    <div className="min-h-screen bg-background text-foreground print:bg-white print:text-black">

      {/* Kontrollbar — skjules ved print */}
      <div className="print:hidden border-b border-border bg-card/50 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3 flex-wrap">
          <Link href={`/fdvu/${propertyId}`} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
            <ChevronLeft size={16} /> Tilbake
          </Link>
          <span className="flex-1" />
          {savedMsg && <span className="text-sm text-success">{savedMsg}</span>}
          {dirtyCount > 0 && (
            <button onClick={saveAll} disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm hover:bg-secondary/80 disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Lagre endringer ({dirtyCount})
            </button>
          )}
          <button onClick={() => window.print()}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90">
            <Printer size={14} /> Skriv ut / PDF
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 print:px-8 print:py-6 space-y-8">

        {/* === RAPPORT-HEADER === */}
        <div className="border-b border-border print:border-gray-300 pb-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs text-muted-foreground print:text-gray-500 uppercase tracking-widest mb-1">
                Tilsynsrapport — FDVU Compliance
              </div>
              <h1 className="text-2xl font-bold print:text-3xl">{prop.name}</h1>
              <div className="text-sm text-muted-foreground print:text-gray-600 mt-1 space-y-0.5">
                {prop.address && <div>{prop.address}{prop.city ? `, ${prop.city}` : ""}</div>}
                <div>{prop.region} · {prop.unit_type_derived ?? "Eiendom"}{prop.approved_places ? ` · ${prop.approved_places} godkjente plasser` : ""}</div>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className={`text-4xl font-bold print:text-5xl ${rate >= 90 ? "text-emerald-500 print:text-black" : rate >= 60 ? "text-amber-500 print:text-black" : "text-red-500 print:text-black"}`}>
                {rate}%
              </div>
              <div className="text-xs text-muted-foreground print:text-gray-500">Compliance-rate</div>
            </div>
          </div>

          {/* Inspektørinfo — fritt felt */}
          <div className="mt-4 grid grid-cols-2 gap-4 print:grid-cols-2">
            <div>
              <label className="text-xs text-muted-foreground print:text-gray-500">Inspektør / ansvarlig</label>
              <input type="text" value={inspektørNavn} onChange={e => setInspektørNavn(e.target.value)}
                placeholder="Navn på inspektør…"
                className="mt-1 w-full text-sm px-2 py-1.5 border-b border-border print:border-gray-400 bg-transparent outline-none placeholder:text-muted-foreground/50 print:placeholder:text-transparent" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground print:text-gray-500">Tilsynsdato</label>
              <input type="date" value={tilsynsDato} onChange={e => setTilsynsDato(e.target.value)}
                className="mt-1 w-full text-sm px-2 py-1.5 border-b border-border print:border-gray-400 bg-transparent outline-none" />
            </div>
          </div>
        </div>

        {/* === SAMMENDRAG === */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-3 print:grid-cols-6">
          {[
            { label: "Totalt krav", value: cs.total_assignments },
            { label: "Oppfylt", value: cs.compliant, cls: "text-emerald-500 print:text-black" },
            { label: "Avvik", value: cs.non_compliant, cls: "text-red-600 print:text-black font-bold" },
            { label: "Delvis", value: cs.partial, cls: "text-amber-500 print:text-black" },
            { label: "Ikke vurdert", value: cs.not_assessed },
            { label: "Forfalt", value: cs.overdue_reviews, cls: cs.overdue_reviews > 0 ? "text-orange-500 print:text-black" : "" },
          ].map(k => (
            <div key={k.label} className="text-center p-2 border border-border print:border-gray-300 rounded-lg">
              <div className={`text-2xl font-bold ${k.cls ?? ""}`}>{k.value}</div>
              <div className="text-xs text-muted-foreground print:text-gray-500">{k.label}</div>
            </div>
          ))}
        </div>

        {/* === COMPLIANCE-DETALJER per regelverk === */}
        {Object.entries(grouped).map(([reg, items]) => {
          const done = items.filter(d => local[d.assignment_id]?.status !== "not_assessed").length;
          const avvik = items.filter(d => local[d.assignment_id]?.status === "non_compliant").length;
          return (
            <div key={reg} className="space-y-1 print:break-inside-avoid">
              {/* Regelverk-header */}
              <div className="flex items-center justify-between bg-muted print:bg-gray-100 px-4 py-2 rounded-lg print:rounded-none">
                <h2 className="font-semibold text-sm">{REG_LABELS[reg] ?? reg}</h2>
                <div className="flex items-center gap-3 text-xs text-muted-foreground print:text-gray-500">
                  {avvik > 0 && <span className="text-red-500 font-semibold print:text-black">{avvik} avvik</span>}
                  <span>{done}/{items.length} vurdert</span>
                </div>
              </div>

              {/* Kravliste */}
              <div className="border border-border print:border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted/30 print:bg-gray-50 border-b border-border print:border-gray-200">
                      <th className="text-left px-3 py-2 font-medium text-muted-foreground w-24">Kode</th>
                      <th className="text-left px-3 py-2 font-medium text-muted-foreground">Krav</th>
                      <th className="text-center px-3 py-2 font-medium text-muted-foreground w-32">Status</th>
                      <th className="text-left px-3 py-2 font-medium text-muted-foreground print:w-48">Notater / dokumentasjon</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50 print:divide-gray-200">
                    {items.map(d => {
                      const loc = local[d.assignment_id] ?? { status: d.status, evidence_notes: d.evidence_notes ?? "", dirty: false };
                      const statusMeta = STATUS_OPTIONS.find(s => s.value === loc.status) ?? STATUS_OPTIONS[4];
                      const StatusIcon = statusMeta.icon;
                      return (
                        <tr key={d.assignment_id} className={loc.dirty ? "bg-warning/5" : ""}>
                          <td className="px-3 py-2 font-mono text-muted-foreground">{d.code}</td>
                          <td className="px-3 py-2">
                            <div className="font-medium">{d.title}</div>
                            {d.severity && d.severity !== "low" && (
                              <div className={`text-[10px] mt-0.5 font-medium ${d.severity === "critical" ? "text-red-500 print:text-black" : d.severity === "high" ? "text-orange-500 print:text-black" : "text-amber-500 print:text-black"}`}>
                                {d.severity === "critical" ? "⚠ Kritisk" : d.severity === "high" ? "▲ Høy alvorlighet" : "Middels"}
                              </div>
                            )}
                          </td>
                          <td className="px-3 py-2 text-center">
                            {/* Skjerm: dropdown */}
                            <select
                              value={loc.status}
                              onChange={e => setField(d.assignment_id, "status", e.target.value)}
                              className={`print:hidden text-xs px-2 py-1 rounded border bg-background appearance-none cursor-pointer ${statusMeta.cls}`}
                            >
                              {STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                            {/* Print: tekst */}
                            <span className="hidden print:inline-block text-[10px] font-medium">
                              {STATUS_PRINT_SYMBOL[loc.status] ?? loc.status}
                            </span>
                          </td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={loc.evidence_notes}
                              onChange={e => setField(d.assignment_id, "evidence_notes", e.target.value)}
                              placeholder="Notater…"
                              className="print:hidden w-full text-xs px-2 py-1 bg-background border border-border/50 rounded outline-none placeholder:text-muted-foreground/40 focus:border-primary/40"
                            />
                            <span className="hidden print:inline text-[10px] text-gray-600">{loc.evidence_notes}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}

        {/* === TILSTANDSGRADER (komponenter) === */}
        {components.length > 0 && (
          <div className="space-y-1 print:break-inside-avoid">
            <div className="flex items-center justify-between bg-muted print:bg-gray-100 px-4 py-2 rounded-lg">
              <h2 className="font-semibold text-sm">Bygningskomponenter — Tilstandsgrader</h2>
              <div className="flex items-center gap-2 text-xs">
                {["TG0", "TG1", "TG2", "TG3"].map(tg => tgCounts[tg] ? (
                  <span key={tg} className={`px-2 py-0.5 rounded ${tg === "TG3" ? "bg-red-500/20 text-red-400 print:text-black" : tg === "TG2" ? "bg-amber-500/20 text-amber-500 print:text-black" : "text-muted-foreground"}`}>
                    {tg}: {tgCounts[tg]}
                  </span>
                ) : null)}
              </div>
            </div>
            <div className="border border-border print:border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-muted/30 print:bg-gray-50 border-b border-border print:border-gray-200">
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Komponent</th>
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Type</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Tilstand</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Kritikalitet</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Utskifting</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50 print:divide-gray-200">
                  {components.map(c => (
                    <tr key={c.component_id} className={c.condition_grade === "TG3" ? "bg-red-500/5" : c.condition_grade === "TG2" ? "bg-amber-500/5" : ""}>
                      <td className="px-3 py-2 font-medium">{c.name}</td>
                      <td className="px-3 py-2 text-muted-foreground">{c.type ?? "—"}</td>
                      <td className="px-3 py-2 text-center">
                        <span className={`font-bold text-xs px-2 py-0.5 rounded ${c.condition_grade === "TG3" ? "bg-red-500/20 text-red-500 print:text-black" : c.condition_grade === "TG2" ? "bg-amber-500/20 text-amber-500 print:text-black" : c.condition_grade === "TG0" ? "text-emerald-500 print:text-black" : "text-muted-foreground"}`}>
                          {c.condition_grade ? TG_LABELS[c.condition_grade] : "Ikke vurdert"}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center text-muted-foreground">{c.criticality_level ?? "—"}</td>
                      <td className="px-3 py-2 text-center text-muted-foreground">{c.replacement_year ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* === FDV-DOKUMENTER === */}
        {docs.length > 0 && (
          <div className="space-y-1 print:break-inside-avoid">
            <div className="bg-muted print:bg-gray-100 px-4 py-2 rounded-lg">
              <h2 className="font-semibold text-sm">FDV-dokumentasjon ({docs.length} dokumenter)</h2>
            </div>
            <div className="border border-border print:border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-muted/30 print:bg-gray-50 border-b border-border print:border-gray-200">
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Dokument</th>
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Type</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Dato</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Gyldig til</th>
                    <th className="text-center px-3 py-2 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50 print:divide-gray-200">
                  {docs.map(doc => (
                    <tr key={doc.document_id}>
                      <td className="px-3 py-2 font-medium">{doc.title}</td>
                      <td className="px-3 py-2 text-muted-foreground">{doc.document_type}</td>
                      <td className="px-3 py-2 text-center text-muted-foreground">{doc.document_date ?? "—"}</td>
                      <td className="px-3 py-2 text-center text-muted-foreground">{doc.valid_until ?? "—"}</td>
                      <td className="px-3 py-2 text-center">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${doc.status === "active" ? "bg-emerald-500/15 text-emerald-500 print:text-black" : doc.status === "expired" ? "bg-red-500/15 text-red-500 print:text-black" : "text-muted-foreground"}`}>
                          {doc.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* === KONKLUSJON (fritt felt) === */}
        <div className="space-y-3 print:break-inside-avoid">
          <div className="bg-muted print:bg-gray-100 px-4 py-2 rounded-lg">
            <h2 className="font-semibold text-sm">Konklusjon og anbefalte tiltak</h2>
          </div>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground print:text-gray-500 mb-1 block">Samlet vurdering / konklusjon</label>
              <textarea value={konklusjon} onChange={e => setKonklusjon(e.target.value)}
                placeholder="Skriv samlet vurdering av eiendommens compliance-status og eventuelle funn…"
                rows={4}
                className="w-full text-sm px-3 py-2 border border-border print:border-gray-400 rounded-lg bg-background print:bg-transparent outline-none placeholder:text-muted-foreground/40 resize-none focus:border-primary/50 print:placeholder:text-transparent" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground print:text-gray-500 mb-1 block">Anbefalte tiltak og tidsplan</label>
              <textarea value={tiltak} onChange={e => setTiltak(e.target.value)}
                placeholder="Liste over anbefalte tiltak med tidsfrister…"
                rows={4}
                className="w-full text-sm px-3 py-2 border border-border print:border-gray-400 rounded-lg bg-background print:bg-transparent outline-none placeholder:text-muted-foreground/40 resize-none focus:border-primary/50 print:placeholder:text-transparent" />
            </div>
          </div>
        </div>

        {/* === SIGNERINGSFELT === */}
        <div className="print:break-inside-avoid grid grid-cols-2 gap-8 pt-6 border-t border-border print:border-gray-300 mt-8">
          {[{ label: "Inspektør / ansvarlig BEFS", navn: inspektørNavn }, { label: "Eiendomsansvarlig" }].map(f => (
            <div key={f.label} className="space-y-2">
              <div className="text-xs text-muted-foreground print:text-gray-500">{f.label}</div>
              <div className="text-sm font-medium print:min-h-[2rem] border-b border-border print:border-gray-400 pb-1">{f.navn ?? ""}</div>
              <div className="text-xs text-muted-foreground print:text-gray-500">Dato: {tilsynsDato}</div>
            </div>
          ))}
        </div>

        {/* Fotnote */}
        <div className="text-[10px] text-muted-foreground print:text-gray-400 text-center pt-4 print:pt-2">
          Tilsynsrapport · {prop.name} · Bufetat Eiendom · {today} · Konfidensielt dokument
        </div>
      </div>
    </div>
  );
}
