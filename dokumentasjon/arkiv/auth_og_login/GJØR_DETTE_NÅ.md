# ⚡ Gjør Dette Nå - Fix 401-Feil

## Problem

Console viser `401 (Unauthorized)` - dette er **authentication-problem**, ikke database-problem.

---

## Løsning: 3 Enkle Steg

### Steg 1: Sett Backend URL i Vercel (KRITISK!)

1. **Gå til:** https://vercel.com/dashboard
2. **Finn app:** `knowme-frontend` (eller lignende)
3. **Settings** → **Environment Variables**
4. **Edit eller Add:** `NEXT_PUBLIC_API_URL`
5. **Sett verdi:** `https://befs1.railway.app/api/v1`
6. **Environment:** ✅ Production, ✅ Preview, ✅ Development
7. **Save**

### Steg 2: Sett NEXTAUTH_SECRET i Vercel (KRITISK!)

1. **Vercel Dashboard** → **Settings** → **Environment Variables**
2. **Edit eller Add:** `NEXTAUTH_SECRET`
3. **Sett verdi:** `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`
   - (Samme som `SECRET_KEY` i Railway)
4. **Environment:** ✅ Production, ✅ Preview, ✅ Development
5. **Save**

### Steg 3: Redeploy Frontend (KRITISK!)

**VIKTIG:** Frontend må redeployes etter å ha satt environment variables!

1. **Vercel Dashboard** → **Deployments**
2. **Klikk:** "Redeploy" på siste deployment
3. **Eller:** Push til git (auto-deploy)
4. **Vent:** 2-5 minutter

---

## Etter Redeploy

### 1. Logg Ut og Slett Cookies

1. **Logg ut** fra frontend
2. **DevTools** → **Application** → **Cookies** → **Delete all**
3. **Logg inn på nytt**

### 2. Test

1. **Gå til:** Dashboard eller Properties
2. **Sjekk:** Skal laste data (ikke "Ingen eiendommer funnet")
3. **Console:** Skal ikke vise 401-feil

---

## Verifiser Railway Backend

**Først, sjekk at Railway backend er Live:**

```bash
curl https://befs1.railway.app/api/v1/health
```

**Forventet:**
```json
{
  "status": "healthy",
  "service": "knowme-backend",
  "db": "connected"
}
```

**Hvis backend ikke svarer:**
- Sjekk Railway Dashboard → Er service "Live"?
- Se Railway logs for errors

---

## Debug i Console

**Etter innlogging, kjør dette:**

```javascript
// Test API URL
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL || 'Using fallback: https://befs1.railway.app/api/v1');

// Test session
import('next-auth/react').then(m => {
  m.getSession().then(s => {
    console.log('Has accessToken?', !!s?.accessToken);
    if (!s?.accessToken) {
      console.error('❌ PROBLEM: No accessToken!');
    } else {
      console.log('✅ SUCCESS: accessToken found!');
    }
  });
});
```

---

## Oppsummering

**Dette er IKKE database-problem - det er authentication-problem!**

**Løsning:**
1. ✅ Sett `NEXT_PUBLIC_API_URL` = `https://befs1.railway.app/api/v1`
2. ✅ Sett `NEXTAUTH_SECRET` = `IlNtm7y1eaEJ6Rst/wzt5twWOzo8xMjGlOFFDbBV1As=`
3. ✅ Redeploy frontend
4. ✅ Logg ut og inn på nytt

**Dette SKAL fikse problemet!** 🔐
