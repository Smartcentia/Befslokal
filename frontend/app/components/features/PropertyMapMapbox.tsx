'use client';

import React, { useMemo, useState } from 'react';
import Map from 'react-map-gl';
import { Marker, Popup } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { getPropertyPinStyle } from '@/lib/mapPropertyTypes';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || '';

const SERVICE_COLORS: Record<string, string> = {
    hospital: '#dc2626',
    pharmacy: '#ea580c',
    doctor: '#f97316',
    police: '#1e40af',
    fire_station: '#b91c1c',
    school: '#ca8a04',
    kindergarten: '#eab308',
    supermarket: '#16a34a',
    transit_station: '#2563eb',
    bus_station: '#3b82f6',
    train_station: '#6366f1',
    park: '#22c55e',
    gym: '#84cc16',
    library: '#8b5cf6',
    bup: '#ec4899',
    default: '#6b7280',
};

interface PropertyMapMapboxProps {
    latitude: number;
    longitude: number;
    propertyName: string;
    propertyUsage?: string;
    services?: Array<{ latitude?: number; longitude?: number; service_type?: string; service_name?: string; distance_meters?: number }>;
}

const PropertyMapMapbox: React.FC<PropertyMapMapboxProps> = ({
    latitude,
    longitude,
    propertyName,
    propertyUsage,
    services = [],
}) => {
    const lat = latitude || 59.9139;
    const lng = longitude || 10.7522;
    const [showPopup, setShowPopup] = useState(true);
    const [servicePopup, setServicePopup] = useState<typeof services[0] | null>(null);

    const validServices = useMemo(
        () => services.filter((s) => s.latitude != null && s.longitude != null),
        [services]
    );

    const { color: propertyColor, icon: PropertyIcon } = getPropertyPinStyle({ usage: propertyUsage });

    if (!MAPBOX_TOKEN) {
        return (
            <div className="h-full w-full flex items-center justify-center bg-muted/20 text-muted-foreground text-sm">
                Sett NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN for Mapbox-kart
            </div>
        );
    }

    return (
        <div className="h-full w-full min-h-70">
            <Map
                mapboxAccessToken={MAPBOX_TOKEN}
                initialViewState={{ longitude: lng, latitude: lat, zoom: 15 }}
                mapStyle="mapbox://styles/mapbox/streets-v12"
            >
                {/* Eiendom (hovedmarkør) */}
                <Marker
                    longitude={lng}
                    latitude={lat}
                    anchor="bottom"
                    onClick={(e) => {
                        e.originalEvent?.stopPropagation?.();
                        setShowPopup((v) => !v);
                    }}
                >
                    <div
                        className="cursor-pointer hover:scale-110 transition-transform w-10 h-10 flex items-center justify-center rounded-full shadow-lg border-2 border-white"
                        style={{ backgroundColor: propertyColor, color: '#fff' }}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(ev) => {
                            if (ev.key === 'Enter' || ev.key === ' ') {
                                ev.preventDefault();
                                setShowPopup((v) => !v);
                            }
                        }}
                        aria-label={`Vis info om ${propertyName}`}
                        title={`Vis info om ${propertyName}`}
                    >
                        <PropertyIcon size={20} />
                    </div>
                </Marker>
                {showPopup && (
                    <Popup
                        longitude={lng}
                        latitude={lat}
                        anchor="top"
                        onClose={() => setShowPopup(false)}
                        closeButton={false}
                    >
                        <div className="text-sm font-medium text-gray-900">{propertyName}</div>
                        <div className="text-xs text-slate-500">
                            {lat.toFixed(4)}, {lng.toFixed(4)}
                        </div>
                    </Popup>
                )}

                {/* Nærliggende tjenester */}
                {validServices.map((svc, i) => {
                    const color = SERVICE_COLORS[svc.service_type || ''] || SERVICE_COLORS.default;
                    return (
                        <Marker
                            key={`${svc.latitude}-${svc.longitude}-${i}`}
                            longitude={svc.longitude!}
                            latitude={svc.latitude!}
                            anchor="bottom"
                            onClick={(e) => {
                                e.originalEvent?.stopPropagation?.();
                                setServicePopup((p) => (p === svc ? null : svc));
                            }}
                        >
                            <div
                                className={`cursor-pointer hover:scale-125 transition-transform w-5 h-5 rounded-full border-2 border-white shadow-md bg-[${color}]`}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(ev) => {
                                    if (ev.key === 'Enter' || ev.key === ' ') {
                                        ev.preventDefault();
                                        setServicePopup((p) => (p === svc ? null : svc));
                                    }
                                }}
                                aria-label={`Vis info om ${svc.service_name || svc.service_type}`}
                                title={`Vis info om ${svc.service_name || svc.service_type}`}
                            />
                        </Marker>
                    );
                })}
                {servicePopup && (
                    <Popup
                        longitude={servicePopup.longitude!}
                        latitude={servicePopup.latitude!}
                        anchor="top"
                        onClose={() => setServicePopup(null)}
                        closeButton
                    >
                        <div className="text-sm font-medium text-gray-900">
                            {servicePopup.service_name || servicePopup.service_type}
                        </div>
                        {servicePopup.distance_meters != null && (
                            <div className="text-xs text-slate-500">
                                {Math.round(servicePopup.distance_meters)} m unna
                            </div>
                        )}
                    </Popup>
                )}
            </Map>
        </div>
    );
};

export default PropertyMapMapbox;
