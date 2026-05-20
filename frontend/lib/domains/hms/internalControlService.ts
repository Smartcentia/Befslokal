import { fetchAPI } from '../../api/client';

export interface ChecklistItem {
    task: string;
    responsibility: 'TENANT' | 'LANDLORD' | 'SHARED' | 'UNKNOWN';
    criticality: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    action?: string;
}

export interface InternalControlCase {
    case_id: string;
    property_id?: string;
    title: string;
    description?: string;
    status: string;
    priority: string;
    due_date?: string;
    case_type: string;
    created_at?: string;
    property?: { name?: string; address?: string };
    assigned_user?: { name?: string; email?: string };
    process_data?: {
        checklist?: ChecklistItem[];
        template_id?: string;
        risk_class?: number;
        legal_references?: { title: string, url: string }[];
    };
}

export interface ChecklistTemplate {
    template_id: string;
    title: string;
    description?: string;
    items: { id?: string; label?: string; task?: string; responsibility?: string; criticality?: string }[];
    category: string;
    frequency?: string;
    created_by_user_id?: string | null;
    scope?: string | null;
    created_at?: string;
}

export const internalControlService = {
    async getPropertyCases(propertyId?: string, status?: string, priority?: string): Promise<InternalControlCase[]> {
        const query = new URLSearchParams();
        if (propertyId) query.append('property_id', propertyId);
        if (status) query.append('status', status);
        if (priority) query.append('priority', priority);
        try {
            const res = await fetchAPI(`/internal-control/cases?${query.toString()}`);
            if (Array.isArray(res)) return res;
            return [];
        } catch (e) {
            console.error("Failed to fetch internal control cases", e);
            return [];
        }
    },

    async getCaseById(caseId: string): Promise<InternalControlCase> {
        return fetchAPI(`/internal-control/cases/${caseId}`);
    },

    async completeChecklist(
        caseId: string,
        responses: Record<string, boolean>,
        notes?: string
    ): Promise<InternalControlCase> {
        return fetchAPI(`/internal-control/cases/${caseId}/complete-checklist`, {
            method: 'POST',
            body: JSON.stringify({ responses, notes: notes ?? '' }),
        });
    },

    async createInitialCasesForProperty(propertyId: string): Promise<InternalControlCase[]> {
        const res = await fetchAPI(`/internal-control/cases/create-initial-for-property/${propertyId}`, {
            method: 'POST',
        });
        return Array.isArray(res) ? res : [];
    },

    async createMockCasesForProperty(propertyId: string): Promise<InternalControlCase[]> {
        // This function is likely for development/testing purposes
        // and might not interact with a real API endpoint in the same way.
        // For now, returning an empty array or a mock response.
        console.warn(`createMockCasesForProperty called for propertyId: ${propertyId}. This is a mock implementation.`);
        return [];
    },

    getChecklists: async (scope?: 'my' | 'shared' | 'all'): Promise<ChecklistTemplate[]> => {
        try {
            const q = scope ? `?scope=${scope}` : '';
            const res = await fetchAPI(`/checklists/templates${q}`);
            if (Array.isArray(res)) return res;
            return [];
        } catch (e) {
            console.error("Failed to fetch checklists", e);
            return [];
        }
    },

    createTemplate: async (data: {
        title: string;
        description?: string;
        items: { id?: string; label?: string; task?: string }[];
        category: string;
        frequency?: string;
    }): Promise<ChecklistTemplate> => {
        return fetchAPI('/checklists/templates', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    updateTemplate: async (
        templateId: string,
        data: Partial<{ title: string; description: string; items: unknown[]; category: string; frequency: string }>
    ): Promise<ChecklistTemplate> => {
        return fetchAPI(`/checklists/templates/${templateId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    deleteTemplate: async (templateId: string): Promise<void> => {
        await fetchAPI(`/checklists/templates/${templateId}`, { method: 'DELETE' });
    },

    createCaseFromTemplate: async (templateId: string, propertyId: string): Promise<InternalControlCase> => {
        return fetchAPI('/internal-control/cases/from-template', {
            method: 'POST',
            body: JSON.stringify({ template_id: templateId, property_id: propertyId }),
        });
    },

    submitChecklist: async (execution: any) => {
        return await fetchAPI(`/checklists/executions`, {
            method: 'POST',
            body: JSON.stringify(execution)
        });
    }
};
