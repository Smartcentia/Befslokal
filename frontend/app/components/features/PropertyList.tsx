"use client";

import { useState, Fragment } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Property } from "@/lib/api";
import DataTooltip from "@/app/components/ui/DataTooltip";

/** Map property_id -> total_annual_budget (2026). */
export type BudgetByProperty = Map<string, number>;

export type SortColumn = "name" | "address" | "city" | "region" | "usage";

interface PropertyListProps {
    properties: Property[];
    /** Valgfritt: budsjett per eiendom for å vise kolonne. */
    budgetByProperty?: BudgetByProperty;
    sortBy?: SortColumn;
    sortDir?: "asc" | "desc";
    onSort?: (column: SortColumn) => void;
    /** Avdelinger gruppert per forelderens unit_id_erp. */
    avdelingerByParentErpId?: Map<string, Property[]>;
}

const formatCurrency = (n: number) =>
    new Intl.NumberFormat("nb-NO", { style: "currency", currency: "NOK", maximumFractionDigits: 0 }).format(n);

function SortIcon({ active, dir }: { active: boolean; dir?: "asc" | "desc" }) {
    return (
        <span className={`inline-flex flex-col leading-none ml-1 text-[9px] ${active ? "text-primary" : "text-muted/30"}`}>
            <span className={active && dir === "asc" ? "text-primary" : ""}>▲</span>
            <span className={active && dir === "desc" ? "text-primary" : ""}>▼</span>
        </span>
    );
}

function SortableTh({
    column,
    sortBy,
    sortDir,
    onSort,
    tooltip,
    children,
    className = "",
}: {
    column: SortColumn;
    sortBy?: SortColumn;
    sortDir?: "asc" | "desc";
    onSort?: (col: SortColumn) => void;
    tooltip: string;
    children: React.ReactNode;
    className?: string;
}) {
    const active = sortBy === column;
    return (
        <th
            className={`px-6 py-4 cursor-pointer select-none hover:bg-muted/5 transition-colors ${className}`}
            onClick={() => onSort?.(column)}
        >
            <div className="flex items-center gap-0.5">
                <DataTooltip content={tooltip}>{children}</DataTooltip>
                <SortIcon active={active} dir={active ? sortDir : undefined} />
            </div>
        </th>
    );
}

