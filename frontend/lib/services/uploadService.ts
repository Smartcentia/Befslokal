import { API_BASE_URL, fetchAPI } from '../api/client';

export interface UploadResponse {
    file_id: string;
    path: string;
    message: string;
    indexing_stats?: any;
}

interface SASResponse {
    file_id: string;
    upload_url: string;
    blob_path: string;
}

export const uploadService = {
    /**
     * Upload a file directly to cloud storage using a SAS/presigned URL token.
     * This avoids sending large files through the backend API.
     */
    async uploadFileSAS(file: File, contractId?: string): Promise<UploadResponse> {
        console.log(`[uploadService] Starting SAS upload for ${file.name}`);

        try {
            // 1. Get SAS Token from Backend
            const sasReqBody = {
                filename: file.name,
                content_type: file.type,
                contract_id: contractId || null
            };

            // fetchAPI defaults to JSON content-type
            const sasRes: SASResponse = await fetchAPI('/files/upload/sas', {
                method: 'POST',
                body: JSON.stringify(sasReqBody)
            });

            console.log(`[uploadService] Got SAS URL for blob: ${sasRes.blob_path}`);

            // 2. Upload directly to cloud storage
            // Note: We use native fetch here to avoid our API client wrappers
            const uploadRes = await fetch(sasRes.upload_url, {
                method: 'PUT',
                headers: {
                    'x-ms-blob-type': 'BlockBlob',
                    'Content-Type': file.type || 'application/octet-stream',
                },
                body: file
            });

            if (!uploadRes.ok) {
                console.error(`[uploadService] Blob Upload Failed: ${uploadRes.status} ${uploadRes.statusText}`);
                throw new Error("Failed to upload file to storage.");
            }

            console.log(`[uploadService] Blob Upload Complete. Notifying backend...`);

            // 3. Notify Backend to Register & Index
            const completeReqBody = {
                file_id: sasRes.file_id,
                contract_id: contractId || null,
                blob_path: sasRes.blob_path,
                filename: file.name,
                content_type: file.type
            };

            const completeRes: UploadResponse = await fetchAPI('/files/upload/complete', {
                method: 'POST',
                body: JSON.stringify(completeReqBody)
            });

            return completeRes;

        } catch (error) {
            console.error('[uploadService] SAS Upload Error:', error);
            throw error;
        }
    },

    /**
     * Legacy Upload (through Backend)
     * Kept for fallback or smaller files if needed.
     */
    async uploadFile(file: File, contractId?: string): Promise<UploadResponse> {
        const url = `${API_BASE_URL}/files/upload`;

        const formData = new FormData();
        formData.append('file', file);
        if (contractId) {
            formData.append('contract_id', contractId);
        }

        console.log(`[uploadService] Uploading file via Proxy to: ${url}`);

        try {
            // Note: We deliberately do NOT set Content-Type header.
            // Browser sets it automatically to multipart/form-data with boundary.
            const res = await fetch(url, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const errorBody = await res.text().catch(() => '');
                console.error(`[uploadService] HTTP Error ${res.status}:`, errorBody);
                throw new Error(`Upload failed: ${res.status} ${res.statusText} - ${errorBody}`);
            }

            return await res.json();
        } catch (error) {
            console.error('[uploadService] Network or Parse Error:', error);
            throw error;
        }
    },

    /**
     * Trigger Backend Scanner to find and import files dropped directly in Blob Storage.
     */
    async scanFiles(): Promise<any> {
        console.log('[uploadService] Triggering Backend Scan...');
        return fetchAPI('/files/scan', {
            method: 'POST',
        });
    }
};
