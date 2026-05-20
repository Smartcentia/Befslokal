import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Browser client — use in Client Components
// Lazy initialization to avoid crash during SSR build if env vars are absent
let _supabase: ReturnType<typeof createBrowserClient> | null = null

const authStub = {
  getSession: async () => ({ data: { session: null }, error: null }),
  getUser: async () => ({ data: { user: null }, error: null }),
  onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
  getRedirectUrl: () => Promise.resolve(null),
  signInWithOAuth: async () => ({ data: { url: null }, error: { message: 'Supabase not configured' } }),
  signInWithPassword: async () => ({ data: { user: null, session: null }, error: { message: 'Supabase not configured' } }),
  signOut: async () => ({ error: null }),
} as const

function getSupabaseClient() {
  if (!_supabase) {
    if (!supabaseUrl || !supabaseAnonKey) {
      // Return stub whenever env is missing (SSR and browser) so app never crashes when not configured
      return { auth: authStub } as unknown as ReturnType<typeof createBrowserClient>
    }
    _supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
  }
  return _supabase
}

export const supabase = new Proxy({} as ReturnType<typeof createBrowserClient>, {
  get(_target, prop) {
    return (getSupabaseClient() as unknown as Record<string, unknown>)[prop as string]
  }
})

// Helper: get current session token for API calls
export async function getAccessToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

// Helper: get current user
export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}
