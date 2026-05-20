"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function RiskError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        if (process.env.NODE_ENV !== "production") {
            console.error("[Risiko]", error);
        }
    }, [error]);

    return (
        <div className="space-y-4 rounded-lg border border-destructive/30 bg-destructive/5 p-6">
            <h1 className="text-xl font-semibold">Kunne ikke laste risikobildet</h1>
            <p className="text-muted-foreground">
                Noe gikk galt ved lasting av siden. Prøv igjen, eller kontroller at backend er tilgjengelig
                og at miljøvariabler for API er satt i Vercel.
            </p>
            {error.digest ? (
                <p className="font-mono text-xs text-muted-foreground">Referanse: {error.digest}</p>
            ) : null}
            <Button type="button" onClick={() => reset()}>
                Prøv igjen
            </Button>
        </div>
    );
}
