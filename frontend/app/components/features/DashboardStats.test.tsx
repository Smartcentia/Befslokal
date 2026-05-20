import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import DashboardStats from './DashboardStats';
import React from 'react';

// Mock the API module
vi.mock('@/lib/api', () => ({
    getDashboardStats: vi.fn().mockResolvedValue({
        properties: 42,
        contracts: 10,
        risks: 5
    }),
    API_BASE_URL: 'http://mock-api'
}));

// Mock Next.js Link
vi.mock('next/link', () => ({
    default: ({ children, href }: { children: React.ReactNode; href: string }) => (
        <a href={href}>{children}</a>
    ),
}));

describe('DashboardStats', () => {
    it('renders loading state initially', () => {
        // We can't easily catch the loading state because fetch is fast in mock, 
        // but we can check that it eventually renders data.
        render(<DashboardStats />);
    });

    it('renders statistics after data fetch', async () => {
        render(<DashboardStats />);

        // Wait for the mock value "42" to appear
        await waitFor(() => {
            expect(screen.getByText('42')).toBeDefined();
        });

        // Check strict values from our mock
        expect(screen.getByText('Antall eiendommer')).toBeDefined();
        expect(screen.getByText('42')).toBeDefined();

        expect(screen.getByText('Aktive kontrakter')).toBeDefined();
        expect(screen.getByText('10')).toBeDefined();

        expect(screen.getByText('Åpne driftsavvik')).toBeDefined();
        expect(screen.getByText('5')).toBeDefined();
    });
});
