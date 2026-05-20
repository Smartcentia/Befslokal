"use client";

import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { X } from "lucide-react";
import { useEffect } from "react";

interface FullScreenMenuProps {
    isOpen: boolean;
    onClose: () => void;
    role?: string;
}

const menuItems = [
    { title: "Hjem", href: "/", roles: ["all"] },
    { title: "Eiendommer", href: "/properties", roles: ["all"] },
    { title: "Kontrakter", href: "/contracts", roles: ["admin", "property_manager", "regional_manager"] },
    { title: "Økonomi", href: "/financials", roles: ["admin", "property_manager", "regional_manager"] },
    { title: "Avviksanalyse 🆕", href: "/dashboard/financial/variance?propertyId=SELECT", roles: ["admin", "property_manager", "regional_manager"] },
    { title: "Rullerende Prognoser 📈", href: "/dashboard/financial/forecast?propertyId=SELECT", roles: ["admin", "property_manager", "regional_manager"] },
    { title: "Avvik & Risiko", href: "/deviations", roles: ["all"] },
    { title: "Risikobildet ⚠️", href: "/risk", roles: ["all"] },
    { title: "Sjekklister", href: "/checklists", roles: ["all"] },

    { title: "Admin & Verktøy", href: "/admin", roles: ["admin"] },
    { title: "Finansiell Innsikt (Admin)", href: "/admin/financial-analysis", roles: ["admin"] },
    { title: "Innstillinger", href: "/settings", roles: ["all"] }, // Or restricted?
    { title: "BUP Lokasjoner", href: "/bup-locations", roles: ["all"] },
    { title: "Lovdata ⚖️", href: "/lovdata-search", roles: ["all"] },
    { title: "AI Research Lab 🧪", href: "/lab", roles: ["all"] },
    { title: "Brukerhjelp", href: "/help", roles: ["all"] },
];

export default function FullScreenMenu({ isOpen, onClose, role = "property_manager" }: FullScreenMenuProps) {
    // Prevent scrolling when menu is open
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "unset";
        }
        return () => { document.body.style.overflow = "unset"; };
    }, [isOpen]);

    // Filter items
    const filteredItems = menuItems.filter(item => {
        if (item.roles.includes("all")) return true;
        
        // Robust role check (case insensitive and supports "ADMIN")
        const normalizedRole = role.toLowerCase();
        return item.roles.some(r => {
            const normalizedR = r.toLowerCase();
            if (normalizedR === "admin" && normalizedRole === "admin") return true;
            return normalizedR === normalizedRole;
        });
    });

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="fixed inset-0 z-50 bg-background/95 backdrop-blur-md flex items-center justify-center"
                >
                    <button
                        onClick={onClose}
                        className="absolute top-6 right-6 p-2 text-muted hover:text-foreground transition-colors"
                        aria-label="Lukk meny"
                        title="Lukk meny"
                    >
                        <X size={32} />
                    </button>

                    <nav className="flex flex-col items-center gap-6 max-h-[80vh] overflow-y-auto w-full">
                        {filteredItems.map((item, index) => (
                            <motion.div
                                key={item.href}
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.05 * index, duration: 0.3 }}
                            >
                                <Link
                                    href={item.href}
                                    onClick={onClose}
                                    className="text-2xl font-bold text-foreground hover:text-primary transition-colors tracking-tight"
                                >
                                    {item.title}
                                </Link>
                            </motion.div>
                        ))}
                    </nav>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
