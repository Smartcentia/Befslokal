"use client";

/**
 * /fdvu/vurdering — Bulk-vurderingsverktøy for BEFS sentral
 *
 * Sentrale BEFS-ansatte velger eiendom → ser alle 122 krav gruppert per
 * regelverk → setter status + notater → lagrer til backend i én bulk-POST.
 *
 * Arbeidsflyt:
 *  1. Søk / velg eiendom
 *  2. Klikk "Last inn krav" → henter assignments for eiendommen
 *  3. Per krav: sett status (dropdown) + notater (tekstfelt)
 *  4. "Lagre alle vurderinger" → POST /fdvu/compliance/bulk-assess per gruppe
 */

import { useEffect, useState, useCallback } from "react";
import { CheckCircle2, XCircle, AlertCircle, MinusCircle, HelpCircle, Save, ChevronDown, ChevronRight, Loader2, Building2, Search } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const TOKEN = process.env.NEXT_PUBLIC_BACKEND_SECRET ?? "befs-super-secret-key-12345";

const headers = () => ({
  Authorization: `Bearer ${TOKEN}`,
  "Content-Type": "application/json",
});

// ─────────────────────────────────────────────
// Typer
// ─────────────────────────────────────────────

interface Property { property_id: string; name: string; address?: string; region?: string; }
interface Requirement { requirement_id: string; code: string; title: string; description?: string | null; regulation_set: string; severity_if_breached?: string | null; category?: string | null; }
interface Assessment { assessment_id?: string; status: string; evidence_notes?: string; next_review_date?: string; }
interface Assignment { assignment_id: string; requirement_id: string; requirement?: Requirement | null; compliance_assessment?: Assessment | null; }

// ─────────────────────────────────────────────
// Konstanter
// ─────────────────────────────────────────────

const STATUS_OPTIONS = [
  { value: "not_assessed",   label: "Ikke vurdert",   icon: HelpCircle,    cls: "text-gray-400" },
  { value: "compliant",      label: "Oppfylt",        icon: CheckCircle2,  cls: "text-emerald-500" },
  { value: "partial",        label: "Delvis oppfylt", icon: AlertCircle,   cls: "text-amber-500" },
  { value: "non_compliant",  label: "Avvik",          icon: XCircle,       cls: "text-red-500" },
  { value: "not_applicable", label: "Ikke aktuelt",   icon: MinusCircle,   cls: "text-gray-400" },
];

const REG_LABELS: Record<string, string> = {
  RKL6: "Risikoklasse 6 – Brann",
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

const REG_COLORS: Record<string, string> = {
  RKL6: "border-red-500/40 bg-red-500/5",
  BVL: "border-purple-500/40 bg-purple-500/5",
  KVALITETSFORSKRIFTEN: "border-teal-500/40 bg-teal-500/5",
  TEK17: "border-blue-500/40 bg-blue-500/5",
  HMS: "border-orange-500/40 bg-orange-500/5",
  INTERN: "border-gray-500/40 bg-gray-500/5",
  DRIFTSLEDELSE: "border-sky-500/40 bg-sky-500/5",
  ENOK: "border-green-500/40 bg-green-500/5",
  UU: "border-indigo-500/40 bg-indigo-500/5",
  SIKKERHET: "border-yellow-500/40 bg-yellow-500/5",
  MILJØ: "border-emerald-500/40 bg-emerald-500/5",
  BYGG: "border-stone-500/40 bg-stone-500/5",
};

const SEV_BADGE: Record<string, string> = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-green-500/20 text-green-400 border-green-500/30",
};

// ─────────────────────────────────────────────
// Lokalt state per assignment
// ─────────────────────────────────────────────

interface LocalAssessment {
  assignment_id: string;
  status: string;
  evidence_notes: string;
  next_review_date: string;
  dirty: boolean;
}

function initLocal(assignments: Assignment[]): Record<string, LocalAssessment> {
  const map: Record<string, LocalAssessment> = {};
  for (const a of assignments) {
    const ca = a.compliance_assessment;
    map[a.assignment_id] = {
      assignment_id: a.assignment_id,
      status: ca?.status ?? "not_assessed",
      evidence_notes: ca?.evidence_notes ?? "",
      next_review_date: ca?.next_review_date ?? "",
      dirty: false,
    };
  }
  return map;
}

