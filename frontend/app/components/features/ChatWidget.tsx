"use client";

import { useState, useEffect } from "react";
import { MessageCircle, X, Maximize2, Minimize2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ChatInterface from "./ChatInterface";

/** Dispatches this event (e.g. from Hjelp-siden) to åpne KI Kollega. */
export const OPEN_KI_KOLLEGA_EVENT = "befs:open-ki-kollega";

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);

    useEffect(() => {
        const open = () => setIsOpen(true);
        window.addEventListener(OPEN_KI_KOLLEGA_EVENT, open);
        return () => window.removeEventListener(OPEN_KI_KOLLEGA_EVENT, open);
    }, []);

    return (
        <div
            className="fixed z-[1100] flex flex-col items-end gap-3 bottom-[max(1.25rem,env(safe-area-inset-bottom,0px))] right-[max(1.25rem,env(safe-area-inset-right,0px))]"
            aria-live="polite"
        >
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        className={`bg-surface border border-border shadow-2xl rounded-2xl overflow-hidden flex flex-col mb-2 origin-bottom-right transition-all duration-300 ease-in-out
                            ${isExpanded ? 'w-[90vw] h-[80vh] md:w-200' : 'w-[90vw] md:w-112.5 h-150'}
                        `}
                    >
                        <div className="bg-primary p-4 flex justify-between items-center text-primary-foreground">
                            <div>
                                <h3 className="font-bold">KI Kollega</h3>
                                <p className="text-xs text-primary-foreground/80">AI-drevet støtte</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setIsExpanded(!isExpanded)}
                                    className="p-1 hover:bg-primary-foreground/20 rounded-full transition-colors"
                                    title={isExpanded ? "Minimer" : "Utvid"}
                                >
                                    {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsOpen(false)}
                                    className="p-1 hover:bg-primary-foreground/20 rounded-full transition-colors"
                                    title="Lukk"
                                >
                                    <X size={20} />
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 overflow-hidden relative">
                            <ChatInterface />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                title={isOpen ? "Lukk chat" : "Åpne KI kollega chat"}
                className={`rounded-full shadow-lg transition-all duration-200 flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background p-3 md:p-3.5 ${isOpen
                    ? "bg-foreground text-background rotate-90"
                    : "bg-primary text-primary-foreground hover:shadow-md hover:brightness-105 ring-2 ring-primary/25 hover:ring-primary/40"
                    }`}
            >
                {isOpen ? <X size={28} /> : <MessageCircle size={28} />}
                {!isOpen && <span className="font-semibold text-base pr-1.5 hidden sm:inline">KI kollega</span>}
            </button>
        </div>
    );
}
