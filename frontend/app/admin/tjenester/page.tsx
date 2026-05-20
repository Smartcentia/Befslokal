"use client";

import { useState } from "react";
import {
  CheckCircle2, Circle, Clock, ChevronDown, ChevronRight,
  Building2, TrendingUp, Wrench, ShieldCheck, Brain,
  FileText, Users, BarChart3, Database, Settings,
  Printer, Download, ClipboardCheck, AlertCircle
} from "lucide-react";

// ─── Datamodell ──────────────────────────────────────────────────────────────

type Status = "ferdig" | "aktiv" | "under_utvikling" | "planlagt";

interface Tjeneste {
  id: string;
  navn: string;
  beskrivelse: string;
  detaljer?: string[];
  status: Status;
  url?: string;
  godkjent?: boolean;
}

interface TjenesteGruppe {
  id: string;
  navn: string;
  ikon: React.ReactNode;
  farge: string;
  tjenester: Tjeneste[];
}

// ─── Tjenestedata ─────────────────────────────────────────────────────────────

const TJENESTE_DATA: TjenesteGruppe[] = [
  {
    id: "eiendom",
    navn: "Eiendomsforvaltning",
    ikon: <Building2 size={20} />,
    farge: "blue",
    tjenester: [
      {
        id: "eiendom-oversikt",
        navn: "Eiendommsoversikt",
        beskrivelse: "Komplett oversikt over alle 648+ eiendommer i Bufetat med søk, filtrering og detaljvisning.",
        detaljer: [
          "Søk på navn, adresse og region",
          "Filter på type, region og status",
          "Kartvisning med Mapbox",
          "Detaljprofil per eiendom: areal, plasser, type",
        ],
        status: "ferdig",
        url: "/properties",
      },
      {
        id: "eiendom-kart",
        navn: "Kartvisning",
        beskrivelse: "Interaktivt kart som viser alle eiendommer geografisk med klyngevisning.",
        status: "ferdig",
        url: "/properties",
      },
      {
        id: "eiendom-kontrakter",
        navn: "Kontraktsforvaltning",
        beskrivelse: "Administrasjon av leiekontrakter: utløpsdatoer, husleiesats, status og parter.",
        detaljer: [
          "Oversikt alle aktive kontrakter",
          "Varsling ved utløp",
          "Kobling mot GL-regnskap for leie-gap",
        ],
        status: "ferdig",
        url: "/contracts",
      },
      {
        id: "eiendom-parter",
        navn: "Partsregister",
        beskrivelse: "Register over alle utleiere og leietakere (parter) med kontaktinformasjon.",
        status: "ferdig",
        url: "/parties",
      },
      {
        id: "eiendom-lokasjon",
        navn: "Lokasjoner og organisasjon",
        beskrivelse: "Hierarkisk struktur for regioner, lokalkontorer og organisatoriske enheter.",
        status: "aktiv",
        url: "/admin/lokasjoner",
      },
    ],
  },
  {
    id: "okonomi",
    navn: "Økonomi og Regnskap",
    ikon: <TrendingUp size={20} />,
    farge: "green",
    tjenester: [
      {
        id: "okonomi-gl",
        navn: "GL-regnskap (transaksjoner)",
        beskrivelse: "Faktiske kostnader fra General Ledger med 7-dimensjons regnskapsmodell (SRS-standard).",
        detaljer: [
          "Kostnadsoversikt per eiendom, region og konto",
          "Leverandøroversikt og kostnadskategorier",
          "Månedlig og årlig sammenligning (YoY)",
          "Netto-filter: GROUP BY + HAVING SUM > 0 (ikke brutto)",
          "Anomalidetektion for omposteringsår",
        ],
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "okonomi-budsjett",
        navn: "Budsjett 2026",
        beskrivelse: "Budsjettoppfølging per eiendom og region med avviksanalyse mot faktiske tall.",
        detaljer: [
          "Budsjett vs. faktisk per måned",
          "Avviksrapport per kategori og eiendom",
          "Import av budsjettsdata (Excel/CSV)",
        ],
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "okonomi-prediksjon",
        navn: "Prediksjon 2027 (Holt-Winters)",
        beskrivelse: "Automatisk prognosegenerering med Holt-Winters algoritme basert på historiske GL-data.",
        detaljer: [
          "Prediksjon per eiendom og kategori",
          "Regional sammenstilling (BEFS-tall ~566 MNOK 2026)",
          "Excel-eksport med metodikk-fane",
        ],
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "okonomi-leiegap",
        navn: "Leie-gap analyse",
        beskrivelse: "Differanse mellom kontraktsfestet husleie og GL-bokført husleie per eiendom.",
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "okonomi-avvik",
        navn: "Avviksanalyse budsjett",
        beskrivelse: "Månedlig og kumulativ avviksrapport mellom budsjett og faktiske kostnader.",
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "okonomi-innkjop",
        navn: "Innkjøpsanalyse",
        beskrivelse: "Leverandøroversikt og kategorianalyse av innkjøp via GL-transaksjoner.",
        status: "aktiv",
        url: "/admin/procurement",
      },
      {
        id: "okonomi-import",
        navn: "GL-import (CSV)",
        beskrivelse: "Import av transaksjoner fra kildesystemet med validering mot SRS-regler og bilagsarter.",
        detaljer: [
          "Validering av 7 dimensjoner",
          "Bilagsart-kontroll (IV, IW, MT, RE m.fl.)",
          "Dim 6 polymorfi (Ansattnr/Anleggsnr)",
          "Balansesjekk per bilagsnummer",
        ],
        status: "aktiv",
        url: "/admin/import",
      },
    ],
  },
  {
    id: "fdvu",
    navn: "FDVU (Forvaltning, Drift, Vedlikehold og Utvikling)",
    ikon: <Wrench size={20} />,
    farge: "orange",
    tjenester: [
      {
        id: "fdvu-kravkatalog",
        navn: "Kravkatalog (122 krav)",
        beskrivelse: "Komplett katalog over lovkrav og interne krav fordelt på 12 regelverk.",
        detaljer: [
          "RKL6, BVL, KVALITETSFORSKRIFTEN, TEK17",
          "HMS, DRIFTSLEDELSE, ENOK, UU",
          "SIKKERHET, MILJØ, BYGG, INTERN",
          "Kategorier: kritisk, høy, middels, lav",
        ],
        status: "ferdig",
        url: "/fdvu/krav",
      },
      {
        id: "fdvu-tilordninger",
        navn: "Krav-tilordninger (12.250+)",
        beskrivelse: "Alle 122 krav er tilordnet alle 648+ eiendommer — totalt 12.250+ tilordninger.",
        status: "ferdig",
      },
      {
        id: "fdvu-vurdering",
        navn: "Vurderingsverktøy (bulk-assessment)",
        beskrivelse: "Effektivt verktøy for å vurdere compliance-status for én eiendom om gangen.",
        detaljer: [
          "Søk og velg eiendom blant 648+",
          "Grupper krav per regelverk (kollapsbar)",
          "Bulk-sett status per gruppe (RKL6, TEK17 osv.)",
          "Individuelle notater og neste revisjonsdato",
          "Lagre kun endrede (dirty tracking)",
        ],
        status: "ferdig",
        url: "/fdvu/vurdering",
      },
      {
        id: "fdvu-tilsynsrapport",
        navn: "Tilsynsrapport (per eiendom)",
        beskrivelse: "Pre-utfylt tilsynsrapport per eiendom med avkrysning og fritekst. Kan skrives ut som PDF.",
        detaljer: [
          "Compliance-status per krav (avkrysning/dropdown)",
          "Fritekst: notat og begrunnelse per krav",
          "Inspektørnavn, dato, konklusjon og tiltak",
          "Signaturfelter",
          "Skriv ut → PDF via nettleser",
        ],
        status: "ferdig",
        url: "/fdvu/[eiendom-id]/rapport",
      },
      {
        id: "fdvu-portefolje",
        navn: "Porteføljestatus (region/Bufetat)",
        beskrivelse: "Aggregert FDVU-status for region eller hele Bufetat med KPI-kort og sorterbar tabell.",
        detaljer: [
          "Filter: Bufetat / region / eiendom",
          "6 KPI-kort: eiendommer, rate, oppfylt, avvik, delvis, forfalt",
          "Compliance-stolpediagram per eiendom",
          "Sortering på navn, rate og avvik",
          "Skriv ut → PDF-rapport",
        ],
        status: "ferdig",
        url: "/fdvu/rapport",
      },
      {
        id: "fdvu-komponenter",
        navn: "FDV-komponenter og tilstandsgrader",
        beskrivelse: "Registrering av bygningskomponenter med tilstandsgrader TG0–TG3 og servicehistorikk.",
        status: "aktiv",
        url: "/fdvu",
      },
      {
        id: "fdvu-dokumenter",
        navn: "FDV-dokumenter",
        beskrivelse: "Bibliotek over FDV-dokumentasjon per eiendom (brukermanualer, serviceavtaler, tegninger).",
        status: "aktiv",
        url: "/fdvu",
      },
      {
        id: "fdvu-vedlikehold",
        navn: "Vedlikeholdsplan",
        beskrivelse: "Planlegging og oppfølging av vedlikeholdsoppgaver med periodisitet og ansvarlig.",
        status: "under_utvikling",
      },
      {
        id: "fdvu-avvik",
        navn: "FDVU-avvik (non_compliant kobling)",
        beskrivelse: "Dedikert avvikshåndtering for FDVU-krav med kobling til HMS-avvikssystemet.",
        status: "planlagt",
      },
    ],
  },
  {
    id: "hms",
    navn: "HMS (Helse, Miljø og Sikkerhet)",
    ikon: <ShieldCheck size={20} />,
    farge: "red",
    tjenester: [
      {
        id: "hms-avvik",
        navn: "Avvikshåndtering",
        beskrivelse: "Registrering, behandling og oppfølging av HMS-avvik med alvorlighetsgrad og status.",
        detaljer: [
          "Kategorier: ulykke, nestenulykke, observasjon",
          "Alvorlighetsgrad: kritisk, høy, middels, lav",
          "Workflow: åpen → under behandling → lukket",
          "Eiendomskobling og ansvarlig person",
        ],
        status: "ferdig",
        url: "/deviations",
      },
      {
        id: "hms-sjekklister",
        navn: "Sjekklister",
        beskrivelse: "Periodiske HMS-sjekklister per eiendom med avkrysning og historikk.",
        status: "ferdig",
        url: "/checklists",
      },
      {
        id: "hms-kalender",
        navn: "HMS-kalender",
        beskrivelse: "Oversikt over planlagte inspeksjoner, revisjoner og tilsyn.",
        status: "aktiv",
        url: "/admin/hms-calendar",
      },
    ],
  },
  {
    id: "ki",
    navn: "KI-Kollega (Kunstig Intelligens)",
    ikon: <Brain size={20} />,
    farge: "purple",
    tjenester: [
      {
        id: "ki-chat",
        navn: "KI-Kollega chat",
        beskrivelse: "Intelligent assistent som kan svare på spørsmål om alle BEFS-tjenester på norsk.",
        detaljer: [
          "Eiendommer, kontrakter og parter",
          "Økonomi og GL-regnskap (SQL-basert)",
          "FDVU compliance og tilsynsrapporter",
          "HMS-avvik og sjekklister",
          "Barnevern og institusjonsdata",
          "SSB-statistikk og prognoser",
        ],
        status: "ferdig",
        url: "/ki-kollega",
      },
      {
        id: "ki-fdvu",
        navn: "KI FDVU-rapport",
        beskrivelse: "KI-Kollega kan generere komplette tilsynsrapporter og compliance-analyser via chat.",
        detaljer: [
          "«Lag tilsynsrapport for [eiendom]»",
          "«Hva er FDVU-status for region Øst?»",
          "«Hvilke eiendommer har flest avvik i RKL6?»",
        ],
        status: "ferdig",
        url: "/ki-kollega",
      },
      {
        id: "ki-okonomi",
        navn: "KI økonomi og regnskap",
        beskrivelse: "Naturlig-språk-spørringer mot GL-data, budsjett og prediksjoner.",
        detaljer: [
          "«Vis kostnadsvekst for Drammen 2023–2025»",
          "«Hvilke leverandører bruker vi mest?»",
          "«Hva er leie-gap for Stavanger?»",
        ],
        status: "ferdig",
        url: "/ki-kollega",
      },
      {
        id: "ki-barnevern",
        navn: "KI barnevern og institusjoner",
        beskrivelse: "Simulering og analyse av barnevernskostnader og institusjonsdata.",
        status: "ferdig",
        url: "/ki-kollega",
      },
      {
        id: "ki-lovdata",
        navn: "KI lovdataanalyse",
        beskrivelse: "Søk og analyse av relevant lovverk og forskrifter via Lovdata-integrasjon.",
        status: "aktiv",
        url: "/ki-kollega",
      },
    ],
  },
  {
    id: "rapporter",
    navn: "Rapporter og analyse",
    ikon: <BarChart3 size={20} />,
    farge: "teal",
    tjenester: [
      {
        id: "rapport-finans",
        navn: "Finansiell oversikt",
        beskrivelse: "Komplett finansdashboard med budsjett, faktiske tall, avvik og prediksjon.",
        status: "ferdig",
        url: "/financials",
      },
      {
        id: "rapport-barnevern",
        navn: "Barnevern-analyse",
        beskrivelse: "Analyse av barnevernskostnader og plassdekning med SSB-sammenligning.",
        status: "ferdig",
        url: "/barnevern-analysis",
      },
      {
        id: "rapport-fdvu-rapport",
        navn: "FDVU porteføljerapport (PDF)",
        beskrivelse: "Utskriftbar rapport over FDVU-status for hele Bufetat eller per region.",
        status: "ferdig",
        url: "/fdvu/rapport",
      },
      {
        id: "rapport-tilsynsrapport",
        navn: "Tilsynsrapport per eiendom (PDF)",
        beskrivelse: "Pre-utfylt, utskriftbar tilsynsrapport for hver enkelt eiendom.",
        status: "ferdig",
        url: "/fdvu/[id]/rapport",
      },
      {
        id: "rapport-excel",
        navn: "Excel-eksport budsjett 2026/2027",
        beskrivelse: "Nedlastbar Excel med budsjettprognoser, regionvekst og metodikk-fane.",
        status: "ferdig",
      },
    ],
  },
  {
    id: "admin",
    navn: "Administrasjon og system",
    ikon: <Settings size={20} />,
    farge: "gray",
    tjenester: [
      {
        id: "admin-brukere",
        navn: "Brukeradministrasjon",
        beskrivelse: "Administrasjon av brukere med roller (ADMIN, REGIONAL_MANAGER, PROPERTY_MANAGER, JANITOR, TENANT).",
        status: "ferdig",
        url: "/admin/users",
      },
      {
        id: "admin-rbac",
        navn: "Rollebasert tilgangsstyring (RBAC)",
        beskrivelse: "Granulert tilgangsstyring per rolle og eiendom. ADMIN ser alt, øvrige roller filtreres.",
        status: "ferdig",
      },
      {
        id: "admin-governance",
        navn: "Data Governance",
        beskrivelse: "Klassifisering av tabeller (FINANCIAL, PII, RESTRICTED, INTERNAL, PUBLIC) med norske nøkkelord.",
        status: "ferdig",
        url: "/admin/governance",
      },
      {
        id: "admin-mfa",
        navn: "MFA og sikkerhet",
        beskrivelse: "Tofaktorautentisering med e-postkode, timing-attack-beskyttelse og kryptografiske tokens.",
        status: "ferdig",
      },
      {
        id: "admin-logg",
        navn: "System- og aktivitetslogg",
        beskrivelse: "Sporing av brukerhandlinger, import-operasjoner og API-kall.",
        status: "aktiv",
        url: "/admin/logs",
      },
      {
        id: "admin-impersonate",
        navn: "Rollesimulering",
        beskrivelse: "Admin kan simulere andre roller for å verifisere tilgangsstyring.",
        status: "ferdig",
        url: "/admin/impersonate",
      },
    ],
  },
];