// ─────────────────────────────────────────────
// Komponent
// ─────────────────────────────────────────────

export default function VurderingPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [search, setSearch] = useState("");
  const [selectedProp, setSelectedProp] = useState<Property | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [local, setLocal] = useState<Record<string, LocalAssessment>>({});
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedCount, setSavedCount] = useState<number | null>(null);
  const [loadError, setLoadError] = useState("");

  // Last eiendommer
  useEffect(() => {
    fetch(`${API}/api/v1/properties?limit=700`, { headers: headers() })
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => setProperties(Array.isArray(d?.items) ? d.items : Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  const filtered = search.length > 1
    ? properties.filter(p => `${p.name} ${p.address} ${p.region}`.toLowerCase().includes(search.toLowerCase())).slice(0, 20)
    : [];

  // Last assignments for valgt eiendom
  const loadAssignments = useCallback(async (prop: Property) => {
    setLoading(true);
    setLoadError("");
    setAssignments([]);
    setLocal({});
    try {
      const res = await fetch(`${API}/api/v1/fdvu/assignments?property_id=${prop.property_id}`, { headers: headers() });
      if (!res.ok) throw new Error("Kunne ikke hente krav");
      const data: Assignment[] = await res.json();
      setAssignments(data);
      setLocal(initLocal(data));
      // Collapse alle grupper først
      const groups: Record<string, boolean> = {};
      for (const a of data) {
        const reg = a.requirement?.regulation_set ?? "UKJENT";
        groups[reg] = false; // expanded by default
      }
      setCollapsed(groups);
    } catch (e: unknown) {
      setLoadError(e instanceof Error ? e.message : "Feil ved lasting");
    } finally {
      setLoading(false);
    }
  }, []);

  // Grupper assignments per regulation_set
  const grouped: Record<string, Assignment[]> = {};
  for (const a of assignments) {
    const reg = a.requirement?.regulation_set ?? "UKJENT";
    (grouped[reg] ??= []).push(a);
  }

  // Oppdater lokalt felt
  const setField = (assignmentId: string, field: keyof LocalAssessment, value: string) => {
    setLocal(prev => ({
      ...prev,
      [assignmentId]: { ...prev[assignmentId], [field]: value, dirty: true },
    }));
  };

  // Bulk: sett alle i gruppe til en status
  const bulkSetGroup = (reg: string, status: string) => {
    const ids = (grouped[reg] ?? []).map(a => a.assignment_id);
    setLocal(prev => {
      const next = { ...prev };
      for (const id of ids) {
        next[id] = { ...next[id], status, dirty: true };
      }
      return next;
    });
  };

  // Lagre alle dirty
  const saveAll = async () => {
    const dirty = Object.values(local).filter(l => l.dirty);
    if (!dirty.length) return;
    setSaving(true);
    setSavedCount(null);
    try {
      // Grupper per status for batch-kall
      const byStatus: Record<string, string[]> = {};
      for (const l of dirty) {
        (byStatus[l.status] ??= []).push(l.assignment_id);
      }
      let total = 0;
      for (const [status, ids] of Object.entries(byStatus)) {
        // Bruk evidence_notes fra siste dirty for gruppen (individuelle kall)
        // For batch: send alle ids med samme status + generisk note
        const res = await fetch(`${API}/api/v1/fdvu/compliance/bulk-assess`, {
          method: "POST",
          headers: headers(),
          body: JSON.stringify({ assignment_ids: ids, status }),
        });
        if (res.ok) {
          const d = await res.json();
          total += (d.updated ?? 0) + (d.created ?? 0);
        }
      }
      // Individuelle notater: PUT per assignment
      for (const l of dirty) {
        if (l.evidence_notes) {
          await fetch(`${API}/api/v1/fdvu/compliance/assess`, {
            method: "PUT",
            headers: headers(),
            body: JSON.stringify({
              assignment_id: l.assignment_id,
              status: l.status,
              evidence_notes: l.evidence_notes || undefined,
              next_review_date: l.next_review_date || undefined,
            }),
          });
        }
      }
      setSavedCount(total);
      // Mark as clean
      setLocal(prev => {
        const next = { ...prev };
        for (const l of dirty) next[l.assignment_id] = { ...next[l.assignment_id], dirty: false };
        return next;
      });
      // Refresh assignments
      if (selectedProp) loadAssignments(selectedProp);
    } finally {
      setSaving(false);
    }
  };

  const dirtyCount = Object.values(local).filter(l => l.dirty).length;
  const totalAssessed = Object.values(local).filter(l => l.status !== "not_assessed").length;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/50 px-6 py-5">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Building2 size={20} className="text-primary" />
              FDVU Vurderingsverktøy
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Sentral BEFS-team — registrer compliance-status for alle 122 krav per eiendom
            </p>
          </div>
          {assignments.length > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                {totalAssessed}/{assignments.length} vurdert
                {dirtyCount > 0 && <span className="text-warning ml-2">({dirtyCount} ulagrede)</span>}
              </span>
              {savedCount !== null && (
                <span className="text-sm text-success">✓ {savedCount} lagret</span>
              )}
              <button
                onClick={saveAll}
                disabled={saving || dirtyCount === 0}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                Lagre alle ({dirtyCount})
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-6">
        {/* Eiendomsvelger */}
        <div className="bg-card rounded-xl border border-border p-5">
          <h2 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-3">Velg eiendom</h2>
          <div className="relative">
            <div className="flex items-center gap-2 px-3 py-2 bg-background border border-border rounded-lg">
              <Search size={16} className="text-muted-foreground flex-shrink-0" />
              <input
                type="text"
                placeholder="Søk på navn, adresse eller region…"
                value={selectedProp ? selectedProp.name : search}
                onChange={e => { setSearch(e.target.value); setShowDropdown(true); setSelectedProp(null); }}
                onFocus={() => setShowDropdown(true)}
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
              {selectedProp && (
                <button onClick={() => { setSelectedProp(null); setSearch(""); setAssignments([]); setLocal({}); }}
                  className="text-muted-foreground hover:text-foreground text-xs">×</button>
              )}
            </div>
            {showDropdown && filtered.length > 0 && (
              <div className="absolute z-50 top-full mt-1 w-full bg-popover border border-border rounded-lg shadow-xl max-h-64 overflow-y-auto">
                {filtered.map(p => (
                  <button key={p.property_id}
                    onClick={() => { setSelectedProp(p); setSearch(""); setShowDropdown(false); loadAssignments(p); }}
                    className="w-full text-left px-4 py-2.5 hover:bg-accent text-sm flex items-center justify-between gap-2"
                  >
                    <span className="font-medium">{p.name}</span>
                    <span className="text-muted-foreground text-xs">{p.region}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          {selectedProp && (
            <div className="mt-3 flex items-center gap-2 text-sm">
              <span className="font-medium text-primary">{selectedProp.name}</span>
              {selectedProp.region && <span className="text-muted-foreground">· {selectedProp.region}</span>}
              {selectedProp.address && <span className="text-muted-foreground">· {selectedProp.address}</span>}
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
            <Loader2 size={20} className="animate-spin" />
            Henter krav for eiendommen…
          </div>
        )}
        {loadError && <div className="text-red-500 text-sm p-4 bg-red-500/10 rounded-lg">{loadError}</div>}

        {/* Ingen eiendom valgt */}
        {!selectedProp && !loading && (
          <div className="text-center py-16 text-muted-foreground">
            <Building2 size={40} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">Søk og velg en eiendom for å starte vurdering</p>
          </div>
        )}

        {/* Grupper per regulation_set */}
        {!loading && assignments.length > 0 && Object.entries(grouped).map(([reg, items]) => {
          const isCollapsed = collapsed[reg];
          const groupLocal = items.map(a => local[a.assignment_id]).filter(Boolean);
          const groupDone = groupLocal.filter(l => l.status !== "not_assessed").length;
          const groupAvvik = groupLocal.filter(l => l.status === "non_compliant").length;
          const groupDirty = groupLocal.filter(l => l.dirty).length;

          return (
            <div key={reg} className={`rounded-xl border-2 overflow-hidden ${REG_COLORS[reg] ?? "border-border bg-card"}`}>
              {/* Gruppe-header */}
              <button
                onClick={() => setCollapsed(prev => ({ ...prev, [reg]: !isCollapsed }))}
                className="w-full flex items-center gap-3 px-5 py-4 hover:bg-black/5 transition-colors text-left"
              >
                {isCollapsed ? <ChevronRight size={16} className="flex-shrink-0" /> : <ChevronDown size={16} className="flex-shrink-0" />}
                <span className="font-semibold text-sm">{REG_LABELS[reg] ?? reg}</span>
                <span className="text-xs text-muted-foreground">{items.length} krav</span>
                <span className="ml-auto flex items-center gap-2">
                  {groupDirty > 0 && <span className="text-xs text-warning">({groupDirty} ulagret)</span>}
                  {groupAvvik > 0 && <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">{groupAvvik} avvik</span>}
                  <span className="text-xs px-2 py-0.5 rounded bg-white/10 border border-border">{groupDone}/{items.length} vurdert</span>
                </span>
              </button>

              {/* Bulk-knapper + kravliste */}
              {!isCollapsed && (
                <div className="border-t border-border/50">
                  {/* Bulk-handlinger */}
                  <div className="flex items-center gap-2 px-5 py-2 bg-black/5 flex-wrap">
                    <span className="text-xs text-muted-foreground mr-1">Sett alle til:</span>
                    {STATUS_OPTIONS.filter(s => s.value !== "not_assessed").map(opt => (
                      <button key={opt.value}
                        onClick={() => bulkSetGroup(reg, opt.value)}
                        className={`text-xs px-2.5 py-1 rounded border transition-colors hover:bg-white/10 ${opt.cls}`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>

                  {/* Kravliste */}
                  <div className="divide-y divide-border/30">
                    {items.map(a => {
                      const req = a.requirement;
                      const loc = local[a.assignment_id] ?? { status: "not_assessed", evidence_notes: "", next_review_date: "", dirty: false };
                      const statusMeta = STATUS_OPTIONS.find(s => s.value === loc.status) ?? STATUS_OPTIONS[0];
                      const StatusIcon = statusMeta.icon;

                      return (
                        <div key={a.assignment_id} className={`px-5 py-3 ${loc.dirty ? "bg-warning/5" : ""}`}>
                          <div className="flex items-start gap-3 flex-wrap">
                            {/* Code + tittel */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-mono text-muted-foreground">{req?.code}</span>
                                {req?.severity_if_breached && (
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${SEV_BADGE[req.severity_if_breached] ?? ""}`}>
                                    {req.severity_if_breached === "critical" ? "Kritisk" : req.severity_if_breached === "high" ? "Høy" : req.severity_if_breached === "medium" ? "Middels" : "Lav"}
                                  </span>
                                )}
                                {loc.dirty && <span className="text-[10px] text-warning">●</span>}
                              </div>
                              <p className="text-sm font-medium mt-0.5">{req?.title}</p>
                              {req?.description && (
                                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{req.description}</p>
                              )}
                            </div>

                            {/* Status-selector */}
                            <div className="flex-shrink-0">
                              <div className="relative">
                                <select
                                  value={loc.status}
                                  onChange={e => setField(a.assignment_id, "status", e.target.value)}
                                  className={`appearance-none text-xs pl-7 pr-8 py-1.5 rounded-lg border bg-background cursor-pointer ${statusMeta.cls} border-current/30`}
                                >
                                  {STATUS_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                  ))}
                                </select>
                                <StatusIcon size={12} className={`absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none ${statusMeta.cls}`} />
                              </div>
                            </div>
                          </div>

                          {/* Notater (vises alltid) */}
                          <div className="mt-2 flex items-center gap-2">
                            <input
                              type="text"
                              placeholder="Notater / dokumentasjon (valgfritt)…"
                              value={loc.evidence_notes}
                              onChange={e => setField(a.assignment_id, "evidence_notes", e.target.value)}
                              className="flex-1 text-xs px-2.5 py-1.5 bg-background border border-border rounded-lg outline-none placeholder:text-muted-foreground/50 focus:border-primary/50"
                            />
                            <input
                              type="date"
                              title="Neste revisjonsdato"
                              value={loc.next_review_date}
                              onChange={e => setField(a.assignment_id, "next_review_date", e.target.value)}
                              className="text-xs px-2 py-1.5 bg-background border border-border rounded-lg outline-none text-muted-foreground focus:border-primary/50"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {/* Lagre-knapp nederst */}
        {dirtyCount > 0 && (
          <div className="sticky bottom-4 flex justify-center">
            <button
              onClick={saveAll}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-xl shadow-2xl text-sm font-semibold hover:bg-primary/90 disabled:opacity-50 transition-all"
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Lagre {dirtyCount} ulagrede vurderinger
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
