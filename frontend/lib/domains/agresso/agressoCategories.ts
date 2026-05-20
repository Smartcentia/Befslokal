export type AccountingCategory = {
  /** Stabil nøkkel for filter/summering */
  groupKey: string;
  /** Lesbar gruppe */
  groupLabel: string;
  /** Typisk kontonavn fra raden */
  detailLabel: string;
};

type AgressoRow = Record<string, string>;

type MapFn = (row: AgressoRow, ...candidates: string[]) => string;

/**
 * Grupperer lokalkostnader etter hovedbokskonto (Bufetat / Agresso 01).
 * Ukjente konti havner i «Øvrige» med kontonavn som detalj.
 */
const KONTO_GROUP: Record<
  string,
  { groupKey: string; groupLabel: string }
> = {
  "6300": { groupKey: "leie", groupLabel: "Husleie og areal" },
  "6310": { groupKey: "leie", groupLabel: "Husleie og areal" },
  "6391": { groupKey: "leie", groupLabel: "Husleie og areal" },
  "6395": { groupKey: "felles", groupLabel: "Fellesutgifter" },
  "6396": { groupKey: "felles", groupLabel: "Fellesutgifter" },
  "6398": { groupKey: "felles", groupLabel: "Fellesutgifter" },
  "6320": { groupKey: "forsyning", groupLabel: "Forsyning og energi" },
  "6340": { groupKey: "forsyning", groupLabel: "Forsyning og energi" },
  "6360": { groupKey: "drift", groupLabel: "Renhold" },
  "6364": { groupKey: "drift", groupLabel: "Vakthold / alarm" },
  "6365": { groupKey: "drift", groupLabel: "Vaktmestertjenester" },
  "6390": { groupKey: "drift", groupLabel: "Annen kostnad lokaler" },
  "6630": { groupKey: "vedlikehold", groupLabel: "Vedlikehold leide lokaler" },
  "6662": { groupKey: "vedlikehold", groupLabel: "Reparasjon / service anlegg" },
  "4960": { groupKey: "investering", groupLabel: "Fast bygningsinventar" },
  "1268": { groupKey: "investering", groupLabel: "Påkostning leide bygg" },
};

const GROUP_ORDER: string[] = [
  "leie",
  "felles",
  "forsyning",
  "drift",
  "vedlikehold",
  "investering",
  "ovrige",
];

export function orderedGroupKeys(): string[] {
  return [...GROUP_ORDER];
}

export function categorizeRow(row: AgressoRow, get: MapFn): AccountingCategory {
  const konto = get(row, "Konto", "konto").trim();
  const kontoT = get(row, "Konto(T)", "konto(t)").trim();
  const meta = konto ? KONTO_GROUP[konto] : undefined;
  if (meta) {
    return {
      groupKey: meta.groupKey,
      groupLabel: meta.groupLabel,
      detailLabel: kontoT || `${konto}`,
    };
  }
  return {
    groupKey: "ovrige",
    groupLabel: "Øvrige kostnader",
    detailLabel: konto ? `${konto}${kontoT ? ` — ${kontoT}` : ""}` : kontoT || "—",
  };
}

export type GroupSummary = {
  groupKey: string;
  groupLabel: string;
  rowCount: number;
  sumAmount: number;
};

export function summarizeByGroup(
  categories: AccountingCategory[],
  amounts: number[],
): GroupSummary[] {
  const map = new Map<
    string,
    { groupLabel: string; rowCount: number; sumAmount: number }
  >();
  for (let i = 0; i < categories.length; i++) {
    const c = categories[i]!;
    const a = amounts[i] ?? 0;
    const cur = map.get(c.groupKey) ?? {
      groupLabel: c.groupLabel,
      rowCount: 0,
      sumAmount: 0,
    };
    cur.groupLabel = c.groupLabel;
    cur.rowCount += 1;
    cur.sumAmount += a;
    map.set(c.groupKey, cur);
  }
  const keys = orderedGroupKeys().filter((k) => map.has(k));
  const rest = [...map.keys()].filter((k) => !keys.includes(k));
  const ordered = [...keys, ...rest.sort()];
  return ordered.map((groupKey) => {
    const v = map.get(groupKey)!;
    return {
      groupKey,
      groupLabel: v.groupLabel,
      rowCount: v.rowCount,
      sumAmount: v.sumAmount,
    };
  });
}
