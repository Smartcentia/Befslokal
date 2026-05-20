"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { fetchAPI, getApiAuthContext, API_BASE_URL } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Upload,
    FileText,
    Download,
    ChevronLeft,
    CheckCircle2,
    AlertCircle,
    Loader2,
} from "lucide-react";

// ─────────────────────────────────────────────
// Typer
// ─────────────────────────────────────────────

interface ImportResult {
    created: number;
    skipped: number;
    errors: string[];
}

interface DocumentImportResult {
    document_id: string;
    title: string;
    document_type: string;
}

const DOCUMENT_TYPES = [
    { value: "brannplan", label: "Brannplan" },
    { value: "fdv_manual", label: "FDV-manual" },
    { value: "tegning", label: "Tegning" },
    { value: "akustikkrapport", label: "Akustikkrapport" },
    { value: "energiattest", label: "Energiattest" },
    { value: "serviceavtale", label: "Serviceavtale" },
    { value: "garantidokument", label: "Garantidokument" },
    { value: "samsvarserklæring", label: "Samsvarserklæring" },
    { value: "instruksjon", label: "Instruksjon" },
    { value: "hms_prosedyre", label: "HMS-prosedyre" },
    { value: "tilstandsrapport", label: "Tilstandsrapport" },
    { value: "inspeksjonsprotokoll", label: "Inspeksjonsprotokoll" },
];

// ─────────────────────────────────────────────
// Hoved-komponent
// ─────────────────────────────────────────────

