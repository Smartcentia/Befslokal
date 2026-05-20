"use client";

import { useState, useEffect, useRef } from "react";
import { deviationService, CreateDeviationDTO } from "@/lib/domains/fdv/deviationService";
import { getProperties, Property } from "@/lib/api";
import { X, Save, AlertTriangle, Camera, ImagePlus, Trash2 } from "lucide-react";

interface DeviationCreateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated: () => void;
}

export default function DeviationCreateModal({ isOpen, onClose, onCreated }: DeviationCreateModalProps) {
    const [properties, setProperties] = useState<Property[]>([]);
    const [loading, setLoading] = useState(false);

    // Form State
    const [propertyId, setPropertyId] = useState("");
    const [title, setTitle] = useState("");
    const [priority, setPriority] = useState("medium");
    const [description, setDescription] = useState("");
    const [dueDate, setDueDate] = useState("");

    // Bilde-state
    const [images, setImages] = useState<File[]>([]);
    const [previews, setPreviews] = useState<string[]>([]);
    const [uploadStatus, setUploadStatus] = useState<string>("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            getProperties().then(setProperties);
        }
    }, [isOpen]);

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files ?? []);
        if (files.length === 0) return;
        setImages((prev) => [...prev, ...files]);
        files.forEach((f) => {
            const reader = new FileReader();
            reader.onload = (ev) => setPreviews((prev) => [...prev, ev.target?.result as string]);
            reader.readAsDataURL(f);
        });
        // Reset input så samme fil kan velges igjen
        e.target.value = "";
    };

    const removeImage = (idx: number) => {
        setImages((prev) => prev.filter((_, i) => i !== idx));
        setPreviews((prev) => prev.filter((_, i) => i !== idx));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setUploadStatus("");

        try {
            const created = await deviationService.create({
                property_id: propertyId,
                title,
                description,
                priority,
                due_date: dueDate || undefined,
            });

            // Last opp bilder etter avviket er opprettet
            if (images.length > 0) {
                for (let i = 0; i < images.length; i++) {
                    setUploadStatus(`Laster opp bilde ${i + 1} av ${images.length}...`);
                    await deviationService.uploadImage(created.id, images[i]);
                }
            }

            onCreated();
            onClose();
            // Reset form
            setPropertyId(""); setTitle(""); setPriority("medium");
            setDescription(""); setDueDate("");
            setImages([]); setPreviews([]); setUploadStatus("");
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
                        <select
                            required
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all font-sans p-2 border"
                            value={propertyId}
                            onChange={(e) => setPropertyId(e.target.value)}
                        >
                            <option value="">Velg eiendom...</option>
                            {properties.map(p => (
                                <option key={p.property_id} value={p.property_id}>{p.address}, {p.city}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Tittel</label>
                        <input
                            required
                            type="text"
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all p-2 border"
                            placeholder="F.eks. Vannlekkasje i kjeller"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Prioritet</label>
                        <div className="flex gap-2">
                            {['low', 'medium', 'high', 'critical'].map((level) => (
                                <button
                                    key={level}
                                    type="button"
                                    onClick={() => setPriority(level)}
                                    className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border transition-all capitalize ${priority === level
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
                        <label className="block text-sm font-medium text-foreground mb-1">Frist (Valgfritt)</label>
                        <input
                            type="date"
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all p-2 border"
                            value={dueDate}
                            onChange={(e) => setDueDate(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Beskrivelse</label>
                        <textarea
                            className="w-full rounded-lg border-border bg-background text-foreground focus:ring-2 focus:ring-primary transition-all font-mono text-sm p-2 border"
                            rows={4}
                            placeholder="Beskriv situasjonen nærmere..."
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>

                    {/* Bilder av skaden */}
                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            Bilder av skaden <span className="text-muted-foreground font-normal">(valgfritt)</span>
                        </label>

                        {/* Thumbnail-grid */}
                        {previews.length > 0 && (
                            <div className="grid grid-cols-3 gap-2 mb-3">
                                {previews.map((src, idx) => (
                                    <div key={idx} className="relative group rounded-lg overflow-hidden border border-border aspect-square">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img src={src} alt={`Bilde ${idx + 1}`} className="w-full h-full object-cover" />
                                        <button
                                            type="button"
                                            onClick={() => removeImage(idx)}
                                            className="absolute top-1 right-1 bg-black/60 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Skjulte file-inputs: én for kamera, én for galleri */}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            multiple
                            className="hidden"
                            onChange={handleImageChange}
                        />
                        <div className="flex gap-2">
                            {/* Kamera (bakre) — trigger capture-input */}
                            <label className="flex-1 cursor-pointer">
                                <input
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    className="hidden"
                                    onChange={handleImageChange}
                                />
                                <span className="flex items-center justify-center gap-1.5 px-3 py-2 border border-border rounded-lg text-sm text-muted-foreground hover:border-primary hover:text-primary transition w-full">
                                    <Camera size={15} /> Ta bilde
                                </span>
                            </label>
                            <button
                                type="button"
                                onClick={() => fileInputRef.current?.click()}
                                className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 border border-border rounded-lg text-sm text-muted-foreground hover:border-primary hover:text-primary transition"
                            >
                                <ImagePlus size={15} /> Velg fra enhet
                            </button>
                        </div>
                        {images.length > 0 && (
                            <p className="text-xs text-muted-foreground mt-1">{images.length} bilde{images.length !== 1 ? "r" : ""} valgt</p>
                        )}
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
                            {loading ? (uploadStatus || 'Lagrer...') : <>
                                <Save size={18} />
                                Lagre Avvik{images.length > 0 ? ` + ${images.length} bilde${images.length !== 1 ? 'r' : ''}` : ''}
                            </>}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
