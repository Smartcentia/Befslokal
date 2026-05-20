import { ShieldCheck } from "lucide-react";

export default function FdvuLoading() {
    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-foreground">
                        <ShieldCheck className="text-primary animate-pulse" size={26} />
                        FDVU Compliance
                    </h1>
                    <p className="text-muted text-sm mt-1">Laster compliance-data for alle eiendommer…</p>
                </div>
            </div>

            {/* KPI skeletons */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="border border-border rounded-xl p-5 bg-card animate-pulse">
                        <div className="h-8 w-16 bg-muted rounded mb-2" />
                        <div className="h-3 w-32 bg-muted rounded" />
                    </div>
                ))}
            </div>

            {/* Table skeleton */}
            <div className="border border-border rounded-xl bg-card">
                <div className="p-4 border-b border-border">
                    <div className="h-4 w-40 bg-muted rounded animate-pulse" />
                </div>
                <div className="p-4 space-y-3">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                        <div key={i} className="flex items-center gap-4 animate-pulse">
                            <div className="h-4 w-48 bg-muted rounded" />
                            <div className="h-4 w-24 bg-muted rounded hidden md:block" />
                            <div className="ml-auto h-6 w-16 bg-muted rounded-full" />
                            <div className="h-4 w-20 bg-muted rounded" />
                        </div>
                    ))}
                </div>
                <div className="p-4 text-center text-sm text-muted-foreground border-t border-border">
                    Henter data fra alle avdelinger — dette tar noen sekunder…
                </div>
            </div>
        </div>
    );
}
