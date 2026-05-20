"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, Loader2, CheckCircle2, Shield } from "lucide-react";
import Link from "next/link";

function VerifyMFAContent() {
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [success, setSuccess] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        // Get token from query params
        const token = searchParams.get("token");
        if (token) {
            handleVerifyToken(token);
        } else {
            setError("Mangler verifiseringslenke");
            setLoading(false);
        }
    }, [searchParams]);

    const handleVerifyToken = async (token: string) => {
        setLoading(true);
        setError("");

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/verify-mfa/${token}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Ugyldig eller utløpt verifiseringslenke");
            }

            // Success - set success message and redirect
            setSuccess(true);
            setTimeout(() => {
                router.push("/dashboard");
                router.refresh();
            }, 2000);
        } catch (err: any) {
            setError(err.message || "Kunne ikke bekrefte innlogging. Prøv å logge inn igjen.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md">
            {/* Logo/Header */}
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl text-primary-foreground font-bold text-2xl shadow-lg shadow-primary/20 mb-4">
                    <Shield size={32} />
                </div>
                <h1 className="text-3xl font-bold text-foreground mb-2">
                    Bekreft innlogging
                </h1>
                <p className="text-muted-foreground">
                    Verifiserer din innlogging...
                </p>
            </div>

            {/* Verification Status */}
            <div className="glass-card p-8 border border-border">
                {loading && (
                    <div className="text-center py-8">
                        <Loader2 size={48} className="animate-spin text-primary mx-auto mb-4" />
                        <p className="text-muted-foreground">Bekrefter innlogging...</p>
                    </div>
                )}

                {success && (
                    <div className="text-center py-8">
                        <CheckCircle2 size={48} className="text-success mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-foreground mb-2">
                            Innlogging bekreftet!
                        </h2>
                        <p className="text-muted-foreground">
                            Omdirigerer til dashboard...
                        </p>
                    </div>
                )}

                {error && (
                    <div className="space-y-6">
                        <div className="p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg flex items-center gap-3">
                            <AlertCircle size={20} />
                            <span className="text-sm">{error}</span>
                        </div>

                        <div className="space-y-4">
                            <p className="text-sm text-muted-foreground text-center">
                                Verifiseringslenken er ugyldig eller har utløpt.
                            </p>
                            <Link
                                href="/login"
                                className="block w-full px-6 py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-primary/20 text-center"
                            >
                                Gå til innlogging
                            </Link>
                        </div>
                    </div>
                )}
            </div>

            {/* Back to login */}
            {!loading && !success && (
                <div className="mt-6 text-center">
                    <Link
                        href="/login"
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                        ← Tilbake til innlogging
                    </Link>
                </div>
            )}
        </div>
    );
}

export default function VerifyMFAPage() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
            <Suspense fallback={
                <div className="flex items-center justify-center">
                    <Loader2 size={32} className="animate-spin text-primary" />
                </div>
            }>
                <VerifyMFAContent />
            </Suspense>
        </div>
    );
}
