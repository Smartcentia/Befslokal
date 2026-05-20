import { RequireAuth } from "@/app/components/auth/RequireAuth";

/**
 * Alle ruter under /dashboard krever gyldig Supabase-sesjon.
 * (Vercel Deployment Protection er ekstra lag – se docs/DEPLOY_SJEKKLISTE.md.)
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return <RequireAuth>{children}</RequireAuth>;
}
