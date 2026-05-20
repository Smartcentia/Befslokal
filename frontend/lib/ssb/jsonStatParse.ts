/**
 * Flater ut SSB PxWebApi json-stat2 til tabellrader (samme rekkefølge som backend / KI-verktøy).
 * @see https://json-stat.org/
 */

export interface JsonStatDimensionParsed {
    key: string;
    label: string;
    codes: string[];
    /** Kode → visningsnavn */
    codeToLabel: Map<string, string>;
}

export interface JsonStatRole {
    time?: string[];
    metric?: string[];
    geo?: string[];
}

export interface FlattenedJsonStat {
    /** Datasett-tittel fra json-stat, om satt */
    datasetLabel?: string;
    /** json-stat2 `role` – brukes til diagram (tid / måling) */
    role?: JsonStatRole;
    dimensionKeys: string[];
    dimensions: JsonStatDimensionParsed[];
    /** Kolonnenavn = dimensionKeys + verdiKey */
    rows: Array<Record<string, string | number | null>>;
    valueKey: string;
    rowCount: number;
    totalValueSlots: number;
    truncated: boolean;
    maxRows: number;
    /** true hvis value.length ikke matcher forventet produkt av dimensjoner */
    sizeMismatchWarning?: string;
}

const DEFAULT_VALUE_KEY = "verdi";

function readCategoryMaps(dim: Record<string, unknown>): {
    codes: string[];
    codeToLabel: Map<string, string>;
} {
    const cat = (dim.category as Record<string, unknown>) || {};
    const idxRaw = cat.index;
    const lblRaw = cat.label;

    const codeToLabel = new Map<string, string>();

    if (idxRaw && typeof idxRaw === "object" && !Array.isArray(idxRaw)) {
        const idxMap = idxRaw as Record<string, number>;
        const lblMap =
            lblRaw && typeof lblRaw === "object" && !Array.isArray(lblRaw)
                ? (lblRaw as Record<string, string>)
                : {};
        const codes = Object.keys(idxMap).sort(
            (a, b) => (idxMap[a] ?? 0) - (idxMap[b] ?? 0)
        );
        for (const code of codes) {
            codeToLabel.set(code, lblMap[code] ?? code);
        }
        return { codes, codeToLabel };
    }

    if (Array.isArray(idxRaw)) {
        const codes = idxRaw.map(String);
        const lblArr = Array.isArray(lblRaw) ? lblRaw.map(String) : [];
        codes.forEach((c, i) => {
            codeToLabel.set(c, lblArr[i] ?? c);
        });
        return { codes, codeToLabel };
    }

    return { codes: [], codeToLabel: new Map() };
}

export function isJsonStatLike(data: unknown): data is Record<string, unknown> {
    if (!data || typeof data !== "object") return false;
    const o = data as Record<string, unknown>;
    return (
        Array.isArray(o.value) &&
        Array.isArray(o.id) &&
        typeof o.dimension === "object" &&
        o.dimension !== null
    );
}

/**
 * Flater ut json-stat2-datasett til én rad per celle med alle dimensjonsverdier + tallverdi.
 */
