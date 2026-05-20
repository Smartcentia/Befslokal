// Backend URL: KUN NEXT_PUBLIC_API_URL (uten /api/v1). Ingen fallback – sett i Vercel/Render.
const envUrl = process.env?.NEXT_PUBLIC_API_URL;
const base = typeof envUrl === 'string' ? envUrl.trim() : '';
const devFallback = process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '';
const apiOrigin = base || devFallback;
export const API_BASE_URL = apiOrigin ? `${apiOrigin.replace(/\/$/, '')}/api/v1` : '';
export const BACKEND_URL = base ? base.replace(/\/$/, '') : '';

/** Rot-URL til API (uten /api/v1). Brukes for ruter som er montert under f.eks. /api/external/ (ikke /api/v1). */
export function getApiOrigin(): string {
    if (!API_BASE_URL) return '';
    return API_BASE_URL.replace(/\/api\/v1\/?$/, '');
}

/**
 * Full URL til external_api-router (FastAPI: prefix `/api/external`).
 * Eksempel: externalApiUrl('/brreg/123456789/regnskap') → …/api/external/brreg/123456789/regnskap
 */
export function externalApiUrl(path: string): string {
    const origin = getApiOrigin();
    if (!origin) throw new Error('NEXT_PUBLIC_API_URL is not set; cannot resolve external API URL');
    const p = path.startsWith('/') ? path : `/${path}`;
    return `${origin}/api/external${p}`;
}

import { supabase } from '@/lib/supabase';
import type { Session } from '@supabase/supabase-js';
import { isLocalAuthEnabled, getLocalSession } from '@/lib/localAuth';

/**
 * Bearer mot backend: shared secret som standard (krever ALLOW_SHARED_SECRET_BYPASS på backend).
 * Sett NEXT_PUBLIC_USE_SUPABASE_JWT_FOR_API=true når backend har gyldig SUPABASE_JWT_SECRET og JWT skal brukes.
 * NEXT_PUBLIC_ALLOW_BACKEND_SECRET_BYPASS=true tvinger shared secret selv om JWT-flagget er satt (nødmodus).
 */
export async function getApiAuthContext(): Promise<{
    token: string | null;
    session: Session | null;
}> {
    let session: Session | null = null;
    if (isLocalAuthEnabled()) {
        const local = getLocalSession();
        if (local?.user) {
            session = {
                user: { email: local.user.email } as Session['user'],
            } as Session;
        }
    } else {
        const { data } = await supabase.auth.getSession();
        session = data.session;
    }
    let token: string | null = session?.access_token ?? null;
    const bypassSecret =
        (typeof process.env.NEXT_PUBLIC_BACKEND_SECRET === "string" &&
            process.env.NEXT_PUBLIC_BACKEND_SECRET.trim()) ||
        "befs-super-secret-key-12345";

    const useSupabaseJwtForApi =
        process.env.NEXT_PUBLIC_USE_SUPABASE_JWT_FOR_API === "true";

    const allowSecretBypass =
        !useSupabaseJwtForApi ||
        process.env.NEXT_PUBLIC_ALLOW_BACKEND_SECRET_BYPASS === "true" ||
        process.env.NODE_ENV === "development";

    if (allowSecretBypass) {
        token = bypassSecret;
    }
    return { token, session };
}

