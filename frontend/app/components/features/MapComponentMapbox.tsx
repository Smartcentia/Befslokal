'use client';

import React, { useMemo, useState, useEffect } from 'react';
import Map from 'react-map-gl';
import { Marker, Popup } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Property } from '@/lib/types';
import { Building2 } from 'lucide-react';
import Link from 'next/link';
import { getBUPLocationsNearbyMap } from '@/lib/services/bupService';
import type { BUPLocationForMap } from '@/lib/types';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || '';
const BUP_COLOR = '#ec4899';

function getUsageMarkerStyle(usage?: string): { label: string; color: string } {
    const normalized = (usage || '').toLowerCase();
    if (normalized.includes('barnevernsinstitusjon') || normalized.includes('formålsbygg') || normalized.includes('formalsbygg')) {
        return { label: 'Formålsbygg', color: '#2563eb' };
    }
    if (normalized.includes('næring') || normalized.includes('naering')) {
        return { label: 'Næringseiendom', color: '#16a34a' };
    }
    if (normalized.includes('bolig')) {
        return { label: 'Bolig', color: '#f59e0b' };
    }
    if (normalized.includes('tomt')) {
        return { label: 'Tomt', color: '#7c3aed' };
    }
    return { label: usage || 'Annet', color: '#64748b' };
}

interface MapComponentMapboxProps {
    properties: Property[];
    onPropertySelect?: (property: Property) => void;
}

