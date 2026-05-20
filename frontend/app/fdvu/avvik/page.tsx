"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, XCircle, Clock, ChevronRight, RefreshCw, Filter, Building2, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { fetchAPI } from '@/lib/api/client';

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

interface FdvuAvvik {
    assignment_id: string;
    property_id: string;
    property_name?: string;
    property_region?: string;
    requirement_code?: string;
    requirement_title?: string;
    requirement_category?: string;
    severity?: string;
    regulation_set?: string;
    status: string; // 'non_compliant' | 'partial' | 'not_assessed'
    assessed_at?: string;
    next_review_date?: string;
    evidence_notes?: string;
}

interface PortfolioNonCompliant {
    property_id: string;
    property_name: string;
    region?: string;
    non_compliant: number;
    partial: number;
    overdue_reviews: number;
    compliance_rate: number;
}

const SEV_STYLE: Record<string, string> = {
    critical: 'bg-destructive/15 text-destructive border-destructive/30',
    high: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
    medium: 'bg-warning/15 text-warning border-warning/30',
    low: 'bg-success/15 text-success border-success/30',
};

const STATUS_STYLE: Record<string, { label: string; style: string }> = {
    non_compliant: { label: 'Avvik', style: 'bg-destructive/15 text-destructive border-destructive/30' },
    partial: { label: 'Delvis', style: 'bg-warning/15 text-warning border-warning/30' },
    not_assessed: { label: 'Ikke vurdert', style: 'bg-border/50 text-muted border-border' },
};

const REG_LABELS: Record<string, string> = {
    RKL6: 'RKL6', BVL: 'BVL', TEK17: 'TEK17', HMS: 'HMS',
    KVALITETSFORSKRIFTEN: 'Kvalitet', INTERN: 'Intern',
};

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function isOverdue(next_review_date?: string): boolean {
    if (!next_review_date) return false;
    return new Date(next_review_date) < new Date();
}

// ─────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────

