/**
 * Parsere for Innkjøpsanalyse-CSV-eksporter fra Agresso/Cognos.
 * To formater:
 *  - Pivot: kategori/underkategori som rader, regioner som kolonner (leie, aggregert)
 *  - Flat:  region som seksjonheader, institusjon + beløp som rader (strøm, annen kostnad)
 */

export interface PivotRow {
    category: string;       // Toppkategori, f.eks. "Leie lokaler andre utleiere"
    institution: string;    // Institusjonsnavn (tom = kategoriheader-rad)
    midt: number;
    nord: number;
    sor: number;
    vest: number;
    ost: number;
    bufdir: number;
    total: number;
}

export interface FlatRow {
    region: string;
    institution: string;
    amount: number;
    category: string;       // Fra filens Konto Beskrivelse-felt
}

export interface AggregertRow {
    category: string;
    midt: number;
    nord: number;
    sor: number;
    vest: number;
    ost: number;
    bufdir: number;
    total: number;
}

/** Fjerner norsk tusenskilletegn (mellomrom) og parser til tall. */
function parseNOK(s: string): number {
    if (!s || !s.trim()) return 0;
    const cleaned = s.replace(/\s/g, "").replace(",", ".");
    const n = parseFloat(cleaned);
    return isNaN(n) ? 0 : n;
}

/** Detect delimiter: semicolon eller comma */
function detectDelimiter(firstLine: string): string {
    const semis = (firstLine.match(/;/g) || []).length;
    const commas = (firstLine.match(/,/g) || []).length;
    return semis >= commas ? ";" : ",";
}

/**
 * Kjente seksjonstitler i Cognos-pivot (rad uten beløp). Må matche eksporten — ikke bruk
 * institusjonsnavn med null i alle regioner som kategori (vanlig feilkilde).
 * Inkluderer kategorier fra aggregert.csv pluss pivot-spesifikke (f.eks. indre vedlikehold).
 */
export const PIVOT_SECTION_HEADERS = new Set<string>([
    "Leie lokaler andre utleiere",
    "Leie lokaler fra Statsbygg",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter andre utleiere",
    "Strøm og oppvarming",
    "Renhold lokaler",
    "Reparasjon og vedlikehold leide lokaler",
    "Annen kostnad lokaler",
    "Leie parkeringsplass",
    "Vakthold lokaler",
    "Vaktmestertjenester",
    "Renovasjon, vann, avløp o.l.",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Reparasjon og vedlikehold av verktøy og maskiner, inkl serviceavtaler",
    "Reparasjon og vedlikehold av datautstyr, inkl. serviceavtaler",
    "Fellesutgifter Statsbygg - indre vedlikehold",
]);

/** Strøm / annen kostnad — splittes i egen kolonne på detaljfanen */
export const PIVOT_CATEGORY_STROM = "Strøm og oppvarming";
export const PIVOT_CATEGORY_ANNEN_LOKALER = "Annen kostnad lokaler";

/** Region med størst beløp (for visning/filter), samme navn som i flat-filer */
export function pivotRegionLabel(r: PivotRow): string {
    const pairs: [string, number][] = [
        ["Region Midt-Norge", r.midt],
        ["Region Nord", r.nord],
        ["Region Sør", r.sor],
        ["Region Vest", r.vest],
        ["Region Øst", r.ost],
        ["Bufdir", r.bufdir],
    ];
    const best = pairs.reduce((a, b) => (b[1] > a[1] ? b : a));
    return best[1] !== 0 ? best[0] : "";
}

/**
 * Parser pivot-format: Leie av lokaler (detaljert per institusjon).
 * Kolonner: institusjon | Midt-Norge | Nord | Sør | Vest | Øst | Bufdir | Totalsum
 */
