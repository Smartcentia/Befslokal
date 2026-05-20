"use client";

import { useEffect, useState } from "react";
import { Building2, Plus, X, TrendingUp, Users, FileText } from "lucide-react";
import Link from "next/link";
import {
    listOrganisations,
    createOrganisation,
    getOrganisationKPI,
    Organisation,
    OrganisationCreate,
    OrganisationKPI,
} from "@/lib/api/organisationApi";

function formatNOK(amount: number | null): string {
    if (amount == null) return "—";
    return new Intl.NumberFormat("nb-NO", {
        style: "currency",
        currency: "NOK",
        maximumFractionDigits: 0,
    }).format(amount);
}

interface OrgWithKPI {
    org: Organisation;
    kpi: OrganisationKPI | null;
}

export default function OrganisasjonerPage() {
    const [orgs, setOrgs] = useState<OrgWithKPI[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState<OrganisationCreate>({
        name: "",
        region_code: "",
        org_nr: "",
        contact_email: "",
        budget_target_nok: null,
        is_active: true,
    });
    const [saving, setSaving] = useState(false);

    async function load() {
        setLoading(true);
        setError(null);
        try {
            const data = await listOrganisations();
            const withKPI = await Promise.all(
                data.map(async (org) => {
                    try {
                        const kpi = await getOrganisationKPI(org.org_id);
                        return { org, kpi };
                    } catch {
                        return { org, kpi: null };
                    }
                })
            );
            setOrgs(withKPI);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Feil ved lasting");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load();
    }, []);

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        setSaving(true);
        try {
            await createOrganisation(form);
            setShowModal(false);
            setForm({ name: "", region_code: "", org_nr: "", contact_email: "", budget_target_nok: null, is_active: true });
            await load();
        } catch (e: unknown) {
            alert(e instanceof Error ? e.message : "Feil ved opprettelse");
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                        <Building2 size={22} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">Organisasjoner</h1>
                        <p className="text-sm text-muted-foreground">Bufetat regioner og organisasjonsenheter</p>
                    </div>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                    <Plus size={16} />
                    Ny organisasjon
                </button>
            </div>

            {/* Error */}
            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                    {error}
                </div>
            )}

            {/* Loading */}
            {loading ? (
                <div className="flex items-center justify-center h-48 text-muted-foreground text-sm">
                    Laster organisasjoner...
                </div>
            ) : (
                <>
                    {/* Table */}
                    <div className="bg-card border border-border rounded-xl overflow-hidden mb-8">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-muted/50 border-b border-border">
                                    <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Navn</th>
                                    <th className="text-left px-4 py-3 font-semibold text-muted-foreground">Region</th>
                                    <th className="text-right px-4 py-3 font-semibold text-muted-foreground">Eiendommer</th>
                                    <th className="text-right px-4 py-3 font-semibold text-muted-foreground">Brukere</th>
                                    <th className="text-right px-4 py-3 font-semibold text-muted-foreground">Budsjettmål</th>
                                    <th className="text-center px-4 py-3 font-semibold text-muted-foreground">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orgs.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="text-center py-10 text-muted-foreground">
                                            Ingen organisasjoner funnet
                                        </td>
                                    </tr>
                                ) : (
                                    orgs.map(({ org, kpi }) => (
                                        <tr key={org.org_id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                                            <td className="px-4 py-3">
                                                <Link
                                                    href={`/admin/organisasjoner/${org.org_id}`}
                                                    className="font-medium text-blue-600 hover:underline"
                                                >
                                                    {org.name}
                                                </Link>
                                            </td>
                                            <td className="px-4 py-3 text-muted-foreground">{org.region_code ?? "—"}</td>
                                            <td className="px-4 py-3 text-right">{kpi?.property_count ?? "—"}</td>
                                            <td className="px-4 py-3 text-right">{kpi?.user_count ?? "—"}</td>
                                            <td className="px-4 py-3 text-right">{formatNOK(org.budget_target_nok)}</td>
                                            <td className="px-4 py-3 text-center">
                                                <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${org.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                                                    {org.is_active ? "Aktiv" : "Inaktiv"}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* KPI Cards grid */}
                    {orgs.length > 0 && (
                        <div>
                            <h2 className="text-lg font-semibold mb-4 text-foreground">KPI per organisasjon</h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {orgs.map(({ org, kpi }) => (
                                    <Link
                                        key={org.org_id}
                                        href={`/admin/organisasjoner/${org.org_id}`}
                                        className="bg-card border border-border rounded-xl p-4 hover:shadow-md transition-shadow"
                                    >
                                        <div className="flex items-center gap-2 mb-3">
                                            <Building2 size={16} className="text-blue-600" />
                                            <span className="font-semibold text-sm text-foreground">{org.name}</span>
                                        </div>
                                        {kpi ? (
                                            <div className="space-y-2">
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="flex items-center gap-1 text-muted-foreground">
                                                        <FileText size={12} /> Aktive kontrakter
                                                    </span>
                                                    <span className="font-medium">{kpi.active_contracts}</span>
                                                </div>
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="flex items-center gap-1 text-muted-foreground">
                                                        <TrendingUp size={12} /> Mnd. husleie
                                                    </span>
                                                    <span className="font-medium">{formatNOK(kpi.total_monthly_rent_nok)}</span>
                                                </div>
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="flex items-center gap-1 text-muted-foreground">
                                                        <Users size={12} /> Brukere
                                                    </span>
                                                    <span className="font-medium">{kpi.user_count}</span>
                                                </div>
                                                <div className="pt-2 border-t border-border">
                                                    <div className="flex items-center justify-between text-xs mb-1">
                                                        <span className="text-muted-foreground">Compliance</span>
                                                        <span className="font-semibold">{Math.round(kpi.compliance_rate * 100)}%</span>
                                                    </div>
                                                    <div className="w-full bg-muted rounded-full h-1.5">
                                                        <div
                                                            className="bg-blue-600 h-1.5 rounded-full"
                                                            style={{ width: `${Math.round(kpi.compliance_rate * 100)}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-xs text-muted-foreground">Ingen KPI-data</p>
                                        )}
                                    </Link>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-foreground">Ny organisasjon</h2>
                            <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                                <X size={20} />
                            </button>
                        </div>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">Navn *</label>
                                <input
                                    required
                                    className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                                    value={form.name}
                                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">Regionkode</label>
                                <input
                                    className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                                    placeholder="f.eks. Øst, Nord, Vest…"
                                    value={form.region_code ?? ""}
                                    onChange={(e) => setForm({ ...form, region_code: e.target.value || null })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">Org.nr</label>
                                <input
                                    className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                                    placeholder="9 siffer"
                                    value={form.org_nr ?? ""}
                                    onChange={(e) => setForm({ ...form, org_nr: e.target.value || null })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">Kontakt-e-post</label>
                                <input
                                    type="email"
                                    className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                                    value={form.contact_email ?? ""}
                                    onChange={(e) => setForm({ ...form, contact_email: e.target.value || null })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-foreground mb-1">Budsjettmål (NOK/år)</label>
                                <input
                                    type="number"
                                    className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background text-foreground"
                                    value={form.budget_target_nok ?? ""}
                                    onChange={(e) =>
                                        setForm({ ...form, budget_target_nok: e.target.value ? Number(e.target.value) : null })
                                    }
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-sm border border-border rounded-lg text-foreground hover:bg-muted transition-colors"
                                >
                                    Avbryt
                                </button>
                                <button
                                    type="submit"
                                    disabled={saving}
                                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                                >
                                    {saving ? "Lagrer..." : "Opprett"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
