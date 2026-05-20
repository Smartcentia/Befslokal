"use client";
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { fetchAPI } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import {
    Book, BookOpen, Rocket, LayoutDashboard, Building2, DoorOpen, FileText, Users,
    Stethoscope, Activity, Wrench, AlertTriangle, Zap, Search, Map, Settings,
    PieChart, BrainCircuit, Info, HelpCircle
} from 'lucide-react';

interface Article {
    id: string;
    title: string;
    filename?: string;
    category: string;
    content?: string;
}

const CATEGORY_ICONS: Record<string, any> = {
    'Introduksjon og Oversikt': BookOpen,
    'Kom i gang': Rocket,
    'Hovedfunksjoner': LayoutDashboard,
    'Dashboard': LayoutDashboard,
    'Eiendommer': Building2,
    'Enheter': DoorOpen,
    'Kontrakter': FileText,
    'Parter': Users,
    'BUP-lokasjoner': Stethoscope, // or Activity if Stethoscope not available? guide said local_hospital which matches Stethoscope/Plus like icon better.
    'Vedlikehold': Wrench,
    'Risikovurdering': AlertTriangle,
    'Søkefunksjonalitet': Search,
    'Kart': Map,
    'KI som Kjerne': BrainCircuit,
    'CMS (Content Management System)': Book,
    'Admin': Settings,
    'Analyser': PieChart,
    'Tips og Triks': HelpCircle,
    'Akronymer og Forkortelser': Info,
    'Help og Støtte': HelpCircle,
    'Historisk dokumentasjon (arkiv) – for administratorer': Settings
};

const ADMIN_ONLY_ARTICLE_ID_PREFIX = 'historisk-dokumentasjon';

