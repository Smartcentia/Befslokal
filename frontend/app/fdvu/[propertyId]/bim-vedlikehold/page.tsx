"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    Wrench,
    ArrowLeft,
    AlertTriangle,
    CheckCircle2,
    Clock,
    Plus,
    ChevronDown,
    ChevronRight,
    Cpu,
} from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

// ─── Types ────────────────────────────────────────────────────────────────────

interface LinkedComponent {
    component_id: string;
    name: string;
    status: string;
}

interface BIMEquipmentItem {
    object_id: string;
    ifc_guid: string | null;
    name: string;
    type: string;
    pos_x: number | null;
    pos_y: number | null;
    pos_z: number | null;
    linked_component: LinkedComponent | null;
    plans_count: number;
    next_due_date: string | null;
    is_overdue: boolean;
}

// ─── Type-navn (norsk) ────────────────────────────────────────────────────────

const TYPE_LABELS: Record<string, string> = {
    IfcBoiler:                 "Kjele",
    IfcChiller:                "Kjølemaskin",
    IfcPump:                   "Pumpe",
    IfcUnitaryEquipment:       "Luftbehandlingsaggregat",
    IfcFlowTerminal:           "Strømningsterminal",
    IfcAirTerminal:            "Luftterminal",
    IfcElectricAppliance:      "Elektrisk apparat",
    IfcLightFixture:           "Armatyr",
    IfcFireSuppressionTerminal:"Brannslukker",
    IfcSanitaryTerminal:       "Sanitærarmatyr",
    IfcCoolingTower:           "Kjøletårn",
    IfcHeatExchanger:          "Varmeveksler",
};

// ─── Hjelpere ─────────────────────────────────────────────────────────────────

function MaintenanceStatusBadge({ item }: { item: BIMEquipmentItem }) {
    if (!item.linked_component) {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                Ingen plan
            </span>
        );
    }
    if (item.is_overdue) {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                <AlertTriangle className="w-3 h-3" /> Forfalt
            </span>
        );
    }
    if (item.plans_count > 0) {
        return (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                <CheckCircle2 className="w-3 h-3" /> {item.plans_count} plan{item.plans_count > 1 ? "er" : ""}
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
            <Clock className="w-3 h-3" /> Koblet, ingen plan
        </span>
    );
}

// ─── Hurtigopprett-modal ───────────────────────────────────────────────────────

