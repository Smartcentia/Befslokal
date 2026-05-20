import { fetchAPI } from './client';

export interface MfaLinkResponse {
    status: string;
    message: string;
    expires_in_minutes: number;
}

export interface MfaVerifyResponse {
    status: 'success' | 'invalid' | 'expired';
    user_email?: string;
    message: string;
}

export async function sendMfaLink(email: string): Promise<MfaLinkResponse> {
    return fetchAPI<MfaLinkResponse>('/auth/send-mfa-link', {
        method: 'POST',
        body: JSON.stringify({ email }),
    });
}

export async function verifyMfaToken(token: string): Promise<MfaVerifyResponse> {
    return fetchAPI<MfaVerifyResponse>(`/auth/verify-mfa/${token}`);
}

export const mfaApi = {
    sendLink: sendMfaLink,
    verify: verifyMfaToken,
};
