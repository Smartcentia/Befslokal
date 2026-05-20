"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import { isLocalAuthEnabled, loginWithCredentials } from "@/lib/localAuth";
import { safeRedirectPath } from "@/app/components/auth/RequireAuth";

function LoginForm() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();
    const searchParams = useSearchParams();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        if (isLocalAuthEnabled()) {
            const result = await loginWithCredentials(email, password);
            setLoading(false);
            if (!result.ok) {
                setError(result.error);
                return;
            }
        } else {
            const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
            setLoading(false);
            if (authError) {
                setError("Ugyldig e-post eller passord");
                return;
            }
        }

        const next = safeRedirectPath(searchParams.get("redirect"));
        router.push(next);
        router.refresh();
    };

    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
            <div className="w-full max-w-md">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl text-primary-foreground font-bold text-2xl shadow-lg shadow-primary/20 mb-4">
                        B
                    </div>
                    <h1 className="text-3xl font-bold text-foreground mb-2">BEFS</h1>
                    <p className="text-muted-foreground">
                        {isLocalAuthEnabled() ? "Befslokal – lokal drift" : "Bufetat Eiendomsforvaltningssystem"}
                    </p>
                </div>

                {/* Login Form */}
                <div className="glass-card p-8 border border-border">
                    <h2 className="text-xl font-semibold text-foreground mb-6">Logg inn</h2>

                    {error && (
                        <div className="mb-6 p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg flex items-center gap-3">
                            <AlertCircle size={20} />
                            <span className="text-sm">{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                                E-post
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={loading}
                                className="w-full px-4 py-3 bg-surface border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all disabled:opacity-50"
                                placeholder="din@epost.no"
                                autoComplete="email"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                                Passord
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={loading}
                                className="w-full px-4 py-3 bg-surface border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all disabled:opacity-50"
                                placeholder="••••••••"
                                autoComplete="current-password"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-6 py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    Logger inn...
                                </>
                            ) : (
                                "Logg inn"
                            )}
                        </button>
                    </form>
                </div>

                {isLocalAuthEnabled() && (
                    <p className="mt-4 text-center text-xs text-muted-foreground">
                        Standard: admin@befslokal.no / befslokal123
                    </p>
                )}

                <div className="mt-6 text-center">
                    <Link href="/welcome" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                        ← Tilbake til velkomstside
                    </Link>
                </div>
            </div>
        </div>
    );
}

function LoginFallback() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
            <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" aria-label="Laster" />
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<LoginFallback />}>
            <LoginForm />
        </Suspense>
    );
}
