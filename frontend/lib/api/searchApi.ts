import { fetchAPI } from './client';

export interface VectorSearchResult {
    document_id: string;
    content: string;
    score: number;
    metadata: {
        source?: string;
        property_id?: string;
        file_name?: string;
        page_number?: number;
    };
}

export interface VectorSearchResponse {
    results: VectorSearchResult[];
    total: number;
    query: string;
    processing_time_ms: number;
}

export interface GlobalSearchResult {
    type: 'property' | 'contract' | 'party' | 'deviation' | 'document';
    id: string;
    title: string;
    description?: string;
    score: number;
    metadata?: Record<string, unknown>;
}

export interface GlobalSearchResponse {
    results: GlobalSearchResult[];
    total: number;
    query: string;
    facets?: {
        by_type: Record<string, number>;
    };
}

export interface VectorSearchStatus {
    status: 'ready' | 'indexing' | 'unavailable';
    total_documents: number;
    last_indexed: string;
    index_size_mb: number;
}

export interface FulltextSearchResult {
    id: string;
    entity_type: string;
    title: string;
    content_preview: string;
    score: number;
    highlights: string[];
}

export interface FulltextSearchResponse {
    results: FulltextSearchResult[];
    total: number;
    page: number;
    page_size: number;
}

export interface SearchStats {
    total_indexed: number;
    by_type: Record<string, number>;
    last_reindex: string;
    index_health: 'healthy' | 'degraded' | 'rebuilding';
}

export async function vectorSearch(
    query: string,
    options: {
        limit?: number;
        property_id?: string;
        file_type?: string;
    } = {}
): Promise<VectorSearchResponse> {
    return fetchAPI<VectorSearchResponse>('/search/vector', {
        method: 'POST',
        body: JSON.stringify({
            query,
            limit: options.limit ?? 10,
            property_id: options.property_id,
            file_type: options.file_type,
        }),
    });
}

export async function getVectorSearchStatus(): Promise<VectorSearchStatus> {
    return fetchAPI<VectorSearchStatus>('/search/vector/status');
}

export async function indexDocument(fileId: string): Promise<{ status: string; chunks: number }> {
    return fetchAPI(`/search/index/${fileId}`, { method: 'POST' });
}

export async function globalSearch(
    query: string,
    options: {
        limit?: number;
        types?: string[];
    } = {}
): Promise<GlobalSearchResponse> {
    const params = new URLSearchParams({ q: query });
    if (options.limit) params.set('limit', String(options.limit));
    if (options.types?.length) params.set('types', options.types.join(','));

    return fetchAPI<GlobalSearchResponse>(`/search/global?${params}`);
}

export async function fulltextSearch(
    query: string,
    options: {
        page?: number;
        page_size?: number;
        entity_types?: string[];
    } = {}
): Promise<FulltextSearchResponse> {
    return fetchAPI<FulltextSearchResponse>('/fulltext-search/search/fulltext', {
        method: 'POST',
        body: JSON.stringify({
            query,
            page: options.page ?? 1,
            page_size: options.page_size ?? 20,
            entity_types: options.entity_types,
        }),
    });
}

export async function getSearchStats(): Promise<SearchStats> {
    return fetchAPI<SearchStats>('/fulltext-search/search/stats');
}

export const searchApi = {
    vector: {
        search: vectorSearch,
        status: getVectorSearchStatus,
        indexDocument,
    },
    global: globalSearch,
    fulltext: {
        search: fulltextSearch,
        stats: getSearchStats,
    },
};
