"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { fetchAPI } from "@/lib/api/client";

interface FeatureFlags {
    hide_financials: boolean;
    show_financials: boolean;   // true = denne brukeren ser økonomidata
    is_admin: boolean;
    loading: boolean;
    refresh: () => void;        // for å oppdatere etter toggle
}

const defaults: FeatureFlags = {
    hide_financials: false,
    show_financials: true,
    is_admin: false,
    loading: true,
    refresh: () => {},
};

const FeatureFlagsContext = createContext<FeatureFlags>(defaults);

export function useFeatureFlags() {
    return useContext(FeatureFlagsContext);
}

export function FeatureFlagsProvider({ children }: { children: React.ReactNode }) {
    const [flags, setFlags] = useState<Omit<FeatureFlags, "refresh" | "loading">>({
        hide_financials: false,
        show_financials: true,
        is_admin: false,
    });
    const [loading, setLoading] = useState(true);

    const fetchFlags = useCallback(async () => {
        try {
            const data = await fetchAPI<{
                hide_financials: boolean;
                show_financials: boolean;
                is_admin: boolean;
            }>("/feature-flags");
            setFlags({
                hide_financials: data.hide_financials ?? false,
                show_financials: data.show_financials ?? true,
                is_admin: data.is_admin ?? false,
            });
        } catch {
            // Feil – vis økonomidata som standard (fail-open)
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchFlags();
    }, [fetchFlags]);

    return (
        <FeatureFlagsContext.Provider value={{ ...flags, loading, refresh: fetchFlags }}>
            {children}
        </FeatureFlagsContext.Provider>
    );
}
