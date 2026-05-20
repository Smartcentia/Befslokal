import { fetchAPI } from './client';

export interface BrregEnhet {
    organisasjonsnummer: string;
    navn: string;
    organisasjonsform?: { kode: string; beskrivelse: string };
    registreringsdatoEnhetsregisteret?: string;
    registrertIMvaregisteret?: boolean;
    naeringskode1?: { kode: string; beskrivelse: string };
    antallAnsatte?: number;
    forretningsadresse?: {
        adresse: string[];
        postnummer: string;
        poststed: string;
        kommune: string;
        land: string;
    };
    stiftelsesdato?: string;
    institusjonellSektorkode?: { kode: string; beskrivelse: string };
    registrertIForetaksregisteret?: boolean;
    registrertIStiftelsesregisteret?: boolean;
    registrertIFrivillighetsregisteret?: boolean;
    konkurs?: boolean;
    underAvvikling?: boolean;
    underTvangsavviklingEllerTvangsopplosning?: boolean;
    maalform?: string;
    sisteInnsendteAarsregnskap?: string;
    roller?: Array<{
        type: string;
        person?: { navn: string; fodselsdato?: string };
        enhet?: { organisasjonsnummer: string; navn: string };
    }>;
}

export interface BrregRegnskap {
    id: number;
    journalnr: string;
    regnskapstype: string;
    virksomhet?: { organisasjonsnummer: string; organisasjonsform: string; morselskap: boolean };
    regnskapsperiode?: { fraDato: string; tilDato: string };
    valuta: string;
    avviklingsregnskap: boolean;
    oppstillingsplan?: string;
    revisjon?: { ikkeRevidertAarsregnskap: boolean };
    regnkapsprinsipper?: Record<string, unknown>;
    egenkapitalGjeld?: Record<string, unknown>;
    eiendeler?: Record<string, unknown>;
    resultatregnskapResultat?: Record<string, unknown>;
}

export interface LeverandorRisiko {
    orgnr: string;
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    flags: string[];
    details: {
        konkurs: boolean;
        under_avvikling: boolean;
        siste_regnskap?: number;
        antall_ansatte?: number;
        sektor?: string;
    };
    last_checked: string;
}

export interface KartverketGeocodeResult {
    lat: number;
    lon: number;
    display_name: string;
    address: {
        road?: string;
        house_number?: string;
        postcode?: string;
        city?: string;
        municipality?: string;
        county?: string;
    };
    confidence: number;
}

export interface KartverketReverseResult {
    address: string;
    municipality: string;
    county: string;
    postcode: string;
    city: string;
}

export interface NVEFloodZone {
    zone_id: string;
    zone_type: string;
    risk_level: 'low' | 'medium' | 'high';
    return_period: number;
    description: string;
    geometry?: Record<string, unknown>;
}

export interface NVEEnergyData {
    property_address: string;
    energy_label?: string;
    heating_demand_kwh?: number;
    electricity_demand_kwh?: number;
    heating_sources: string[];
    co2_emissions_kg?: number;
}

export interface FrostObservation {
    station_id: string;
    station_name: string;
    timestamp: string;
    temperature?: number;
    precipitation?: number;
    wind_speed?: number;
    humidity?: number;
}

export interface LovdataResult {
    title: string;
    url: string;
    snippet: string;
    document_type: string;
    published_date?: string;
}

export interface PlanslurpenResult {
    plan_id: string;
    name: string;
    status: string;
    municipality: string;
    description?: string;
    url?: string;
}

export async function getBrregEnhet(orgnr: string): Promise<BrregEnhet> {
    return fetchAPI<BrregEnhet>(`/external/brreg/${orgnr}`);
}

export async function getBrregRegnskap(orgnr: string): Promise<BrregRegnskap[]> {
    return fetchAPI<BrregRegnskap[]>(`/external/brreg/${orgnr}/regnskap`);
}

export async function getLeverandorRisiko(orgnr: string): Promise<LeverandorRisiko> {
    return fetchAPI<LeverandorRisiko>(`/external/risk/${orgnr}`);
}

export async function geocodeAddress(address: string): Promise<KartverketGeocodeResult | null> {
    const params = new URLSearchParams({ address });
    return fetchAPI<KartverketGeocodeResult | null>(`/external/kartverket/geocode?${params}`);
}

export async function reverseGeocode(lat: number, lon: number): Promise<KartverketReverseResult | null> {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    return fetchAPI<KartverketReverseResult | null>(`/external/kartverket/reverse?${params}`);
}

export async function getNVEFloodZones(lat: number, lon: number): Promise<NVEFloodZone[]> {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    return fetchAPI<NVEFloodZone[]>(`/external/nve/flood-zones?${params}`);
}

export async function getNVEEnergyData(address: string): Promise<NVEEnergyData | null> {
    const params = new URLSearchParams({ address });
    return fetchAPI<NVEEnergyData | null>(`/external/nve/energy?${params}`);
}

export async function getFrostObservations(
    stationId: string,
    fromDate: string,
    toDate: string
): Promise<FrostObservation[]> {
    const params = new URLSearchParams({
        station_id: stationId,
        from_date: fromDate,
        to_date: toDate,
    });
    return fetchAPI<FrostObservation[]>(`/external/frost/observations?${params}`);
}

export async function searchLovdata(query: string): Promise<LovdataResult[]> {
    return fetchAPI<LovdataResult[]>(`/external/fetch-lovdata?query=${encodeURIComponent(query)}`, {
        method: 'POST',
    });
}

export async function searchPlanslurpen(
    lat: number,
    lon: number,
    radius: number = 1000
): Promise<PlanslurpenResult[]> {
    return fetchAPI<PlanslurpenResult[]>('/external/fetch-planslurpen', {
        method: 'POST',
        body: JSON.stringify({ lat, lon, radius }),
    });
}

export const externalApi = {
    brreg: {
        getEnhet: getBrregEnhet,
        getRegnskap: getBrregRegnskap,
        getRisiko: getLeverandorRisiko,
    },
    kartverket: {
        geocode: geocodeAddress,
        reverse: reverseGeocode,
    },
    nve: {
        floodZones: getNVEFloodZones,
        energyData: getNVEEnergyData,
    },
    frost: {
        observations: getFrostObservations,
    },
    lovdata: {
        search: searchLovdata,
    },
    planslurpen: {
        search: searchPlanslurpen,
    },
};
