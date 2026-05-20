import { categorizeRow, type AccountingCategory } from "./agressoCategories";

export type ParsedRow = Record<string, string>;

export type { AccountingCategory };

export type RowAnalysis = {
  rowIndex: number;
  amount: number;
  flags: FlagCode[];
  flagLabels: string[];
  category: AccountingCategory;
};

export type FlagCode =
  | "credit"
  | "cross_reference"
  | "large_line"
  | "missing_dim2_material"
  | "bilag_many_locations"
  | "suspected_period_mismatch"
  | "empty_text_material"
  | "statsbygg_account_other_supplier"
  | "husleie_account_mismatch";

const FLAG_LABELS: Record<FlagCode, string> = {
  credit: "Kredit / negativt beløp (kreditnota eller motpost)",
  cross_reference: "Tekst tyder på kryssreferanse (går mot bilag, kreditnota …)",
  large_line: "Svært stor enkeltpost (≥ 1 MNOK i absoluttverdi)",
  missing_dim2_material: "Dim2 mangler men beløpet er materielt (≥ 50k)",
  bilag_many_locations: "Bilaget har mange ulike Dim2-steder (≥ 9) — kontroller fordeling",
  suspected_period_mismatch: "Bilagsår og regnskapsår avviker mer enn ett år",
  empty_text_material: "Tom tekst ved beløp ≥ 10k",
  statsbygg_account_other_supplier: "Statsbygg-konto men leverandør ser ikke ut som Statsbygg",
  husleie_account_mismatch:
    "Underkategori «Husleie» men konto matcher ikke forventet leiekonto (6300/6310 ± parkering 6391 / felles 6395)",
};

/** Konti som ofte følger husleie-avtale uten å være ren leie. */
const HUSLEIE_RELATERT_KONTI = new Set(["6391", "6395"]);

const LARGE_ABS = 1_000_000;
const MATERIAL_NO_DIM2 = 50_000;
const MATERIAL_TEXT = 10_000;
const BILAG_LOCATION_THRESHOLD = 9;

