import { fetchAPI } from './client';

export interface IndexingStatus {
    status: 'idle' | 'running' | 'completed' | 'failed';
    last_run: string;
    total_documents: number;
    documents_indexed: number;
    documents_pending: number;
    errors: number;
    estimated_completion?: string;
}

export interface BatchIndexResult {
    status: string;
    triggered: number;
    message: string;
}

export async function triggerBatchIndex(
    documentIds?: string[]
): Promise<BatchIndexResult> {
    return fetchAPI<BatchIndexResult>('/indexing/batch-index', {
        method: 'POST',
        body: JSON.stringify({ document_ids: documentIds }),
    });
}

export async function getIndexingStatus(): Promise<IndexingStatus> {
    return fetchAPI<IndexingStatus>('/indexing/indexing-status');
}

export const indexingApi = {
    triggerBatch: triggerBatchIndex,
    status: getIndexingStatus,
};