export function flattenJsonStat2(
    dataset: Record<string, unknown>,
    options?: { maxRows?: number; valueKey?: string }
): FlattenedJsonStat {
    const maxRows = options?.maxRows ?? 8000;
    const valueKey = options?.valueKey ?? DEFAULT_VALUE_KEY;

    const value = dataset.value as Array<number | null> | undefined;
    const id = dataset.id as string[] | undefined;
    const dimension = dataset.dimension as Record<string, unknown> | undefined;
    const datasetLabel =
        typeof dataset.label === "string" ? dataset.label : undefined;

    const roleRaw = dataset.role as Record<string, string[] | undefined> | undefined;
    const role: JsonStatRole | undefined =
        roleRaw && typeof roleRaw === "object"
            ? {
                  time: roleRaw.time,
                  metric: roleRaw.metric,
                  geo: roleRaw.geo,
              }
            : undefined;

    if (!value || !id || !dimension) {
        throw new Error("Ugyldig json-stat: mangler value, id eller dimension");
    }

    const dimensions: JsonStatDimensionParsed[] = [];
    for (const key of id) {
        const d = dimension[key] as Record<string, unknown> | undefined;
        const dimLabel =
            typeof d?.label === "string" ? d.label : key;
        const { codes, codeToLabel } = readCategoryMaps(d || {});
        dimensions.push({
            key,
            label: dimLabel,
            codes,
            codeToLabel,
        });
    }

    let expected = 1;
    for (const dim of dimensions) {
        expected *= Math.max(1, dim.codes.length);
    }

    const sizeMismatchWarning =
        expected !== value.length
            ? `Forventet ${expected} verdier ut fra dimensjoner, men fikk ${value.length} (kan være sparse data).`
            : undefined;

    const rows: Array<Record<string, string | number | null>> = [];
    let valIdx = 0;

    function walk(di: number, acc: string[]) {
        if (rows.length >= maxRows) return;
        if (di >= dimensions.length) {
            const v = value[valIdx];
            const row: Record<string, string | number | null> = {
                [valueKey]: v ?? null,
            };
            for (let i = 0; i < dimensions.length; i++) {
                const dim = dimensions[i];
                const code = acc[i];
                row[dim.key] = dim.codeToLabel.get(code) ?? code;
            }
            rows.push(row);
            valIdx += 1;
            return;
        }
        const dim = dimensions[di];
        for (const code of dim.codes) {
            if (rows.length >= maxRows) return;
            walk(di + 1, [...acc, code]);
        }
    }

    walk(0, []);

    const truncated = valIdx < expected && rows.length >= maxRows;

    return {
        datasetLabel,
        role,
        dimensionKeys: [...id],
        dimensions,
        rows,
        valueKey,
        rowCount: rows.length,
        totalValueSlots: expected,
        truncated,
        maxRows,
        sizeMismatchWarning,
    };
}

export function rowsToCsv(
    rows: Array<Record<string, string | number | null>>,
    columns: string[]
): string {
    const esc = (v: string | number | null) => {
        if (v === null || v === undefined) return "";
        const s = String(v);
        if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
        return s;
    };
    const header = columns.map(esc).join(";");
    const lines = rows.map((r) => columns.map((c) => esc(r[c] ?? "")).join(";"));
    return [header, ...lines].join("\n");
}

export function summarizeNumericValues(
    rows: Array<Record<string, string | number | null>>,
    valueKey: string
): { min: number; max: number; sum: number; count: number } | null {
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    let sum = 0;
    let count = 0;
    for (const r of rows) {
        const v = r[valueKey];
        if (typeof v !== "number" || Number.isNaN(v)) continue;
        count += 1;
        sum += v;
        if (v < min) min = v;
        if (v > max) max = v;
    }
    if (count === 0) return null;
    return { min, max, sum, count };
}

/** Laveste/høyeste avvik etter IQR (tukey) – innen samme gruppe (alle ikke-tid dimensjoner) */
export type OutlierFlag = "lav" | "høy";

function quantileSorted(sorted: number[], q: number): number {
    if (sorted.length === 0) return Number.NaN;
    const pos = (sorted.length - 1) * q;
    const base = Math.floor(pos);
    const rest = pos - base;
    if (sorted[base + 1] === undefined) return sorted[base];
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
}

/**
 * Løser tidsnøkkel fra json-stat role eller vanlige navn.
 */
export function resolveTimeDimensionKey(parsed: FlattenedJsonStat): string | null {
    const t = parsed.role?.time?.[0];
    if (t && parsed.dimensionKeys.includes(t)) return t;
    const exact = parsed.dimensionKeys.find(
        (k) => k.toLowerCase() === "tid" || k.toLowerCase() === "time"
    );
    if (exact) return exact;
    return (
        parsed.dimensionKeys.find((k) =>
            /år|periode|uke|måned|kvartal|month|year|quarter/i.test(k)
        ) ?? null
    );
}

