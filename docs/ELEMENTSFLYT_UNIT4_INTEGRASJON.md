# Integrasjonsplan: ElementsFlyt - Unit4

Denne planen beskriver integrasjonen mellom ElementsFlyt (sak/arkiv) og Unit4 (økonomi) for å oppnå bedre økonomistyring ved å synkronisere avtaleinformasjon.

## 1. Formål og Omfang

**Formål:** Bedre økonomistyring og internkontroll.
**Hovedfunksjon:** Opprette et register over avtaler i Unit4 med direkte tilgang til kontraktsdokumentene i ElementsFlyt.
**Bruksområde:**
1.  **Tilgang:** Gi økonomimedarbeidere i Unit4 direkte tilgang til kontrakter lagret i ElementsFlyt.
2.  **Avstemming:** Muliggjøre kontroll av fakturaer og regnskapstall i Unit4 opp mot faktiske avtalevilkår i kontrakten.
3.  **Feilsøking:** Identifisere avvik mellom bokførte opplysninger og kontraktsdata.

Integrasjonen er teknisk sett **en-veis** fra ElementsFlyt til Unit4, men støtter en **toveis arbeidsprosess** der brukeren jobber i begge systemer.

## 2. Arbeidsflyt for Avstemming (Brukerscenario)

For å løse behovet for å "bruke Unit4 regnskapsdata og dokumentarkiv kontrakten", legges følgende arbeidsflyt til grunn:

1.  **I Unit4 (Økonomi):** En økonomimedarbeider behandler en faktura eller gjennomgår regnskapstall for en leverandør/prosjekt.
2.  **Behov oppstår:** Medarbeideren trenger å verifisere om beløpet stemmer med inngått avtale.
3.  **Tilgang:** Vedkommende slår opp på "Begrepsverdi" (DIM7) for den aktuelle avtalen i Unit4.
4.  **Oppslag:** Feltet `attributeValue` inneholder saksnummeret, som er en klikkbar **hyperkobling**.
5.  **I ElementsFlyt (Dokument):** Klikk på lenken åpner saken direkte i ElementsFlyt, hvor originalkontrakten ligger.
6.  **Kontroll:** Medarbeideren sammenligner regnskapstallene (fra Unit4) med kontraktsvilkårene (i Elements) og avdekker eventuelle feil.

## 3. Arkitektur og Dataflyt

Data flyter fra ElementsFlyt til DFØs integrasjonspunkt, som deretter oppdaterer Unit4.

1.  **Kilde (ElementsFlyt):** Saksbehandler oppretter sak/avtale.
2.  **Trigger:** Avtale signeres og merkes for overføring.
3.  **Integrasjon (API Kalls):** Data hentes fra Elements og sendes til DFØ API.
4.  **Mål (Unit4):** Data lagres som begrepsverdier (DIM7/R07).

### Masterdata som overføres:
*   Sakstittel (Avtalens navn)
*   Saksnummer (inkl. hyperkobling til saken i Elements)

## 3. Integrasjonsdetaljer (DFØ API)

Integrasjonen benytter DFØs REST-API for begrepsverdier.

- **Metode:** `POST`
- **Endepunkt (KINT/Test):** `https://api-dev.dfo.no/begrepsverdier/v2/BU`
- **Endepunkt (Akseptansetest):** `https://apitest.dfo.no/begrepsverdier/v2/BU`
- **Endepunkt (Prod):** `https://api.dfo.no/begrepsverdier/v2/BU`

### Data-mapping

