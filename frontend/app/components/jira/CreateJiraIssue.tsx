"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import {
    getJiraConfig,
    getJiraProjects,
    getProjectIssueTypes,
    createJiraIssue,
    type JiraProject,
    type JiraIssueType,
    type CreateJiraIssueRequest,
} from '@/lib/api/jiraApi';

interface CreateJiraIssueProps {
    onSuccess?: (issueKey: string, issueUrl: string) => void;
    onCancel?: () => void;
    defaultProject?: string;
    defaultSummary?: string;
    defaultDescription?: string;
}

export default function CreateJiraIssue({
    onSuccess,
    onCancel,
    defaultProject,
    defaultSummary = '',
    defaultDescription = '',
}: CreateJiraIssueProps) {
    const { user, loading: authLoading } = useAuth();
    const status = authLoading ? 'loading' : user ? 'authenticated' : 'unauthenticated';
    const session = user;
    const [isConfigured, setIsConfigured] = useState(false);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Form state
    const [projects, setProjects] = useState<JiraProject[]>([]);
    const [issueTypes, setIssueTypes] = useState<JiraIssueType[]>([]);
    const [selectedProject, setSelectedProject] = useState(defaultProject || '');
    const [selectedIssueType, setSelectedIssueType] = useState('Task');
    const [summary, setSummary] = useState(defaultSummary);
    const [description, setDescription] = useState(defaultDescription);
    const [priority, setPriority] = useState('Medium');
    const [labels, setLabels] = useState('');

    // Load Jira configuration and projects
    useEffect(() => {
        async function loadJiraData() {
            if (status === 'loading') return;

            if (status === 'unauthenticated') {
                setError('Du må være logget inn for å bruke Jira-integrasjonen.');
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setError(null);

                console.log('Jira Integration: Fetching configuration...');
                // Check if Jira is configured
                const config = await getJiraConfig();
                setIsConfigured(config.configured);

                // If not configured, we still might want to show the specific error if it was a connection error
                // but getJiraConfig returns a success response with configured=false in that case.

                if (!config.configured) {
                    setLoading(false);
                    return;
                }

                // Check connection status
                if (config.connection_test && !config.connection_test.success) {
                    setError(`Jira-konfigurasjonsfeil: ${config.connection_test.message}`);
                    setLoading(false);
                    return;
                }

                console.log('Jira Integration: Fetching projects...');
                // Load projects
                const projectList = await getJiraProjects();
                setProjects(projectList);

                // Set default project if available
                if (!selectedProject && config.default_project) {
                    setSelectedProject(config.default_project);
                } else if (!selectedProject && projectList.length > 0) {
                    setSelectedProject(projectList[0].key);
                }

                setLoading(false);
            } catch (err: any) {
                console.error('Error loading Jira data:', err);
                // Extract error message properly
                let errorMessage = 'Kunne ikke laste Jira-data';

                if (err instanceof Error) {
                    errorMessage = err.message;
                } else if (typeof err === 'string') {
                    errorMessage = err;
                }

                if (errorMessage.includes('Failed to fetch') || errorMessage.includes('Network request failed')) {
                    errorMessage = 'Kunne ikke koble til backend. Sjekk at serveren kjører.';
                }

                setError(errorMessage);
                // Important: If we have an error, we should probably allow the user to see it 
                // even if isConfigured is false (which is default).
                setLoading(false);
            }
        }

        loadJiraData();
    }, [session, status]);

    // Load issue types when project changes
    useEffect(() => {
        async function loadIssueTypes() {
            if (!selectedProject || status !== 'authenticated') return;

            try {
                const types = await getProjectIssueTypes(selectedProject);
                setIssueTypes(types);

                // Reset issue type if current selection is not available
                if (!types.find(t => t.name === selectedIssueType) && types.length > 0) {
                    setSelectedIssueType(types[0].name);
                }
            } catch (err) {
                console.error('Error loading issue types:', err);
                setError(err instanceof Error ? err.message : 'Failed to load issue types');
            }
        }

        loadIssueTypes();
    }, [selectedProject, status]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (status !== 'authenticated') {
            setError('You must be logged in to create Jira issues');
            return;
        }

        if (!selectedProject || !summary.trim()) {
            setError('Project and summary are required');
            return;
        }

        try {
            setSubmitting(true);
            setError(null);
            setSuccess(null);

            const request: CreateJiraIssueRequest = {
                project_key: selectedProject,
                summary: summary.trim(),
                description: description.trim(),
                issue_type: selectedIssueType,
                priority: priority,
                labels: labels ? labels.split(',').map(l => l.trim()).filter(Boolean) : undefined,
            };

            const issue = await createJiraIssue(request);

            setSuccess(`Issue ${issue.key} created successfully!`);

            // Reset form
            setSummary('');
            setDescription('');
            setLabels('');
            setPriority('Medium');

            // Call success callback
            if (onSuccess) {
                onSuccess(issue.key, issue.url);
            }

            setSubmitting(false);
        } catch (err) {
            console.error('Error creating Jira issue:', err);
            setError(err instanceof Error ? err.message : 'Failed to create Jira issue');
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!isConfigured) {
        return (
            <div className="space-y-4">
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-red-800 font-medium">Feil oppstod:</p>
                        <p className="text-red-700">{error}</p>
                    </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-800">
                        Jira integration is not configured. Please contact your administrator to set up Jira integration.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Jira Issue</h2>

            {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-800">{error}</p>
                </div>
            )}

            {success && (
                <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-green-800">{success}</p>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Project Selection */}
                <div>
                    <label htmlFor="project" className="block text-sm font-medium text-gray-700 mb-2">
                        Project *
                    </label>
                    <select
                        id="project"
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                        required
                    >
                        <option value="">Select a project</option>
                        {projects.map((project) => (
                            <option key={project.key} value={project.key}>
                                {project.name} ({project.key})
                            </option>
                        ))}
                    </select>
                </div>

                {/* Issue Type Selection */}
                <div>
                    <label htmlFor="issueType" className="block text-sm font-medium text-gray-700 mb-2">
                        Issue Type *
                    </label>
                    <select
                        id="issueType"
                        value={selectedIssueType}
                        onChange={(e) => setSelectedIssueType(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                        required
                    >
                        {issueTypes.map((type) => (
                            <option key={type.id} value={type.name}>
                                {type.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Summary */}
                <div>
                    <label htmlFor="summary" className="block text-sm font-medium text-gray-700 mb-2">
                        Summary *
                    </label>
                    <input
                        type="text"
                        id="summary"
                        value={summary}
                        onChange={(e) => setSummary(e.target.value)}
                        placeholder="Brief description of the issue"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white placeholder-gray-400"
                        required
                        maxLength={255}
                    />
                </div>

                {/* Description */}
                <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                        Description *
                    </label>
                    <textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Detailed description of the issue"
                        rows={6}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white placeholder-gray-400"
                        required
                    />
                </div>

                {/* Priority */}
                <div>
                    <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
                        Priority
                    </label>
                    <select
                        id="priority"
                        value={priority}
                        onChange={(e) => setPriority(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                    >
                        <option value="Highest">Highest</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                        <option value="Lowest">Lowest</option>
                    </select>
                </div>

                {/* Labels */}
                <div>
                    <label htmlFor="labels" className="block text-sm font-medium text-gray-700 mb-2">
                        Labels
                    </label>
                    <input
                        type="text"
                        id="labels"
                        value={labels}
                        onChange={(e) => setLabels(e.target.value)}
                        placeholder="Comma-separated labels (e.g., bug, frontend, urgent)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white placeholder-gray-400"
                    />
                    <p className="mt-1 text-sm text-gray-500">Separate multiple labels with commas</p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                    <button
                        type="submit"
                        disabled={submitting}
                        className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {submitting ? 'Creating...' : 'Create Issue'}
                    </button>

                    {onCancel && (
                        <button
                            type="button"
                            onClick={onCancel}
                            disabled={submitting}
                            className="px-4 py-2 border border-gray-300 rounded-md font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}
