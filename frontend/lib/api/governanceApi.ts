import { fetchAPI } from './client';

export interface CatalogEntry {
    table: string;
    column: string;
    type: string;
    classification: string;
    description?: string;
    details?: Record<string, any> | null;
    is_json?: boolean;
}

export interface ClassificationStats {
    total_tables: number;
    classification_counts: Record<string, number>;
}

export interface SchemaForeignKey {
    from_table: string;
    from_columns: string[];
    to_table: string;
    to_columns: string[];
    name?: string | null;
}

export interface SchemaGraphResponse {
    tables: string[];
    foreign_keys: SchemaForeignKey[];
    mermaid: string;
}

export interface HelpArticle {
    id: string;
    title: string;
    content: string;
}

export const getGovernanceCatalog = async (): Promise<CatalogEntry[]> => {
    return fetchAPI<CatalogEntry[]>('/governance/catalog');
};

export const getClassificationStats = async (): Promise<ClassificationStats> => {
    return fetchAPI<ClassificationStats>('/governance/stats');
};

export const getSchemaGraph = async (): Promise<SchemaGraphResponse> => {
    return fetchAPI<SchemaGraphResponse>('/governance/schema-graph');
};

export const updateGovernanceDescription = async (table: string, column: string, description: string): Promise<void> => {
    return fetchAPI('/governance/catalog/description', {
        method: 'POST',
        body: JSON.stringify({ table, column, description }),
    });
};

export const getDPIA = async (): Promise<HelpArticle> => {
    return fetchAPI<HelpArticle>('/help/DPIA');
}

export const governanceApi = {
    getCatalog: getGovernanceCatalog,
    getStats: getClassificationStats,
    getSchemaGraph,
    updateDescription: updateGovernanceDescription,
    getDPIA: getDPIA
};