function QuickCreateModal({
    item,
    onClose,
    onCreated,
}: {
    item: BIMEquipmentItem;
    onClose: () => void;
    onCreated: () => void;
}) {
    const [title, setTitle] = useState(`Vedlikehold – ${item.name}`);
    const [category, setCategory] = useState("preventive");
    const [freqMonths, setFreqMonths] = useState(12);
    const [role, setRole] = useState("contractor");
    const [cost, setCost] = useState("");
    const [ns3451, setNs3451] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(`/fdvu/maintenance/bim/${item.object_id}/quick-create`, {
                method: "POST",
                body: JSON.stringify({
                    title,
                    category,
                    frequency_months: freqMonths,
                    responsible_role: role,
                    estimated_cost_nok: cost ? parseFloat(cost) : null,
                    ns3451_code: ns3451 || null,
                }),
                headers: { "Content-Type": "application/json" },
            });
            onCreated();
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md shadow-xl">
                <h3 className="font-bold text-lg mb-1">Opprett vedlikeholdsplan</h3>
                <p className="text-sm text-muted-foreground mb-4">
                    <span className="font-mono text-xs">{item.type}</span> · {item.name}
                </p>

                <div className="space-y-3">
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1 block">Tittel</label>
                        <input
                            className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">Kategori</label>
                            <select
                                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                                value={category}
                                onChange={e => setCategory(e.target.value)}
                            >
                                <option value="preventive">Forebyggende</option>
                                <option value="inspection">Inspeksjon</option>
                                <option value="cleaning">Renhold</option>
                                <option value="corrective">Utbedring</option>
                                <option value="legal">Lovpålagt</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">Frekvens (mnd)</label>
                            <select
                                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                                value={freqMonths}
                                onChange={e => setFreqMonths(parseInt(e.target.value))}
                            >
                                {[1,3,6,12,24,36].map(m => (
                                    <option key={m} value={m}>{m === 1 ? "Månedlig" : m === 3 ? "Kvartalsvis" : m === 6 ? "Halvårlig" : m === 12 ? "Årlig" : `Hvert ${m/12}. år`}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">Ansvarlig</label>
                            <select
                                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                                value={role}
                                onChange={e => setRole(e.target.value)}
                            >
                                <option value="contractor">Leverandør</option>
                                <option value="janitor">Vaktmester</option>
                                <option value="property_manager">Eiendomsforvalter</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">Est. kostnad (kr)</label>
                            <input
                                type="number"
                                className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                                placeholder="0"
                                value={cost}
                                onChange={e => setCost(e.target.value)}
                            />
                        </div>
                    </div>
                    <div>
                        <label className="text-xs font-medium text-muted-foreground mb-1 block">NS 3451-kode (valgfritt)</label>
                        <input
                            className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background"
                            placeholder="f.eks. 363.1"
                            value={ns3451}
                            onChange={e => setNs3451(e.target.value)}
                        />
                    </div>
                </div>

                {error && (
                    <p className="mt-3 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
                )}

                <div className="flex gap-3 mt-5">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 border border-border rounded-lg text-sm hover:bg-muted/30 transition-colors"
                    >
                        Avbryt
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving || !title}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
                    >
                        {saving ? "Oppretter…" : "Opprett plan"}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ─── Hoved-komponent ──────────────────────────────────────────────────────────

export default function BIMVedlikehold() {
    const { propertyId } = useParams<{ propertyId: string }>();
    const router = useRouter();

    const [equipment, setEquipment] = useState<BIMEquipmentItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());
    const [quickCreateItem, setQuickCreateItem] = useState<BIMEquipmentItem | null>(null);

    const loadEquipment = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchAPI<{ equipment: BIMEquipmentItem[] }>(
                `/fdvu/maintenance/bim/${propertyId}/equipment`
            );
            setEquipment(data.equipment ?? []);
            // Åpne typer med forfalt automatisk
            const toOpen = new Set<string>();
            data.equipment?.forEach(e => { if (e.is_overdue) toOpen.add(e.type); });
            setExpandedTypes(toOpen.size ? toOpen : new Set(
                [...new Set(data.equipment?.map(e => e.type) ?? [])].slice(0, 2)
            ));
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }, [propertyId]);

    useEffect(() => { loadEquipment(); }, [loadEquipment]);

    const toggleType = (t: string) =>
        setExpandedTypes(prev => {
            const next = new Set(prev);
            next.has(t) ? next.delete(t) : next.add(t);
            return next;
        });

    // Grupper etter type
    const grouped = equipment.reduce<Record<string, BIMEquipmentItem[]>>((acc, item) => {
        (acc[item.type] = acc[item.type] ?? []).push(item);
        return acc;
    }, {});

    const totalWithPlan = equipment.filter(e => e.plans_count > 0).length;
    const totalOverdue  = equipment.filter(e => e.is_overdue).length;
    const totalNoPlan   = equipment.filter(e => !e.linked_component).length;

    return (
        <div className="min-h-screen bg-background text-foreground p-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex items-center gap-3 flex-wrap">
                <button
                    onClick={() => router.back()}
                    className="p-2 rounded-lg hover:bg-accent transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                </button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Wrench className="w-6 h-6" /> BIM-utstyr og vedlikehold
                    </h1>
                    <p className="text-sm text-muted-foreground">
                        Knytt driftsrelevant utstyr fra IFC-modellen til vedlikeholdsplaner
                    </p>
                </div>
            </div>

            {/* KPI-rad */}
            {!loading && equipment.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                    {[
                        { label: "Utstyrsobjekter", value: equipment.length, color: "text-foreground", icon: <Cpu className="w-4 h-4" /> },
                        { label: "Med vedlikeholdsplan", value: totalWithPlan, color: "text-green-600", icon: <CheckCircle2 className="w-4 h-4" /> },
                        { label: "Forfalt", value: totalOverdue, color: "text-red-600", icon: <AlertTriangle className="w-4 h-4" /> },
                        { label: "Uten plan", value: totalNoPlan, color: "text-yellow-600", icon: <Clock className="w-4 h-4" /> },
                    ].map(c => (
                        <div key={c.label} className="rounded-xl border border-border bg-card p-4 flex items-center gap-3">
                            <span className={c.color}>{c.icon}</span>
                            <div>
                                <p className={`text-xl font-bold ${c.color}`}>{c.value}</p>
                                <p className="text-xs text-muted-foreground">{c.label}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Feil */}
            {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 mb-6 text-red-700 text-sm">
                    {error}
                </div>
            )}

            {/* Laster */}
            {loading && (
                <div className="text-center py-16 text-muted-foreground">Laster utstyr fra BIM-modell…</div>
            )}

            {/* Tom tilstand */}
            {!loading && equipment.length === 0 && !error && (
                <div className="text-center py-16 text-muted-foreground">
                    <Cpu className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p className="font-medium">Ingen BIM-utstyr funnet</p>
                    <p className="text-sm mt-1">
                        Importer en IFC-fil med IfcBoiler, IfcPump, IfcAirTerminal e.l. først.
                    </p>
                    <button
                        onClick={() => router.push(`/properties/${propertyId}/structure`)}
                        className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm"
                    >
                        Gå til IFC-import
                    </button>
                </div>
            )}

            {/* Grupperte utstyrsobjekter */}
            {!loading && Object.keys(grouped).length > 0 && (
                <div className="space-y-3">
                    {Object.entries(grouped).map(([type, items]) => {
                        const isOpen = expandedTypes.has(type);
                        const overdue = items.filter(i => i.is_overdue).length;
                        const noPlan  = items.filter(i => !i.linked_component).length;
                        return (
                            <div key={type} className="rounded-xl border border-border overflow-hidden">
                                {/* Type-header */}
                                <button
                                    className="w-full px-5 py-4 flex items-center gap-3 text-left bg-card hover:bg-muted/20 transition-colors"
                                    onClick={() => toggleType(type)}
                                >
                                    <Cpu className="w-4 h-4 text-muted-foreground shrink-0" />
                                    <div className="flex-1">
                                        <span className="font-medium">{TYPE_LABELS[type] ?? type}</span>
                                        <span className="text-xs text-muted-foreground ml-2 font-mono">{type}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs">
                                        <span className="text-muted-foreground">{items.length} obj.</span>
                                        {overdue > 0 && (
                                            <span className="text-red-600 font-medium">{overdue} forfalt</span>
                                        )}
                                        {noPlan > 0 && (
                                            <span className="text-yellow-600 font-medium">{noPlan} u/plan</span>
                                        )}
                                    </div>
                                    {isOpen
                                        ? <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                        : <ChevronRight className="w-4 h-4 text-muted-foreground" />
                                    }
                                </button>

                                {/* Objektliste */}
                                {isOpen && (
                                    <div className="divide-y divide-border border-t border-border">
                                        {items.map(item => (
                                            <div key={item.object_id} className="px-5 py-3 flex items-center gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium">{item.name}</p>
                                                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                                                        {item.ifc_guid && (
                                                            <span className="font-mono">{item.ifc_guid.slice(0, 12)}…</span>
                                                        )}
                                                        {item.next_due_date && (
                                                            <span className={item.is_overdue ? "text-red-600" : ""}>
                                                                Neste: {item.next_due_date}
                                                            </span>
                                                        )}
                                                        {item.linked_component && (
                                                            <span>→ {item.linked_component.name}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <MaintenanceStatusBadge item={item} />
                                                {!item.linked_component && (
                                                    <button
                                                        onClick={() => setQuickCreateItem(item)}
                                                        className="flex items-center gap-1 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:opacity-90 transition-opacity"
                                                    >
                                                        <Plus className="w-3 h-3" /> Plan
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Hurtigopprett-modal */}
            {quickCreateItem && (
                <QuickCreateModal
                    item={quickCreateItem}
                    onClose={() => setQuickCreateItem(null)}
                    onCreated={async () => {
                        setQuickCreateItem(null);
                        await loadEquipment();
                    }}
                />
            )}
        </div>
    );
}
