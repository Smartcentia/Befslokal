import { Metadata } from 'next';
import Link from 'next/link';
import { API_BASE_URL } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, FileText, ExternalLink } from 'lucide-react';
import type { Requirement } from '@/lib/api/fdvuApi';

export const metadata: Metadata = { title: 'Kravkatalog | FDVU' };

async function getRequirements(): Promise<Requirement[]> {
    if (!API_BASE_URL) return [];
    const token = process.env.NEXT_PUBLIC_BACKEND_SECRET || 'befs-super-secret-key-12345';
    try {
        const res = await fetch(`${API_BASE_URL}/fdvu/requirements`, {
            cache: 'no-store',
            headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return [];
        return res.json();
    } catch {
        return [];
    }
}

const REGULATION_LABELS: Record<string, string> = {
    RKL6:                'Risikoklasse 6 – Brann',
    BVL:                 'Barnevernloven',
    TEK17:               'TEK17 – Teknisk forskrift',
    HMS:                 'HMS / Arbeidsmiljøloven',
    KVALITETSFORSKRIFTEN:'Kvalitetsforskriften',
    INTERN:              'Interne krav',
    DRIFTSLEDELSE:       'Driftsledelse',
    ENOK:                'Energieffektivisering (ENOK)',
    UU:                  'Universell utforming',
    SIKKERHET:           'Sikkerhet og personvern',
    MILJØ:               'Miljø og farlige stoffer',
    BYGG:                'Bygg – NS3451 tilstandsanalyse',
};

const SEV_META: Record<string, { label: string; cls: string }> = {
    critical: { label: 'Kritisk',  cls: 'bg-destructive/15 text-destructive border-destructive/30' },
    high:     { label: 'Høy',      cls: 'bg-orange-500/15 text-orange-400 border-orange-500/30' },
    medium:   { label: 'Middels',  cls: 'bg-warning/15 text-warning border-warning/30' },
    low:      { label: 'Lav',      cls: 'bg-success/15 text-success border-success/30' },
};

const REG_COLORS: Record<string, string> = {
    RKL6:                'bg-red-500/10 text-red-400 border-red-500/30',
    BVL:                 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    TEK17:               'bg-blue-500/10 text-blue-400 border-blue-500/30',
    HMS:                 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    KVALITETSFORSKRIFTEN:'bg-teal-500/10 text-teal-400 border-teal-500/30',
    INTERN:              'bg-gray-500/10 text-gray-400 border-gray-500/30',
    DRIFTSLEDELSE:       'bg-sky-500/10 text-sky-400 border-sky-500/30',
    ENOK:                'bg-green-500/10 text-green-400 border-green-500/30',
    UU:                  'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    SIKKERHET:           'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    MILJØ:               'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    BYGG:                'bg-stone-500/10 text-stone-400 border-stone-500/30',
};

export default async function KravkatalogPage() {
    const requirements = await getRequirements();

    // Group by regulation_set
    const grouped = requirements.reduce<Record<string, Requirement[]>>((acc, r) => {
        if (!acc[r.regulation_set]) acc[r.regulation_set] = [];
        acc[r.regulation_set].push(r);
        return acc;
    }, {});

    const regulationOrder = ['RKL6', 'BVL', 'KVALITETSFORSKRIFTEN', 'HMS', 'TEK17', 'DRIFTSLEDELSE', 'ENOK', 'UU', 'SIKKERHET', 'MILJØ', 'BYGG', 'INTERN'];
    const sortedGroups = regulationOrder.filter(r => grouped[r]).concat(
        Object.keys(grouped).filter(r => !regulationOrder.includes(r))
    );

    return (
        <div className="p-6 space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Link href="/fdvu" className="text-muted hover:text-foreground transition-colors">
                    <ChevronLeft size={20} />
                </Link>
                <div>
                    <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <FileText className="text-primary" size={22} />
                        Kravkatalog
                    </h1>
                    <p className="text-muted text-xs mt-0.5">
                        {requirements.length} krav fra {sortedGroups.length} regelverk
                    </p>
                </div>
            </div>

            {/* Groups */}
            {sortedGroups.map(reg => {
                const reqs = grouped[reg];
                const regColor = REG_COLORS[reg] ?? 'bg-primary/10 text-primary border-primary/30';
                return (
                    <Card key={reg} className="bg-card border-border">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm font-semibold flex items-center gap-2">
                                <Badge className={`text-xs ${regColor}`}>
                                    {REGULATION_LABELS[reg] ?? reg}
                                </Badge>
                                <span className="text-muted font-normal">({reqs.length} krav)</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {reqs.map(req => {
                                    const sev = SEV_META[req.severity_if_breached ?? ''];
                                    return (
                                        <div key={req.requirement_id} className="border border-border/60 rounded-lg px-4 py-3">
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap mb-1">
                                                        <span className="font-mono text-xs text-muted bg-background px-1.5 py-0.5 rounded">{req.code}</span>
                                                        {sev && (
                                                            <Badge className={`text-xs px-1.5 py-0 ${sev.cls}`}>{sev.label}</Badge>
                                                        )}
                                                        {!req.is_mandatory && (
                                                            <Badge variant="outline" className="text-xs text-muted">Valgfritt</Badge>
                                                        )}
                                                    </div>
                                                    <div className="font-medium text-foreground text-sm">{req.title}</div>
                                                    {req.description && (
                                                        <p className="text-xs text-muted mt-1 leading-relaxed">{req.description}</p>
                                                    )}
                                                    <div className="flex flex-wrap gap-3 mt-2 text-xs text-muted">
                                                        <span>Gjelder: <span className="text-foreground">{req.applies_to}</span></span>
                                                        {req.category && <span>Kategori: <span className="text-foreground">{req.category}</span></span>}
                                                        {req.effective_from && <span>Fra: <span className="text-foreground">{req.effective_from}</span></span>}
                                                    </div>
                                                </div>
                                                {req.source_url && (
                                                    <a
                                                        href={req.source_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="shrink-0 text-muted hover:text-primary transition-colors"
                                                        title="Åpne kilde"
                                                    >
                                                        <ExternalLink size={14} />
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                );
            })}

            {requirements.length === 0 && (
                <div className="text-center py-16 text-muted text-sm">
                    Ingen krav i katalogen. Kjør seed-scriptet på backend.
                </div>
            )}
        </div>
    );
}