// ─── Status-visning ───────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<Status, { label: string; color: string; icon: React.ReactNode }> = {
  ferdig: {
    label: "Ferdig",
    color: "bg-green-100 text-green-800 border-green-200",
    icon: <CheckCircle2 size={12} className="inline mr-1" />,
  },
  aktiv: {
    label: "Aktiv / delvis",
    color: "bg-blue-100 text-blue-800 border-blue-200",
    icon: <Circle size={12} className="inline mr-1" />,
  },
  under_utvikling: {
    label: "Under utvikling",
    color: "bg-yellow-100 text-yellow-800 border-yellow-200",
    icon: <Clock size={12} className="inline mr-1" />,
  },
  planlagt: {
    label: "Planlagt",
    color: "bg-gray-100 text-gray-600 border-gray-200",
    icon: <Clock size={12} className="inline mr-1 opacity-50" />,
  },
};

const FARGE_MAP: Record<string, string> = {
  blue:   "border-l-blue-500 bg-blue-50",
  green:  "border-l-green-500 bg-green-50",
  orange: "border-l-orange-500 bg-orange-50",
  red:    "border-l-red-500 bg-red-50",
  purple: "border-l-purple-500 bg-purple-50",
  teal:   "border-l-teal-500 bg-teal-50",
  gray:   "border-l-gray-400 bg-gray-50",
};

