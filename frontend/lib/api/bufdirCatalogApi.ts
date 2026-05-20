import { fetchAPI } from './client';

export interface BufdirCatalogItem {
  id: number | null;
  name?: string | null;
  address?: string | null;
  location?: string | null;
  owner_type?: string | null;
  bufdir_url?: string | null;
  image_url?: string | null;
  legal_bases: string[];
  property_id?: string | null;
  in_befs_portfolio: boolean;
}

export interface BufdirCatalogResponse {
  generated_at: string;
  source_file: string;
  matches_file: string;
  count: number;
  matched_count: number;
  items: BufdirCatalogItem[];
}

export async function getBufdirInstitutionsCatalog(): Promise<BufdirCatalogResponse> {
  return fetchAPI<BufdirCatalogResponse>('/bufdir-catalog/institutions');
}
