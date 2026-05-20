import type { Property } from '@/lib/types';
import type { LucideIcon } from 'lucide-react';
import { ShieldCheck, Users, Building2, Heart, LayoutGrid, Store, MapPin, Home } from 'lucide-react';

export type PropertyPinCategory =
    | 'Barnevern'
    | 'Familievern'
    | 'Kontor'
    | 'Omsorgssenter'
    | 'Avdeling'
    | 'Næringseiendom'
    | 'Beredskapslokasjon'
    | 'Annet';

export interface PinCategoryStyle {
    color: string;
    label: string;
    icon: LucideIcon;
}

const raw = (s: string | undefined): string => (s ?? '').toLowerCase();

function matches(combined: string, ...keywords: string[]): boolean {
    return keywords.some((k) => combined.includes(k.toLowerCase()));
}

/**
 * Derives a single display category from property.usage, unit_type_derived, unit_short_type.
 * Order: unit_type_derived, unit_short_type, usage; first match wins.
 */
export function getPropertyPinCategory(prop: Pick<Property, 'usage' | 'unit_type_derived' | 'unit_short_type'>): PropertyPinCategory {
    const a = raw(prop.unit_type_derived);
    const b = raw(prop.unit_short_type);
    const c = raw(prop.usage);
    const combined = `${a} ${b} ${c}`;

    if (matches(combined, 'barnevern', 'barnevernsinstitusjon')) return 'Barnevern';
    if (matches(combined, 'familievern')) return 'Familievern';
    if (matches(combined, 'kontor')) return 'Kontor';
    if (matches(combined, 'omsorg', 'omsorgssenter')) return 'Omsorgssenter';
    if (matches(combined, 'avdeling', 'institusjonsavdeling')) return 'Avdeling';
    if (matches(combined, 'næring', 'naering')) return 'Næringseiendom';
    if (matches(combined, 'beredskap')) return 'Beredskapslokasjon';

    return 'Annet';
}

export const PIN_CATEGORY_STYLES: Record<PropertyPinCategory, PinCategoryStyle> = {
    Barnevern: { color: '#2563eb', label: 'Barnevern', icon: ShieldCheck },
    Familievern: { color: '#16a34a', label: 'Familievern', icon: Users },
    Kontor: { color: '#6b7280', label: 'Kontor', icon: Building2 },
    Omsorgssenter: { color: '#7c3aed', label: 'Omsorgssenter', icon: Heart },
    Avdeling: { color: '#ea580c', label: 'Avdeling', icon: LayoutGrid },
    Næringseiendom: { color: '#92400e', label: 'Næringseiendom', icon: Store },
    Beredskapslokasjon: { color: '#6366f1', label: 'Beredskapslokasjon', icon: MapPin },
    Annet: { color: '#3b82f6', label: 'Eiendom', icon: Home },
};

/** Henter farge og ikon for en eiendom – brukes på kart. */
export function getPropertyPinStyle(prop: Pick<Property, 'usage' | 'unit_type_derived' | 'unit_short_type'>) {
    const category = getPropertyPinCategory(prop);
    return PIN_CATEGORY_STYLES[category];
}
