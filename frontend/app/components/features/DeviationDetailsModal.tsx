"use client";

import { useState, useEffect } from "react";
import { Deviation, DeviationImage, AiAssessmentResult, deviationService } from "@/lib/domains/fdv/deviationService";
import { API_BASE_URL } from "@/lib/api/client";
import { X, AlertTriangle, List, FileText, Activity, Brain, Loader2, ImageIcon, TriangleAlert, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface DeviationDetailsModalProps {
    deviation: Deviation | null;
    onClose: () => void;
}

const SEVERITY_COLORS: Record<string, string> = {
    kritisk: "bg-red-100 text-red-700 border-red-300",
    høy: "bg-orange-100 text-orange-700 border-orange-300",
    middels: "bg-yellow-100 text-yellow-700 border-yellow-300",
    lav: "bg-green-100 text-green-700 border-green-300",
};

export default function DeviationDetailsModal({ deviation, onClose }: DeviationDetailsModalProps) {
    const [images, setImages] = useState<DeviationImage[]>([]);
    const [lightbox, setLightbox] = useState<string | null>(null);
    const [assessment, setAssessment] = useState<AiAssessmentResult | null>(null);
    const [assessing, setAssessing] = useState(false);
    const [assessError, setAssessError] = useState<string | null>(null);

    useEffect(() => {
        if (!deviation) return;
        setImages([]);
        setAssessment(null);
        setAssessError(null);
        deviationService.getImages(deviation.id).then(setImages);
    }, [deviation]);

    const handleAiAssess = async () => {
        if (!deviation) return;
        setAssessing(true);
        setAssessError(null);
        try {
            const result = await deviationService.getAiAssessment(deviation.id);
            setAssessment(result);
        } catch (err: any) {
            setAssessError(err?.message ?? "KI-analyse feilet. Prøv igjen.");
        } finally {
            setAssessing(false);
        }
    };

    if (!deviation) return null;

    const imgDownloadUrl = (img: DeviationImage) =>
        `${API_BASE_URL}${img.download_url}`;

    return (
        <AnimatePresence>
            {deviation && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-overlay backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-2xl bg-surface rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col max-h-[90vh]"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-border bg-background/50">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-lg ${
                                    deviation.severity === "critical" ? "bg-red-500/20 text-red-500" :
                                    deviation.severity === "high" ? "bg-orange-500/20 text-orange-500" :
                                    "bg-blue-500/20 text-blue-500"
                                }`}>
                                    <AlertTriangle size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">{deviation.title}</h2>
                                    <p className="text-sm text-muted">ID: {deviation.id} · {deviation.property_name}</p>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 rounded-full hover:bg-muted/10 text-muted hover:text-foreground transition-colors">
                                <X size={24} />
                            </button>
                        </div>

                        {/* Scrolling Content */}
                        <div className="p-6 overflow-y-auto space-y-6 custom-scrollbar">

                            {/* Beskrivelse */}
                            <div className="space-y-2">
                                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                                    <FileText size={14} className="text-blue-500" /> Beskrivelse
                                </h3>
                                <p className="text-foreground leading-relaxed bg-background/50 p-4 rounded-lg border border-border">
                                    {deviation.description || "Ingen beskrivelse registrert."}
                                </p>
                            </div>

                            {/* Detaljer */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-background/50 p-4 rounded-lg border border-border space-y-2">
                                    <p className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1"><Activity size={12} /> Detaljer</p>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Prioritet</span>
                                        <span className="font-medium capitalize">{deviation.severity}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Opprettet</span>
                                        <span className="font-medium">{deviation.created_at ? new Date(deviation.created_at).toLocaleDateString("nb-NO") : "—"}</span>
                                    </div>
                                </div>
                                <div className="bg-background/50 p-4 rounded-lg border border-border space-y-2">
                                    <p className="text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1"><List size={12} /> Status</p>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted">Status</span>
                                        <span className={`font-medium ${deviation.status === "open" ? "text-emerald-500" : "text-muted"}`}>
                                            {deviation.status === "open" ? "Åpen" : deviation.status}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* ─── Skadebilder ─── */}
                            <div className="space-y-3">
                                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                                    <ImageIcon size={14} className="text-purple-500" />
                                    Skadebilder {images.length > 0 && <span className="text-muted normal-case font-normal">({images.length})</span>}
                                </h3>

                                {images.length === 0 ? (
                                    <p className="text-sm text-muted italic">Ingen bilder lastet opp for dette avviket.</p>
                                ) : (
                                    <div className="grid grid-cols-3 gap-2">
                                        {images.map((img) => (
                                            <button
                                                key={img.file_id}
                                                onClick={() => setLightbox(imgDownloadUrl(img))}
                                                className="relative aspect-square rounded-lg overflow-hidden border border-border hover:border-primary transition group"
                                            >
                                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                                <img
                                                    src={imgDownloadUrl(img)}
                                                    alt={img.original_filename ?? "Skadebilde"}
                                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                                />
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* KI-analyse-knapp */}
                                {images.length > 0 && !assessment && (
                                    <button
                                        onClick={handleAiAssess}
                                        disabled={assessing}
                                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white rounded-lg font-medium text-sm transition"
                                    >
                                        {assessing ? (
                                            <><Loader2 size={16} className="animate-spin" /> Analyserer skader med KI…</>
                                        ) : (
                                            <><Brain size={16} /> Analyser skader med KI</>
                                        )}
                                    </button>
                                )}
                                {assessError && (
                                    <p className="text-sm text-red-600 flex items-center gap-1">
                                        <TriangleAlert size={14} /> {assessError}
                                    </p>
                                )}
                            </div>

                            {/* ─── KI-vurdering ─── */}
                            {assessment && (
                                <div className="rounded-xl border border-purple-200 bg-purple-50 p-4 space-y-3">
                                    <div className="flex items-center gap-2">
                                        <Brain size={16} className="text-purple-600" />
                                        <span className="text-sm font-bold text-purple-800">KI-vurdering av skaden</span>
                                        <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${SEVERITY_COLORS[assessment.alvorlighetsgrad] ?? "bg-gray-100 text-gray-700 border-gray-300"}`}>
                                            {assessment.alvorlighetsgrad}
                                        </span>
                                    </div>

                                    <p className="text-sm text-purple-900 leading-relaxed">{assessment.sammendrag}</p>

                                    {assessment.anbefalte_tiltak.length > 0 && (
                                        <div>
                                            <p className="text-xs font-semibold text-purple-700 mb-1">Anbefalte tiltak:</p>
                                            <ul className="space-y-1">
                                                {assessment.anbefalte_tiltak.map((t, i) => (
                                                    <li key={i} className="text-sm text-purple-800 flex items-start gap-1.5">
                                                        <ChevronRight size={14} className="mt-0.5 flex-shrink-0 text-purple-500" />
                                                        {t}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}

                                    {assessment.estimert_kostnad_nok != null && (
                                        <p className="text-xs text-purple-600">
                                            Estimert kostnad: <span className="font-semibold">{assessment.estimert_kostnad_nok.toLocaleString("nb-NO")} kr</span>
                                        </p>
                                    )}

                                    <button
                                        onClick={handleAiAssess}
                                        disabled={assessing}
                                        className="text-xs text-purple-500 hover:text-purple-700 underline"
                                    >
                                        {assessing ? "Analyserer…" : "Analyser på nytt"}
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-6 border-t border-border bg-background/50 flex justify-end gap-3">
                            <button onClick={onClose} className="px-4 py-2 rounded-lg text-muted hover:text-foreground hover:bg-muted/10 transition-colors">
                                Lukk
                            </button>
                            <button className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg shadow-lg shadow-primary/20 transition-colors">
                                Oppdater Status
                            </button>
                        </div>
                    </motion.div>

                    {/* Lightbox */}
                    {lightbox && (
                        <div
                            className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4"
                            onClick={() => setLightbox(null)}
                        >
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={lightbox} alt="Skadebilde" className="max-h-full max-w-full rounded-lg shadow-2xl" />
                            <button className="absolute top-4 right-4 text-white/80 hover:text-white" onClick={() => setLightbox(null)}>
                                <X size={28} />
                            </button>
                        </div>
                    )}
                </div>
            )}
        </AnimatePresence>
    );
}
