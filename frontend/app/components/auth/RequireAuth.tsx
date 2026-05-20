"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

/** Tillat kun interne stier (unngå åpen redirect). */
export function safeRedirectPath(raw: string | null): string {
    if (!raw || typeof raw !== "string") return "/dashboard";
    const t = raw.trim();
    if (!t.startsWith("/") || t.startsWith("//")) return "/dashboard";
    return t;
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (loading) return;
        if (!user) {
            const next = safeRedirectPath(pathname || "/dashboard");
            router.replace(`/login?redirect=${encodeURIComponent(next)}`);
        }
    }, [loading, user, router, pathname]);

    if (loading) {
        return (
            <div className="flex min-h-[40vh] items-center justify-center" role="status" aria-live="polite">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden />
                <span className="sr-only">Laster sesjon</span>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="flex min-h-[40vh] items-center justify-center" role="status">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden />
                <span className="sr-only">Sender til innlogging</span>
            </div>
        );
    }

    return <>{children}</>;
}
