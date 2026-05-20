import { fetchAPI } from '../api/client';

export interface RecentActivityItem {
    type: string;
    text: string;
    time: string;
    icon: string;
    color: string;
}

export async function getRecentActivity(): Promise<RecentActivityItem[]> {
    try {
        const res = await fetchAPI('/dashboard/recent-activity');
        return res;
    } catch (error) {
        console.warn("Failed to fetch recent activity", error);
        return [];
    }
}

export interface Party {
    party_id: string;
    name: string;
    role: string;
    is_company: boolean;
}

export async function getParty(id: string) {
    return fetchAPI(`/parties/${id}`);
}

/** Hent firmaoppsummering via internett-søk + LLM. Lagres på partiet og returneres. Krever orgnr og OPENAI_API_KEY på backend. */
export async function fetchPartyCompanySummaryFromWeb(partyId: string): Promise<{ summary: string; saved: boolean }> {
    return fetchAPI(`/parties/${partyId}/company-summary-from-web`, { method: 'POST' });
}

export interface DueDiligenceReport {
    risk_level: 'LAV' | 'MIDDELS' | 'HØY';
    summary: string;
    red_flags: string[];
    detailed_analysis: { okonomi?: string; juridisk?: string; omdømme?: string };
    follow_up_questions: string[];
    sources: { url: string; title: string }[];
}

/** Kjør Due Diligence / risikovurdering for partiet. Lagres i external_data.due_diligence_report. */
export async function runPartyDueDiligence(partyId: string): Promise<DueDiligenceReport> {
    return fetchAPI(`/parties/${partyId}/due-diligence`, { method: 'POST' });
}

/** Hent BRREG-data (enhet + roller) for partiet. Lagres i external_data.brreg_enhet. Krever orgnr. */
export async function enrichPartyBrreg(partyId: string) {
    return fetchAPI(`/parties/${partyId}/enrich-brreg`, { method: 'POST' });
}

// ── Konkurs Monitor ──────────────────────────────────────────────────────────

export interface KonkursStatusEntry {
    party_id: string;
    name: string;
    orgnr: string;
    active_contracts: number;
    risk_level: 'CRITICAL' | 'WARNING' | 'OK';
    risk_flags: string[];
    konkurs: boolean;
    under_avvikling: boolean;
    under_tvangsavvikling: boolean;
    slettet: boolean;
    mangler_regnskap: boolean;
    siste_regnskap_aar?: number;
    checked_at?: string;
}

/** Hent alle parter med aktive risikoflagg (CRITICAL / WARNING). */
export async function getKonkursFlaggedParties(): Promise<KonkursStatusEntry[]> {
    return fetchAPI('/konkurs-monitor/flagged');
}

/** Kjør konkurssjekk for én part. */
export async function runKonkursCheckSingle(partyId: string): Promise<KonkursStatusEntry | null> {
    return fetchAPI(`/konkurs-monitor/run/${partyId}`, { method: 'POST' });
}

/** Kjør konkurssjekk for alle parter (bakgrunnsjobb). */
export async function runKonkursCheckAll(): Promise<{ status: string; message: string }> {
    return fetchAPI('/konkurs-monitor/run-all', { method: 'POST' });
}

/** Hent status fra siste kjøring av konkurssjekk. */
export async function getKonkursRunStatus(): Promise<Record<string, unknown>> {
    return fetchAPI('/konkurs-monitor/status');
}

// ── Media Monitor ────────────────────────────────────────────────────────────

export interface MediaMonitoringResult {
    sentiment_score: number;
    sentiment_label: 'Negativt' | 'Nøytralt' | 'Positivt';
    summary: string;
    red_flags: string[];
    positive_news: string[];
    sources_checked: number;
    last_updated?: string;
}

/** Kjør media monitor for én part. Returnerer resultat og lagrer i external_data.media_monitoring. */
export async function runMediaMonitorSingle(partyId: string): Promise<MediaMonitoringResult> {
    return fetchAPI(`/media-monitor/run/${partyId}`, { method: 'POST' });
}
