"use client";

import TerminalDashboard from '@/app/components/features/TerminalDashboard';
import Header from '@/app/components/ui/Header';

export default function TerminalDashboardPage() {
    return (
        <div className="min-h-screen">
            <Header />
            <div className="pt-20">
                <TerminalDashboard />
            </div>
        </div>
    );
}
