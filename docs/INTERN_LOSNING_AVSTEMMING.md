# Plan: Intern Avstemming og Kontroll i Egen Løsning (BEFS)

Dette dokumentet beskriver hvordan vår egen løsning (BEFS / KI Kollega) skal "løse alt" ved å hente data fra både Unit4 og ElementsFlyt for å utføre automatisk eller støttet avstemming.

## 1. Konsept
I stedet for kun manuell sjekk via lenker (som beskrevet i Elements-Unit4 integrasjonen), skal vår løsning **hente inn dataene** sentralt og utføre analysen.

**Mål:** Automatisert kontroll av at fakturerte beløp i Unit4 stemmer overens med kontraktsvilkårene i ElementsFlyt.

## 2. Arkitektur

Vår løsning (KI Kollega / Økonomi Dashboard) fungerer som en **Integrasjons-hub**:
1.  **Input 1 (Økonomi):** Henter transaksjoner/fakturaer fra Unit4 (API).
2.  **Input 2 (Avtale):** Henter kontraktdata og dokumentinnhold fra ElementsFlyt (OData/REST).
3.  **Prosessering:** Sammenstiller data basert på felles nøkkel (Saksnummer/DIM7).
4.  **Output:** Avviksrapport eller "Grønt lys" i dashboard.

## 3. Datakilder og Integrasjon

### A. Unit4 (Regnskap)
Vi må hente fakturadata for å vite *hva* som er betalt.
*   **Metode:** API / Dataoppslag / DataDump
*   **Nøkkeldata å hente:**
    *   LeverandørID (Kreditor)
    *   Beløp (Brutto/Netto)
    *   Dato (Bokføringsperiode/Fakturadato)
    *   **Begrepsverdi/Saksnummer (DIM7):** Dette er koblingen til kontrakten.

### B. ElementsFlyt (Kontrakt)
Vi må hente kontraktsdata for å vite *hva* som skulle vært betalt.
*   **Metode:** OData / REST API
*   **Nøkkeldata å hente:**
    *   Saksnummer (Matcher DIM7 fra Unit4).
    *   **Dokumentinnhold:** Selve avtaleteksten (PDF/Tekst) for AI-analyse.
    *   Metadata: Avtaleperiode, Beløpsgrenser (hvis registrert som metadata).

## 4. Løsningsdesign: "Den Digitale Kontrolløren"

### Steg 1: Datafangst
Systemet overvåker eller poller nye transaksjoner i Unit4. Når en transaksjon er merket med DIM7 (Saksnummer):
1.  Systemet slår opp dette saksnummeret i ElementsFlyt via API.
2.  Henter tilhørende avtaledokument(er).

### Steg 2: Tolkning (AI/KI)
Siden kontraktsvilkår ustrukturert tekst (PDF), bruker vi KI-modulen (KI Kollega) til å tolke avtalen:
*   *Prompt for analyse:* "Les denne kontrakten og finn avtalte priser (timepris/fastpris) og gyldighet."
*   *Output:* Struktivert JSON (Pris, Valuta, Periode, Ref).

### Steg 3: Avstemming (Logikk)
Systemet sammenligner automatisk:
*   **Faktura (Unit4):** Kr 50.000,- (Periode Jan 2026)
*   **Kontrakt AI-Output:** "Fastpris kr 50.000,- pr mnd".
*   **Resultat:** Match OK = Grønn status.

### Steg 4: Rapportering
*   Viser status i "Vår Løsning".
*   Lager en "Attest" som systemet kan returnere til saksbehandler eller Unit4?
*   Varsler saksbehandler kun ved **avvik** (Feil beløp, utgått kontrakt etc).

## 5. Forutsetninger for suksess
*   **DIM7 Integrasjonen (Elements -> Unit4):** Må være på plass (slik vi planla først) for at Unit4 skal ha saksnummeret koblet til bilagene.
*   **Tilgang:** BEFS må ha tilgang (API-nøkler) til begge kildesystemene.
*   **Kvalitet:** Kontraktene må være lesbare (OCR-behandlet i Elements).

## 6. Neste Steg
1.  Verifisere at vi kan hente DIM7 feltet fra Unit4 API-et.
2.  Teste uthenting av dokumenttekst fra Elements for en pilotsak.
3.  Bygge en enkel prototype som matcher tall fra A mot tekst fra B.
