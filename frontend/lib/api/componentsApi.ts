import { fetchAPI } from './client';

export interface BuildingComponent {
    component_id: string;
    property_id: string;
    name: string;
    type?: string;
    ns3451_code?: string;
    parent_id?: string;
    status: string;
}

export type CreateComponentData = Omit<BuildingComponent, 'component_id' | 'status'> & { status?: string };

export const componentsApi = {
    getByProperty: async (propertyId: string) => {
        try {
            return await fetchAPI<BuildingComponent[]>(`/fdv/components/property/${propertyId}`);
        } catch (error) {
            console.error("Failed to fetch components:", error);
            return [];
        }
    },

    create: async (data: CreateComponentData) => {
        return await fetchAPI<BuildingComponent>('/fdv/components', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    update: async (id: string, data: Partial<BuildingComponent>) => {
        return await fetchAPI<BuildingComponent>(`/fdv/components/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};
