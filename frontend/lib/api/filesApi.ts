import { fetchAPI, API_BASE_URL } from './client';

export interface FileMetadata {
    file_id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    property_id?: string;
    contract_id?: string;
    uploaded_by?: string;
    created_at: string;
    tags?: string[];
}

export interface SasUploadResponse {
    sas_url: string;
    blob_name: string;
    container: string;
    expires_at: string;
}

export interface UploadCompletePayload {
    blob_name: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    property_id?: string;
    contract_id?: string;
    tags?: string[];
}

export interface ScanResult {
    status: string;
    new_files: number;
    updated_files: number;
    errors: string[];
}

export async function getSasUploadUrl(
    filename: string,
    contentType: string
): Promise<SasUploadResponse> {
    return fetchAPI<SasUploadResponse>('/files/upload/sas', {
        method: 'POST',
        body: JSON.stringify({ filename, content_type: contentType }),
    });
}

export async function completeUpload(payload: UploadCompletePayload): Promise<FileMetadata> {
    return fetchAPI<FileMetadata>('/files/upload/complete', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function uploadFileDirect(
    file: File,
    propertyId?: string,
    contractId?: string
): Promise<FileMetadata> {
    const formData = new FormData();
    formData.append('file', file);
    if (propertyId) formData.append('property_id', propertyId);
    if (contractId) formData.append('contract_id', contractId);

    return fetchAPI<FileMetadata>('/files/upload', {
        method: 'POST',
        body: formData,
    });
}

export async function getFileMetadata(fileId: string): Promise<FileMetadata> {
    return fetchAPI<FileMetadata>(`/files/${fileId}/metadata`);
}

export function getFileDownloadUrl(fileId: string): string {
    return `${API_BASE_URL}/files/${fileId}/download`;
}

export async function scanFiles(): Promise<ScanResult> {
    return fetchAPI<ScanResult>('/files/scan', { method: 'POST' });
}

export const filesApi = {
    getSasUrl: getSasUploadUrl,
    completeUpload,
    uploadDirect: uploadFileDirect,
    getMetadata: getFileMetadata,
    getDownloadUrl: getFileDownloadUrl,
    scan: scanFiles,
};
