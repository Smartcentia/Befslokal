"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
    children?: ReactNode;
    componentName?: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`Uncaught error in ${this.props.componentName || "component"}:`, error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20 flex items-start gap-3">
                    <AlertTriangle className="text-red-500 shrink-0" size={20} />
                    <div>
                        <h3 className="text-sm font-bold text-red-500">
                            Feil i {this.props.componentName || "komponent"}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                            En klientfeil oppstod.
                            <br />
                            <span className="opacity-50 font-mono text-[10px]">{this.state.error?.message}</span>
                        </p>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
