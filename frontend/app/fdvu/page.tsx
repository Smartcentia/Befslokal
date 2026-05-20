import { Metadata } from 'next';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck, AlertTriangle, Clock, FileText, Building2, ChevronRight } from 'lucide-react';
import type { ComplianceSummary } from '@/lib/api/fdvuApi';
import BulkGenerateButton from './BulkGenerateButton';

export const metadata: Metadata = { title: 'FDVU Compliance' };

// ─────────────────────────────────────────────
// Server-side data fetch
// ─────────────────────────────────────────────

async function getAllProperties() {
    if (!API_BASE_URL) return [];
    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || 'befs-super-secret-key-12345';
    try {
        const res = await fetch(`${API_BASE_URL}/properties?limit=200`, {
            cache: 'no-store',
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

async function getComplianceSummary(propertyId: string): Promise<ComplianceSummary | null> {
    if (!API_BASE_URL) return null;
    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || 'befs-super-secret-key-12345';
    try {
        const res = await fetch(`${API_BASE_URL}/fdvu/compliance/summary/${propertyId}`, {
            cache: 'no-store',
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return null;
        return res.json();
    } catch {
        return null;
    }
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function statusColor(rate: number): string {
    if (rate >= 0.9) return 'text-success';
    if (rate >= 0.6) return 'text-warning';
    return 'text-destructive';
}

function statusBadge(summary: ComplianceSummary) {
    const r = summary.compliance_rate;
    if (summary.total_assignments === 0) return <Badge variant="outline" className="text-xs">Ikke startet</Badge>;
    if (r >= 0.9) return <Badge className="bg-success/15 text-success border-success/30 text-xs">God</Badge>;
    if (r >= 0.6) return <Badge className="bg-warning/15 text-warning border-warning/30 text-xs">Delvis</Badge>;
    return <Badge className="bg-destructive/15 text-destructive border-destructive/30 text-xs">Avvik</Badge>;
}

// ─────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────

export default async function FdvuDashboardPage() {
    const properties = await getAllProperties();

    // Fetch summaries in parallel (cap at 50 to avoid overloading)
    const sample = properties.slice(0, 50);
    const summaries = await Promise.all(
        sample.map((p: { property_id: string }) => getComplianceSummary(p.property_id))
    );

    // Build combined list
    const rows = sample.map((p: { property_id: string; name?: string; address?: string; region?: string }, i: number) => ({
        ...p,
        summary: summaries[i],
    }));

    // Portfolio totals from properties that have assignments
    const withData = rows.filter(r => r.summary && r.summary.total_assignments > 0);
    const totalAssignments = withData.reduce((s, r) => s + (r.summary?.total_assignments ?? 0), 0);
    const totalCompliant = withData.reduce((s, r) => s + (r.summary?.compliant ?? 0), 0);
    const totalOverdue = withData.reduce((s, r) => s + (r.summary?.overdue_reviews ?? 0), 0);
    const totalNonCompliant = withData.reduce((s, r) => s + (r.summary?.non_compliant ?? 0), 0);
    const portfolioRate = totalAssignments > 0 ? totalCompliant / totalAssignments : 0;

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                        <ShieldCheck className="text-primary" size={26} />
                        FDVU Compliance
                    </h1>
                    <p className="text-muted text-sm mt-1">
                        Oversikt over kravoppfyllelse, FDV-dokumentasjon og tilstandsgrad
                    </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                    {totalAssignments === 0 && <BulkGenerateButton />}
                    <Link
                        href="/onboarding"
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
                    >
                        <Building2 size={15} />
                        Ny eiendom
                    </Link>
                    <Link
                        href="/fdvu/bulk-vurdering"
                        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg text-sm text-foreground hover:bg-primary/10 transition-colors"
                    >
                        <ShieldCheck size={15} />
                        Bulk-vurdering
                    </Link>
                    <Link
                        href="/fdvu/krav"
                        className="flex items-center gap-2 px-4 py-2 bg-card border border-border rounded-lg text-sm text-foreground hover:bg-primary/10 transition-colors"
                    >
                        <FileText size={15} />
                        Kravkatalog
                    </Link>
                </div>
            </div>

            {/* Portfolio KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="bg-card border-border">
                    <CardContent className="pt-5">
                        <div className="text-3xl font-bold text-foreground">{Math.round(portfolioRate * 100)}%</div>
                        <div className="text-sm text-muted mt-1">Portefølje compliance-rate</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-5">
                        <div className="text-3xl font-bold text-success">{totalCompliant}</div>
                        <div className="text-sm text-muted mt-1">Oppfylte krav</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-5">
                        <div className="text-3xl font-bold text-destructive">{totalNonCompliant}</div>
                        <div className="text-sm text-muted mt-1">Avvik registrert</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-5">
                        <div className={`text-3xl font-bold ${totalOverdue > 0 ? 'text-warning' : 'text-success'}`}>{totalOverdue}</div>
                        <div className="text-sm text-muted mt-1">Forfalt revisjon</div>
                    </CardContent>
                </Card>
            </div>

            {/* Property table */}
            <Card className="bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                        <Building2 size={16} className="text-primary" />
                        Eiendommer ({rows.length})
                    </CardTitle>
                    <CardDescription className="text-muted text-xs">
                        Klikk på en eiendom for detaljert compliance-oversikt
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border text-muted text-xs uppercase">
                                    <th className="text-left pb-2 pr-4">Eiendom</th>
                                    <th className="text-left pb-2 pr-4 hidden md:table-cell">Region</th>
                                    <th className="text-center pb-2 pr-4">Rate</th>
                                    <th className="text-center pb-2 pr-4 hidden sm:table-cell">Krav</th>
                                    <th className="text-center pb-2 pr-4 hidden lg:table-cell">Avvik</th>
                                    <th className="text-center pb-2 pr-4 hidden lg:table-cell">
                                        <Clock size={12} className="inline mr-1" />Forfalt
                                    </th>
                                    <th className="text-center pb-2">Status</th>
                                    <th className="pb-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map(row => {
                                    const s = row.summary;
                                    const rate = s ? Math.round(s.compliance_rate * 100) : null;
                                    return (
                                        <tr key={row.property_id} className="border-b border-border/40 hover:bg-primary/5 transition-colors">
                                            <td className="py-3 pr-4">
                                                <div className="font-medium text-foreground">{row.name || 'Ukjent'}</div>
                                                <div className="text-muted text-xs truncate max-w-48">{row.address}</div>
                                            </td>
                                            <td className="py-3 pr-4 hidden md:table-cell text-muted text-xs">{row.region || '–'}</td>
                                            <td className="py-3 pr-4 text-center">
                                                {rate !== null ? (
                                                    <span className={`font-bold ${statusColor(s!.compliance_rate)}`}>{rate}%</span>
                                                ) : (
                                                    <span className="text-muted">–</span>
                                                )}
                                            </td>
                                            <td className="py-3 pr-4 text-center hidden sm:table-cell text-muted">
                                                {s ? s.total_assignments : '–'}
                                            </td>
                                            <td className="py-3 pr-4 text-center hidden lg:table-cell">
                                                {s && s.non_compliant > 0 ? (
                                                    <span className="text-destructive font-medium">{s.non_compliant}</span>
                                                ) : (
                                                    <span className="text-muted">{s ? 0 : '–'}</span>
                                                )}
                                            </td>
                                            <td className="py-3 pr-4 text-center hidden lg:table-cell">
                                                {s && s.overdue_reviews > 0 ? (
                                                    <span className="text-warning font-medium flex items-center justify-center gap-1">
                                                        <AlertTriangle size={12} />{s.overdue_reviews}
                                                    </span>
                                                ) : (
                                                    <span className="text-muted">{s ? 0 : '–'}</span>
                                                )}
                                            </td>
                                            <td className="py-3 text-center">
                                                {s ? statusBadge(s) : (
                                                    <Badge variant="outline" className="text-xs">Ingen data</Badge>
                                                )}
                                            </td>
                                            <td className="py-3 pl-2">
                                                <Link href={`/fdvu/${row.property_id}`}>
                                                    <ChevronRight size={16} className="text-muted hover:text-primary transition-colors" />
                                                </Link>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
