

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FinancialQueryPanel from '@/components/lab/FinancialQueryPanel';
import * as api from '@/lib/api';

// Mock API functions
vi.mock('@/lib/api', () => ({
    runFinancialQuery: vi.fn(),
    propertyService: {
        getAll: vi.fn()
    }
}));

describe('FinancialQueryPanel', () => {
    const mockProperties = [
        { id: 'prop1', name: 'Tærudgata 16', external_id: 'T16' },
        { id: 'prop2', name: 'Majorstua 4', external_id: 'M4' },
        { id: 'prop3', name: 'Grünerløkka 7', external_id: 'G7' }
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        (api.propertyService.getAll as any).mockResolvedValue(mockProperties);
    });

    it('renders the component with title and input', () => {
        render(<FinancialQueryPanel />);

        expect(screen.getByText('Financial Intelligence')).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i)).toBeInTheDocument();
    });

    it('loads properties on mount', async () => {
        render(<FinancialQueryPanel />);

        await waitFor(() => {
            expect(api.propertyService.getAll).toHaveBeenCalledTimes(1);
        });
    });

    it('shows and hides property selector', async () => {
        render(<FinancialQueryPanel />);

        const toggleButton = screen.getByText(/Vis/i);
        fireEvent.click(toggleButton);

        await waitFor(() => {
            expect(screen.getByText('Tærudgata 16 (T16)')).toBeInTheDocument();
        });

        const hideButton = screen.getByText(/Skjul/i);
        fireEvent.click(hideButton);

        await waitFor(() => {
            expect(screen.queryByText('Tærudgata 16 (T16)')).not.toBeVisible();
        });
    });

    it('allows property selection', async () => {
        render(<FinancialQueryPanel />);

        // Show selector
        fireEvent.click(screen.getByText(/Vis/i));

        // Select a property
        const checkbox = screen.getByLabelText(/Tærudgata 16/i);
        fireEvent.click(checkbox);

        expect(checkbox).toBeChecked();
        expect(screen.getByText(/1 valgt/i)).toBeInTheDocument();
    });

    it('populates query from quick action', () => {
        render(<FinancialQueryPanel />);

        const quickActionButton = screen.getByText('Finn outliers i kostnader');
        fireEvent.click(quickActionButton);

        const textarea = screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i);
        expect((textarea as HTMLTextAreaElement).value).toContain('unormalt høye driftskostnader');
    });

    it('submits query and displays result', async () => {
        const mockResponse = {
            status: 'tool_created',
            intent: 'outlier_detection',
            confidence: 0.85,
            tool_id: 'tool-123',
            code: 'import pandas as pd\n# Generated code'
        };

        (api.runFinancialQuery as any).mockResolvedValue(mockResponse);

        render(<FinancialQueryPanel />);

        const textarea = screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i);
        fireEvent.change(textarea, { target: { value: 'Finn outliers' } });

        const submitButton = screen.getByText('Analyser');
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(api.runFinancialQuery).toHaveBeenCalledWith({
                query: 'Finn outliers',
                property_ids: undefined
            });
        });

        await waitFor(() => {
            expect(screen.getByText('tool_created')).toBeInTheDocument();
            expect(screen.getByText(/outlier_detection/i)).toBeInTheDocument();
            expect(screen.getByText(/85%/i)).toBeInTheDocument();
        });
    });

    it('handles error state', async () => {
        (api.runFinancialQuery as any).mockRejectedValue(new Error('API Error'));

        render(<FinancialQueryPanel />);

        const textarea = screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i);
        fireEvent.change(textarea, { target: { value: 'Test query' } });

        const submitButton = screen.getByText('Analyser');
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(/API Error/i)).toBeInTheDocument();
        });
    });

    it('disables submit button when query is empty', () => {
        render(<FinancialQueryPanel />);

        const submitButton = screen.getByText('Analyser');
        expect(submitButton).toBeDisabled();
    });

    it('calls onToolCreated callback when tool is created', async () => {
        const mockCallback = vi.fn();
        const mockResponse = {
            status: 'tool_created',
            intent: 'comparison',
            confidence: 0.9,
            tool_id: 'new-tool-456'
        };

        (api.runFinancialQuery as any).mockResolvedValue(mockResponse);

        render(<FinancialQueryPanel onToolCreated={mockCallback} />);

        const textarea = screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i);
        fireEvent.change(textarea, { target: { value: 'Compare properties' } });

        const submitButton = screen.getByText('Analyser');
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockCallback).toHaveBeenCalledWith('new-tool-456');
        });
    });

    it('includes selected properties in API request', async () => {
        render(<FinancialQueryPanel />);

        // Show and select properties
        fireEvent.click(screen.getByText(/Vis/i));
        fireEvent.click(screen.getByLabelText(/Tærudgata 16/i));
        fireEvent.click(screen.getByLabelText(/Majorstua 4/i));

        const textarea = screen.getByPlaceholderText(/Sammenlign 8 eiendommer/i);
        fireEvent.change(textarea, { target: { value: 'Compare' } });

        const submitButton = screen.getByText('Analyser');
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(api.runFinancialQuery).toHaveBeenCalledWith({
                query: 'Compare',
                property_ids: ['prop1', 'prop2']
            });
        });
    });
});
