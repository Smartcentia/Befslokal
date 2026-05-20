'use client';

import React, { useState } from 'react';

export interface PendingAction {
    tool: string;
    title: string;
    description?: string;
    status: 'pending_approval' | 'approved' | 'rejected';
    recipient?: string; // e.g. for email
    [key: string]: any;
}

interface ActionApprovalCardProps {
    action: PendingAction;
    onApprove: (action: PendingAction) => void;
    onReject: (action: PendingAction) => void;
}

/**
 * Komponent som viser handlinger foreslått av KI Kollega
 * for Human-in-the-Loop godkjenning.
 */
export const ActionApprovalCard: React.FC<ActionApprovalCardProps> = ({
    action,
    onApprove,
    onReject,
}) => {
    const [isProcessing, setIsProcessing] = useState(false);

    // Visuell representasjon basert på tool
    const getToolIcon = () => {
        switch (action.tool) {
            case 'create_jira_ticket':
                return '🎫';
            case 'send_email':
                return '📧';
            case 'update_database':
                return '💾';
            default:
                return '⚡';
        }
    };

    const handleApprove = async () => {
        setIsProcessing(true);
        await onApprove(action);
        setIsProcessing(false);
    };

    const handleReject = async () => {
        setIsProcessing(true);
        await onReject(action);
        setIsProcessing(false);
    };

    if (action.status !== 'pending_approval') {
        return (
            <div className="rounded-md bg-gray-50 border border-gray-200 p-3 mb-2 opacity-70">
                <div className="flex items-center text-sm text-gray-500">
                    <span className="mr-2">{getToolIcon()}</span>
                    <span>
                        Handling: {action.title} ({action.status === 'approved' ? 'Godkjent' : 'Avvist'})
                    </span>
                </div>
            </div>
        );
    }

    return (
        <div className="rounded-lg shadow-sm border border-blue-200 bg-blue-50 p-4 mb-3">
            <div className="flex items-start mb-2">
                <div className="bg-blue-100 rounded p-2 text-xl shadow-sm mr-3">
                    {getToolIcon()}
                </div>
                <div className="flex-1">
                    <h4 className="font-semibold text-blue-900 m-0 leading-tight">
                        Systemhandling krever godkjenning
                    </h4>
                    <p className="text-sm text-blue-800 m-0 mt-1 font-medium">
                        {action.title}
                    </p>
                </div>
            </div>

            <div className="bg-white rounded p-3 text-sm text-gray-700 border border-blue-100 shadow-inner mb-4">
                {action.description && (
                    <p className="mb-2 whitespace-pre-wrap">{action.description}</p>
                )}
                {action.tool === 'send_email' && action.recipient && (
                    <p className="mb-1"><strong>Til:</strong> {action.recipient}</p>
                )}
                <div className="mt-2 text-xs font-mono bg-gray-50 p-2 rounded text-gray-500 overflow-x-auto">
                    Handling: {action.tool}
                </div>
            </div>

            <div className="flex justify-end gap-2">
                <button
                    className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
                    onClick={handleReject}
                    disabled={isProcessing}
                >
                    Avvis
                </button>
                <button
                    className="px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors shadow-sm"
                    onClick={handleApprove}
                    disabled={isProcessing}
                >
                    {isProcessing ? 'Utfører...' : 'Godkjenn og Utfør'}
                </button>
            </div>
        </div>
    );
};
