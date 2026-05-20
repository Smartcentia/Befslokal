"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getGLCosts, type GLCosts, type GLCostsSubcategory } from "@/lib/api/propertiesApi";

const fmt = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

interface Props {
    propertyId: string;
}

function SubcategoryAccordion({
    subcat,
    defaultOpen = false,
}: {
    subcat: GLCostsSubcategory;
    defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);

    return (
        <div className="border border-border/50 rounded-lg overflow-hidden">
            <button
                type="button"
                onClick={() => setOpen(!open)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-muted/20 transition-colors"
            >
                <span className="flex items-center gap-1.5 font-medium text-foreground">
                    <span className="text-muted-foreground text-xs w-3">{open ? "▼" : "►"}</span>
                    {subcat.name}
                </span>
                <span className="font-mono tabular-nums text-xs font-semibold shrink-0 ml-2">
                    {fmt(subcat.total)}
                </span>
            </button>

            <AnimatePresence initial={false}>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18 }}
                        className="overflow-hidden"
                    >
                        <div className="px-3 pb-3 space-y-2 border-t border-border/30 pt-2">
                            {subcat.accounts.map((acc, i) => (
                                <div key={i} className="space-y-0.5">
                                    {/* Kontonivå */}
                                    <div className="flex justify-between items-center text-xs">
                                        <span
                                            className="text-muted-foreground font-medium truncate max-w-[65%]"
                                            title={acc.name}
                                        >
                                            {acc.code ? `${acc.code} ` : ""}
                                            {acc.name}
                                        </span>
                                        <span className="font-mono tabular-nums shrink-0 ml-2">
                                            {fmt(acc.total)}
                                        </span>
                                    </div>
                                    {/* Leverandørnivå */}
                                    {acc.vendors.map((v, j) => (
                                        <div
                                            key={j}
                                            className="flex justify-between items-center text-xs pl-4"
                                        >
                                            <span
                                                className="text-muted truncate max-w-[65%]"
                                                title={v.name}
                                            >
                                                {v.name}
                                            </span>
                                            <span className="font-mono tabular-nums text-muted shrink-0 ml-2">
                                                {fmt(v.total)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default function DetaljerteKostnaderCard({ propertyId }: Props) {
    const [data, setData] = useState<GLCosts | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedYear, setSelectedYear] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        getGLCosts(propertyId)
            .then((d) => {
                setData(d);
                if (d && d.available_years.length > 0) {
                    // Default til siste tilgjengelige år
                    setSelectedYear(String(Math.max(...d.available_years)));
                }
            })
            .finally(() => setLoading(false));
    }, [propertyId]);

    const yearData = selectedYear && data ? data.by_year[selectedYear] : null;
    const hasData = data && data.available_years.length > 0;
    const sortedYears = data
        ? [...data.available_years].sort((a, b) => b - a)
        : [];

    return (
        <motion.div
            className="glass-card p-5"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-1">
                <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
                    <svg
                        className="w-4 h-4 text-primary shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                        />
                    </svg>
                    Løpende kostnader
                    {selectedYear && (
                        <span className="text-muted-foreground font-normal">{selectedYear}</span>
                    )}
                </h3>
                {yearData && (
                    <span className="font-mono text-sm font-bold shrink-0 ml-2">
                        {fmt(yearData.total)}
                    </span>
                )}
            </div>
            <p className="text-[10px] text-muted mb-3">Kilde: Regnskapssystem (GL)</p>

            {/* Loading */}
            {loading && <div className="h-16 bg-muted/30 rounded animate-pulse" />}

            {/* Ingen data */}
            {!loading && !hasData && (
                <p className="text-muted text-xs italic">Ingen GL-data tilgjengelig.</p>
            )}

            {/* Data */}
            {!loading && hasData && (
                <>
                    {/* Årsvelger (vises kun hvis > 1 år) */}
                    {sortedYears.length > 1 && (
                        <div className="flex gap-1.5 mb-3 flex-wrap">
                            {sortedYears.map((yr) => (
                                <button
                                    key={yr}
                                    type="button"
                                    onClick={() => setSelectedYear(String(yr))}
                                    className={`px-2.5 py-0.5 rounded text-xs font-semibold transition-colors ${
                                        selectedYear === String(yr)
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted/40 text-muted-foreground hover:bg-muted/70"
                                    }`}
                                >
                                    {yr}
                                </button>
                            ))}
                        </div>
                    )}

                    {/* Accordion per underkategori */}
                    {yearData ? (
                        yearData.subcategories.length > 0 ? (
                            <div className="space-y-1.5">
                                {yearData.subcategories.map((subcat, i) => (
                                    <SubcategoryAccordion
                                        key={`${selectedYear}-${subcat.name}`}
                                        subcat={subcat}
                                        defaultOpen={i === 0}
                                    />
                                ))}
                            </div>
                        ) : (
                            <p className="text-muted text-xs italic">
                                Ingen kostnader for {selectedYear}.
                            </p>
                        )
                    ) : null}
                </>
            )}
        </motion.div>
    );
}
