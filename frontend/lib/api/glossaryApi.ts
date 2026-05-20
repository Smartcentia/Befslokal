import { fetchAPI } from "./client";

export interface GlossaryTerm {
    term: string;
    definition: string;
    tags?: string[];
    usage?: TermUsage[];
}

export interface TermUsage {
    term: string;
    file: string;
    line: number;
    context: string;
}

export const glossaryApi = {
    getTerms: async (): Promise<GlossaryTerm[]> => {
        return await fetchAPI<GlossaryTerm[]>("/glossary");
    },
    scanTerms: async (): Promise<any> => {
        return await fetchAPI<any>("/glossary/scan", {
            method: "POST",
        });
    },
};
