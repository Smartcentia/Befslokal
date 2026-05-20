import Link from "next/link";
import { ArrowLeft, BookOpen, ExternalLink, Table2 } from "lucide-react";

export const metadata = {
    title: "Utdanning og gjennomføring – kilder og metode | BEFS",
    description:
        "Utdanning, NEET/UVAS, ytelsesnivåer Norge–Sverige, samfunnsøkonomisk tap og tabellskisse.",
};

export default function SsbUtdanningMetodePage() {
    return (
        <div className="min-h-screen bg-background text-foreground">
            <div className="max-w-3xl mx-auto px-6 pt-28 pb-16 space-y-10">
                <div>
                    <Link
                        href="/ssb"
                        className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline mb-6"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Tilbake til SSB Statistikk
                    </Link>
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-primary/15 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                            <BookOpen size={24} />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">
                                Utdanning og gjennomføring
                            </h1>
                            <p className="text-muted mt-2 text-lg leading-relaxed">
                                Dypdykk: hvilke data du henter hvor, og hvordan du vasker metoden
                                slik at tall kan stå ved siden av hverandre uten å sammenligne epler
                                med pærer.
                            </p>
                        </div>
                    </div>
                </div>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">1. Datakilder: hva henter vi hvor?</h2>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
                        Norge (SSB og Bufdir)
                    </h3>
                    <p className="text-sm text-muted leading-relaxed">
                        I Norge finnes koblingsstatistikk som følger personer fra barnevernstiltak mot
                        utdanningsnivå. Bruk alltid tabellens fotnoter for eksakt populasjon og år.
                    </p>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Hovedkilde:</strong>{" "}
                            <a
                                href="https://www.ssb.no/statbank/table/13350/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                SSB tabell 13350
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>
                            — personer 18–25 år etter barnevernserfaring og utdanningsnivå (sjekk
                            siste årgang i Statistikkbanken).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Se særlig etter:</strong>{" "}
                            dimensjoner for fullført videregående nivå og segmentering på type
                            tiltak (hjelpetiltak i hjemmet versus plassering/omsorgstiltak).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Tillegg:</strong> tabell{" "}
                            <a
                                href="https://www.ssb.no/statbank/table/13346/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                13346
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>{" "}
                            der den er relevant for samme tema.
                        </li>
                    </ul>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        Sverige (Socialstyrelsen og Kolada)
                    </h3>
                    <p className="text-sm text-muted leading-relaxed">
                        Sverige rapporterer mye på samhällsvård; indikatorer og begreper er ikke 1:1
                        med norske tabeller.
                    </p>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Hovedkilde:</strong>{" "}
                            <a
                                href="https://www.socialstyrelsen.se/statistik-och-data/oppna-jamforelser/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                Socialstyrelsen – öppna jämförelser (åpne sammenligninger)
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>
                            , og søk derfra i statistikkdatabasen etter publikasjoner om
                            socialtjänst for barn och unga samt skoleresultat for barn i
                            samhällsvård (eksakte undersider endres; verifiser alltid år og definisjon).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Kolada:</strong>{" "}
                            <a
                                href="https://kolada.se"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                kolada.se
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>
                            — søk etter indikator{" "}
                            <code className="text-xs bg-muted px-1 rounded">U07405</code> (andel
                            elever med plasseringserfaring som oppnådd behörighet til yrkesprogram)
                            og verifiser definisjon og år før bruk.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Viktig nyanse:</strong>{" "}
                            Sverige vektlegger ofte «behörighet» (kvalifikasjon til neste nivå)
                            fremfor kun «fullført» som i mange norske tabeller. Dokumenter dette i
                            metodenotatet.
                        </li>
                    </ul>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">
                        2. Tekniske definisjoner (unngå statistisk støy)
                    </h2>
                    <p className="text-sm text-muted leading-relaxed">
                        Landene teller ikke det samme. Under er spesifikasjonene du bør holde deg til når
                        norske og svenske tall skal stå i samme rapport.
                    </p>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
                        Norge: «Fullført og bestått» (SSB / Udir)
                    </h3>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Definisjon:</strong> Fullført når
                            eleven har oppnådd <strong className="text-foreground font-medium">vitnemål</strong>{" "}
                            (studiekompetanse) eller <strong className="text-foreground font-medium">fag-/svennebrev</strong>{" "}
                            (yrkeskompetanse).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Gjennomføring i tid:</strong> SSB
                            opererer mye med fullføring innen{" "}
                            <strong className="text-foreground font-medium">5 år</strong> (studieforberedende)
                            eller <strong className="text-foreground font-medium">6 år</strong> (yrkesfag) etter
                            påbegynt V1 — sjekk alltid fotnote i aktuell tabell.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Tabell 13350:</strong> Status måles
                            ved <strong className="text-foreground font-medium">25 års alder</strong>. Det
                            fanger barn som trenger lengre løp etter barnevern og livshendelser.
                        </li>
                    </ul>
                    <p className="text-sm text-muted leading-relaxed rounded-lg border border-border bg-muted/20 px-4 py-3 font-mono text-xs sm:text-sm">
                        Gjennomføringsgrad (%) = (antall fullførte og bestått / opprinnelig elevkull N) × 100
                    </p>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        Sverige: gymnasieexamen (Skolverket / Socialstyrelsen)
                    </h3>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Gy11:</strong> Reformen gjør
                            sammenligning med eldre årganger vanskelig — dokumenter år og definisjon.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Examen:</strong> Minst 2500 poeng,
                            hvorav 2250 godkjente. To hovedtyper:{" "}
                            <em>högskoleförberedande examen</em> (bl.a. godkjent svensk, engelsk, matematikk) og{" "}
                            <em>yrkesexamen</em> (samme kjernefag + 400 poeng i programfag).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Genomströmning:</strong> Ofte
                            rapportert etter <strong className="text-foreground font-medium">3 år</strong>{" "}
                            (normaltid) og <strong className="text-foreground font-medium">4 år</strong>.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Behörighet vs examen:</strong> Mange
                            rapporter for barn i samhällsvård vektlegger behörighet (kvalifisert til neste steg),
                            ikke nødvendigvis fullført løp — det er ofte en{" "}
                            <strong className="text-foreground font-medium">lavere terskel</strong> enn norsk
                            «fullført og bestått».
                        </li>
                    </ul>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        Den tekniske «broen» (mapping)
                    </h3>
                    <div className="rounded-xl border border-border overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30 text-left">
                                    <th className="p-3 font-semibold text-foreground">Parameter</th>
                                    <th className="p-3 font-semibold text-foreground">Norsk verdi (SSB)</th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Svensk verdi (SCB / Socialstyrelsen)
                                    </th>
                                    <th className="p-3 font-semibold text-foreground">Teknisk merknad</th>
                                </tr>
                            </thead>
                            <tbody className="text-muted">
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Fullført nivå</td>
                                    <td className="p-3">Vitnemål / fagbrev</td>
                                    <td className="p-3">Gymnasieexamen</td>
                                    <td className="p-3">
                                        Ikke bruk svensk «studiebevis» som synonym for norsk fullført VGO.
                                    </td>
                                </tr>
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Populasjon</td>
                                    <td className="p-3">Barn med tiltak før 18 år</td>
                                    <td className="p-3">Barn med socialtjänstinsatser</td>
                                    <td className="p-3">
                                        Avklar om kilden inkluderer öppenvård eller kun placerade.
                                    </td>
                                </tr>
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Tidshorisont</td>
                                    <td className="p-3">5–7 år etter start (ofte målt mot 25 år i 13350)</td>
                                    <td className="p-3">3–4 år etter start (genomströmning)</td>
                                    <td className="p-3">
                                        Norge kan vise «senere» suksess; sammenlign ikke ukritisk kort svensk løp med norsk 25-årsmåling.
                                    </td>
                                </tr>
                                <tr>
                                    <td className="p-3 text-foreground font-medium">Yrkesfag</td>
                                    <td className="p-3">2+2 (skole + lære)</td>
                                    <td className="p-3">Treårig skolemodell</td>
                                    <td className="p-3">Norsk modell bruker ofte ett år mer i normaltid.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <p className="text-sm text-muted leading-relaxed border-l-2 border-primary/40 pl-4">
                        <strong className="text-foreground font-medium">Anbefalt fellesnevner:</strong> Be om
                        eller trekk ut data på{" "}
                        <strong className="text-foreground font-medium">
                            oppnådd studie- eller yrkeskompetanse innen fylte 25 år
                        </strong>
                        . Dette gir det mest sammenlignbare grunnlaget mellom systemene og reflekterer
                        ettervern og lengre løp.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">
                        3. Metodisk sammenstilling (epler mot pærer-sjekken)
                    </h2>
                    <p className="text-sm text-muted leading-relaxed">
                        Fyll ut kolonnen «Slik jeg bruker det» når du legger tall inn i en rapport —
                        da kan leseren se hvor sammenligningen er ren og hvor den er tentativ.
                    </p>
                    <div className="rounded-xl border border-border overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30 text-left">
                                    <th className="p-3 font-semibold text-foreground">Variabel</th>
                                    <th className="p-3 font-semibold text-foreground">Norge (VGO)</th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Sverige (gymnasium)
                                    </th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Risiko ved sammenligning
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="text-muted">
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Normaltid</td>
                                    <td className="p-3">
                                        Typisk 3 år studieforløp; fagbrev/læring kan ta lengre tid.
                                    </td>
                                    <td className="p-3">Ofte tre års gymnasium.</td>
                                    <td className="p-3">
                                        Norge har mer lærlingløp — tidsbruk og «fullført» må leses
                                        sammen med definisjon.
                                    </td>
                                </tr>
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Målepunkt</td>
                                    <td className="p-3">
                                        Gjennomføring innen definerte år i tabell (f.eks. 5/6 år der
                                        kilden angir det).
                                    </td>
                                    <td className="p-3">
                                        Ofte knyttet til alder (f.eks. ved 20 år) i svenske kilder.
                                    </td>
                                    <td className="p-3">
                                        «Fullført» i Norge og «behörighet» i Sverige er ikke
                                        identiske.
                                    </td>
                                </tr>
                                <tr>
                                    <td className="p-3 text-foreground font-medium">Populasjon</td>
                                    <td className="p-3">
                                        Alle med registrert tiltak før 18 (etter tabellens fotnote).
                                    </td>
                                    <td className="p-3">
                                        Ofte utvalg med tyngde på plassering (HVB/familjehem) i
                                        enkelte serier.
                                    </td>
                                    <td className="p-3">
                                        Sammenligning av «alle med tiltak» i Norge mot «kun
                                        plasserte» i Sverige gir skjeve konklusjoner.
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">4. Praktisk arbeidsflyt (med BEFS)</h2>
                    <ol className="text-sm text-muted space-y-3 list-decimal pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Lokale tall:</strong> der
                            dere har lovlig grunnlag og rutiner, dokumenter andel som fullfører VGO
                            (eller avtalt mål) i egen region/kommune — utenfor BEFS om
                            persondata ikke ligger i systemet.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Benchmark mot SSB:</strong>{" "}
                            bruk tabell 13350 (og ev. 13346) for å se om geografien ligger over eller
                            under landssnitt for relevant populasjon.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Speil mot Sverige:</strong>{" "}
                            bruk svenske kilder/Kolada som orientering — med eksplisitt fotnote om
                            definisjon og år.
                        </li>
                    </ol>
                    <p className="text-sm text-muted leading-relaxed border-l-2 border-primary/40 pl-4">
                        <strong className="text-foreground font-medium">Ettervern:</strong> I nyere
                        år er tiltak etter fylte 18 år sentralt. Sjekk om kildene skiller ettervern —
                        det påvirker om «norske» tall inkluderer lengre løp enn enkelte svenske
                        utvalg der unge «skrives ut» av statistikken ved bestemte aldre.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">5. Hva du bør se etter i 2026-tallene</h2>
                    <ol className="text-sm text-muted space-y-3 list-decimal pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Ettervernseffekten:</strong> Lovfestet
                            tilbud om ettervern til 25 år i Norge — undersøk om fullført VGO korrelerer med
                            varighet eller omfang av ettervern i tilgjengelige kilder.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Studievägar:</strong> I Sverige havner
                            mange i <em>introduktionsprogram</em> når behörighet mangler; i Norge ligger
                            tilsvarende ofte i forberedende løp eller kombinasjonsklasser. Tall for disse sporene
                            viser ofte dem som risikerer å falle utenfor — ikke bland dem umerket med
                            ordinært program.
                        </li>
                    </ol>
                    <p className="text-sm text-muted leading-relaxed">
                        <strong className="text-foreground font-medium">Videre kobling:</strong> Se{" "}
                        <strong className="text-foreground font-medium">avsnitt 6</strong> for hvordan utdanning
                        kobles til inntekt, NEET/UVAS og varige ytelser uten å blande definisjoner.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold">
                        6. Utenforskap og økonomiske konsekvenser (2026)
                    </h2>
                    <p className="text-sm text-muted leading-relaxed">
                        Når utdanningsløpet brytes, følger ofte <strong className="text-foreground font-medium">varig utenforskap</strong>. For presise sammenligninger må utdanningsdata kobles mot inntekts- og ytelsesstatistikk med eksplisitte definisjoner.
                    </p>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
                        6.1 Utenforskap (NEET / UVAS)
                    </h3>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">NEET</strong> (Not in Education,
                            Employment, or Training): Før varig ytelse havner mange her.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Norge (SSB):</strong> Personer 15–29 år
                            utenfor arbeid, utdanning og arbeidsmarkedstiltak. I Statistikkbanken vises ofte eldre
                            tabellnumre (f.eks.{" "}
                            <a
                                href="https://www.ssb.no/statbank/table/12411/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                12411
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>
                            ); i PxWeb API finnes blant annet{" "}
                            <strong className="text-foreground font-medium">12423</strong> og kommunefordelt{" "}
                            <strong className="text-foreground font-medium">13556</strong> (15–29 år, NEET). I BEFS:
                            åpne{" "}
                            <Link
                                href="/ssb?category=utenforskap"
                                className="text-primary underline underline-offset-2 font-medium"
                            >
                                SSB med filter «Utenforskap / NEET»
                            </Link>
                            . Verifiser alltid år og fotnote.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Sverige:</strong> Begrepet{" "}
                            <strong className="text-foreground font-medium">UVAS</strong> (unga som varken arbetar
                            eller studerar). Kilder inkluderer{" "}
                            <a
                                href="https://www.scb.se/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                                title="Søk etter relevant statistikkdatabas og publikasjoner"
                            >
                                SCB
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>{" "}
                            og{" "}
                            <a
                                href="https://www.mucf.se/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary underline underline-offset-2 inline-flex items-center gap-1"
                            >
                                MUCF
                                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                            </a>{" "}
                            (Myndigheten för ungdoms- och civilsamhällesfrågor).
                        </li>
                    </ul>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        6.2 Varige ytelser: uføretrygd og svenske paralleller
                    </h3>
                    <ul className="text-sm text-muted space-y-2 list-disc pl-5 leading-relaxed">
                        <li>
                            <strong className="text-foreground font-medium">Norge — uføretrygd:</strong> Krav om
                            varig inntektsevnesvikt (typisk minst 50 %) på grunn av sykdom eller skade. For unge:
                            vurder regelverket om <strong className="text-foreground font-medium">unge uføre</strong>{" "}
                            (alvorlig problematikk før fylte 26 år). NAV/SSB har statistikk knyttet til tidligere
                            barnevernstiltak — dokumenter alltid årgang og definisjon.
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Sverige — aktivitetsersättning:</strong>{" "}
                            Ytelse for unge (ofte 19–29) ved nedsatt arbeidsevne i minst ett år.{" "}
                            <strong className="text-foreground font-medium">Sjukersättning:</strong> nærmere varig
                            nivå (ofte fra 30 år, eller ved helt varig nedsatt evne).
                        </li>
                        <li>
                            <strong className="text-foreground font-medium">Nyanse:</strong> Strengere praksis for
                            unge i Sverige kan gi lavere «uføretall» samtidig som flere er på{" "}
                            <strong className="text-foreground font-medium">ekonomiskt bistånd</strong> (sosialhjelp).
                            Ikke les avvik som ren suksess uten denne konteksten.
                        </li>
                    </ul>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        6.3 Samfunnsøkonomisk tap (kostnad ved utestengelse)
                    </h3>
                    <p className="text-sm text-muted leading-relaxed">
                        Modeller sammenligner forventet skatteinngang med fullført VGO mot akkumulerte offentlige
                        kostnader (ytelser, tapt skattegrunnlag) over livsløp — ofte illustrert som nåverdi.
                    </p>
                    <p className="text-sm text-muted leading-relaxed rounded-lg border border-border bg-muted/20 px-4 py-3">
                        <span className="font-mono text-xs sm:text-sm block tracking-tight">
                            L = ∑<sub>t=18</sub>
                            <sup>67</sup> (S<sub>t</sub> + Y<sub>t</sub>) / (1 + r)<sup>t</sup>
                        </span>
                        <span className="block mt-2 text-xs font-sans text-muted">
                            S<sub>t</sub> = tapt skatteinntekt, Y<sub>t</sub> = utbetalt stønad, r = diskonteringsrente (sjekk metodenotatets forutsetninger).
                        </span>
                    </p>
                    <p className="text-sm text-muted leading-relaxed">
                        I 2026-kroner brukes ofte størrelsesorden <strong className="text-foreground font-medium">15–20 mill. kr</strong> som grovt anslag for samfunnsmessig tap når én ungdom faller varig utenfor — dette er modellavhengig og må ikke presenteres som enkeltobservasjon.
                    </p>

                    <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide pt-2">
                        6.4 Praktisk matrise (Norge ↔ Sverige)
                    </h3>
                    <div className="rounded-xl border border-border overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30 text-left">
                                    <th className="p-3 font-semibold text-foreground">Indikator</th>
                                    <th className="p-3 font-semibold text-foreground">Norge (SSB / NAV)</th>
                                    <th className="p-3 font-semibold text-foreground">Sverige (SCB / Socialstyrelsen)</th>
                                </tr>
                            </thead>
                            <tbody className="text-muted">
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Laveste nivå</td>
                                    <td className="p-3">Sosialhjelpsmottakere (f.eks. 18–25 år, etter kilde)</td>
                                    <td className="p-3">Ekonomiskt bistånd</td>
                                </tr>
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Mellomnivå</td>
                                    <td className="p-3">AAP (arbeidsavklaringspenger)</td>
                                    <td className="p-3">Aktivitetsersättning</td>
                                </tr>
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground font-medium">Varig nivå</td>
                                    <td className="p-3">Uføretrygd</td>
                                    <td className="p-3">Sjukersättning</td>
                                </tr>
                                <tr>
                                    <td className="p-3 text-foreground font-medium">Koble mot (arv)</td>
                                    <td className="p-3">SSB: foreldres utdanningsnivå (der tilgjengelig)</td>
                                    <td className="p-3">SCB: bakgrundsfaktorer (der tilgjengelig)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <p className="text-sm text-muted leading-relaxed border-l-2 border-primary/40 pl-4">
                        <strong className="text-foreground font-medium">Sosial arv:</strong> Sterk prediktor for utfall i begge land. God kartlegging viser om barnevernet bidrar til å bryte arven (barn bedre enn foreldre) eller primært forvalter utenforskap — krev eksplisitte definisjoner i bestilling av tabeller.
                    </p>
                    <p className="text-sm text-muted leading-relaxed">
                        <strong className="text-foreground font-medium">Neste steg:</strong> Et kort{" "}
                        <strong className="text-foreground font-medium">hypotesedokument</strong> (hvilket utfall, hvilken populasjon, hvilke SSB-/NAV-variabler og år) gjør det enklere å bestille eller trekke ut nøyaktige koblinger uten etterkorrigering.
                    </p>
                </section>

                <section className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Table2 className="h-6 w-6 text-primary shrink-0" />
                        7. Tabellskisse for beslutningstaker
                    </h2>
                    <p className="text-sm text-muted leading-relaxed">
                        Kopier strukturen til presentasjon eller notat. Tall fylles inn når analyse
                        er gjort; «Tekniske definisjoner» er minst like viktige som selve prosentene.
                    </p>
                    <div className="rounded-xl border border-border overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30 text-left">
                                    <th className="p-3 font-semibold text-foreground">Indikator</th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Ditt nivå (region/kommune)
                                    </th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Nasjonalt (SSB)
                                    </th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Referanse (Sverige / valgfritt)
                                    </th>
                                    <th className="p-3 font-semibold text-foreground">
                                        Metodekommentar
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="text-muted">
                                <tr className="border-b border-border/80">
                                    <td className="p-3 text-foreground">
                                        Fullført VGO (def. fra tabell)
                                    </td>
                                    <td className="p-3">…</td>
                                    <td className="p-3">…</td>
                                    <td className="p-3">…</td>
                                    <td className="p-3">År, populasjon, hjelpetiltak vs plassering</td>
                                </tr>
                                <tr>
                                    <td className="p-3 text-foreground">
                                        Ev. delmål (f.eks. behörighet)
                                    </td>
                                    <td className="p-3">…</td>
                                    <td className="p-3">—</td>
                                    <td className="p-3">…</td>
                                    <td className="p-3">Kun hvis sammenlignbar definisjon</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <section className="flex flex-wrap gap-3 pt-4">
                    <Link
                        href="/ssb?category=utdanning"
                        className="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                    >
                        Åpne SSB med filter utdanning
                    </Link>
                    <Link
                        href="/ssb?category=utenforskap"
                        className="inline-flex items-center justify-center rounded-xl border border-primary/40 bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary hover:bg-primary/15"
                    >
                        Åpne SSB med filter utenforskap / NEET
                    </Link>
                    <Link
                        href="/properties/anskaffelse"
                        className="inline-flex items-center justify-center rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted/40"
                    >
                        Anskaffelse og sjekkliste
                    </Link>
                </section>
            </div>
        </div>
    );
}
