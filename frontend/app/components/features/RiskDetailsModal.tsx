import { Deviation } from "@/lib/api";
import Link from 'next/link';
import { X, AlertTriangle, List, CheckCircle, FileText, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface RiskDetailsModalProps {
    deviation: Deviation | null;
    onClose: () => void;
}

export default function RiskDetailsModal({ deviation, onClose }: RiskDetailsModalProps) {
    if (!deviation) return null;

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

                    {/* Modal Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="relative w-full max-w-2xl bg-surface rounded-2xl shadow-2xl border border-border overflow-hidden flex flex-col max-h-[90vh]"
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between p-6 border-b border-border bg-background/50">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-lg ${deviation.severity === 'Critical' ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'}`}>
                                    <AlertTriangle size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-foreground">{deviation.title}</h2>
                                    <p className="text-sm text-muted">ID: {deviation.id}</p>
                                </div>
                            </div>
                            <button 
                                onClick={onClose} 
                                className="p-2 rounded-full hover:bg-muted/10 text-muted hover:text-foreground transition-colors"
                                aria-label="Lukk"
                                title="Lukk"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        {/* Scrolling Content */}
                        <div className="p-6 overflow-y-auto space-y-8 custom-scrollbar">

                            {/* Description Section */}
                            <div className="space-y-3">
                                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                                    <FileText size={16} className="text-blue-500" /> Beskrivelse
                                </h3>
                                <p className="text-foreground leading-relaxed bg-background/50 p-4 rounded-lg border border-border">
                                    {deviation.description || "Ingen beskrivelse tilgjengelig."}
                                </p>
                            </div>

                            {/* Risk Assessment Data */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                                        <Activity size={16} className="text-emerald-500" /> Risikoanalyse
                                    </h3>
                                    <div className="bg-background/50 p-4 rounded-lg border border-border space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-muted">Alvorlighetsgrad:</span>
                                            <span className="text-foreground font-medium">{deviation.severity}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted">Sannsynlighet:</span>
                                            <span className="text-foreground font-medium">Middels</span> {/* Placeholder if missing in Model */}
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted">Konsekvens:</span>
                                            <span className="text-foreground font-medium">Høy</span> {/* Placeholder */}
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <h3 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
                                        <List size={16} className="text-purple-500" /> Status
                                    </h3>
                                    <div className="bg-background/50 p-4 rounded-lg border border-border space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-muted">Nåværende Status:</span>
                                            <span className={`font-medium ${deviation.status === 'open' ? 'text-emerald-500' : 'text-muted'}`}>
                                                {deviation.status === 'open' ? "Åpen" : "Lukket"}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-muted">Ansvarlig:</span>
                                            <span className="text-foreground font-medium">Frank Vevle</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Mitigation / Measures Helper */}
                            <div className="bg-primary/10 border border-primary/20 p-5 rounded-lg">
                                <h3 className="text-primary font-semibold mb-2 flex items-center gap-2">
                                    <CheckCircle size={18} /> Anbefalte Tiltak
                                </h3>
                                <ul className="list-disc list-inside text-foreground space-y-1 text-sm">
                                    <li>Utfør ny verdivurdering av eiendommen.</li>
                                    <li>Kontakt leietaker for avklaring av utbedringsplikt.</li>
                                    <li>Oppdater HMS-dokumentasjon.</li>
                                </ul>
                            </div>

                        </div>

                        {/* Footer Actions */}
                        <div className="p-6 border-t border-border bg-background/50 flex justify-end gap-3">
                            <button onClick={onClose} className="px-4 py-2 rounded-lg text-muted hover:text-foreground hover:bg-muted/10 transition-colors">
                                Lukk
                            </button>
                            <Link href={`/deviations/${deviation.id}`} className="px-4 py-2 bg-muted/20 hover:bg-muted/30 text-foreground hover:text-primary rounded-lg transition-colors">
                                Vis detaljert side
                            </Link>
                            <button className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg shadow-lg shadow-primary/20 transition-colors">
                                Oppdater Status
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
