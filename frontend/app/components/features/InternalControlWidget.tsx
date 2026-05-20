"use client";

import React, { useEffect, useState } from 'react';
import { getInternalControlCases, InternalControlCase } from '@/lib/api';
import { internalControlService, ChecklistTemplate } from '@/lib/domains/hms/internalControlService';
import Link from 'next/link';
import DataTooltip from '@/app/components/ui/DataTooltip';
import { Plus, FileCheck, ChevronDown } from 'lucide-react';

interface InternalControlWidgetProps {
    propertyId?: string;
}

export default function InternalControlWidget({ propertyId }: InternalControlWidgetProps) {
    const [cases, setCases] = useState<InternalControlCase[]>([]);
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);
    const [templates, setTemplates] = useState<ChecklistTemplate[]>([]);
    const [showTemplateDropdown, setShowTemplateDropdown] = useState(false);
    const [creatingFromTemplate, setCreatingFromTemplate] = useState(false);

    const loadCases = () => {
        getInternalControlCases()
            .then(data => {
                let filtered = data;
                if (propertyId) {
                    filtered = data.filter(c => c.property_id === propertyId);
                }
                setCases(filtered.slice(0, 5));
            })
            .catch(console.error);
    };

    useEffect(() => {
        loadCases();
    }, [propertyId]);

    useEffect(() => {
        if (propertyId && showTemplateDropdown) {
            internalControlService.getChecklists('all').then(setTemplates).catch(() => setTemplates([]));
        }
    }, [propertyId, showTemplateDropdown]);

    const handleCreateInitialCases = async () => {
        if (!propertyId) return;
        setCreateError(null);
        setCreating(true);
        try {
            await internalControlService.createInitialCasesForProperty(propertyId);
            loadCases();
        } catch (e) {
            setCreateError(e instanceof Error ? e.message : "Kunne ikke opprette saker.");
        } finally {
            setCreating(false);
        }
    };

    const handleCreateFromTemplate = async (templateId: string) => {
        if (!propertyId) return;
        setCreateError(null);
        setCreatingFromTemplate(true);
        try {
            await internalControlService.createCaseFromTemplate(templateId, propertyId);
            setShowTemplateDropdown(false);
            loadCases();
        } catch (e) {
            setCreateError(e instanceof Error ? e.message : "Kunne ikke opprette sak fra mal.");
        } finally {
            setCreatingFromTemplate(false);
        }
    };

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-4">
                <div className="flex-1"></div>
                <DataTooltip content="Avvik: Avvikelse fra krav eller plan (f.eks. manglende dokumentasjon, forfalt inspeksjon, HMS-brudd). Overvåkes via sjekklister og internkontroll.">
                    <span className="px-2 py-0.5 bg-amber-50 dark:bg-amber-500/20 text-amber-600 dark:text-amber-300 text-[10px] font-bold uppercase tracking-wide rounded-full border border-amber-200 dark:border-amber-500/30">
                        {cases.length} Avvik
                    </span>
                </DataTooltip>
            </div>

            <div className="space-y-3">
                {cases.map(dev => (
                    <Link
                        key={dev.case_id}
                        href={`/checklists?case_id=${dev.case_id}`}
                        className="flex items-center justify-between p-3 bg-surface hover:bg-muted/10 rounded-lg transition-all border border-border group shadow-sm"
                    >
                        <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full shadow-[0_0_8px] ${dev.priority === 'critical' || dev.priority === 'high' ? 'bg-red-500 shadow-red-500/50' :
                                dev.priority === 'medium' ? 'bg-amber-500 shadow-amber-500/50' :
                                    'bg-blue-500 shadow-blue-500/50'
                                }`} />
                            <div>
                                <div className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">{dev.title}</div>
                                <div className="text-[10px] text-muted font-bold uppercase tracking-tight">{dev.case_type}</div>
                            </div>
                        </div>
                        <span className="text-xs text-muted group-hover:text-muted-foreground font-medium">
                            {dev.due_date ? new Date(dev.due_date).toLocaleDateString() : 'Ingen frist'}
                        </span>
                    </Link>
                ))}
                {cases.length === 0 && (
                    <DataTooltip content="Ingen aktive avvik: Alle sjekklister er oppfylt eller ingen avvik er registrert for denne eiendommen.">
                        <div className="text-muted text-sm text-center py-4 italic font-medium">Ingen aktive avvik funnet</div>
                    </DataTooltip>
                )}
            </div>

            {propertyId && (
                <div className="mt-3 space-y-2">
                    <DataTooltip content="Opprett initiale internkontroll-saker for denne eiendommen basert på maler (RKL6, brannvern, etc.).">
                        <button
                            onClick={handleCreateInitialCases}
                            disabled={creating}
                            className="flex items-center justify-center gap-2 w-full py-2 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary/80 hover:bg-primary/10 rounded-lg transition-all border border-dashed border-primary/20 disabled:opacity-50"
                        >
                            <Plus size={14} />
                            {creating ? "Oppretter..." : "Opprett internkontroll-saker"}
                        </button>
                    </DataTooltip>
                    <div className="relative">
                        <DataTooltip content="Opprett en internkontroll-sak fra en sjekklistemal (system eller egendefinert).">
                            <button
                                onClick={() => setShowTemplateDropdown(!showTemplateDropdown)}
                                disabled={creatingFromTemplate}
                                className="flex items-center justify-center gap-2 w-full py-2 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary/80 hover:bg-primary/10 rounded-lg transition-all border border-dashed border-primary/20 disabled:opacity-50"
                            >
                                <FileCheck size={14} />
                                {creatingFromTemplate ? "Oppretter..." : "Opprett fra mal"}
                                <ChevronDown size={12} className={showTemplateDropdown ? "rotate-180" : ""} />
                            </button>
                        </DataTooltip>
                        {showTemplateDropdown && templates.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-background border border-border rounded-lg shadow-lg z-20 max-h-48 overflow-y-auto">
                                {templates.map((t) => (
                                    <button
                                        key={t.template_id}
                                        onClick={() => handleCreateFromTemplate(t.template_id)}
                                        className="w-full text-left px-3 py-2 text-sm hover:bg-muted/50 rounded truncate"
                                    >
                                        {t.title}
                                    </button>
                                ))}
                            </div>
                        )}
                        {showTemplateDropdown && templates.length === 0 && (
                            <div className="absolute top-full left-0 right-0 mt-1 p-3 bg-background border border-border rounded-lg shadow-lg z-20 text-sm text-muted">
                                Ingen maler. <Link href="/checklists/templates" className="text-primary hover:underline">Opprett mal</Link>
                            </div>
                        )}
                    </div>
                </div>
            )}
            {createError && (
                <p className="text-red-400 text-xs mt-2">{createError}</p>
            )}
            <DataTooltip content="Sjekklister: Strukturerte lister for internkontroll (f.eks. brannslukker, rømningsveier). Brukes til systematisk oppfølging av HMS og vedlikehold.">
                <Link
                    href="/checklists"
                    className="block w-full mt-4 py-2 text-[10px] font-bold uppercase tracking-widest text-primary hover:text-primary/80 hover:bg-primary/10 rounded-lg transition-all text-center border border-dashed border-primary/20"
                >
                    Se alle sjekklister og avvik
                </Link>
            </DataTooltip>
        </div>
    );
}
