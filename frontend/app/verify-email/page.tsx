"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, Loader2, Mail, CheckCircle2 } from "lucide-react";
import Link from "next/link";

function VerifyEmailContent() {
    const [code, setCode] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [success, setSuccess] = useState(false);
    const [email, setEmail] = useState("");
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        // Get email from query params or session
        const emailParam = searchParams.get("email");
        if (emailParam) {
            setEmail(emailParam);
            // Auto-send verification code on mount
            handleSendCode(emailParam);
        }
    }, [searchParams]);

    const handleSendCode = async (emailToSend?: string) => {
        const emailAddress = emailToSend || email;
        if (!emailAddress) {
            setError("E-postadresse mangler");
            return;
        }

        setSending(true);
        setError("");

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/send-verification-code`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email: emailAddress }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Kunne ikke sende bekreftelseskode");
            }

            setSuccess(false); // Reset success message
        } catch (err: any) {
            setError(err.message || "Kunne ikke sende bekreftelseskode. Prøv igjen.");
        } finally {
            setSending(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        if (!email) {
            setError("E-postadresse mangler");
            setLoading(false);
            return;
        }

        if (code.length !== 6 || !code.match(/^\d{6}$/)) {
            setError("Koden må være 6 sifre");
            setLoading(false);
            return;
        }

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/verify-email`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ email, code }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Ugyldig bekreftelseskode");
            }

            // Success - redirect to login
            setSuccess(true);
            setTimeout(() => {
                router.push("/login?verified=true");
            }, 2000);
        } catch (err: any) {
            setError(err.message || "Ugyldig bekreftelseskode. Prøv igjen.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md">
            {/* Logo/Header */}
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl text-primary-foreground font-bold text-2xl shadow-lg shadow-primary/20 mb-4">
                    B
                </div>
                <h1 className="text-3xl font-bold text-foreground mb-2">
                    Bekreft e-postadresse
                </h1>
                <p className="text-muted-foreground">
                    Vi har sendt en 6-sifret kode til din e-postadresse
                </p>
            </div>

            {/* Verification Form */}
            <div className="glass-card p-8 border border-border">
                {success && (
                    <div className="mb-6 p-4 bg-success/10 border border-success/20 text-success rounded-lg flex items-center gap-3">
                        <CheckCircle2 size={20} />
                        <span className="text-sm">E-postadresse bekreftet! Omdirigerer...</span>
                    </div>
                )}

                {error && (
                    <div className="mb-6 p-4 bg-danger/10 border border-danger/20 text-danger rounded-lg flex items-center gap-3">
                        <AlertCircle size={20} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                {email && (
                    <div className="mb-6 p-4 bg-surface border border-border rounded-lg flex items-center gap-3">
                        <Mail size={20} className="text-muted-foreground" />
                        <span className="text-sm text-foreground">{email}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label
                            htmlFor="code"
                            className="block text-sm font-medium text-foreground mb-2"
                        >
                            Bekreftelseskode
                        </label>
                        <input
                            id="code"
                            type="text"
                            value={code}
                            onChange={(e) => {
                                const value = e.target.value.replace(/\D/g, "").slice(0, 6);
                                setCode(value);
                            }}
                            required
                            disabled={loading || success}
                            maxLength={6}
                            className="w-full px-4 py-3 bg-surface border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all disabled:opacity-50 text-center text-2xl tracking-widest font-mono"
                            placeholder="000000"
                            autoComplete="one-time-code"
                        />
                        <p className="mt-2 text-xs text-muted-foreground text-center">
                            Skriv inn 6-sifret kode fra e-posten din
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || success || code.length !== 6}
                        className="w-full px-6 py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={20} className="animate-spin" />
                                Bekrefter...
                            </>
                        ) : (
                            "Bekreft e-postadresse"
                        )}
                    </button>
                </form>

                <div className="mt-6 pt-6 border-t border-border">
                    <button
                        type="button"
                        onClick={() => handleSendCode()}
                        disabled={sending || !email}
                        className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {sending ? (
                            <>
                                <Loader2 size={16} className="animate-spin" />
                                Sender...
                            </>
                        ) : (
                            <>
                                <Mail size={16} />
                                Send ny kode
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Back to login */}
            <div className="mt-6 text-center">
                <Link
                    href="/login"
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    ← Tilbake til innlogging
                </Link>
            </div>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center px-6 py-12">
            <Suspense fallback={
                <div className="flex items-center justify-center">
                    <Loader2 size={32} className="animate-spin text-primary" />
                </div>
            }>
                <VerifyEmailContent />
            </Suspense>
        </div>
    );
}
