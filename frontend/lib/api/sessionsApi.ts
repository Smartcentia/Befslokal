import { fetchAPI } from './client';

export interface Session {
    session_id: string;
    user_id: string;
    email: string;
    access_token?: string;
    refresh_token?: string;
    expires_at: string;
    created_at: string;
}

export interface CreateSessionPayload {
    user_id: string;
    email: string;
    access_token?: string;
    refresh_token?: string;
    expires_in_seconds?: number;
}

export interface UpdateSessionPayload {
    access_token?: string;
    refresh_token?: string;
    expires_in_seconds?: number;
}

export async function createSession(payload: CreateSessionPayload): Promise<Session> {
    return fetchAPI<Session>('/sessions', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function getSession(sessionId: string): Promise<Session> {
    return fetchAPI<Session>(`/sessions/${sessionId}`);
}

export async function updateSession(
    sessionId: string,
    payload: UpdateSessionPayload
): Promise<Session> {
    return fetchAPI<Session>(`/sessions/${sessionId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
    });
}

export async function deleteSession(sessionId: string): Promise<void> {
    await fetchAPI(`/sessions/${sessionId}`, { method: 'DELETE' });
}

export async function cleanupExpiredSessions(): Promise<{ deleted: number }> {
    return fetchAPI('/sessions-cleanup', { method: 'DELETE' });
}

export const sessionsApi = {
    create: createSession,
    get: getSession,
    update: updateSession,
    delete: deleteSession,
    cleanup: cleanupExpiredSessions,
};