function groupKeyFromRow(
    row: Record<string, string | number | null>,
    dimensionKeys: string[],
    timeKey: string | null
): string {
    const parts: string[] = [];
    for (const k of dimensionKeys) {
        if (k === timeKey) continue;
        parts.push(`${k}=${String(row[k] ?? "")}`);
    }
    return parts.join("|");
}

function parseTimeSortKey(label: string): number {
    const m = String(label).match(/(\d{4})/);
    if (m) return parseInt(m[1], 10);
    const n = parseFloat(String(label).replace(",", "."));
    return Number.isFinite(n) ? n : 0;
}

export interface RowAnalytics {
    /** År-for-år endring i % (samme gruppe, forrige tidsperiode) */
    yoyPct: number | null;
    /** Indeks med basis = første tidsperiode i gruppen (= 100) */
    index100: number | null;
    /** Tukey-IQR utenfor gruppen (alle observasjoner i gruppen) */
    outlier: OutlierFlag | null;
}

/**
 * Beregner YoY, indeks (basis første tid i gruppe) og IQR-avvik per rad.
 * Krever at `timeKey` er satt; ellers returneres «tom» analyse.
 */
export function computeRowAnalytics(
    rows: Array<Record<string, string | number | null>>,
    dimensionKeys: string[],
    valueKey: string,
    timeKey: string | null
): RowAnalytics[] {
    const n = rows.length;
    const empty = (): RowAnalytics[] =>
        Array.from({ length: n }, () => ({
            yoyPct: null,
            index100: null,
            outlier: null,
        }));

    if (!timeKey || n === 0) return empty();

    const byGroup = new Map<string, number[]>();
    for (let i = 0; i < n; i++) {
        const g = groupKeyFromRow(rows[i], dimensionKeys, timeKey);
        if (!byGroup.has(g)) byGroup.set(g, []);
        byGroup.get(g)!.push(i);
    }

    const yoyPct: (number | null)[] = Array(n).fill(null);
    const index100: (number | null)[] = Array(n).fill(null);
    const outlier: (OutlierFlag | null)[] = Array(n).fill(null);

    for (const indices of byGroup.values()) {
        const sorted = [...indices].sort(
            (a, b) =>
                parseTimeSortKey(String(rows[a][timeKey] ?? "")) -
                parseTimeSortKey(String(rows[b][timeKey] ?? ""))
        );

        const vals: number[] = [];
        for (const i of sorted) {
            const v = rows[i][valueKey];
            if (typeof v === "number" && !Number.isNaN(v)) vals.push(v);
        }
        vals.sort((a, b) => a - b);
        let q1 = quantileSorted(vals, 0.25);
        let q3 = quantileSorted(vals, 0.75);
        let iqr = q3 - q1;
        if (!Number.isFinite(iqr) || iqr === 0) {
            q1 = q3 = iqr = Number.NaN;
        }
        const low = Number.isFinite(q1) ? q1 - 1.5 * iqr : Number.NaN;
        const high = Number.isFinite(q3) ? q3 + 1.5 * iqr : Number.NaN;
        const minPts = 4;

        let baseVal: number | null = null;
        let prevVal: number | null = null;
        for (let j = 0; j < sorted.length; j++) {
            const i = sorted[j];
            const v = rows[i][valueKey];
            if (typeof v !== "number" || Number.isNaN(v)) continue;

            if (baseVal === null) {
                baseVal = v;
                index100[i] = 100;
                prevVal = v;
            } else {
                if (prevVal !== null && prevVal !== 0) {
                    yoyPct[i] = ((v - prevVal) / prevVal) * 100;
                }
                if (baseVal !== 0) {
                    index100[i] = (v / baseVal) * 100;
                }
                prevVal = v;
            }

            if (vals.length >= minPts && Number.isFinite(low) && Number.isFinite(high)) {
                if (v < low) outlier[i] = "lav";
                else if (v > high) outlier[i] = "høy";
            }
        }
    }

    return Array.from({ length: n }, (_, i) => ({
        yoyPct: yoyPct[i] ?? null,
        index100: index100[i] ?? null,
        outlier: outlier[i] ?? null,
    }));
}
