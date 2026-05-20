'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import 'leaflet/dist/leaflet.css';

const MapContainer = dynamic(
    () => import('react-leaflet').then((mod) => mod.MapContainer),
    { ssr: false }
);
const TileLayer = dynamic(
    () => import('react-leaflet').then((mod) => mod.TileLayer),
    { ssr: false }
);
const Marker = dynamic(
    () => import('react-leaflet').then((mod) => mod.Marker),
    { ssr: false }
);
const Popup = dynamic(
    () => import('react-leaflet').then((mod) => mod.Popup),
    { ssr: false }
);

interface PropertyMapLeafletProps {
    latitude: number;
    longitude: number;
    propertyName: string;
    services?: any[];
}

const PropertyMapLeaflet: React.FC<PropertyMapLeafletProps> = ({
    latitude,
    longitude,
    propertyName,
}) => {
    const lat = latitude || 59.9139;
    const lng = longitude || 10.7522;
    const position: [number, number] = [lat, lng];
    const tileUrl = "https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{z}/{y}/{x}.png";
    const attribution = '&copy; <a href="http://www.kartverket.no/">Kartverket</a>';

    return (
        <div className="h-full w-full" style={{ minHeight: '280px' }}>
            {typeof window !== 'undefined' && (
                <MapContainer
                    center={position}
                    zoom={15}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom={false}
                >
                    <TileLayer url={tileUrl} attribution={attribution} />
                    <Marker position={position}>
                        <Popup>
                            <div className="text-sm font-medium">{propertyName}</div>
                            <div className="text-xs text-slate-500">
                                {lat.toFixed(4)}, {lng.toFixed(4)}
                            </div>
                        </Popup>
                    </Marker>
                </MapContainer>
            )}
        </div>
    );
};

export default PropertyMapLeaflet;
