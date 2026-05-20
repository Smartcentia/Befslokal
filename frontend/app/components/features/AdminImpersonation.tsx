"use client";

import { useState } from "react";
import { UserCog, X, Play, LogOut } from "lucide-react";

export default function AdminImpersonation({ currentUserRole }: { currentUserRole?: string }) {
    const [impersonatingEmail, setImpersonatingEmail] = useState<string | null>(() => {
        if (typeof window === "undefined") return null;
        return localStorage.getItem("impersonate_email");
    });
    const [targetEmail, setTargetEmail] = useState("");
    const [isOpen, setIsOpen] = useState(false);

    // Only Admins should see this tool
    if (currentUserRole !== "admin") return null;

    const startImpersonation = () => {
        if (!targetEmail) return;
        localStorage.setItem("impersonate_email", targetEmail);
        setImpersonatingEmail(targetEmail);
        setIsOpen(false);
        window.location.href = "/"; // Hard reload to reset state/menus
    };

    const stopImpersonation = () => {
        localStorage.removeItem("impersonate_email");
        setImpersonatingEmail(null);
        window.location.href = "/"; // Hard reload
    };

    // If actively impersonating, show a prominent warning bar
    if (impersonatingEmail) {
        return (
            <div className="bg-amber-500/10 border-l-4 border-amber-500 px-4 py-2 flex items-center justify-between gap-4 rounded-r animate-in slide-in-from-top-2">
                <div className="flex items-center gap-2">
                    <UserCog className="text-amber-500" size={20} />
                    <div>
                        <p className="text-xs text-amber-500 font-bold uppercase tracking-wider">Simuleringsmodus</p>
                        <p className="text-sm text-foreground">Du ser nå systemet som: <span className="font-mono font-bold">{impersonatingEmail}</span></p>
                    </div>
                </div>
                <button
                    onClick={stopImpersonation}
                    className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded flex items-center gap-2 transition-colors"
                >
                    <LogOut size={14} />
                    Avslutt
                </button>
            </div>
        );
    }

    // Default: Small entry button in header
    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="p-2 text-muted hover:text-foreground transition-colors rounded-full hover:bg-surface ml-2 relative group"
                title="Start brukersimulering (Admin)"
            >
                <UserCog size={20} />
                <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-popover text-popover-foreground text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    Simuler bruker
                </span>
            </button>
        );
    }

    // Expanded input mode
    return (
        <div className="flex items-center bg-surface border border-border rounded-full px-1 py-1 animate-in fade-in zoom-in-95 duration-200">
            <input
                type="email"
                placeholder="E-post å simulere..."
                value={targetEmail}
                onChange={(e) => setTargetEmail(e.target.value)}
                className="bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted px-3 w-48"
                autoFocus
                onKeyDown={(e) => e.key === "Enter" && startImpersonation()}
            />
            <div className="flex items-center gap-1 border-l border-border pl-1">
                <button
                    onClick={startImpersonation}
                    disabled={!targetEmail}
                    className="p-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-full transition-colors disabled:opacity-50"
                    title="Start"
                >
                    <Play size={16} fill="currentColor" />
                </button>
                <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 hover:bg-muted text-muted hover:text-foreground rounded-full transition-colors"
                    title="Avbryt"
                >
                    <X size={16} />
                </button>
            </div>
        </div>
    );
}
