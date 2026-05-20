# 🔐 KRITISK: Synkroniser SECRET_KEY og NEXTAUTH_SECRET NÅ

## Problem

Console viser: **"Invalid signature"** - dette betyr:
- ❌ Frontend signerer tokens med `NEXTAUTH_SECRET` (Vercel)
- ❌ Backend verifiserer med `SECRET_KEY` (Fly.io)
- ❌ **De matcher ikke!**

## Løsning: Sjekk og Synkroniser Secrets

### Steg 1: Sjekk Backend SECRET_KEY (Fly.io)

1. **Gå til:** https://fly.io/apps/knowme-backend-prod/secrets
2. **Finn:** `SECRET_KEY` i listen
3. **Klikk:** "Edit" eller "View" for å se verdien
4. **Kopier:** Verdien (f.eks. `n96UqNbcpHmpBaM0ztX/fKn5vPtORM+e42TwB/7j2II=`)

### Steg 2: Sjekk Frontend NEXTAUTH_SECRET (Vercel)

1. **Gå til:** https://vercel.com/dashboard
2. **Finn app:** `knowme-frontend` (eller lignende navn)
3. **Settings** → **Environment Variables**
4. **Finn:** `NEXTAUTH_SECRET`
5. **Sjekk:** Er den satt? Hva er verdien?

### Steg 3: Sammenlign

**Hvis de er forskjellige:**
- ✅ **Dette er problemet!**
- De må være **identiske**

### Steg 4: Synkroniser

**Alternativ A: Sett Vercel = Fly.io (Anbefalt)**

1. **Vercel Dashboard:**
   - Settings → Environment Variables
   - Finn eller legg til `NEXTAUTH_SECRET`
   - Sett verdi til samme som Fly.io `SECRET_KEY`
   - Velg: Production (og Preview/Development hvis nødvendig)
   - Save

2. **Redeploy Frontend:**
   - Vercel Dashboard → Deployments
   - Klikk "Redeploy" på siste deployment
   - Eller vent til neste git push (auto-deploy)

**Alternativ B: Sett Fly.io = Vercel**

1. **Fly.io Dashboard:**
   - Secrets tab
   - Edit `SECRET_KEY`
   - Sett til samme verdi som Vercel `NEXTAUTH_SECRET`
   - Save

2. **Restart Backend:**
   - Machines tab → Klikk "Restart" på maskinen
   - Eller: Activity tab → "Redeploy"

### Steg 5: Hvis Ingen Secret Eksisterer

**Generer ny secret:**

```bash
openssl rand -base64 32
```

**Sett på begge:**
1. **Fly.io:** Secrets → Add → `SECRET_KEY` = [generert verdi]
2. **Vercel:** Environment Variables → Add → `NEXTAUTH_SECRET` = [samme verdi]

**Restart begge:**
- Backend: Restart machine
- Frontend: Redeploy

---

## Verifisering

### Test fra Frontend:

1. **Gå til:** https://knowme-frontend-amber.vercel.app
2. **Logg inn**
3. **Åpne Console:** `Cmd+Option+I` → Console tab
4. **Sjekk:** Skal ikke lenger se "Invalid signature" feil
5. **Test:** Gå til Dashboard → Skal laste data (ikke 401-feil)

### Test Backend:

```bash
# Test health (skal fungere uten auth)
curl https://knowme-backend-prod.fly.dev/api/v1/health

# Test med token (fra frontend session)
# Skal ikke returnere 401 Unauthorized
```

---

## Viktig

- ✅ `SECRET_KEY` (Fly.io) og `NEXTAUTH_SECRET` (Vercel) må være **identiske**
- ✅ Frontend må redeployes etter å ha satt environment variable
- ✅ Backend må restartes etter å ha endret secret (hvis du endrer Fly.io)

---

## Hvorfor Dette Skjer

1. **Frontend (NextAuth):**
   - Signerer JWT tokens med `NEXTAUTH_SECRET`
   - Sender tokens i Authorization header

2. **Backend (AuthMiddleware):**
   - Verifiserer tokens med `SECRET_KEY`
   - Hvis secrets ikke matcher → "Invalid signature"

3. **Løsning:**
   - Begge må bruke samme secret verdi!

---

## Quick Fix (Hvis du har tilgang)

**Sett samme verdi på begge:**

1. **Fly.io:** https://fly.io/apps/knowme-backend-prod/secrets
   - Edit `SECRET_KEY` → Sett verdi

2. **Vercel:** https://vercel.com → Settings → Environment Variables
   - Edit/Add `NEXTAUTH_SECRET` → Sett samme verdi

3. **Restart/Redeploy:**
   - Backend: Restart machine
   - Frontend: Redeploy

---

**Dette er sannsynligvis årsaken til 401-feilene!** 🔐
