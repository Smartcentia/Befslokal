#!/usr/bin/env python3
"""
Utvidet kravkatalog v2 — legger til ~100 nye krav til requirements-tabellen.
Kjør ETTER seed_requirements.py (v1 med 33 krav).

Kjør:
  DATABASE_URL=... python3 scripts/seed_requirements_v2.py
  DATABASE_URL=... python3 scripts/seed_requirements_v2.py --dry-run
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except Exception:
    pass

import app.db.base  # noqa
from app.db.session import SessionLocal
from sqlalchemy import select
from app.domains.fdv.models.compliance import Requirement
import uuid

DRY_RUN = "--dry-run" in sys.argv

NEW_REQUIREMENTS: list[dict] = [

    # ════════════════════════════════════════════════════════════════════════
    # RKL6 – Risikoklasse 6 (barnevernsinstitusjoner med overnattende beboere)
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "RKL6-RISIKOVURD-BRANN",
        "title": "Brannteknisk risikovurdering",
        "description": "Skriftlig brannteknisk risikovurdering av hele bygget, inkl. beboernes evakueringsevne og spesielle risikofaktorer. Skal oppdateres ved endringer i bygg eller drift. Ref: TEK17 §11-1, VTEK17.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "RKL6-BRANNØVELSE",
        "title": "Brannøvelse minimum 2 ganger per år",
        "description": "Praktisk brannøvelse / evakueringsøvelse for alle ansatte og beboere minimum 2 ganger per år. Øvelsene skal dokumenteres med dato, deltakere og evaluering. Ref: Brannvernloven §7, FOBTOB.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "RKL6-RØYKDETEKTOR",
        "title": "Røykdetektorer i alle soverom og korridorer",
        "description": "Autonome røykdetektorer (eller tilknyttet ABA) i alle soverom og rømningsveier. Batteristatus sjekkes jevnlig. Ref: TEK17 §11-12, Brannvernloven §7.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "RKL6-BRANNSPJELD",
        "title": "Brannspjeld i ventilasjonsanlegg",
        "description": "Ventilasjonskanaler gjennom brannceller skal ha godkjente brannspjeld som hindrer røyk- og brannspredning. Spjeldene skal kontrolleres jevnlig. Ref: TEK17 §11-9, VTEK17.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "RKL6-RØMNINGSSKILT",
        "title": "Rømningsskilt og ledelys i alle rom og korridorer",
        "description": "Godkjente rømningsskilt (grønt symbol) over alle utganger og i rømningsveier. Ledelys skal vise vei til nærmeste nødutgang. Ref: TEK17 §11-13, NS-EN 1838.",
        "regulation_set": "RKL6", "category": "rømning", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "RKL6-BRANNTEKNISK-PROSJEKTERING",
        "title": "Brannteknisk prosjekteringsdokumentasjon",
        "description": "Komplett brannteknisk prosjekteringsdokumentasjon (brannstrategi, tegninger, produktdokumentasjon) oppbevart og tilgjengelig. Gjelder som-bygget. Ref: SAK10 §12-1.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "RKL6-TILSTANDSRAPPORT-BRANN",
        "title": "Brannteknisk tilstandsrapport (hvert 5. år)",
        "description": "Ekstern brannteknisk tilstandsrapport fra godkjent foretak. Gir statusbilde på avvik fra krav og anbefaler tiltak. Anbefalt intervall: 5 år. Ref: GOF.",
        "regulation_set": "RKL6", "category": "brann", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "RKL6-ADGANGSKONTROLL",
        "title": "Adgangskontroll ved alle innganger",
        "description": "Godkjent adgangskontrollsystem på alle inngangsdører. Sikrer at beboere ikke forlater institusjonen uten tillatelse og at uvedkommende ikke slipper inn. Ref: BVL §5-9.",
        "regulation_set": "RKL6", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # BVL – Barnevernloven og tilhørende forskrifter
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "BVL-BEREDSKAPSPLAN",
        "title": "Beredskapsplan for kriser og hendelser",
        "description": "Skriftlig beredskapsplan for håndtering av kriser (rømning, vold, brann, psykisk helse). Planen skal være kjent for alle ansatte og revideres minst hvert annet år.",
        "regulation_set": "BVL", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "BVL-TVANGSLOGG",
        "title": "Registrering og rapportering av tvangsbruk",
        "description": "Alle tvangstiltak skal registreres i tvangsprotokoll og rapporteres til Statsforvalter. Ref: Rettighetsforskriften §26 og §27.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high",
        "source_url": "https://lovdata.no/dokument/SF/forskrift/2011-11-15-1103",
    },
    {
        "code": "BVL-KLAGEORDNING",
        "title": "Klageordning for beboere",
        "description": "Beboere skal ha lett tilgang til klageordning, inkl. informasjon om Statsforvalter som klageinstans. Informasjonen skal foreligge skriftlig. Ref: BVL §5-9, Rettighetsforskriften §6.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BVL-BRUKERMEDVIRKNING",
        "title": "Brukermedvirkning og beboerråd",
        "description": "Beboere skal ha reell medvirkning i hverdagen og ved utforming av tilbudet. Beboerråd eller tilsvarende fora skal gjennomføres jevnlig. Ref: Rettighetsforskriften §5.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BVL-PRIVATLIV-VERDIER",
        "title": "Sikring av beboers privatliv og personlige eiendeler",
        "description": "Beboer skal ha mulighet til å oppbevare personlige eiendeler forsvarlig og låst. Personvern ivaretas ved at uvedkommende ikke har tilgang til beboers rom uten samtykke. Ref: BVL §5-9.",
        "regulation_set": "BVL", "category": "privatliv", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BVL-HELSETILGANG",
        "title": "Tilgang til helsetjenester og legetilgang",
        "description": "Institusjonen skal sikre at beboere har tilgang til nødvendige helsetjenester, inkl. fastlege, tannlege og psykolog. Rutiner for helsehjelp skal foreligge. Ref: BVL §5-9, Rettighetsforskriften §13.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "BVL-SKOLEGANG",
        "title": "Tilgang til skolegang og leksehjelp",
        "description": "Beboere i skolepliktig alder skal ha tilgang til tilpasset opplæring. Institusjonen tilrettelegger for skolegang og leksehjelp. Ref: Opplæringsloven, Rettighetsforskriften §14.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "BVL-EGENEVALUERING",
        "title": "Egenevaluering av institusjonens kvalitet (2x/år)",
        "description": "Institusjonen skal gjennomføre intern egenevaluering av kvalitet og faglig innhold minimum to ganger per år. Resultater dokumenteres og følges opp. Ref: Krav om kvalitetsarbeid.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BVL-HANDLINGSPLAN",
        "title": "Handlingsplan for kvalitetsutvikling",
        "description": "Skriftlig handlingsplan med mål og tiltak for faglig og bygningsmessig kvalitetsutvikling. Revideres årlig.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "BVL-KONTAKTINFORMASJON",
        "title": "Oppdatert kontaktinformasjon til alle nødfunksjoner",
        "description": "Oppslagstavle med oppdatert kontaktinformasjon: brann, ambulanse, politi, vakttelefon, Statsforvalter, ledelse. Synlig for alle ansatte og beboere.",
        "regulation_set": "BVL", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BVL-INTERNETT-DIGITAL",
        "title": "Tilgang til internett og digitale tjenester for beboere",
        "description": "Beboere skal ha tilgang til internett for skole, fritid og kontakt med pårørende. Bruken reguleres av husordensregler. Ref: Rettighetsforskriften §12.",
        "regulation_set": "BVL", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "low", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # KVALITETSFORSKRIFTEN (Utdypet)
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "KVAL-KJØKKEN",
        "title": "Tilgang til kjøkken for beboere",
        "description": "Beboere skal ha tilgang til kjøkken eller kjøkkenfasiliteter for å lage enkle måltider. Fellesskjøkken skal være tilpasset antall beboere. Ref: Kvalitetsforskriften §6.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "KVAL-VASKEROM",
        "title": "Tilgang til vaskerom og tørkerom",
        "description": "Beboere skal ha tilgang til vaskemaskin og tørketrommel/tørkerom. Kapasitet tilpasset antall beboere. Ref: Kvalitetsforskriften §6.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "KVAL-TOALETT-DUSJ",
        "title": "Eget toalett og dusj per beboer (eller delt mellom 2)",
        "description": "Hvert beboerrom skal ha tilgang til eget toalett og dusj, evt. delt mellom maksimalt 2 beboere. Ref: Kvalitetsforskriften §6, Rundskriv Q-19/2012.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "hygiene", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "KVAL-LAGERLASS-ROM",
        "title": "Låsbart oppbevaringsrom for beboers eiendeler",
        "description": "Hvert beboerrom skal ha tilgang til låsbart oppbevaringsrom eller innebygd garderobe for å sikre personlige eiendeler. Ref: Kvalitetsforskriften §6.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "KVAL-AKTIVITETSROM",
        "title": "Aktivitets- og fritidsrom for beboere",
        "description": "Institusjonen skal ha rom for fritidsaktiviteter (TV-stue, spillrom, treningsrom e.l.) tilpasset beboernes alder og behov. Ref: Kvalitetsforskriften §6.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "KVAL-TILPASNING-ALDER",
        "title": "Bygg og utstyr tilpasset beboernes alder",
        "description": "Bygg, møblering og utstyr skal tilpasses alder og funksjonsnivå. Barnesikring ved behov. Leker og aktivitetsutstyr for barn, ungdom tilpasset for eldre beboere. Ref: BVL §5-9.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "KVAL-ROM-STANDARD",
        "title": "Tilfredsstillende møblering og standard på beboerrom",
        "description": "Hvert beboerrom skal ha minimum: seng, skrivebord/pult, stol, garderobe/klesoppbevaring og god belysning. Møbler og utstyr i god stand. Ref: Kvalitetsforskriften §6.",
        "regulation_set": "KVALITETSFORSKRIFTEN", "category": "privatliv", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # TEK17 (Utdypet – Teknisk Forskrift 2017)
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "TEK17-FUKTSIKRING",
        "title": "Fuktsikring – bygningsdeler mot grunnen og vått rom",
        "description": "Bygningsdeler mot grunnen og våtrom skal være sikret mot fuktskader. Kontrolleres ved tegninger og visuell inspeksjon. Fuktskader skal utbedres umiddelbart. Ref: TEK17 §13-14.",
        "regulation_set": "TEK17", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "TEK17-STØY",
        "title": "Støynivå – innendørs lydforhold",
        "description": "Innendørs lydnivå (Rw og LpA,eq) skal være innenfor kravene i NS 8175 tilpasset bygningstype. Særlig viktig i sove- og hvilerom. Ref: TEK17 §13-6, NS 8175.",
        "regulation_set": "TEK17", "category": "inneklima", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "TEK17-DAGSLYS",
        "title": "Tilfredsstillende dagslys i oppholdsrom og soverom",
        "description": "Vindusflatens areal skal utgjøre minimum 10% av gulvarealet i oppholdsrom. Soverom skal ha tilstrekkelig dagslys og mulighet for mørklegging. Ref: TEK17 §13-7.",
        "regulation_set": "TEK17", "category": "inneklima", "applies_to": "section",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "TEK17-DRIKKEVANN",
        "title": "Tilfredsstillende drikkevannstilgang",
        "description": "Bygget skal ha tilgang til godkjent drikkevann i henhold til Drikkevannsforskriften. Vannkvalitet sjekkes ved tilkobling til kommunalt nett eller egen brønn. Ref: TEK17 §15-1.",
        "regulation_set": "TEK17", "category": "hygiene", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "TEK17-AVRENNING",
        "title": "Tilfredsstillende avrenning og overvannshåndtering",
        "description": "Tak- og overflatevann avrenning håndteres uten at det forårsaker skade på bygg eller naboforhold. Taknedløp og drenering i god stand. Ref: TEK17 §15-6.",
        "regulation_set": "TEK17", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "TEK17-BRANN-BÆRENDE",
        "title": "Bærende konstruksjoners brannmotstand",
        "description": "Bærende konstruksjoner (bjelker, søyler, dekker) skal ha brannmotstand som angitt i brannklasse (BKL2/BKL3 for RKL6). Ref: TEK17 §11-7, VTEK17.",
        "regulation_set": "TEK17", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "TEK17-SIKKERHETSGLASSRING",
        "title": "Glassflater sikret mot personskade",
        "description": "Glassflater i risikoposisjon (under 90 cm over gulv, dører, sideflater) skal være av sikkerhetsglass (herdet eller laminert). Ref: TEK17 §12-17, NS-EN 12600.",
        "regulation_set": "TEK17", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "TEK17-ROMTEMP",
        "title": "Romtemperatur 20°C ved dimensjonerende utetemperatur",
        "description": "Varmeanlegg skal sikre minimum 20°C innendørs ved dimensjonerende utetemperatur for stedet. Gjeldende for alle oppholdsrom. Ref: TEK17 §14-3.",
        "regulation_set": "TEK17", "category": "inneklima", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "TEK17-HEIS-KRAV",
        "title": "Heis eller rampe ved bygg med mer enn 2 etasjer",
        "description": "Bygg med beboelse i mer enn 2 etasjer som er åpent for allmennheten skal ha tilgjengelig heis eller rampeløsning til alle etasjer med beboere. Ref: TEK17 §12-3.",
        "regulation_set": "TEK17", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "TEK17-BRANNSLUSE",
        "title": "Brannsluse ved rømningsvei (RKL5/6)",
        "description": "Rømningsveier i bygg med risikoklasse 5 og 6 skal ha brannsluser der det er krevd. Brannslusene sikrer røykfri evakuering. Ref: TEK17 §11-14, VTEK17.",
        "regulation_set": "TEK17", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "TEK17-TRAPPESIKRING",
        "title": "Rekkverk og gelender ved trapper og balkonger",
        "description": "Trapper, ramper og balkonger skal ha rekkverk med høyde min. 90 cm (1,0 m over 10 m høyde). Geometri og åpninger skal hindre klatring for barn. Ref: TEK17 §12-16.",
        "regulation_set": "TEK17", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "TEK17-BEREDSKAPSLYS",
        "title": "Beredskapslys i fellesarealer og trapperom",
        "description": "Nødlys som sikrer minimum 1 lux i rømningsveier ved strømbrudd. Uavhengig strømforsyning (batteri minimum 1 time). Ref: TEK17 §11-13, NS-EN 1838.",
        "regulation_set": "TEK17", "category": "rømning", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # HMS – Arbeidsmiljøloven / Internkontrollforskriften (Utdypet)
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "HMS-FØRSTEHJELP",
        "title": "Godkjent førstehjelputstyr og opplæring",
        "description": "Tilstrekkelig og godkjent førstehjelputstyr (hjertestarter/AED anbefalt ved >50 pers.) og minimum én ansatt per vakt med førstehjelpsopplæring. Ref: AML §3-2, Forskrift om utførelse av arbeid §23.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "HMS-SKADEREGISTRERING",
        "title": "Registrering og rapportering av arbeidsulykker",
        "description": "Alle personskader og farlige hendelser på arbeidsplassen skal registreres. Alvorlige skader meldes Arbeidstilsynet. Ulykkesregister oppdateres løpende. Ref: AML §5-2, §5-4.",
        "regulation_set": "HMS", "category": "internkontroll", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high",
        "source_url": "https://lovdata.no/dokument/NL/lov/2005-06-17-62/KAPITTEL_5#KAPITTEL_5",
    },
    {
        "code": "HMS-KJEMIKALIER",
        "title": "Kjemikaliekartlegging og HMS-datablad",
        "description": "Alle kjemiske produkter i bruk (rengjøring, desinfeksjon, maling) skal kartlegges og HMS-datablad foreligger. Ansatte er opplært i bruk og håndtering. Ref: Kjemikalieforskriften, REACH.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "HMS-ERGONOMI",
        "title": "Ergonomisk tilrettelagte arbeidsplasser",
        "description": "Arbeidsplasser (kontorer, kjøkken, vaktrom) er ergonomisk utformet. Hev-/senkpulter og hjelpemidler ved behov. Kartlegges i risikovurderingen. Ref: AML §4-1, Arbeidsplassforskriften.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "HMS-PSYKOSOSIALT",
        "title": "Kartlegging av psykososialt arbeidsmiljø",
        "description": "Psykososialt arbeidsmiljø (vold, trusler, belastning) kartlegges jevnlig. Tiltak implementeres ved avvik. Særlig relevant for barneverninstitusjoner. Ref: AML §4-3, §4-6.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "HMS-VOLD-TRUSLER",
        "title": "Rutiner for håndtering av vold og trusler",
        "description": "Skriftlige rutiner for forebygging og håndtering av vold og trusler mot ansatte. Inkluderer sikring av rom, alarmknapper og oppfølging etter hendelser. Ref: AML §4-3, Vold-i-nære-relasjoner-forskriften.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "HMS-BEDRIFTSHELSETJENESTE",
        "title": "Tilknytning til godkjent bedriftshelsetjeneste",
        "description": "Virksomheter i bransjer med særlig risiko (inkl. sosial omsorg) skal ha godkjent BHT. BHT bistår ved vernerunder, AKAN og yrkessykdommer. Ref: AML §3-3, Forskrift om BHT.",
        "regulation_set": "HMS", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium",
        "source_url": "https://lovdata.no/dokument/SF/forskrift/2009-12-10-1396",
    },
    {
        "code": "HMS-AVFALLSHÅNDTERING",
        "title": "Forsvarlig avfallshåndtering – inkl. smittefarlig avfall",
        "description": "Avfall sorteres etter kommunale krav. Smittefarlig avfall (bandasjer, sprøyter) håndteres etter helseregler. Farlig avfall (batterier, lyspærer) leveres godkjent mottak. Ref: Avfallsforskriften.",
        "regulation_set": "HMS", "category": "miljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "HMS-VERNERUNDE",
        "title": "Systematisk vernerunde minimum 1 gang per år",
        "description": "Vernerunde med representanter fra ledelse, verneombud og evt. BHT gjennomføres minimum én gang per år. Avvik registreres og lukkes. Ref: Internkontrollforskriften §5, AML §6-2.",
        "regulation_set": "HMS", "category": "internkontroll", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "HMS-BRANNSERVICE",
        "title": "Serviceavtale for branntekniske anlegg",
        "description": "Godkjent serviceavtale for brannalarmanlegg, sprinkler og slokkeutstyr. Servicerapporter dokumenteres. Ref: NS 3910 (brannalarmanlegg), NS-EN 12845 (sprinkler).",
        "regulation_set": "HMS", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "HMS-VENTILASJONSSERVICE",
        "title": "Serviceavtale og filterskift for ventilasjonsanlegg",
        "description": "Ventilasjonsanlegg har løpende serviceavtale. Filtre skiftes etter leverandøranvisning (typisk 1-2 ganger/år). Aggregat rengjøres årlig. Ref: TEK17 §13-2, NS 3031.",
        "regulation_set": "HMS", "category": "inneklima", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # DRIFTSLEDELSE – Periodiske lovpålagte kontroller (Utdypet)
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "DL-BRANNSLUKKERE-KONTROLL",
        "title": "Håndholdte brannslukkere – kontroll hvert 5. år",
        "description": "Håndholdte brannslukkere kontrolleres av godkjent firma minst hvert 5. år, eller etter bruk. Servicebevis oppbevares. Ref: NS-EN 3, Brannvernloven §7.",
        "regulation_set": "DRIFTSLEDELSE", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-SPRINKLER-SERVICE",
        "title": "Sprinkleranlegg – full kontroll hvert 2. år",
        "description": "Sprinkleranlegg kontrolleres av godkjent firma etter NS-EN 12845. Halvårlig og 2-årig kontroll. Alle avvik utbedres umiddelbart. Servicerapport oppbevares.",
        "regulation_set": "DRIFTSLEDELSE", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "DL-BRANNALARM-SERVICE",
        "title": "Automatisk brannalarmanlegg – årlig service",
        "description": "ABA-anlegget servicekontrolleres av godkjent firma etter NS 3910 minst én gang per år. Alle detektorer og hoder testes. Servicerapport oppbevares.",
        "regulation_set": "DRIFTSLEDELSE", "category": "brann", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "DL-NØDLYS-TEST",
        "title": "Nødlysanlegg – månedlig test og 3-årig full test",
        "description": "Nødlysanlegg testes månedlig (korttest) og hvert 3. år (full 1-times utladestest). Defekte armaturer utskiftes umiddelbart. Ref: NS-EN 50172, NS-EN 1838.",
        "regulation_set": "DRIFTSLEDELSE", "category": "rømning", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-EL-TAVLE",
        "title": "El-tavle og sikringer – visuell kontroll hvert 5. år",
        "description": "Elektriske tavler (fordelingstavler, sikringstavler) kontrolleres av autorisert elinstallatør. Termografering anbefalt. Overstyrte sikringer og utdatert utstyr skiftes. Ref: FEL §9.",
        "regulation_set": "DRIFTSLEDELSE", "category": "el-sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-TAKTEKNING",
        "title": "Taktekning og taksluk – inspeksjon hvert 5. år",
        "description": "Taktekning, beslag, taksluk og rennekanter inspiseres for lekkasje og slitasje hvert 5. år. Funn dokumenteres og utbedres. Taknedløp renses for blader og rusk hvert år.",
        "regulation_set": "DRIFTSLEDELSE", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-FASADE-VINDUER",
        "title": "Fasade og vinduer – inspeksjon hvert 5. år",
        "description": "Fasadekledning, vinduer, dører og beslag inspiseres for råte, sprekker og dårlig tetting hvert 5. år. Maling og beis vedlikeholdes etter behov.",
        "regulation_set": "DRIFTSLEDELSE", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "DL-DRENSSYSTEM",
        "title": "Drenssystem og grunnvann – kontroll hvert 10. år",
        "description": "Drensrør, grøfter og fundamentdrenering rundt bygget inspiseres for tetting, setning og vanninntrenging. Kamera-inspeksjon av drensrør anbefalt. Ref: TEK17 §13-14.",
        "regulation_set": "DRIFTSLEDELSE", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-VARMEPUMPE-SERVICE",
        "title": "Varmepumpe(r) – serviceavtale og årlig kontroll",
        "description": "Varmepumper (luft-luft, luft-vann, bergvarme) servicekontrolleres av godkjent tekniker etter leverandørens anvisning, minimum hvert år. Kuldemedie sjekkes (F-gassforordningen).",
        "regulation_set": "DRIFTSLEDELSE", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "DL-UTEANLEGG",
        "title": "Uteanlegg og lekeapparater – årlig inspeksjon",
        "description": "Lekeapparater, benker, gjerder og utendørs overflater inspiseres og vedlikeholdes etter NS-EN 1176/1177. Farlig utstyr fjernes umiddelbart. Ref: Plan- og bygningsloven §29-5.",
        "regulation_set": "DRIFTSLEDELSE", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "DL-ÅRSRAPPORT-DRIFT",
        "title": "Årsrapport for drift og vedlikehold",
        "description": "Samlet årsrapport over gjennomførte vedlikeholdsaktiviteter, avvik og kostnader. Danner grunnlag for neste års vedlikeholdsplan og budsjett. Ref: NS 3600 / ISO 55000.",
        "regulation_set": "DRIFTSLEDELSE", "category": "drift", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "DL-LEGIONELLA-TEMPERATUR",
        "title": "Legionella – månedlig temperaturlogging varmtvann",
        "description": "Temperatur på varmtvannstank (≥60°C) og varmtvann i tappepunkter (≥50°C) logges månedlig. Avvik følges opp umiddelbart med spyling og temperaturhøyning. Ref: FHI-veileder legionella.",
        "regulation_set": "DRIFTSLEDELSE", "category": "hygiene", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },
    {
        "code": "DL-INNEMILJOE-MAALING",
        "title": "Inneklimaparametre – CO₂, temperatur og fukt kontrollert",
        "description": "CO₂-innhold, lufttemperatur og relativ luftfuktighet i oppholds- og soverom kontrolleres jevnlig. Avvik fra anbefalt nivå dokumenteres og følges opp. Ref: TEK17 §13-1.",
        "regulation_set": "DRIFTSLEDELSE", "category": "inneklima", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # ENØK – Energieffektivitet og ENOVA-krav
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "ENOK-ENERGIOPPFOLGING",
        "title": "Energioppfølging og -rapportering (EOS)",
        "description": "Energiforbruk (kWh) registreres og rapporteres månedlig. Sammenlignes mot normtall og historikk. Avvik over 10% analyseres og tiltak iverksettes. Ref: Energilovforskriften, ENOVA-krav for statlige virksomheter.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": "https://www.enova.no/",
    },
    {
        "code": "ENOK-BELYSNING",
        "title": "Energieffektiv belysning (LED eller tilsvarende)",
        "description": "Alle lysarmaturer bør være LED eller annen høyeffektiv belysning. Bevegelsessensorer i trapperom, lager og fellesarealer. Ref: Energieffektiviseringsdirektivet (EED), ENOVA.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "ENOK-ISOLERING",
        "title": "Tilfredsstillende isolering – tak, vegger og gulv",
        "description": "Bygningskroppen er godt isolert og tett. U-verdier for yttervegg, tak og gulv dokumentert. Vesentlige kuldebroer er tettet. Ref: TEK17 §14-2, NS 3700.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "ENOK-VINDUER-U-VERDI",
        "title": "Vinduer med god isolasjonsevne (U-verdi ≤1,2 W/m²K)",
        "description": "Vinduer og ytterdører har U-verdi ≤1,2 W/m²K for å redusere varmetap. Eldre enkeltglass skiftes. Ref: TEK17 §14-3, Norsk Enova-støtte for vindusbytte.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "ENOK-VARMEGJENVINNING",
        "title": "Varmegjenvinning fra ventilasjonsanlegg (≥80% temperaturvirkningsgrad)",
        "description": "Balansert ventilasjon med roterende varmeveksler eller kryssstrøms-veksler med temperaturvirkningsgrad ≥80%. Tilstandskontrolleres jevnlig. Ref: TEK17 §14-3 (energirammer).",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "ENOK-ENERGIKARTLEGGING",
        "title": "Energikartlegging av bygget (siste 5 år)",
        "description": "Helhetlig energikartlegging gjennomført av energirådgiver siste 5 år. Rapport med tiltak og lønnsomhetsberegning foreligger. Ref: EED art. 8 (foretak >250 pers.), ENOVA grunnstøtte.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "ENOK-STYRINGSANLEGG",
        "title": "SD-anlegg eller sentralt styringssystem for energi",
        "description": "Sentralt driftskontrollanlegg (SD) overvåker og styrer varme, ventilasjon og belysning. Driftsdata logges. Ref: ISO 50001, ENOVA støtte til SD-anlegg.",
        "regulation_set": "ENOK", "category": "energi", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # UNIVERSELL UTFORMING – Diskriminerings- og tilgjengelighetsloven
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "UU-INNGANGSPARTI",
        "title": "Tilgjengelig inngangsparti for alle brukere",
        "description": "Inngangsparti uten trinn (eller rampe med maks stigning 1:20). Bredde min. 90 cm. Automatisk dørfunksjon eller betjeningspanel i passende høyde. Ref: TEK17 §12-15, Diskriminerings- og tilgjengelighetsloven §17.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium",
        "source_url": "https://lovdata.no/dokument/NL/lov/2017-06-16-51",
    },
    {
        "code": "UU-HC-TOALETT",
        "title": "HC-tilpasset toalett tilgjengelig i bygget",
        "description": "Minst ett HC-toalett i byggets plan tilgjengelig for rullestolbrukere. Dimensjoner, vendeareal og klosettmontering etter NS 11001-1. Ref: TEK17 §12-9.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "UU-RAMPE-HEIS",
        "title": "Rampe eller heis ved nivåforskjeller innendørs",
        "description": "Alle etasjer i bygg som er åpent for allmennheten eller beboere er tilgjengelige via rampe (maks 1:20) eller heis. Ref: TEK17 §12-3, §12-15.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "UU-DORBREDDE",
        "title": "Dørbredde minimum 80 cm (klarvidde 86 cm) i fellesarealer",
        "description": "Alle dører i felles rømningsveier og fellesarealer har klarvidde min. 80 cm (dørblad min. 86 cm). Rullestolvennlig. Ref: TEK17 §12-14, NS 3926.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "UU-SKILTING",
        "title": "God merking og skilting – synlig og lesbar",
        "description": "Rominformasjon og retningsskilt i god kontrast og lesbar skriftstørrelse. Punktskrift på viktige steder. Ref: TEK17 §12-3, NS 11001-1.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "UU-HC-PARKERING",
        "title": "HC-parkeringsplasser etter krav (2% eller min. 1 plass)",
        "description": "Minst 2% av parkeringsplasser (minimum 1) er merket og reservert for HC. Plassert nær inngang. Ref: TEK17 §8-7, NS 3920.",
        "regulation_set": "UU", "category": "tilgjengelighet", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "low", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # SIKKERHET – Adgangskontroll, GDPR, Beredskap
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "SIKK-NØKKELFORVALTNING",
        "title": "Systematisk nøkkel- og adgangsbevisforvaltning",
        "description": "Nøkler og adgangskort er registrert i nøkkelregister med oversikt over hvem som har hva. Tapte nøkler håndteres med umiddelbar sperring eller sylinderbytte. Ref: Internkontrollforskriften.",
        "regulation_set": "SIKKERHET", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "SIKK-GDPR-PERSONVERN",
        "title": "GDPR – personvernrutiner for beboeres data",
        "description": "Rutiner for behandling av beboerdata (navn, historikk, helse) i samsvar med GDPR. Personvernombud utpekt for Bufetat. Databehandleravtaler med systemer foreligger. Ref: GDPR art. 6, 9.",
        "regulation_set": "SIKKERHET", "category": "internkontroll", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high",
        "source_url": "https://lovdata.no/dokument/NL/lov/2018-06-15-38",
    },
    {
        "code": "SIKK-KAMERAOVERVÅKING",
        "title": "Kameraovervåkning – lovlig bruk og informert samtykke",
        "description": "Eventuelle kameraer er lovlig installert med hjemmel i GDPR art. 6 / Personopplysningsloven. Informasjonsplikt oppfylt. Opptak slettes etter maks 30 dager. Ref: POL §12, Datatilsynets retningslinjer.",
        "regulation_set": "SIKKERHET", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "SIKK-BEBOER-EIENDELER",
        "title": "Rutiner for håndtering av beboers personlige verdier og ID",
        "description": "Skriftlige rutiner for mottak, oppbevaring og utlevering av beboers penger, verdisaker og ID-papirer. Kvitteringsordning og regnskapsmessig sporbarhet. Ref: Rettighetsforskriften §8.",
        "regulation_set": "SIKKERHET", "category": "sikkerhet", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "SIKK-VOLDSALARM",
        "title": "Personlig alarmknapp/voldsalarm for ansatte",
        "description": "Ansatte har tilgang til personlige alarmknapper eller voldsalarm. Alarmer kobles til vaktsentral eller mobiltelefon. Testes månedlig. Ref: AML §4-3, Arbeidstilsynets veileder.",
        "regulation_set": "SIKKERHET", "category": "arbeidsmiljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "critical", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # MILJØ – Miljøsanering og farlige stoffer
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "MILJO-ASBEST",
        "title": "Asbestkartlegging – bygg oppført før 1985",
        "description": "Bygg oppført eller rehabilitert før 1985 skal ha kartlegging av asbest. Kartleggingen dokumenterer lokalisering og mengde. Asbestholdige materialer håndteres av godkjent firma. Ref: Asbest-forskriften.",
        "regulation_set": "MILJØ", "category": "miljø", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "critical",
        "source_url": "https://lovdata.no/dokument/SF/forskrift/2012-06-06-622",
    },
    {
        "code": "MILJO-PCB",
        "title": "PCB-kartlegging – bygg fra 1956–1980",
        "description": "Bygg oppført mellom 1956 og 1980 skal kartlegges for PCB i fugemasser, maling og isolerglassruter. PCB-holdige materialer saneres etter Forurensingsloven. Ref: PCB-forskriften §9.",
        "regulation_set": "MILJØ", "category": "miljø", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "critical",
        "source_url": "https://lovdata.no/dokument/SF/forskrift/2001-10-26-1130",
    },
    {
        "code": "MILJO-BLYMALNG",
        "title": "Blyholdig maling kartlagt i eldre bygg",
        "description": "Bygg oppført før 1980 kan ha blyholdig maling. Kartlegging gjennomføres ved rehabilitering eller ved synlig forfall. Sanering utføres av godkjent firma. Ref: Produktforskriften, SHA-plan.",
        "regulation_set": "MILJØ", "category": "miljø", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "high", "source_url": None,
    },
    {
        "code": "MILJO-FARLIG-AVFALL",
        "title": "Farlig avfall levert til godkjent mottak",
        "description": "Farlig avfall (maling, kjemikalier, lysstoffrør, batterier, elektronikk) leveres til godkjent mottak. Kvitteringer oppbevares. Ref: Avfallsforskriften kap. 11.",
        "regulation_set": "MILJØ", "category": "miljø", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },

    # ════════════════════════════════════════════════════════════════════════
    # BYGG / NS 3451 – Tilstand og vedlikehold
    # ════════════════════════════════════════════════════════════════════════
    {
        "code": "BYGG-TILSTANDSANALYSE",
        "title": "Tilstandsanalyse (NS 3600) gjennomført siste 5 år",
        "description": "Helhetlig tilstandsanalyse etter NS 3600 gjennomført av takstmann eller bygningsingeniør siste 5 år. Tilstandsgrader TG0–TG3 per bygningsdel. Rapport foreligger og er tilgjengelig. Ref: NS 3600, NS 3424.",
        "regulation_set": "BYGG", "category": "drift", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BYGG-VEDLIKEHOLDSPLAN",
        "title": "10-årig vedlikeholdsplan med kostestimat",
        "description": "Rullerende vedlikeholdsplan (minimum 10 år frem) med planlagte tiltak og kostestimat per år. Grunnlag for budsjettplanlegging. Planen revideres etter tilstandsanalyse. Ref: NS 3600, ISO 55001.",
        "regulation_set": "BYGG", "category": "drift", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BYGG-TEGNINGER",
        "title": "Oppdaterte tegninger og arealoppmålinger",
        "description": "Som-bygget-tegninger (plantegninger, snitt, fasader) og oppdatert arealoppmåling (BRA, GUA per etasje) foreligger og er tilgjengelig. Ref: Plan- og bygningsloven §31-3, NS 3940.",
        "regulation_set": "BYGG", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "low", "source_url": None,
    },
    {
        "code": "BYGG-FDV-DOKUMENTASJON",
        "title": "FDV-dokumentasjon – brukermanualer og driftsanvisninger",
        "description": "Komplett FDV-dokumentasjon foreligger: brukermanualer, drifts- og vedlikeholdsanvisninger, produktdatablad og garantidokumenter for tekniske installasjoner. Ref: SAK10 §12-1, NS 3451.",
        "regulation_set": "BYGG", "category": "drift", "applies_to": "property",
        "is_mandatory": True, "severity_if_breached": "medium", "source_url": None,
    },
    {
        "code": "BYGG-GRUNN-DRENS",
        "title": "Fundamentering og drens – kontrollert og dokumentert",
        "description": "Fundamentering og dreneringsforhold rundt bygget er kontrollert og dokumentert. Setningskader, sprekkdannelser eller fuktinntrenging er kartlagt. Ref: TEK17 §13-14, NS 3420.",
        "regulation_set": "BYGG", "category": "konstruksjon", "applies_to": "property",
        "is_mandatory": False, "severity_if_breached": "high", "source_url": None,
    },
]


async def main() -> None:
    async with SessionLocal() as db:
        existing = await db.execute(select(Requirement.code))
        existing_codes = {row[0] for row in existing.fetchall()}

        new_count = 0
        skip_count = 0

        for r in NEW_REQUIREMENTS:
            if r["code"] in existing_codes:
                skip_count += 1
                continue

            req = Requirement(requirement_id=uuid.uuid4(), **r)
            db.add(req)
            new_count += 1
            print(f"  [NY]  {r['code']:40s} {r['title'][:55]}")

        print(f"\nSammendrag:")
        print(f"  Nye krav lagt til:  {new_count}")
        print(f"  Allerede i DB:      {skip_count}")
        print(f"  Totalt i katalogen: {len(existing_codes) + new_count}")

        if DRY_RUN:
            print("\n[DRY RUN] Ingen endringer lagret.")
            await db.rollback()
        else:
            await db.commit()
            print(f"\n✅ {new_count} krav lagt til i requirements-tabellen.")


asyncio.run(main())