/** RFC4180-lignende parser: håndterer anførselstegn og komma i felt. */
export function parseCsvText(text: string): { headers: string[]; rows: ParsedRow[] } {
  const rows: string[][] = [];
  let row: string[] = [];
  let cur = "";
  let inQuotes = false;
  const len = text.length;
  for (let i = 0; i < len; i++) {
    const c = text[i]!;
    if (inQuotes) {
      if (c === '"') {
        if (i + 1 < len && text[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        cur += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      row.push(cur);
      cur = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && i + 1 < len && text[i + 1] === "\n") i++;
      row.push(cur);
      cur = "";
      if (row.some((cell) => cell.trim().length > 0)) {
        rows.push(row);
      }
      row = [];
    } else {
      cur += c;
    }
  }
  row.push(cur);
  if (row.some((cell) => cell.trim().length > 0)) {
    rows.push(row);
  }

  if (rows.length === 0) {
    return { headers: [], rows: [] };
  }

  const rawHeaders = rows[0]!.map((h) => h.replace(/^\ufeff/, "").trim());
  const dataRows = rows.slice(1);
  const out: ParsedRow[] = [];
  const width = rawHeaders.length;

  for (const r of dataRows) {
    const obj: ParsedRow = {};
    for (let j = 0; j < width; j++) {
      obj[rawHeaders[j] ?? `col_${j}`] = (r[j] ?? "").trim();
    }
    out.push(obj);
  }

  return { headers: rawHeaders, rows: out };
}

export function parseBeløp(raw: string | undefined): number {
  if (raw == null) return 0;
  let s = String(raw).trim();
  const negParen = s.startsWith("(") && s.endsWith(")");
  s = s.replace(/^\(|\)$/g, "");
  s = s.replace(/,/g, "").replace(/\s/g, "");
  if (!s || s === "-") return 0;
  const n = Number(s);
  if (Number.isNaN(n)) return 0;
  return negParen ? -Math.abs(n) : n;
}

function normalizeHeaderMap(headers: string[]): Map<string, string> {
  const m = new Map<string, string>();
  for (const h of headers) {
    m.set(h.trim().toLowerCase(), h);
  }
  return m;
}

function get(
  row: ParsedRow,
  map: Map<string, string>,
  ...candidates: string[]
): string {
  for (const c of candidates) {
    const key = map.get(c.toLowerCase());
    if (key && row[key] !== undefined) return row[key] ?? "";
  }
  return "";
}

function buildLocationKey(dim2: string, dim2t: string): string {
  const a = dim2t.trim();
  const b = dim2.trim();
  if (a) return a;
  if (b) return b;
  return "";
}

export function computeBilagLocationCounts(rows: ParsedRow[], headers: string[]): Map<string, number> {
  const map = normalizeHeaderMap(headers);
  const bilagToLocs = new Map<string, Set<string>>();

  for (const row of rows) {
    const bilag = get(row, map, "Bilagsnr", "bilagsnr");
    if (!bilag) continue;
    const loc = buildLocationKey(get(row, map, "Dim2", "dim2"), get(row, map, "Dim2(T)", "dim2(t)"));
    if (!loc) continue;
    if (!bilagToLocs.has(bilag)) bilagToLocs.set(bilag, new Set());
    bilagToLocs.get(bilag)!.add(loc);
  }

  const counts = new Map<string, number>();
  for (const [b, set] of bilagToLocs) {
    counts.set(b, set.size);
  }
  return counts;
}

export function analyzeRows(headers: string[], rows: ParsedRow[]): RowAnalysis[] {
  const map = normalizeHeaderMap(headers);
  const bilagLocs = computeBilagLocationCounts(rows, headers);
  const out: RowAnalysis[] = [];

  rows.forEach((row, rowIndex) => {
    const beløpRaw = get(row, map, "Beløp", "Beløp ", "beløp");
    const amount = parseBeløp(beløpRaw);
    const flags: FlagCode[] = [];

    const tekst = get(row, map, "Tekst", "tekst");
    const bilag = get(row, map, "Bilagsnr", "bilagsnr");
    const dim2 = get(row, map, "Dim2", "dim2");
    const dim2t = get(row, map, "Dim2(T)", "dim2(t)");
    const konto = get(row, map, "Konto", "konto");
    const kontoT = get(row, map, "Konto(T)", "konto(t)");
    const underT = get(row, map, "Underkategorier(T)", "underkategorier(t)");
    const lev = get(row, map, "Resk.nr(T)", "resk.nr(t)");
    const bilagsdato = get(row, map, "Bilagsdato", "bilagsdato");
    const år = get(row, map, "År", "ar");

    if (amount < 0) flags.push("credit");

    const tl = tekst.toLowerCase();
    if (
      /går\s+mot\s+bilag|mot\s+bilag|kreditnota|kreditt\s*nota|kr\.?\s*nota|går\s+mot/i.test(
        tekst,
      ) ||
      /900\d{6}/.test(tekst)
    ) {
      flags.push("cross_reference");
    }

    if (Math.abs(amount) >= LARGE_ABS) flags.push("large_line");

    const hasDim2 = !!(dim2.trim() || dim2t.trim());
    if (!hasDim2 && Math.abs(amount) >= MATERIAL_NO_DIM2) {
      flags.push("missing_dim2_material");
    }

    const nLocs = bilag ? bilagLocs.get(bilag) ?? 0 : 0;
    if (bilag && nLocs >= BILAG_LOCATION_THRESHOLD) {
      flags.push("bilag_many_locations");
    }

    const yDoc = extractYear(bilagsdato);
    const yReg = parseInt(år, 10);
    if (yDoc && !Number.isNaN(yReg) && Math.abs(yDoc - yReg) > 1) {
      flags.push("suspected_period_mismatch");
    }

    if (!tekst.trim() && Math.abs(amount) >= MATERIAL_TEXT) {
      flags.push("empty_text_material");
    }

    const statsbyggKonto =
      konto === "6310" ||
      konto === "6396" ||
      konto === "6398" ||
      /statsbygg/i.test(kontoT);
    if (statsbyggKonto && lev && !/statsbygg/i.test(lev)) {
      flags.push("statsbygg_account_other_supplier");
    }

    if (
      /husleie/i.test(underT) &&
      konto !== "6300" &&
      konto !== "6310" &&
      !HUSLEIE_RELATERT_KONTI.has(konto)
    ) {
      flags.push("husleie_account_mismatch");
    }

    const getRow = (r: ParsedRow, ...candidates: string[]) => get(r, map, ...candidates);
    const category = categorizeRow(row, getRow);

    const unique = [...new Set(flags)];
    out.push({
      rowIndex,
      amount,
      flags: unique,
      flagLabels: unique.map((f) => FLAG_LABELS[f]),
      category,
    });
  });

  return out;
}

function extractYear(bilagsdato: string): number | null {
  const s = bilagsdato.trim();
  const m = s.match(/(\d{4})/);
  if (m) return parseInt(m[1]!, 10);
  const us = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (us) return parseInt(us[3]!, 10);
  return null;
}

export const DEFAULT_EVAL_PROMPT = `Du er senior regnskapskonsulent for statlig eiendomsforvaltning (Bufetat).

Oppgave: Vurder ÉN datalinje fra en Agresso CSV-eksport (leie og tilknyttede lokalkostnader).

Vurder kort:
1) Er konto og underkategori konsistente?
2) Er dimensjoner (Dim1/Dim2) rimelige i forhold til beløp og leverandør?
3) Finnes tegn på kreditnota, kryssreferanse eller behov for oppfølging?
4) Forslag til neste steg (f.eks. slå opp bilag, avstemme mot kontrakt).

Svar strukturert med: Oppsummering, Risiko (lav/middels/høy), Anbefaling.

Data (JSON):
`;

export function rowToJsonForPrompt(row: ParsedRow, analysis?: RowAnalysis): string {
  if (!analysis) {
    return JSON.stringify({ row }, null, 2);
  }
  return JSON.stringify(
    {
      row,
      regnskapskategori: {
        gruppe: analysis.category.groupLabel,
        detalj: analysis.category.detailLabel,
        gruppe_nøkkel: analysis.category.groupKey,
      },
      maskinelle_flagg: {
        beløp_tolkes: analysis.amount,
        koder: analysis.flags,
        beskrivelser: analysis.flagLabels,
      },
    },
    null,
    2,
  );
}
