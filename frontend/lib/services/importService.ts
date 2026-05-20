import { fetchAPI, API_BASE_URL } from '../api/client';

export interface ImportAnalysisResponse {
    total_rows: number;
    new_records: any[];
    conflicts: any[];
    identical: number;
    new_columns: string[];
}

export async function analyzeImport(file: File, type: string): Promise<ImportAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return fetchAPI<ImportAnalysisResponse>(`/import/analyze?type=${type}`, {
        method: 'POST',
        body: formData,
    });
}

export async function executeImport(file: File, type: string, updateConflicts: boolean): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    return fetchAPI<any>(`/import/execute?type=${type}&update_conflicts=${updateConflicts}`, {
        method: 'POST',
        body: formData
    });
}
