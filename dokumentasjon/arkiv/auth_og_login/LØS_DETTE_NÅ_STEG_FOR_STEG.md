# 🔥 LØS DETTE NÅ - Steg-for-steg løsning

## Problem

Console viser: `[fetchAPI] No accessToken in session!`

**Årsak:** Frontend genererer ikke tokens fordi `NEXTAUTH_SECRET` mangler eller frontend ikke er redeployet.

---

## LØSNING - 3 kritiske steg (må gjøres i rekkefølge!)

### STEG 1: Sjekk NEXTAUTH_SECRET i Vercel (KRITISK!)

1. **Gå til:** https://vercel.com/dashboard
2. **Finn app:** `knowme-frontend-amber` (eller lignende navn)
3. **Settings** → **Environment Variables**
4. **Sjekk:** Finn `NEXTAUTH_SECRET` i listen

**Hvis den IKKE finnes:**
- ✅ Klikk **"Add Environment Variable"**
- ✅ **Name:** `NEXTAUTH_SECRET`
- ✅ **Value:** Generer ny (se nedenfor) eller bruk samme som `SECRET_KEY` i Railway
- ✅ **Velg:** ✅ Production, ✅ Preview, ✅ Development
- ✅ **Save**

**Hvis den finnes:**
- ✅ Klikk **"Edit"** (pencil-ikonet)
- ✅ **Sjekk:** Er verdien identisk med `SECRET_KEY` i Railway?
- ✅ Hvis ikke: Kopier `SECRET_KEY` fra Railway og sett som `NEXTAUTH_SECRET` i Vercel
- ✅ **Velg:** ✅ Production, ✅ Preview, ✅ Development
- ✅ **Save**

**Generer ny secret (hvis nødvendig):**
```bash
openssl rand -base64 32
```

**Viktig:** `NEXTAUTH_SECRET` (Vercel) og `SECRET_KEY` (Railway) må være **nøyaktig identiske**!

---

### STEG 2: Redeploy Frontend i Vercel (KRITISK!)

**Dette er det viktigste steget!** Uten redeploy vil ikke `NEXTAUTH_SECRET` være tilgjengelig.

1. **Vercel Dashboard** → **Deployments**
2. **Finn:** Siste deployment (øverst i listen)
3. **Klikk:** **"..."** (tre prikker) → **"Redeploy"**
4. **Eller:** Klikk **"Redeploy"** knapp hvis tilgjengelig
5. **Bekreft:** Klikk **"Redeploy"** i popup
6. **Vent:** 2-3 minutter mens frontend bygges og deployes

**Alternativ:** Push en tom commit til GitHub (triggerer auto-deploy):
```bash
git commit --allow-empty -m "trigger frontend redeploy"
git push
```

---

### STEG 3: Clear Cookies og Re-login (KRITISK!)

**Dette er også kritisk!** Eksisterende session ble generert uten `NEXTAUTH_SECRET`, så den har ikke `accessToken`.

1. **Åpne:** https://knowme-frontend-amber.vercel.app
2. **Logg ut** (hvis du er innlogget)
3. **Clear cookies:**
   - **Chrome/Edge:** `Cmd+Shift+Delete` → Velg "Cookies" → "Clear data"
   - **Eller:** Developer Tools → Application → Cookies → Delete alle for `vercel.app`
4. **Hard refresh:** `Cmd+Shift+R` (Mac) eller `Ctrl+Shift+R` (Windows)
5. **Logg inn igjen** med `admin@befs.no`

**Etter re-login skal du se i console:**
- ✅ `[NextAuth] Generating backend token for user: admin@befs.no`
- ✅ `[NextAuth] Token generated, length: XXX`
- ✅ `[fetchAPI] Token found, length: XXX`

**Ikke lenger:**
- ❌ `[fetchAPI] No accessToken in session!`
- ❌ `401 Unauthorized`
- ❌ `Authentication header missing`

---

