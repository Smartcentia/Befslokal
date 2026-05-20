"use client";

import { useState } from "react";
import { Menu, LogOut, Sparkles, LayoutDashboard, ChevronDown } from "lucide-react";
import FullScreenMenu from "./FullScreenMenu";
import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "@/hooks/useAuth";
import AdminImpersonation from "@/app/components/features/AdminImpersonation";

export default function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { user, name: authName, role: authRole, signOut } = useAuth();

    const isAuthenticated = !!user;
    const name = authName || "Bruker";

    // Check for simulated role
    const [simulatedRole, setSimulatedRole] = useState<string | null>(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('simulate_role');
        }
        return null;
    });

    const realRole = authRole || (user?.email === "admin@befs.no" || user?.email === "frankvevle@gmail.com" ? "admin" : "property_manager");
    const userRole = simulatedRole || realRole;

    const roleDisplay = userRole === "admin" || userRole === "ADMIN" ? "Administrator" :
        userRole === "property_manager" || userRole === "PROPERTY_MANAGER" ? "Eiendomsforvalter" :
            userRole === "janitor" || userRole === "JANITOR" ? "Vaktmester" :
                userRole === "tenant" || userRole === "TENANT" ? "Leietaker" : userRole;

    const handleRoleSwitch = (role: string | null) => {
        if (role) {
            localStorage.setItem('simulate_role', role);
            setSimulatedRole(role);
        } else {
            localStorage.removeItem('simulate_role');
            setSimulatedRole(null);
        }
        // Force reload to update all components with new permission state
        window.location.reload();
    };

    const isAdmin = realRole === 'admin' || realRole === 'ADMIN';
    const initials = name ? name.split(" ").map(n => n[0]).join("").toUpperCase().substring(0, 2) : "??";

    return (
        <>
            {/* lg:left-72: må matche Sidebar (w-72) + main (lg:ml-72) */}
            <header className="fixed top-0 left-0 right-0 lg:left-72 z-40 bg-background/80 backdrop-blur-xl border-b border-border px-3 md:px-6 py-2 md:py-3 flex flex-col gap-2 md:gap-3 transition-all duration-300">
                <div className="flex justify-between items-center">
                    <Link href="/" className="text-lg font-semibold text-foreground tracking-tight flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-primary-foreground font-bold shadow-lg shadow-primary/20">B</div>
                        BEFS <span className="opacity-50 font-normal">| Bufetat</span>
                    </Link>

                    <div className="flex items-center gap-4">
                        <div className="group/dash relative">
                            <button
                                className="p-2 text-primary hover:text-primary/90 rounded-lg hover:bg-primary/10 border border-primary/30 hover:border-primary/50 transition-all flex items-center gap-1"
                                title="Dashboard-varianter"
                                aria-label="Velg dashboard-variant"
                                aria-haspopup="true"
                                aria-expanded="false"
                            >
                                <LayoutDashboard size={20} />
                                <ChevronDown size={14} className="opacity-70" />
                            </button>
                            <div className="absolute right-0 top-full mt-2 w-52 bg-surface border border-border rounded-xl shadow-2xl opacity-0 invisible group-hover/dash:opacity-100 group-hover/dash:visible transition-all duration-200 z-50 p-2">
                                <Link href="/dashboard" className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted hover:text-foreground hover:bg-surface/50 rounded-lg transition-colors">
                                    Standard
                                </Link>
                                <Link href="/dashboard/cyberpunk" className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted hover:text-primary hover:bg-primary/10 rounded-lg transition-colors">
                                    <Sparkles size={18} className="text-primary" /> Cyberpunk
                                </Link>
                                <Link href="/dashboard/minimalist" className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted hover:text-foreground hover:bg-surface/50 rounded-lg transition-colors">
                                    Minimalist
                                </Link>
                                <Link href="/dashboard/terminal" className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors">
                                    Terminal
                                </Link>
                                <Link href="/dashboard/nordic" className="flex items-center gap-3 px-3 py-2.5 text-sm text-muted hover:text-sky-400 hover:bg-sky-500/10 rounded-lg transition-colors">
                                    Nordic
                                </Link>
                            </div>
                        </div>
                        <Link href="/help" className="text-sm font-medium text-muted hover:text-foreground transition-colors">Hjelp</Link>

                        <div className="h-8 w-px bg-border"></div>

                        <ThemeToggle />

                        {isAdmin && <AdminImpersonation currentUserRole={realRole.toLowerCase()} />}

                        <div className="flex items-center gap-3 pl-2">
                            {isAuthenticated ? (
                                <>
                                    {isAdmin && (
                                        <div className="group relative">
                                            <button
                                                className={`text-xs px-2 py-1 rounded border transition-colors ${simulatedRole ? 'bg-amber-100 border-amber-300 text-amber-800' : 'bg-transparent border-transparent text-muted hover:bg-surface/50'}`}
                                                title="Bytt rolle (Simulering)"
                                            >
                                                {simulatedRole ? 'Simulering' : 'Bytt rolle'}
                                            </button>
                                            <div className="absolute right-0 top-full mt-2 w-48 bg-surface border border-border rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-1">
                                                <div className="px-3 py-2 text-xs font-semibold text-muted uppercase tracking-wider border-b border-border mb-1">
                                                    Simuler rolle
                                                </div>
                                                <button
                                                    onClick={() => handleRoleSwitch(null)}
                                                    className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${!simulatedRole ? 'bg-primary/10 text-primary font-medium' : 'text-muted hover:text-foreground hover:bg-surface/50'}`}
                                                >
                                                    Ingen (Admin)
                                                </button>
                                                <button
                                                    onClick={() => handleRoleSwitch('PROPERTY_MANAGER')}
                                                    className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${simulatedRole === 'PROPERTY_MANAGER' ? 'bg-primary/10 text-primary font-medium' : 'text-muted hover:text-foreground hover:bg-surface/50'}`}
                                                >
                                                    Eiendomsforvalter
                                                </button>
                                                <button
                                                    onClick={() => handleRoleSwitch('JANITOR')}
                                                    className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${simulatedRole === 'JANITOR' ? 'bg-primary/10 text-primary font-medium' : 'text-muted hover:text-foreground hover:bg-surface/50'}`}
                                                >
                                                    Vaktmester
                                                </button>
                                                <button
                                                    onClick={() => handleRoleSwitch('TENANT')}
                                                    className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-colors ${simulatedRole === 'TENANT' ? 'bg-primary/10 text-primary font-medium' : 'text-muted hover:text-foreground hover:bg-surface/50'}`}
                                                >
                                                    Leietaker
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    <div className="text-right hidden sm:block">
                                        <p className="text-xs font-medium text-foreground">{name}</p>
                                        <p className="text-[10px] text-muted uppercase tracking-wide flex items-center justify-end gap-1">
                                            {roleDisplay}
                                            {simulatedRole && <span className="text-amber-500" title="Simulert rolle">•</span>}
                                        </p>
                                    </div>
                                    <div className="group relative">
                                        <div className="w-9 h-9 rounded-full bg-primary border border-border flex items-center justify-center text-xs font-bold text-primary-foreground shadow-lg cursor-pointer">
                                            {initials}
                                        </div>
                                        {/* Simple Dropdown for Logout */}
                                        <div className="absolute right-0 top-full mt-2 w-48 bg-surface border border-border rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-2">
                                            <button
                                                onClick={async () => { await signOut(); window.location.href = "/welcome"; }}
                                                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-muted hover:text-foreground hover:bg-surface/50 rounded-lg transition-colors"
                                            >
                                                <LogOut size={16} /> Logg ut
                                            </button>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <Link
                                    href="/login"
                                    className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors"
                                >
                                    Logg inn
                                </Link>
                            )}
                        </div>

                        <button
                            onClick={() => setIsMenuOpen(true)}
                            className="p-2 text-muted hover:text-foreground transition-colors rounded-full hover:bg-surface/50 ml-2"
                            aria-label="Open Menu"
                            title="Åpne meny"
                        >
                            <Menu size={24} />
                        </button>
                    </div>
                </div>

                {/* Search Bar - nederst i topbar */}
                <div className="hidden md:flex items-center bg-surface/50 rounded-full px-4 py-1.5 border border-border focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/50 transition-all w-full max-w-sm">
                    <input
                        type="text"
                        placeholder="Søk etter eiendom, kontrakt eller avvik..."
                        className="bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted w-full"
                    />
                    <kbd className="hidden lg:inline-flex h-5 items-center gap-1 rounded border border-border bg-surface/50 px-1.5 font-mono text-[10px] font-medium text-muted">
                        <span className="text-xs">⌘</span>K
                    </kbd>
                </div>
            </header>

            <FullScreenMenu
                isOpen={isMenuOpen}
                onClose={() => setIsMenuOpen(false)}
                role={userRole.toLowerCase()}
            />
        </>
    );
}
