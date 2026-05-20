import { fetchAPI } from '../../api/client';

export interface VectorSearchResult {
    text: string;
    score: number;
    metadata: any;
}

export interface SearchResultItem {
    id: string;
    type: 'property' | 'contract' | 'deviation';
    title: string;
    subtitle?: string;
    url: string;
    status?: string;
}

export interface GlobalSearchResponse {
    query: string;
    results: SearchResultItem[];
}

export const searchService = {
    vectorSearch: async (query: string): Promise<VectorSearchResult[]> => {
        try {
            const res = await fetchAPI('/search/vector', {
                method: 'POST',
                body: JSON.stringify({ query, n_results: 5 })
            });
            return res.results || [];
        } catch (error) {
            console.warn("Vector search failed", error);
            return [];
        }
    },

    globalSearch: async (query: string): Promise<SearchResultItem[]> => {
        try {
            const res = await fetchAPI(`/search/global?q=${encodeURIComponent(query)}&limit=8`);
            return res.results || [];
        } catch (error) {
            console.warn("Global search failed", error);
            return [];
        }
    }
};
