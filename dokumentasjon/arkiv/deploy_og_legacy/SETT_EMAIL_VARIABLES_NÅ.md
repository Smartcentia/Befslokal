# 📧 Sett Email Environment Variables - Instruksjoner

## Situasjon

Du trenger å sette email environment variables i BEFS1 service for at e-postbekreftelse og MFA skal fungere.

**Backend:** BEFS1 (`srv-d5sgj1ggjchc738u2ro0`)  
**URL:** https://befs1.railway.app

---

## Hva Trenger Du?

### Alternativ 1: Resend (Anbefalt) ⭐

Du trenger:
1. **Resend API Key** - Få fra [resend.com](https://resend.com/api-keys)
2. **EMAIL_FROM** - Fra-adresse (f.eks. `noreply@befs.no`)

### Alternativ 2: SMTP

Du trenger:
1. **SMTP_HOST** - F.eks. `smtp.gmail.com`
2. **SMTP_PORT** - F.eks. `587`
3. **SMTP_USER** - Din e-postadresse
4. **SMTP_PASSWORD** - App password eller passord
5. **SMTP_USE_TLS** - `true`
6. **EMAIL_FROM** - Fra-adresse

---

## Sett Variables via Railway Dashboard

Siden Railway MCP kan være ustabil, her er den sikreste metoden:

### Steg-for-steg:

1. **Gå til:** [Railway Dashboard](https://railway.app)
2. **Klikk på:** "BEFS1" service
3. **I venstre meny:** Klikk "Environment"
4. **Klikk:** "Edit" knapp (øverst til høyre i Environment Variables-seksjonen)
5. **Legg til nye variables:**

**For Resend:**
- Klikk "+ Add Environment Variable"
- Key: `RESEND_API_KEY`
- Value: `re_xxxxx` (din Resend API key)
- Klikk "Save"

- Klikk "+ Add Environment Variable" igjen
- Key: `EMAIL_FROM`
- Value: `noreply@befs.no` (eller din e-postadresse)
- Klikk "Save"

**For SMTP:**
- Legg til alle 6 variables (se over)

6. **Railway redeployer automatisk** når du lagrer

---

## Hvis Du Vil Prøve Railway MCP

Hvis Railway MCP fungerer, kan du be meg:

```
Sett RESEND_API_KEY environment variable i BEFS1 service til re_xxxxx
```

Eller:

```
Sett EMAIL_FROM environment variable i BEFS1 service til noreply@befs.no
```

**Men:** Den sikreste metoden er å gjøre det manuelt i Railway Dashboard.

---

## Verifisering

Etter at du har satt variables:

1. **Vent på redeploy** (1-2 minutter)
2. **Sjekk logs** i Railway Dashboard → Logs
3. **Se etter:**
   - `✅ Email service initialized with Resend` (hvis Resend)
   - `✅ Email service initialized with SMTP` (hvis SMTP)
   - `⚠️ No email service configured` (hvis ingenting er satt)

4. **Test:** Logg inn som ny bruker og sjekk e-posten din

---

## Har Du Allerede Resend API Key eller SMTP Credentials?

Hvis du har credentials klar, kan du:
1. **Sette dem manuelt i Railway Dashboard** (anbefalt)
2. **Eller gi meg verdiene** og jeg kan prøve å sette dem via MCP

---

**Status:** Vent på at du setter email variables, enten manuelt eller via MCP
