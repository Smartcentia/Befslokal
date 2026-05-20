/**
 * Lokal innlogging uten Supabase – bruker backend /auth/validate-credentials.
 * Aktiveres med NEXT_PUBLIC_LOCAL_AUTH=true
 */

export const LOCAL_AUTH_STORAGE_KEY = "befs_local_session";

export interface LocalAuthUser {
  id: string;
  email: string;
  name: string | null;
  role: string | null;
  mfa_verified?: boolean;
  mfa_enabled?: boolean;
}

export interface LocalAuthSession {
  user: LocalAuthUser;
  createdAt: number;
}

export function isLocalAuthEnabled(): boolean {
  return process.env.NEXT_PUBLIC_LOCAL_AUTH === "true";
}

export function getLocalSession(): LocalAuthSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(LOCAL_AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as LocalAuthSession;
    if (!parsed?.user?.email) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setLocalSession(user: LocalAuthUser): void {
  if (typeof window === "undefined") return;
  const session: LocalAuthSession = { user, createdAt: Date.now() };
  localStorage.setItem(LOCAL_AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearLocalSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(LOCAL_AUTH_STORAGE_KEY);
}

export async function loginWithCredentials(
  email: string,
  password: string
): Promise<{ ok: true; user: LocalAuthUser } | { ok: false; error: string }> {
  const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
  const url = `${base}/api/v1/auth/validate-credentials`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    return { ok: false, error: "Kunne ikke kontakte backend" };
  }

  const data = await res.json();
  if (!data.success || !data.user) {
    return { ok: false, error: data.detail || "Ugyldig e-post eller passord" };
  }

  const user: LocalAuthUser = {
    id: data.user.id,
    email: data.user.email,
    name: data.user.name ?? data.user.email,
    role: data.user.role ?? null,
    mfa_verified: data.user.mfa_verified,
    mfa_enabled: data.user.mfa_enabled,
  };

  setLocalSession(user);
  return { ok: true, user };
}
