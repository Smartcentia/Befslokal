'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dagre from 'dagre';
import {
    Background,
    Controls,
    MarkerType,
    MiniMap,
    ReactFlow,
    ReactFlowProvider,
    useReactFlow,
    type Edge,
    type Node,
    type NodeMouseHandler,
    Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { getSchemaGraph, type SchemaForeignKey, type SchemaGraphResponse } from '@/lib/api/governanceApi';
import { Copy, GitBranch, Loader2, Search, X, ChevronRight } from 'lucide-react';

const NODE_W = 200;
const NODE_H = 44;

// ─── Layout ─────────────────────────────────────────────────────────────────

function layoutWithDagre(
    nodeList: Node[],
    edgeList: Edge[],
    direction: 'TB' | 'LR' = 'TB'
): { nodes: Node[]; edges: Edge[] } {
    if (nodeList.length === 0) return { nodes: [], edges: edgeList };
    const g = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
    g.setGraph({ rankdir: direction, ranksep: 72, nodesep: 48, marginx: 24, marginy: 24 });
    nodeList.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
    edgeList.forEach((e) => g.setEdge(e.source, e.target));
    dagre.layout(g);
    const isHorizontal = direction === 'LR';
    return {
        nodes: nodeList.map((node) => {
            const pos = g.node(node.id);
            return {
                ...node,
                targetPosition: isHorizontal ? Position.Left : Position.Top,
                sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
                position: { x: pos.x - NODE_W / 2, y: pos.y - NODE_H / 2 },
            };
        }),
        edges: edgeList,
    };
}

// ─── Graph building ──────────────────────────────────────────────────────────

function buildBaseGraph(
    payload: SchemaGraphResponse,
    search: string
): { nodes: Node[]; edges: Edge[] } {
    const q = search.trim().toLowerCase();
    const tableSet = new Set(payload.tables);
    const visibleTables = q
        ? new Set([...tableSet].filter((t) => t.toLowerCase().includes(q)))
        : tableSet;
    if (visibleTables.size === 0) return { nodes: [], edges: [] };

    const nodes: Node[] = [...visibleTables].sort().map((id) => ({
        id,
        type: 'default',
        data: { label: id },
        position: { x: 0, y: 0 },
    }));

    const edges: Edge[] = [];
    payload.foreign_keys.forEach((fk, idx) => {
        if (!visibleTables.has(fk.from_table) || !visibleTables.has(fk.to_table)) return;
        const fc = fk.from_columns.join(', ');
        const tc = fk.to_columns.join(', ');
        let label = `${fc} → ${tc}`;
        if (label.length > 48) label = `${label.slice(0, 45)}…`;
        edges.push({
            id: `fk_${idx}_${fk.from_table}_${fk.to_table}`,
            source: fk.from_table,
            target: fk.to_table,
            label,
            markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
            style: { stroke: '#64748b', strokeWidth: 1.25 },
            labelStyle: { fontSize: 10, fill: '#475569' },
            labelBgStyle: { fill: '#f8fafc', fillOpacity: 0.92 },
        });
    });

    return layoutWithDagre(nodes, edges, 'TB');
}

// ─── Highlight logic ─────────────────────────────────────────────────────────

function applyHighlight(
    nodes: Node[],
    edges: Edge[],
    selectedTable: string | null
): { nodes: Node[]; edges: Edge[] } {
    if (!selectedTable) return { nodes, edges };

    const connected = new Set<string>([selectedTable]);
    const activeEdgeIds = new Set<string>();
    edges.forEach((e) => {
        if (e.source === selectedTable || e.target === selectedTable) {
            connected.add(e.source);
            connected.add(e.target);
            activeEdgeIds.add(e.id);
        }
    });

    return {
        nodes: nodes.map((n) => ({
            ...n,
            style:
                n.id === selectedTable
                    ? { background: '#2563eb', color: '#fff', borderColor: '#1d4ed8', fontWeight: 700, borderWidth: 2 }
                    : connected.has(n.id)
                    ? { background: '#dbeafe', borderColor: '#3b82f6', borderWidth: 1.5 }
                    : { opacity: 0.2 },
        })),
        edges: edges.map((e) => ({
            ...e,
            style: activeEdgeIds.has(e.id)
                ? { stroke: '#2563eb', strokeWidth: 2.5 }
                : { stroke: '#cbd5e1', strokeWidth: 0.75, opacity: 0.25 },
            labelStyle: activeEdgeIds.has(e.id)
                ? { fontSize: 10, fill: '#1e40af', fontWeight: 600 }
                : { fontSize: 10, fill: '#94a3b8', opacity: 0.3 },
        })),
    };
}

// ─── Detail panel ────────────────────────────────────────────────────────────

function TableDetailPanel({
    table,
    foreignKeys,
    onClose,
    onSelectTable,
}: {
    table: string;
    foreignKeys: SchemaForeignKey[];
    onClose: () => void;
    onSelectTable: (t: string) => void;
}) {
    const outgoing = foreignKeys.filter((fk) => fk.from_table === table);
    const incoming = foreignKeys.filter((fk) => fk.to_table === table);

    return (
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-5 py-4">
            <div className="flex items-start justify-between mb-3">
                <h3 className="font-bold text-blue-900 flex items-center gap-2 text-base">
                    <GitBranch className="w-4 h-4 shrink-0" />
                    {table}
                </h3>
                <button
                    type="button"
                    onClick={onClose}
                    className="text-blue-400 hover:text-blue-700 transition-colors"
                    aria-label="Lukk"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <p className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-2">
                        Refererer til →
                    </p>
                    {outgoing.length === 0 ? (
                        <p className="text-sm text-blue-400 italic">Ingen utgående FK</p>
                    ) : (
                        <div className="space-y-1.5">
                            {outgoing.map((fk, i) => (
                                <div key={i} className="flex items-center gap-1.5 text-sm flex-wrap">
                                    <ChevronRight className="w-3 h-3 text-blue-400 shrink-0" />
                                    <span className="font-mono text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                                        {fk.from_columns.join(', ')}
                                    </span>
                                    <span className="text-blue-400 text-xs">→</span>
                                    <button
                                        type="button"
                                        onClick={() => onSelectTable(fk.to_table)}
                                        className="font-semibold text-blue-900 hover:underline hover:text-blue-600 transition-colors"
                                    >
                                        {fk.to_table}
                                    </button>
                                    <span className="font-mono text-xs text-blue-500">
                                        .{fk.to_columns.join(', ')}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div>
                    <p className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-2">
                        ← Referert av
                    </p>
                    {incoming.length === 0 ? (
                        <p className="text-sm text-blue-400 italic">Ingen inngående FK</p>
                    ) : (
                        <div className="space-y-1.5">
                            {incoming.map((fk, i) => (
                                <div key={i} className="flex items-center gap-1.5 text-sm flex-wrap">
                                    <ChevronRight className="w-3 h-3 text-blue-400 shrink-0 rotate-180" />
                                    <button
                                        type="button"
                                        onClick={() => onSelectTable(fk.from_table)}
                                        className="font-semibold text-blue-900 hover:underline hover:text-blue-600 transition-colors"
                                    >
                                        {fk.from_table}
                                    </button>
                                    <span className="font-mono text-xs text-blue-500">
                                        .{fk.from_columns.join(', ')}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {outgoing.length === 0 && incoming.length === 0 && (
                <p className="text-sm text-blue-500 italic mt-1">
                    Ingen fremmednøkkelkoblinger for denne tabellen.
                </p>
            )}
        </div>
    );
}

// ─── Inner graph (needs ReactFlow context) ───────────────────────────────────

function GraphInner({
    payload,
    search,
    selectedTable,
    onSelectTable,
}: {
    payload: SchemaGraphResponse;
    search: string;
    selectedTable: string | null;
    onSelectTable: (t: string | null) => void;
}) {
    const { fitView } = useReactFlow();
    const prevSelected = useRef<string | null>(null);

    const { nodes: baseNodes, edges: baseEdges } = useMemo(
        () => buildBaseGraph(payload, search),
        [payload, search]
    );

    const { nodes, edges } = useMemo(
        () => applyHighlight(baseNodes, baseEdges, selectedTable),
        [baseNodes, baseEdges, selectedTable]
    );

    useEffect(() => {
        if (selectedTable && selectedTable !== prevSelected.current) {
            prevSelected.current = selectedTable;
            setTimeout(() => {
                fitView({ nodes: [{ id: selectedTable }], duration: 600, padding: 0.5, maxZoom: 1.2 });
            }, 50);
        }
        if (!selectedTable) prevSelected.current = null;
    }, [selectedTable, fitView]);

    const onNodeClick: NodeMouseHandler = useCallback(
        (_evt, node) => {
            onSelectTable(selectedTable === node.id ? null : node.id);
        },
        [selectedTable, onSelectTable]
    );

    const onPaneClick = useCallback(() => onSelectTable(null), [onSelectTable]);

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ padding: 0.15 }}
            minZoom={0.08}
            maxZoom={2}
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            proOptions={{ hideAttribution: true }}
        >
            <Background gap={16} size={1} color="#e2e8f0" />
            <Controls showInteractive={false} />
            <MiniMap
                nodeStrokeWidth={2}
                zoomable
                pannable
                className="!bg-slate-50"
                maskColor="rgba(148, 163, 184, 0.12)"
            />
        </ReactFlow>
    );
}

// ─── Main component ──────────────────────────────────────────────────────────

export default function SchemaGraphView() {
    const [payload, setPayload] = useState<SchemaGraphResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState('');
    const [selectedTable, setSelectedTable] = useState<string | null>(null);
    const [copyMsg, setCopyMsg] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const data = await getSchemaGraph();
                if (!cancelled) setPayload(data);
            } catch (e) {
                if (!cancelled) setError(e instanceof Error ? e.message : 'Kunne ikke hente relasjonskart');
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    const onCopyMermaid = useCallback(async () => {
        if (!payload?.mermaid) return;
        try {
            await navigator.clipboard.writeText(payload.mermaid);
            setCopyMsg('Mermaid kopiert');
        } catch {
            setCopyMsg('Kunne ikke kopiere');
        }
        setTimeout(() => setCopyMsg(null), 2500);
    }, [payload]);

    const sidebarTables = useMemo(() => {
        if (!payload) return [];
        const q = search.trim().toLowerCase();
        return payload.tables
            .slice()
            .sort()
            .filter((t) => !q || t.toLowerCase().includes(q));
    }, [payload, search]);

    if (loading) {
        return (
            <div className="flex items-center justify-center gap-2 py-16 text-gray-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                Laster relasjonskart…
            </div>
        );
    }
    if (error) return <div className="py-8 text-center text-red-600">Feil: {error}</div>;
    if (!payload) return null;

    return (
        <div className="space-y-3">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setSelectedTable(null); }}
                        placeholder="Søk etter tabell…"
                        className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-sm"
                    />
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500 whitespace-nowrap">
                        {payload.tables.length} tabeller · {payload.foreign_keys.length} FK
                    </span>
                    {selectedTable && (
                        <button
                            type="button"
                            onClick={() => setSelectedTable(null)}
                            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-100 text-blue-800 text-sm font-medium hover:bg-blue-200 transition-colors"
                        >
                            <X className="w-3.5 h-3.5" />
                            Nullstill valg
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={onCopyMermaid}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium hover:bg-slate-900"
                    >
                        <Copy className="w-4 h-4" />
                        Kopier Mermaid
                    </button>
                </div>
            </div>
            {copyMsg && <p className="text-sm text-emerald-700 px-1" role="status">{copyMsg}</p>}

            {/* Main layout: sidebar + graph */}
            <div className="flex gap-3">
                {/* Left sidebar — table list */}
                <div className="w-56 shrink-0 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
                    <div className="px-3 py-2 border-b border-gray-100 text-[10px] font-bold uppercase tracking-wider text-gray-500">
                        Tabeller ({sidebarTables.length})
                    </div>
                    <div className="overflow-y-auto flex-1" style={{ maxHeight: 'min(72vh, 900px)' }}>
                        {sidebarTables.map((t) => {
                            const fkCount = payload.foreign_keys.filter(
                                (fk) => fk.from_table === t || fk.to_table === t
                            ).length;
                            const isSelected = t === selectedTable;
                            return (
                                <button
                                    key={t}
                                    type="button"
                                    onClick={() => setSelectedTable(isSelected ? null : t)}
                                    className={`w-full text-left px-3 py-1.5 text-xs border-l-2 flex items-center justify-between gap-1 transition-colors hover:bg-blue-50 ${
                                        isSelected
                                            ? 'border-l-blue-600 bg-blue-50 text-blue-900 font-semibold'
                                            : 'border-l-transparent text-gray-700 font-normal'
                                    }`}
                                >
                                    <span className="truncate">{t}</span>
                                    {fkCount > 0 && (
                                        <span className={`shrink-0 text-[9px] font-bold px-1 py-0.5 rounded ${isSelected ? 'bg-blue-200 text-blue-800' : 'bg-gray-100 text-gray-500'}`}>
                                            {fkCount}
                                        </span>
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Graph */}
                <div className="flex-1 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                    <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 text-xs text-gray-500">
                        <GitBranch className="w-4 h-4" />
                        Klikk en tabell for å se dens koblinger · Dra noder for å omorganisere
                    </div>
                    <div className="h-[min(72vh,900px)] w-full">
                        <ReactFlowProvider>
                            <GraphInner
                                payload={payload}
                                search={search}
                                selectedTable={selectedTable}
                                onSelectTable={setSelectedTable}
                            />
                        </ReactFlowProvider>
                    </div>
                </div>
            </div>

            {/* Detail panel */}
            {selectedTable && (
                <TableDetailPanel
                    table={selectedTable}
                    foreignKeys={payload.foreign_keys}
                    onClose={() => setSelectedTable(null)}
                    onSelectTable={setSelectedTable}
                />
            )}
        </div>
    );
}
