"use client";

// Import everything needed
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardStats from '@/app/components/features/DashboardStats';
import { Building2, Loader2 } from 'lucide-react';
import { getRecentActivity, RecentActivityItem, getSystemStatus, SystemStatus, getProperties, Property } from "@/lib/api";
import FocusAreaPanel from "@/app/components/features/FocusAreaPanel";
import OperationsPanel from "@/app/components/features/OperationsPanel";
import AnalysisPanel from "@/app/components/features/AnalysisPanel";
import MapComponent from "@/app/components/features/MapComponent";
import TopTenantsPanel from "@/app/components/features/TopTenantsPanel";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { useAuth } from "@/hooks/useAuth";

// iconMap moved to OperationsPanel.tsx

export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/welcome");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    if (authLoading || !user) return;

    async function loadData() {
      try {
        const [activity, status, propertyData] = await Promise.all([
          getRecentActivity(),
          getSystemStatus(),
          getProperties(0, 500)
        ]);

        setRecentActivity(activity);
        setSystemStatus(status);
        setProperties(propertyData);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [authLoading, user]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-[50vh] w-full items-center justify-center" role="status" aria-live="polite">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden />
        <span className="sr-only">Laster</span>
      </div>
    );
  }

  return (
    <main className="flex-1 p-6 md:p-8 max-w-400 mx-auto w-full flex flex-col gap-6">

      {/* Header Section */}
      <div className="flex items-center justify-between pb-6 border-b border-gray-200/50 dark:border-slate-700/50">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Oversikt</h1>
          <p className="text-sm text-muted-foreground mt-1">Status for din eiendomsportefølje.</p>
        </div>
      </div>

      {/* HOLY GRAIL GRID LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 min-h-125">

        {/* LEFT PANEL: Analysis & Risk (25%) */}
        <aside className="lg:col-span-3 flex flex-col gap-6">
          <ErrorBoundary componentName="AnalysisPanel">
            <AnalysisPanel />
          </ErrorBoundary>
          <ErrorBoundary componentName="FocusAreaPanel">
            <FocusAreaPanel systemStatus={systemStatus} loading={loading} />
          </ErrorBoundary>
        </aside>

        {/* CENTER PANEL: Core/Map/Stats (50%) */}
        <section className="lg:col-span-6 flex flex-col gap-8">
          <ErrorBoundary componentName="DashboardStats">
            <DashboardStats />
          </ErrorBoundary>

          {/* Main Content Area: Map */}
          <div className="glass-card flex-1 min-h-125 relative overflow-hidden border border-border bg-surface">
            <ErrorBoundary componentName="MapComponent">
              <MapComponent properties={properties} />
            </ErrorBoundary>

            {/* Overlay Search (UI Concept Phase 1) */}
            <div className="absolute top-4 left-4 right-4 z-10 flex gap-2">
              <div className="flex-1 bg-surface/90 backdrop-blur-md border border-border rounded-full px-4 py-2 flex items-center gap-3 shadow-xl">
                <Building2 size={16} className="text-primary" />
                <input
                  type="text"
                  placeholder="Søk i porteføljen (f.eks 'Olsen Eiendom')"
                  className="bg-transparent border-none outline-none text-sm w-full text-foreground"
                />
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT PANEL: Ops & Activity (25%) */}
        <aside className="lg:col-span-3 flex flex-col gap-6">
          <ErrorBoundary componentName="TopTenantsPanel">
            <TopTenantsPanel />
          </ErrorBoundary>
          <ErrorBoundary componentName="OperationsPanel">
            <OperationsPanel recentActivity={recentActivity} loading={loading} />
          </ErrorBoundary>
        </aside>

      </div>

    </main>
  );
}
