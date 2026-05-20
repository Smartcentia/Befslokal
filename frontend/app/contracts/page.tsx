"use client";

import { useState, useEffect, useMemo } from "react";
import { getContracts, Contract } from "@/lib/api";
import ContractList from "@/app/components/features/ContractList";
import { motion } from "framer-motion";

export default function ContractsPage() {
    const [contracts, setContracts] = useState<Contract[]>([]);
    const [activeFilter, setActiveFilter] = useState('Alle');
    const filteredContracts = useMemo<Contract[]>(() => {
        if (!contracts) return [];

        let result = [...contracts];
        if (activeFilter === 'Aktive') {
            result = contracts.filter(c => c.status === 'active');
        } else if (activeFilter === 'Avsluttet') {
            result = contracts.filter(c => c.status === 'terminated' || c.status === 'expired');
        } else if (activeFilter === 'Utløper snart') {
            const sixtyDaysFromNow = new Date();
            sixtyDaysFromNow.setDate(sixtyDaysFromNow.getDate() + 60);

            result = contracts.filter(c => {
                if (c.status !== 'active') return false;
                const endDateStr = c.periods?.[0]?.end_date;
                if (!endDateStr) return false;
                const endDate = new Date(endDateStr);
                return endDate <= sixtyDaysFromNow;
            });
        }
        return result;
    }, [contracts, activeFilter]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadContracts() {
            setLoading(true);
            const data = await getContracts({ limit: 1000 }); // Increase limit to ensure client-side filtering works
            setContracts(data);
            // filteredContracts is derived from contracts
            setLoading(false);
        }
        loadContracts();
    }, []);

    // Filtering now derived via useMemo above; effect removed to avoid state updates in effects

    return (
        <div className="min-h-screen font-sans text-foreground pb-20">
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-foreground tracking-tight">
                        Kontrakter
                    </h1>
                    <p className="text-gray-500 dark:text-slate-400 mt-2">
                        Oversikt over alle leiekontrakter og avtaler.
                    </p>
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {['Alle', 'Aktive', 'Avsluttet', 'Utløper snart'].map((filter) => (
                        <button
                            key={filter}
                            onClick={() => setActiveFilter(filter)}
                            className={`px-4 py-2 rounded-full text-sm font-bold whitespace-nowrap transition-all ${activeFilter === filter
                                ? "bg-primary text-primary-foreground shadow-md scale-105"
                                : "bg-surface text-foreground border border-border hover:border-primary"
                                }`}
                        >
                            {filter}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="flex flex-col gap-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-24 bg-[#1e293b] rounded-xl shadow-sm border border-slate-700/50 animate-pulse" />
                        ))}
                    </div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <ContractList contracts={filteredContracts} />
                    </motion.div>
                )}
            </main>
        </div>
    );
}
