import { API_BASE_URL, getApiAuthContext } from '@/lib/api/client';

export interface ChatMessage { role: "user" | "assistant"; content: string; }
export interface Source {
    title: string;
    url?: string;
    id?: string;
    type?: string;
    name?: string;
}

export interface ChatContext {
    entity_type?: string;
    entity_id?: string;
    path: string;
}

/** UUID for matching /properties/{id} osv. */
const ENTITY_ID_RE =
 /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** App-rute → backend ChatContext.entity_type (kun typer med sidekontekst i API). */
const PATH_PREFIX_TO_ENTITY: Record<string, string> = {
    properties: "property",
    contracts: "contract",
    parties: "party",
    cases: "case",
    deviations: "deviation",
};

/**
 * Utleder page + valgfri entity fra Next.js pathname slik at backend kan injisere «BRUKEREN SER PÅ».
 */
export function extractContextFromPath(path: string): ChatContext {
    const pathOnly =
        (path.split("?")[0].split("#")[0] || "").replace(/\/+$/, "") || "/";
    const segments = pathOnly.split("/").filter(Boolean);
    const out: ChatContext = { path: pathOnly };

    if (segments.length >= 2) {
        const kind = segments[0];
        const id = segments[1];
        const entityType = PATH_PREFIX_TO_ENTITY[kind];
        if (entityType && ENTITY_ID_RE.test(id)) {
            out.entity_type = entityType;
            out.entity_id = id;
        }
    }
    return out;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
    const { token, session } = await getApiAuthContext();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    if (typeof window !== "undefined") {
        const impersonate = localStorage.getItem("impersonate_email");
        const user = localStorage.getItem("befs_user");
        const email =
            impersonate ||
            session?.user?.email ||
            (user ? (JSON.parse(user) as { email?: string }).email : null);
        if (email) headers["X-User-Email"] = email;
    }
    return headers;
}

export type ChatMode = "avansert" | "fullverdig";

export const kiKollegaService = {
    async getSuggestions(_entityType?: string, _entityId?: string): Promise<{ suggestions: string[] }> {
        return { suggestions: [] };
    },

    async chatFullverdig(
        message: string,
        context: ChatContext,
        history: ChatMessage[],
        conversationId?: string
    ): Promise<{ answer: string; sources: Source[]; follow_up_questions: string[]; conversation_id?: string; error?: string }> {
        const headers = await getAuthHeaders();
        const body = JSON.stringify({
            message,
            context: {
                page: context.path,
                ...(context.entity_type && context.entity_id
                    ? { entity_type: context.entity_type, entity_id: context.entity_id }
                    : {}),
            },
            history,
            conversation_id: conversationId ?? null,
        });
        const response = await fetch(`${API_BASE_URL}/ai/chat/fullverdig`, {
            method: "POST",
            headers,
            body,
        });
        if (!response.ok) {
            const text = await response.text().catch(() => "");
            throw new Error(`Feil fra server: ${response.status}${text ? ` – ${text}` : ""}`);
        }
        return response.json();
    },

    async submitFeedback(conversationId: string, rating: 1 | -1): Promise<void> {
        try {
            const headers = await getAuthHeaders();
            await fetch(`${API_BASE_URL}/ai/feedback`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ conversation_id: conversationId, rating }),
            });
        } catch (e) {
            // feedback er ikke kritisk – logg og gå videre
            console.warn('Feedback sending feilet:', e);
        }
    },

    chatStream(
        message: string,
        context: ChatContext,
        history: ChatMessage[],
        conversationId?: string
    ): AsyncIterable<{
        type: string;
        content: string;
        sources?: Source[];
        follow_up_questions?: string[];
        conversation_id?: string;
        error?: string;
        /** Diagram/tabell-data (SSB json-stat) når tilgjengelig */
        data?: Record<string, unknown> | null;
    }> {
        return {
            [Symbol.asyncIterator]() {
                let started = false;
                let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
                let buffer = "";
                let done = false;
                const decoder = new TextDecoder();

                return {
                    async next() {
                        if (done) return { done: true as const, value: { type: "done", content: "" } };

                        if (!started) {
                            started = true;
                            const headers = await getAuthHeaders();
                            const body = JSON.stringify({
                                message,
                                context: {
                                    page: context.path,
                                    ...(context.entity_type && context.entity_id
                                        ? {
                                              entity_type: context.entity_type,
                                              entity_id: context.entity_id,
                                          }
                                        : {}),
                                },
                                history,
                                conversation_id: conversationId ?? null,
                                stream: true,
                            });

                            const response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
                                method: "POST",
                                headers,
                                body,
                            });

                            if (!response.ok || !response.body) {
                                done = true;
                                return { done: false as const, value: { type: "error", content: `Feil fra server: ${response.status}` } };
                            }
                            reader = response.body.getReader();
                        }

                        // Read until a complete SSE event
                        while (true) {
                            const idx = buffer.indexOf("\n\n");
                            if (idx !== -1) {
                                const rawLine = buffer.slice(0, idx).trim();
                                buffer = buffer.slice(idx + 2);
                                if (rawLine.startsWith("data: ")) {
                                    try {
                                        const parsed = JSON.parse(rawLine.slice(6));
                                        if (parsed.type === "done") done = true;
                                        return { done: false as const, value: parsed };
                                    } catch {
                                        continue;
                                    }
                                }
                                continue;
                            }

                            if (!reader) { done = true; return { done: true as const, value: { type: "done", content: "" } }; }
                            const { value, done: streamDone } = await reader.read();
                            if (streamDone) {
                                done = true;
                                return { done: true as const, value: { type: "done", content: "" } };
                            }
                            buffer += decoder.decode(value, { stream: true });
                        }
                    },
                };
            },
        };
    },
};