export default function HelpCenter({ categoryFilter }: { categoryFilter?: string | string[] }) {
    const { role } = useAuth();
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedArticleIds, setExpandedArticleIds] = useState<Set<string>>(new Set());

    const isAdmin = role === 'ADMIN' || role === 'admin';

    useEffect(() => {
        const fetchArticles = async () => {
            setFetchError(null);
            try {
                const data = await fetchAPI('/help/');
                setArticles(Array.isArray(data) ? data : []);
                if (Array.isArray(data) && data.length > 0) {
                    const first = data.find((a: Article) => !a.id.toLowerCase().includes(ADMIN_ONLY_ARTICLE_ID_PREFIX)) || data[0];
                    setExpandedArticleIds(new Set([first.id]));
                }
            } catch (err) {
                console.error("Failed to fetch help articles", err);
                setFetchError("Kunne ikke laste dokumentasjon. Sjekk at du er koblet til nettverket og prøv igjen.");
            } finally {
                setLoading(false);
            }
        };
        fetchArticles();
    }, []);

    const toggleArticle = async (id: string) => {
        const newSet = new Set(expandedArticleIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
            // Fetch content if missing (for file-based articles that loaded empty)
            const article = articles.find(a => a.id === id);
            if (article && !article.content) {
                try {
                    const detail = await fetchAPI(`/help/${id}`);
                    setArticles(prev => prev.map(a => a.id === id ? { ...a, content: detail.content } : a));
                } catch (e) {
                    console.error("Failed to load content", e);
                }
            }
        }
        setExpandedArticleIds(newSet);
    };

    const handleSidebarClick = (id: string) => {
        if (!expandedArticleIds.has(id)) {
            toggleArticle(id);
        }
        const element = document.getElementById(`card-${id}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    const visibleArticles = isAdmin
        ? articles
        : articles.filter(a => !a.id.toLowerCase().includes(ADMIN_ONLY_ARTICLE_ID_PREFIX));

    const filteredArticles = visibleArticles.filter(a => {
        const term = searchTerm.toLowerCase();
        const matchesSearch = a.title.toLowerCase().includes(term) ||
            a.category.toLowerCase().includes(term) ||
            (a.content && a.content.toLowerCase().includes(term));

        if (categoryFilter) {
            const filters = Array.isArray(categoryFilter) ? categoryFilter : [categoryFilter];
            return matchesSearch && filters.includes(a.category);
        }
        return matchesSearch;
    });

    if (loading) return (
        <div className="p-8 text-center text-muted-foreground animate-pulse flex flex-col items-center gap-4">
            <div className="w-12 h-12 rounded-full border-2 border-primary/30 border-t-primary animate-spin" aria-hidden />
            <p>Laster kunnskapsbasen...</p>
        </div>
    );

    return (
        <div className="flex flex-col lg:flex-row gap-8 text-foreground">
            {/* Sidebar Navigation */}
            <aside className="w-full lg:w-72 flex-shrink-0">
                <div className="sticky top-24 glass-card overflow-hidden flex flex-col max-h-[calc(100vh-120px)] ring-1 ring-border">
                    <div className="p-4 border-b border-border bg-[var(--glass-bg)] backdrop-blur-xl">
                        <h2 className="font-bold text-foreground flex items-center gap-3 text-lg">
                            <BookOpen className="w-5 h-5 text-primary" />
                            Innhold
                        </h2>
                    </div>
                    <nav className="p-3 space-y-1 overflow-y-auto custom-scrollbar">
                        {filteredArticles.map(article => {
                            const Icon = CATEGORY_ICONS[article.title] || CATEGORY_ICONS[article.category] || Book;
                            const isActive = expandedArticleIds.has(article.id);
                            return (
                                <button
                                    key={article.id}
                                    onClick={() => handleSidebarClick(article.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group
                                        ${isActive
                                            ? 'bg-primary shadow-lg shadow-primary/20 text-primary-foreground ring-1 ring-primary/50'
                                            : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground text-left'}`}
                                >
                                    <Icon size={18} className={`transition-colors flex-shrink-0 ${isActive ? 'text-primary-foreground' : 'text-muted-foreground group-hover:text-foreground'}`} />
                                    <span className="truncate leading-relaxed">{article.title}</span>
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 min-w-0 space-y-6">
                {/* Search Bar */}
                <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                        <Search className="h-6 w-6 text-muted-foreground group-focus-within:text-primary transition-colors" />
                    </div>
                    <input
                        type="text"
                        className="block w-full pl-14 pr-4 py-5 bg-background border border-border rounded-2xl text-lg leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all shadow-sm"
                        placeholder="Søk i dokumentasjonen..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                {/* Tips Card */}
                {!categoryFilter && searchTerm === '' && (
                    <div className="glass-card p-8 border-l-4 border-l-primary bg-linear-to-r from-primary/10 to-transparent">
                        <div className="flex items-start gap-5">
                            <div className="p-3 bg-primary/20 rounded-xl shadow-inner">
                                <Info size={24} className="text-primary" />
                            </div>
                            <div>
                                <h3 className="font-bold text-foreground text-xl mb-2">Velkommen til Brukerhjelpen</h3>
                                <p className="text-base text-muted-foreground leading-relaxed">
                                    Her finner du komplett dokumentasjon for systemet. Bruk menyen til venstre for å navigere i kapitlene, eller søkefeltet over for å finne spesifikk informasjon.
                                </p>
                                <p className="text-sm text-muted-foreground mt-3">
                                    Se også: <a href="/tilgjengelighet" className="text-primary hover:underline font-medium">Tilgjengelighet</a> og <a href="/personvern" className="text-primary hover:underline font-medium">Personvern</a>.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Content Cards (Accordion) */}
                <div className="space-y-4">
                    {filteredArticles.map(article => {
                        const Icon = CATEGORY_ICONS[article.title] || CATEGORY_ICONS[article.category] || Book;
                        const isExpanded = expandedArticleIds.has(article.id);

                        return (
                            <div
                                id={`card-${article.id}`}
                                key={article.id}
                                className={`glass-card overflow-hidden transition-all duration-300 border
                                    ${isExpanded ? 'border-primary/30 bg-overlay shadow-2xl' : 'border-border hover:bg-surface/50 hover:border-primary/20'}`}
                            >
                                <button
                                    onClick={() => toggleArticle(article.id)}
                                    className="w-full flex items-center justify-between p-6 text-left focus:outline-none group"
                                >
                                    <div className="flex items-center gap-5">
                                        <div className={`p-4 rounded-2xl transition-all duration-300 shadow-lg ${isExpanded ? 'bg-primary text-primary-foreground shadow-primary/30' : 'bg-muted/40 text-muted-foreground group-hover:bg-muted/60 group-hover:text-foreground'}`}>
                                            <Icon size={28} strokeWidth={1.5} />
                                        </div>
                                        <div>
                                            <h2 className={`text-xl font-bold transition-colors ${isExpanded ? 'text-foreground' : 'text-foreground group-hover:text-primary'}`}>
                                                {article.title}
                                            </h2>
                                            {!isExpanded && (
                                                <p className="text-sm text-muted-foreground mt-1 line-clamp-1 group-hover:text-foreground">
                                                    Klikk for å lese kapittelet...
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    <div className={`p-2 rounded-full transition-all duration-300 ${isExpanded ? 'bg-primary/15 rotate-180 text-primary' : 'text-muted-foreground group-hover:bg-muted/60 group-hover:text-foreground'}`}>
                                        <svg
                                            className="w-6 h-6"
                                            fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                        >
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </button>

                                {isExpanded && (
                                    <div className="px-8 pb-10 pt-4 animate-fadeIn border-t border-border">
                                        <div className="prose prose-neutral prose-lg max-w-none dark:prose-invert prose-headings:font-bold prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-p:text-muted-foreground prose-a:text-primary prose-strong:text-foreground prose-code:text-primary prose-code:bg-muted/50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none">
                                            {article.content ? (
                                                <ReactMarkdown
                                                    components={{
                                                        // Custom components to ensure strict design system adherence
                                                        h1: ({ node, ...props }) => <h1 className="text-3xl font-bold text-foreground mb-6 mt-8" {...props} />,
                                                        h2: ({ node, ...props }) => <h2 className="text-2xl font-semibold text-primary mb-4 mt-10 pb-2 border-b border-border flex items-center gap-2" {...props} />,
                                                        h3: ({ node, ...props }) => <h3 className="text-xl font-medium text-foreground mb-3 mt-6" {...props} />,
                                                        p: ({ node, ...props }) => <p className="text-muted-foreground leading-relaxed mb-4 text-base" {...props} />,
                                                        ul: ({ node, ...props }) => <ul className="list-disc list-outside ml-6 space-y-2 text-muted-foreground mb-6" {...props} />,
                                                        ol: ({ node, ...props }) => <ol className="list-decimal list-outside ml-6 space-y-2 text-muted-foreground mb-6" {...props} />,
                                                        li: ({ node, ...props }) => <li className="pl-1 marker:text-primary" {...props} />,
                                                        a: ({ node, ...props }) => <a className="text-primary hover:text-primary/80 underline decoration-primary/30 hover:decoration-primary transition-all font-medium" target="_blank" {...props} />,
                                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-primary bg-primary/10 py-4 px-6 rounded-r-xl my-6 not-italic" {...props} />,
                                                        code: ({ node, className, children, ...props }) => {
                                                            const match = /language-(\w+)/.exec(className || '')
                                                            return !String(children).includes('\n') ? (
                                                                <code className="bg-muted/10 text-primary px-1.5 py-0.5 rounded font-mono text-sm border border-border" {...props}>
                                                                    {children}
                                                                </code>
                                                            ) : (
                                                                <code className={className} {...props}>
                                                                    {children}
                                                                </code>
                                                            )
                                                        },
                                                        pre: ({ node, ...props }) => <pre className="bg-surface/50 p-0 rounded-xl overflow-hidden border border-border my-6 shadow-lg" {...props}><div className="bg-surface/50 px-4 py-2 border-b border-border text-xs font-mono text-muted uppercase tracking-widest">Code</div><div className="p-4 overflow-x-auto">{props.children}</div></pre>,
                                                        table: ({ node, ...props }) => <div className="overflow-x-auto my-8 rounded-xl border border-border shadow-lg"><table className="min-w-full divide-y divide-border" {...props} /></div>,
                                                        thead: ({ node, ...props }) => <thead className="bg-surface/50" {...props} />,
                                                        tbody: ({ node, ...props }) => <tbody className="divide-y divide-border bg-transparent" {...props} />,
                                                        tr: ({ node, ...props }) => <tr className="hover:bg-surface/10 transition-colors group" {...props} />,
                                                        th: ({ node, ...props }) => <th className="px-6 py-4 text-left text-xs font-bold text-muted uppercase tracking-wider" {...props} />,
                                                        td: ({ node, ...props }) => <td className="px-6 py-4 whitespace-nowrap text-sm text-muted group-hover:text-foreground transition-colors" {...props} />,
                                                    }}
                                                >
                                                    {article.content}
                                                </ReactMarkdown>
                                            ) : (
                                                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
                                                    <div className="w-8 h-8 rounded-full border-2 border-border border-t-primary animate-spin" aria-hidden />
                                                    <p className="text-sm font-medium">Henter innhold...</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {fetchError && (
                        <div className="flex flex-col items-center justify-center py-20 glass-card border-dashed border-red-500/30 bg-red-950/20">
                            <div className="p-6 rounded-full bg-red-500/20 mb-6 ring-1 ring-red-500/30">
                                <AlertTriangle className="w-12 h-12 text-red-400" />
                            </div>
                            <h3 className="text-xl font-bold text-foreground mb-2">Kunne ikke laste dokumentasjon</h3>
                            <p className="text-muted max-w-sm text-center leading-relaxed mb-4">{fetchError}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                            >
                                Last siden på nytt
                            </button>
                        </div>
                    )}
                    {!fetchError && filteredArticles.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20 glass-card border-dashed border-border/50">
                            <div className="p-6 rounded-full bg-surface/50 mb-6 ring-1 ring-border shadow-xl">
                                <Search className="w-12 h-12 text-muted" />
                            </div>
                            <h3 className="text-xl font-bold text-foreground mb-2">Ingen treff</h3>
                            <p className="text-muted max-w-sm text-center leading-relaxed">
                                {searchTerm
                                    ? `Vi fant ingen artikler som matcher "${searchTerm}". Prøv et annet søkeord eller bla gjennom menyen.`
                                    : "Ingen dokumentasjon ble funnet. Kontakt administrator hvis problemet vedvarer."}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
