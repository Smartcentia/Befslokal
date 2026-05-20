import { fetchAPI } from '@/lib/api/client';

export interface DocSearchResult {
    document_id: string;
    title: string;
    document_type: string;
    property_id: string;
    similarity: number;
    excerpt: string | null;
}

export interface FdvDocumentWithStatus {
    document_id: string;
    title: string;
    document_type: string;
    extraction_status: 'pending' | 'processing' | 'done' | 'failed';
    page_count: number | null;
    extracted_text?: string;
    file_path?: string;
    external_url?: string;
    created_at: string;
}

export async function searchFdvDocuments(
    q: string,
    propertyId?: string,
    limit: number = 10,
): Promise<DocSearchResult[]> {
    const params = new URLSearchParams({ q, limit: String(limit) });
    if (propertyId) params.set('property_id', propertyId);
    return fetchAPI<DocSearchResult[]>(`/fdvu/documents/search?${params.toString()}`);
}

export async function processDocument(documentId: string): Promise<{ status: string }> {
    return fetchAPI<{ status: string }>(`/fdvu/documents/${documentId}/process`, {
        method: 'POST',
    });
}

export async function processAllDocuments(propertyId: string): Promise<{ queued: number }> {
    return fetchAPI<{ queued: number }>(
        `/fdvu/documents/process-all?property_id=${propertyId}`,
        { method: 'POST' },
    );
}

export async function getDocumentText(
    documentId: string,
): Promise<{ text: string; page_count: number }> {
    const res = await fetchAPI<{ text: string; page_count: number | null }>(
        `/fdvu/documents/${documentId}/text`,
    );
    return { text: res.text ?? '', page_count: res.page_count ?? 0 };
}
