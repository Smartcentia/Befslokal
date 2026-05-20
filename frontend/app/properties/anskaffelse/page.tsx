"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
    ListChecks,
    ExternalLink,
    Database,
    Baby,
    Building2,
    BookOpen,
} from "lucide-react";

const STORAGE_KEY = "befs_acquisition_checklist_v1";

type CheckItem = { id: string; label: string };

const CHECKLIST_SECTIONS: { title: string; items: CheckItem[] }[] = [
    {
        title: "Behov og statistikk (nasjonalt / regionalt)",
        items: [
            {
                id: "ssb-utdanning",
                label:
                    "Vurdert nasjonale tall for barnevern og utdanning (SSB, f.eks. tabell 13350 / 13346) som kontekst for målgruppe.",
            },
            {
                id: "ssb-tiltak",
                label:
                    "Sett på omfang og type tiltak (plassering vs. hjelpetiltak) – tabell 12845 og beslektet – som påvirker funksjonskrav.",
            },
            {
                id: "ssb-melding",
                label:
                    "Orientering om meldingsmønstre (tabell 10674) der det er relevant for kapasitet og samfunnspress i regionen.",
            },
            {
                id: "bufdir-monitor",
                label:
                    "Bufdir / kommunemonitor eller tilsvarende faglige kilder vurdert for lokal kontekst (ikke bare nasjonalt snitt).",
            },
        ],
    },
    {
        title: "Lokalisering og tjenestetilgang",
        items: [
            {
                id: "skoletilgang",
                label:
                    "Reisetid og tilgang til skole / opplæring vurdert (særlig ved ungdom og oppfølging i videregående).",
            },
            {
                id: "kollektiv",
                label:
                    "Kollektivtilgang og arbeidstrening / viktige tjenester innen akseptabel reiseavstand.",
            },
            {
                id: "nærhet",
                label:
                    "Proximity / tilgjengelighet i BEFS sjekket for eiendommer i samme område (der data finnes).",
            },
        ],
    },
    {
        title: "Funksjon, målgruppe og risiko",
        items: [
            {
                id: "malgruppe",
                label:
                    "Målgruppe avklart (familie, ungdom, akutt, institusjon) og avstemt mot statistisk behovsbilde.",
            },
            {
                id: "sikring",
                label:
                    "Krav til sikring, personsoner, uteareal og intern fleksibilitet avklart med fag.",
            },
            {
                id: "drift",
                label:
                    "Drifts- og vedlikeholdsprofil vurdert (bygningsmessig stand, teknisk livsløp).",
            },
        ],
    },
    {
        title: "Økonomi, kontrakt og forankring",
        items: [
            {
                id: "budsjett",
                label:
                    "Business case: investering / leie, drift og eventuell oppgradering dokumentert.",
            },
            {
                id: "kontrakt",
                label:
                    "Kontraktsmessige rammer og risiko (oppsigelse, vedlikeholdsansvar) gjennomgått.",
            },
            {
                id: "forankring",
                label:
                    "Beslutning forankret i porteføljeplan og relevante interne beslutningsforum.",
            },
        ],
    },
    {
        title: "Internasjonale referanser (valgfritt)",
        items: [
            {
                id: "metode-notat",
                label:
                    "Kort metodenotat: populasjon (N), tverrsnitt vs. forløp, og om «fullført videregående» er sammenlignbart på tvers av land.",
            },
            {
                id: "sverige",
                label:
                    "Ved behov: innhentet orienteringsnivå fra Socialstyrelsen / Kolada – uten å blande definisjoner med norske tall.",
            },
        ],
    },
];