const IKON_FARGE: Record<string, string> = {
  blue: "text-blue-600 bg-blue-100",
  green: "text-green-600 bg-green-100",
  orange: "text-orange-600 bg-orange-100",
  red: "text-red-600 bg-red-100",
  purple: "text-purple-600 bg-purple-100",
  teal: "text-teal-600 bg-teal-100",
  gray: "text-gray-600 bg-gray-100",
};

// ─── Komponent ────────────────────────────────────────────────────────────────

export default function TjenesterPage() {
  const [godkjente, setGodkjente] = useState<Record<string, boolean>>({});
  const [aapne, setAapne] = useState<Record<string, boolean>>(
    Object.fromEntries(TJENESTE_DATA.map((g) => [g.id, true]))
  );
  const [visKun, setVisKun] = useState<"alle" | "ferdig" | "planlagt">("alle");

  const toggleGodkjent = (id: string) =>
    setGodkjente((prev) => ({ ...prev, [id]: !prev[id] }));

  const toggleGruppe = (id: string) =>
    setAapne((prev) => ({ ...prev, [id]: !prev[id] }));

  const godkjennAlle = () => {
    const alle = TJENESTE_DATA.flatMap((g) => g.tjenester).map((t) => t.id);
    setGodkjente(Object.fromEntries(alle.map((id) => [id, true])));
  };

  const fjernAlleGodkjenninger = () => setGodkjente({});

  // Statistikk
  const alleTjenester = TJENESTE_DATA.flatMap((g) => g.tjenester);
  const antallFerdig = alleTjenester.filter((t) => t.status === "ferdig" || t.status === "aktiv").length;
  const antallGodkjent = Object.values(godkjente).filter(Boolean).length;
  const antallTotal = alleTjenester.length;

  const filtrert = (tjenester: Tjeneste[]) => {
    if (visKun === "ferdig") return tjenester.filter((t) => t.status === "ferdig" || t.status === "aktiv");
    if (visKun === "planlagt") return tjenester.filter((t) => t.status === "under_utvikling" || t.status === "planlagt");
    return tjenester;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 print:border-none">
        <div className="max-w-5xl mx-auto px-6 py-6 print:py-4">
          <div className="flex items-start justify-between print:block">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
                Bufetat Eiendomsforvaltningssystem
              </p>
              <h1 className="text-2xl font-bold text-gray-900">
                BEFS — Tjenesteoversikt og godkjenning
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Komplett oversikt over alle tjenester, status og veien videre · {new Date().toLocaleDateString("nb-NO", { year: "numeric", month: "long", day: "numeric" })}
              </p>
            </div>
            <div className="flex gap-2 mt-1 print:hidden">
              {antallGodkjent < antallTotal ? (
                <button
                  onClick={godkjennAlle}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg transition font-medium"
                >
                  <CheckCircle2 size={14} /> Godkjenn alle ({antallTotal})
                </button>
              ) : (
                <button
                  onClick={fjernAlleGodkjenninger}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition"
                >
                  <Circle size={14} /> Fjern alle godkjenninger
                </button>
              )}
              <button
                onClick={() => window.print()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
              >
                <Printer size={14} /> Skriv ut / PDF
              </button>
            </div>
          </div>

          {/* KPI-stripe */}
          <div className="grid grid-cols-3 gap-4 mt-5 print:grid-cols-3">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <p className="text-2xl font-bold text-green-700">{antallFerdig}</p>
              <p className="text-xs text-green-600 mt-0.5">av {antallTotal} tjenester ferdig / aktive</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-2xl font-bold text-blue-700">648+</p>
              <p className="text-xs text-blue-600 mt-0.5">eiendommer forvaltet</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
              <p className="text-2xl font-bold text-purple-700">{antallGodkjent} / {antallTotal}</p>
              <p className="text-xs text-purple-600 mt-0.5">tjenester godkjent i denne sesjonen</p>
            </div>
          </div>

          {/* Filter */}
          <div className="flex gap-2 mt-4 print:hidden">
            {(["alle", "ferdig", "planlagt"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setVisKun(v)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition ${
                  visKun === v ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {v === "alle" ? "Alle tjenester" : v === "ferdig" ? "✅ Ferdig / aktive" : "🔜 Under utvikling / planlagt"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Innhold */}
      <div className="max-w-5xl mx-auto px-6 py-6 space-y-6 print:px-0 print:py-4">
        {TJENESTE_DATA.map((gruppe) => {
          const tjenester = filtrert(gruppe.tjenester);
          if (tjenester.length === 0) return null;
          const erAapen = aapne[gruppe.id] !== false;

          return (
            <div key={gruppe.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden print:break-inside-avoid print:shadow-none print:border-gray-300">
              {/* Gruppe-header */}
              <button
                onClick={() => toggleGruppe(gruppe.id)}
                className="w-full flex items-center gap-3 px-5 py-4 hover:bg-gray-50 transition print:pointer-events-none"
              >
                <span className={`p-2 rounded-lg ${IKON_FARGE[gruppe.farge]}`}>
                  {gruppe.ikon}
                </span>
                <span className="font-semibold text-gray-900 flex-1 text-left text-base">
                  {gruppe.navn}
                </span>
                <span className="text-xs text-gray-400 mr-2">
                  {filtrert(gruppe.tjenester).filter((t) => t.status === "ferdig" || t.status === "aktiv").length} / {filtrert(gruppe.tjenester).length} aktive
                </span>
                <span className="print:hidden">
                  {erAapen ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
                </span>
              </button>

              {/* Tjeneste-rader */}
              {erAapen && (
                <div className="divide-y divide-gray-50">
                  {tjenester.map((tjeneste) => {
                    const st = STATUS_CONFIG[tjeneste.status];
                    const erGodkjent = godkjente[tjeneste.id] || false;

                    return (
                      <div
                        key={tjeneste.id}
                        className={`flex gap-4 px-5 py-4 transition border-l-4 ${
                          FARGE_MAP[gruppe.farge]
                        } ${erGodkjent ? "bg-green-50/60" : ""} print:py-3`}
                      >
                        {/* Print-avkrysning */}
                        <div className="mt-1 flex-shrink-0 hidden print:block">
                          <div className="w-4 h-4 border border-gray-400 rounded" />
                        </div>

                        {/* Innhold */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className={`font-semibold text-sm ${erGodkjent ? "text-gray-400" : "text-gray-900"}`}>
                              {erGodkjent && <CheckCircle2 size={13} className="inline mr-1 text-green-500" />}
                              {tjeneste.navn}
                            </h3>
                            <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${st.color}`}>
                              {st.icon}{st.label}
                            </span>
                            {tjeneste.url && (
                              <a
                                href={tjeneste.url}
                                className="text-xs text-blue-500 hover:underline print:hidden"
                                target="_blank"
                              >
                                → åpne
                              </a>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
                            {tjeneste.beskrivelse}
                          </p>
                          {tjeneste.detaljer && tjeneste.detaljer.length > 0 && (
                            <ul className="mt-2 space-y-0.5">
                              {tjeneste.detaljer.map((d, i) => (
                                <li key={i} className="text-xs text-gray-400 flex items-start gap-1.5">
                                  <span className="mt-1 flex-shrink-0 w-1 h-1 rounded-full bg-gray-300" />
                                  {d}
                                </li>
                              ))}
                            </ul>
                          )}
                          {/* Godkjenningsknapp – tydelig atskilt fra status */}
                          <div className="mt-3 print:hidden">
                            <button
                              onClick={() => toggleGodkjent(tjeneste.id)}
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium border transition ${
                                erGodkjent
                                  ? "bg-green-100 border-green-300 text-green-700 hover:bg-green-200"
                                  : "bg-white border-gray-200 text-gray-500 hover:border-green-400 hover:text-green-600"
                              }`}
                            >
                              {erGodkjent ? (
                                <><CheckCircle2 size={12} /> Godkjent i denne sesjonen — klikk for å angre</>
                              ) : (
                                <><Circle size={12} /> Merk som gjennomgått</>
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {/* Videre arbeid */}
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 print:break-inside-avoid">
          <h2 className="font-bold text-amber-900 mb-3 flex items-center gap-2">
            <AlertCircle size={18} className="text-amber-500" />
            Videre arbeid — hva gjenstår
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 print:grid-cols-2">
            {[
              { pri: "Høy", tekst: "FDVU-vurdering av alle 648 eiendommer (status: ikke_vurdert → compliant/non_compliant)" },
              { pri: "Høy", tekst: "Budsjett 2026 — full avviksoppfølging per eiendom og region" },
              { pri: "Middels", tekst: "FDVU vedlikeholdsplan — planlegg tiltak for non_compliant-krav" },
              { pri: "Middels", tekst: "Automatisk varsling ved kontraktutløp og FDVU-forfalte revisjoner" },
              { pri: "Middels", tekst: "FDVU-avvikssystem — kobling til HMS-avvik for non_compliant FDVU-krav" },
              { pri: "Lav", tekst: "GL-import automatisering — planlagt jobbing mot kildesystem" },
              { pri: "Lav", tekst: "KI-Kollega SSO / Copilot-integrasjon for Teams" },
              { pri: "Lav", tekst: "Mobile-app for driftspersonell (sjekklister og FDVU på farten)" },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className={`text-xs px-1.5 py-0.5 rounded font-bold flex-shrink-0 mt-0.5 ${
                  item.pri === "Høy" ? "bg-red-100 text-red-700" :
                  item.pri === "Middels" ? "bg-yellow-100 text-yellow-700" :
                  "bg-gray-100 text-gray-600"
                }`}>
                  {item.pri}
                </span>
                <p className="text-sm text-amber-800">{item.tekst}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Print-footer */}
      <div className="hidden print:block text-center text-xs text-gray-400 pb-8">
        Bufetat Eiendomsforvaltningssystem (BEFS) · Konfidensielt · {new Date().toLocaleDateString("nb-NO")}
      </div>
    </div>
  );
}
