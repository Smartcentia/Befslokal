"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
    Building2,
    Layers,
    DoorOpen,
    ChevronDown,
    ChevronRight,
    Plus,
    Trash2,
    ArrowLeft,
    Upload,
    FileCode,
    CheckCircle2,
    AlertTriangle,
    RefreshCw,
} from "lucide-react";
import {
    buildingApi,
    type Building,
    type Floor,
    type Space,
    type UnitRef,
    type PropertyStructure,
} from "@/lib/api/buildingApi";

// ---------------------------------------------------------------------------
// Small reusable helpers
// ---------------------------------------------------------------------------

function KPICard({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
    return (
        <div className="bg-card border border-border rounded-xl p-5 flex items-center gap-4">
            <div className="text-primary">{icon}</div>
            <div>
                <div className="text-2xl font-bold text-foreground">{value}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-medium">{label}</div>
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Modal component
// ---------------------------------------------------------------------------

interface ModalProps {
    title: string;
    onClose: () => void;
    children: React.ReactNode;
}

function Modal({ title, onClose, children }: ModalProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-foreground">{title}</h3>
                    <button
                        onClick={onClose}
                        className="text-muted-foreground hover:text-foreground text-xl leading-none"
                    >
                        ×
                    </button>
                </div>
                {children}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function PropertyStructurePage() {
    const params = useParams();
    const propertyId = params?.id as string;

    const [structure, setStructure] = useState<PropertyStructure | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Collapsed state for buildings/floors
    const [collapsedBuildings, setCollapsedBuildings] = useState<Set<string>>(new Set());
    const [collapsedFloors, setCollapsedFloors] = useState<Set<string>>(new Set());

    // Modal state
    const [showAddBuilding, setShowAddBuilding] = useState(false);
    const [showAddFloor, setShowAddFloor] = useState<string | null>(null); // building_id
    const [showAddSpace, setShowAddSpace] = useState<{ floorId: string; propId: string } | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // IFC import state
    const [showIFCUpload, setShowIFCUpload] = useState(false);
    const [ifcFile, setIfcFile] = useState<File | null>(null);
    const [ifcPreview, setIfcPreview] = useState<Record<string, unknown> | null>(null);
    const [ifcParsing, setIfcParsing] = useState(false);
    const [ifcImporting, setIfcImporting] = useState(false);
    const [ifcResult, setIfcResult] = useState<Record<string, unknown> | null>(null);

    // Form state
    const [buildingForm, setBuildingForm] = useState({ name: "", building_code: "", year_built: "", building_type: "main" });
    const [floorForm, setFloorForm] = useState({ floor_number: "0", name: "" });
    const [spaceForm, setSpaceForm] = useState({ name: "", space_type: "room", area_sqm: "" });

    const loadStructure = useCallback(async () => {
        if (!propertyId) return;
        setLoading(true);
        setError(null);
        try {
            const data = await buildingApi.getPropertyStructure(propertyId);
            setStructure(data);
        } catch (err) {
            setError("Kunne ikke laste bygningsstruktur. Sjekk at backend er oppe.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [propertyId]);

    useEffect(() => {
        loadStructure();
    }, [loadStructure]);

    // ---------------------------------------------------------------------------
    // Derived KPIs
    // ---------------------------------------------------------------------------
    const kpiBuildings = structure?.buildings.length ?? 0;
    const kpiFloors = structure?.buildings.reduce((acc, b) => acc + b.floors.length, 0) ?? 0;
    const kpiSpaces =
        structure?.buildings.reduce(
            (acc, b) => acc + b.floors.reduce((fa, f) => fa + (f.spaces?.length ?? 0), 0),
            0
        ) ?? 0;

    // ---------------------------------------------------------------------------
    // Toggle helpers
    // ---------------------------------------------------------------------------
    const toggleBuilding = (id: string) =>
        setCollapsedBuildings((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });

    const toggleFloor = (id: string) =>
        setCollapsedFloors((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });

    // ---------------------------------------------------------------------------
    // CRUD handlers
    // ---------------------------------------------------------------------------
    const handleCreateBuilding = async () => {
        if (!buildingForm.name.trim()) return;
        setSubmitting(true);
        try {
            await buildingApi.createBuilding({
                property_id: propertyId,
                name: buildingForm.name.trim(),
                building_code: buildingForm.building_code || undefined,
                year_built: buildingForm.year_built ? parseInt(buildingForm.year_built) : undefined,
                building_type: buildingForm.building_type || "main",
            });
            setBuildingForm({ name: "", building_code: "", year_built: "", building_type: "main" });
            setShowAddBuilding(false);
            await loadStructure();
        } catch {
            alert("Kunne ikke opprette bygg.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteBuilding = async (buildingId: string) => {
        if (!confirm("Slette bygget og alt innhold?")) return;
        try {
            await buildingApi.deleteBuilding(buildingId);
            await loadStructure();
        } catch {
            alert("Sletting feilet.");
        }
    };

    const handleCreateFloor = async () => {
        if (!showAddFloor) return;
        setSubmitting(true);
        try {
            await buildingApi.createFloor(showAddFloor, {
                floor_number: parseInt(floorForm.floor_number),
                name: floorForm.name || undefined,
            });
            setFloorForm({ floor_number: "0", name: "" });
            setShowAddFloor(null);
            await loadStructure();
        } catch {
            alert("Kunne ikke opprette etasje.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteFloor = async (floorId: string) => {
        if (!confirm("Slette etasjen og alle rom?")) return;
        try {
            await buildingApi.deleteFloor(floorId);
            await loadStructure();
        } catch {
            alert("Sletting feilet.");
        }
    };

    const handleCreateSpace = async () => {
        if (!showAddSpace || !spaceForm.name.trim()) return;
        setSubmitting(true);
        try {
            await buildingApi.createSpace(showAddSpace.floorId, {
                property_id: showAddSpace.propId,
                name: spaceForm.name.trim(),
                space_type: spaceForm.space_type || "room",
                area_sqm: spaceForm.area_sqm ? parseFloat(spaceForm.area_sqm) : undefined,
            });
            setSpaceForm({ name: "", space_type: "room", area_sqm: "" });
            setShowAddSpace(null);
            await loadStructure();
        } catch {
            alert("Kunne ikke opprette rom.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteSpace = async (spaceId: string) => {
        if (!confirm("Slette rommet?")) return;
        try {
            await buildingApi.deleteSpace(spaceId);
            await loadStructure();
        } catch {
            alert("Sletting feilet.");
        }
    };

    // ---------------------------------------------------------------------------
    // Render
    // ---------------------------------------------------------------------------
    // ── IFC helpers ──────────────────────────────────────────────────────────
    const handleIFCPreview = async () => {
        if (!ifcFile || !propertyId) return;
        setIfcParsing(true);
        setIfcPreview(null);
        try {
            const { fetchAPI } = await import("@/lib/api/client");
            const form = new FormData();
            form.append("file", ifcFile);
            const data = await fetchAPI(`/fdvu/ifc/${propertyId}/parse`, {
                method: "POST",
                body: form,
            });
            setIfcPreview(data as Record<string, unknown>);
        } catch (e: unknown) {
            alert(`Parse feilet: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIfcParsing(false);
        }
    };

    const handleIFCImport = async () => {
        if (!ifcFile || !propertyId) return;
        if (!confirm(`Importer bygningsstruktur fra ${ifcFile.name}?\nEksisterende bygg/etasjer/rom oppdateres, nye opprettes.`)) return;
        setIfcImporting(true);
        try {
            const { fetchAPI } = await import("@/lib/api/client");
            const form = new FormData();
            form.append("file", ifcFile);
            const data = await fetchAPI(`/fdvu/ifc/${propertyId}/import`, {
                method: "POST",
                body: form,
            });
            setIfcResult(data as Record<string, unknown>);
            await loadStructure(); // refresh structure
        } catch (e: unknown) {
            alert(`Import feilet: ${e instanceof Error ? e.message : String(e)}`);
        } finally {
            setIfcImporting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground p-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
                <Link
                    href={`/properties/${propertyId}`}
                    className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors font-medium text-sm"
                >
                    <ArrowLeft size={16} />
                    Tilbake til eiendom
                </Link>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowIFCUpload(true)}
                        className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted/30 transition-colors text-foreground"
                    >
                        <FileCode size={15} />
                        IFC-import
                    </button>
                    <Link
                        href={`/properties/${propertyId}/simba`}
                        className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted/30 transition-colors text-foreground"
                    >
                        <CheckCircle2 size={15} />
                        SIMBA 2.1
                    </Link>
                    <button
                        onClick={() => setShowAddBuilding(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
                    >
                        <Plus size={16} />
                        Legg til bygg
                    </button>
                </div>
            </div>

            <h1 className="text-2xl font-bold text-foreground mb-2 flex items-center gap-3">
                <Building2 size={28} className="text-primary" />
                Bygningsstruktur
            </h1>
            <p className="text-muted-foreground text-sm mb-6">
                Hierarki: Bygg → Etasje → Rom/Enheter
            </p>

            {/* KPI cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <KPICard label="Bygg" value={kpiBuildings} icon={<Building2 size={24} />} />
                <KPICard label="Etasjer" value={kpiFloors} icon={<Layers size={24} />} />
                <KPICard label="Rom" value={kpiSpaces} icon={<DoorOpen size={24} />} />
            </div>

            {/* Error / Loading */}
            {loading && (
                <div className="text-muted-foreground text-sm py-12 text-center">Laster struktur...</div>
            )}
            {error && (
                <div className="text-red-500 text-sm py-4 text-center">{error}</div>
            )}

            {/* Building tree */}
            {!loading && !error && structure && (
                <div className="space-y-4">
                    {structure.buildings.length === 0 && (
                        <div className="text-center text-muted-foreground border border-dashed border-border rounded-xl py-12">
                            Ingen bygg registrert enda. Klikk «Legg til bygg» for å starte.
                        </div>
                    )}

                    {structure.buildings.map((building) => {
                        const isBuildingCollapsed = collapsedBuildings.has(building.building_id);
                        return (
                            <div
                                key={building.building_id}
                                className="border border-border rounded-xl overflow-hidden bg-card"
                            >
                                {/* Building header */}
                                <div className="flex items-center justify-between px-5 py-4 bg-card border-b border-border">
                                    <button
                                        onClick={() => toggleBuilding(building.building_id)}
                                        className="flex items-center gap-3 text-left flex-1 min-w-0"
                                    >
                                        {isBuildingCollapsed ? (
                                            <ChevronRight size={18} className="text-muted-foreground shrink-0" />
                                        ) : (
                                            <ChevronDown size={18} className="text-muted-foreground shrink-0" />
                                        )}
                                        <Building2 size={18} className="text-primary shrink-0" />
                                        <span className="font-bold text-foreground truncate">{building.name}</span>
                                        {building.building_code && (
                                            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded font-mono">
                                                {building.building_code}
                                            </span>
                                        )}
                                        {building.building_type && (
                                            <span className="text-xs text-muted-foreground hidden sm:inline">
                                                {building.building_type}
                                            </span>
                                        )}
                                        {building.year_built && (
                                            <span className="text-xs text-muted-foreground hidden sm:inline">
                                                bygd {building.year_built}
                                            </span>
                                        )}
                                    </button>
                                    <div className="flex items-center gap-2 ml-3 shrink-0">
                                        <button
                                            onClick={() => setShowAddFloor(building.building_id)}
                                            title="Legg til etasje"
                                            className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-border hover:bg-muted transition-colors text-foreground"
                                        >
                                            <Plus size={13} />
                                            Etasje
                                        </button>
                                        <button
                                            onClick={() => handleDeleteBuilding(building.building_id)}
                                            title="Slett bygg"
                                            className="p-1.5 text-muted-foreground hover:text-red-500 transition-colors"
                                        >
                                            <Trash2 size={15} />
                                        </button>
                                    </div>
                                </div>

                                {/* Floors */}
                                {!isBuildingCollapsed && (
                                    <div className="divide-y divide-border">
                                        {building.floors.length === 0 && (
                                            <div className="px-8 py-4 text-xs text-muted-foreground italic">
                                                Ingen etasjer registrert.
                                            </div>
                                        )}
                                        {building.floors.map((floor) => {
                                            const isFloorCollapsed = collapsedFloors.has(floor.floor_id);
                                            const floorSpaces: Space[] = floor.spaces ?? [];
                                            const floorUnits: UnitRef[] = floor.units ?? [];

                                            return (
                                                <div key={floor.floor_id} className="bg-card/50">
                                                    {/* Floor header */}
                                                    <div className="flex items-center justify-between px-8 py-3">
                                                        <button
                                                            onClick={() => toggleFloor(floor.floor_id)}
                                                            className="flex items-center gap-2 text-left flex-1 min-w-0"
                                                        >
                                                            {isFloorCollapsed ? (
                                                                <ChevronRight size={15} className="text-muted-foreground shrink-0" />
                                                            ) : (
                                                                <ChevronDown size={15} className="text-muted-foreground shrink-0" />
                                                            )}
                                                            <Layers size={15} className="text-primary shrink-0" />
                                                            <span className="font-semibold text-sm text-foreground">
                                                                {floor.name || `Etasje ${floor.floor_number}`}
                                                            </span>
                                                            <span className="text-xs text-muted-foreground">
                                                                ({floorSpaces.length} rom, {floorUnits.length} enheter)
                                                            </span>
                                                        </button>
                                                        <div className="flex items-center gap-2 ml-3 shrink-0">
                                                            <button
                                                                onClick={() =>
                                                                    setShowAddSpace({
                                                                        floorId: floor.floor_id,
                                                                        propId: propertyId,
                                                                    })
                                                                }
                                                                title="Legg til rom"
                                                                className="flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded-lg border border-border hover:bg-muted transition-colors text-foreground"
                                                            >
                                                                <Plus size={12} />
                                                                Rom
                                                            </button>
                                                            <button
                                                                onClick={() => handleDeleteFloor(floor.floor_id)}
                                                                title="Slett etasje"
                                                                className="p-1 text-muted-foreground hover:text-red-500 transition-colors"
                                                            >
                                                                <Trash2 size={13} />
                                                            </button>
                                                        </div>
                                                    </div>

                                                    {/* Spaces & Units */}
                                                    {!isFloorCollapsed && (
                                                        <div className="px-12 pb-4 space-y-2">
                                                            {floorSpaces.length === 0 && floorUnits.length === 0 && (
                                                                <p className="text-xs text-muted-foreground italic">Ingen rom eller enheter.</p>
                                                            )}

                                                            {/* Spaces */}
                                                            {floorSpaces.map((space) => (
                                                                <div
                                                                    key={space.space_id}
                                                                    className="flex items-center justify-between rounded-lg border border-border px-3 py-2 bg-background text-sm"
                                                                >
                                                                    <div className="flex items-center gap-2 min-w-0">
                                                                        <DoorOpen size={14} className="text-muted-foreground shrink-0" />
                                                                        <span className="font-medium text-foreground truncate">{space.name}</span>
                                                                        {space.space_type && (
                                                                            <span className="text-xs text-muted-foreground hidden sm:inline">
                                                                                {space.space_type}
                                                                            </span>
                                                                        )}
                                                                        {space.area_sqm != null && (
                                                                            <span className="text-xs text-muted-foreground">
                                                                                {space.area_sqm} m²
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <button
                                                                        onClick={() => handleDeleteSpace(space.space_id)}
                                                                        className="p-1 text-muted-foreground hover:text-red-500 transition-colors shrink-0"
                                                                    >
                                                                        <Trash2 size={12} />
                                                                    </button>
                                                                </div>
                                                            ))}

                                                            {/* Units on this floor */}
                                                            {floorUnits.map((unit) => (
                                                                <div
                                                                    key={unit.unit_id}
                                                                    className="flex items-center gap-2 rounded-lg border border-border/50 px-3 py-2 bg-primary/5 text-sm"
                                                                >
                                                                    <span className="text-xs font-bold text-primary uppercase tracking-wider shrink-0">
                                                                        Enhet
                                                                    </span>
                                                                    <span className="text-foreground truncate">
                                                                        {unit.address || unit.purpose || unit.unit_id.slice(0, 8)}
                                                                    </span>
                                                                    {unit.area_sqm != null && (
                                                                        <span className="text-xs text-muted-foreground ml-auto">
                                                                            {unit.area_sqm} m²
                                                                        </span>
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
                            </div>
                        );
                    })}

                    {/* Unassigned units */}
                    {structure.unassigned_units.length > 0 && (
                        <div className="border border-border rounded-xl overflow-hidden bg-card">
                            <div className="px-5 py-3 border-b border-border bg-muted/30">
                                <span className="text-sm font-semibold text-muted-foreground">
                                    Enheter uten bygg ({structure.unassigned_units.length})
                                </span>
                            </div>
                            <div className="px-5 py-3 space-y-2">
                                {structure.unassigned_units.map((unit) => (
                                    <div
                                        key={unit.unit_id}
                                        className="flex items-center gap-2 text-sm text-foreground px-3 py-2 rounded-lg border border-border/50 bg-background"
                                    >
                                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider shrink-0">
                                            Enhet
                                        </span>
                                        <span className="truncate">
                                            {unit.address || unit.purpose || unit.unit_id.slice(0, 8)}
                                        </span>
                                        {unit.area_sqm != null && (
                                            <span className="text-xs text-muted-foreground ml-auto">
                                                {unit.area_sqm} m²
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* --------------- Modals --------------- */}

            {showAddBuilding && (
                <Modal title="Legg til bygg" onClose={() => setShowAddBuilding(false)}>
                    <div className="space-y-3">
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Navn *
                            </label>
                            <input
                                type="text"
                                value={buildingForm.name}
                                onChange={(e) => setBuildingForm((f) => ({ ...f, name: e.target.value }))}
                                placeholder="Bygg A"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Kode
                            </label>
                            <input
                                type="text"
                                value={buildingForm.building_code}
                                onChange={(e) => setBuildingForm((f) => ({ ...f, building_code: e.target.value }))}
                                placeholder="A"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Byggeår
                            </label>
                            <input
                                type="number"
                                value={buildingForm.year_built}
                                onChange={(e) => setBuildingForm((f) => ({ ...f, year_built: e.target.value }))}
                                placeholder="2005"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Type
                            </label>
                            <select
                                value={buildingForm.building_type}
                                onChange={(e) => setBuildingForm((f) => ({ ...f, building_type: e.target.value }))}
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="main">Hovedbygg</option>
                                <option value="annex">Anneks</option>
                                <option value="garage">Garasje</option>
                            </select>
                        </div>
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={handleCreateBuilding}
                                disabled={submitting || !buildingForm.name.trim()}
                                className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                            >
                                {submitting ? "Oppretter..." : "Opprett bygg"}
                            </button>
                            <button
                                onClick={() => setShowAddBuilding(false)}
                                className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                            >
                                Avbryt
                            </button>
                        </div>
                    </div>
                </Modal>
            )}

            {showAddFloor !== null && (
                <Modal title="Legg til etasje" onClose={() => setShowAddFloor(null)}>
                    <div className="space-y-3">
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Etasjenummer *
                            </label>
                            <input
                                type="number"
                                value={floorForm.floor_number}
                                onChange={(e) => setFloorForm((f) => ({ ...f, floor_number: e.target.value }))}
                                placeholder="0 = bakkeplan, -1 = kjeller"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Navn (valgfritt)
                            </label>
                            <input
                                type="text"
                                value={floorForm.name}
                                onChange={(e) => setFloorForm((f) => ({ ...f, name: e.target.value }))}
                                placeholder="1. etasje"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={handleCreateFloor}
                                disabled={submitting}
                                className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                            >
                                {submitting ? "Oppretter..." : "Opprett etasje"}
                            </button>
                            <button
                                onClick={() => setShowAddFloor(null)}
                                className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                            >
                                Avbryt
                            </button>
                        </div>
                    </div>
                </Modal>
            )}

            {showAddSpace !== null && (
                <Modal title="Legg til rom" onClose={() => setShowAddSpace(null)}>
                    <div className="space-y-3">
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Navn *
                            </label>
                            <input
                                type="text"
                                value={spaceForm.name}
                                onChange={(e) => setSpaceForm((f) => ({ ...f, name: e.target.value }))}
                                placeholder="Rom 101"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Type
                            </label>
                            <select
                                value={spaceForm.space_type}
                                onChange={(e) => setSpaceForm((f) => ({ ...f, space_type: e.target.value }))}
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="room">Rom</option>
                                <option value="office">Kontor</option>
                                <option value="kitchen">Kjøkken</option>
                                <option value="bathroom">Bad</option>
                                <option value="corridor">Gang/Korridor</option>
                                <option value="storage">Lager</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                                Areal (m²)
                            </label>
                            <input
                                type="number"
                                value={spaceForm.area_sqm}
                                onChange={(e) => setSpaceForm((f) => ({ ...f, area_sqm: e.target.value }))}
                                placeholder="25"
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            />
                        </div>
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={handleCreateSpace}
                                disabled={submitting || !spaceForm.name.trim()}
                                className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                            >
                                {submitting ? "Oppretter..." : "Opprett rom"}
                            </button>
                            <button
                                onClick={() => setShowAddSpace(null)}
                                className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-foreground hover:bg-muted transition-colors"
                            >
                                Avbryt
                            </button>
                        </div>
                    </div>
                </Modal>
            )}

            {/* ── IFC Upload Modal ──────────────────────────────────────────── */}
            {showIFCUpload && (
                <Modal title="Importer bygningsstruktur fra IFC" onClose={() => {
                    setShowIFCUpload(false);
                    setIfcFile(null);
                    setIfcPreview(null);
                    setIfcResult(null);
                }}>
                    <div className="space-y-4">
                        {/* Forklaring */}
                        <div className="flex items-start gap-2 text-xs text-muted bg-muted/20 rounded-lg p-3">
                            <FileCode size={14} className="mt-0.5 flex-shrink-0" />
                            <div>
                                Laster opp en IFC-fil (IFC2x3 eller IFC4) og oppretter automatisk
                                Bygg → Etasje → Rom. Eksisterende poster oppdateres — ingenting slettes.
                                Kompatibel med Statsbygg SIMBA og alle BIM-verktøy.
                            </div>
                        </div>

                        {/* Filopplasting */}
                        {!ifcResult && (
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-2">
                                    IFC-fil (.ifc)
                                </label>
                                <input
                                    type="file"
                                    accept=".ifc"
                                    onChange={e => {
                                        setIfcFile(e.target.files?.[0] ?? null);
                                        setIfcPreview(null);
                                    }}
                                    className="w-full text-sm border border-border rounded-lg px-3 py-2 bg-background"
                                />
                                {ifcFile && (
                                    <div className="text-xs text-muted mt-1">
                                        {ifcFile.name} · {(ifcFile.size / 1024 / 1024).toFixed(1)} MB
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Preview-resultater */}
                        {ifcPreview && !ifcResult && (
                            <div className="border border-border rounded-lg p-4 space-y-3">
                                <div className="font-medium text-sm flex items-center gap-2">
                                    <CheckCircle2 size={14} className="text-green-600" />
                                    Forhåndsvisning — ingenting lagret ennå
                                </div>
                                <div className="grid grid-cols-3 gap-3 text-center">
                                    {[
                                        { label: "Bygg", val: (ifcPreview.stats as Record<string,number>)?.buildings ?? 0 },
                                        { label: "Etasjer", val: (ifcPreview.stats as Record<string,number>)?.floors ?? 0 },
                                        { label: "Rom", val: (ifcPreview.stats as Record<string,number>)?.spaces ?? 0 },
                                    ].map(k => (
                                        <div key={k.label} className="bg-primary/5 rounded-lg p-3">
                                            <div className="text-xl font-bold text-primary">{k.val}</div>
                                            <div className="text-xs text-muted">{k.label}</div>
                                        </div>
                                    ))}
                                </div>
                                <div className="text-xs text-muted">
                                    Schema: {ifcPreview.schema as string} · Prosjekt: {ifcPreview.project_name as string}
                                </div>
                                {(ifcPreview.warnings as string[])?.length > 0 && (
                                    <div className="flex items-start gap-2 text-xs text-amber-700 bg-amber-50 rounded p-2">
                                        <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
                                        {(ifcPreview.warnings as string[]).join(" · ")}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Import-resultat */}
                        {ifcResult && (
                            <div className="border border-green-200 bg-green-50 rounded-lg p-4 space-y-2">
                                <div className="font-medium text-sm text-green-800 flex items-center gap-2">
                                    <CheckCircle2 size={14} />
                                    Import fullført!
                                </div>
                                {(() => {
                                    const c = ifcResult.created as Record<string,number>;
                                    return (
                                        <div className="text-xs text-green-700 space-y-1">
                                            <div>Nye bygg: {c?.buildings ?? 0} · Nye etasjer: {c?.floors ?? 0} · Nye rom: {c?.spaces ?? 0}</div>
                                            <div>BIM-objekter: {c?.bim_objects ?? 0} · Oppdaterte poster: {c?.updated ?? 0}</div>
                                        </div>
                                    );
                                })()}
                            </div>
                        )}

                        {/* Knapper */}
                        <div className="flex gap-2 justify-end pt-2">
                            {!ifcResult && (
                                <>
                                    <button
                                        onClick={handleIFCPreview}
                                        disabled={!ifcFile || ifcParsing}
                                        className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm hover:bg-muted/20 disabled:opacity-50"
                                    >
                                        {ifcParsing
                                            ? <><RefreshCw size={13} className="animate-spin" /> Parser…</>
                                            : <><Upload size={13} /> Forhåndsvis</>
                                        }
                                    </button>
                                    {ifcPreview && (
                                        <button
                                            onClick={handleIFCImport}
                                            disabled={ifcImporting}
                                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:opacity-90 disabled:opacity-50"
                                        >
                                            {ifcImporting
                                                ? <><RefreshCw size={13} className="animate-spin" /> Importerer…</>
                                                : <><CheckCircle2 size={13} /> Importer til BEFS</>
                                            }
                                        </button>
                                    )}
                                </>
                            )}
                            {ifcResult && (
                                <button
                                    onClick={() => { setShowIFCUpload(false); setIfcFile(null); setIfcPreview(null); setIfcResult(null); }}
                                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold"
                                >
                                    Lukk
                                </button>
                            )}
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}
