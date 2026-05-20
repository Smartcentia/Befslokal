"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

interface AccordionProps {
    title: string;
    icon?: React.ReactNode;
    children: React.ReactNode;
    defaultOpen?: boolean;
    /** Kjøres når panelet åpnes eller lukkes (f.eks. lazy lasting av innhold). */
    onOpenChange?: (open: boolean) => void;
}

export default function Accordion({
    title,
    icon,
    children,
    defaultOpen = false,
    onOpenChange,
}: AccordionProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    const toggle = () => {
        const next = !isOpen;
        setIsOpen(next);
        onOpenChange?.(next);
    };

    return (
        <div className="glass-card overflow-hidden mb-4 border border-border bg-muted/10">
            <button
                type="button"
                onClick={toggle}
                className="w-full flex items-center justify-between p-4 px-6 text-left hover:bg-muted/5 transition-colors group"
            >
                <div className="flex items-center gap-4">
                    {icon && <div className="text-primary group-hover:text-primary/80 transition-colors">{icon}</div>}
                    <span className="text-lg font-medium text-foreground transition-colors">{title}</span>
                </div>
                <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="text-muted group-hover:text-foreground"
                >
                    <ChevronDown size={20} />
                </motion.div>
            </button>

            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                        <div className="p-6 pt-0 border-t border-border">
                            <div className="pt-4">
                                {children}
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