export async function fetchAPI<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    if (process.env.NODE_ENV !== "production") {
        console.log(`[fetchAPI] Requesting: ${url}`);
    }

    const { token, session } = await getApiAuthContext();

    if (process.env.NODE_ENV !== "production") {
        if (!token) {
            console.warn("[fetchAPI] No accessToken in session", {
                hasSession: !!session,
                sessionKeys: session ? Object.keys(session) : [],
            });
        } else {
            console.log(`[fetchAPI] Token found, length: ${token.length}`);
        }
    }

    const headers: Record<string, string> = {
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers as Record<string, string>),
    };

    // Check for Impersonation (Admin Tool) or set current user email for personalization
    if (typeof window !== 'undefined') {
        const impersonateEmail = localStorage.getItem('impersonate_email');
        const simulateRole = localStorage.getItem('simulate_role');
        // Admin-API (/admin/*) må alltid identifisere innlogget konto (admin), ikke simulert bruker —
        // ellers får PATCH /admin/users 403 fordi effektiv bruker blir eiendomsforvalter e.l.
        // Admin-tunge jobber under /agent/admin/* må identifisere ekte admin (ikke impersonert bruker).
        const isAdminEndpoint =
            endpoint.startsWith('/admin') ||
            endpoint.startsWith('/agent/admin');

        if (impersonateEmail && !isAdminEndpoint) {
            headers['X-Impersonate-Email'] = impersonateEmail;
            if (process.env.NODE_ENV !== "production") {
                console.log(`[fetchAPI] Impersonating: ${impersonateEmail}`);
            }
        } else if (simulateRole && !impersonateEmail) {
            headers['X-Simulate-Role'] = simulateRole;
            // Also send user email to ensure backend knows who is simulating
            if (session?.user?.email) {
                headers['X-User-Email'] = session.user.email;
            }
            if (process.env.NODE_ENV !== "production") {
                console.log(`[fetchAPI] Simulating Role: ${simulateRole}`);
            }
        } else if (session?.user?.email) {
            // Send the actual logged in user's email for personalization
            // Brukeridentitet for RBAC (Bearer er shared secret eller Supabase JWT ved NEXT_PUBLIC_USE_SUPABASE_JWT_FOR_API)
            headers['X-User-Email'] = session.user.email;
        }
    }

    try {
        const res = await fetch(url, {
            cache: 'no-store',
            credentials: 'include', // Ensure cookies are sent (CORS)
            ...options,
            headers: headers,
        });

        if (!res.ok) {
            const errorBody = await res.text().catch(() => '');

            // Check for MFA Requirement
            // DISABLED FOR VERCEL AUTH STRATEGY
            /*
            if (res.status === 403) {
                try {
                    const errorJson = JSON.parse(errorBody);
                    if (errorJson.code === 'MFA_REQUIRED' || errorJson.mfa_required === true) {
                        if (typeof window !== 'undefined') {
                            window.location.href = '/verify-mfa';
                            throw new Error('MFA verification required');
                        }
                    }
                } catch (e) {
                    // Ignore parsing error, handle as normal error
                }
            }
            */

            if (process.env.NODE_ENV !== "production") {
                console.error(`[fetchAPI] HTTP Error ${res.status} at ${url}:`, errorBody);
            }
            throw new Error(`API Error: ${res.status} ${res.statusText} at ${url} - ${errorBody}`);
        }

        return res.json();
    } catch (error) {
        if (process.env.NODE_ENV !== "production") {
            console.error(`[fetchAPI] Network/Parse Error at ${url}:`, error);
        }
        throw error;
    }
}

/** Samme auth som fetchAPI, men URL under `/api/external/` (ikke `/api/v1`). Path: f.eks. `/brreg/123456789/regnskap`. */
export async function fetchExternalAPI<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = externalApiUrl(path);
    if (process.env.NODE_ENV !== "production") {
        console.log(`[fetchExternalAPI] Requesting: ${url}`);
    }

    const { token, session } = await getApiAuthContext();

    const headers: Record<string, string> = {
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers as Record<string, string>),
    };

    if (typeof window !== 'undefined') {
        const impersonateEmail = localStorage.getItem('impersonate_email');
        const simulateRole = localStorage.getItem('simulate_role');

        if (impersonateEmail) {
            headers['X-Impersonate-Email'] = impersonateEmail;
        } else if (simulateRole) {
            headers['X-Simulate-Role'] = simulateRole;
            if (session?.user?.email) {
                headers['X-User-Email'] = session.user.email;
            }
        } else if (session?.user?.email) {
            headers['X-User-Email'] = session.user.email;
        }
    }

    const res = await fetch(url, {
        cache: 'no-store',
        credentials: 'include',
        ...options,
        headers,
    });

    if (!res.ok) {
        const errorBody = await res.text().catch(() => '');
        if (process.env.NODE_ENV !== "production") {
            console.error(`[fetchExternalAPI] HTTP Error ${res.status} at ${url}:`, errorBody);
        }
        throw new Error(`API Error: ${res.status} ${res.statusText} at ${url} - ${errorBody}`);
    }

    const ct = res.headers.get('content-type');
    if (ct && ct.includes('application/json')) {
        return res.json() as Promise<T>;
    }
    return undefined as T;
}