## Verifisering

### Test 1: Sjekk Console etter Re-login

1. **Åpne Console:** `Cmd+Option+I` → Console tab
2. **Sjekk:** Skal se:
   - ✅ `[NextAuth] Generating backend token...`
   - ✅ `[fetchAPI] Token found, length: XXX`
   - ✅ Ingen `401 Unauthorized` feil

### Test 2: Gå til Dashboard

1. **Gå til:** Dashboard
2. **Sjekk:** Data skal laste (ikke "Ingen eiendommer funnet")
3. **Sjekk Console:** Skal ikke se 401-feil

### Test 3: Sjekk Network Tab

1. **Developer Tools** → **Network** tab
2. **Sjekk:** Requests til `befs1.railway.app`
3. **Klikk på en request** → **Headers**
4. **Sjekk:** Skal se `Authorization: Bearer <token>` header

---

## Hvis det fortsatt ikke fungerer

### Sjekkliste:

1. ✅ **Er `NEXTAUTH_SECRET` satt i Vercel?**
   - Settings → Environment Variables → Sjekk at den finnes
   - Sjekk at den er valgt for **Production** environment

2. ✅ **Er frontend redeployet?**
   - Deployments → Sjekk at siste deploy er etter at du satte `NEXTAUTH_SECRET`
   - Status skal være "Ready" (grønn)

3. ✅ **Er `SECRET_KEY` (Railway) identisk med `NEXTAUTH_SECRET` (Vercel)?**
   - Kopier fra Vercel og sammenlign med Railway
   - De må være **nøyaktig** like (inkludert alle tegn)

4. ✅ **Har du clearet cookies og re-logget inn?**
   - Dette er kritisk! Eksisterende session har ikke `accessToken`

5. ✅ **Er backend redeployet etter å ha satt `SECRET_KEY`?**
   - Railway Dashboard → BEFS1 → Sjekk at siste deploy er etter `SECRET_KEY` ble lagt til

---

## Debugging Tips

### Sjekk NextAuth Secret i Console

Åpne Console og skriv:
```javascript
// Sjekk om NEXTAUTH_SECRET er tilgjengelig (kun på server-side)
// Men du kan sjekke session:
const session = await getSession();
console.log('Session:', session);
console.log('AccessToken:', session?.accessToken);
```

### Sjekk Railway Backend Logs

1. **Railway Dashboard** → **BEFS1** → **Logs**
2. **Sjekk:** Skal ikke se:
   - ❌ "SECRET_KEY is not set"
   - ❌ "Invalid signature"
   - ❌ "Token verification failed"

### Test Backend Direkte

```bash
# Test health (skal fungere)
curl https://befs1.railway.app/api/v1/health

# Test med token (hvis du har token fra console)
curl -H "Authorization: Bearer <token>" https://befs1.railway.app/api/v1/dashboard/status
```

---

## Oppsummering

**Problemet:**
- ❌ `[fetchAPI] No accessToken in session!` → Frontend genererer ikke tokens

**Løsningen (3 kritiske steg):**
1. ✅ Sett `NEXTAUTH_SECRET` i Vercel (Production environment)
2. ✅ Redeploy frontend i Vercel
3. ✅ Clear cookies og re-login

**Etter dette skal alt fungere!** 🚀

---

## Quick Checklist

- [ ] `NEXTAUTH_SECRET` er satt i Vercel (Production)
- [ ] `SECRET_KEY` (Railway) = `NEXTAUTH_SECRET` (Vercel) (identiske!)
- [ ] Frontend er redeployet i Vercel
- [ ] Backend er redeployet i Railway (etter `SECRET_KEY`)
- [ ] Cookies er clearet
- [ ] Re-logget inn
- [ ] Console viser `[fetchAPI] Token found` (ikke "No accessToken")
- [ ] Dashboard laster data uten 401-feil

**Gjør alle stegene i rekkefølge - dette skal fungere!** 💪
