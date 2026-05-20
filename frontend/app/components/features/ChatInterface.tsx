"use client";

import { useState, useRef, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import { ExternalLink, Building, FileText, User, RefreshCw, Sparkles, ShieldCheck, Calendar, Clock, CheckCircle2, Zap, Search, Database, Shield, ThumbsUp, ThumbsDown } from 'lucide-react';
import { kiKollegaService, extractContextFromPath, ChatMessage, Source, ChatMode } from '@/lib/domains/innsikt/kiKollegaService';
import type { JsonStatRole } from '@/lib/ssb/jsonStatParse';
import SSBJsonStatChart from '@/app/components/features/ssb/SSBJsonStatChart';

// Custom renderer for Entity Links
const components = {
    a: ({ href, children }: any) => {
        if (!href) return <a href={href}>{children}</a>;

        // Check for Entity Protocols
        const isProperty = href.startsWith('property:');
        const isContract = href.startsWith('contract:');
        const isParty = href.startsWith('party:');
        const isCase = href.startsWith('case:');
        const isDeviation = href.startsWith('deviation:');
        const isActivity = href.startsWith('activity:');
        const isRisk = href.startsWith('risk:');
        const isUnit = href.startsWith('unit:');

        if (isProperty || isContract || isParty || isCase || isDeviation || isActivity || isRisk || isUnit) {
            const id = href.split(':')[1];
            let url = '#';
            let Icon = ExternalLink;

            if (isProperty) {
                url = `/properties/${id}`;
                Icon = Building;
            } else if (isContract) {
                url = `/contracts/${id}`;
                Icon = FileText;
            } else if (isParty) {
                url = `/parties/${id}`;
                Icon = User;
            } else if (isCase) {
                url = `/cases/${id}`;
                Icon = ShieldCheck;
            } else if (isDeviation) {
                url = `/deviations/${id}`;
                Icon = Clock;
            } else if (isActivity) {
                url = `/activities/${id}`;
                Icon = Calendar;
            } else if (isRisk) {
                url = `/risk-assessments/${id}`;
                Icon = ShieldCheck;
            } else if (isUnit) {
                url = `/units/${id}`;
                Icon = Building;
            }

            return (
                <Link
                    href={url}
                    className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs font-medium hover:bg-primary/20 transition-colors no-underline"
                >
                    <Icon size={12} />
                    <span className="truncate max-w-37.5">{children}</span>
                </Link>
            );
        }

        // Default Link
        return (
            <a
                href={href}
                className="text-primary hover:underline break-all"
                target="_blank"
                rel="noopener noreferrer"
            >
                {children}
            </a>
        );
    },
    // Style other elements
    ul: ({ children }: any) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
    li: ({ children }: any) => <li className="mb-1">{children}</li>,
    p: ({ children }: any) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
    strong: ({ children }: any) => <strong className="font-semibold text-foreground">{children}</strong>,
    table: ({ children }: any) => (
        <div className="overflow-x-auto my-2">
            <table className="min-w-full text-xs border-collapse">{children}</table>
        </div>
    ),
    th: ({ children }: any) => (
        <th className="border border-border bg-muted/20 px-2 py-1 text-left font-semibold">{children}</th>
    ),
    td: ({ children }: any) => (
        <td className="border border-border px-2 py-1">{children}</td>
    ),
};

/** Payload fra KI Kollega stream «done» for SSB-diagram */
interface KollegaChartPayload {
    rows: Array<Record<string, string | number | null>>;
    dimensionKeys: string[];
    valueKey: string;
    role?: JsonStatRole | null;
}

function isKollegaChartPayload(d: unknown): d is KollegaChartPayload {
    if (!d || typeof d !== 'object') return false;
    const o = d as Record<string, unknown>;
    return (
        Array.isArray(o.rows) &&
        o.rows.length > 0 &&
        Array.isArray(o.dimensionKeys) &&
        (o.dimensionKeys as unknown[]).length > 0 &&
        typeof o.valueKey === 'string'
    );
}

interface ExtendedMessage extends ChatMessage {
    sources?: Source[];
    followUpQuestions?: string[];
    chartPayload?: KollegaChartPayload | null;
    isError?: boolean;
    /** Samtale-ID brukt for tilbakemelding (satt ved 'done'-event) */
    conversationId?: string;
}

export default function ChatInterface() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<ExtendedMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [thinkingStatus, setThinkingStatus] = useState<string | null>(null);
    const [thinkingSteps, setThinkingSteps] = useState<string[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [mode, setMode] = useState<ChatMode>('avansert');
    /** { [messageIndex]: 1 | -1 } – tilbakemelding sendt per melding */
    const [feedbackSent, setFeedbackSent] = useState<Record<number, 1 | -1>>({});
    const scrollRef = useRef<HTMLDivElement>(null);
    const pathname = usePathname();

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, loading]);

    // Load suggestions based on context
    const loadSuggestions = useCallback(async () => {
        try {
            const context = extractContextFromPath(pathname);
            const data = await kiKollegaService.getSuggestions(
                context.entity_type,
                context.entity_id
            );
            setSuggestions(data.suggestions || []);
        } catch (error) {
            console.error('Failed to load suggestions:', error);
            setSuggestions([
                'Gi meg en oversikt over porteføljen',
                'Hvilke kontrakter utløper snart?',
                'Sammenlign regionene'
            ]);
        }
    }, [pathname]);

    useEffect(() => {
        if (messages.length === 0) {
            loadSuggestions();
        }
    }, [messages.length, loadSuggestions]);

    // Clear chat
    const clearChat = () => {
        setMessages([]);
        setConversationId(null);
        loadSuggestions();
    };

    async function handleSubmit(e?: React.FormEvent, customMessage?: string) {
        if (e) e.preventDefault();
        const text = customMessage || input;
        if (!text.trim()) return;

        const userMsg: ExtendedMessage = { role: 'user', content: text };
        const historyForApi: ChatMessage[] = messages
            .filter(m => !m.isError)
            .slice(-12)
            .map(m => ({ role: m.role, content: m.content }));

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);
        setThinkingStatus('KI Kollega tenker...');
        setThinkingSteps([]);

        const context = extractContextFromPath(pathname);

        try {
            if (mode === 'fullverdig') {
                setThinkingStatus('KI Kollega utfører oppgave...');
                const result = await kiKollegaService.chatFullverdig(text, context, historyForApi, conversationId || undefined);
                setThinkingStatus(null);
                const convId = result.conversation_id || conversationId || undefined;
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: result.answer || 'Jeg fant dessverre ikke noe svar.',
                    sources: result.sources,
                    followUpQuestions: result.follow_up_questions,
                    conversationId: convId,
                    isError: !!result.error,
                }]);
                if (result.conversation_id) setConversationId(result.conversation_id);
                return;
            }

            // Using streaming for better UX and to avoid proxy timeouts
            const stream = kiKollegaService.chatStream(text, context, historyForApi, conversationId || undefined);
            
            let assistantMsg: ExtendedMessage = { role: 'assistant', content: '' };
            let foundContent = false;

            for await (const chunk of stream) {
                if (chunk.type === 'status' && chunk.content) {
                    setThinkingStatus(chunk.content);
                    setThinkingSteps(prev => {
                        // Avoid duplicates if same status is sent multiple times
                        if (prev.includes(chunk.content)) return prev;
                        return [...prev, chunk.content];
                    });
                } else if (chunk.type === 'content' && chunk.content) {
                    if (!foundContent) {
                        foundContent = true;
                        setThinkingStatus(null);
                        setMessages(prev => [...prev, assistantMsg]);
                    }
                    assistantMsg.content += chunk.content;
                    // Update the last message in state
                    setMessages(prev => {
                        const newMsgs = [...prev];
                        newMsgs[newMsgs.length - 1] = { ...assistantMsg };
                        return newMsgs;
                    });
                } else if (chunk.type === 'done') {
                    const chartPayload = isKollegaChartPayload(chunk.data) ? chunk.data : null;
                    const doneConvId = chunk.conversation_id || conversationId || undefined;
                    if (!foundContent) {
                        // If we never got content (e.g. empty response or error handled as done)
                        setThinkingStatus(null);
                        setMessages(prev => [...prev, {
                            role: 'assistant',
                            content: assistantMsg.content || 'Jeg fant dessverre ikke noe svar på det.',
                            sources: chunk.sources,
                            followUpQuestions: chunk.follow_up_questions,
                            chartPayload,
                            conversationId: doneConvId,
                        }]);
                    } else {
                        // Just update final metadata
                        setMessages(prev => {
                            const newMsgs = [...prev];
                            const last = newMsgs[newMsgs.length - 1];
                            newMsgs[newMsgs.length - 1] = {
                                ...last,
                                sources: chunk.sources,
                                followUpQuestions: chunk.follow_up_questions,
                                chartPayload,
                                conversationId: doneConvId,
                            };
                            return newMsgs;
                        });
                    }
                    if (chunk.conversation_id) setConversationId(chunk.conversation_id);
                } else if (chunk.type === 'error') {
                    throw new Error(chunk.error || 'Ukjent feil');
                }
            }
        } catch (err: any) {
            console.error('Chat error:', err);
            setThinkingStatus(null);
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: err.message?.includes('lang tid') 
                    ? 'Forespørselen tok for lang tid. Prøv å forenkle spørsmålet eller prøv igjen senere.' 
                    : 'Beklager, det oppstod en feil under behandlingen av spørsmålet ditt.', 
                isError: true 
            }]);
        } finally {
            setLoading(false);
            setThinkingStatus(null);
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth" ref={scrollRef}>
                {messages.length === 0 && (
                    <div className="text-center text-muted mt-6">
                        <div className="bg-primary/5 p-4 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                            <Sparkles className="w-8 h-8 text-primary" />
                        </div>
                        <p className="font-medium text-foreground">Hei! Jeg er KI Kollega</p>
                        <p className="text-xs mt-1 text-muted">Spør meg om eiendommer, kontrakter, kostnader eller HMS.</p>

                        {/* Suggestions */}
                        {suggestions.length > 0 && (
                            <div className="mt-6 space-y-2">
                                <p className="text-xs uppercase tracking-wider text-muted">Forslag</p>
                                {suggestions.slice(0, 4).map((suggestion, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSubmit(undefined, suggestion)}
                                        className="block w-full text-left px-3 py-2 bg-muted/10 hover:bg-muted/20 border border-border rounded-lg text-sm text-foreground transition-colors"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[95%] md:max-w-[85%] p-3 rounded-lg text-sm shadow-sm relative group text-left ${m.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : m.isError
                                ? 'bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/30'
                                : 'bg-surface border border-border text-foreground'
                            }`}>

                            {m.role === 'user' ? (
                                <p>{m.content}</p>
                            ) : (
                                <>
                                    <ReactMarkdown components={components}>
                                        {m.content}
                                    </ReactMarkdown>

                                    {m.chartPayload && (
                                        <div className="mt-3 pt-2 border-t border-border">
                                            <p className="text-xs text-muted mb-2">
                                                Interaktivt diagram fra verktøydata i dette svaret. Ved flere datasett vises det siste som ble hentet.
                                            </p>
                                            <div className="h-64 w-full min-w-0">
                                                <SSBJsonStatChart
                                                    rows={m.chartPayload.rows}
                                                    dimensionKeys={m.chartPayload.dimensionKeys}
                                                    valueKey={m.chartPayload.valueKey}
                                                    role={m.chartPayload.role ?? undefined}
                                                />
                                            </div>
                                        </div>
                                    )}

                                    {/* Sources */}
                                    {m.sources && m.sources.length > 0 && (
                                        <div className="mt-3 pt-2 border-t border-border">
                                            <p className="text-xs text-muted mb-1">Kilder:</p>
                                            <div className="flex flex-wrap gap-1">
                                                {m.sources.slice(0, 8).map((source, si) => {
                                                    let Icon = ExternalLink;
                                                    let href: string | undefined;

                                                    if (source.type === 'property' && source.id) {
                                                        Icon = Building;
                                                        href = `/properties/${source.id}`;
                                                    } else if (source.type === 'contract' && source.id) {
                                                        Icon = FileText;
                                                        href = `/contracts/${source.id}`;
                                                    } else if (source.type === 'party' && source.id) {
                                                        Icon = User;
                                                        href = `/parties/${source.id}`;
                                                    } else if (source.type === 'case' && source.id) {
                                                        Icon = ShieldCheck;
                                                        href = `/cases/${source.id}`;
                                                    } else if (source.type === 'deviation' && source.id) {
                                                        Icon = Clock;
                                                        href = `/deviations/${source.id}`;
                                                    } else if (source.type === 'activity' && source.id) {
                                                        Icon = Calendar;
                                                        href = `/activities/${source.id}`;
                                                    } else if (source.type === 'risk' && source.id) {
                                                        Icon = ShieldCheck;
                                                        href = `/risk-assessments/${source.id}`;
                                                    } else if (source.url) {
                                                        href = source.url;
                                                        if (source.type === 'document') Icon = FileText;
                                                    }

                                                    const linkClass = 'inline-flex items-center gap-1 text-xs bg-muted/10 hover:bg-muted/20 px-2 py-0.5 rounded transition-colors text-foreground';
                                                    const label = source.name || source.type;

                                                    if (href) {
                                                        const isExternal = href.startsWith('http');
                                                        return isExternal ? (
                                                            <a
                                                                key={si}
                                                                href={href}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className={linkClass}
                                                            >
                                                                <Icon size={10} />
                                                                <span className="truncate max-w-30">{label}</span>
                                                            </a>
                                                        ) : (
                                                            <Link key={si} href={href} className={linkClass}>
                                                                <Icon size={10} />
                                                                <span className="truncate max-w-30">{label}</span>
                                                            </Link>
                                                        );
                                                    }
                                                    return (
                                                        <span key={si} className="text-xs bg-muted/10 px-2 py-0.5 rounded text-muted">
                                                            {label}
                                                        </span>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}

                                    {/* Follow-up questions */}
                                    {m.followUpQuestions && m.followUpQuestions.length > 0 && (
                                        <div className="mt-3 pt-2 border-t border-border space-y-1">
                                            {m.followUpQuestions.map((q, qi) => (
                                                <button
                                                    key={qi}
                                                    onClick={() => handleSubmit(undefined, q)}
                                                    className="block w-full text-left text-xs text-primary hover:text-primary/80 hover:underline"
                                                >
                                                    → {q}
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {/* Feedback buttons */}
                                    {m.conversationId && (
                                        <div className="mt-2 pt-2 border-t border-border/50 flex items-center gap-2">
                                            <span className="text-[10px] text-muted">Var svaret nyttig?</span>
                                            {feedbackSent[i] ? (
                                                <span className="text-[10px] text-muted italic">
                                                    {feedbackSent[i] === 1 ? '👍 Takk!' : '👎 Notert!'}
                                                </span>
                                            ) : (
                                                <>
                                                    <button
                                                        onClick={async () => {
                                                            setFeedbackSent(prev => ({ ...prev, [i]: 1 }));
                                                            await kiKollegaService.submitFeedback(m.conversationId!, 1);
                                                        }}
                                                        className="text-muted hover:text-emerald-500 transition-colors"
                                                        title="Bra svar"
                                                        aria-label="Bra svar"
                                                    >
                                                        <ThumbsUp size={13} />
                                                    </button>
                                                    <button
                                                        onClick={async () => {
                                                            setFeedbackSent(prev => ({ ...prev, [i]: -1 }));
                                                            await kiKollegaService.submitFeedback(m.conversationId!, -1);
                                                        }}
                                                        className="text-muted hover:text-red-500 transition-colors"
                                                        title="Dårlig svar"
                                                        aria-label="Dårlig svar"
                                                    >
                                                        <ThumbsDown size={13} />
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    )}
                                </>
                            )}

                            {/* TTS Button for Assistant */}
                            {m.role === 'assistant' && !m.isError && (
                                <button
                                    onClick={() => {
                                        const ut = new SpeechSynthesisUtterance(m.content);
                                        ut.lang = 'no-NO';
                                        window.speechSynthesis.speak(ut);
                                    }}
                                    className="absolute -right-8 top-2 text-muted hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity"
                                    title="Les opp"
                                    aria-label="Les opp melding"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                        <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 2.485.586 4.815 1.632 6.874.192.39.496.637.836.656h6.108c.991 0 1.944-.396 2.645-1.097l4.508-4.508c.944-.944 2.56-1.611 2.56-2.947v-6.918z" />
                                        <path fillRule="evenodd" d="M15.75 3.75a.75.75 0 01.75.75v.558c1.335.297 2.628.87 3.82 1.685.5.342.61.946.366 1.455a.75.75 0 01-1.16.223A8.99 8.99 0 0016.5 6.095v1.277c1.472.544 2.822 1.47 3.868 2.585.503.535.437 1.432-.164 1.916a.75.75 0 01-1.067.098 7.487 7.487 0 00-2.637-1.385v1.755c.951.353 1.838.852 2.64 1.458.557.42.628 1.156.273 1.748a.75.75 0 01-1.177.164A8.973 8.973 0 0016.5 17.654v.667a.75.75 0 01-1.5 0v-15a.75.75 0 01.75-.75z" clipRule="evenodd" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    </div>
                ))}

                {/* Thinking Status & Steps Indicator */}
                {(thinkingStatus || thinkingSteps.length > 0) && (
                    <div className="flex flex-col gap-2 max-w-[90%] animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {/* Summary of steps taken so far */}
                        {thinkingSteps.length > 0 && (
                            <div className="flex flex-col gap-1.5 ml-1">
                                {thinkingSteps.map((step, idx) => {
                                    const isLast = idx === thinkingSteps.length - 1 && loading;
                                    const iconColor = step.includes('Søk') ? 'text-blue-500' : 
                                                    step.includes('Analyse') ? 'text-amber-500' : 
                                                    step.includes('Kvalitet') ? 'text-emerald-500' : 'text-primary';
                                    
                                    return (
                                        <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-surface/50 border border-border/50 rounded-lg text-[11px] shadow-sm animate-in zoom-in-95 duration-200">
                                            {isLast ? (
                                                <RefreshCw className="w-3 h-3 animate-spin text-primary" />
                                            ) : (
                                                <CheckCircle2 className={`w-3 h-3 ${iconColor}`} />
                                            )}
                                            <span className="font-medium text-muted-foreground">{step}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        
                        {/* Current thinking spinner if no detailed steps yet or show current specific status */}
                        {loading && thinkingSteps.length === 0 && (
                            <div className="bg-surface border border-border text-foreground px-4 py-2 rounded-lg text-sm flex items-center gap-3 shadow-sm animate-pulse">
                                <RefreshCw className="w-4 h-4 animate-spin text-primary" />
                                <span className="font-medium text-muted-foreground">{thinkingStatus || 'KI Kollega tenker...'}</span>
                            </div>
                        )}
                    </div>
                )}

                {loading && !thinkingStatus && thinkingSteps.length === 0 && (
                    <div className="flex justify-start">
                        <div className="bg-surface border border-border text-muted p-3 rounded-lg text-xs flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" />
                            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:0.2s]" />
                            <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:0.4s]" />
                            Tenker...
                        </div>
                    </div>
                )}
            </div>

            {/* Clear chat + mode toggle */}
            <div className="px-4 py-1 border-t border-border flex justify-between items-center gap-2 flex-wrap">
                {messages.length > 0 && (
                    <button
                        onClick={clearChat}
                        className="text-xs text-muted hover:text-foreground flex items-center gap-1 transition-colors"
                    >
                        <RefreshCw size={12} />
                        Ny samtale
                    </button>
                )}
                <div className="flex items-center gap-1 ml-auto">
                    <button
                        onClick={() => setMode('avansert')}
                        disabled={loading}
                        className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border transition-colors ${mode === 'avansert' ? 'bg-primary text-primary-foreground border-primary' : 'text-muted border-border hover:border-primary/50'}`}
                        title="Avansert modus – full LangGraph-flyt"
                    >
                        <Search size={10} />
                        Avansert
                    </button>
                    <button
                        onClick={() => setMode('fullverdig')}
                        disabled={loading}
                        className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border transition-colors ${mode === 'fullverdig' ? 'bg-primary text-primary-foreground border-primary' : 'text-muted border-border hover:border-primary/50'}`}
                        title="Fullverdig – AI-first med domeneagenter (internkontroll, m.m.)"
                    >
                        <Zap size={10} />
                        Fullverdig
                    </button>
                </div>
            </div>

            {/* Input form */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-border flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Skriv et spørsmål..."
                    className="enterprise-input text-foreground"
                    disabled={loading}
                />
                <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="enterprise-button disabled:opacity-50"
                    aria-label="Send melding"
                    title="Send melding"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                    </svg>
                </button>
            </form>
        </div>
    );
}
