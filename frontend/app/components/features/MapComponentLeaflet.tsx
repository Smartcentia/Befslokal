'use client';

import React, { useEffect } from 'react';
import { Property } from '@/lib/domains/core/propertyService';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';
import { Building2 } from 'lucide-react';
import Link from 'next/link';

const MapContainer = dynamic(() => import('react-leaflet').then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import('react-leaflet').then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import('react-leaflet').then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import('react-leaflet').then(mod => mod.Popup), { ssr: false });

interface MapComponentLeafletProps {
    properties: Property[];
    onPropertySelect?: (property: Property) => void;
}

const MapComponentLeaflet: React.FC<MapComponentLeafletProps> = ({ properties }) => {
    useEffect(() => {
        (async () => {
            const L = (await import('leaflet')).default;
            const DefaultIcon = L.icon({
                iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            });
            L.Marker.prototype.options.icon = DefaultIcon;
        })();
    }, []);

    const defaultCenter: [number, number] = [59.9139, 10.7522];
    const safeProps = Array.isArray(properties) ? properties : [];
    const center = safeProps.length > 0 && safeProps[0].latitude && safeProps[0].longitude
        ? [safeProps[0].latitude, safeProps[0].longitude] as [number, number]
        : defaultCenter;

    return (
        <div className="h-full w-full relative z-0">
            <MapContainer
                center={center}
                zoom={10}
                style={{ height: '100%', width: '100%', borderRadius: '0.75rem', zIndex: 0 }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {safeProps.map((prop) => {
                    if (!prop.latitude || !prop.longitude) return null;
                    return (
                        <Marker key={prop.property_id} position={[prop.latitude, prop.longitude]}>
                            <Popup>
                                <div className="p-1 min-w-50">
                                    <div className="flex items-start gap-2 mb-2">
                                        <div className="p-1.5 bg-primary/10 rounded text-primary mt-0.5">
                                            <Building2 size={14} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-sm text-foreground">{prop.name}</h3>
                                            <p className="text-xs text-muted">{prop.address}</p>
                                        </div>
                                    </div>
                                    <div className="border-t border-border pt-2 mt-2 flex justify-between items-center">
                                        <span className="text-[10px] bg-muted/20 px-1.5 py-0.5 rounded text-muted uppercase tracking-wide">
                                            {prop.type || "Eiendom"}
                                        </span>
                                        <Link href={`/properties/${prop.property_id}`} className="text-xs text-primary font-bold hover:underline">
                                            Gå til eiendom →
                                        </Link>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default MapComponentLeaflet;
