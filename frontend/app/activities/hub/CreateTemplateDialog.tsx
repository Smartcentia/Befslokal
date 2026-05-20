"use client";

import React, { useState } from "react";
import { X, Save } from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

interface CreateTemplateDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (newTemplate: any) => void;
}

export default function CreateTemplateDialog({
    isOpen,
    onClose,
    onSuccess,
}: CreateTemplateDialogProps) {
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        title: "",
        description: "",
        category: "hms",
        priority: "medium",
        activity_type: "monthly",
        responsible_role: "vaktmester",
        recurrence_interval: 1,
        recurrence_unit: "months",
    });

    if (!isOpen) return null;

    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
    ) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Construct recurrence pattern
            let pattern: any = {
                frequency: "monthly",
                interval: Number(formData.recurrence_interval),
                day_of_month: 1,
            };

            if (formData.recurrence_unit === "days") {
                pattern = {
                    frequency: "daily",
                    interval: Number(formData.recurrence_interval),
                };
            } else if (formData.recurrence_unit === "weeks") {
                pattern = {
                    frequency: "weekly",
                    interval: Number(formData.recurrence_interval),
                    day_of_week: 1, // Monday
                };
            } else if (formData.recurrence_unit === "years") {
                pattern = {
                    frequency: "yearly",
                    interval: Number(formData.recurrence_interval),
                    month: 1,
                    day_of_month: 1,
                };
            }

            const payload = {
                title: formData.title,
                description: formData.description,
                category: formData.category,
                priority: formData.priority,
                activity_type: formData.activity_type,
                responsible_role: formData.responsible_role,
                recurrence_pattern: pattern,
                scope: "user",
            };

            const newTemplate = await fetchAPI("/hms/activities/templates", {
                method: "POST",
                body: JSON.stringify(payload),
            });

            onSuccess(newTemplate);
            onClose();
        } catch (error) {
            console.error("Failed to create template:", error);
            alert("Feil ved opprettelse av mal");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-card glass-card border border-border rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <h2 className="text-xl font-bold">Opprett ny aktivitetsmal</h2>
                    <button
                        onClick={onClose}
                        className="text-muted hover:text-foreground transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Tittel</label>
                            <input
                                type="text"
                                name="title"
                                required
                                value={formData.title}
                                onChange={handleChange}
                                className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                placeholder="F.eks. Månedlig sjekk av..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Beskrivelse</label>
                            <textarea
                                name="description"
                                rows={3}
                                value={formData.description}
                                onChange={handleChange}
                                className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                placeholder="Beskriv hva som skal gjøres..."
                            />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Kategori</label>
                                <select
                                    name="category"
                                    value={formData.category}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                >
                                    <option value="hms">HMS</option>
                                    <option value="brann">Brannvern</option>
                                    <option value="teknisk">Teknisk</option>
                                    <option value="inneklima">Inneklima</option>
                                    <option value="sikkerhet">Sikkerhet</option>
                                    <option value="utvendig">Utvendig</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Prioritet</label>
                                <select
                                    name="priority"
                                    value={formData.priority}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                >
                                    <option value="low">Lav</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">Høy</option>
                                    <option value="critical">Kritisk</option>
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Type</label>
                                <select
                                    name="activity_type"
                                    value={formData.activity_type}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                >
                                    <option value="adhoc">Ad-hoc</option>
                                    <option value="daily">Daglig</option>
                                    <option value="weekly">Ukentlig</option>
                                    <option value="monthly">Månedlig</option>
                                    <option value="quarterly">Kvartalsvis</option>
                                    <option value="annual">Årlig</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Intervall</label>
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        name="recurrence_interval"
                                        min="1"
                                        value={formData.recurrence_interval}
                                        onChange={handleChange}
                                        className="w-20 px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                    />
                                    <select
                                        name="recurrence_unit"
                                        value={formData.recurrence_unit}
                                        onChange={handleChange}
                                        className="flex-1 px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                    >
                                        <option value="days">Dager</option>
                                        <option value="weeks">Uker</option>
                                        <option value="months">Måneder</option>
                                        <option value="years">År</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Ansvarlig</label>
                                <select
                                    name="responsible_role"
                                    value={formData.responsible_role}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-background border border-input focus:ring-2 focus:ring-primary/50 outline-none"
                                >
                                    <option value="vaktmester">Vaktmester</option>
                                    <option value="eiendomsansvarlig">Eiendomsansvarlig</option>
                                    <option value="områdeleder">Områdeleder</option>
                                    <option value="leietaker">Leietaker</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-muted hover:bg-muted/10 transition-colors"
                        >
                            Avbryt
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex items-center gap-2 disabled:opacity-50"
                        >
                            {loading ? (
                                <span className="animate-spin">⏳</span>
                            ) : (
                                <Save size={18} />
                            )}
                            Lagre Mal
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