const MapComponentMapbox: React.FC<MapComponentMapboxProps> = ({ properties }) => {
    const [popupId, setPopupId] = useState<string | null>(null);
    const [bupPopupId, setBupPopupId] = useState<string | null>(null);
    const [bupLocations, setBupLocations] = useState<BUPLocationForMap[]>([]);

    const safeProps = useMemo(() => {
        if (!Array.isArray(properties)) return [];
        return properties
            .map(p => {
                // Sjekk både topp-nivå og external_data for koordinater
                const lat = p.latitude ?? p.external_data?.latitude ?? p.external_data?.lat;
                const lon = p.longitude ?? p.external_data?.longitude ?? p.external_data?.lon;

                return {
                    ...p,
                    latitude: typeof lat === 'string' ? parseFloat(lat) : lat,
                    longitude: typeof lon === 'string' ? parseFloat(lon) : lon
                };
            })
            .filter(
                (p): p is Property & { latitude: number; longitude: number } =>
                    typeof p.latitude === 'number' &&
                    typeof p.longitude === 'number' &&
                    !isNaN(p.latitude) &&
                    !isNaN(p.longitude) &&
                    p.latitude !== 0 &&
                    p.longitude !== 0
            );
    }, [properties]);

    const [viewState, setViewState] = useState(() => {
        const first = safeProps[0];
        if (first) {
            return {
                longitude: first.longitude,
                latitude: first.latitude,
                zoom: 10,
            };
        }
        return {
            longitude: 10.7522,
            latitude: 59.9139,
            zoom: 4,
        };
    });

    const propertyIds = useMemo(() => safeProps.map((p) => p.property_id), [safeProps]);

    useEffect(() => {
        if (propertyIds.length === 0) {
            return;
        }
        getBUPLocationsNearbyMap(propertyIds, 30)
            .then((res) => setBupLocations(res.locations ?? []))
            .catch(() => setBupLocations([]));
    }, [propertyIds]);

    const effectiveBupLocations = useMemo(() => {
        return propertyIds.length === 0 ? [] : bupLocations;
    }, [propertyIds.length, bupLocations]);

    const legendItems = useMemo(
        () => [
            { label: 'Formålsbygg', color: '#2563eb' },
            { label: 'Næringseiendom', color: '#16a34a' },
            { label: 'Bolig', color: '#f59e0b' },
            { label: 'Tomt', color: '#7c3aed' },
            { label: 'Annet', color: '#64748b' },
        ],
        []
    );

    if (!MAPBOX_TOKEN) {
        return (
            <div className="h-full w-full min-h-75 flex flex-col items-center justify-center bg-muted/20 text-muted-foreground rounded-lg p-6">
                <p className="text-sm font-medium mb-2">Kart krever Mapbox-token</p>
                <p className="text-xs text-center max-w-sm">
                    Sett <code className="bg-muted px-1 rounded">NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN</code> i Vercel Environment Variables og redeploy.
                </p>
            </div>
        );
    }

    return (
        <div className="h-full w-full relative z-0 rounded-lg overflow-hidden">
            <Map
                mapboxAccessToken={MAPBOX_TOKEN}
                {...viewState}
                onMove={(evt) => setViewState(evt.viewState)}
                style={{ width: '100%', height: '100%', borderRadius: '0.75rem' }}
                mapStyle="mapbox://styles/mapbox/streets-v12"
            >
                {safeProps.map((prop) => (
                    <React.Fragment key={prop.property_id}>
                        <Marker
                            longitude={prop.longitude}
                            latitude={prop.latitude}
                            anchor="bottom"
                            onClick={(e) => {
                                e.originalEvent?.stopPropagation?.();
                                setPopupId((id) => (id === prop.property_id ? null : prop.property_id));
                            }}
                        >
                            <div
                                className="cursor-pointer hover:scale-110 transition-transform p-1 rounded-full text-white shadow-lg border-2 border-white"
                                style={{ backgroundColor: getUsageMarkerStyle(prop.usage).color }}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(ev) => {
                                    if (ev.key === 'Enter' || ev.key === ' ') {
                                        ev.preventDefault();
                                        setPopupId((id) => (id === prop.property_id ? null : prop.property_id));
                                    }
                                }}
                                aria-label={`Vis info om ${prop.name}`}
                            >
                                <Building2 size={20} />
                            </div>
                        </Marker>
                        {popupId === prop.property_id && (
                            <Popup
                                longitude={prop.longitude}
                                latitude={prop.latitude}
                                anchor="top"
                                onClose={() => setPopupId(null)}
                                closeButton
                            >
                                <div className="p-1 min-w-50">
                                    <div className="flex items-start gap-2 mb-2">
                                        <div className="p-1.5 bg-primary/10 rounded text-primary mt-0.5">
                                            <Building2 size={14} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-sm text-gray-900">{prop.name}</h3>
                                            <p className="text-xs text-gray-600">{prop.address}</p>
                                        </div>
                                    </div>
                                    <div className="border-t border-gray-200 pt-2 mt-2 flex justify-between items-center">
                                        <span className="text-[10px] uppercase font-bold text-muted bg-surface/50 px-2 py-0.5 rounded border border-border">
                                            {getUsageMarkerStyle(prop.usage).label}
                                        </span>
                                        <Link href={`/properties/${prop.property_id}`} className="text-xs text-blue-600 font-bold hover:underline">
                                            Gå til eiendom →
                                        </Link>
                                    </div>
                                </div>
                            </Popup>
                        )}
                    </React.Fragment>
                ))}
                {effectiveBupLocations.map((bup) => (
                    <React.Fragment key={bup.id}>
                        <Marker
                            longitude={bup.longitude}
                            latitude={bup.latitude}
                            anchor="bottom"
                            onClick={(e) => {
                                e.originalEvent?.stopPropagation?.();
                                setBupPopupId((id) => (id === bup.id ? null : bup.id));
                            }}
                        >
                            <div
                                className="cursor-pointer hover:scale-125 transition-transform w-5 h-5 rounded-full border-2 border-white shadow-md bg-[#ec4899]"
                                role="button"
                                tabIndex={0}
                                onKeyDown={(ev) => {
                                    if (ev.key === 'Enter' || ev.key === ' ') {
                                        ev.preventDefault();
                                        setBupPopupId((id) => (id === bup.id ? null : bup.id));
                                    }
                                }}
                                aria-label={`Vis info om ${bup.navn}`}
                            />
                        </Marker>
                        {bupPopupId === bup.id && (
                            <Popup
                                longitude={bup.longitude}
                                latitude={bup.latitude}
                                anchor="top"
                                onClose={() => setBupPopupId(null)}
                                closeButton
                            >
                                <div className="p-1 min-w-45">
                                    <div className="flex items-start gap-2">
                                        <div
                                            className="w-6 h-6 rounded-full mt-0.5 shrink-0 bg-[#ec4899]"
                                        />
                                        <div>
                                            <h3 className="font-bold text-sm text-gray-900">{bup.navn}</h3>
                                            {bup.adresse && (
                                                <p className="text-xs text-gray-600">{bup.adresse}</p>
                                            )}
                                            <p className="text-xs text-gray-500 mt-1">
                                                {bup.nearest_property_distance_km} km til nærmeste eiendom
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        )}
                    </React.Fragment>
                ))}
            </Map>
            <div className="absolute left-3 bottom-3 z-10 rounded-lg border border-border bg-background/95 px-3 py-2 shadow-md">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-muted mb-1">Eiendomstype</div>
                <div className="grid grid-cols-1 gap-1">
                    {legendItems.map((item) => (
                        <div key={item.label} className="flex items-center gap-2 text-xs text-foreground">
                            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                            <span>{item.label}</span>
                        </div>
                    ))}
                    <div className="flex items-center gap-2 text-xs text-foreground">
                        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: BUP_COLOR }} />
                        <span>BUP</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MapComponentMapbox;
