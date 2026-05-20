import { fetchAPI, API_BASE_URL } from './client';

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface ChatResponse {
    response: string;
    sources?: Array<{
        type: string;
        id?: string;
        title?: string;
    }>;
    suggestions?: string[];
    processing_time_ms?: number;
}

export interface StreamChatOptions {
    messages: ChatMessage[];
    context?: {
        property_id?: string;
        contract_id?: string;
        deviation_id?: string;
    };
    onChunk: (chunk: string) => void;
    onDone?: () => void;
    onError?: (error: Error) => void;
}

export interface AISuggestion {
    type: string;
    title: string;
    description: string;
    action?: string;
    priority: 'low' | 'medium' | 'high';
}

export interface ProactiveInsight {
    insight_id: string;
    type: string;
    title: string;
    description: string;
    severity: 'info' | 'warning' | 'critical';
    entity_type?: string;
    entity_id?: string;
    created_at: string;
}

export interface AIHealth {
    status: 'healthy' | 'degraded' | 'unavailable';
    models_available: string[];
    last_request: string;
    average_latency_ms: number;
}

export interface AITransparencyVitals {
    total_requests_24h: number;
    average_latency_ms: number;
    error_rate: number;
    tokens_used_24h: number;
    cost_estimate_24h: number;
    by_endpoint: Record<string, { requests: number; avg_latency: number }>;
}

export interface AIBenchmarkScenario {
    scenario_id: string;
    name: string;
    description: string;
    expected_response: string;
    actual_response?: string;
    passed?: boolean;
    latency_ms?: number;
}

export async function chat(
    messages: ChatMessage[],
    context?: { property_id?: string; contract_id?: string }
): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ messages, context }),
    });
}

export async function chatSimple(message: string): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>('/ai/chat/simple', {
        method: 'POST',
        body: JSON.stringify({ message }),
    });
}

export async function chatFullverdig(
    messages: ChatMessage[],
    context?: Record<string, unknown>
): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>('/ai/chat/fullverdig', {
        method: 'POST',
        body: JSON.stringify({ messages, context }),
    });
}

export async function chatUnified(
    messages: ChatMessage[],
    options?: { tools?: string[]; context?: Record<string, unknown> }
): Promise<ChatResponse> {
    return fetchAPI<ChatResponse>('/ai/chat/unified', {
        method: 'POST',
        body: JSON.stringify({ messages, ...options }),
    });
}

export async function streamChat(options: StreamChatOptions): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            messages: options.messages,
            context: options.context,
        }),
    });

    if (!response.ok) {
        throw new Error(`Stream error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            options.onChunk(chunk);
        }
        options.onDone?.();
    } catch (error) {
        options.onError?.(error as Error);
    }
}

export async function getSuggestions(
    entityType: string,
    entityId: string
): Promise<AISuggestion[]> {
    return fetchAPI<AISuggestion[]>(
        `/ai/suggestions?entity_type=${entityType}&entity_id=${entityId}`
    );
}

export async function getProactiveInsights(): Promise<ProactiveInsight[]> {
    return fetchAPI<ProactiveInsight[]>('/ai/proactive');
}

export async function getAIHealth(): Promise<AIHealth> {
    return fetchAPI<AIHealth>('/ai/health');
}

export async function getAIDebug(): Promise<Record<string, unknown>> {
    return fetchAPI('/ai/debug');
}

export async function getTransparencyVitals(): Promise<AITransparencyVitals> {
    return fetchAPI<AITransparencyVitals>('/ai/transparency/vitals');
}

export async function getBenchmarkScenarios(): Promise<AIBenchmarkScenario[]> {
    return fetchAPI<AIBenchmarkScenario[]>('/ai/transparency/scenarios');
}

export const aiApi = {
    chat,
    chatSimple,
    chatFullverdig,
    chatUnified,
    streamChat,
    suggestions: getSuggestions,
    proactiveInsights: getProactiveInsights,
    health: getAIHealth,
    debug: getAIDebug,
    transparency: {
        vitals: getTransparencyVitals,
        scenarios: getBenchmarkScenarios,
    },
};