export function parsePivotDetailCsv(text: string): PivotRow[] {
    const lines = text.split(/\r?\n/);
    const delimiter = detectDelimiter(lines[0] || lines[2] || ";");

    // Finn datastart: raden med "Radetiketter" er kolonneheaderen
    const headerIdx = lines.findIndex((l) => l.includes("Radetiketter"));
    if (headerIdx === -1) return [];

    const rows: PivotRow[] = [];
    let currentCategory = "";

    for (let i = headerIdx + 1; i < lines.length; i++) {
        const cols = lines[i].split(delimiter);
        if (cols.every((c) => !c.trim())) continue;

        const name = cols[0]?.trim();

        // Toppkategori og Totalsum-rad — skip
        if (name?.startsWith("Leie av lokaler og tilknyttede")) continue;
        if (name?.startsWith("Totalsum")) continue;

        if (!name) {
            // Tom institusjonsnavn = Bufdir-allokering uten spesifikk institusjon
            const bufdirAmt = parseNOK(cols[6]);
            const totalAmt  = parseNOK(cols[7]);
            if (bufdirAmt !== 0 || totalAmt !== 0) {
                rows.push({
                    category: currentCategory,
                    institution: "Bufdir",
                    midt:   parseNOK(cols[1]),
                    nord:   parseNOK(cols[2]),
                    sor:    parseNOK(cols[3]),
                    vest:   parseNOK(cols[4]),
                    ost:    parseNOK(cols[5]),
                    bufdir: bufdirAmt,
                    total:  totalAmt || bufdirAmt,
                });
            }
            continue;
        }

        // Seksjonstittel: ingen beløp — kun kjente overskrifter bytter kategori (ikke «Justøya …» m.m.)
        const hasAmount = cols.slice(1).some((c) => parseNOK(c) !== 0);
        if (!hasAmount) {
            if (PIVOT_SECTION_HEADERS.has(name)) {
                currentCategory = name;
            }
            continue;
        }

        rows.push({
            category: currentCategory,
            institution: name,
            midt:   parseNOK(cols[1]),
            nord:   parseNOK(cols[2]),
            sor:    parseNOK(cols[3]),
            vest:   parseNOK(cols[4]),
            ost:    parseNOK(cols[5]),
            bufdir: parseNOK(cols[6]),
            total:  parseNOK(cols[7]),
        });
    }

    return rows;
}

/**
 * Parser aggregert-format: Lokaler, repar og vedlikehold.
 * Rader = kostnadskategorier, kolonner = regioner.
 */
export function parseAggregertCsv(text: string): AggregertRow[] {
    const lines = text.split(/\r?\n/);
    const delimiter = detectDelimiter(lines[0] || ";");

    // Finn raden med "Radetiketter"
    const headerIdx = lines.findIndex((l) => l.includes("Radetiketter"));
    if (headerIdx === -1) return [];

    const rows: AggregertRow[] = [];

    for (let i = headerIdx + 1; i < lines.length; i++) {
        const cols = lines[i].split(delimiter);
        if (cols.every((c) => !c.trim())) continue;

        const name = cols[0]?.trim();
        if (!name) continue;
        if (name.startsWith("Leie av lokaler og tilknyttede")) continue;
        if (name === "Kontor og administrasjon" || name === "IKT") continue;

        const hasAmount = cols.slice(1).some((c) => parseNOK(c) !== 0);
        if (!hasAmount) continue;

        rows.push({
            category: name,
            midt: parseNOK(cols[1]),
            nord: parseNOK(cols[2]),
            sor: parseNOK(cols[3]),
            vest: parseNOK(cols[4]),
            ost: parseNOK(cols[5]),
            bufdir: parseNOK(cols[6]),
            total: parseNOK(cols[7]),
        });
    }

    return rows;
}

/**
 * Parser flat-format: Strøm og oppvarming, Annen kostnad lokaler.
 * Struktur: Bufetat > Region X > Institusjonsnavn | beløp
 */
export function parseFlatCsv(text: string, category: string): FlatRow[] {
    const lines = text.split(/\r?\n/);
    const delimiter = detectDelimiter(lines[0] || ";");

    // Finn datastart: raden etter "Radetiketter;Kontantbeløp"
    const headerIdx = lines.findIndex((l) => l.includes("Radetiketter"));
    if (headerIdx === -1) return [];

    const REGIONS = new Set([
        "Region Midt-Norge", "Region Nord", "Region Sør", "Region Vest", "Region Øst",
        "Region S\xf8r", "Region \xd8st", // latin-1 varianter
        "Bufdir",
    ]);
    const SKIP = new Set(["Bufetat", "Leie av lokaler og tilknyttede utgifter", "Totalsum"]);

    const rows: FlatRow[] = [];
    let currentRegion = "";

    for (let i = headerIdx + 1; i < lines.length; i++) {
        const cols = lines[i].split(delimiter);
        const name = cols[0]?.trim() || "";

        if (SKIP.has(name)) continue;

        if (REGIONS.has(name)) {
            // Normaliser regionnavnet
            currentRegion = name
                .replace("S\xf8r", "Sør")
                .replace("\xd8st", "Øst");
            continue;
        }

        const amount = parseNOK(cols[1]);

        // Tom institusjonsnavn + beløp = overhead for gjeldende region (f.eks. Bufdir-rad)
        const institutionName = name || (amount !== 0 ? currentRegion : "");
        if (!institutionName || amount === 0) continue;

        rows.push({ region: currentRegion, institution: institutionName, amount, category });
    }

    return rows;
}

/** Enkel navnelikhet (Sørensen–Dice på ord) for BEFS-matching */
export function nameSimilarity(a: string, b: string): number {
    const tokenize = (s: string) =>
        s.toLowerCase()
            .replace(/[(),.]/g, " ")
            .split(/\s+/)
            .filter(Boolean);
    const ta = new Set(tokenize(a));
    const tb = new Set(tokenize(b));
    const intersection = [...ta].filter((t) => tb.has(t)).length;
    return (2 * intersection) / (ta.size + tb.size);
}
