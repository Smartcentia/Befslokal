"use client";

import MinimalistDashboard from '@/app/components/features/MinimalistDashboard';
import Header from '@/app/components/ui/Header';

export default function MinimalistDashboardPage() {
    return (
        <div className="min-h-screen">
            <Header />
            <div className="pt-20">
                <MinimalistDashboard />
            </div>
        </div>
    );
}