export default function PropertyList({ properties, budgetByProperty, sortBy, sortDir, onSort, avdelingerByParentErpId }: PropertyListProps) {
    const router = useRouter();
    const [expandedErpIds, setExpandedErpIds] = useState<Set<string>>(new Set());

    const toggleExpanded = (erpId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setExpandedErpIds((prev) => {
            const next = new Set(prev);
            if (next.has(erpId)) {
                next.delete(erpId);
            } else {
                next.add(erpId);
            }
            return next;
        });
    };

    if (properties.length === 0) {
        return (
            <div className="rounded-lg border border-border bg-muted/20 px-4 py-5 text-sm text-foreground max-w-2xl">
                <p className="font-medium text-foreground mb-2">Ingen eiendommer å vise</p>
                <p className="text-muted mb-3">
                    Listen er tom fordi du ikke har tilgang til noen eiendommer med gjeldende filtre, eller fordi ingen eiendommer matcher søket.
                </p>
                <p className="text-muted">
                    <strong className="text-foreground font-medium">Eiendomsforvalter og vaktmester:</strong> dere ser kun eiendommer som administrator har knyttet til brukeren i brukeradministrasjonen. Uten slike koblinger blir listen tom, og enkelt-eiendommer gir 403 («ikke tildelt denne eiendommen») i nettleserkonsollen.
                </p>
                <p className="text-muted mt-3">
                    <strong className="text-foreground font-medium">Regional leder:</strong> krever at feltet region på brukeren stemmer med eiendommenes region.
                </p>
            </div>
        );
    }

    // Number of columns for colSpan (8 base + 1 if budget)
    const colCount = budgetByProperty != null ? 9 : 8;

    return (
        <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
                <table className="enterprise-table">
                    <thead>
                        <tr>
                            <SortableTh column="name" sortBy={sortBy} sortDir={sortDir} onSort={onSort} tooltip="Navn på eiendom: Offisielt navn eller adresse fra eiendomsregister.">
                                Navn på eiendom
                            </SortableTh>
                            <SortableTh column="address" sortBy={sortBy} sortDir={sortDir} onSort={onSort} tooltip="Adresse: Gateadresse for eiendommen.">
                                Adresse
                            </SortableTh>
                            <SortableTh column="city" sortBy={sortBy} sortDir={sortDir} onSort={onSort} tooltip="Poststed: Postnummer og stedsnavn.">
                                Poststed
                            </SortableTh>
                            <th className="px-6 py-4">
                                <DataTooltip content="Avdeling: Avdelingens koststed og navn fra CSV (1:1 med institusjon).">Avdeling</DataTooltip>
                            </th>
                            <th className="px-6 py-4">
                                <DataTooltip content="Ansvarlig: Overordnet institusjon for avdelinger, eller tildelt forvalter for eiendommer.">Ansvarlig</DataTooltip>
                            </th>
                            <SortableTh column="region" sortBy={sortBy} sortDir={sortDir} onSort={onSort} tooltip="Region: Geografisk region (f.eks. Vestlandet, Østlandet).">
                                Region
                            </SortableTh>
                            <SortableTh column="usage" sortBy={sortBy} sortDir={sortDir} onSort={onSort} tooltip="Type: Formålsbygg (barnevernsinstitusjon), Familievernkontor, Kontor.">
                                Type
                            </SortableTh>
                            {budgetByProperty != null && (
                                <th className="px-6 py-4 text-right font-bold text-emerald-600 dark:text-emerald-500 uppercase text-xs tracking-wider">
                                    <DataTooltip content="Budsjett 2026: Årlig budsjett for eiendommen. Generert fra forbruk eller manuelt.">Budsjett 2026</DataTooltip>
                                </th>
                            )}
                            <th className="px-6 py-4 w-10" aria-label="Naviger"></th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {properties.map((property) => {
                            const subAvd = property.unit_id_erp
                                ? (avdelingerByParentErpId?.get(property.unit_id_erp) ?? [])
                                : [];
                            const hasAvd = subAvd.length > 0;
                            const isExpanded = property.unit_id_erp ? expandedErpIds.has(property.unit_id_erp) : false;

                            return (
                                <Fragment key={property.property_id}>
                                    {/* ── Hoved-rad ── */}
                                    <tr
                                        onClick={() => router.push(`/properties/${property.property_id}`)}
                                        className="group transition-colors cursor-pointer"
                                    >
                                        <td className="px-6 py-5 font-bold text-foreground group-hover:text-primary transition-colors">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                {property.bufdir_image_path && (
                                                    // eslint-disable-next-line @next/next/no-img-element
                                                    <img
                                                        src={property.bufdir_image_path}
                                                        alt=""
                                                        className="w-9 h-9 rounded-md object-cover border border-border shrink-0 hidden sm:block"
                                                    />
                                                )}
                                                {hasAvd && (
                                                    <button
                                                        type="button"
                                                        aria-label={isExpanded ? "Skjul avdelinger" : "Vis avdelinger"}
                                                        onClick={(e) => toggleExpanded(property.unit_id_erp!, e)}
                                                        className={`flex-shrink-0 w-5 h-5 rounded flex items-center justify-center transition-all
                                                            bg-primary/10 hover:bg-primary/20 text-primary text-[10px] font-bold
                                                            ${isExpanded ? "rotate-90" : ""}`}
                                                    >
                                                        ▶
                                                    </button>
                                                )}
                                                {property.name || "-"}
                                                {hasAvd && (
                                                    <span className="text-[10px] font-normal text-muted bg-muted/10 border border-border rounded-full px-1.5 py-0.5">
                                                        {subAvd.length} avd.
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-muted">
                                            {property.address || "Adresse mangler"}
                                        </td>
                                        <td className="px-6 py-5 text-muted text-xs">
                                            <div>
                                                {property.postal_code || ""} {property.city || property.municipality || ""}
                                                {!property.postal_code && !property.city && !property.municipality && "Sted ukjent"}
                                            </div>
                                        </td>
                                        <td className="px-6 py-5 text-muted text-xs">
                                            {property.department_name || property.department_code ? (
                                                <span title={property.department_code}>{property.department_name || property.department_code}</span>
                                            ) : (
                                                "–"
                                            )}
                                        </td>
                                        <td className="px-6 py-5">
                                            {property.unit_short_type === "Avdeling" ? (
                                                property.affiliation ? (
                                                    property.parent_property_id ? (
                                                        <Link
                                                            href={`/properties/${property.parent_property_id}`}
                                                            className="text-xs text-primary hover:underline font-medium"
                                                            title={property.affiliation}
                                                            onClick={(e) => e.stopPropagation()}
                                                        >
                                                            {property.affiliation}
                                                        </Link>
                                                    ) : (
                                                        <span className="text-xs text-foreground font-medium" title={property.affiliation}>
                                                            {property.affiliation}
                                                        </span>
                                                    )
                                                ) : (
                                                    <span className="text-muted italic text-[11px]">Ukjent</span>
                                                )
                                            ) : (
                                                <div className="flex -space-x-1.5 items-center">
                                                    {property.managers && property.managers.length > 0 ? (
                                                        <>
                                                            {property.managers.slice(0, 2).map((m) => (
                                                                <div key={m.user_id} className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 border border-white dark:border-slate-800 flex items-center justify-center text-[10px] font-bold text-blue-600 dark:text-blue-400" title={m.name}>
                                                                    {m.name?.charAt(0) || "U"}
                                                                </div>
                                                            ))}
                                                            <span className="ml-2 text-xs text-foreground font-medium">
                                                                {property.managers[0].name}
                                                                {property.managers.length > 1 && ` (+${property.managers.length - 1})`}
                                                            </span>
                                                        </>
                                                    ) : (
                                                        <span className="text-muted italic text-[11px]">—</span>
                                                    )}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-6 py-5 text-muted text-xs font-mono">
                                            {property.region || "-"}
                                        </td>
                                        <td className="px-6 py-5">
                                            <span className="px-2 py-1 rounded bg-muted/10 text-[10px] font-bold uppercase tracking-wider text-muted border border-border">
                                                {property.usage?.toLowerCase() === 'barnevernsinstitusjon' ? 'Formålsbygg' : (property.usage || "Næring")}
                                            </span>
                                        </td>
                                        {budgetByProperty != null && (
                                            <td className="px-6 py-5 text-right font-mono text-emerald-700 dark:text-emerald-400 text-sm">
                                                {budgetByProperty.has(property.property_id)
                                                    ? formatCurrency(budgetByProperty.get(property.property_id)!)
                                                    : "—"}
                                            </td>
                                        )}
                                        <td className="px-6 py-5 text-right">
                                            <span className="text-primary group-hover:translate-x-1 transition-transform inline-block font-bold">
                                                →
                                            </span>
                                        </td>
                                    </tr>

                                    {/* ── Avdeling-rader (ekspandert) ── */}
                                    {isExpanded && subAvd.map((avd) => (
                                        <tr
                                            key={avd.property_id}
                                            onClick={() => router.push(`/properties/${avd.property_id}`)}
                                            className="cursor-pointer bg-muted/5 hover:bg-primary/5 transition-colors border-l-2 border-primary/30"
                                        >
                                            <td className="pl-14 pr-6 py-3 text-foreground">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-muted/40 text-xs select-none">└</span>
                                                    <span className="font-medium text-sm">{avd.name || "–"}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-3 text-muted text-xs">
                                                {avd.address || "–"}
                                            </td>
                                            <td className="px-6 py-3 text-muted text-xs">
                                                {avd.postal_code || ""} {avd.city || avd.municipality || ""}
                                            </td>
                                            <td className="px-6 py-3 text-muted text-xs">
                                                {avd.department_name || avd.department_code || "–"}
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className="text-[10px] text-muted/60 italic">Underenhet</span>
                                            </td>
                                            <td className="px-6 py-3 text-muted text-xs font-mono">
                                                {avd.region || "-"}
                                            </td>
                                            <td className="px-6 py-3">
                                                <span className="px-2 py-0.5 rounded bg-primary/10 text-[10px] font-bold uppercase tracking-wider text-primary/70 border border-primary/20">
                                                    Avdeling
                                                </span>
                                            </td>
                                            {budgetByProperty != null && (
                                                <td className="px-6 py-3 text-right font-mono text-emerald-700 dark:text-emerald-400 text-xs">
                                                    {budgetByProperty.has(avd.property_id)
                                                        ? formatCurrency(budgetByProperty.get(avd.property_id)!)
                                                        : "—"}
                                                </td>
                                            )}
                                            <td className="px-6 py-3 text-right">
                                                <span className="text-primary/50 text-xs">→</span>
                                            </td>
                                        </tr>
                                    ))}
                                </Fragment>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
