# FIX SECRET_KEY MISMATCH - 401 Errors

## Problem
JWT tokens signeres av Vercel med `NEXTAUTH_SECRET`, men valideres av Railway med `SECRET_KEY`. Hvis disse er forskjellige → 401 Unauthorized.

## Løsning (5 minutter)

### Steg 1: Generer nytt delt secret
```bash
# På Mac/Linux terminal:
openssl rand -hex 32
```

Kopier output (f.eks. `a1b2c3d4e5f6...`).

### Steg 2: Sett i Vercel
1. Gå til: https://vercel.com/frank-vevles-projects
2. Finn prosjekt: **befs1** (frontend)
3. Gå til: Settings → Environment Variables
4. Oppdater: `NEXTAUTH_SECRET` = `a1b2c3d4e5f6...` (fra steg 1)
5. **Redeploy frontend** (Deployments → latest → ⋯ → Redeploy)

### Steg 3: Sett i Railway
1. Gå til: https://railway.app
2. Finn service: **befs1** (backend)
3. Gå til: Environment → Environment Variables
4. Oppdater: `SECRET_KEY` = `a1b2c3d4e5f6...` (SAMME verdi fra steg 1)
5. **Manuell deploy** (Manual Deploy → Deploy latest commit)

### Steg 4: Verifiser
```bash
# Vent 2-3 minutter på deploy, deretter test:
curl https://befs1.railway.app/api/v1/health

# Skal returnere:
{"status":"healthy","service":"knowme-backend","db":"connected",...}
```

## Sjekkliste
- [ ] Generert nytt secret med `openssl rand -hex 32`
- [ ] Satt `NEXTAUTH_SECRET` i Vercel = same value
- [ ] Satt `SECRET_KEY` i Railway = same value  
- [ ] Redeployed frontend (Vercel)
- [ ] Redeployed backend (Railway)
- [ ] Health endpoint OK
- [ ] Login fungerer (ingen 401)

## Når er denne fikset?
✅ Når dere kan logge inn på frontend og kalle beskyttede API endepunkter uten 401-feil.

## Referanser
- CODE_REVIEW_30-01.md - Fix 1: Secrets Verification (P0+++)
- [security.py](backend/app/core/security.py) - JWT validation logic
