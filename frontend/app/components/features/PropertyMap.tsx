'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { LazyMap } from '@/app/components/ui/LazyMap';

const MapboxMap = dynamic(() => import('./PropertyMapMapbox'), { ssr: false });

interface PropertyMapProps {
    latitude: number;
    longitude: number;
    propertyName: string;
    propertyUsage?: string;
    services?: any[];
}

const PropertyMap: React.FC<PropertyMapProps> = (props) => {
    return (
        <LazyMap minHeight={280} className="h-full w-full">
            <div className="h-full w-full rounded-xl overflow-hidden shadow-sm border border-slate-200 min-h-70">
                <MapboxMap {...props} />
            </div>
        </LazyMap>
    );
};

export default PropertyMap;
