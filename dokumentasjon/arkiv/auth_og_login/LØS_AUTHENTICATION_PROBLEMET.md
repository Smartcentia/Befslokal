# ✅ Løs Authentication Problemet - Steg for Steg

## Problem

Console viser: **"Authentication header missing"** - dette betyr at `session.accessToken` er `undefined`.

---

## Løsning: 5 Enkle Steg

### Steg 1: Verifiser NEXTAUTH_SECRET i Vercel

1. **Gå til:** https://vercel.com/dashboard
2. **Finn app:** `knowme-frontend` (eller lignende navn)
3. **Klikk:** Settings → Environment Variables
4. **Sjekk:** Finn `NEXTAUTH_SECRET` i listen

**Hvis den IKKE eksisterer:**
- Klikk "Add New"
- Name: `NEXTAUTH_SECRET`
- Value: `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`
- Environment: ✅ Production, ✅ Preview, ✅ Development
- Klikk "Save"

**Hvis den eksisterer men er tom:**
- Klikk "Edit" på `NEXTAUTH_SECRET`
- Sett Value: `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`
- Klikk "Save"

### Steg 2: Redeploy Frontend

**VIKTIG:** Frontend må redeployes etter å ha satt/endret environment variable!

1. **Gå til:** Vercel Dashboard → Deployments
2. **Klikk:** "Redeploy" på siste deployment
3. **Eller:** Trigger ny deploy via git push
4. **Vent:** 2-5 minutter til deploy er ferdig

### Steg 3: Logg Ut og Slett Cookies

**VIKTIG:** Eksisterende session har ikke token - må opprette ny!

1. **Logg ut** fra frontend
2. **Åpne DevTools:** `Cmd+Option+I` (Mac) eller `F12` (Windows)
3. **Gå til:** Application tab → Cookies
4. **Slett alle cookies** for `knowme-frontend-amber.vercel.app`
5. **Eller:** Slett alle cookies i browser

### Steg 4: Logg Inn På Nytt

1. **Gå til:** https://knowme-frontend-amber.vercel.app
2. **Logg inn** med `admin@befs.no`
3. **Åpne Console:** `Cmd+Option+I` → Console tab
4. **Se etter:** Debug-meldinger

### Steg 5: Test Session

**Kjør dette i browser console:**

```javascript
import('next-auth/react').then(m => {
  m.getSession().then(s => {
    console.log('=== SESSION TEST ===');
    console.log('Has session?', !!s);
    console.log('Has accessToken?', !!s?.accessToken);
    console.log('AccessToken:', s?.accessToken);
    
    if (!s?.accessToken) {
      console.error('❌ PROBLEM: No accessToken in session!');
      console.log('Session object:', s);
    } else {
      console.log('✅ SUCCESS: accessToken found!');
      console.log('Token length:', s.accessToken.length);
    }
  });
});
```

**Forventet output:**
```
=== SESSION TEST ===
Has session? true
Has accessToken? true
AccessToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
✅ SUCCESS: accessToken found!
Token length: 200+
```

**Hvis du ser `❌ PROBLEM: No accessToken in session!`:**
- `NEXTAUTH_SECRET` er ikke satt eller feil
- Frontend er ikke redeployet
- Gå tilbake til Steg 1 og 2

---

## Debug-Meldinger i Console

**Etter innlogging, se etter:**

### ✅ Gode Meldinger:
- `[NextAuth] Generating backend token for user: admin@befs.no`
- `[NextAuth] Token generated, length: XXX`
- `[fetchAPI] Token found, length: XXX`

### ❌ Dårlige Meldinger:
- `[NextAuth] NEXTAUTH_SECRET is not defined!` → Secret mangler
- `[NextAuth] No accessToken in token object!` → Token settes ikke
- `[fetchAPI] No accessToken in session!` → Session har ikke token

---

## Hvis Det Fortsatt Feiler

### Sjekkliste:

- [ ] Er `NEXTAUTH_SECRET` satt i Vercel?
- [ ] Er verdien `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`?
- [ ] Er den satt for Production, Preview og Development?
- [ ] Er frontend redeployet etter å ha satt secret?
- [ ] Har du logget ut og slettet cookies?
- [ ] Har du logget inn på nytt?
- [ ] Viser console `[NextAuth] Generating backend token`?

### Test Backend Secret:

**Sjekk at backend også har riktig secret:**

1. **Gå til:** https://fly.io/apps/knowme-backend-prod/secrets
2. **Sjekk:** `SECRET_KEY` eksisterer
3. **Sett:** `SECRET_KEY` = `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`
4. **Deploy backend** (se `HVOR_ER_DEPLOY_KNAPPEN.md`)

**VIKTIG:** `SECRET_KEY` (backend) og `NEXTAUTH_SECRET` (frontend) må være identiske!

---

## Quick Test

**Etter å ha fulgt alle steg:**

1. **Gå til:** Dashboard eller Contracts side
2. **Sjekk:** Skal laste data (ikke "Ingen kontrakter funnet")
3. **Console:** Skal ikke vise "Authentication header missing"
4. **Console:** Skal vise `[fetchAPI] Token found`

---

## Oppsummering

1. ✅ Sett `NEXTAUTH_SECRET` i Vercel
2. ✅ Redeploy frontend
3. ✅ Logg ut og slett cookies
4. ✅ Logg inn på nytt
5. ✅ Test session i console

**Dette SKAL fikse problemet!** 🔐
