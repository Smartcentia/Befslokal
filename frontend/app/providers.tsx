"use client";

import * as Tooltip from "@radix-ui/react-tooltip";
import { FeatureFlagsProvider } from "@/contexts/FeatureFlagsContext";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <FeatureFlagsProvider>
            <Tooltip.Provider delayDuration={300} skipDelayDuration={100}>
                {children}
            </Tooltip.Provider>
        </FeatureFlagsProvider>
    );
}