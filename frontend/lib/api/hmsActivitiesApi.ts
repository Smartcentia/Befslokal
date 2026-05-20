import { fetchAPI } from './client';

export interface HMSActivityTemplate {
    template_id: string;
    name: string;
    description?: string;
    category: string;
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
    checklist_template_id?: string;
    created_by?: string;
    is_published: boolean;
    adoption_count: number;
    created_at: string;
    updated_at: string;
}

export interface ScheduledActivity {
    activity_id: string;
    property_id: string;
    property_name?: string;
    template_id?: string;
    template_name?: string;
    name: string;
    description?: string;
    category: string;
    scheduled_date: string;
    due_date: string;
    status: 'scheduled' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
    assigned_to?: string;
    completed_at?: string;
    completed_by?: string;
    notes?: string;
    created_at: string;
}

export interface CreateActivityTemplatePayload {
    name: string;
    description?: string;
    category: string;
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
    checklist_template_id?: string;
}

export interface UpdateActivityTemplatePayload {
    name?: string;
    description?: string;
    category?: string;
    frequency?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
    checklist_template_id?: string;
}

export interface CreateCustomActivityPayload {
    property_id: string;
    name: string;
    description?: string;
    category: string;
    scheduled_date: string;
    due_date: string;
    assigned_to?: string;
}

export interface GenerateActivitiesPayload {
    property_ids: string[];
    template_ids: string[];
    start_date: string;
    end_date: string;
}

export async function getActivityTemplates(): Promise<HMSActivityTemplate[]> {
    return fetchAPI<HMSActivityTemplate[]>('/hms/activities/templates');
}

export async function createActivityTemplate(payload: CreateActivityTemplatePayload): Promise<HMSActivityTemplate> {
    return fetchAPI<HMSActivityTemplate>('/hms/activities/templates', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function updateActivityTemplate(
    templateId: string,
    payload: UpdateActivityTemplatePayload
): Promise<HMSActivityTemplate> {
    return fetchAPI<HMSActivityTemplate>(`/hms/activities/templates/${templateId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
    });
}

export async function deleteActivityTemplate(templateId: string): Promise<void> {
    await fetchAPI(`/hms/activities/templates/${templateId}`, { method: 'DELETE' });
}

export async function publishActivityTemplate(templateId: string): Promise<{ status: string }> {
    return fetchAPI(`/hms/activities/templates/${templateId}/publish`, { method: 'POST' });
}

export async function adoptActivityTemplate(templateId: string): Promise<{ status: string }> {
    return fetchAPI(`/hms/activities/templates/${templateId}/adopt`, { method: 'POST' });
}

export async function getScheduledActivities(params: {
    property_id?: string;
    status?: string;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
} = {}): Promise<ScheduledActivity[]> {
    const searchParams = new URLSearchParams();
    if (params.property_id) searchParams.set('property_id', params.property_id);
    if (params.status) searchParams.set('status', params.status);
    if (params.from_date) searchParams.set('from_date', params.from_date);
    if (params.to_date) searchParams.set('to_date', params.to_date);
    if (params.skip !== undefined) searchParams.set('skip', String(params.skip));
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));

    const query = searchParams.toString();
    return fetchAPI<ScheduledActivity[]>(`/hms/activities/scheduled${query ? `?${query}` : ''}`);
}

export async function getScheduledActivitiesByProperty(propertyId: string): Promise<ScheduledActivity[]> {
    return fetchAPI<ScheduledActivity[]>(`/hms/activities/scheduled/property/${propertyId}`);
}

export async function getUpcomingActivities(days: number = 30): Promise<ScheduledActivity[]> {
    return fetchAPI<ScheduledActivity[]>(`/hms/activities/upcoming?days=${days}`);
}

export async function createCustomActivity(payload: CreateCustomActivityPayload): Promise<ScheduledActivity> {
    return fetchAPI<ScheduledActivity>('/hms/activities/custom', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function generateActivities(payload: GenerateActivitiesPayload): Promise<{
    status: string;
    generated: number;
    activities: ScheduledActivity[];
}> {
    return fetchAPI('/hms/activities/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}

export async function triggerActivity(activityId: string): Promise<{ status: string }> {
    return fetchAPI(`/hms/activities/scheduled/${activityId}/trigger`, { method: 'POST' });
}

export async function publishActivityToHub(activityId: string): Promise<{ status: string }> {
    return fetchAPI(`/hms/activities/scheduled/${activityId}/publish-to-hub`, { method: 'POST' });
}

export async function deactivateActivity(activityId: string): Promise<void> {
    await fetchAPI(`/hms/activities/scheduled/${activityId}`, { method: 'DELETE' });
}

export async function processDueActivities(): Promise<{ processed: number }> {
    return fetchAPI('/hms/activities/process-due', { method: 'POST' });
}

export const hmsActivitiesApi = {
    templates: {
        getAll: getActivityTemplates,
        create: createActivityTemplate,
        update: updateActivityTemplate,
        delete: deleteActivityTemplate,
        publish: publishActivityTemplate,
        adopt: adoptActivityTemplate,
    },
    scheduled: {
        getAll: getScheduledActivities,
        getByProperty: getScheduledActivitiesByProperty,
        getUpcoming: getUpcomingActivities,
        createCustom: createCustomActivity,
        generate: generateActivities,
        trigger: triggerActivity,
        publishToHub: publishActivityToHub,
        deactivate: deactivateActivity,
        processDue: processDueActivities,
    },
};
