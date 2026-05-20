import React from 'react';

interface RiskPanelProps {
    systemStatus?: {
        database?: string;
        api_gateway?: string;
        nve_integration?: string;
        google_auth?: string;
    } | null;
    loading?: boolean;
}

function toBadge(value?: string): string {
    const normalized = (value || '').toLowerCase();
    if (normalized === 'online' || normalized === 'active' || normalized === 'ok') return 'ONLINE';
    if (normalized === 'offline' || normalized === 'down' || normalized === 'error') return 'OFFLINE';
    if (normalized === 'degraded' || normalized === 'warning') return 'DEGRADED';
    return 'UNKNOWN';
}

export default function RiskPanel({ systemStatus, loading = false }: RiskPanelProps) {
    const entries = [
        { label: 'Database', value: systemStatus?.database },
        { label: 'API Gateway', value: systemStatus?.api_gateway },
        { label: 'NVE Integration', value: systemStatus?.nve_integration },
        { label: 'Google Auth', value: systemStatus?.google_auth },
    ];

    return (
        <div className="space-y-3">
            <h2 className="text-lg font-bold">Risiko & Status</h2>
            <div className="space-y-2">
                {entries.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                        <span>{item.label}</span>
                        <span>{loading ? '...' : toBadge(item.value)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
