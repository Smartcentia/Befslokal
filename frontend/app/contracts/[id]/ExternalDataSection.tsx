"use client";

import React from "react";

/** Norsk etikett-mapping for external_data-nøkler */
const LABEL_MAP: Record<string, string> = {
  elements: "Arkivreferanse (Elements)",
  avtalenavn: "Avtalenavn",
  contract_name: "Avtalenavn",
  region: "Region",
  p_plasser: "P-plasser",
  parking_spaces: "P-plasser",
  leieregulering: "Indeksregulering",
  regulation_type: "Indeksregulering",
  forlengelse_vilkår: "Opsjon / Forlengelse",
  extension_terms: "Opsjon / Forlengelse",
  utleier: "Utleier",
  lokalisering: "Lokalisering",
  kommentar: "Kommentar",
  deposit: "Depositum",
};

/** Nøkler som ikke skal vises i Tilleggsopplysninger */
const EXCLUDED_KEYS = new Set([
  "filnavn",
  "parsing_warning",
  "is_outlier",
  "is_summary_contract",
  "original_rent_string",
  // Kostnader – vises i Kostnadsfordeling
  "common_costs",
  "internal_maintenance_cost",
  "user_dependent_costs",
  "energy_cost",
  "heating_cost",
  "municipal_fees",
  "deposit",
  "total_annual_cost", // Sum alle kontrakter i komplekset – forvirrende på enkeltkontrakt
]);

interface ExternalDataSectionProps {
  data: Record<string, unknown>;
}

export const ExternalDataSection: React.FC<ExternalDataSectionProps> = ({
  data,
}) => {
  if (!data || typeof data !== "object") return null;

  const entries = Object.entries(data).filter(([key, value]) => {
    if (EXCLUDED_KEYS.has(key)) return false;
    if (value == null || value === "") return false;
    if (typeof value === "object" && !Array.isArray(value)) return false;
    return true;
  });

  if (entries.length === 0) return null;

  return (
    <div className="mt-8 pt-8 border-t border-border">
      <h3 className="text-sm font-semibold text-foreground mb-4 uppercase tracking-wider">
        Tilleggsopplysninger
      </h3>
      <div className="rounded-xl border border-border bg-surface/50 p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {entries.map(([key, value]) => {
            const label = LABEL_MAP[key] ?? key.replace(/_/g, " ");
            const display =
              typeof value === "number"
                ? new Intl.NumberFormat("nb-NO", {
                    style: "currency",
                    currency: "NOK",
                    maximumFractionDigits: 0,
                  }).format(value)
                : String(value);

            return (
              <div
                key={key}
                className="flex flex-col gap-1 p-3 rounded-lg bg-background/50 border border-border/50"
              >
                <div className="text-[11px] font-medium text-muted uppercase tracking-wider">
                  {label}
                </div>
                <div className="text-sm font-medium text-foreground break-words">
                  {display}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
