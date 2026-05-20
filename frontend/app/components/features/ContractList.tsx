import { Contract } from "@/lib/api";
import Link from "next/link";
import { FileText, Calendar, DollarSign, CheckCircle, XCircle, ArrowRight } from "lucide-react";
import PropertyMap from "./PropertyMap";

export default function ContractList({ contracts }: { contracts: Contract[] }) {
    if (!contracts || contracts.length === 0) {
        return (
            <div className="text-center p-8 bg-surface rounded-lg border border-dashed border-border">
                <p className="text-muted">Ingen kontrakter funnet.</p>
            </div>
        );
    }

    // Helper to format currency
    const formatAmount = (amount?: number, currency: string = "NOK") => {
        if (!amount) return "Ikke angitt";
        return new Intl.NumberFormat('no-NO', { style: 'currency', currency }).format(amount);
    };

    // Helper for status badge
    const StatusBadge = ({ status }: { status: string }) => {
        const isActive = status === 'active';
        return (
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                {isActive ? <CheckCircle size={12} /> : <XCircle size={12} />}
                {isActive ? 'Aktiv' : 'Avsluttet'}
            </span>
        );
    };

    return (
        <div className="grid grid-cols-1 gap-4">
            {contracts.map((contract) => {
                const hasMap = contract.property?.latitude && contract.property?.longitude;
                const propertyName = contract.property?.name || contract.property?.address || "Eiendom";
                
                return (
                    <div
                        key={contract.contract_id}
                        className="glass-card overflow-hidden group hover:bg-muted/10 transition-all relative"
                    >
                        <Link
                            href={`/contracts/${contract.contract_id}`}
                            className="p-6 flex flex-col lg:flex-row gap-6"
                        >
                            {/* Left side - Contract info */}
                            <div className="flex-1 flex items-start gap-4">
                                <div className="p-3 bg-primary/10 text-primary rounded-lg group-hover:bg-primary group-hover:text-white transition-colors">
                                    <FileText size={24} />
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-start justify-between gap-4 mb-2">
                                        <h3 className="font-bold text-foreground group-hover:text-primary transition-colors text-lg line-clamp-1">
                                            {contract.party?.name || "Ukjent Leietaker"}
                                        </h3>
                                        <StatusBadge status={contract.status} />
                                    </div>
                                    <div className="flex flex-col gap-1 mt-1">
                                        <span className="text-xs uppercase tracking-wide">
                                            {contract.property?.address ? (
                                                <span className="text-foreground font-bold">{contract.property?.address}</span>
                                            ) : (
                                                <span className="text-muted">Ingen Eiendom</span>
                                            )}
                                        </span>

                                        {/* Elements / Archive Reference display */}
                                        {(contract.external_data?.elements || contract.property?.external_data?.master_data?.archive_name) && (
                                            <div className="text-[10px] text-muted font-mono bg-muted/20 px-2 py-0.5 rounded self-start mt-1">
                                                Ref: {contract.external_data?.elements || contract.property?.external_data?.master_data?.archive_name}
                                            </div>
                                        )}

                                        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-sm text-muted font-medium">
                                            <div className="flex items-center gap-1">
                                                <Calendar size={14} className="text-primary" />
                                                <span>
                                                    {contract.periods?.[0]?.start_date ? new Date(contract.periods[0].start_date).toLocaleDateString('no-NO') : 'N/A'}
                                                    -
                                                    {contract.periods?.[0]?.end_date ? new Date(contract.periods[0].end_date).toLocaleDateString('no-NO') : 'Løpende'}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-1 text-foreground font-bold">
                                                <DollarSign size={14} className="text-emerald-500" />
                                                <span>{formatAmount(contract.amount?.amount_per_year, contract.amount?.currency)} / år</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right side - Map */}
                            {hasMap ? (
                                <div className="w-full lg:w-64 h-48 lg:h-32 rounded-lg overflow-hidden border border-border flex-shrink-0">
                                    <PropertyMap
                                        latitude={contract.property.latitude!}
                                        longitude={contract.property.longitude!}
                                        propertyName={propertyName}
                                    />
                                </div>
                            ) : (
                                <div className="w-full lg:w-64 h-48 lg:h-32 rounded-lg bg-muted/20 border border-border flex items-center justify-center flex-shrink-0">
                                    <span className="text-xs text-muted">Ingen kartdata</span>
                                </div>
                            )}
                        </Link>
                    </div>
                );
            })}
        </div>
    );
}
