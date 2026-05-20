import React, { useState } from 'react';
import { Tool, executeTool } from '@/lib/api';

interface AIWidgetProps {
    tool: Tool;
}

export const AIWidget: React.FC<AIWidgetProps> = ({ tool }) => {
    const [input, setInput] = useState('');
    const [output, setOutput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleRun = async () => {
        setIsLoading(true);
        setError(null);
        setOutput('');

        try {
            const res = await executeTool(tool.id, input);
            if (res.status === 'error') {
                setError(res.error || res.message || 'Unknown error');
            } else {
                // If sandbox stdout is available, use it. Else use result prop?
                // Backend execute_tool returns result from sandbox.run_code
                // which has { status, stdout, stderr, logs ... }
                // So if status=Success, we show stdout.
                if (res.status === 'Success') {
                    setOutput(res.stdout || '✅ Executed successfully (No Output)');
                } else if (res.status === 'failed') {
                    setError(res.error || res.stderr || 'Execution failed');
                } else {
                    // Fallback
                    setOutput(JSON.stringify(res, null, 2));
                }
            }
        } catch (e) {
            setError('Failed to reach neural core.');
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-5 shadow-lg backdrop-blur-sm flex flex-col h-full hover:border-cyan-900/50 transition-colors group">
            <div className="flex justify-between items-start mb-3">
                <h3 className="text-cyan-400 font-bold text-sm tracking-wide truncate w-3/4 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                    {tool.name.replace("AutoTool-", "")}
                </h3>
                <span className="text-[10px] text-slate-500 font-mono">{tool.id.substring(0, 4)}</span>
            </div>

            <p className="text-slate-400 text-xs mb-4 min-h-[2.5em] line-clamp-2">
                {tool.description}
            </p>

            <div className="flex-1 flex flex-col gap-2">
                <textarea
                    className="w-full bg-slate-950/50 border border-slate-800 rounded p-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-800/50 resize-none font-mono"
                    rows={2}
                    placeholder="Input parameters..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                />

                {output && (
                    <div className="bg-black/30 rounded p-2 text-[10px] font-mono text-green-400 overflow-x-auto whitespace-pre-wrap max-h-32 border-l-2 border-green-900">
                        {output}
                    </div>
                )}

                {error && (
                    <div className="bg-red-900/10 rounded p-2 text-[10px] font-mono text-red-400 border-l-2 border-red-900">
                        {error}
                    </div>
                )}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800/50 flex justify-end">
                <button
                    onClick={handleRun}
                    disabled={isLoading}
                    className="bg-cyan-900/20 hover:bg-cyan-900/40 text-cyan-400 border border-cyan-900/50 text-xs px-4 py-1.5 rounded transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isLoading ? (
                        <>
                            <span className="w-3 h-3 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></span>
                            Running...
                        </>
                    ) : (
                        <>▶ EXECUTE</>
                    )}
                </button>
            </div>
        </div>
    );
};
