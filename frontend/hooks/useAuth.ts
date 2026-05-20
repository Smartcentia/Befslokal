"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { User, Session } from "@supabase/supabase-js";
import {
  isLocalAuthEnabled,
  getLocalSession,
  clearLocalSession,
  type LocalAuthUser,
} from "@/lib/localAuth";

export interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  // Compat helpers matching old useSession shape
  email: string | null;
  name: string | null;
  role: string | null;
  accessToken: string | null;
}

export function useAuth(): AuthState & { signOut: () => Promise<void> } {
  const [state, setState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    email: null,
    name: null,
    role: null,
    accessToken: null,
  });

  useEffect(() => {
    if (isLocalAuthEnabled()) {
      const local = getLocalSession();
      setState(buildLocalState(local?.user ?? null, false));
      return;
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setState(buildState(session, false));
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setState(buildState(session, false));
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = useCallback(async () => {
    if (isLocalAuthEnabled()) {
      clearLocalSession();
      setState(buildLocalState(null, false));
      return;
    }
    await supabase.auth.signOut();
  }, []);

  return { ...state, signOut };
}

function buildState(session: Session | null, loading: boolean): AuthState {
  const user = session?.user ?? null;
  const meta = user?.user_metadata ?? {};
  return {
    user,
    session,
    loading,
    email: user?.email ?? null,
    name: meta.full_name ?? meta.name ?? user?.email ?? null,
    role: meta.role ?? null,
    accessToken: session?.access_token ?? null,
  };
}

function buildLocalState(localUser: LocalAuthUser | null, loading: boolean): AuthState {
  if (!localUser) {
    return {
      user: null,
      session: null,
      loading,
      email: null,
      name: null,
      role: null,
      accessToken: null,
    };
  }
  const pseudoUser = {
    id: localUser.id,
    email: localUser.email,
    user_metadata: { name: localUser.name, role: localUser.role },
  } as unknown as User;
  return {
    user: pseudoUser,
    session: null,
    loading,
    email: localUser.email,
    name: localUser.name,
    role: localUser.role,
    accessToken: null,
  };
}
