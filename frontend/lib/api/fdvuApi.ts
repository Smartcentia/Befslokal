import { fetchAPI } from './client';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface FdvuSection {
    section_id: string;
    property_id: string;
    name: string;
    section_type: string;
    floor?: number | null;
    area_sqm?: number | null;
    capacity?: number | null;
    description?: string | null;
    is_active: boolean;
    created_at: string;
    updated_at?: string | null;
}

export interface Requirement {
    requirement_id: string;
    code: string;
    title: string;
    description?: string | null;
    regulation_set: string;
    category?: string | null;
    applies_to: string;
    is_mandatory: boolean;
    severity_if_breached?: string | null;
    effective_from?: string | null;
    effective_to?: string | null;
    source_url?: string | null;
    created_at: string;
}

export interface ComplianceAssessment {
    assessment_id: string;
    assignment_id: string;
    status: string;
    assessed_at: string;
    assessed_by?: string | null;
    valid_until?: string | null;
    next_review_date?: string | null;
    evidence_notes?: string | null;
    deviation_case_id?: string | null;
    created_at: string;
    updated_at?: string | null;
}

export interface AssignmentWithAssessment {
    assignment_id: string;
    requirement_id: string;
    property_id: string;
    section_id?: string | null;
    is_auto_assigned: boolean;
    notes?: string | null;
    assigned_at: string;
    requirement?: Requirement | null;
    compliance_assessment?: ComplianceAssessment | null;
}

export interface ComplianceSummary {
    property_id: string;
    total_assignments: number;
    compliant: number;
    non_compliant: number;
    partial: number;
    not_assessed: number;
    not_applicable: number;
    overdue_reviews: number;
    compliance_rate: number;
}

export interface FdvDocument {
    document_id: string;
    property_id: string;
    section_id?: string | null;
    document_type: string;
    title: string;
    description?: string | null;
    document_number?: string | null;
    document_date?: string | null;
    valid_until?: string | null;
    revision?: string | null;
    file_path?: string | null;
    external_url?: string | null;
    status: string;
    uploaded_by?: string | null;
    created_at: string;
    updated_at?: string | null;
}

export interface AssessmentUpsert {
    assignment_id: string;
    status: string;
    valid_until?: string | null;
    next_review_date?: string | null;
    evidence_notes?: string | null;
    deviation_case_id?: string | null;
}

export interface ComponentTilstand {
    component_id: string;
    property_id: string;
    name: string;
    type?: string | null;
    ns3451_code?: string | null;
    condition_grade?: string | null;   // TG0|TG1|TG2|TG3
    criticality_level?: string | null; // critical|important|standard
    condition_assessed_at?: string | null;
    condition_assessed_by?: string | null;
    replacement_year?: number | null;
    barcode?: string | null;
    serial_number?: string | null;
    section_id?: string | null;
    status?: string | null;
}

export interface TilstandUpdate {
    condition_grade?: string | null;
    criticality_level?: string | null;
    replacement_year?: number | null;
    barcode?: string | null;
    serial_number?: string | null;
    section_id?: string | null;
}

export interface FdvuSectionCreate {
    property_id: string;
    name: string;
    section_type: string;
    floor?: number | null;
    area_sqm?: number | null;
    capacity?: number | null;
    description?: string | null;
}

// ─────────────────────────────────────────────
// Sections
// ─────────────────────────────────────────────

export async function getFdvuSections(propertyId: string): Promise<FdvuSection[]> {
    try {
        return await fetchAPI(`/fdvu/sections?property_id=${propertyId}`);
    } catch {
        return [];
    }
}