export default function PropertyAcquisitionPage() {
    const [checked, setChecked] = useState<Set<string>>(() => new Set());

    useEffect(() => {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return;
            const arr = JSON.parse(raw) as string[];
            if (Array.isArray(arr)) setChecked(new Set(arr));
        } catch {
            /* ignore */
        }
    }, []);

    useEffect(() => {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...checked]));
        } catch {
            /* ignore */
        }
    }, [checked]);

    const toggle = useCallback((id: string) => {
        setChecked((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    }, []);

    const totalItems = CHECKLIST_SECTIONS.reduce((n, s) => n + s.items.length, 0);
    const done = checked.size;

    return (
        <div className="min-h-screen bg-background text-foreground">
            <div className="max-w-3xl mx-auto px-6 pt-28 pb-16">
                <div className="flex items-start gap-4 mb-10">
                    <div className="w-14 h-14 rounded-2xl bg-primary/15 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                        <ListChecks size={28} />
                    </div>
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">
                            Anskaffelse og beslutningsstøtte
                        </h1>
                        <p className="text-muted mt-2 text-base leading-relaxed">
                            Når dere vurderer nye eiendommer, gir offisiell barneverns- og
                            utdanningsstatistikk <strong className="text-foreground font-medium">kontekst</strong>{" "}
                            (behov, målgruppe, lokalisering) – ikke en erstatning for
                            tilstandsrapport, verdivurdering eller intern porteføljeplan. Bruk
                            sjekklisten under sammen med BEFS-data og faglige vurderinger.
                        </p>
                    </div>
                </div>

                <div className="rounded-2xl border border-border bg-card/40 p-5 mb-8 space-y-4">
                    <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                        <Database size={18} className="text-primary" />
                        Nasjonale data i BEFS
                    </h2>
                    <ul className="text-sm text-muted space-y-2 leading-relaxed">
                        <li>
                            <Link
                                href="/ssb/utdanning-metode"
                                className="text-primary font-medium underline underline-offset-2"
                            >
                                Metodeguide: utdanning (Norge/Sverige, epler mot pærer, tabell for
                                beslutning)
                            </Link>
                        </li>
                        <li>
                            <Link
                                href="/ssb?category=utdanning"
                                className="text-primary font-medium underline underline-offset-2"
                            >
                                SSB Statistikk med filter «Utdanning og livsløp»
                            </Link>{" "}
                            – tabeller som 13350 / 13346 (barnevern og utdanning) når de er i den
                            kuraterte listen.
                        </li>
                        <li>
                            <Link href="/ssb" className="text-primary font-medium underline underline-offset-2">
                                Full SSB-fane
                            </Link>{" "}
                            for meldinger (10674), tiltak/plassering (12845) og kombinasjon med
                            eiendommer under «Kombiner med BEFS».
                        </li>
                        <li>
                            <Link href="/barnevern" className="text-primary font-medium underline underline-offset-2">
                                Barnevern-simulering og dokumenter
                            </Link>{" "}
                            for overordnet kontekst og referanser.
                        </li>
                    </ul>
                </div>

                <div className="rounded-2xl border border-border bg-muted/10 p-5 mb-8">
                    <h2 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-2">
                        <BookOpen size={18} className="text-primary" />
                        Kort metodehusk
                    </h2>
                    <p className="text-sm text-muted leading-relaxed">
                        Ved sammenligning over tid eller med andre land: dokumenter{" "}
                        <span className="text-foreground">populasjon (N)</span>, om tallet er{" "}
                        <span className="text-foreground">tverrsnitt eller forløp</span>, og hva
                        «fullført videregående» innebærer i kilden. Skill gjerne mellom{" "}
                        <span className="text-foreground">plassert</span> og{" "}
                        <span className="text-foreground">hjelpetiltak</span> der kildene tillater
                        det – det er ofte der forklaringskraften ligger.
                    </p>
                </div>

                <div className="rounded-2xl border border-border bg-surface/50 p-5 mb-6">
                    <div className="flex items-center justify-between gap-4 mb-4">
                        <h2 className="text-lg font-semibold flex items-center gap-2">
                            <ListChecks size={20} className="text-primary" />
                            Sjekkliste
                        </h2>
                        <span className="text-xs text-muted tabular-nums">
                            {done}/{totalItems} krysset av
                        </span>
                    </div>
                    <p className="text-xs text-muted mb-6">
                        Avkryssing lagres i denne nettleseren (sessionStorage) til fanen lukkes.
                    </p>
                    <div className="space-y-8">
                        {CHECKLIST_SECTIONS.map((section) => (
                            <div key={section.title}>
                                <h3 className="text-sm font-medium text-foreground mb-3">
                                    {section.title}
                                </h3>
                                <ul className="space-y-2">
                                    {section.items.map((item) => (
                                        <li key={item.id}>
                                            <label className="flex items-start gap-3 cursor-pointer group">
                                                <input
                                                    type="checkbox"
                                                    checked={checked.has(item.id)}
                                                    onChange={() => toggle(item.id)}
                                                    className="mt-1 rounded border-input"
                                                />
                                                <span className="text-sm text-muted group-hover:text-foreground transition-colors leading-snug">
                                                    {item.label}
                                                </span>
                                            </label>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="rounded-2xl border border-dashed border-border bg-muted/5 p-5">
                    <h2 className="text-sm font-semibold text-foreground mb-3">
                        Eksterne referanser (manuelt arbeid)
                    </h2>
                    <ul className="space-y-2 text-sm">
                        <li>
                            <a
                                href="https://www.socialstyrelsen.se/statistik-och-data/oppna-jamforelser/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-primary underline underline-offset-2"
                            >
                                Socialstyrelsen – statistikk og åpne sammenligninger (Sverige)
                                <ExternalLink size={14} />
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.kolada.se"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-primary underline underline-offset-2"
                            >
                                Kolada (kommunale nøkkeltall, Sverige)
                                <ExternalLink size={14} />
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.bufdir.no/fagstotte/produkter/tilstandsrapportering_for_kommunale_barnevernstjenester/brukerveiledning---barnevern-kommunemonitor/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-primary underline underline-offset-2"
                            >
                                Bufdir – barnevern kommunemonitor / tilstandsrapport
                                <ExternalLink size={14} />
                            </a>
                        </li>
                    </ul>
                </div>

                <div className="flex flex-wrap gap-3 mt-10">
                    <Link
                        href="/properties"
                        className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted/40"
                    >
                        <Building2 size={18} />
                        Til eiendomslisten
                    </Link>
                    <Link
                        href="/ssb?category=utdanning"
                        className="inline-flex items-center gap-2 rounded-xl bg-primary text-primary-foreground px-4 py-2.5 text-sm font-medium hover:opacity-90"
                    >
                        <Database size={18} />
                        SSB utdanning
                    </Link>
                    <Link
                        href="/barnevern"
                        className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium hover:bg-muted/40"
                    >
                        <Baby size={18} />
                        Barnevern
                    </Link>
                </div>
            </div>
        </div>
    );
}
