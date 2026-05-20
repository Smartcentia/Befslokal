import { fetchAPI } from './client';

export interface MediaMonitoringResult {
    party_id: string;
    party_name: string;
    sentiment_score: number;
    sentiment_label: 'Negativt' | 'Nøytralt' | 'Positivt';
    summary: string;
    red_flags: string[];
    positive_news: string[];
    sources_checked: number;
    last_updated: string;
}

export interface MediaMonitorRanking {
    parties: Array<{
        party_id: string;
        party_name: string;
        orgnr?: string;
        sentiment_score: number;
        sentiment_label: string;
        trend: 'improving' | 'stable' | 'declining';
    }>;
    last_run: string;
}

export interface MediaMonitorStatus {
    status: 'idle' | 'running' | 'completed' | 'failed';
    last_run: string;
    parties_checked: number;
    errors: number;
}

export async function getMediaMonitorRanking(): Promise<MediaMonitorRanking> {
    return fetchAPI<MediaMonitorRanking>('/media-monitor/ranking');
}

export async function runMediaMonitorAll(): Promise<{ status: string; message: string }> {
    return fetchAPI('/media-monitor/run-all', { method: 'POST' });
}

export async function runMediaMonitorSingle(partyId: string): Promise<MediaMonitoringResult> {
    return fetchAPI<MediaMonitoringResult>(`/media-monitor/run/${partyId}`, { method: 'POST' });
}

export async function getMediaMonitorStatus(): Promise<MediaMonitorStatus> {
    return fetchAPI<MediaMonitorStatus>('/media-monitor/status');
}

export const mediaMonitorApi = {
    ranking: getMediaMonitorRanking,
    runAll: runMediaMonitorAll,
    runSingle: runMediaMonitorSingle,
    status: getMediaMonitorStatus,
};
