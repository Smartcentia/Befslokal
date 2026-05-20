import { fetchAPI } from './client';

export interface ImportAnalysis {
    status: 'valid' | 'invalid' | 'warnings';
    row_count: number;
    columns: string[];
    column_mapping: Record<string, string>;
    sample_rows: Array<Record<string, unknown>>;
    warnings: string[];
    errors: string[];
}

export interface ImportResult {
    status: 'success' | 'partial' | 'failed';
    imported: number;
    updated: number;
    failed: number;
    errors: Array<{ row: number; error: string }>;
}

export interface Edon2ImportResult {
    status: string;
    properties_imported: number;
    contracts_imported: number;
    parties_imported: number;
    errors: string[];
}

export async function analyzeImport(
    file: File,
    entityType: string
): Promise<ImportAnalysis> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('entity_type', entityType);

    return fetchAPI<ImportAnalysis>('/import/analyze', {
        method: 'POST',
        body: formData,
    });
}

export async function executeImport(
    file: File,
    entityType: string,
    columnMapping: Record<string, string>,
    options?: {
        update_existing?: boolean;
        dry_run?: boolean;
    }
): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('entity_type', entityType);
    formData.append('column_mapping', JSON.stringify(columnMapping));
    if (options?.update_existing !== undefined) {
        formData.append('update_existing', String(options.update_existing));
    }
    if (options?.dry_run !== undefined) {
        formData.append('dry_run', String(options.dry_run));
    }

    return fetchAPI<ImportResult>('/import/execute', {
        method: 'POST',
        body: formData,
    });
}

export async function importEdon2(file: File): Promise<Edon2ImportResult> {
    const formData = new FormData();
    formData.append('file', file);

    return fetchAPI<Edon2ImportResult>('/import/edon2', {
        method: 'POST',
        body: formData,
    });
}

export const importApi = {
    analyze: analyzeImport,
    execute: executeImport,
    edon2: importEdon2,
};
