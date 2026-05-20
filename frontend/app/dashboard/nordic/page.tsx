"use client";

import NordicDashboard from '@/app/components/features/NordicDashboard';
import Header from '@/app/components/ui/Header';

export default function NordicDashboardPage() {
    return (
        <div className="min-h-screen">
            <Header />
            <div className="pt-20">
                <NordicDashboard />
            </div>
        </div>
    );
}
