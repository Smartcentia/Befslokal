'use client';

import React, { useState, useEffect } from 'react';
import { labChat, getTools, publishTool, searchTools, pinTool, LabResponse, Tool } from '@/lib/api';
import FinancialQueryPanel from '@/components/lab/FinancialQueryPanel';
// import { Navbar } from '@/components/ui/Navbar'; 

export default function LabPage() {
    const [activeTab, setActiveTab] = useState<'chat' | 'library' | 'financial'>('chat');

    // Chat State
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<LabResponse | null>(null);
    const [logs, setLogs] = useState<string[]>([]);

    // Toast State
    const [toast, setToast] = useState<{ message: string, type: 'success' | 'error' | 'info' | 'warning' } | null>(null);

    const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Library State
    const [tools, setTools] = useState<Tool[]>([]);
    const [loadingTools, setLoadingTools] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    // Fetch tools when Library tab is opened
    useEffect(() => {
        if (activeTab === 'library') {
            fetchTools();
        }
    }, [activeTab]);

    const fetchTools = async (search: string = '') => {
        setLoadingTools(true);
        try {
            let data;
            if (search.trim()) {
                data = await searchTools(search);
            } else {
                data = await getTools();
            }
            setTools(data);
        } catch (err) {
            console.error("Failed to fetch tools", err);
            showToast("Failed to fetch tools", 'error');
        } finally {
            setLoadingTools(false);
        }
    };

    const handlePublish = async (toolId: string) => {
        try {
            const res = await publishTool(toolId);
            if (res.status === 'success') {
                showToast(res.message, 'success');
                fetchTools(); // Refresh
            } else {
                showToast(`Error: ${res.message}`, 'error');
            }
        } catch (err: any) {
            showToast(err.message, 'error');
        }
    };

    const handlePin = async (tool: Tool) => {
        try {
            const newPinState = !tool.is_pinned;
            const res = await pinTool(tool.id, newPinState);
            if (res.status === 'success') {
                // Optimistic update
                setTools(prev => prev.map(t =>
                    t.id === tool.id ? { ...t, is_pinned: newPinState } : t
                ));
                showToast(res.message, 'success');
            } else {
                showToast(`Error: ${res.message}`, 'error');
            }
        } catch (err: any) {
            showToast(err.message, 'error');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setLogs([]);
        setResponse(null);

        try {
            setLogs(["🚀 Sending request to API..."]);
            // Fix: Pass array as expected by labChat signature
            const res = await labChat([{ role: 'user', content: query }]);
            setResponse(res);
            setLogs(res.logs || []);
        } catch (err: any) {
            setLogs(prev => [...prev, `❌ Error: ${err.message}`]);
            showToast(`Error: ${err.message}`, 'error');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0f172a] text-slate-200 font-sans relative">
            {/* Toast Notification - Improved */}
            {toast && (
                <div className="fixed bottom-4 right-4 z-50 max-w-md min-w-25">
                    <div
                        className={`
                            px-6 py-4 rounded-lg shadow-2xl border-2
                            flex items-start gap-3
                            animate-slide-in
                            backdrop-blur-sm
                            ${toast.type === 'success'
                                ? 'bg-green-900/95 border-green-600 text-green-50'
                                : toast.type === 'error'
                                    ? 'bg-red-900/95 border-red-600 text-red-50'
                                    : toast.type === 'warning'
                                        ? 'bg-orange-900/95 border-orange-600 text-orange-50'
                                        : 'bg-blue-900/95 border-blue-600 text-blue-50'
                            }
                        `}
                    >
                        {/* Icon */}
                        <span className="text-2xl shrink-0 mt-0.5">
                            {toast.type === 'success' ? '✅'
                                : toast.type === 'error' ? '❌'
                                    : toast.type === 'warning' ? '⚠️'
                                        : 'ℹ️'}
                        </span>

                        {/* Message - with multi-line support */}
                        <div className="flex-1 wrap-break-word whitespace-pre-wrap text-sm font-medium leading-relaxed">
                            {toast.message}
                        </div>

                        {/* Dismiss button */}
                        <button
                            onClick={() => setToast(null)}
                            className="shrink-0 text-white/60 hover:text-white transition-colors text-lg"
                            aria-label="Close notification"
                            title="Lukk varsling"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            <header className="border-b border-slate-800 bg-[#0f172a]/80 backdrop-blur p-4 sticky top-0 z-10 flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <h1 className="text-xl font-bold bg-linear-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                        🧪 AI Research Lab
                    </h1>

                    {/* Tabs */}
                    <div className="flex bg-slate-900 rounded-lg p-1 border border-slate-800">
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`px-4 py-1 text-xs font-bold rounded-md transition-all ${activeTab === 'chat' ? 'bg-cyan-900/50 text-cyan-400' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            PROTOCOL
                        </button>
                        <button
                            onClick={() => setActiveTab('library')}
                            className={`px-4 py-1 text-xs font-bold rounded-md transition-all ${activeTab === 'library' ? 'bg-cyan-900/50 text-cyan-400' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            LIBRARY
                        </button>
                        <button
                            onClick={() => setActiveTab('financial')}
                            className={`px-4 py-1 text-xs font-bold rounded-md transition-all ${activeTab === 'financial' ? 'bg-cyan-900/50 text-cyan-400' : 'text-slate-500 hover:text-slate-300'}`}
                        >
                            FINANCIAL
                        </button>
                    </div>
                </div>
                <div className="text-xs text-slate-500 font-mono">v1.2.0 | Shared Memory</div>
            </header>

            <main className="max-w-7xl mx-auto p-6">

                {activeTab === 'chat' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Left Column: Chat & Logs */}
                        <div className="flex flex-col gap-6">
                            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl">
                                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                                    <label className="text-sm font-medium text-slate-400">Target Objective</label>
                                    <textarea
                                        value={query}
                                        onChange={(e) => setQuery(e.target.value)}
                                        placeholder="E.g. Create a tool that calculates the Fibonacci sequence..."
                                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none min-h-25"
                                    />
                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {isLoading ? 'Processing...' : 'Execute Protocol'}
                                    </button>
                                </form>
                            </div>

                            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-0 flex-1 min-h-100 flex flex-col overflow-hidden font-mono text-xs">
                                <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 font-bold text-slate-400 flex justify-between">
                                    <span>SYSTEM LOGS</span>
                                    {response?.strategy && (
                                        <span className="text-cyan-400">STRATEGY: {response.strategy}</span>
                                    )}
                                </div>
                                <div className="p-4 overflow-y-auto flex-1 space-y-2">
                                    {logs.length === 0 && <span className="text-slate-600 italic">Waiting for input...</span>}
                                    {logs.map((log, i) => {
                                        const isHealing = log.includes("🩹") || log.includes("Self-Healing");
                                        const isError = log.includes("❌") || log.includes("Error");

                                        return (
                                            <div
                                                key={i}
                                                className={`
                                                    border-l-2 pl-2 py-0.5
                                                    ${isHealing
                                                        ? 'border-yellow-500 text-yellow-300 bg-yellow-900/10'
                                                        : isError
                                                            ? 'border-red-500 text-red-400 bg-red-900/10'
                                                            : 'border-slate-800'
                                                    }
                                                `}
                                            >
                                                {log}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Right Column: Code & Output */}
                        <div className="flex flex-col gap-6">
                            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-125">
                                <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 font-bold text-slate-400 flex justify-between items-center">
                                    <span>GENERATED TOOL CODE</span>
                                    {response?.status === 'created' && <span className="text-green-400 text-xs flex items-center gap-1">
                                        ● Live
                                        {logs.some(l => l.includes("Self-Healing")) && (
                                            <span className="bg-yellow-900/60 text-yellow-400 border border-yellow-700 px-1.5 rounded text-[10px] animate-pulse">
                                                🩹 Healed
                                            </span>
                                        )}
                                    </span>}
                                    {response?.status === 'found' && <span className="text-blue-400 text-xs">● Retrieved from Library</span>}
                                </div>
                                <div className="flex-1 overflow-auto p-4 bg-[#0d1117]">
                                    <pre className="font-mono text-xs text-green-400">
                                        {response?.code || "// No code generated yet."}
                                    </pre>
                                </div>
                            </div>

                            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-75">
                                <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 font-bold text-slate-400">
                                    SANDBOX STDOUT
                                </div>
                                <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-300">
                                    {response?.sandbox_stdout || "// Results will appear here."}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'library' && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl">
                        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                            <h2 className="text-lg font-bold text-slate-200">Global Tool Library</h2>

                            {/* Search Bar */}
                            <div className="relative w-full md:w-96">
                                <input
                                    type="text"
                                    placeholder="Search tools semantically..."
                                    className="w-full bg-slate-900 border border-slate-800 rounded-lg py-2 px-4 shadow-inner text-sm focus:ring-2 focus:ring-cyan-500 focus:outline-none pl-10"
                                    onKeyDown={async (e) => {
                                        if (e.key === 'Enter') {
                                            const val = e.currentTarget.value;
                                            setLoadingTools(true);
                                            try {
                                                // Trigger search logic
                                                if (val.trim()) {
                                                    await fetchTools(val);
                                                } else {
                                                    await fetchTools();
                                                }
                                            } catch (e) {
                                                console.error(e);
                                            }
                                        }
                                    }}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                                <span className="absolute left-3 top-2.5 text-slate-500 text-xs">🔍</span>
                            </div>

                            <button onClick={() => fetchTools()} className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded text-white whitespace-nowrap">Refresh</button>
                        </div>

                        {loadingTools ? (
                            <div className="text-center p-12 text-slate-500">
                                {searchQuery ? "Searching neural pathways..." : "Loading neural archives..."}
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {tools.map(tool => (
                                    <div key={tool.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors flex flex-col gap-3">
                                        <div className="flex justify-between items-start">
                                            <h3 className="font-bold text-cyan-400 text-sm truncate w-3/4">{tool.id.substring(0, 12)}...</h3>
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold flex items-center gap-1 ${tool.qa_status === 'pending' ? 'bg-purple-900/50 text-purple-400 border border-purple-800 animate-pulse' :
                                                tool.qa_status === 'fail' ? 'bg-red-900/50 text-red-400 border border-red-800' :
                                                    tool.status === 'verified' ? 'bg-green-900/50 text-green-400 border border-green-800' :
                                                        'bg-yellow-900/50 text-yellow-500 border border-yellow-800'
                                                }`}>
                                                {tool.qa_status === 'pending' ? 'QA Analyzing...' :
                                                    tool.qa_status === 'fail' ? 'QA Failed' :
                                                        tool.status}
                                            </span>
                                        </div>
                                        <p className="text-xs text-slate-400 line-clamp-3 min-h-12">
                                            {tool.description}
                                        </p>

                                        <div className="mt-auto pt-4 border-t border-slate-900 flex justify-between items-center">
                                            <span className="text-[10px] text-slate-600 font-mono">
                                                {new Date(tool.created_at).toLocaleDateString()}
                                            </span>

                                            <div className="flex gap-2">
                                                {tool.status === 'verified' && (
                                                    <button
                                                        onClick={() => handlePin(tool)}
                                                        className={`text-[10px] px-2 py-1 rounded-md uppercase font-bold tracking-wider border transition-colors ${tool.is_pinned
                                                            ? 'bg-cyan-900/50 text-cyan-400 border-cyan-800 hover:bg-cyan-900/30'
                                                            : 'bg-slate-900 text-slate-500 border-slate-700 hover:text-cyan-400 hover:border-cyan-700'
                                                            }`}
                                                    >
                                                        {tool.is_pinned ? 'Pinned ⚡' : 'Pin'}
                                                    </button>
                                                )}

                                                {tool.status === 'experimental' && (
                                                    <button
                                                        onClick={() => handlePublish(tool.id)}
                                                        className="text-[10px] bg-blue-900/30 hover:bg-blue-900/50 text-blue-400 border border-blue-900 px-2 py-1 rounded uppercase font-bold tracking-wider"
                                                    >
                                                        Publish
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {tools.length === 0 && (
                                    <div className="col-span-3 text-center text-slate-500 py-10">
                                        {searchQuery ? "No matching tools found." : "No tools found across the network."}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'financial' && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl">
                        <FinancialQueryPanel onToolCreated={(toolId) => {
                            showToast(`Tool created: ${toolId.substring(0, 12)}...`, 'success');
                        }} />
                    </div>
                )}
            </main>
        </div>
    );
}
