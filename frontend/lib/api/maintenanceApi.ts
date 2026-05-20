import { fetchAPI } from './client';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface MaintenancePlan {
    plan_id: string;
    property_id: string;
    component_id?: string | null;
    title: string;
    description?: string | null;
    category: string;
    frequency_months: number;
    responsible_role: string;
    estimated_cost_nok?: number | null;
    ns3451_code?: string | null;
    last_performed_date?: string | null;
    next_due_date?: string | null;
    is_active: boolean;
    created_at: string;
}

export interface MaintenanceTask {
    task_id: string;
    plan_id: string;
    property_id: string;
    component_id?: string | null;
    title: string;
    description?: string | null;
    due_date: string;
    status: string; // pending|in_progress|completed|overdue|cancelled|skipped
    assigned_to_user_id?: string | null;
    completed_at?: string | null;
    completion_notes?: string | null;
    actual_cost_nok?: number | null;
    created_at: string;
}

export interface MaintenanceSummary {
    property_id: string;
    plans_active: number;
    tasks_total: number;
    tasks_pending: number;
    tasks_overdue: number;
    tasks_completed: number;
    next_due_title?: string | null;
    next_due_date?: string | null;
}

export interface PlanCreate {
    property_id: string;
    component_id?: string | null;
    title: string;
    description?: string | null;
    category?: string;
    frequency_months: number;
    responsible_role?: string;
    estimated_cost_nok?: number | null;
    ns3451_code?: string | null;
    last_performed_date?: string | null;
}

export interface TaskUpdate {
    status?: string;
    completion_notes?: string;
    actual_cost_nok?: number;
}

// ─────────────────────────────────────────────
// API functions
// ─────────────────────────────────────────────

export async function getMaintenancePlans(propertyId: string, activeOnly = true): Promise<MaintenancePlan[]> {
    try {
        return await fetchAPI(`/fdvu/maintenance/plans?property_id=${propertyId}&active_only=${activeOnly}`);
    } catch { return []; }
}

export async function createMaintenancePlan(body: PlanCreate): Promise<MaintenancePlan> {
    return fetchAPI('/fdvu/maintenance/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export async function updateMaintenancePlan(planId: string, body: Partial<PlanCreate & { is_active: boolean }>): Promise<MaintenancePlan> {
    return fetchAPI(`/fdvu/maintenance/plans/${planId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export async function deleteMaintenancePlan(planId: string): Promise<void> {
    await fetchAPI(`/fdvu/maintenance/plans/${planId}`, { method: 'DELETE' });
}

export async function generateTasks(planId: string, horizonMonths = 12): Promise<{ created: number }> {
    return fetchAPI(`/fdvu/maintenance/plans/${planId}/generate-tasks?horizon_months=${horizonMonths}`, {
        method: 'POST',
    });
}

export async function getMaintenanceTasks(propertyId: string, status?: string): Promise<MaintenanceTask[]> {
    try {
        const qs = new URLSearchParams({ property_id: propertyId });
        if (status) qs.set('status', status);
        return await fetchAPI(`/fdvu/maintenance/tasks?${qs}`);
    } catch { return []; }
}

export async function updateMaintenanceTask(taskId: string, body: TaskUpdate): Promise<MaintenanceTask> {
    return fetchAPI(`/fdvu/maintenance/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export async function getMaintenanceSummary(propertyId: string): Promise<MaintenanceSummary | null> {
    try {
        return await fetchAPI(`/fdvu/maintenance/summary/${propertyId}`);
    } catch { return null; }
}
