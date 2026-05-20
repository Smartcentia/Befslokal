/**
 * Normaliserer navn for matching mot godkjent liste.
 * Fjerner ekstra mellomrom, lowercase, fjerner "avdeling X" suffix.
 */
function normalizeForMatch(name: string): string {
    if (!name || typeof name !== "string") return "";
    return name
        .replace(/\s+/g, " ")
        .replace(/,?\s*avdeling\s+[^,]+/gi, "")
        .replace(/\s*-\s*$/, "")
        .trim()
        .toLowerCase();
}

/**
 * Sjekker om propertyName matcher noe i godkjent liste.
 * Bruker prefix/contains: "Bergen Akuttsenter Ungdom, avdeling Toppe" matcher "Bergen Akuttsenter Ungdom".
 */
export function isInApprovedList(
    propertyName: string | null | undefined,
    approvedList: string[]
): boolean {
    if (!propertyName || approvedList.length === 0) return false;
    const normalized = normalizeForMatch(propertyName);
    if (!normalized) return false;
    return approvedList.some((approved) => {
        const normApproved = normalizeForMatch(approved);
        if (!normApproved) return false;
        return normalized.includes(normApproved) || normApproved.includes(normalized);
    });
}

/**
 * Sjekker om eiendom har kostnader i 2025 (Total kost fra Innkjøpsanalyse).
 */
export function hasCosts2025(
    propertyId: string | null | undefined,
    byProperty: Record<string, { aggregert?: number }> | null | undefined
): boolean {
    if (!propertyId || !byProperty) return false;
    const data = byProperty[propertyId];
    return (data?.aggregert ?? 0) > 0;
}

/**
 * Sjekker om eiendom skal vise UTGÅTT-badge.
 * UTGÅTT = ikke i godkjent liste OG ingen kostnader 2025.
 */
export function isUtgatt(
    propertyName: string | null | undefined,
    propertyId: string | null | undefined,
    approvedList: string[],
    byProperty: Record<string, { aggregert?: number }> | null | undefined
): boolean {
    if (isInApprovedList(propertyName, approvedList)) return false;
    if (hasCosts2025(propertyId, byProperty)) return false;
    return true;
}
