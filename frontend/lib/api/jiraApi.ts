import { fetchAPI } from './client';

// Type Definitions
export interface JiraConfig {
    configured: boolean;
    url?: string;
    default_project?: string;
    connection_test?: {
        success: boolean;
        message: string;
        user?: string;
    };
}

export interface JiraProject {
    key: string;
    name: string;
    id: string;
    projectTypeKey?: string;
}

export interface JiraIssueType {
    id: string;
    name: string;
    description: string;
    subtask: boolean;
}

export interface CreateJiraIssueRequest {
    project_key: string;
    summary: string;
    description: string;
    issue_type?: string;
    priority?: string;
    labels?: string[];
    assignee?: string;
}

export interface JiraIssue {
    key: string;
    url: string;
    id: string;
    self: string;
}

export interface JiraIssueDetail {
    key: string;
    id: string;
    summary: string;
    description?: string;
    status?: string;
    priority?: string;
    assignee?: string;
    reporter?: string;
    created?: string;
    updated?: string;
    url: string;
}

/**
 * Get Jira configuration status
 */
export async function getJiraConfig(): Promise<JiraConfig> {
    return await fetchAPI('/jira/config');
}

/**
 * Get list of accessible Jira projects
 */
export async function getJiraProjects(): Promise<JiraProject[]> {
    return await fetchAPI('/jira/projects');
}

/**
 * Get available issue types for a specific project
 */
export async function getProjectIssueTypes(
    projectKey: string
): Promise<JiraIssueType[]> {
    return fetchAPI<JiraIssueType[]>(`/jira/projects/${projectKey}/issue-types`);
}

/**
 * Create a new Jira issue
 */
export async function createJiraIssue(
    request: CreateJiraIssueRequest
): Promise<JiraIssue> {
    return fetchAPI<JiraIssue>('/jira/issues', {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

/**
 * Get details of a specific Jira issue
 */
export async function getJiraIssue(
    issueKey: string
): Promise<JiraIssueDetail> {
    return fetchAPI<JiraIssueDetail>(`/jira/issues/${issueKey}`);
}