export default function FdvuAvvikPage() {
    const [loading, setLoading] = useState(true);
    const [properties, setProperties] = useState<{ property_id: string; name: string; region?: string }[]>([]);
    const [portfolio, setPortfolio] = useState<PortfolioNonCompliant[]>([]);
    const [avvikList, setAvvikList] = useState<FdvuAvvik[]>([]);
    const [filterRegion, setFilterRegion] = useState<string>('alle');
    const [filterStatus, setFilterStatus] = useState<string>('alle');

    useEffect(() => { loadData(); }, []);

    async function loadData() {
        setLoading(true);
        try {
            // Load properties
            const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || 'befs-super-secret-key-12345';
            const API = process.env.NEXT_PUBLIC_API_URL || '';

            const propRes = await fetch(`${API}/api/v1/properties?limit=200`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const propData = propRes.ok ? await propRes.json() : {};
            const allProps: { property_id: string; name: string; region?: string }[] =
                Array.isArray(propData?.items) ? propData.items : Array.isArray(propData) ? propData : [];
            setProperties(allProps);

            // Load compliance summaries to build portfolio list of non-compliant properties
            const summaries = await Promise.allSettled(
                allProps.slice(0, 60).map(async (p) => {
                    try {
                        const res = await fetch(`${API}/api/v1/fdv/compliance/summary/${p.property_id}`, {
                            headers: { Authorization: `Bearer ${token}` },
                        });
                        if (!res.ok) return null;
                        const s = await res.json();
                        return { ...s, property_name: p.name, region: p.region };
                    } catch { return null; }
                })
            );

            const portfolioData: PortfolioNonCompliant[] = summaries
                .filter((r): r is PromiseFulfilledResult<PortfolioNonCompliant | null> => r.status === 'fulfilled' && r.value !== null && (r.value.non_compliant > 0 || r.value.partial > 0 || r.value.overdue_reviews > 0))
                .map(r => r.value as PortfolioNonCompliant)
                .sort((a, b) => b.non_compliant - a.non_compliant);
            setPortfolio(portfolioData);

            // Load assignments with non_compliant/partial status across top properties
            const topProps = portfolioData.slice(0, 20).map(p => p.property_id);
            if (topProps.length > 0) {
                const assignmentResults = await Promise.allSettled(
                    topProps.map(async (pid) => {
                        const pInfo = allProps.find(p => p.property_id === pid);
                        try {
                            const res = await fetch(`${API}/api/v1/fdv/compliance/assignments?property_id=${pid}&status=non_compliant,partial`, {
                                headers: { Authorization: `Bearer ${token}` },
                            });
                            if (!res.ok) {
                                // Fallback: fetch all assignments and filter
                                const res2 = await fetch(`${API}/api/v1/fdv/compliance/assignments?property_id=${pid}`, {
                                    headers: { Authorization: `Bearer ${token}` },
                                });
                                if (!res2.ok) return [];
                                const data = await res2.json();
                                return (Array.isArray(data) ? data : data?.items ?? [])
                                    .filter((a: { compliance_assessment?: { status: string } }) =>
                                        ['non_compliant', 'partial'].includes(a?.compliance_assessment?.status ?? '')
                                    )
                                    .map((a: {
                                        assignment_id: string;
                                        requirement?: { code?: string; title?: string; category?: string; severity_if_breached?: string; regulation_set?: string };
                                        compliance_assessment?: { status: string; assessed_at?: string; next_review_date?: string; evidence_notes?: string };
                                    }) => ({
                                        assignment_id: a.assignment_id,
                                        property_id: pid,
                                        property_name: pInfo?.name,
                                        property_region: pInfo?.region,
                                        requirement_code: a.requirement?.code,
                                        requirement_title: a.requirement?.title,
                                        requirement_category: a.requirement?.category,
                                        severity: a.requirement?.severity_if_breached,
                                        regulation_set: a.requirement?.regulation_set,
                                        status: a.compliance_assessment?.status ?? 'not_assessed',
                                        assessed_at: a.compliance_assessment?.assessed_at,
                                        next_review_date: a.compliance_assessment?.next_review_date,
                                        evidence_notes: a.compliance_assessment?.evidence_notes,
                                    }));
                            }
                            const data = await res.json();
                            return (Array.isArray(data) ? data : data?.items ?? []).map((a: {
                                assignment_id: string;
                                requirement?: { code?: string; title?: string; category?: string; severity_if_breached?: string; regulation_set?: string };
                                compliance_assessment?: { status: string; assessed_at?: string; next_review_date?: string; evidence_notes?: string };
                            }) => ({
                                assignment_id: a.assignment_id,
                                property_id: pid,
                                property_name: pInfo?.name,
                                property_region: pInfo?.region,
                                requirement_code: a.requirement?.code,
                                requirement_title: a.requirement?.title,
                                requirement_category: a.requirement?.category,
                                severity: a.requirement?.severity_if_breached,
                                regulation_set: a.requirement?.regulation_set,
                                status: a.compliance_assessment?.status ?? 'non_compliant',
                                assessed_at: a.compliance_assessment?.assessed_at,
                                next_review_date: a.compliance_assessment?.next_review_date,
                                evidence_notes: a.compliance_assessment?.evidence_notes,
                            }));
                        } catch { return []; }
                    })
                );
                const flat: FdvuAvvik[] = assignmentResults
                    .filter((r): r is PromiseFulfilledResult<FdvuAvvik[]> => r.status === 'fulfilled')
                    .flatMap(r => r.value);
                setAvvikList(flat);
            }
        } catch (e) {
            console.error('FDVU avvik load failed', e);
        } finally {
            setLoading(false);
        }
    }

    const regions = ['alle', ...Array.from(new Set(properties.map(p => p.region ?? 'Nasjonal'))).sort()];
    const statuses = ['alle', 'non_compliant', 'partial'];

    const filteredPortfolio = portfolio.filter(p =>
        filterRegion === 'alle' || (p.region ?? 'Nasjonal') === filterRegion
    );

    const filteredAvvik = avvikList.filter(a =>
        (filterRegion === 'alle' || (a.property_region ?? 'Nasjonal') === filterRegion) &&
        (filterStatus === 'alle' || a.status === filterStatus)
    );

    const totalNonCompliant = portfolio.reduce((s, p) => s + p.non_compliant, 0);
    const totalPartial = portfolio.reduce((s, p) => s + p.partial, 0);
    const totalOverdue = portfolio.reduce((s, p) => s + p.overdue_reviews, 0);
    const criticalAvvik = avvikList.filter(a => a.severity === 'critical' || a.severity === 'high').length;

    return (
        <div className="p-6 space-y-6 max-w-7xl mx-auto pb-20">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Link href="/fdvu" className="text-muted hover:text-foreground transition-colors">
                            <ArrowLeft size={16} />
                        </Link>
                        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                            <AlertTriangle className="text-destructive" size={24} />
                            FDVU Avvik
                        </h1>
                    </div>
                    <p className="text-muted text-sm">Kravbrudd og delvis oppfylte krav på tvers av alle eiendommer</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={loadData}
                        className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-lg text-sm text-foreground hover:bg-primary/5 transition-colors"
                    >
                        <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
                        Oppdater
                    </button>
                    <Link href="/fdvu/om-fduv" className="flex items-center gap-1.5 px-3 py-1.5 bg-card border border-border rounded-lg text-xs font-medium text-foreground hover:bg-primary/5 transition-colors">
                        Om FDVU
                    </Link>
                </div>
            </div>

            {/* KPI row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Card className="bg-card border-border">
                    <CardContent className="pt-4 pb-4">
                        <div className="text-2xl font-bold text-destructive">{loading ? '–' : totalNonCompliant}</div>
                        <div className="text-xs text-muted mt-0.5">Avvik (non-compliant)</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-4 pb-4">
                        <div className="text-2xl font-bold text-warning">{loading ? '–' : totalPartial}</div>
                        <div className="text-xs text-muted mt-0.5">Delvis oppfylt</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-4 pb-4">
                        <div className="text-2xl font-bold text-orange-400">{loading ? '–' : totalOverdue}</div>
                        <div className="text-xs text-muted mt-0.5">Forfalt revisjon</div>
                    </CardContent>
                </Card>
                <Card className="bg-card border-border">
                    <CardContent className="pt-4 pb-4">
                        <div className="text-2xl font-bold text-destructive">{loading ? '–' : criticalAvvik}</div>
                        <div className="text-xs text-muted mt-0.5">Kritiske / høye</div>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-1.5 text-xs text-muted">
                    <Filter size={13} /> Filtrer:
                </div>
                <select
                    value={filterRegion}
                    onChange={e => setFilterRegion(e.target.value)}
                    className="text-xs bg-card border border-border rounded-lg px-2 py-1.5 text-foreground"
                >
                    {regions.map(r => (
                        <option key={r} value={r}>{r === 'alle' ? 'Alle regioner' : r}</option>
                    ))}
                </select>
                <select
                    value={filterStatus}
                    onChange={e => setFilterStatus(e.target.value)}
                    className="text-xs bg-card border border-border rounded-lg px-2 py-1.5 text-foreground"
                >
                    <option value="alle">Alle statustyper</option>
                    <option value="non_compliant">Avvik</option>
                    <option value="partial">Delvis</option>
                </select>
            </div>

            {/* Properties with most avvik */}
            <Card className="bg-card border-border">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2">
                        <Building2 size={14} className="text-primary" />
                        Eiendommer med avvik ({filteredPortfolio.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="text-center py-8 text-muted text-sm">Laster avvik...</div>
                    ) : filteredPortfolio.length === 0 ? (
                        <div className="text-center py-8 text-muted text-sm">Ingen avvik registrert ✅</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr className="border-b border-border text-muted uppercase">
                                        <th className="text-left pb-2 pr-4">Eiendom</th>
                                        <th className="text-left pb-2 pr-4 hidden md:table-cell">Region</th>
                                        <th className="text-center pb-2 pr-3">Avvik</th>
                                        <th className="text-center pb-2 pr-3">Delvis</th>
                                        <th className="text-center pb-2 pr-3 hidden sm:table-cell">Forfalt</th>
                                        <th className="text-center pb-2">Rate</th>
                                        <th className="pb-2"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredPortfolio.map(p => (
                                        <tr key={p.property_id} className="border-b border-border/30 hover:bg-primary/5 transition-colors">
                                            <td className="py-2.5 pr-4 font-medium text-foreground">{p.property_name}</td>
                                            <td className="py-2.5 pr-4 text-muted hidden md:table-cell">{p.region ?? 'Nasjonal'}</td>
                                            <td className="py-2.5 pr-3 text-center">
                                                {p.non_compliant > 0
                                                    ? <span className="text-destructive font-bold">{p.non_compliant}</span>
                                                    : <span className="text-muted">0</span>}
                                            </td>
                                            <td className="py-2.5 pr-3 text-center">
                                                {p.partial > 0
                                                    ? <span className="text-warning font-bold">{p.partial}</span>
                                                    : <span className="text-muted">0</span>}
                                            </td>
                                            <td className="py-2.5 pr-3 text-center hidden sm:table-cell">
                                                {p.overdue_reviews > 0
                                                    ? <span className="text-orange-400 font-bold flex items-center justify-center gap-0.5"><Clock size={10} />{p.overdue_reviews}</span>
                                                    : <span className="text-muted">0</span>}
                                            </td>
                                            <td className="py-2.5 text-center">
                                                <span className={`font-semibold ${p.compliance_rate >= 0.9 ? 'text-success' : p.compliance_rate >= 0.6 ? 'text-warning' : 'text-destructive'}`}>
                                                    {Math.round(p.compliance_rate * 100)}%
                                                </span>
                                            </td>
                                            <td className="py-2.5 pl-2">
                                                <Link href={`/fdvu/${p.property_id}`}>
                                                    <ChevronRight size={14} className="text-muted hover:text-primary transition-colors" />
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Detailed avvik list */}
            {filteredAvvik.length > 0 && (
                <Card className="bg-card border-border">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <XCircle size={14} className="text-destructive" />
                            Detaljerte avvik ({filteredAvvik.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {filteredAvvik.slice(0, 100).map(a => (
                                <div key={a.assignment_id} className={`rounded-lg border p-3 text-xs ${isOverdue(a.next_review_date) ? 'border-orange-500/30 bg-orange-500/5' : 'border-border bg-card/50'}`}>
                                    <div className="flex items-start justify-between gap-2 flex-wrap">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                                <span className="font-medium text-foreground truncate">{a.requirement_title ?? a.requirement_code ?? 'Ukjent krav'}</span>
                                                {a.requirement_code && (
                                                    <Badge variant="outline" className="text-[10px] px-1.5 py-0">{a.requirement_code}</Badge>
                                                )}
                                                {a.regulation_set && (
                                                    <Badge className={`text-[10px] px-1.5 py-0 ${SEV_STYLE[a.severity ?? ''] ?? 'bg-border/50 text-muted border-border'}`}>
                                                        {REG_LABELS[a.regulation_set] ?? a.regulation_set}
                                                    </Badge>
                                                )}
                                                {a.severity && (
                                                    <Badge className={`text-[10px] px-1.5 py-0 ${SEV_STYLE[a.severity] ?? ''}`}>
                                                        {a.severity}
                                                    </Badge>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-3 text-muted flex-wrap">
                                                <span className="flex items-center gap-1">
                                                    <Building2 size={10} />
                                                    {a.property_name ?? a.property_id}
                                                </span>
                                                {a.property_region && <span>{a.property_region}</span>}
                                                {a.assessed_at && (
                                                    <span>Registrert {new Date(a.assessed_at).toLocaleDateString('nb-NO')}</span>
                                                )}
                                                {isOverdue(a.next_review_date) && (
                                                    <span className="text-orange-400 flex items-center gap-0.5">
                                                        <Clock size={10} /> Forfalt revisjon
                                                    </span>
                                                )}
                                            </div>
                                            {a.evidence_notes && (
                                                <div className="mt-1 text-muted italic">{a.evidence_notes}</div>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Badge className={`text-[10px] px-1.5 py-0 ${STATUS_STYLE[a.status]?.style ?? ''}`}>
                                                {STATUS_STYLE[a.status]?.label ?? a.status}
                                            </Badge>
                                            <Link href={`/fdvu/${a.property_id}`}>
                                                <ChevronRight size={14} className="text-muted hover:text-primary transition-colors" />
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* HMS cross-link */}
            <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-xl text-sm">
                <AlertTriangle size={16} className="text-warning flex-shrink-0" />
                <div className="flex-1 text-muted">
                    Fysiske sikkerhetsavvik (branntilløp, personskader, elektrisk) registreres i{' '}
                    <Link href="/deviations" className="text-primary hover:underline">HMS-avvikssystemet</Link>.
                    FDVU-avvik gjelder krav til bygningsteknisk standard og dokumentasjon.
                </div>
            </div>
        </div>
    );
}
