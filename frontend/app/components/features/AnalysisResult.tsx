import React from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import { Sparkles, X } from 'lucide-react';

interface AnalysisResultProps {
    title: string;
    content: string;
    onClose: () => void;
}

export default function AnalysisResult({ title, content, onClose }: AnalysisResultProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-overlay backdrop-blur-sm">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-surface border border-primary/30 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl shadow-primary/20"
            >
                {/* Header */}
                <div className="p-6 border-b border-border flex items-center justify-between bg-muted/10">
                    <div className="flex items-center gap-3">
                        <div className="bg-primary/20 p-2 rounded-lg">
                            <Sparkles className="w-5 h-5 text-primary" />
                        </div>
                        <h2 className="text-xl font-bold text-foreground">{title}</h2>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        title="Lukk"
                        className="p-2 hover:bg-muted/10 rounded-full transition-colors text-muted hover:text-foreground"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    <div className="prose dark:prose-invert max-w-none prose-img:rounded-xl prose-img:border prose-img:border-border prose-headings:text-primary">
                        <ReactMarkdown>
                            {content}
                        </ReactMarkdown>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-border bg-muted/10 flex justify-end">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-6 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors font-medium"
                    >
                        Lukk
                    </button>
                </div>
            </motion.div>
        </div>
    );
}
