# Resend-oppsett for e-post (MFA og verifisering)

BEFS bruker Resend for å sende:
- **E-postverifikasjonskoder** (6 sifre) til nye brukere
- **MFA-lenker** (bekreft innlogging) etter innlogging

## Steg 1: Opprett Resend-konto

1. Gå til [resend.com](https://resend.com) og registrer deg
2. Gratis plan: 100 e-poster/dag, 3000/måned

## Steg 2: Hent API-nøkkel

1. Logg inn på [Resend Dashboard](https://resend.com/api-keys)
2. Klikk **Create API Key**
3. Gi den et navn (f.eks. "BEFS")
4. Kopier nøkkelen (starter med `re_`)

## Steg 3: Konfigurer miljøvariabler

### Lokal utvikling (`backend/.env`)

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=BEFS <onboarding@resend.dev>
```

**Viktig:** For testing uten egen domene brukes `onboarding@resend.dev` – Resends testdomene som fungerer uten verifisering.

### Produksjon (Railway, Fly.io, etc.)

1. **For testing:** Bruk fortsatt `onboarding@resend.dev`
2. **For produksjon med eget domene:**
   - Verifiser domenet på [resend.com/domains](https://resend.com/domains)
   - Legg til DNS-records (MX, TXT) som Resend viser
   - Bruk f.eks. `EMAIL_FROM=BEFS <noreply@befs.no>`

## Steg 4: Verifiser at det fungerer

1. Start backend: `cd backend && python run_server.py`
2. Sjekk loggen – du skal se: `✅ Email service initialized with Resend`
3. Logg inn og be om MFA-lenke – sjekk at e-post kommer

## Feilsøking

| Problem | Løsning |
|--------|---------|
| `⚠️ No email service configured` | `RESEND_API_KEY` er ikke satt |
| `❌ Resend API error: Unauthorized` | Ugyldig eller utløpt API-nøkkel |
| `❌ Resend API error: Domain not verified` | Bruk `onboarding@resend.dev` for testing, eller verifiser ditt domene |
| E-post kommer ikke | Sjekk spam-mappen; Resend har god leveringsrate |

## Alternativ: SMTP

Hvis du foretrekker egen SMTP-server (f.eks. Office 365, Gmail), sett i stedet:

```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=noreply@befs.no
```

Resend prioriteres hvis `RESEND_API_KEY` er satt.
