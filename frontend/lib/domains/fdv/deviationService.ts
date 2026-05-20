import { fetchAPI, API_BASE_URL, getApiAuthContext } from '../../api/client';

export interface Deviation {
    id: string;
    title: string;
    description?: string;
    status: string;
    property_id: string;
    property_name?: string;
    severity: string; // "critical", "high", "medium", "low"
    created_at: string;
}

export interface DeviationImage {
    file_id: string;
    original_filename: string | null;
    download_url: string;
    created_at: string;
}

export interface AiAssessmentResult {
    alvorlighetsgrad: 'kritisk' | 'høy' | 'middels' | 'lav' | string;
    sammendrag: string;
    anbefalte_tiltak: string[];
    estimert_kostnad_nok: number | null;
}

export interface CreateDeviationDTO {
    title: string;
    description: string;
    property_id: string;
    priority: string; // "high", "medium", "low"
    due_date?: string;
}

export const deviationService = {
    getAll: async (page: number = 1, limit: number = 50, status?: string): Promise<Deviation[]> => {
        try {
            const offset = (page - 1) * limit;
            const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
            if (status) params.set('status', status);
            return await fetchAPI(`/deviations?${params.toString()}`);
        } catch (error) {
            console.warn("Failed to fetch deviations", error);
            return [];
        }
    },
    getById: async (id: string): Promise<Deviation | null> => {
        try {
            return await fetchAPI(`/deviations/${id}`);
        } catch (error) {
            console.warn(`Failed to fetch deviation ${id}`, error);
            return null;
        }
    },
    create: async (data: CreateDeviationDTO): Promise<Deviation> => {
        return await fetchAPI('/deviations', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    getStats: async (): Promise<any> => {
        try {
            return await fetchAPI('/deviations/stats');
        } catch (error) {
            console.warn("Failed to fetch deviation stats", error);
            return null;
        }
    },

    uploadImage: async (caseId: string, file: File): Promise<DeviationImage> => {
        const { headers } = await getApiAuthContext();
        const formData = new FormData();
        formData.append('file', file);
        const resp = await fetch(`${API_BASE_URL}/deviations/${caseId}/images`, {
            method: 'POST',
            headers: {
                // Content-Type settes automatisk av nettleseren for FormData (multipart boundary)
                Authorization: headers['Authorization'] ?? '',
                'X-User-Email': headers['X-User-Email'] ?? '',
            },
            body: formData,
        });
        if (!resp.ok) {
            const msg = await resp.text();
            throw new Error(`Bildeopplasting feilet (${resp.status}): ${msg}`);
        }
        return resp.json();
    },

    getImages: async (caseId: string): Promise<DeviationImage[]> => {
        try {
            return await fetchAPI(`/deviations/${caseId}/images`);
        } catch (error) {
            console.warn("Kunne ikke hente bilder for avvik", error);
            return [];
        }
    },

    getAiAssessment: async (caseId: string): Promise<AiAssessmentResult> => {
        return await fetchAPI(`/deviations/${caseId}/ai-assess`, { method: 'POST' });
    },
};