| Felt i API Payload | Beskrivelse | Mapping fra ElementsFlyt | Verdi / Kommentar |
| :--- | :--- | :--- | :--- |
| `attributeName` | Begrepsnavn | Fast verdi | `DIM7` |
| `attributeId` | Begreps-ID | Fast verdi | `R07` |
| `companyId` | Firmakode | Fast verdi | `BU` |
| `description` | Beskrivelse | `Sak.Tittel` (Journalpost innhold?) | Beskrivelse/tittel på avtalen. |
| `attributeValue` | Verdi | `Sak.Saksnummer` | Må være hyperkobling til saken i Elements. |
| `periodFrom` | Gyldig fra | `Sak.OpprettetDato`? | *Format:* YYYYMM (f.eks. `202501`). **Må avklares med DFØ om `197001` er OK.** |
| `periodTo` | Gyldig til | Fast verdi | `209912` (Standard) |
| `status` | Status | Fast verdi | `N` (N = Aktiv) |

**OBS:** Feltene `periodFrom`, `periodTo`, og `status` kan endres i DFØ/Unit4 etter opprettelse. Integrasjonen **MÅ IKKE** overskrive disse ved eventuelle oppdateringer, med mindre det er en eksplisitt ønsket handling.
Hvis `description` korrigeres i Elements: Må avklares om ny overføring skal skje.

## 4. Trigger og Logikk i ElementsFlyt

For å kun overføre relevante og signerte avtaler, implementeres følgende logikk/metadata:

### A. Kategorisering (Metadata)
1.  **Saksmappetype:** Bruk av relevante mapper (f.eks. "Innkjøp").
    *   *Merk:* Saken opprettes ofte FØR signert avtale. Overføring skjer ved signering.
2.  **Tilleggsattributt (Påkrevd):** Indikator for overføring status.
    *   **Navn:** `Overføring Unit4` (eller lignende)
    *   **Type:** Rullgardin / Liste
    *   **Verdier:**
        *   (Tomt) - *Ingen handling*
        *   `Avtale signert – overfør til Unit4` - *Trigger integrasjon*
        *   `Skal ikke overføres til Unit4` - *Eksplisitt unntak*

### B. Trigger-Regel
Integrasjonen kjører (eller poller) og ser etter saker hvor:
*   `Tilleggsattributt` er satt til `Avtale signert – overfør til Unit4`.
*   (Opsjon) `Saksmappetype` er en av de definerte typene (f.eks. "Innkjøp").

### C. Kvalitetssikring (Manuelle rutiner)
Dokumentforvaltningen kjører ukentlige søk for å fange opp avvik:
*   Søk etter saker av type "Innkjøp" (eller relevante typer).
*   Filtrer der `Tilleggsattributt` mangler "Avtale signert...".
*   Sjekk om journalposttittel inneholder "Signert".
*   Dette sikrer at saksbehandlere husker å sette attributtet.

## 5. Implementeringsplan

### Fase 1: KINT (Test)
1.  Sette opp tilgang til DFØ KINT-miljø.
2.  Konfigurere ElementsFlyt med nødvendige tilleggsattributter.
3.  Utvikle/konfigurere integrasjonsscriptet mot `api-dev.dfo.no`.
4.  **Test:** Opprett sak i Elements -> Sett attributt -> Verifiser resultatet i Unit4 (KINT).

### Fase 2: Akseptansetest (Prod-kopi)
1.  Flytte konfigurasjon til Prod-kopi miljøet.
2.  Endre URL til `apitest.dfo.no`.
3.  Gjennomføre ende-til-ende test med reelle data.
4.  Utarbeide dokumentasjon til DFØ (Flytdiagram + beskrivelse).

### Fase 3: Produksjon
1.  Oversende dokumentasjon til DFØ.
2.  Avtale dato for produksjonssetting.
3.  Endre URL til `api.dfo.no` og aktivere.

## 6. Uavklarte Punkter / Spørsmål
*   **Oppdatering av beskrivelse:** Hvis `description` (sakstittel) endres i Elements etter overføring, skal API-et kalles på nytt for å oppdatere Unit4?
*   **Datostyring:** Er `197001` akseptert av DFØ som standard `periodFrom`?
*   **Sletting:** Hva skjer hvis en avtale slettes eller annulleres i Elements? Skal `status` settes til noe annet enn `N`?
