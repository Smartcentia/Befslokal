import { fetchAPI } from "./client";

/** Første ledd i SSB paths (emne/hierarki). */
export interface SSBPathSegment {
    id?: string;
    label?: string;
    sortCode?: string;
}

export interface SSBTable {
    id: string;
    label: string;
    description?: string;
    variableNames?: string[];
    firstPeriod?: string;
    lastPeriod?: string;
    timeUnit?: string;
    /** Hierarki fra SSB; paths[0][0] brukes ofte som primæremne. */
    paths?: SSBPathSegment[][];
    links?: { rel: string; href: string }[];
    subjectCode?: string;
}

export interface SSBTablesResponse {
    language: string;
    tables: SSBTable[];
    page?: {
        pageNumber: number;
        pageSize: number;
        totalElements: number;
        totalPages: number;
    };
}

export interface SSBDataSelectionItem {
    variableCode: string;
    valueCodes: string[];
}

export interface SSBCombineRequest {
    table_id: string;
    value_codes?: Record<string, string>;
    selection?: SSBDataSelectionItem[];
    befs_dataset: "region_costs" | "properties" | "contracts";
    join_key: "region" | "kommune" | "year";
    year?: number;
}

export type SsbTableSearchOpts = {
    /** Kun kuraterte tabeller (alle eller med category) */
    catalog?: "curated";
    /** f.eks. utdanning, utenforskap — aktiverer kuratert modus når satt */
    category?: string | null;
};

export async function searchTables(
    query?: string,
    page = 1,
    pageSize = 20,
    lang = "no",
    opts?: SsbTableSearchOpts
): Promise<SSBTablesResponse> {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize)); // backend uses snake_case
    params.set("lang", lang);
    if (query) params.set("query", query);
    if (opts?.catalog) params.set("catalog", opts.catalog);
    if (opts?.category) params.set("category", opts.category);
    return fetchAPI<SSBTablesResponse>(`/ssb/tables?${params.toString()}`);
}

export async function getTable(tableId: string, lang = "no"): Promise<SSBTable> {
    return fetchAPI<SSBTable>(`/ssb/tables/${tableId}?lang=${lang}`);
}

export async function getTableMetadata(
    tableId: string,
    lang = "no"
): Promise<Record<string, unknown>> {
    return fetchAPI<Record<string, unknown>>(
        `/ssb/tables/${tableId}/metadata?lang=${lang}`
    );
}

export async function getTableData(
    tableId: string,
    options?: {
        valueCodes?: Record<string, string>;
        outputFormat?: string;
        lang?: string;
    }
): Promise<unknown> {
    const params = new URLSearchParams();
    params.set("output_format", options?.outputFormat ?? "json-stat2");
    params.set("lang", options?.lang ?? "no");
    if (options?.valueCodes) {
        Object.entries(options.valueCodes).forEach(([k, v]) => {
            params.set(`valueCodes[${k}]`, v);
        });
    }
    return fetchAPI<unknown>(`/ssb/tables/${tableId}/data?${params.toString()}`);
}

export async function getTableDataPost(
    tableId: string,
    body: { selection?: SSBDataSelectionItem[] },
    options?: { outputFormat?: string; lang?: string }
): Promise<unknown> {
    const params = new URLSearchParams();
    params.set("output_format", options?.outputFormat ?? "json-stat2");
    params.set("lang", options?.lang ?? "no");
    return fetchAPI<unknown>(`/ssb/tables/${tableId}/data?${params.toString()}`, {
        method: "POST",
        body: JSON.stringify(body),
    });
}

export async function combineSSBBefs(
    req: SSBCombineRequest
): Promise<{ ssb: unknown; befs: { by_key: Record<string, number>; join_key: string; year: number } }> {
    return fetchAPI(`/ssb/combine`, {
        method: "POST",
        body: JSON.stringify(req),
    });
}
