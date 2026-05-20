# Instruks for Leverandørkontroll og Risikostyring (v2.0)

**Formål:** Sikre at [Virksomheten] kun handler med seriøse leverandører, oppfyller kravene i Hvitvaskingsloven/FOA, og minimerer risiko for økonomisk tap.

## 1. Brukerveiledning (For Saksbehandlere og Attestanter)

Når du behandler en faktura eller inngår en avtale, skal du alltid sjekke **Risikoindikatoren** på leverandørkortet i systemet. Systemet overvåker leverandøren i sanntid.

### Risikoklassifisering og Handlingsplikt

| Nivå | Fargekode | Beskrivelse | **Påkrevd Handling** |
| --- | --- | --- | --- |
| **LAV** | 🟢 GRØNN | Leverandøren er solid. Ingen negative anmerkninger. | **Ingen.** Faktura kan behandles/attesteres som normalt. |
| **MODERAT** | 🟡 GUL | Økt risiko. F.eks. fallende lønnsomhet, nylig endret styre, eller manglende historikk (nytt selskap). | **Vær årvåken.** Sjekk at varen/tjenesten faktisk er levert før godkjenning. |
| **HØY** | 🔴 RØD | Alvorlig risiko. Skattegjeld, inkassosaker, negativ egenkapital eller pant i driftstilbehør. | **Stopp!** Kontakt Økonomisjef før bestilling/betaling. Det kreves manuell godkjenning for å overstyre advarselen. |
| **KRITISK** | ⚫ SVART | Konkurs, tvangsoppløsning eller sanksjonstreff. | **BLOKKERT.** Leverandøren er sperret for betaling i økonomisystemet. Ingen unntak. |

### Hva betyr varslene? (Røde Flagg)

* **"Negativ Egenkapital / Tapt Aksjekapital":** Selskapet skylder mer enn det eier. Teknisk konkursfare.
* **"Sanksjonstreff / PEP":** Selskapet eller reelle rettighetshavere står på internasjonale sanksjonslister eller er politisk eksponert.
* **"Faktura-anomali":** Mønsteret i fakturering avviker sterkt fra normalen (f.eks. mange små fakturaer rett under fullmaktsgrensen).

---

## 2. Automatiske Prosesser (System-integrasjon)

Systemet er ikke bare passivt; det utfører aktive handlinger mot økonomisystemet (Unit4) basert på risiko.

### Automatisk Sperring (Unit4 Integration)

Hvis `Risikoscore` når nivået **KRITISK (100)**:

1. Systemet kaller Unit4 API (`PUT /api/agresso/supplier/{id}`).
2. Status på leverandør settes til **"P" (Parked/Sperret)**.
3. Alle åpne fakturaer i flyt (Workflow) settes automatisk på **"Hold"**.
4. E-postvarsel sendes umiddelbart til Regnskapssjef og Sikkerhetsansvarlig.

### Varsling ved Endringer (Early Warning)

Systemet lytter til endringer i Brønnøysundregistrene.

* *Scenario:* En "Grønn" leverandør melder oppbud (konkurs).
* *Reaksjon:* Innen 1 time oppdateres status til "Svart", og systemet stopper utbetalinger som ligger i bankremitteringsfilen hvis de ikke er sendt ennå.

---

## 3. Teknisk Dokumentasjon (For Utviklere)

### Risk Engine: Algoritme og Vekting

Risiko beregnes som en vektet sum (`TotalRiskScore`), normalisert til 0-100.

#### Datakilder (Input)

* **BRREG (Enhetsregisteret):** Statuskoder, Roller.
* **Regnskap (API):** Nøkkeltall siste 3 år.
* **Løsøreregisteret:** Tinglyste pant (Driftstilbehør/Varelager).
* **Unit4 (Internt):** Fakturadatoer, beløp, kontonummer.
* **Compliance (Sanksjoner):** OpenSanctions API / EU List.

#### Beregningslogikk (Pseudokode)

```python
def calculate_risk_score(supplier):
    score = 0
    flags = []

    # --- KRITISKE STOPP-FAKTORER (Instant 100) ---
    if supplier.status in ['Konkurs', 'Tvangsoppløsning', 'Avvikling']:
        return 100, ["KRITISK: Selskapet er under avvikling"]
    
    if check_sanctions_list(supplier.beneficial_owners):
        return 100, ["KRITISK: Treff på sanksjonsliste (EU/FN/OFAC)"]

    # --- ØKONOMISKE INDIKATORER (Vektet) ---
    # Negativ Egenkapital (Insolvensfare)
    if supplier.equity < 0:
        score += 40
        flags.append("Insolvent: Negativ egenkapital")
    
    # Driftsresultat (Lønnsomhet)
    if supplier.operating_profit < 0 and supplier.operating_profit_last_year < 0:
        score += 15
        flags.append("Vedvarende driftsunderskudd")

    # Pant og Heftelser (Likviditetspress)
    if has_recent_liens(supplier.orgnr, months=6):
        score += 25
        flags.append("Nylig pantstillelse i driftstilbehør/varelager")

    # --- ATFERDSANALYSE (Internt) ---
    # Endret bankkonto (Svindelfare)
    if unit4_check_bank_change(supplier.id, days=30):
        score += 30
        flags.append("OBS: Bankkontonummer nylig endret")

    # Faktureringsmønster (Anomali)
    if ai_anomaly_detection(supplier.invoices) > 0.8:
        score += 20
        flags.append("Uvanlig faktureringsmønster detektert")

    # --- ALDER OG STABILITET ---
    # Nytt selskap (< 6 mnd)
    if supplier.age_months < 6:
        score += 10
        flags.append("Nytt selskap (begrenset historikk)")

    # Endringer i styre/ledelse
    if supplier.recent_role_changes:
        score += 10
        flags.append("Nylige utskiftninger i styre/ledelse")

    return min(score, 100), flags
```

### API Respons (JSON Modell)

Endepunkt: `GET /api/risk-assessment/{orgnr}`

```json
{
  "orgnr": "987654321",
  "riskLevel": "HIGH", // LOW, MEDIUM, HIGH, CRITICAL
  "score": 65,
  "lastUpdated": "2024-02-14T10:00:00Z",
  "autoBlockActive": false,
  "redFlags": [
    {
      "code": "NEGATIVE_EQUITY",
      "description": "Selskapet har tapt aksjekapitalen.",
      "severity": "HIGH"
    },
    {
      "code": "RECENT_LIEN",
      "description": "Pant i varelager tinglyst 01.02.2024.",
      "severity": "MEDIUM"
    }
  ],
  "financialSummary": {
    "revenue": 15000000,
    "equity": -500000,
    "currency": "NOK"
  }
}
```

---

## 4. Personvern og Sikkerhet

* **Behandlingsgrunnlag:** Risikovurderingen er nødvendig for å oppfylle rettslige forpliktelser (Økonomireglementet i staten, Hvitvaskingsloven) og berettiget interesse (forhindre svindel).
* **Reelle Rettighetshavere:** Data om fysiske personer (eiere/styre) hentes kun for *aktive* leverandører og lagres kryptert. Slettes ved opphør av leverandørforhold.
* **Innsyn:** Leverandører har rett til innsyn i registrerte opplysninger som påvirker deres rating, jf. Forvaltningsloven.
