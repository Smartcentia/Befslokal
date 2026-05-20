"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { deviationService, Deviation } from "@/lib/domains/fdv/deviationService";
import DeviationList from "@/app/components/features/DeviationList";
import DeviationStats from "@/app/components/features/DeviationStats";
import DeviationCreateModal from "@/app/components/features/DeviationCreateModal";
import DeviationDetailsModal from "@/app/components/features/DeviationDetailsModal";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";

function DeviationsContent() {
    const searchParams = useSearchParams();
    const priorityParam = searchParams.get("priority");
    const [deviations, setDeviations] = useState<Deviation[]>([]);
    const [stats, setStats] = useState<any | null>(null);
    const [selectedDeviation, setSelectedDeviation] = useState<Deviation | null>(null);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // We can use this for filtering if needed, currently stats don't support callback filtering in backend fully/frontend logic
    const [activeFilter, setActiveFilter] = useState<string | null>(null);

    async function loadData() {
        setLoading(true);
        try {
            const [devData, statsData] = await Promise.all([
                deviationService.getAll(1, 50, priorityParam ?? undefined),
                deviationService.getStats()
            ]);
            setDeviations(devData);
            setStats(statsData);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    async function refreshData() {
        const [devData, statsData] = await Promise.all([
            deviationService.getAll(1, 50, priorityParam ?? undefined),
            deviationService.getStats()
        ]);
        setDeviations(devData);
        setStats(statsData);
    }

    useEffect(() => {
        loadData();
    }, [priorityParam]);

    return (
        <div className="min-h-screen font-sans text-foreground pb-20">
            <DeviationDetailsModal
                deviation={selectedDeviation}
                onClose={() => setSelectedDeviation(null)}
            />

            <DeviationCreateModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreated={refreshData}
            />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* ... Header section ... */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-linear-to-r from-red-600 to-orange-500">
                            Avvik & HMS
                        </h1>
                        <p className="text-muted mt-2">
                            Oversikt over registrerte avvik og saker (Internal Control).
                        </p>
                    </div>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="flex items-center gap-2 rounded-lg border border-primary/40 bg-primary px-5 py-2.5 text-primary-foreground shadow-lg shadow-primary/20 transition-all hover:scale-105 hover:bg-primary/90"
                    >
                        <Plus size={18} />
                        <span>Meld Avvik</span>
                    </button>
                </div>

                {loading ? (
                    <div className="flex flex-col gap-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-24 animate-pulse rounded-xl border border-border bg-card shadow-sm" />
                        ))}
                    </div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        {stats && (
                            <DeviationStats stats={stats} />
                        )}

                        <h2 className="text-xl font-semibold text-foreground mb-4 mt-8">Alle registreringer</h2>
                        <DeviationList
                            deviations={deviations}
                            onSelect={setSelectedDeviation}
                        />
                    </motion.div>
                )}
            </main>
        </div>
    );
}

export default function DeviationsPage() {
    return (
        <Suspense fallback={<div className="min-h-screen p-8 pt-24 text-muted">Laster...</div>}>
            <DeviationsContent />
        </Suspense>
    );
}
