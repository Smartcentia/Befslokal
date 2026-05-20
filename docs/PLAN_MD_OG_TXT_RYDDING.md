# Plan: .md-filer ut av rot + .txt i .gitignore

## Status (sjekk 31.01.2025)

### 1. .md-filer i GitHub-rot

- **På GitHub (origin):** Mange `.md`-filer ligger fortsatt i roten fordi flyttingen aldri ble fullført i git.
- **Lokalt:**
  - De gamle `.md`-filene i rot er **slettet** (vises som `D` i `git status`).
  - Alt innhold ligger nå i mappen **`dokumentasjon/`** (ikke `docs/`).
  - **`dokumentasjon/` er untracked** – mappen er aldri blitt `git add` og commitet.

**Konklusjon:** Du flyttet filene til `dokumentasjon/`, men ga aldri git den nye mappen. Derfor ser GitHub fortsatt de gamle filene i rot.

### 2. docs vs dokumentasjon

- **`docs/`** inneholder bare `README.md` (én fil).
- **`dokumentasjon/`** inneholder alle de flyttede arkiv-/dokumentasjonsfilene (hundrevis av .md).

Scriptet `move_md_to_dokumentasjon.py` flytter til **dokumentasjon**, ikke **docs**. Hvis du vil at alt skal ligge under **docs**, må vi enten:
- omdøpe `dokumentasjon/` → `docs/` og flytte innhold der, eller
- beholde `dokumentasjon/` og bare fullføre commit/push (da forsvinner .md fra rot på GitHub).

### 3. .txt og .gitignore

- **`.gitignore` inneholder ikke `*.txt`.** Ingen regel for .txt i dag.
- **Tracked .txt-filer:** Blant annet:
  - `backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt` (brukes i koden – **må forbli i repo**)
  - `backend/app/ai_lab/prompts/*.txt`
  - `backend/docs/*.txt`, `backend/app/scripts/*.txt` m.m.

Hvis vi legger til **`*.txt`** uten unntak, vil bl.a. `befs_instruksjoner.txt` bli ignorert og kan forsvinne fra repo / feile i deploy. Derfor bør vi enten:
- ignorere **kun .txt i prosjektrot** (f.eks. `/*.txt`), eller
- bruke `*.txt` og eksplisitte **unntak** for filer som skal være i repo.

---

## Anbefalt plan

### Steg 1: Fullfør flyttingen av .md (slik at GitHub ikke lenger viser .md i rot)

1. **Legg til den nye mappen og commit sletting av gamle filer** (på main trenger du ikke merge – bare add, commit, push):
   ```bash
   git add dokumentasjon/
   git add -u
   git status   # sjekk at du ser: nye filer under dokumentasjon/, slettede .md i rot/arkiv/backend osv.
   git commit -m "docs: Flytt alle .md til dokumentasjon/, fjern fra rot"
   git push origin main
   ```
2. Etter push vil .md-filene i rot på GitHub forsvinne og ligge under `dokumentasjon/`.

(Valgfritt: Hvis du vil at alt skal hete **docs** i stedet for **dokumentasjon**, kan vi omdøpe mappen før `git add` – se steg 2.)

### Steg 2: Valgfritt – bruk `docs/` som hovedmappe for dokumentasjon

Hvis du vil samle alt under **docs** (som du opprinnelig tenkte):

1. **Flytt innhold fra `dokumentasjon/` til `docs/`:**
   - F.eks. flytt alle filer og undermapper fra `dokumentasjon/` inn i `docs/` (ev. bruk script).
2. **Slett den tomme `dokumentasjon/`:**
   - Etter at alt er flyttet.
3. **Commit:**
   - `git add docs/` og `git add -u` (slett dokumentasjon), deretter commit og push.

Da vil GitHub vise én samlet **docs/** i stedet for **dokumentasjon/**.

### Steg 3: .txt i .gitignore

**Anbefaling:** Ignorer **kun .txt i prosjektrot**, så vi ikke ved et uhell ignorerer viktige backend-filer.

I **`.gitignore`** (f.eks. under "Misc"):

```gitignore
# .txt i rot (logger, eksport, midlertidige filer)
/*.txt
```

Dette ignorerer kun filer som `sammenstilt.txt`, `stderr.txt`, `unmatched_properties.txt` osv. i roten. Filer under `backend/` (inkl. `befs_instruksjoner.txt` og prompts) forblir tracked.

**Alternativ:** Hvis du virkelig vil ignorere **alle** .txt i hele repo:

```gitignore
*.txt
# Unntak: filer som må være i repo
!backend/app/services/intelligence/ki_kollega/befs_instruksjoner.txt
!backend/app/ai_lab/prompts/
!backend/app/ai_lab/prompts/*.txt
```

Da må du evt. legge til flere `!`-unntak for andre .txt-filer som skal versjoneres.

### Steg 4: Fjerne .txt-filer som allerede er tracked i rot (valgfritt)

Hvis det ligger .txt i rot som nå blir ignorert, vil git fortsatt spore dem til du fjerner dem fra indeksen (uten å slette filene lokalt):

```bash
git rm --cached *.txt
# eller kun konkrete filer, f.eks.:
# git rm --cached stderr.txt stdout.txt sammenstilt.txt ...
```

Deretter commit og push. Lokale filer blir værende; de dukker ikke lenger opp på GitHub.

---

## Kort sjekkliste

- [ ] Bestem: beholde **dokumentasjon/** eller samle alt under **docs/**.
- [ ] `git add dokumentasjon/` (eller `docs/` etter flytt) + `git add -u`.
- [ ] Commit med tydelig melding (flytt .md ut av rot).
- [ ] Push til `origin main`.
- [ ] Legg til `/*.txt` (eller `*.txt` + unntak) i `.gitignore`.
- [ ] Valgfritt: `git rm --cached` for .txt i rot som ikke skal versjoneres.
- [ ] Commit og push .gitignore (og evt. cache-fjerning).

Etter dette vil GitHub ikke lenger vise mange .md-filer i rot, og .txt i rot (eller alle .txt, med valgte unntak) vil være ignorert som ønsket.
