#!/usr/bin/env node
/**
 * Sett nytt passord for en Supabase Auth-bruker (admin).
 * Krever SUPABASE_SERVICE_ROLE_KEY og NEXT_PUBLIC_SUPABASE_URL.
 *
 * Bruk:
 *   cd frontend && node --env-file=.env scripts/reset-password.mjs <epost> <nytt-passord>
 * eller:
 *   NEXT_PUBLIC_SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node frontend/scripts/reset-password.mjs <epost> <nytt-passord>
 */

import { createClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const [email, newPassword] = process.argv.slice(2);

if (!url || !serviceRoleKey) {
  console.error('Mangler miljøvariabler. Sett NEXT_PUBLIC_SUPABASE_URL og SUPABASE_SERVICE_ROLE_KEY.');
  console.error('Kjør f.eks. fra frontend/: node --env-file=.env scripts/reset-password.mjs <epost> <passord>');
  process.exit(1);
}

if (!email || !newPassword) {
  console.error('Bruk: node reset-password.mjs <epost> <nytt-passord>');
  process.exit(1);
}

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function main() {
  // Finn bruker via listUsers (filtrer på e-post)
  let page = 1;
  const perPage = 500;
  let user = null;

  while (true) {
    const { data, error } = await supabase.auth.admin.listUsers({ page, perPage });
    if (error) {
      console.error('Feil ved henting av brukere:', error.message);
      process.exit(1);
    }
    const match = data.users.find((u) => (u.email || '').toLowerCase() === email.toLowerCase());
    if (match) {
      user = match;
      break;
    }
    if (data.users.length < perPage) break;
    page++;
  }

  if (!user) {
    console.error('Bruker ikke funnet med e-post:', email);
    process.exit(1);
  }

  const { error } = await supabase.auth.admin.updateUserById(user.id, { password: newPassword });
  if (error) {
    console.error('Feil ved oppdatering av passord:', error.message);
    process.exit(1);
  }

  console.log('Passord oppdatert for:', user.email);
}

main();
