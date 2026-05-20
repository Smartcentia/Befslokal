"use client";

import { usePathname } from "next/navigation";
import Header from "@/app/components/ui/Header";
import Sidebar from "@/app/components/ui/Sidebar";
import ChatWidget from "@/app/components/features/ChatWidget";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";

/** Ruter uten app-skall (sidebar, header, KI-widget) – kun hero/innlogging. */
const PUBLIC_PATH_PREFIXES = ["/welcome", "/login"];

function isPublicRoute(pathname: string | null): boolean {
    if (!pathname) return false;
    return PUBLIC_PATH_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function AppChrome({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isPublic = isPublicRoute(pathname);

    if (isPublic) {
        return (
            <div id="main-content" className="min-h-screen">
                {children}
            </div>
        );
    }

    return (
        <>
            <div className="flex min-h-screen">
                <div className="hidden lg:block">
                    <Sidebar />
                </div>
                <div className="flex-1 flex flex-col ml-0 lg:ml-72 transition-all duration-300">
                    <Header />
                    <ErrorBoundary componentName="Root Content">
                        <main id="main-content" className="flex-1 overflow-y-auto p-8 pt-32 pb-28">
                            {children}
                        </main>
                    </ErrorBoundary>
                </div>
            </div>
            <ChatWidget />
        </>
    );
}
