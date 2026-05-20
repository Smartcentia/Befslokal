"use client";

import Accordion from "@/app/components/ui/Accordion";
import { HelpCircle } from "lucide-react";

type FaqItem = { q: string; a: string };

const SECTIONS: { title: string; items: FaqItem[] }[] = [
    {
        title: "Generelt",
        items: [
            {
                q: "Hva er KI Kollega?",
                a: "KI Kollega er assistenten i BEFS som svarer på vanlig norsk og bruker data fra systemet (eiendommer, kontrakter, økonomi m.m.). Den åpnes fra den blå knappen nede til høyre, eller fra fanen «Spør KI Kollega» på denne siden.",
            },
            {
                q: "Hvor finner jeg full dokumentasjon?",
                a: "Velg fanen «Dokumentasjon». Der ligger alle hovedemner fra brukerhjelpen (søkbar liste og kapitler). Innholdet hentes fra den sentrale kunnskapsbasen.",
            },
            {
                q: "Hvordan logger jeg inn, og hvem kontakter jeg ved problemer?",
                a: "Du logger inn med organisasjonens vanlige innlogging. Ved manglende tilgang: kontakt lokal IT eller superbruker. Ved feil: beskriv steg, side og gjerne skjermbilde.",
            },
            {
                q: "Hvor finner jeg personvern og tilgjengelighet?",
                a: "Under «Offentlig informasjon» på denne siden, eller via lenker i brukerhjelpen.",
            },
            {
                q: "Støtter BEFS mørk og lys visning?",
                a: "Ja. Bruk lys/mørk-ikonet i toppfeltet. Innholdet tilpasser seg valgt modus.",
            },
        ],
    },
    {
        title: "Regnskap og økonomi",
        items: [
            {
                q: "Hvor finner jeg økonomisk oversikt for porteføljen?",
                a: "Velg «Økonomi» i sidemenyen (sti /financials). Der finner du regional oversikt, leverandører, transaksjoner, mønstre, fakturaer, manglende kostnader, avviklet eiendom og mer – avhengig av hvilken fane du bruker.",
            },
            {
                q: "Hva er forskjellen mellom budsjett og regnskap (GL) i BEFS?",
                a: "Budsjett er planlagte beløp (f.eks. generert eller justert prognoser). Regnskap viser faktiske bokførte utgifter fra hovedboken (GL), typisk importert fra Agresso. Avviksanalyse sammenligner budsjett med regnskap per eiendom og periode.",
            },
            {
                q: "Hvor kommer regnskapstallene fra?",
                a: "GL-transaksjoner importeres fra Agresso (Unit4) og kobles til eiendom via koststed (Dim1) og mapping. Ufullstendig koststedkobling gir redusert sporbarhet – se SRS-rapport og dokumentasjon om koststed.",
            },
            {
                q: "Hva betyr «Avviklet eiendom» i datakvalitet?",
                a: "Fanen viser eiendommer som ikke er i budsjett for valgt år og samtidig ikke har GL-kostnader i året. Det betyr i praksis at eiendommen regnes som uten aktivitet for året, ikke bare uten budsjettlinjer.",
            },
            {
                q: "Hva er SRS-rapporten?",
                a: "SRS-rapporten (/financials/srs) viser hvordan data støtter Statlig regnskapsstandard: kategorisering (drift, investering, gjennomstrømning), koststeddekning, leie på relevante konti m.m. Den er særlig relevant for regnskap og revisjon.",
            },
            {
                q: "Hva er Prediksjon 2027?",
                a: "En prognose for hele porteføljen basert på historisk GL (typisk Holt-Winters). Du finner den under «Prediksjon 2027» i menyen, med interaktiv budsjettjustering og metodebeskrivelse. Tallene er scenariobaserte – verifiser mot faktisk behov og vedtak.",
            },
            {
                q: "Hva er avviksanalyse?",
                a: "Sammenligning av budsjett med regnskap for valgt eiendom, år og periode. Du ser avvik i kroner og prosent, ofte med graf. Krever at både budsjettdata og utgiftsdata finnes for eiendommen.",
            },
            {
                q: "Hva er forskjellen mellom Eiendomskostnader og Økonomi-siden?",
                a: "Økonomi-siden gir bred analyse og mange faner (leverandører, transaksjoner, kontraktsoversikt osv.). Eiendomskostnader (egen menypunkt) fokuserer på kostnadsvisning for et gitt år – se dokumentasjon for detaljer og begrensninger.",
            },
            {
                q: "Hva er anleggsregisteret?",
                a: "Oversikt over balanseførte anleggsmidler (investeringer over terskel, typisk 50 000 kr) med avskrivninger i tråd med SRS 17. Tilgjengelig under Økonomi → Anleggsregister.",
            },
            {
                q: "Hva betyr «syntetisk» budsjett eller estimat?",
                a: "Noen beløp er beregnet i systemet (f.eks. prediksjoner eller estimater) og ikke kun manuelt bokført. De er merket slik at du skiller dem fra ren faktisk historikk.",
            },
            {
                q: "Hva er Agresso CSV-lab?",
                a: "Et verktøy på /agresso-csv for å laste inn en CSV fra Agresso, se kolonner, SRS-kategorisering og mulige avvik før data importeres til BEFS. Nyttig for regnskap og kontroll.",
            },
            {
                q: "Hva er Kontroll 2027?",
                a: "Siden /kontroll-2027 samler outlier-analyse på GL-data, gjennomgang av prognose 2027 og en kort vurdering for intern kontroll – beregnet for regnskap, kontroll og ledelse.",
            },
            {
                q: "Hvor finner jeg SSB-statistikk sammen med BEFS?",
                a: "Gå til «SSB Statistikk» i menyen. Under fanen «Kombiner med BEFS» kan du samstille offisiell statistikk med egne data. KI Kollega kan også hjelpe med spørsmål om KPI og indekser.",
            },
            {
                q: "Hvordan leser jeg kostnader for én eiendom?",
                a: "Åpne eiendomsdetalj for valgt eiendom. Der finner du blant annet finansiell oversikt og kostnadsanalyse (forhold til husleie, kategorier). Krever at data er koblet til eiendommen (kontrakter, enheter, GL).",
            },
            {
                q: "Hva er rullerende prognoser?",
                a: "Under «Økonomi» finnes egne visninger for prognose basert på historisk forbruk. Du kan justere inflasjon og horisont – se dokumentasjon for forutsetninger og datakilder.",
            },
            {
                q: "Hva er forskjellen mellom GL per eiendom og «kostnader uten eiendom»?",
                a: "GL per eiendom viser kostnader som er koblet til en eiendom. «Kostnader uten eiendom» fanger poster som ikke er knyttet til eiendom i mapping – nyttig for å finne hull i koststed eller felleskostnader.",
            },
            {
                q: "Hvor ser jeg leverandørfordeling og fakturalinjer?",
                a: "På Økonomi-siden: fanene «Leverandører» og «Fakturaer» viser henholdsvis fordeling på leverandør og detaljerte bilagslinjer der data finnes.",
            },
            {
                q: "Hva er kontraktsoversikt (pivot)?",
                a: "En pivot-lignende tabell som kobler kontrakter til økonomiske tall – nyttig for å se leie og tillegg samlet. Åpnes fra fanen for kontraktsoversikt på Økonomi-siden.",
            },
            {
                q: "Hva er «mangler kostnader»?",
                a: "En oversikt over eiendommer eller forhold der systemet mangler kostnadsdata for valgt år, slik at du kan prioritere innhenting eller mapping.",
            },
            {
                q: "Kan KI Kollega svare på økonomispørsmål?",
                a: "Ja. Du kan f.eks. spørre om kostnader for en eiendom, sammenligne regioner eller be om forklaring på begreper. Svarene bygger på tilgjengelige data og kilder – verifiser viktige tall mot rapportene i Økonomi.",
            },
        ],
    },
    {
        title: "Eiendom, kontrakt og risiko",
        items: [
            {
                q: "Hvor finner jeg kontrakter og utløpsdatoer?",
                a: "Bruk «Kontrakter» i menyen eller gå fra eiendomsdetalj. Dashboard viser også varsler om kontrakter som nærmer seg utløp.",
            },
            {
                q: "Hva er risikobildet?",
                a: "En oversikt som sorterer eiendommer etter prioritet (risiko, kostnad, avvik m.m.). Tilgjengelig fra «Risikoanalyse» i menyen – se dokumentasjon for tolkning av indekser.",
            },
            {
                q: "Hva er ekstern risiko (NVE)?",
                a: "Systemet kan vise naturfare og tilknyttet informasjon basert på adresse (NVE). Brukes som supplement til intern risikovurdering.",
            },
        ],
    },
    {
        title: "HMS og internkontroll",
        items: [
            {
                q: "Hvor finner jeg sjekklister og avvik?",
                a: "«Sjekklister» og «Avvikshåndtering» ligger i sidemenyen. Du kan opprette saker fra maler, følge opp avvik og se kritiske saker fra dashboard.",
            },
            {
                q: "Hva er innboksen?",
                a: "«Innboks» samler varsler (f.eks. relatert til saker eller anomalier). Klikk på et varsel for å gå til riktig eiendom eller sak.",
            },
        ],
    },
];

export default function HelpFaq() {
    return (
        <div className="space-y-8">
            <div className="rounded-xl border border-border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
                <p className="flex items-start gap-2">
                    <HelpCircle className="w-5 h-5 shrink-0 text-primary mt-0.5" aria-hidden />
                    <span>
                        Korte svar på vanlige spørsmål – særlig om{" "}
                        <strong className="text-foreground">økonomi og regnskap</strong>. Mer detaljer finner du under{" "}
                        <strong className="text-foreground">Dokumentasjon</strong> eller ved å spørre{" "}
                        <strong className="text-foreground">KI Kollega</strong>.
                    </span>
                </p>
            </div>

            {SECTIONS.map((section) => (
                <section key={section.title} className="space-y-4">
                    <h2 className="text-lg font-semibold text-foreground border-b border-border pb-2">{section.title}</h2>
                    <div className="space-y-3">
                        {section.items.map((item) => (
                            <Accordion key={item.q} title={item.q} icon={<HelpCircle className="w-5 h-5" />}>
                                <p className="text-muted-foreground leading-relaxed px-2 pb-2">{item.a}</p>
                            </Accordion>
                        ))}
                    </div>
                </section>
            ))}
        </div>
    );
}
