"use client";
import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  getProcurementPivot, getDynamicPivot, getPerRegionPivot,
  getInstitutionDetail, getPropertyProfiles,
  ProcurementPivot, ProcurementGroup, ProcurementCategory,
  DynamicPivot, DynamicPivotGroup,
  PerRegionPivot, PerRegionGroup, PerRegionAccount,
  InstitutionDetail, PropertyProfiles,
} from '@/lib/api/procurementApi';

const REGIONS = ['Midt-Norge', 'Nord', 'Sør', 'Vest', 'Øst', 'Bufdir', 'Øvrig'];
const YEARS = [2025, 2024, 2023, 2022, 2021, 2020];

type ViewMode = 'predefined' | 'dynamic' | 'per-region' | 'profiles';

function fmt(n: number | null | undefined): string {
  if (n == null || !n) return '–';
  return Math.round(n).toLocaleString('no-NO');
}

// ─── Institution detail sidepanel ────────────────────────────────────────────

function InstitutionPanel({ name, year, onClose }: {
  name: string;
  year?: number;
  onClose: () => void;
}) {
  const [data, setData] = useState<InstitutionDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getInstitutionDetail(name, year)
      .then(setData)
      .finally(() => setLoading(false));
  }, [name, year]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-slate-900 border-l border-slate-700 overflow-y-auto flex flex-col">
        {/* Panel header */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-slate-700 sticky top-0 bg-slate-900 z-10">
          <div>
            <h2 className="text-sm font-bold text-white">{name}</h2>
            {data?.region && <p className="text-xs text-slate-400 mt-0.5">Region {data.region}</p>}
          </div>
          <button type="button" aria-label="Lukk" onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full" />
          </div>
        )}

        {data && !loading && (
          <div className="p-5 space-y-6">
            {/* Total */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Totale lokalkostnader {year || 'alle år'}</p>
              <p className="text-2xl font-bold text-white font-mono">{fmt(data.grand_total)} NOK</p>
              {data.property_id && (
                <Link href={`/properties/${data.property_id}`} className="text-xs text-blue-400 hover:underline mt-1 inline-block">
                  Åpne eiendomsprofil →
                </Link>
              )}
            </div>

            {/* Cost by category */}
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">Kostnad per kategori</h3>
              <div className="space-y-1.5">
                {data.cost_by_category.map(cat => (
                  <div key={cat.account_code}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-slate-300 truncate mr-2">{cat.label}</span>
                      <span className="text-slate-200 font-mono shrink-0">{fmt(cat.amount)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(cat.pct, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top suppliers */}
            {data.top_suppliers.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">Topp leverandører</h3>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-slate-700">
                      <th className="text-left pb-1.5">Leverandør</th>
                      <th className="text-right pb-1.5">Fakturaer</th>
                      <th className="text-right pb-1.5">Beløp</th>
                      <th className="text-right pb-1.5">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_suppliers.map((s, i) => (
                      <tr key={i} className="border-t border-slate-800 hover:bg-slate-800/40">
                        <td className="py-1.5 text-slate-200 truncate max-w-45">{s.name}</td>
                        <td className="py-1.5 text-right text-slate-400">{s.invoice_count}</td>
                        <td className="py-1.5 text-right font-mono text-slate-200">{fmt(s.amount)}</td>
                        <td className="py-1.5 text-right text-slate-400">{s.pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Monthly trend */}
            {data.monthly_trend.length > 1 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-3">Månedlig trend</h3>
                <MiniBarChart data={data.monthly_trend} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MiniBarChart({ data }: { data: { period: string; amount: number }[] }) {
  const max = Math.max(...data.map(d => Math.abs(d.amount)));
  return (
    <div className="flex items-end gap-0.5 h-24">
      {data.map(d => {
        const pct = max > 0 ? (Math.abs(d.amount) / max) * 100 : 0;
        const isNeg = d.amount < 0;
        const label = d.period.length === 6
          ? `${d.period.slice(4)}.${d.period.slice(0, 4)}`
          : d.period;
        return (
          <div key={d.period} className="flex flex-col items-center flex-1 gap-1" title={`${label}: ${fmt(d.amount)}`}>
            <div className="w-full flex items-end justify-center h-20">
              <div
                className={`w-full rounded-t ${isNeg ? 'bg-red-500/70' : 'bg-blue-500/70'}`}
                style={{ height: `${pct}%`, minHeight: '2px' }}
              />
            </div>
            {data.length <= 12 && (
              <span className="text-slate-500 text-[9px] writing-mode-vertical rotate-0 leading-tight">
                {label.slice(0, 2)}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Property profiles tab ───────────────────────────────────────────────────

type SortKey = 'total_cost' | 'cost_per_sqm' | 'husleie_gl' | 'strom' | 'vedlikehold' | 'rent_delta';

function ProfileSortTh({
  k,
  label,
  sortKey,
  sortAsc,
  setSortKey,
  setSortAsc,
}: {
  k: SortKey;
  label: string;
  sortKey: SortKey;
  sortAsc: boolean;
  setSortKey: (k: SortKey) => void;
  setSortAsc: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const active = sortKey === k;
  return (
    <th
      className={`text-right px-2 py-1.5 font-medium cursor-pointer select-none hover:text-slate-200 ${active ? 'text-blue-400' : 'text-slate-400'}`}
      onClick={() => {
        if (active) setSortAsc(a => !a);
        else {
          setSortKey(k);
          setSortAsc(false);
        }
      }}
    >
      {label}{active ? (sortAsc ? ' ↑' : ' ↓') : ''}
    </th>
  );
}

function ProfilesTab({ year }: { year?: number }) {
  const [data, setData] = useState<PropertyProfiles | null>(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>('total_cost');
  const [sortAsc, setSortAsc] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    getPropertyProfiles({ year }).then(setData).finally(() => setLoading(false));
  }, [year]);

  const sorted = data?.profiles
    .filter(p => !search || p.name.toLowerCase().includes(search.toLowerCase()))
    .slice()
    .sort((a, b) => {
      const av = (a[sortKey] as number | null) ?? -Infinity;
      const bv = (b[sortKey] as number | null) ?? -Infinity;
      return sortAsc ? av - bv : bv - av;
    }) ?? [];

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
    </div>
  );

  if (!data || data.profiles.length === 0) return (
    <div className="text-center py-20 text-slate-500">
      <p>Ingen eiendomsprofiler tilgjengelig.</p>
      <p className="text-sm mt-1">Krev at GL-transaksjoner er matchet til eiendom og at eiendommen har registrert areal.</p>
    </div>
  );

  const withArea = sorted.filter(p => p.cost_per_sqm != null);
  const maxCostSqm = Math.max(...withArea.map(p => p.cost_per_sqm ?? 0));

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Søk eiendom…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-slate-800 border border-slate-600 text-white text-sm rounded px-3 py-1.5 w-64 focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <span className="text-slate-500 text-xs">{sorted.length} eiendommer matchet</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-800 text-slate-400">
              <th className="text-left px-3 py-1.5 font-medium min-w-50">Eiendom</th>
              <th className="text-left px-2 py-1.5 font-medium">Region</th>
              <th className="text-right px-2 py-1.5 font-medium text-slate-400">Areal m²</th>
              <th className="text-right px-2 py-1.5 font-medium text-slate-400">Byggeår</th>
              <th className="text-right px-2 py-1.5 font-medium text-slate-400">Energi</th>
              <ProfileSortTh k="total_cost" label="Total" sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
              <ProfileSortTh k="husleie_gl" label="Husleie GL" sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
              <ProfileSortTh k="strom" label="Strøm" sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
              <ProfileSortTh k="vedlikehold" label="R&V" sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
              <ProfileSortTh k="cost_per_sqm" label="Kr/m²" sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
              <ProfileSortTh k="rent_delta" label="GL–Kontr." sortKey={sortKey} sortAsc={sortAsc} setSortKey={setSortKey} setSortAsc={setSortAsc} />
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => {
              const sqmPct = p.cost_per_sqm && maxCostSqm ? (p.cost_per_sqm / maxCostSqm) * 100 : 0;
              const highCost = sqmPct > 75;
              return (
                <tr
                  key={p.property_id}
                  className={`border-t border-slate-700/50 ${i % 2 === 0 ? 'bg-slate-800/20' : ''} hover:bg-slate-700/30`}
                >
                  <td className="px-3 py-1.5">
                    <Link href={`/properties/${p.property_id}`} className="text-blue-400 hover:underline truncate block max-w-50">
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-2 py-1.5 text-slate-400">{p.region}</td>
                  <td className="text-right px-2 py-1.5 font-mono text-slate-300">
                    {p.total_area ? p.total_area.toLocaleString('no-NO') : '–'}
                  </td>
                  <td className="text-right px-2 py-1.5 text-slate-400">{p.construction_year ?? '–'}</td>
                  <td className="text-right px-2 py-1.5 text-slate-400">{p.energy_label ?? '–'}</td>
                  <td className="text-right px-2 py-1.5 font-mono text-white font-semibold">{fmt(p.total_cost)}</td>
                  <td className="text-right px-2 py-1.5 font-mono text-slate-300">{fmt(p.husleie_gl)}</td>
                  <td className="text-right px-2 py-1.5 font-mono text-slate-300">{fmt(p.strom)}</td>
                  <td className="text-right px-2 py-1.5 font-mono text-slate-300">{fmt(p.vedlikehold)}</td>
                  <td className={`text-right px-2 py-1.5 font-mono font-semibold ${highCost ? 'text-red-400' : 'text-slate-200'}`}>
                    {p.cost_per_sqm != null ? fmt(p.cost_per_sqm) : '–'}
                  </td>
                  <td className={`text-right px-2 py-1.5 font-mono ${p.rent_delta != null ? (p.rent_delta > 0 ? 'text-amber-400' : 'text-green-400') : 'text-slate-500'}`}>
                    {p.rent_delta != null ? fmt(Math.abs(p.rent_delta)) : '–'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-600 mt-3">
        Kr/m² markert <span className="text-red-400">rødt</span> = blant de 25% dyreste.
        GL–Kontr. = <span className="text-amber-400">oransje</span> (GL {'>'} kontraktspris) / <span className="text-green-400">grønt</span> (GL {'<'} kontraktspris).
      </p>
    </div>
  );
}

// ─── Column-pivot components ─────────────────────────────────────────────────

function CategoryTable({ cat, regions, expanded, onInstitutionClick }: {
  cat: ProcurementCategory;
  regions: string[];
  expanded: boolean;
  onInstitutionClick: (name: string) => void;
}) {
  const [open, setOpen] = useState(expanded);
  useEffect(() => setOpen(expanded), [expanded]);

  return (
    <div className="mb-1">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm font-medium rounded transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-slate-400 text-xs">{open ? '▼' : '▶'}</span>
          {cat.label}
        </span>
        <span className="text-slate-300 font-mono text-xs">{fmt(cat.grand_total)} NOK</span>
      </button>

      {open && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-800 text-slate-400">
                <th className="text-left px-3 py-1.5 font-medium min-w-55">Institusjon</th>
                {regions.map(r => (
                  <th key={r} className="text-right px-2 py-1.5 font-medium min-w-22.5">{r}</th>
                ))}
                <th className="text-right px-3 py-1.5 font-medium min-w-25">Totalsum</th>
              </tr>
            </thead>
            <tbody>
              {cat.rows.map((row, i) => (
                <tr
                  key={i}
                  className={`border-t border-slate-700/50 ${i % 2 === 0 ? 'bg-slate-800/30' : 'bg-slate-800/10'} hover:bg-slate-700/30 cursor-pointer`}
                  onClick={() => onInstitutionClick(row.institution)}
                >
                  <td className="px-3 py-1.5 text-slate-200">
                    <span className="hover:text-blue-400 transition-colors">{row.institution}</span>
                  </td>
                  {regions.map(r => (
                    <td key={r} className="text-right px-2 py-1.5 font-mono text-slate-300">
                      {row.by_region[r] ? fmt(row.by_region[r]) : ''}
                    </td>
                  ))}
                  <td className="text-right px-3 py-1.5 font-mono text-white font-semibold">{fmt(row.total)}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-slate-500 bg-slate-700/60 font-semibold">
                <td className="px-3 py-1.5 text-slate-200">Sum {cat.label}</td>
                {regions.map(r => (
                  <td key={r} className="text-right px-2 py-1.5 font-mono text-slate-100">
                    {cat.totals_by_region[r] ? fmt(cat.totals_by_region[r]) : ''}
                  </td>
                ))}
                <td className="text-right px-3 py-1.5 font-mono text-white">{fmt(cat.grand_total)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function GroupSection({ group, regions, allExpanded, onInstitutionClick }: {
  group: ProcurementGroup | DynamicPivotGroup;
  regions: string[];
  allExpanded: boolean;
  onInstitutionClick: (name: string) => void;
}) {
  const [open, setOpen] = useState(true);
  const groupTotal = group.categories.reduce((s, c) => s + c.grand_total, 0);

  return (
    <div className="mb-4 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-800 text-white font-bold text-sm transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-blue-400">{open ? '▼' : '▶'}</span>
          {group.group}
        </span>
        <span className="font-mono text-blue-300 text-sm">{fmt(groupTotal)} NOK</span>
      </button>
      {open && (
        <div className="p-2 space-y-1">
          {group.categories.map(cat => (
            <CategoryTable
              key={cat.key}
              cat={cat}
              regions={regions}
              expanded={allExpanded}
              onInstitutionClick={onInstitutionClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Per-region components ────────────────────────────────────────────────────

function PerRegionAccountSection({ acct, expanded, onInstitutionClick }: {
  acct: PerRegionAccount;
  expanded: boolean;
  onInstitutionClick: (name: string) => void;
}) {
  const [open, setOpen] = useState(expanded);
  useEffect(() => setOpen(expanded), [expanded]);

  return (
    <div className="mb-1">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 text-sm font-medium rounded transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-slate-400 text-xs">{open ? '▼' : '▶'}</span>
          {acct.label}
        </span>
        <span className="text-slate-300 font-mono text-xs">{fmt(acct.grand_total)} NOK</span>
      </button>

      {open && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-800 text-slate-400">
                <th className="text-left px-3 py-1.5 font-medium min-w-65">Region / Institusjon</th>
                <th className="text-right px-3 py-1.5 font-medium min-w-30">Beløp</th>
              </tr>
            </thead>
            <tbody>
              {acct.regions.map(sec => (
                <React.Fragment key={sec.region}>
                  <tr className="bg-slate-700/40 border-t border-slate-600">
                    <td className="px-3 py-1.5 font-semibold text-slate-200">{sec.region}</td>
                    <td className="text-right px-3 py-1.5 font-mono font-semibold text-slate-100">{fmt(sec.region_total)}</td>
                  </tr>
                  {sec.rows.map((row, i) => (
                    <tr
                      key={i}
                      className={`border-t border-slate-700/30 ${i % 2 === 0 ? 'bg-slate-800/20' : ''} hover:bg-slate-700/20 cursor-pointer`}
                      onClick={() => onInstitutionClick(row.institution)}
                    >
                      <td className="pl-8 pr-3 py-1 text-slate-300 hover:text-blue-400 transition-colors">{row.institution}</td>
                      <td className="text-right px-3 py-1 font-mono text-slate-300">{fmt(row.total)}</td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
              <tr className="border-t-2 border-slate-500 bg-slate-700/60 font-semibold">
                <td className="px-3 py-1.5 text-slate-200">Totalsum</td>
                <td className="text-right px-3 py-1.5 font-mono text-white">{fmt(acct.grand_total)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function PerRegionGroupSection({ group, allExpanded, onInstitutionClick }: {
  group: PerRegionGroup;
  allExpanded: boolean;
  onInstitutionClick: (name: string) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div className="mb-4 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-800 text-white font-bold text-sm transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-blue-400">{open ? '▼' : '▶'}</span>
          {group.group}
        </span>
        <span className="font-mono text-blue-300 text-sm">{fmt(group.grand_total)} NOK</span>
      </button>
      {open && (
        <div className="p-2 space-y-1">
          {group.accounts.map(acct => (
            <PerRegionAccountSection
              key={acct.key}
              acct={acct}
              expanded={allExpanded}
              onInstitutionClick={onInstitutionClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── CSV export ──────────────────────────────────────────────────────────────

function exportToCsv(data: ProcurementPivot | DynamicPivot) {
  const regions = data.regions;
  const rows: string[][] = [['Gruppe', 'Kategori', 'Institusjon', ...regions, 'Totalsum']];
  for (const group of data.groups) {
    for (const cat of group.categories) {
      for (const row of cat.rows) {
        rows.push([group.group, cat.label, row.institution, ...regions.map(r => String(row.by_region[r] || 0)), String(row.total)]);
      }
      rows.push([group.group, `Sum: ${cat.label}`, '', ...regions.map(r => String(cat.totals_by_region[r] || 0)), String(cat.grand_total)]);
    }
  }
  downloadCsv(rows, `innkjøpsanalyse_${data.year || 'alle_år'}.csv`);
}

function exportPerRegionToCsv(data: PerRegionPivot) {
  const rows: string[][] = [['Kategori', 'Konto', 'Region', 'Institusjon', 'Beløp']];
  for (const group of data.groups) {
    for (const acct of group.accounts) {
      for (const sec of acct.regions) {
        for (const row of sec.rows) {
          rows.push([group.group, acct.label, sec.region, row.institution, String(row.total)]);
        }
        rows.push([group.group, acct.label, `Sum ${sec.region}`, '', String(sec.region_total)]);
      }
    }
  }
  downloadCsv(rows, `innkjøpsanalyse_per_enhet_${data.year || 'alle_år'}.csv`);
}

function downloadCsv(rows: string[][], filename: string) {
  const csv = rows.map(r => r.map(c => `"${c}"`).join(';')).join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function ProcurementPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('predefined');
  const [year, setYear] = useState<number | undefined>(2025);
  const [region, setRegion] = useState<string>('');
  const [data, setData] = useState<ProcurementPivot | DynamicPivot | PerRegionPivot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allExpanded, setAllExpanded] = useState(false);
  const [selectedInstitution, setSelectedInstitution] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (viewMode === 'profiles') { setData(null); return; }
    setLoading(true);
    setError(null);
    try {
      const params = { year, region: region || undefined };
      let result;
      if (viewMode === 'per-region') result = await getPerRegionPivot({ year });
      else if (viewMode === 'dynamic') result = await getDynamicPivot(params);
      else result = await getProcurementPivot(params);
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [year, region, viewMode]);

  useEffect(() => { load(); }, [load]);

  const grandTotal = (() => {
    if (!data) return 0;
    if (viewMode === 'per-region') return (data as PerRegionPivot).groups.reduce((s: number, g) => s + g.grand_total, 0);
    const groups = (data as ProcurementPivot | DynamicPivot).groups as Array<{ categories: Array<{ grand_total: number }> }>;
    return groups.reduce((s, g) => s + g.categories.reduce((ss, c) => ss + c.grand_total, 0), 0);
  })();

  const totalCategories = (() => {
    if (!data) return 0;
    if (viewMode === 'per-region') return (data as PerRegionPivot).groups.reduce((s: number, g) => s + g.accounts.length, 0);
    const groups = (data as ProcurementPivot | DynamicPivot).groups as Array<{ categories: unknown[] }>;
    return groups.reduce((s, g) => s + g.categories.length, 0);
  })();

  const tabs: { id: ViewMode; label: string }[] = [
    { id: 'predefined', label: 'Kostnadsanalyse' },
    { id: 'dynamic', label: 'GL-kategorier' },
    { id: 'per-region', label: 'Per enhet' },
    { id: 'profiles', label: 'Eiendomsprofiler' },
  ];

  const showRegionFilter = viewMode !== 'per-region' && viewMode !== 'profiles';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-[1600px] mx-auto">

        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link href="/admin" className="p-2 bg-slate-800 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Innkjøpsanalyse – Lokalkostnader</h1>
            <p className="text-slate-400 text-sm">Kostnader per institusjon og region, basert på GL-transaksjoner</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-4 bg-slate-900 p-1 rounded-lg border border-slate-700 w-fit">
          {tabs.map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setViewMode(tab.id)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                viewMode === tab.id ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {viewMode === 'profiles' ? (
          /* ── Profiles tab – has its own layout ── */
          <div>
            <div className="mb-4 flex items-center gap-3">
              <div>
                <label htmlFor="filter-year-p" className="block text-xs text-slate-400 mb-1">År</label>
                <select
                  id="filter-year-p"
                  value={year ?? ''}
                  onChange={e => setYear(e.target.value ? Number(e.target.value) : undefined)}
                  className="bg-slate-800 border border-slate-600 text-white text-sm rounded px-3 py-1.5 focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">Alle år</option>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
            </div>
            <div className="mb-3 px-3 py-2 bg-slate-800/60 border border-slate-700 rounded text-xs text-slate-400">
              <strong className="text-slate-300">Eiendomsprofiler:</strong>{' '}
              Kostnad per m² og sammenligning av husleie (GL konto 6300) mot kontraktspris.
              Bare eiendommer der GL-transaksjoner er matchet til property_id vises.
              Klikk kolonneoverskrift for sortering.
            </div>
            <ProfilesTab year={year} />
          </div>
        ) : (
          /* ── Pivot views ── */
          <>
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 mb-6 bg-slate-900 p-4 rounded-lg border border-slate-700">
              <div>
                <label htmlFor="filter-year" className="block text-xs text-slate-400 mb-1">År</label>
                <select
                  id="filter-year"
                  value={year ?? ''}
                  onChange={e => setYear(e.target.value ? Number(e.target.value) : undefined)}
                  className="bg-slate-800 border border-slate-600 text-white text-sm rounded px-3 py-1.5 focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="">Alle år</option>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              {showRegionFilter && (
                <div>
                  <label htmlFor="filter-region" className="block text-xs text-slate-400 mb-1">Region</label>
                  <select
                    id="filter-region"
                    value={region}
                    onChange={e => setRegion(e.target.value)}
                    className="bg-slate-800 border border-slate-600 text-white text-sm rounded px-3 py-1.5 focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">Alle regioner</option>
                    {REGIONS.filter(r => r !== 'Øvrig').map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              )}
              <div className="ml-auto flex items-end gap-2">
                <button
                  type="button"
                  onClick={() => setAllExpanded(e => !e)}
                  className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-sm rounded text-slate-200 transition-colors"
                >
                  {allExpanded ? 'Kollaps alle' : 'Ekspander alle'}
                </button>
                {data && viewMode !== 'per-region' && (
                  <button
                    type="button"
                    onClick={() => exportToCsv(data as ProcurementPivot | DynamicPivot)}
                    className="px-3 py-1.5 bg-blue-700 hover:bg-blue-600 text-sm rounded text-white transition-colors flex items-center gap-1"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Eksporter CSV
                  </button>
                )}
                {data && viewMode === 'per-region' && (
                  <button
                    type="button"
                    onClick={() => exportPerRegionToCsv(data as PerRegionPivot)}
                    className="px-3 py-1.5 bg-blue-700 hover:bg-blue-600 text-sm rounded text-white transition-colors flex items-center gap-1"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Eksporter CSV
                  </button>
                )}
              </div>
            </div>

            {/* Summary */}
            {data && !loading && (
              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <p className="text-slate-400 text-xs mb-1">Totalsum</p>
                  <p className="text-2xl font-bold text-white font-mono">{fmt(grandTotal)} NOK</p>
                </div>
                <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <p className="text-slate-400 text-xs mb-1">Kostnadskategorier</p>
                  <p className="text-2xl font-bold text-white">{totalCategories}</p>
                </div>
                <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                  <p className="text-slate-400 text-xs mb-1">Transaksjoner</p>
                  <p className="text-2xl font-bold text-white">{(data?.total_transactions ?? 0).toLocaleString('no-NO')}</p>
                </div>
              </div>
            )}

            {loading && (
              <div className="flex items-center justify-center py-20">
                <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
                <span className="ml-3 text-slate-400">Laster innkjøpsdata…</span>
              </div>
            )}
            {error && (
              <div className="bg-red-900/40 border border-red-700 text-red-300 p-4 rounded-lg mb-6">
                <strong>Feil:</strong> {error}
              </div>
            )}

            {/* Pivot tables */}
            {!loading && data && viewMode !== 'per-region' && (() => {
              const d = data as ProcurementPivot | DynamicPivot;
              return d.groups.length > 0 ? (
                <div className="space-y-2">
                  {d.groups.map(group => (
                    <GroupSection
                      key={group.group}
                      group={group}
                      regions={d.regions}
                      allExpanded={allExpanded}
                      onInstitutionClick={setSelectedInstitution}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-20 text-slate-500">
                  <p className="text-lg mb-2">Ingen transaksjoner funnet</p>
                  <p className="text-sm">Importer regnskapsdata via <Link href="/admin/import" className="text-blue-400 hover:underline">Data Import</Link> først.</p>
                </div>
              );
            })()}

            {!loading && data && viewMode === 'per-region' && (() => {
              const d = data as PerRegionPivot;
              return d.groups.length > 0 ? (
                <div className="space-y-2">
                  {d.groups.map(group => (
                    <PerRegionGroupSection
                      key={group.group}
                      group={group}
                      allExpanded={allExpanded}
                      onInstitutionClick={setSelectedInstitution}
                    />
                  ))}
                </div>
              ) : null;
            })()}
          </>
        )}
      </div>

      {/* Institution detail sidepanel */}
      {selectedInstitution && (
        <InstitutionPanel
          name={selectedInstitution}
          year={year}
          onClose={() => setSelectedInstitution(null)}
        />
      )}
    </div>
  );
}
