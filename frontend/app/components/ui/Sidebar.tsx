"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import {
    LayoutDashboard,
    Building2,
    FileText,
    Users,
    AlertTriangle,
    TrendingUp,
    ShieldCheck,
    Shield,
    Settings,
    LogOut,
    Trello,
    Bell,
    BrainCircuit,
    ClipboardCheck,
    Activity,
    HelpCircle,
    Zap,
    Calendar,
    MapPin,
    Search,
    BarChart3,
    Newspaper,
    Skull,
    Baby,
    Database,
    Building,
    Receipt,
    Wrench,
    Archive,
    LucideIcon
} from "lucide-react";

interface ExtendedUser {
    email?: string | null;
    roles?: string[];
    role?: string;
    isAdmin?: boolean;
}

interface MenuItem {
    icon: LucideIcon;
    label: string;
    href: string;
    adminOnly?: boolean;
}

interface MenuGroup {
    section: string;
    items: MenuItem[];
}

export default function Sidebar() {
    const pathname = usePathname();
    const { user: authUser, signOut } = useAuth();

    const [simulatedRole] = useState<string | null>(() => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('simulate_role');
    });

    const user = authUser as ExtendedUser | undefined;

    // Base admin status
    const isRealAdmin = user?.email === "admin@befs.no" ||
        user?.email === "frankvevle@gmail.com" ||
        user?.roles?.includes("ADMIN") ||
        user?.role === "ADMIN" ||
        user?.isAdmin === true;

    // If simulating a non-admin role, treat as not admin
    const isAdmin = simulatedRole
        ? (["admin", "ADMIN"].includes(simulatedRole))
        : isRealAdmin;

    const isActive = (path: string) => pathname === path || pathname.startsWith(`${path}/`);

    const menuItems: MenuGroup[] = [
        {
            section: "HOVEDMENY", items: [
                { icon: LayoutDashboard, label: "Oversikt", href: "/dashboard" },
                { icon: ShieldCheck, label: "Admin", href: "/admin", adminOnly: true },
                { icon: Bell, label: "Innboks", href: "/inbox" },
                { icon: Building2, label: "Eiendommer", href: "/properties" },
                { icon: FileText, label: "Kontrakter", href: "/contracts" },
                { icon: Users, label: "Leietakere", href: "/tenants" },
                { icon: Archive, label: "Arkiv", href: "/arkiv" },
            ]
        },
        {
            section: "DRIFT & VEDLIKEHOLD", items: [
                { icon: ClipboardCheck, label: "Sjekklister", href: "/checklists" },
                { icon: AlertTriangle, label: "Avvikshåndtering", href: "/deviations" },
                { icon: Wrench, label: "FDVU Oversikt", href: "/fdvu" },
                { icon: ClipboardCheck, label: "FDVU Vurdering", href: "/fdvu/vurdering" },
                { icon: FileText, label: "FDVU Rapport", href: "/fdvu/rapport" },
                { icon: Zap, label: "Aktivitetshub", href: "/activities/hub" },
                { icon: Calendar, label: "Kalender", href: "/calendar" },
                { icon: TrendingUp, label: "Økonomi", href: "/financials" },
                { icon: ShieldCheck, label: "SRS-rapport", href: "/financials/srs" },
                { icon: Building2, label: "Anleggsregister", href: "/financials/anlegg" },
                // { icon: TrendingUp, label: "Prediksjon 2027", href: "/financials/prediksjon" }, // Gjemt — erstattet av økonomidata
                { icon: Receipt, label: "Eiendomskostnader 2025", href: "/okonomi" },
                { icon: BarChart3, label: "Analyse & Innsikt", href: "/analysis" },
                { icon: Activity, label: "Risikoanalyse", href: "/risk" },
                { icon: MapPin, label: "BUP-lokasjoner", href: "/bup-locations" },
                { icon: Search, label: "Lovdata-søk", href: "/lovdata-search" },
                { icon: Newspaper, label: "Media Overvåkning", href: "/media-monitor", adminOnly: true },
            ]
        },
        {
            section: "DATA & STATISTIKK", items: [
                { icon: Database, label: "SSB Statistikk", href: "/ssb" },
                { icon: Baby, label: "Barnevern", href: "/barnevern" },
                { icon: Building, label: "Institusjoner", href: "/institusjoner" },
            ]
        },
    ];

    return (
        <aside className="fixed left-0 top-0 bottom-0 w-64 bg-sidebar border-r border-sidebar flex flex-col z-50 transition-colors duration-300">
            {/* Logo Area - Uses primary color which is consistent or sidebar text */}
            <div className="h-20 flex items-center px-6 border-b border-sidebar">
                <Link href="/dashboard" className="flex items-center gap-3 font-bold text-xl tracking-tight text-sidebar hover:text-(--sidebar-text-hover) transition-colors">
                    <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                        <Building2 size={20} />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-sidebar-text-hover dark:text-(--sidebar-text-hover) font-bold text-xl leading-none">BEFS</span>
                        <span className="text-sidebar-text-hover dark:text-(--sidebar-text-hover) text-[9px] font-normal opacity-70 leading-tight max-w-37.5">Bufetat eiendomsforvaltningssystem</span>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <div className="flex-1 overflow-y-auto py-4 px-4">
                {/* Administration section - Move to front if Admin */}
                {isAdmin && (
                    <div className="mb-4">
                        <h3 className="px-3 text-[10px] font-bold text-sidebar uppercase tracking-widest mb-2 opacity-70">
                            ADMINISTRASJON
                        </h3>
                        <div className="space-y-1">
                            <Link
                                href="/admin"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin") && !isActive("/admin/users")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <ShieldCheck size={18} className={`transition-colors ${(isActive("/admin") && !isActive("/admin/users")) ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Admin Dashboard
                            </Link>
                            <Link
                                href="/admin/users"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/users")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <Users size={18} className={`transition-colors ${isActive("/admin/users") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Brukerstyring
                            </Link>
                            <Link
                                href="/admin/ai-lab"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/ai-lab")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <BrainCircuit size={18} className={`transition-colors ${isActive("/admin/ai-lab") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                KI-Lab & Transparens
                            </Link>
                            <Link
                                href="/admin/governance"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/governance")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <Shield size={18} className={`transition-colors ${isActive("/admin/governance") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Data Governance
                            </Link>
                            <Link
                                href="/admin/presentasjon"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/presentasjon")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <BarChart3 size={18} className={`transition-colors ${isActive("/admin/presentasjon") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Økonomi-presentasjon
                            </Link>
                            <Link
                                href="/admin/okonomi-konto"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/okonomi-konto")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <BarChart3 size={18} className={`transition-colors ${isActive("/admin/okonomi-konto") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Konto per eiendom
                            </Link>
                            <Link
                                href="/admin/tjenester"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/admin/tjenester")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <ClipboardCheck size={18} className={`transition-colors ${isActive("/admin/tjenester") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Tjenesteoversikt
                            </Link>
                            <Link
                                href="/konkurs-monitor"
                                className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/konkurs-monitor")
                                    ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                    : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                    }`}
                            >
                                <Skull size={18} className={`transition-colors ${isActive("/konkurs-monitor") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                Konkursovervåkning
                            </Link>
                        </div>
                    </div>
                )}

                {menuItems.map((group, idx) => (
                    <div key={idx} className="mb-4">
                        <h3 className="px-3 text-[10px] font-bold text-sidebar uppercase tracking-widest mb-2 opacity-70">
                            {group.section}
                        </h3>
                        <div className="space-y-1">
                            {group.items.map((item) => {
                                // Skip admin-only items if user is not admin
                                if (item.adminOnly && !isAdmin) return null;

                                const active = isActive(item.href);
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${active
                                            ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                            : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                            }`}
                                    >
                                        <item.icon size={18} className={`transition-colors ${active ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                                        {item.label}
                                    </Link>
                                );
                            })}
                        </div>
                    </div>
                ))}

                {/* Settings Group */}
                <div>
                    <h3 className="px-3 text-[10px] font-bold text-sidebar uppercase tracking-widest mb-2 opacity-70">
                        APP
                    </h3>
                    <div className="space-y-1">
                        <Link
                            href="/settings"
                            className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/settings")
                                ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                }`}
                        >
                            <Settings size={18} className={`transition-colors ${isActive("/settings") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                            Innstillinger
                        </Link>
                        <Link
                            href="/help"
                            className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/help")
                                ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                }`}
                        >
                            <HelpCircle size={18} className={`transition-colors ${isActive("/help") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                            Hjelp & Dokumentasjon
                        </Link>
                        <Link
                            href="/jira"
                            className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 group ${isActive("/jira")
                                ? "bg-(--sidebar-active-bg) text-(--sidebar-active-text) shadow-lg"
                                : "text-sidebar hover:bg-(--sidebar-active-bg)/10 hover:text-(--sidebar-text-hover)"
                                }`}
                        >
                            <Trello size={18} className={`transition-colors ${isActive("/jira") ? "text-(--sidebar-active-text)" : "text-current group-hover:text-(--sidebar-text-hover)"}`} />
                            Jira
                        </Link>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-sidebar bg-sidebar">
                <button
                    onClick={async () => { await signOut(); window.location.href = "/welcome"; }}
                    className="flex items-center gap-2 text-xs font-medium text-sidebar hover:text-red-500 transition-colors w-full px-2 py-1"
                >
                    <LogOut size={16} />
                    Logg ut
                </button>
            </div>
        </aside>
    );
}