export async function createFdvuSection(body: FdvuSectionCreate): Promise<FdvuSection> {
    return fetchAPI('/fdvu/sections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

// ─────────────────────────────────────────────
// Requirements catalog
// ─────────────────────────────────────────────

export async function getRequirements(params?: {
    regulation_set?: string;
    category?: string;
}): Promise<Requirement[]> {
    try {
        const qs = new URLSearchParams();
        if (params?.regulation_set) qs.set('regulation_set', params.regulation_set);
        if (params?.category) qs.set('category', params.category);
        const query = qs.toString() ? `?${qs}` : '';
        return await fetchAPI(`/fdvu/requirements${query}`);
    } catch {
        return [];
    }
}

// ─────────────────────────────────────────────
// Assignments
// ─────────────────────────────────────────────

export async function getAssignments(propertyId: string, regulationSet?: string): Promise<AssignmentWithAssessment[]> {
    try {
        const qs = new URLSearchParams({ property_id: propertyId });
        if (regulationSet) qs.set('regulation_set', regulationSet);
        return await fetchAPI(`/fdvu/assignments?${qs}`);
    } catch {
        return [];
    }
}

export async function autoGenerateAssignments(propertyId: string): Promise<{
    created: number;
    skipped_already_assigned: number;
    skipped_not_applicable: number;
    is_barnevern: boolean;
}> {
    return fetchAPI(`/fdvu/assignments/auto-generate?property_id=${propertyId}`, {
        method: 'POST',
    });
}

export interface BulkAssessRequest {
    assignment_ids: string[];
    status: string;
    valid_until?: string | null;
    next_review_date?: string | null;
    evidence_notes?: string | null;
}

export async function bulkAssess(body: BulkAssessRequest): Promise<{ updated: number; created: number; total: number }> {
    return fetchAPI('/fdvu/compliance/bulk-assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export interface BulkAssessRegionRequest {
    region?: string | null;
    regulation_sets?: string[] | null;
    only_not_assessed?: boolean;
    status: string;
    valid_until?: string | null;
    next_review_date?: string | null;
    evidence_notes?: string | null;
    dry_run?: boolean;
}

export interface BulkAssessRegionResult {
    affected?: number;   // dry_run=true
    total?: number;      // dry_run=false
    dry_run: boolean;
    status: string;
}

export async function bulkAssessRegion(body: BulkAssessRegionRequest): Promise<BulkAssessRegionResult> {
    return fetchAPI('/fdvu/compliance/bulk-assess-region', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export async function sendReviewReminders(daysAhead: number = 30): Promise<{ reminders_created: number; days_ahead: number }> {
    return fetchAPI(`/fdvu/compliance/send-review-reminders?days_ahead=${daysAhead}`, {
        method: 'POST',
    });
}

// ─────────────────────────────────────────────
// KI-Assist
// ─────────────────────────────────────────────

export interface KiAssistResponse {
    suggested_status: string;
    confidence: 'high' | 'medium' | 'low';
    evidence_notes: string;
    explanation: string;
    next_review_months?: number | null;
}

export async function fdvuKiAssist(
    propertyId: string,
    assignmentId: string,
    userQuestion?: string,
): Promise<KiAssistResponse> {
    return fetchAPI('/fdvu/ki-assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            property_id: propertyId,
            assignment_id: assignmentId,
            user_question: userQuestion ?? null,
        }),
    });
}

// ─────────────────────────────────────────────
// FDVU Rapport
// ─────────────────────────────────────────────

export async function getFdvuRapport(propertyId: string): Promise<Record<string, unknown>> {
    return fetchAPI(`/fdvu/rapport/${propertyId}`);
}

// ─────────────────────────────────────────────
// Compliance summary & assessment
// ─────────────────────────────────────────────

export async function getComplianceSummary(propertyId: string): Promise<ComplianceSummary | null> {
    try {
        return await fetchAPI(`/fdvu/compliance/summary/${propertyId}`);
    } catch {
        return null;
    }
}

export async function upsertAssessment(body: AssessmentUpsert): Promise<ComplianceAssessment> {
    return fetchAPI('/fdvu/compliance/assess', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

// ─────────────────────────────────────────────
// Tilstandsregistrering
// ─────────────────────────────────────────────

export async function getPropertyComponents(propertyId: string): Promise<ComponentTilstand[]> {
    try {
        return await fetchAPI(`/fdvu/components/${propertyId}`);
    } catch {
        return [];
    }
}

export async function updateTilstand(componentId: string, body: TilstandUpdate): Promise<ComponentTilstand> {
    return fetchAPI(`/fdvu/components/${componentId}/tilstand`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

// ─────────────────────────────────────────────
// FDV Documents
// ─────────────────────────────────────────────

export async function getFdvDocuments(propertyId: string, documentType?: string): Promise<FdvDocument[]> {
    try {
        const qs = new URLSearchParams({ property_id: propertyId });
        if (documentType) qs.set('document_type', documentType);
        return await fetchAPI(`/fdvu/documents?${qs}`);
    } catch {
        return [];
    }
}
