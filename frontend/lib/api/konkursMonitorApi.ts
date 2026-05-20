import { fetchAPI } from './client';
import type { KonkursStatusEntry } from '../services/coreService';

export type { KonkursStatusEntry };

export async function getKonkursFlaggedParties(): Promise<KonkursStatusEntry[]> {
    return fetchAPI<KonkursStatusEntry[]>('/konkurs-monitor/flagged');
}

export async function runKonkursCheckAll(): Promise<{ status: string; message: string }> {
    return fetchAPI('/konkurs-monitor/run-all', { method: 'POST' });
}

export async function runKonkursCheckSingle(partyId: string): Promise<KonkursStatusEntry | null> {
    return fetchAPI<KonkursStatusEntry | null>(`/konkurs-monitor/run/${partyId}`, { method: 'POST' });
}

export async function getKonkursRunStatus(): Promise<Record<string, unknown>> {
    return fetchAPI('/konkurs-monitor/status');
}

export const konkursMonitorApi = {
    flagged: getKonkursFlaggedParties,
    runAll: runKonkursCheckAll,
    runSingle: runKonkursCheckSingle,
    status: getKonkursRunStatus,
};
