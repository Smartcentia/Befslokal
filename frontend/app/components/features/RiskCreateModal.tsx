"use client";

import { useState, useEffect } from "react";
import { createRiskAssessment, getProperties, Property } from "@/lib/api";
import { X, Save, AlertTriangle } from "lucide-react";

interface RiskCreateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated: () => void;
}

export default function RiskCreateModal({ isOpen, onClose, onCreated }: RiskCreateModalProps) {
    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(false);

    // Form State
    const [propertyId, setPropertyId] = useState("");
    const [type, setType] = useState("");
    const [severity, setSeverity] = useState("Medium");
    const [description, setDescription] = useState("");

    useEffect(() => {
        if (isOpen) {
            // Load properties for dropdown
            getProperties().then(setProperties);
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await createRiskAssessment({
                property_id: propertyId,
                risk_category: severity,
                risk_type: type,
                severity: severity,
                description: description
            });
            onCreated();
            onClose();
            // Reset form
            setPropertyId("");
            setType("");
            setSeverity("Medium");
            setDescription("");
        } catch (err) {
            console.error(err);
            alert("Kunne ikke opprette avvik.");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay backdrop-blur-sm">
            <div className="bg-surface rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-4 border-b border-border bg-muted/10">
                    <h2 className="text-lg font-bold text-foreground flex items-center gap-2">
                        <AlertTriangle className="text-red-500" size={20} />
                        Meld nytt avvik
                    </h2>
                    <button onClick={onClose} className="p-1 hover:bg-muted/10 rounded-full transition-colors">
                        <X size={20} className="text-muted" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Eiendom</label>
                        <div className="flex gap-2">
                            <select
                                required
                                className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all font-sans"
                                value={propertyId}
                                onChange={(e) => setPropertyId(e.target.value)}
                            >
                                <option value="">Velg eiendom...</option>
                                {properties.map(p => (
                                    <option key={p.property_id} value={p.property_id}>{p.address}, {p.city}</option>
                                ))}
                            </select>
                            <button
                                type="button"
                                onClick={async () => {
                                    if (!propertyId) return alert("Velg eiendom før analyse.");
                                    setLoading(true);
                                    try {
                                        const { analyzeRisk } = await import("@/lib/api");
                                        const data = await analyzeRisk(propertyId);
                                        if (data) {
                                            // Auto-fill form based on findings
                                            const floodForecast = data.flood_forecast;
                                            if (floodForecast && floodForecast.status !== "not_available") {
                                                setType("Mulig flomfare (Auto-detektert)");
                                                setSeverity("High");
                                                setDescription(JSON.stringify(floodForecast, null, 2));
                                            } else {
                                                setDescription("Analyse fullført: Ingen umiddelbare varsler funnet via NVE.");
                                            }
                                        }
                                    } catch (e) {
                                        console.error(e);
                                        alert("Analyse feilet.");
                                    } finally {
                                        setLoading(false);
                                    }
                                }}
                                className="px-3 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors border border-primary/20 text-sm font-medium whitespace-nowrap"
                            >
                                ✨ Analyser med AI
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Tittel / Type avvik</label>
                        <input
                            required
                            type="text"
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all"
                            placeholder="F.eks. Vannlekkasje i kjeller"
                            value={type}
                            onChange={(e) => setType(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Alvorlighetsgrad</label>
                        <div className="flex gap-2">
                            {['Low', 'Medium', 'High', 'Critical'].map((level) => (
                                <button
                                    key={level}
                                    type="button"
                                    onClick={() => setSeverity(level)}
                                    className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border transition-all ${severity === level
                                        ? 'bg-foreground text-background border-foreground shadow-md transform scale-105'
                                        : 'bg-background text-muted border-border hover:border-foreground/50'
                                        }`}
                                >
                                    {level}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Beskrivelse</label>
                        <textarea
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all font-mono text-sm"
                            rows={5}
                            placeholder="Beskriv situasjonen nærmere..."
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>

                    <div className="pt-4 flex gap-3 justify-end border-t border-border mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-muted font-medium hover:bg-muted/10 rounded-lg transition-colors"
                        >
                            Avbryt
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
                        >
                            {loading ? 'Lagrer...' : <>
                                <Save size={18} />
                                Lagre Avvik
                            </>}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
