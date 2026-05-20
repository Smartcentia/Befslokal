import { fetchAPI } from './client';

export interface NS3451Code {
    code: string;
    name: string;
    level: number;
    parent_code?: string;
}

export async function getNS3451Codes(level?: number, parentCode?: string): Promise<NS3451Code[]> {
    try {
        const params = new URLSearchParams();
        if (level) params.append('level', level.toString());
        if (parentCode) params.append('parent_code', parentCode);

        return await fetchAPI<NS3451Code[]>(`/ns3451?${params.toString()}`);
    } catch (error) {
        console.error("Failed to fetch NS 3451 codes:", error);
        return [];
    }
}
