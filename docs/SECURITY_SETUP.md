# 🔒 Sikkerhetsskanning - Oppsettguide

Denne guiden viser hvordan du setter opp automatisert sikkerhetsskanning for BEFS-prosjektet.

## 📋 Innholdsfortegnelse

1. [Dependabot (GitHub Native)](#1-dependabot-github-native)
2. [Snyk Security Platform](#2-snyk-security-platform)
3. [Pre-commit Hooks (Lokal)](#3-pre-commit-hooks-lokal)
4. [Vedlikehold og Monitoring](#4-vedlikehold-og-monitoring)

---

## 1. Dependabot (GitHub Native)

### ✅ Allerede konfigurert!

Dependabot er nå satt opp via `.github/dependabot.yml` og vil:
- Skanne dependencies hver mandag kl 09:00
- Automatisk opprette PR-er for sikkerhetoppdateringer
- Gruppere minor/patch updates for enklere review

### Aktivering i GitHub:

1. Gå til repo **Settings** → **Security** → **Code security and analysis**
2. Aktiver:
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates
   - ✅ Dependabot version updates

### Behandle Dependabot PRs:

```bash
# 1. Sjekk PR lokalt
git fetch origin
git checkout dependabot/pip/backend/fastapi-0.116.0

# 2. Test at alt fungerer
cd backend
pytest
cd ../frontend
npm test

# 3. Merge hvis OK
git checkout main
git merge --no-ff dependabot/pip/backend/fastapi-0.116.0
git push
```

---

## 2. Snyk Security Platform

### Steg 1: Registrering

1. Gå til [snyk.io](https://snyk.io) og klikk "Sign up free"
2. Velg "Sign up with GitHub"
3. Autoriser Snyk

### Steg 2: Importer prosjekt

1. I Snyk dashboard, klikk "Add project"
2. Velg GitHub → `BEFS_CLEAN`
3. Velg både `/backend` og `/frontend`
4. Klikk "Add selected repositories"

### Steg 3: Konfigurer GitHub Secret

1. Gå til repo **Settings** → **Secrets and variables** → **Actions**
2. Klikk "New repository secret"
3. Navn: `SNYK_TOKEN`
4. Verdi: Hent fra [snyk.io/account](https://snyk.io/account) → API Token
5. Klikk "Add secret"

### Steg 4: Verifiser GitHub Actions

GitHub Actions `.github/workflows/snyk-security.yml` vil nå kjøre automatisk:
- ✅ Ved hver push til main/develop
- ✅ Ved hver PR
- ✅ Daglig kl 02:00

Sjekk status:
```bash
# Gå til repo → Actions → Snyk Security Scan
```

### Steg 5: Konfigurer notifications

I Snyk dashboard:
1. Gå til **Settings** → **Notifications**
2. Aktiver:
   - ✅ Email alerts for new vulnerabilities
   - ✅ Slack integration (valgfritt)
   - ✅ Weekly summary

---

## 3. Pre-commit Hooks (Lokal)

Pre-commit hooks kjører sikkerhetsskanning **før** du committer kode.

### Installasjon:

```bash
# 1. Installer pre-commit
pip install pre-commit

# 2. Installer hooks i repo
cd /Users/frank/Documents/BEFS_CLEAN
pre-commit install

# 3. Test at det fungerer
pre-commit run --all-files
```

### Hva sjekkes?

- ✅ **Bandit**: Python security issues (SQL injection, hardcoded passwords, etc.)
- ✅ **detect-secrets**: Forhindrer commit av API-nøkler, tokens, passwords
- ✅ **Black**: Python code formatting
- ✅ **General checks**: Trailing whitespace, large files, merge conflicts

### Bruk:

```bash
# Pre-commit kjører automatisk ved git commit
git add .
git commit -m "Add feature"
# → Pre-commit hooks kjører automatisk!

# Hoppe over hooks (IKKE anbefalt!)
git commit --no-verify -m "Emergency fix"

# Kjøre manuelt
pre-commit run --all-files
```

### Oppdatere hooks:

```bash
# Oppdater til nyeste versjoner
pre-commit autoupdate

# Commit endringene
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

---

## 4. Vedlikehold og Monitoring

### Daglig rutine:

**Ingenting!** Alt kjører automatisk 🎉

### Ukentlig rutine (Mandag morgen):

1. Sjekk GitHub → **Security** → **Dependabot alerts**
2. Review Dependabot PRs og merge
3. Sjekk Snyk dashboard for nye sårbarheter

### Månedlig rutine:

1. Review alle ignorerte sårbarheter i `.snyk` (fjern utløpte)
2. Kjør full security audit:

```bash
# Backend
cd backend
pip install safety
safety check --json

# Frontend
cd frontend
npm audit --audit-level=moderate
```

3. Oppdater pre-commit hooks:

```bash
pre-commit autoupdate
```

### Når du får en sikkerhetsalarm:

#### Prioritering:

| Severity | Action | Timeline |
|----------|--------|----------|
| **Critical** | 🔴 Fix ASAP | < 24 timer |
| **High** | 🟠 Fix this week | < 7 dager |
| **Medium** | 🟡 Fix this sprint | < 30 dager |
| **Low** | 🟢 Fix when convenient | Backlog |

#### Workflow:

```bash
# 1. Sjekk detaljer
# Gå til GitHub Security tab eller Snyk dashboard

# 2. Opprett branch
git checkout -b security/fix-CVE-2024-1234

# 3. Fix sårbarheten
# Oppgrader dependency eller patch kode

# 4. Test
pytest  # Backend
npm test  # Frontend

# 5. Commit og push
git add .
git commit -m "security: fix CVE-2024-1234 in package X"
git push origin security/fix-CVE-2024-1234

# 6. Opprett PR og merge
```

---

## 📊 Oversikt over verktøy

| Verktøy | Hva det scanner | Når det kjører | Kostnad |
|---------|----------------|----------------|---------|
| **Dependabot** | Dependencies (Python, npm) | Ukentlig + ved sikkerhetsfunn | Gratis |
| **Snyk** | Dependencies, Code, Docker, IaC | Daglig + ved PR | Gratis (open source) |
| **Bandit** | Python code security | Pre-commit + CI/CD | Gratis |
| **Safety** | Python dependencies | CI/CD | Gratis |
| **npm audit** | npm dependencies | CI/CD | Gratis |
| **Gitleaks** | Hardcoded secrets | CI/CD | Gratis |
| **detect-secrets** | Secrets i commits | Pre-commit | Gratis |

---

## 🚨 Alarmer og notifikasjoner

### GitHub:

- **Email**: Automatiske alerts ved kritiske sårbarheter
- **Web**: [github.com/Smartcentia/BEFS1/security](https://github.com/Smartcentia/BEFS1/security)

### Snyk:

- **Email**: Daglig/ukentlig sammendrag
- **Slack**: Integrer med team-kanal (anbefalt)
- **Web**: [app.snyk.io](https://app.snyk.io)

### Konfigurer Slack (valgfritt):

1. Gå til Snyk → **Settings** → **Integrations** → **Slack**
2. Klikk "Connect to Slack"
3. Velg kanal (f.eks. `#befs-alerts`)
4. Velg notification preferences

---

## ✅ Suksesskriterier

Du vet at sikkerhetskanningen fungerer når:

- ✅ Dependabot oppretter PRs hver uke
- ✅ Snyk-badge viser "passing" i README
- ✅ Pre-commit blokkerer commits med secrets
- ✅ GitHub Actions kjører uten feil
- ✅ Du får email ved kritiske sårbarheter

---

## 🆘 Feilsøking

### "Pre-commit hook failed"

```bash
# Reinstaller hooks
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### "SNYK_TOKEN not found"

```bash
# Sjekk at secret er satt i GitHub
# Settings → Secrets and variables → Actions → SNYK_TOKEN
```

### "Dependabot PR conflicts"

```bash
# Rebase Dependabot branch
gh pr checkout [PR-nummer]
git rebase main
git push --force-with-lease
```

---

## 📚 Ressurser

- [Dependabot dokumentasjon](https://docs.github.com/en/code-security/dependabot)
- [Snyk dokumentasjon](https://docs.snyk.io)
- [Pre-commit dokumentasjon](https://pre-commit.com)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

**Spørsmål?** Sjekk [GitHub Issues](https://github.com/Smartcentia/BEFS1/issues) eller kontakt sikkerhetsteamet.
