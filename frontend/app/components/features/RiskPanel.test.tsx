import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import RiskPanel from './RiskPanel';
import React from 'react';

describe('RiskPanel', () => {
    it('renders ONLINE status correctly', () => {
        const mockStatus = {
            database: 'online',
            api_gateway: 'online',
            nve_integration: 'active',
            google_auth: 'active'
        };

        render(<RiskPanel systemStatus={mockStatus as any} loading={false} />);

        expect(screen.getByText('Risiko & Status')).toBeDefined();

        // Check for ONLINE badges (there should be 2: Database and API Gateway)
        const onlineBadges = screen.getAllByText('ONLINE');
        expect(onlineBadges.length).toBeGreaterThanOrEqual(2);
    });

    it('renders OFFLINE status correctly', () => {
        const mockStatus = {
            database: 'offline',
            api_gateway: 'offline',
            nve_integration: 'degraded',
            google_auth: 'active'
        };

        render(<RiskPanel systemStatus={mockStatus as any} loading={false} />);

        const offlineBadges = screen.getAllByText('OFFLINE');
        expect(offlineBadges.length).toBeGreaterThanOrEqual(1);

        expect(screen.getByText('DEGRADED')).toBeDefined();
    });

    it('shows loading state', () => {
        render(<RiskPanel systemStatus={null} loading={true} />);
        // Check for loading dots
        expect(screen.getAllByText('...').length).toBeGreaterThan(0);
    });
});
