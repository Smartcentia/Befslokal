'use client';

import React from 'react';
import { Property } from '@/lib/types';
import dynamic from 'next/dynamic';
import { LazyMap } from '@/app/components/ui/LazyMap';

const MapboxMap = dynamic(() => import('./MapComponentMapbox'), { ssr: false });

interface MapComponentProps {
    properties: Property[];
    onPropertySelect?: (property: Property) => void;
}

const MapComponent: React.FC<MapComponentProps> = (props) => {
    return (
        <LazyMap minHeight={400} className="h-full w-full">
            <MapboxMap {...props} />
        </LazyMap>
    );
};

export default MapComponent;
