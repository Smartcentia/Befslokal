/**
 * Agresso CSV-eksport — kolonner og forklaringer (Bufetat / lokalkostnader).
 */
export type AgressoColumnDef = {
  key: string;
  label: string;
  explanation: string;
};

export const AGRESSO_COLUMNS: AgressoColumnDef[] = [
  {
    key: "BA",
    label: "BA",
    explanation:
      "Bilagsart i Agresso (f.eks. IV = leverandørfaktura, KF = intern fordeling, CF/MP = betaling/korrigering). Styrer hvordan posten oppstår.",
  },
  {
    key: "Bilagsnr",
    label: "Bilagsnr",
    explanation:
      "Unikt bilagsnummer. Samme nummer på flere rader = flere kontolinjer på samme bilag.",
  },
  {
    key: "Bilagsdato",
    label: "Bilagsdato",
    explanation: "Dato bilaget er registrert i Agresso (ikke nødvendigvis leverandørens fakturadato).",
  },
  {
    key: "År",
    label: "År",
    explanation: "Regnskapsår for posteringen.",
  },
  {
    key: "Periode",
    label: "Periode",
    explanation: "Regnskapsperiode (typisk YYYYMM el. tilsvarende etter deres oppsett).",
  },
  {
    key: "Innkjøpskategorier",
    label: "Innkjøpskategorier",
    explanation: "Kode for innkjøpskategori (f.eks. 01 = leie lokaler).",
  },
  {
    key: "Innkjøpskategorier(T)",
    label: "Innkjøpskategorier (T)",
    explanation: "Tekst til innkjøpskategorikoden.",
  },
  {
    key: "Underkategorier",
    label: "Underkategorier",
    explanation: "Kode for underkategori (husleie, drift, strøm, renhold …).",
  },
  {
    key: "Underkategorier(T)",
    label: "Underkategorier (T)",
    explanation: "Tekst til underkategorien — ofte beste «hva er dette?» på overordnet nivå.",
  },
  {
    key: "Konto",
    label: "Konto",
    explanation: "Hovedbokskontonummer.",
  },
  {
    key: "Konto(T)",
    label: "Konto (T)",
    explanation: "Kontonavn — presiserer kostnadsart (leie Statsbygg, leie andre, BAD, strøm …).",
  },
  {
    key: "Region",
    label: "Region",
    explanation: "Regional tilhørighet (Øst, Sør, Vest, Nord, Midt, Bufdir …).",
  },
  {
    key: "Dim1",
    label: "Dim1",
    explanation: "Dimensjon 1 — kode (ofte koststed / enhet).",
  },
  {
    key: "Dim1(T)",
    label: "Dim1 (T)",
    explanation: "Dimensjon 1 — beskrivelse (enhet, avdeling, ev. adresse i navnet).",
  },
  {
    key: "Dim2",
    label: "Dim2",
    explanation: "Dimensjon 2 — kode (eiendom/prosjekt/lokalitet når brukt).",
  },
  {
    key: "Dim2(T)",
    label: "Dim2 (T)",
    explanation:
      "Dimensjon 2 — tekst. Ofte fysisk adresse eller bygg/prosjekt — sterkest spor til eiendom når utfylt.",
  },
  {
    key: "Dim3",
    label: "Dim3",
    explanation: "Ekstra fordelingsdimensjon (aktivitet/prosjekt — avhenger av oppsett).",
  },
  {
    key: "Dim4",
    label: "Dim4",
    explanation: "Ekstra fordelingsdimensjon.",
  },
  {
    key: "Dim5",
    label: "Dim5",
    explanation: "Ekstra fordelingsdimensjon.",
  },
  {
    key: "Dim6",
    label: "Dim6",
    explanation: "Ekstra fordelingsdimensjon.",
  },
  {
    key: "Dim7",
    label: "Dim7",
    explanation: "Ekstra fordelingsdimensjon.",
  },
  {
    key: "AV",
    label: "AV",
    explanation:
      "Hjelpefelt / kode som varierer (MVA, avstemming e.l.) — verifiser mot egen Agresso-dokumentasjon ved formell bruk.",
  },
  {
    key: "Tekst",
    label: "Tekst",
    explanation: "Fritekst på linjen — referanser til kreditnota, «går mot bilag», periode, fakturanummer …",
  },
  {
    key: "Beløp",
    label: "Beløp",
    explanation:
      "Linjebeløp. Parentes eller negativ verdi = kredit / reduksjon. Tusenskille kan være komma (US-format i eksport).",
  },
  {
    key: "Resk.nr",
    label: "Resk.nr",
    explanation: "Leverandørreskontro — kode.",
  },
  {
    key: "Resk.nr(T)",
    label: "Resk.nr (T)",
    explanation: "Leverandørnavn.",
  },
];

export const COLUMN_DEF_BY_KEY: Record<string, AgressoColumnDef> = Object.fromEntries(
  AGRESSO_COLUMNS.map((c) => [c.key, c]),
);

export function getColumnExplanation(header: string): string {
  const def = COLUMN_DEF_BY_KEY[header];
  if (def) return def.explanation;
  return "Kolonne fra CSV — ikke definert i standardordboken. Sjekk Agresso-rapportdokumentasjon.";
}
