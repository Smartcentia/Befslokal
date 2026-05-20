"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import { fetchAPI } from "@/lib/api/client";

interface AlertCount {
    open_cases: number;
    critical_cases: number;
    fdvu_overdue: number;
}

export default function AlertsBadge() {
    const [counts, setCounts] = useState<AlertCount | null>(null);

    useEffect(() => {
        Promise.all([
            fetchAPI<{ items?: unknown[]; total?: number } | unknown[]>("/hms/cases?status=open&limit=1").catch(() => null),
            fetchAPI<{ total_assignments?: number; overdue_reviews?: number }>("/fdvu/compliance/portfolio-summary").catch(() => null),
        ]).then(([hmsRes, fdvuRes]) => {
            // HMS open cases total
            let openCases = 0;
            let criticalCases = 0;
            if (hmsRes) {
                // Try both array and {items, total} shapes
                const items = Array.isArray(hmsRes) ? hmsRes : (hmsRes as { items?: unknown[] }).items ?? [];
                const total = Array.isArray(hmsRes) ? hmsRes.length : (hmsRes as { total?: number }).total ?? 0;
                openCases = total;
                criticalCases = 0; // not available from this endpoint without full fetch
            }
            const fdvuOverdue = (fdvuRes as { overdue_reviews?: number } | null)?.overdue_reviews ?? 0;

            if (openCases > 0 || fdvuOverdue > 0) {
                setCounts({ open_cases: openCases, critical_cases: criticalCases, fdvu_overdue: fdvuOverdue });
            }
        });
    }, []);

    if (!counts) return null;

    const total = counts.open_cases + counts.fdvu_overdue;
    if (total === 0) return null;

    return (
        <Link
            href="/hms"
            title={`${counts.open_cases} åpne HMS-saker · ${counts.fdvu_overdue} forfalt FDVU-revisjon`}
            className="relative p-2 text-muted hover:text-foreground rounded-lg hover:bg-surface/50 transition-colors"
        >
            <ShieldAlert size={18} />
            <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-white px-1 leading-none">
                {total > 99 ? "99+" : total}
            </span>
        </Link>
    );
}