export default function FdvImportPage() {
    const params = useParams();
    const propertyId = params?.propertyId as string;

    // CSV-seksjon
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [csvLoading, setCsvLoading] = useState(false);
    const [csvResult, setCsvResult] = useState<ImportResult | null>(null);
    const [csvError, setCsvError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Dokument-seksjon
    const [docTitle, setDocTitle] = useState("");
    const [docType, setDocType] = useState("fdv_manual");
    const [docUrl, setDocUrl] = useState("");
    const [docValidUntil, setDocValidUntil] = useState("");
    const [docLoading, setDocLoading] = useState(false);
    const [docResult, setDocResult] = useState<DocumentImportResult | null>(null);
    const [docError, setDocError] = useState<string | null>(null);

    // ─────────────────────────────────────────────
    // Handlers
    // ─────────────────────────────────────────────

    async function handleCsvUpload(e: React.FormEvent) {
        e.preventDefault();
        if (!csvFile || !propertyId) return;

        setCsvLoading(true);
        setCsvResult(null);
        setCsvError(null);

        try {
            const formData = new FormData();
            formData.append("file", csvFile);

            const res = await fetch(
                `${API_BASE_URL}/fdvu/import/components-csv?property_id=${propertyId}`,
                {
                    method: "POST",
                    body: formData,
                    // Ikke sett Content-Type – nettleseren setter multipart boundary selv
                    headers: await buildAuthHeaders(),
                }
            );

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail ?? "Importfeil");
            }

            const data: ImportResult = await res.json();
            setCsvResult(data);
            setCsvFile(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
        } catch (err: unknown) {
            setCsvError(err instanceof Error ? err.message : "Ukjent feil");
        } finally {
            setCsvLoading(false);
        }
    }

    async function handleDocumentSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!docTitle || !docType || !propertyId) return;

        setDocLoading(true);
        setDocResult(null);
        setDocError(null);

        try {
            const payload = {
                property_id: propertyId,
                title: docTitle,
                document_type: docType,
                external_url: docUrl || null,
                valid_until: docValidUntil || null,
            };

            const data = await fetchAPI<DocumentImportResult>(
                `/fdvu/import/document`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                }
            );

            setDocResult(data);
            setDocTitle("");
            setDocUrl("");
            setDocValidUntil("");
            setDocType("fdv_manual");
        } catch (err: unknown) {
            setDocError(err instanceof Error ? err.message : "Ukjent feil");
        } finally {
            setDocLoading(false);
        }
    }

    function handleDownloadTemplate() {
        window.open(`${API_BASE_URL}/fdvu/import/template`, "_blank");
    }

    // ─────────────────────────────────────────────
    // Render
    // ─────────────────────────────────────────────

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Tilbakelenke */}
                <Link
                    href={`/fdvu/${propertyId}`}
                    className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                    <ChevronLeft size={16} />
                    Tilbake til FDVU-oversikt
                </Link>

                <div>
                    <h1 className="text-2xl font-semibold tracking-tight">
                        Importer FDV-data
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Last opp komponentlister fra CSV eller registrer FDV-dokumenter manuelt.
                    </p>
                </div>

                {/* ── Seksjon 1: CSV-import ── */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Upload size={18} />
                            Importer komponenter fra CSV
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            Last opp en CSV-fil med bygningskomponenter. Bruk malen nedenfor
                            som utgangspunkt.
                        </p>

                        <button
                            type="button"
                            onClick={handleDownloadTemplate}
                            className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                        >
                            <Download size={14} />
                            Last ned CSV-mal
                        </button>

                        <form onSubmit={handleCsvUpload} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    CSV-fil
                                </label>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) =>
                                        setCsvFile(e.target.files?.[0] ?? null)
                                    }
                                    className="block w-full text-sm text-muted-foreground
                                        file:mr-3 file:py-1.5 file:px-3
                                        file:rounded file:border file:border-border
                                        file:text-sm file:font-medium
                                        file:bg-muted file:text-foreground
                                        hover:file:bg-muted/80 cursor-pointer"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={!csvFile || csvLoading}
                                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {csvLoading ? (
                                    <Loader2 size={14} className="animate-spin" />
                                ) : (
                                    <Upload size={14} />
                                )}
                                {csvLoading ? "Importerer..." : "Importer"}
                            </button>
                        </form>

                        {/* CSV-resultat */}
                        {csvResult && (
                            <div className="rounded-md border border-border bg-muted/40 p-4 space-y-2">
                                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                                    <CheckCircle2 size={16} className="text-success" />
                                    Import fullført
                                </div>
                                <dl className="grid grid-cols-3 gap-2 text-sm">
                                    <div>
                                        <dt className="text-muted-foreground">Opprettet</dt>
                                        <dd className="font-semibold">{csvResult.created}</dd>
                                    </div>
                                    <div>
                                        <dt className="text-muted-foreground">Hoppet over</dt>
                                        <dd className="font-semibold">{csvResult.skipped}</dd>
                                    </div>
                                    <div>
                                        <dt className="text-muted-foreground">Feil</dt>
                                        <dd className="font-semibold">{csvResult.errors.length}</dd>
                                    </div>
                                </dl>
                                {csvResult.errors.length > 0 && (
                                    <ul className="mt-2 space-y-1">
                                        {csvResult.errors.map((err, i) => (
                                            <li
                                                key={i}
                                                className="text-xs text-destructive flex items-start gap-1"
                                            >
                                                <AlertCircle size={12} className="mt-0.5 shrink-0" />
                                                {err}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        )}

                        {csvError && (
                            <div className="flex items-center gap-2 text-sm text-destructive">
                                <AlertCircle size={14} />
                                {csvError}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* ── Seksjon 2: Dokument-registrering ── */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText size={18} />
                            Legg til FDV-dokument
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleDocumentSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Tittel <span className="text-destructive">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={docTitle}
                                    onChange={(e) => setDocTitle(e.target.value)}
                                    required
                                    placeholder="F.eks. Brannplan 2024"
                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Dokumenttype <span className="text-destructive">*</span>
                                </label>
                                <select
                                    value={docType}
                                    onChange={(e) => setDocType(e.target.value)}
                                    required
                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                >
                                    {DOCUMENT_TYPES.map((t) => (
                                        <option key={t.value} value={t.value}>
                                            {t.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Ekstern URL
                                </label>
                                <input
                                    type="url"
                                    value={docUrl}
                                    onChange={(e) => setDocUrl(e.target.value)}
                                    placeholder="https://byggeweb.no/dokument/..."
                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    Gyldig til
                                </label>
                                <input
                                    type="date"
                                    value={docValidUntil}
                                    onChange={(e) => setDocValidUntil(e.target.value)}
                                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={!docTitle || docLoading}
                                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {docLoading ? (
                                    <Loader2 size={14} className="animate-spin" />
                                ) : (
                                    <FileText size={14} />
                                )}
                                {docLoading ? "Lagrer..." : "Registrer dokument"}
                            </button>
                        </form>

                        {/* Dokument-resultat */}
                        {docResult && (
                            <div className="mt-4 flex items-center gap-2 rounded-md border border-border bg-muted/40 p-3 text-sm">
                                <CheckCircle2 size={16} className="text-success shrink-0" />
                                <span>
                                    <span className="font-medium">{docResult.title}</span>{" "}
                                    er registrert som{" "}
                                    <span className="font-medium">{docResult.document_type}</span>.
                                </span>
                            </div>
                        )}

                        {docError && (
                            <div className="mt-4 flex items-center gap-2 text-sm text-destructive">
                                <AlertCircle size={14} />
                                {docError}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────
// Auth-hjelper for rå fetch (CSV multipart)
// ─────────────────────────────────────────────

async function buildAuthHeaders(): Promise<HeadersInit> {
    const { token, session } = await getApiAuthContext();
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const userEmail = session?.user?.email;
    if (userEmail) headers['X-User-Email'] = userEmail;
    return headers;
}
