"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getBufdirInstitutionsCatalog,
  type BufdirCatalogItem,
  type BufdirCatalogResponse,
} from "@/lib/api/bufdirCatalogApi";
import {
  getProperties,
  type Property,
} from "@/lib/api/propertiesApi";
import { getFinanceBudgetByProperty, type FinanceBudgetPropertyDetail } from "@/lib/api/financeBudgetApi";

const REGION_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Alle regioner (Bufetat + Bufdir)" },
  { value: "Nord", label: "Nord" },
  { value: "Midt-Norge", label: "Midt-Norge" },
  { value: "Vest", label: "Vest" },
  { value: "Sør", label: "Sør" },
  { value: "\u00d8st", label: "\u00d8st" },
  { value: "Bufdir", label: "Bufdir" },
];

function matchesQuery(row: BufdirCatalogItem, q: string): boolean {
  if (!q.trim()) return true;
  const s = q.trim().toLowerCase();
  const hay = [
    row.name,
    row.location,
    row.address,
    row.owner_type,
    ...(row.legal_bases ?? []),
    row.id != null ? String(row.id) : "",
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return hay.includes(s);
}

const fmtNok = (n: number) =>
  new Intl.NumberFormat("nb-NO", {
    style: "currency",
    currency: "NOK",
    maximumFractionDigits: 0,
  }).format(n);

function bufdirUrlFromProperty(p: Property): string | undefined {
  const ext = p.external_data as Record<string, unknown> | undefined;
  if (!ext) return undefined;
  const b = (ext.bufdir ?? ext.bufdir_institution) as Record<string, unknown> | undefined;
  if (!b) return undefined;
  const u = b.bufdir_url;
  return typeof u === "string" ? u : undefined;
}

function PortfolioCostDrilldown({
  property,
  onClose,
}: {
  property: Property;
  onClose: () => void;
}) {
  const pid = property.property_id;
  const [detail, setDetail] = useState<FinanceBudgetPropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const bufdirUrl = bufdirUrlFromProperty(property);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getFinanceBudgetByProperty(pid, 2026, "finance_dept_2026")
      .then((d) => { if (!cancelled) setDetail(d); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [pid]);

  const byCategory = detail?.by_category ?? {};
  const total = detail?.total ?? 0;

  const CAT_LABEL: Record<string, string> = {
    lokaler: "Lokaler (husleie)",
    drift: "Drift",
    vedlikehold: "Vedlikehold",
  };

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-4 space-y-4 text-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-foreground">{property.name ?? "Eiendom"}</h3>
          <p className="text-muted-foreground text-xs mt-0.5">
            {[property.address, property.postal_code, property.city].filter(Boolean).join(", ")}
          </p>
          <div className="flex flex-wrap gap-3 mt-2 text-xs">
            <Link className="text-primary underline" href={`/properties/${pid}`}>
              Åpne eiendomsside
            </Link>
            {bufdirUrl && (
              <a className="text-primary underline" href={bufdirUrl} target="_blank" rel="noreferrer">
                Bufdir (koblet data)
              </a>
            )}
          </div>
        </div>
        <button type="button" onClick={onClose} className="text-xs text-muted-foreground hover:text-foreground underline">
          Lukk
        </button>
      </div>

      <section className="space-y-1">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Budsjett 2026 — økonomiavd.
        </h4>
        {loading ? (
          <p className="text-xs text-muted-foreground">Laster…</p>
        ) : total === 0 ? (
          <p className="text-xs text-muted-foreground italic">Ingen budsjettdata for denne eiendommen.</p>
        ) : (
          <ul className="text-xs space-y-1 tabular-nums">
            {Object.entries(byCategory).map(([cat, amt]) => (
              <li key={cat} className="flex justify-between gap-4">
                <span>{CAT_LABEL[cat] ?? cat}</span>
                <span className="font-medium">{fmtNok(amt)}</span>
              </li>
            ))}
            <li className="flex justify-between gap-4 border-t border-border/50 pt-1 font-semibold">
              <span>Totalt</span>
              <span>{fmtNok(total)}</span>
            </li>
          </ul>
        )}
      </section>
    </div>
  );
}

export default function BufdirInstitutionsCatalogPage() {
  const [tab, setTab] = useState<"catalog" | "portfolio">("catalog");

  const [data, setData] = useState<BufdirCatalogResponse | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [onlyExternal, setOnlyExternal] = useState(false);

  const [portfolioRegion, setPortfolioRegion] = useState("");
  const [portfolioProps, setPortfolioProps] = useState<Property[]>([]);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [portfolioSearch, setPortfolioSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    setCatalogLoading(true);
    setCatalogError(null);
    (async () => {
      try {
        const res = await getBufdirInstitutionsCatalog();
        if (!cancelled) setData(res);
      } catch (e: unknown) {
        if (!cancelled) {
          setCatalogError(e instanceof Error ? e.message : "Kunne ikke hente katalog.");
        }
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadPortfolio = useCallback(async () => {
    setPortfolioLoading(true);
    setPortfolioError(null);
    try {
      const list = await getProperties(0, 10000, {
        region: portfolioRegion || undefined,
        source_coverage: "all",
        include_risk: false,
        order_by: "name",
        order_dir: "asc",
      });
      setPortfolioProps(list);
    } catch (e: unknown) {
      setPortfolioError(e instanceof Error ? e.message : "Kunne ikke hente eiendommer.");
      setPortfolioProps([]);
    } finally {
      setPortfolioLoading(false);
    }
  }, [portfolioRegion]);

  useEffect(() => {
    if (tab !== "portfolio") return;
    loadPortfolio();
  }, [tab, loadPortfolio]);

  const filteredCatalog = useMemo(() => {
    const items = data?.items ?? [];
    return items.filter((row) => {
      if (onlyExternal && row.in_befs_portfolio) return false;
      return matchesQuery(row, query);
    });
  }, [data, query, onlyExternal]);

  const filteredPortfolio = useMemo(() => {
    const q = portfolioSearch.trim().toLowerCase();
    if (!q) return portfolioProps;
    return portfolioProps.filter((p) => {
      const hay = [p.name, p.address, p.city, p.region, p.property_id].filter(Boolean).join(" ").toLowerCase();
      return hay.includes(q);
    });
  }, [portfolioProps, portfolioSearch]);

  return (
    <main className="p-6 space-y-6 max-w-[1400px] mx-auto">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Bufdir og portefølje</h1>
        <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
          Nasjonal institusjonskatalog fra Bufdir, og portefølje etter BEFS-region med kostnadsdrilldown (husleie,
          Dim4/kapittelpost, løpende GL).
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm pt-1">
          <Link className="text-primary underline font-medium" href="/admin/barnevern-docs">
            Barnevern-dokumenter
          </Link>
          <Link className="text-primary underline font-medium" href="/barnevern">
            Barnevern-simulering
          </Link>
          <a
            className="text-primary underline font-medium"
            href="https://www.bufdir.no/barnevern/finn-institusjon/"
            target="_blank"
            rel="noreferrer"
          >
            Åpne Bufdir (offisiell liste)
          </a>
        </div>
      </div>

      <div className="flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab("catalog")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "catalog"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Nasjonal katalog
        </button>
        <button
          type="button"
          onClick={() => setTab("portfolio")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "portfolio"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Portefølje etter region
        </button>
      </div>

      {tab === "catalog" && (
        <>
          {catalogLoading && <p className="text-muted-foreground">Laster katalog…</p>}
          {catalogError && <p className="text-red-600">{catalogError}</p>}

          {!catalogLoading && !catalogError && data && (
            <>
              <section className="rounded-xl border border-border bg-card/40 p-4 text-sm space-y-3">
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Søk</label>
                    <input
                      type="search"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Navn, sted, eierform, id…"
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer select-none pb-2">
                    <input
                      type="checkbox"
                      checked={onlyExternal}
                      onChange={(e) => setOnlyExternal(e.target.checked)}
                    />
                    <span>Kun uten BEFS-eiendom</span>
                  </label>
                </div>
                <p className="text-muted-foreground">
                  <span className="font-medium text-foreground">{data.count}</span> i katalog (kilde:{" "}
                  <code className="text-xs bg-muted px-1 rounded">{data.source_file}</code>
                  ).{" "}
                  <span className="font-medium text-foreground">{data.matched_count}</span> med treff mot eiendom i BEFS.
                  Viser nå <span className="font-medium text-foreground">{filteredCatalog.length}</span> rader.
                </p>
              </section>

              <div className="overflow-auto border border-border rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 sticky top-0 z-10">
                    <tr>
                      <th className="text-left p-2 font-medium">Navn</th>
                      <th className="text-left p-2 font-medium">Sted</th>
                      <th className="text-left p-2 font-medium">Eierform</th>
                      <th className="text-left p-2 font-medium">BEFS</th>
                      <th className="text-left p-2 font-medium">Lenker</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCatalog.map((row) => (
                      <tr
                        key={`${row.id ?? "x"}-${row.bufdir_url ?? row.name}`}
                        className="border-t border-border"
                      >
                        <td className="p-2 align-top">
                          <div className="font-medium">{row.name ?? "—"}</div>
                          {row.address && (
                            <div className="text-xs text-muted-foreground mt-0.5 whitespace-pre-wrap">
                              {row.address}
                            </div>
                          )}
                        </td>
                        <td className="p-2 align-top text-muted-foreground">{row.location ?? "—"}</td>
                        <td className="p-2 align-top">{row.owner_type ?? "—"}</td>
                        <td className="p-2 align-top">
                          {row.in_befs_portfolio && row.property_id ? (
                            <Link
                              className="text-primary underline"
                              href={`/properties/${row.property_id}`}
                            >
                              Eiendom
                            </Link>
                          ) : (
                            <span className="text-muted-foreground">Ikke i portefølje</span>
                          )}
                        </td>
                        <td className="p-2 align-top space-x-2 whitespace-nowrap">
                          {row.bufdir_url && (
                            <a
                              className="text-primary underline"
                              href={row.bufdir_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Bufdir
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}

      {tab === "portfolio" && (
        <div className="space-y-4">
          <section className="rounded-xl border border-border bg-card/40 p-4 text-sm space-y-3">
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Region</label>
                <select
                  value={portfolioRegion}
                  onChange={(e) => {
                    setPortfolioRegion(e.target.value);
                    setSelectedProperty(null);
                  }}
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm min-w-[220px]"
                >
                  {REGION_OPTIONS.map((o) => (
                    <option key={o.value || "all"} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-medium text-muted-foreground mb-1">Søk i liste</label>
                <input
                  type="search"
                  value={portfolioSearch}
                  onChange={(e) => setPortfolioSearch(e.target.value)}
                  placeholder="Navn, adresse, region, id…"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <button
                type="button"
                onClick={() => loadPortfolio()}
                className="px-3 py-2 text-sm rounded-md border border-border bg-background hover:bg-muted/40"
              >
                Oppdater
              </button>
            </div>
            <p className="text-muted-foreground text-xs">
              Listen følger feltet <code className="bg-muted px-1 rounded">region</code> på eiendommen (samme som i BEFS-eksport).
              «Bufdir» er egen verdi. Tilgang styres av din brukerrolle.
            </p>
          </section>

          {portfolioError && <p className="text-red-600 text-sm">{portfolioError}</p>}
          {portfolioLoading && <p className="text-muted-foreground text-sm">Laster eiendommer…</p>}

          {!portfolioLoading && (
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{filteredPortfolio.length}</span> eiendommer
              {portfolioRegion ? ` (region: ${portfolioRegion})` : ""}.
            </p>
          )}

          {selectedProperty && (
            <PortfolioCostDrilldown property={selectedProperty} onClose={() => setSelectedProperty(null)} />
          )}

          {!portfolioLoading && (
            <div className="overflow-auto border border-border rounded-lg">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 sticky top-0 z-10">
                  <tr>
                    <th className="text-left p-2 font-medium">Navn</th>
                    <th className="text-left p-2 font-medium">Adresse</th>
                    <th className="text-left p-2 font-medium">Region</th>
                    <th className="text-left p-2 font-medium">Handling</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPortfolio.map((p) => (
                    <tr
                      key={p.property_id}
                      className={`border-t border-border cursor-pointer hover:bg-muted/30 ${
                        selectedProperty?.property_id === p.property_id ? "bg-primary/10" : ""
                      }`}
                      onClick={() => setSelectedProperty(p)}
                    >
                      <td className="p-2 align-top font-medium">{p.name ?? "—"}</td>
                      <td className="p-2 align-top text-muted-foreground text-xs">
                        {[p.address, p.postal_code, p.city].filter(Boolean).join(", ")}
                      </td>
                      <td className="p-2 align-top">{p.region ?? "—"}</td>
                      <td className="p-2 align-top whitespace-nowrap">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedProperty(p);
                          }}
                          className="text-primary underline text-xs"
                        >
                          Vis kostnader
                        </button>
                        <Link
                          className="text-primary underline text-xs ml-3"
                          href={`/properties/${p.property_id}`}
                          onClick={(e) => e.stopPropagation()}
                        >
                          Eiendom
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
