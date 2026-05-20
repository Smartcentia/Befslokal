# Rapport: Eiendomfebruar.csv – Regnskapsdata for Bufetat

**Dato:** 20. februar 2026
**Fil:** `Eiendomfebruar.csv` (prosjektrot)

---

## Hva er dette?

Filen er en **eksport av alle eiendomsrelaterte kostnader fra Bufetat sitt regnskapssystem (Visma/Xledger)**. Den inneholder betalte fakturaer og posteringer knyttet til leie, strøm, renhold, vaktmestertjenester og annet driftsrelatert for Bufetat sine lokaler over hele landet.

---

## Størrelse og tidsrom

| | |
|---|---|
| **Antall transaksjoner** | 136 055 |
| **Tidsrom** | 2020 – 2025 (6 år med data) |
| **Samlet beløp** | **ca. 2,96 milliarder NOK** |
| **Rader med eiendomskobling** | 44 328 av 136 055 (32 %) |

> **Merk:** 68 % av radene mangler direkte eiendomskobling (adressen i Dim2-feltet er tom). Disse er registrert på en enhet/avdeling, men ikke koblet til en spesifikk eiendom.

---

## Hva slags kostnader er det?

| Kostnadskategori | Totalt (NOK) | Andel |
|---|---|---|
| Husleie / leiekostnader | 1 138 836 817 | 38 % |
| Leie av maskiner og utstyr | 772 644 556 | 26 % |
| Lys, varme og strøm | 180 280 624 | 6 % |
| Vedlikehold | 169 500 171 | 6 % |
| Andre driftskostnader | 152 913 914 | 5 % |
| Forsikring | 118 650 150 | 4 % |
| Renhold og rengjøring | 110 984 739 | 4 % |
| Vaktmestertjenester | 72 903 898 | 2 % |
| Kommunale avgifter | 10 679 223 | <1 % |
| Vakthold / sikkerhet | 10 601 518 | <1 % |
| Øvrig | ca. 218 000 000 | 7 % |

**Husleie alene utgjør 1,1 milliarder NOK over 6 år** – dette er den klart største kostnadsposten.

---

## Fordeling på regioner

| Region | Antall transaksjoner |
|---|---|
| Sør | 37 782 |
| Øst | 35 373 |
| Nord | 24 856 |
| Vest | 20 472 |
| Midt | 15 799 |
| Bufdir (sentralt) | 1 430 |
| Øvrig | 343 |

---

## Største leverandører

| Leverandør | Antall fakturalinjer |
|---|---|
| Statsbyggs hovedkontor | 14 398 |
| ISS Facility Services AS | 8 595 |
| Ishavskraft AS | 7 878 |
| Sognekraft AS | 4 805 |
| KINECT ENERGY SPOT AS | 4 031 |
| MASKE AS | 3 279 |
| Elis Norge AS | 2 434 |

**Statsbygg** er klart størst – dette er leieavtaler med staten. Kraftleverandørene (Ishavskraft, Sognekraft, KINECT) dekker strøm og oppvarming.

---

## Fordeling per år

| År | Antall transaksjoner |
|---|---|
| 2020 | 23 011 |
| 2021 | 20 412 |
| 2022 | 21 886 |
| 2023 | 19 519 |
| 2024 | 22 092 |
| 2025 | 29 135 |

Data er relativt jevnt fordelt over 6 år, med en økning i 2025.

---

## Teknisk format (for referanse)

| Egenskap | Verdi |
|---|---|
| Filformat | CSV, komma-separert |
| Tegnkoding | Windows-1252 (norsk) |
| Antall kolonner | 26 |
| Beløpsformat | `1,234.56` og `(7,500.00)` for negative beløp |
| Datoformat | M/DD/YYYY (f.eks. `3/31/2023`) |

### Hva kolonnen Dim2(T) betyr (eiendomskobling)

`Dim2(T)` inneholder **adressen til eiendommen** kostnaden tilhører, f.eks.:
- `Torget 6, 2000 Lillestrøm`
- `Ramsrudveien 32, 3518 Hønefoss`

Dette er feltet systemet bruker for å koble transaksjoner til riktig eiendom i databasen.

---

## Hva skjer når vi importerer?

1. **Systemet leser filen** og detekterer format automatisk
2. **For hver transaksjon** forsøker systemet å matche `Dim2(T)`-adressen mot en eiendom i databasen
3. **Ved treff:** Transaksjonen lagres og kobles til eiendommen → vises i regnskapsoversikten
4. **Uten treff:** Transaksjonen hoppes over (registreres som feil)

**Forventet resultat ved import:**
- ~44 000 transaksjoner vil trolig matche (de med utfylt Dim2-adresse)
- ~92 000 transaksjoner uten eiendomsadresse vil bli hoppet over
- For å få flere treff kan vi utvide matching til å bruke enhetsnavnet (Dim1) som kobling

---

## Vurdering

| Spørsmål | Svar |
|---|---|
| Er dataene troverdige? | Ja – dette er reelle regnskapsdata fra Visma |
| Kan vi importere nå? | Ja – teknisk støtte er implementert |
| Hva mister vi? | 68 % av radene uten eiendomsadresse importeres ikke |
| Bør vi beholde alle 6 år? | Det anbefales – gir historikk for trendanalyse |
| Risiko ved import? | Lav – import er ikke-destruktiv og kan gjøres på nytt |
